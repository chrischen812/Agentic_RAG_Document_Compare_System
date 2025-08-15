"""
Pydantic models for API request/response schemas.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

# Request Models
class QueryRequest(BaseModel):
    """Request model for document queries."""
    query: str = Field(..., description="The query text")
    domain_filter: Optional[str] = Field(None, description="Filter by domain (healthcare, legal, financial)")
    document_type_filter: Optional[str] = Field(None, description="Filter by document type")
    top_k: Optional[int] = Field(10, description="Number of results to return")

class ComparisonRequest(BaseModel):
    """Request model for document comparison."""
    document_ids: List[str] = Field(..., description="List of document IDs to compare")
    comparison_type: str = Field("general", description="Type of comparison (coverage, terms, structure, general)")
    focus_areas: Optional[List[str]] = Field(None, description="Specific areas to focus on in comparison")

# Response Models
class DocumentUploadResponse(BaseModel):
    """Response model for document upload."""
    document_id: str
    filename: str
    classification: Dict[str, Any]
    chunks_created: int
    status: str
    message: str

class QueryResponse(BaseModel):
    """Response model for query results."""
    answer: str
    sources: List[Dict[str, str]]
    confidence: float
    reasoning_steps: List[str]
    related_concepts: List[str]
    metadata: Dict[str, Any]

class ComparisonResponse(BaseModel):
    """Response model for document comparison."""
    comparison_id: str
    document_ids: List[str]
    similarities: List[str]
    differences: List[str]
    insights: str
    comparison_matrix: Dict[str, Any]
    confidence: float
    reasoning_steps: List[str]
    metadata: Dict[str, Any]

class DocumentInfo(BaseModel):
    """Model for document information."""
    document_id: str
    filename: str
    domain: str
    document_type: str
    chunk_count: int
    upload_date: Optional[datetime]
    classification_confidence: float

# Analysis Models
class EntityExtraction(BaseModel):
    """Model for extracted entities."""
    entity: str
    entity_type: str
    confidence: float
    context: str

class SemanticConcept(BaseModel):
    """Model for semantic concepts."""
    concept: str
    ontology_class: str
    relationships: List[str]
    frequency: int

class DocumentAnalysis(BaseModel):
    """Comprehensive document analysis."""
    document_id: str
    summary: str
    key_entities: List[EntityExtraction]
    semantic_concepts: List[SemanticConcept]
    document_structure: Dict[str, Any]
    complexity_score: float
    readability_score: float

# Ontology Models
class OntologyMapping(BaseModel):
    """Model for ontology concept mapping."""
    source_term: str
    ontology_class: str
    confidence: float
    relationship_type: str

class DomainOntology(BaseModel):
    """Model for domain ontology information."""
    domain: str
    namespace: str
    classes: List[str]
    properties: List[str]
    coverage_areas: List[str]

# Error Models
class ErrorResponse(BaseModel):
    """Model for error responses."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)

# Health Check Models
class HealthCheck(BaseModel):
    """Model for health check response."""
    status: str
    timestamp: datetime = Field(default_factory=datetime.now)
    services: Dict[str, str]
    version: str = "1.0.0"
