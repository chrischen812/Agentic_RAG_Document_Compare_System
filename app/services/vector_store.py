"""
ChromaDB vector store with hierarchical ontological indexing.
"""
import json
import logging
import uuid
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings

from app.core.config import settings
from app.services.chunking_service import DocumentChunk
from app.services.document_classifier import DocumentClassification
from app.services.ontology_manager import OntologyStructure
from app.models.schemas import DocumentInfo

class VectorStore:
    """ChromaDB-based vector store with ontological indexing."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = None
        self.collection = None
    
    async def initialize(self):
        """Initialize ChromaDB client and collection."""
        try:
            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(
                path=settings.chroma_db_path,
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=settings.chroma_collection_name,
                metadata={"description": "Agentic RAG System Documents"}
            )
            
            self.logger.info("ChromaDB initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing ChromaDB: {str(e)}")
            raise
    
    async def store_document(
        self,
        filename: str,
        chunks: List[DocumentChunk],
        classification: DocumentClassification,
        ontology_mapping: Optional[OntologyStructure] = None
    ) -> str:
        """Store document chunks in the vector database."""
        try:
            document_id = str(uuid.uuid4())
            
            # Prepare data for ChromaDB
            ids = []
            documents = []
            embeddings = []
            metadatas = []
            
            for chunk in chunks:
                chunk_id = f"{document_id}_{chunk.chunk_id}"
                ids.append(chunk_id)
                documents.append(chunk.content)
                
                if chunk.embeddings:
                    embeddings.append(chunk.embeddings)
                
                # Create comprehensive metadata
                metadata = {
                    "document_id": document_id,
                    "filename": filename,
                    "chunk_id": chunk.chunk_id,
                    "chunk_type": chunk.chunk_type,
                    "page_number": chunk.page_number,
                    "position": chunk.position,
                    "domain": classification.domain,
                    "document_type": classification.document_type,
                    "ontology_concepts": json.dumps(chunk.ontology_concepts),
                    "classification_confidence": classification.confidence,
                    "key_entities": json.dumps(classification.key_entities)
                }
                
                # Add chunk-specific metadata
                metadata.update(chunk.metadata)
                
                # Convert all values to strings (ChromaDB requirement)
                metadata = {k: str(v) for k, v in metadata.items()}
                metadatas.append(metadata)
            
            # Store in ChromaDB
            if embeddings and len(embeddings) == len(documents):
                self.collection.add(
                    ids=ids,
                    documents=documents,
                    embeddings=embeddings,
                    metadatas=metadatas
                )
            else:
                # Let ChromaDB generate embeddings
                self.collection.add(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas
                )
            
            # Store document metadata separately
            await self._store_document_metadata(document_id, filename, classification, len(chunks))
            
            self.logger.info(f"Stored document {filename} with {len(chunks)} chunks")
            return document_id
            
        except Exception as e:
            self.logger.error(f"Error storing document: {str(e)}")
            raise
    
    async def query_similar(
        self,
        query_text: str,
        top_k: int = None,
        domain_filter: Optional[str] = None,
        document_type_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Query for similar documents with optional filtering."""
        try:
            if top_k is None:
                top_k = settings.retrieval_top_k
            
            # Build where clause for filtering
            where_clause = {}
            if domain_filter:
                where_clause["domain"] = domain_filter
            if document_type_filter:
                where_clause["document_type"] = document_type_filter
            
            # Query ChromaDB
            results = self.collection.query(
                query_texts=[query_text],
                n_results=top_k,
                where=where_clause if where_clause else None
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    result = {
                        "id": results['ids'][0][i],
                        "content": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i],
                        "distance": results['distances'][0][i] if results.get('distances') else None
                    }
                    
                    # Parse JSON fields in metadata
                    if 'ontology_concepts' in result['metadata']:
                        try:
                            result['metadata']['ontology_concepts'] = json.loads(
                                result['metadata']['ontology_concepts']
                            )
                        except:
                            pass
                    
                    if 'key_entities' in result['metadata']:
                        try:
                            result['metadata']['key_entities'] = json.loads(
                                result['metadata']['key_entities']
                            )
                        except:
                            pass
                    
                    formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"Error querying vector store: {str(e)}")
            raise
    
    async def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        """Get all chunks for a specific document."""
        try:
            results = self.collection.get(
                where={"document_id": document_id}
            )
            
            chunks = []
            if results['documents']:
                for i in range(len(results['documents'])):
                    chunk = {
                        "id": results['ids'][i],
                        "content": results['documents'][i],
                        "metadata": results['metadatas'][i]
                    }
                    
                    # Parse JSON fields
                    if 'ontology_concepts' in chunk['metadata']:
                        try:
                            chunk['metadata']['ontology_concepts'] = json.loads(
                                chunk['metadata']['ontology_concepts']
                            )
                        except:
                            pass
                    
                    chunks.append(chunk)
            
            return chunks
            
        except Exception as e:
            self.logger.error(f"Error getting document chunks: {str(e)}")
            raise
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete a document and all its chunks."""
        try:
            # Get all chunk IDs for the document
            results = self.collection.get(
                where={"document_id": document_id}
            )
            
            if results['ids']:
                # Delete all chunks
                self.collection.delete(ids=results['ids'])
                
                # Delete document metadata
                await self._delete_document_metadata(document_id)
                
                self.logger.info(f"Deleted document {document_id}")
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Error deleting document: {str(e)}")
            raise
    
    async def get_all_documents(self) -> List[DocumentInfo]:
        """Get information about all stored documents."""
        try:
            # This is a simplified implementation
            # In a real system, you might want to store document metadata separately
            results = self.collection.get()
            
            # Group by document_id
            documents = {}
            for i, metadata in enumerate(results['metadatas']):
                doc_id = metadata.get('document_id')
                if doc_id and doc_id not in documents:
                    documents[doc_id] = DocumentInfo(
                        document_id=doc_id,
                        filename=metadata.get('filename', 'unknown'),
                        domain=metadata.get('domain', 'unknown'),
                        document_type=metadata.get('document_type', 'unknown'),
                        chunk_count=0,
                        upload_date=None,  # Would need to be stored separately
                        classification_confidence=float(metadata.get('classification_confidence', 0))
                    )
                
                if doc_id in documents:
                    documents[doc_id].chunk_count += 1
            
            return list(documents.values())
            
        except Exception as e:
            self.logger.error(f"Error getting all documents: {str(e)}")
            raise
    
    async def _store_document_metadata(
        self,
        document_id: str,
        filename: str,
        classification: DocumentClassification,
        chunk_count: int
    ):
        """Store document metadata separately (could be in a different collection or database)."""
        # For now, this is a placeholder
        # In a production system, you might want to store this in a separate collection
        pass
    
    async def _delete_document_metadata(self, document_id: str):
        """Delete document metadata."""
        # Placeholder for metadata deletion
        pass
    
    async def close(self):
        """Close the vector store connection."""
        # ChromaDB doesn't require explicit closing
        self.logger.info("Vector store closed")
