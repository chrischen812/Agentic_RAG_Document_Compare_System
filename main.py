"""
Main FastAPI application entry point for the Agentic RAG System.
"""
import os
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.requests import Request
from contextlib import asynccontextmanager

from app.api.routes import router as api_router
from app.core.config import settings
from app.services.vector_store import VectorStore
from app.services.ontology_manager import OntologyManager

# Global instances
vector_store = None
ontology_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup and cleanup on shutdown."""
    global vector_store, ontology_manager
    
    # Initialize services
    print("Initializing Agentic RAG System...")
    vector_store = VectorStore()
    await vector_store.initialize()
    
    ontology_manager = OntologyManager()
    await ontology_manager.initialize()
    
    # Store in app state for access in routes
    app.state.vector_store = vector_store
    app.state.ontology_manager = ontology_manager
    
    print("System initialized successfully!")
    yield
    
    # Cleanup
    print("Shutting down services...")
    if vector_store:
        await vector_store.close()

# Create FastAPI app with lifespan management
app = FastAPI(
    title="Intelligent Agentic RAG System",
    description="Advanced document classification, ontological mapping, and comparative analysis",
    version="1.0.0",
    lifespan=lifespan
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Include API routes
app.include_router(api_router, prefix="/api")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serve the main interface."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "vector_store": "connected" if vector_store else "disconnected",
        "ontology_manager": "loaded" if ontology_manager else "not_loaded"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5000,
        reload=True,
        log_level="info"
    )
