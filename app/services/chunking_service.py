"""
Advanced semantic chunking service with domain-aware context preservation.
"""
import re
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import spacy
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from app.core.config import settings
from app.services.pdf_parser import ParsedContent
from app.services.document_classifier import DocumentClassification
from app.services.ontology_manager import OntologyStructure

@dataclass
class DocumentChunk:
    """Represents a semantically meaningful document chunk."""
    chunk_id: str
    content: str
    chunk_type: str  # paragraph, table, section, etc.
    page_number: int
    position: int
    metadata: Dict[str, Any]
    ontology_concepts: List[str]
    embeddings: Optional[List[float]] = None

class ChunkingService:
    """Advanced semantic chunking with domain-aware context preservation."""
    
    def __init__(self, ontology: Optional[OntologyStructure] = None):
        self.logger = logging.getLogger(__name__)
        self.ontology = ontology
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap
        
        # Initialize NLP models
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            self.logger.warning("spaCy model not found, using basic tokenization")
            self.nlp = None
        
        # Initialize embedding model
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            self.embedding_model = SentenceTransformer(settings.embedding_model)
        else:
            self.logger.warning("SentenceTransformers not available, using fallback embeddings")
            self.embedding_model = None
    
    async def chunk_document(
        self, 
        parsed_content: ParsedContent, 
        classification: DocumentClassification
    ) -> List[DocumentChunk]:
        """Create semantically meaningful chunks from parsed content."""
        try:
            chunks = []
            
            # Process different content types
            text_chunks = await self._chunk_text_content(parsed_content, classification)
            chunks.extend(text_chunks)
            
            table_chunks = await self._chunk_table_content(parsed_content, classification)
            chunks.extend(table_chunks)
            
            # Add ontology concepts to chunks
            if self.ontology:
                chunks = await self._add_ontology_concepts(chunks, classification)
            
            # Generate embeddings
            chunks = await self._generate_embeddings(chunks)
            
            self.logger.info(f"Created {len(chunks)} chunks from document")
            return chunks
            
        except Exception as e:
            self.logger.error(f"Error chunking document: {str(e)}")
            raise
    
    async def _chunk_text_content(
        self, 
        parsed_content: ParsedContent, 
        classification: DocumentClassification
    ) -> List[DocumentChunk]:
        """Chunk text content with semantic awareness."""
        chunks = []
        
        for page_idx, page in enumerate(parsed_content.pages):
            # Safely get page text
            page_text = ""
            if isinstance(page, dict) and 'text' in page:
                page_text = page['text'] or ""
            
            if not page_text or not str(page_text).strip():
                continue
            
            # Ensure page_text is a string and clean it
            page_text = str(page_text).replace('None', '').strip()
            if not page_text:
                continue
            
            # Apply domain-specific chunking strategy
            if classification.domain == "healthcare":
                page_chunks = await self._chunk_healthcare_text(page_text, page_idx + 1)
            elif classification.domain == "legal":
                page_chunks = await self._chunk_legal_text(page_text, page_idx + 1)
            elif classification.domain == "financial":
                page_chunks = await self._chunk_financial_text(page_text, page_idx + 1)
            else:
                page_chunks = await self._chunk_general_text(page_text, page_idx + 1)
            
            chunks.extend(page_chunks)
        
        return chunks
    
    async def _chunk_healthcare_text(self, text: str, page_number: int) -> List[DocumentChunk]:
        """Healthcare-specific text chunking."""
        chunks = []
        
        # Split by sections common in healthcare documents
        section_patterns = [
            r'\n\s*(?:COVERAGE|BENEFITS|LIMITATIONS|EXCLUSIONS|DEFINITIONS).*?\n',
            r'\n\s*(?:Section|Article|Part)\s+\d+.*?\n',
            r'\n\s*\d+\.\s+[A-Z][^.]*\n'
        ]
        
        sections = self._split_by_patterns(text, section_patterns)
        
        for i, section in enumerate(sections):
            if len(section.strip()) < 50:  # Skip very short sections
                continue
            
            # Further split large sections
            if len(section) > self.chunk_size:
                subsections = self._split_large_section(section)
                for j, subsection in enumerate(subsections):
                    chunk = DocumentChunk(
                        chunk_id=f"health_text_{page_number}_{i}_{j}",
                        content=str(subsection).strip(),
                        chunk_type="healthcare_section",
                        page_number=page_number,
                        position=i * 100 + j,
                        metadata={
                            "section_type": "healthcare",
                            "subsection": j,
                            "parent_section": i
                        },
                        ontology_concepts=[]
                    )
                    chunks.append(chunk)
            else:
                chunk = DocumentChunk(
                    chunk_id=f"health_text_{page_number}_{i}",
                    content=str(section).strip(),
                    chunk_type="healthcare_section",
                    page_number=page_number,
                    position=i,
                    metadata={"section_type": "healthcare"},
                    ontology_concepts=[]
                )
                chunks.append(chunk)
        
        return chunks
    
    async def _chunk_legal_text(self, text: str, page_number: int) -> List[DocumentChunk]:
        """Legal document-specific text chunking."""
        chunks = []
        
        # Legal documents often have numbered clauses
        clause_pattern = r'\n\s*\d+\.\s+[^.]*(?:\.[^.]*)*\.\s*\n'
        clauses = re.split(clause_pattern, text)
        
        for i, clause in enumerate(clauses):
            if len(clause.strip()) < 30:
                continue
            
            chunk = DocumentChunk(
                chunk_id=f"legal_text_{page_number}_{i}",
                content=clause.strip(),
                chunk_type="legal_clause",
                page_number=page_number,
                position=i,
                metadata={"clause_number": i},
                ontology_concepts=[]
            )
            chunks.append(chunk)
        
        return chunks
    
    async def _chunk_financial_text(self, text: str, page_number: int) -> List[DocumentChunk]:
        """Financial document-specific text chunking."""
        chunks = []
        
        # Financial documents often have sections and subsections
        paragraphs = text.split('\n\n')
        
        for i, paragraph in enumerate(paragraphs):
            if len(paragraph.strip()) < 50:
                continue
            
            chunk = DocumentChunk(
                chunk_id=f"financial_text_{page_number}_{i}",
                content=paragraph.strip(),
                chunk_type="financial_paragraph",
                page_number=page_number,
                position=i,
                metadata={"paragraph_type": "financial"},
                ontology_concepts=[]
            )
            chunks.append(chunk)
        
        return chunks
    
    async def _chunk_general_text(self, text: str, page_number: int) -> List[DocumentChunk]:
        """General text chunking with semantic boundaries."""
        chunks = []
        
        # Use spaCy for sentence segmentation if available
        if self.nlp:
            doc = self.nlp(text)
            sentences = [sent.text for sent in doc.sents]
        else:
            sentences = re.split(r'[.!?]+', text)
        
        current_chunk = ""
        chunk_count = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Check if adding this sentence would exceed chunk size
            if len(current_chunk) + len(sentence) > self.chunk_size:
                if current_chunk:
                    chunk = DocumentChunk(
                        chunk_id=f"general_text_{page_number}_{chunk_count}",
                        content=current_chunk.strip(),
                        chunk_type="text_paragraph",
                        page_number=page_number,
                        position=chunk_count,
                        metadata={"chunk_method": "sentence_boundary"},
                        ontology_concepts=[]
                    )
                    chunks.append(chunk)
                    chunk_count += 1
                
                current_chunk = sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        # Add final chunk
        if current_chunk.strip():
            chunk = DocumentChunk(
                chunk_id=f"general_text_{page_number}_{chunk_count}",
                content=current_chunk.strip(),
                chunk_type="text_paragraph",
                page_number=page_number,
                position=chunk_count,
                metadata={"chunk_method": "sentence_boundary"},
                ontology_concepts=[]
            )
            chunks.append(chunk)
        
        return chunks
    
    async def _chunk_table_content(
        self, 
        parsed_content: ParsedContent, 
        classification: DocumentClassification
    ) -> List[DocumentChunk]:
        """Create chunks from table content."""
        chunks = []
        
        for page_idx, page in enumerate(parsed_content.pages):
            for table_idx, table in enumerate(page['tables']):
                # Convert table to text representation
                table_text = self._table_to_text(table)
                
                chunk = DocumentChunk(
                    chunk_id=f"table_{page_idx + 1}_{table_idx}",
                    content=table_text,
                    chunk_type="table",
                    page_number=page_idx + 1,
                    position=table_idx,
                    metadata={
                        "table_structure": table.get('structure_type', 'unknown'),
                        "row_count": table.get('row_count', 0),
                        "column_count": table.get('column_count', 0),
                        "headers": table.get('headers', [])
                    },
                    ontology_concepts=[]
                )
                chunks.append(chunk)
        
        return chunks
    
    def _table_to_text(self, table: Dict[str, Any]) -> str:
        """Convert table structure to readable text."""
        text_parts = []
        
        # Add headers
        headers = table.get('headers', [])
        if headers:
            text_parts.append(f"Table headers: {', '.join(headers)}")
        
        # Add data rows
        data = table.get('data', [])
        for i, row in enumerate(data[:10]):  # Limit to first 10 rows
            row_text = []
            for key, value in row.items():
                if value:
                    row_text.append(f"{key}: {value}")
            if row_text:
                text_parts.append(f"Row {i + 1}: {'; '.join(row_text)}")
        
        if len(data) > 10:
            text_parts.append(f"... and {len(data) - 10} more rows")
        
        return "\n".join(text_parts)
    
    def _split_by_patterns(self, text: str, patterns: List[str]) -> List[str]:
        """Split text by multiple regex patterns."""
        sections = [text]
        
        for pattern in patterns:
            new_sections = []
            for section in sections:
                splits = re.split(pattern, section, flags=re.IGNORECASE)
                new_sections.extend([s for s in splits if s.strip()])
            sections = new_sections
        
        return sections
    
    def _split_large_section(self, text: str) -> List[str]:
        """Split large sections into smaller chunks."""
        # Try to split by paragraphs first
        paragraphs = text.split('\n\n')
        
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph
            else:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    async def _add_ontology_concepts(
        self, 
        chunks: List[DocumentChunk], 
        classification: DocumentClassification
    ) -> List[DocumentChunk]:
        """Add ontology concepts to chunks."""
        if not self.ontology or not self.nlp:
            return chunks
        
        for chunk in chunks:
            # Extract entities from chunk content
            doc = self.nlp(chunk.content)
            entities = [ent.text for ent in doc.ents]
            
            # Map entities to ontology concepts
            concepts = []
            for entity in entities:
                if entity.lower() in [cls.name.lower() for cls in self.ontology.classes.values()]:
                    concepts.append(entity)
            
            # Add domain-specific keywords
            domain_keywords = classification.key_entities
            for keyword in domain_keywords:
                if keyword.lower() in chunk.content.lower():
                    concepts.append(keyword)
            
            chunk.ontology_concepts = list(set(concepts))
        
        return chunks
    
    async def _generate_embeddings(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """Generate embeddings for all chunks."""
        for chunk in chunks:
            try:
                if self.embedding_model:
                    # Use SentenceTransformer if available
                    embedding = self.embedding_model.encode(chunk.content).tolist()
                    chunk.embeddings = embedding
                else:
                    # Simple fallback: use basic word count vector
                    self.logger.warning("Using fallback embedding method")
                    chunk.embeddings = self._generate_fallback_embedding(chunk.content)
            except Exception as e:
                self.logger.error(f"Error generating embeddings: {str(e)}")
                chunk.embeddings = None
        
        return chunks
    
    def _generate_fallback_embedding(self, text: str) -> List[float]:
        """Generate a simple fallback embedding."""
        import hashlib
        
        # Create a simple hash-based embedding (384 dimensions to match sentence-transformers)
        text_hash = hashlib.md5(text.encode()).hexdigest()
        # Convert hex to numbers and normalize
        hash_numbers = [int(text_hash[i:i+2], 16) for i in range(0, len(text_hash), 2)]
        
        # Extend to 384 dimensions
        embedding = []
        for i in range(384):
            embedding.append(hash_numbers[i % len(hash_numbers)] / 255.0)
        
        return embedding
