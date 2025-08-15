# Overview

This is a fully operational Intelligent Agentic RAG (Retrieval-Augmented Generation) System built with FastAPI and LangGraph. The system provides advanced document classification, ontological mapping, and comparative analysis capabilities for PDF documents. It uses AI agents to perform multi-step reasoning for intelligent document retrieval, analysis, and cross-document comparison.

The system integrates multiple AI services and frameworks to create a comprehensive document intelligence platform that can understand, classify, and analyze documents across healthcare Benefits domain while maintaining semantic relationships through ontological structures.



# System Architecture

## Frontend Architecture
- **Static Web Interface**: Bootstrap-based responsive UI with JavaScript for dynamic interactions
- **Real-time Updates**: Event-driven interface with modals for loading states and error handling
- **Document Management**: Interactive document list with selection capabilities for comparison
- **Progressive Enhancement**: Fallback support for various browser capabilities

## Backend Architecture
- **FastAPI Framework**: Asynchronous web framework with automatic API documentation
- **LangGraph Agents**: Multi-step reasoning agents using state graphs for complex workflows
- **Service-Oriented Design**: Modular services for PDF parsing, document classification, chunking, and vector operations
- **Dependency Injection**: FastAPI dependency system for service management and lifecycle

## AI Agent System
- **RAG Agent**: Multi-step retrieval and reasoning using LangGraph state machines
- **Comparative Agent**: Cross-document analysis with structured comparison workflows
- **Agentic Workflows**: State-based processing with validation and iteration capabilities

## Document Processing Pipeline
- **PDF Parser**: Advanced extraction using pdfplumber with table recognition
- **Semantic Chunking**: Context-aware document segmentation with overlap management
- **Document Classification**: AI-powered domain and type classification using Gemini
- **Ontological Mapping**: Knowledge graph integration for semantic relationships

## Vector Storage and Retrieval
- **ChromaDB**: Persistent vector database for document embeddings
- **Hierarchical Indexing**: Multi-level indexing by domain, type, and ontological concepts
- **Semantic Search**: Embedding-based similarity search with metadata filtering

## Knowledge Management
- **Ontology Manager**: Combines RDFLib-based programmatic ontology creation with manual refinement using Protégé, a widely adopted tool for editing and visualizing OWL and RDF schemas.
- **Domain-Specific Structures**: Maintains distinct ontologies tailored to healthcare, legal, and financial domains, enabling modular reasoning and compliance-aware modeling.
- **Concept Mapping**: Automates the linking of document content to ontological concepts, with Protégé facilitating validation, class hierarchy adjustments, and semantic consistency checks.


# External Dependencies

## AI and ML Services
- **Google Gemini API**: Primary LLM for classification, analysis, and response generation
- **Sentence Transformers**: Local embedding generation using all-MiniLM-L6-v2 model
- **spaCy**: Natural language processing for entity recognition and text analysis

## Vector Database
- **ChromaDB**: Persistent vector storage with collection management
- **Local Storage**: File-based persistence for vector embeddings and metadata

## Document Processing
- **pdfplumber**: PDF parsing with table extraction capabilities
- **pandas**: Data manipulation for structured content processing

## Knowledge Graphs
- **RDFLib**: RDF graph creation and SPARQL querying
- **owlready2**: OWL ontology manipulation and reasoning

## Web Framework
- **FastAPI**: Asynchronous web framework with OpenAPI support
- **Jinja2**: Template rendering for web interface
- **Uvicorn**: ASGI server for production deployment

## Frontend Libraries
- **Bootstrap 5**: UI component framework
- **Font Awesome**: Icon library for interface elements

## Language Processing
- **NLTK**: Text processing utilities and stopword management
- **scikit-learn**: Machine learning utilities for similarity calculations

## Agent Framework
- **LangGraph**: State graph framework for multi-step agent workflows
- **LangChain**: Tool integration and agent utilities


## Environment Variables

Create a `.env` file in the main directory:

```env
# Required
GEMINI_API_KEY=your_gemini_api_key_here

```


## Development Environment using Python native Virtual Machine 

1. **Setup and activate Virtual Environment:**
   ```bash
   # Create virtual environment
   python -m venv venv

   # Activate and you should see '(venv)'
   source venv/Scripts/activate
   ```

2. **Install dependencies:**
   ```bash
   # Navigate to Backend ## Deployment using local Virtual Machine (venv)folder
   ./setup.sh
   ```

3. **Set environment variables:**
   ```bash
   # The "GEMINI_API_KEY" is automatically loaded into the environment from the .env file via python-dotenv, so manual declaration is not required.
   ```

4. **Run the server:**
   ```bash
   # Navigate to the folder containing main.py
   uvicorn main:app --host 0.0.0.0 --port 5000 --reload
   ```

5. **Close out the server and Virtual Environment:**
   ```bash
   # Ctrl + C to terminate API, and run the following in base to terminate virtual envorment
   deactivate

   # Remove 'venv' folder under project
   rm -rf venv/
   ```



## Development Environment using Docker, refer to the "Docker" folder README

1. **Start development container:**
   ```bash
   cd docker
   docker-compose -f docker-compose.dev.yml up --build
   ```

2. **Access the application:**
   - API: http://localhost:5000
   - Documentation: http://localhost:5000/docs
