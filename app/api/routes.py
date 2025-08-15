"""
FastAPI routes for the Agentic RAG System.
"""
import io
import json
from typing import List, Optional
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Request
from fastapi.responses import JSONResponse

from app.models.schemas import (
    DocumentUploadResponse, QueryRequest, QueryResponse, 
    ComparisonRequest, ComparisonResponse, DocumentInfo
)
from app.services.pdf_parser import PDFParser
from app.services.document_classifier import DocumentClassifier
from app.services.chunking_service import ChunkingService
from app.agents.rag_agent import RAGAgent
from app.agents.comparative_agent import ComparativeAgent

router = APIRouter()

def get_services(request: Request):
    """Dependency to get services from app state."""
    return {
        "vector_store": request.app.state.vector_store,
        "ontology_manager": request.app.state.ontology_manager
    }

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    services = Depends(get_services)
):
    """Upload and process a PDF document."""
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Read file content
        content = await file.read()
        
        # Parse PDF
        pdf_parser = PDFParser()
        parsed_content = await pdf_parser.parse(io.BytesIO(content), file.filename)
        
        # Classify document
        classifier = DocumentClassifier()
        classification = await classifier.classify(parsed_content)
        
        # Get appropriate ontology
        ontology_manager = services["ontology_manager"]
        ontology = await ontology_manager.get_ontology_for_domain(classification.domain)
        
        # Chunk document
        chunking_service = ChunkingService(ontology)
        chunks = await chunking_service.chunk_document(parsed_content, classification)
        
        # Store in vector database
        vector_store = services["vector_store"]
        document_id = await vector_store.store_document(
            filename=file.filename,
            chunks=chunks,
            classification=classification,
            ontology_mapping=ontology
        )
        
        return DocumentUploadResponse(
            document_id=document_id,
            filename=file.filename,
            classification={
                "domain": classification.domain,
                "document_type": classification.document_type,
                "confidence": classification.confidence,
                "key_entities": classification.key_entities,
                "metadata": classification.metadata,
                "ontology_mapping": classification.ontology_mapping
            },
            chunks_created=len(chunks),
            status="success",
            message=f"Document processed successfully with {len(chunks)} chunks"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

@router.post("/query", response_model=QueryResponse)
async def query_documents(
    query_request: QueryRequest,
    services = Depends(get_services)
):
    """Query the RAG system with intelligent retrieval and reasoning."""
    try:
        # Initialize RAG agent
        rag_agent = RAGAgent(
            vector_store=services["vector_store"],
            ontology_manager=services["ontology_manager"]
        )
        
        # Process query through agent
        response = await rag_agent.process_query(query_request)
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@router.post("/compare", response_model=ComparisonResponse)
async def compare_documents(
    comparison_request: ComparisonRequest,
    services = Depends(get_services)
):
    """Perform intelligent comparative analysis between documents."""
    try:
        # Initialize comparative agent
        comparative_agent = ComparativeAgent(
            vector_store=services["vector_store"],
            ontology_manager=services["ontology_manager"]
        )
        
        # Perform comparison
        comparison = await comparative_agent.compare_documents(comparison_request)
        
        return comparison
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error comparing documents: {str(e)}")

@router.get("/documents", response_model=List[DocumentInfo])
async def list_documents(services = Depends(get_services)):
    """List all uploaded documents with their metadata."""
    try:
        vector_store = services["vector_store"]
        documents = await vector_store.get_all_documents()
        return documents
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving documents: {str(e)}")

@router.delete("/documents/{document_id}")
async def delete_document(document_id: str, services = Depends(get_services)):
    """Delete a document and its associated chunks."""
    try:
        vector_store = services["vector_store"]
        success = await vector_store.delete_document(document_id)
        
        if success:
            return {"message": f"Document {document_id} deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Document not found")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")

@router.get("/ontologies")
async def list_ontologies(services = Depends(get_services)):
    """List available ontologies and their domains."""
    try:
        ontology_manager = services["ontology_manager"]
        ontologies = await ontology_manager.list_available_ontologies()
        return ontologies
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving ontologies: {str(e)}")
