"""
LangGraph-based RAG agent for intelligent document retrieval and reasoning.
"""
import json
import logging
from typing import Dict, List, Any, Optional, TypedDict
from langgraph.graph import StateGraph, END

from app.models.schemas import QueryRequest, QueryResponse
from app.services.vector_store import VectorStore
from app.services.ontology_manager import OntologyManager
from app.services.gemini_client import GeminiClient

class AgentState(TypedDict):
    """State object for the RAG agent."""
    query: str
    domain: Optional[str]
    retrieved_chunks: List[Dict[str, Any]]
    analysis_results: List[Dict[str, Any]]
    final_response: str
    reasoning_steps: List[str]
    confidence: float
    iteration_count: int

class RAGAgent:
    """Intelligent RAG agent using LangGraph for multi-step reasoning."""
    
    def __init__(self, vector_store: VectorStore, ontology_manager: OntologyManager):
        self.vector_store = vector_store
        self.ontology_manager = ontology_manager
        self.gemini_client = GeminiClient()
        self.logger = logging.getLogger(__name__)
        
        # Build the agent graph
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """Build the LangGraph for the RAG agent."""
        # For now, we'll implement a simpler sequential workflow
        # instead of the complex LangGraph to avoid type issues
        self.workflow_steps = [
            self._analyze_query,
            self._retrieve_documents,
            self._analyze_relevance,
            self._generate_response,
            self._validate_response
        ]
        return None
    
    async def process_query(self, query_request: QueryRequest) -> QueryResponse:
        """Process a query through the RAG agent."""
        try:
            # Initialize state
            initial_state: AgentState = {
                "query": query_request.query,
                "domain": query_request.domain_filter,
                "retrieved_chunks": [],
                "analysis_results": [],
                "final_response": "",
                "reasoning_steps": [],
                "confidence": 0.0,
                "iteration_count": 0
            }
            
            # Run the agent graph
            final_state = await self._run_graph(initial_state)
            
            # Create response
            response = QueryResponse(
                answer=final_state["final_response"],
                sources=self._extract_sources(final_state["retrieved_chunks"]),
                confidence=final_state["confidence"],
                reasoning_steps=final_state["reasoning_steps"],
                related_concepts=self._extract_concepts(final_state["retrieved_chunks"]),
                metadata={
                    "iteration_count": final_state["iteration_count"],
                    "chunks_analyzed": len(final_state["retrieved_chunks"]),
                    "domain": final_state["domain"]
                }
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing query: {str(e)}")
            return QueryResponse(
                answer=f"Error processing query: {str(e)}",
                sources=[],
                confidence=0.0,
                reasoning_steps=["Error occurred during processing"],
                related_concepts=[],
                metadata={"error": str(e)}
            )
    
    async def _run_graph(self, initial_state: AgentState) -> AgentState:
        """Run the agent workflow sequentially."""
        try:
            current_state = initial_state.copy()
            
            # Execute workflow steps sequentially
            for step in self.workflow_steps:
                self.logger.info(f"Executing step: {step.__name__}")
                current_state = await step(current_state)
                
            return current_state
            
        except Exception as e:
            self.logger.error(f"Error running agent workflow: {str(e)}")
            current_state["final_response"] = f"Error in processing: {str(e)}"
            current_state["confidence"] = 0.0
            return current_state
    
    async def _analyze_query(self, state: AgentState) -> AgentState:
        """Analyze the query to understand intent and domain."""
        try:
            query = state["query"]
            reasoning_steps = state["reasoning_steps"]
            
            reasoning_steps.append("Analyzing query intent and domain")
            
            # Use Gemini to analyze query
            analysis_prompt = f"""
            Analyze this query to understand:
            1. The main intent
            2. Key concepts mentioned
            3. Most likely domain (healthcare, legal, financial, general)
            4. Type of answer expected (factual, comparative, analytical)
            
            Query: {query}
            
            Respond with JSON:
            {{
                "intent": "intent description",
                "key_concepts": ["concept1", "concept2"],
                "domain": "domain",
                "answer_type": "type"
            }}
            """
            
            # For now, use simple heuristics (replace with Gemini call in production)
            domain = state.get("domain")
            if not domain:
                # Simple domain detection
                query_lower = query.lower()
                if any(word in query_lower for word in ["insurance", "coverage", "medical", "health"]):
                    domain = "healthcare"
                elif any(word in query_lower for word in ["contract", "legal", "agreement", "terms"]):
                    domain = "legal"
                elif any(word in query_lower for word in ["financial", "investment", "portfolio", "budget"]):
                    domain = "financial"
                else:
                    domain = "general"
            
            reasoning_steps.append(f"Identified domain: {domain}")
            
            state["domain"] = domain
            state["reasoning_steps"] = reasoning_steps
            state["iteration_count"] += 1
            
            return state
            
        except Exception as e:
            self.logger.error(f"Error analyzing query: {str(e)}")
            state["reasoning_steps"].append(f"Error in query analysis: {str(e)}")
            return state
    
    async def _retrieve_documents(self, state: AgentState) -> AgentState:
        """Retrieve relevant documents from vector store."""
        try:
            query = state["query"]
            domain = state.get("domain")
            reasoning_steps = state["reasoning_steps"]
            
            reasoning_steps.append("Retrieving relevant documents")
            
            # Query vector store
            retrieved_chunks = await self.vector_store.query_similar(
                query_text=query,
                domain_filter=domain,
                top_k=10
            )
            
            reasoning_steps.append(f"Retrieved {len(retrieved_chunks)} relevant chunks")
            
            state["retrieved_chunks"] = retrieved_chunks
            state["reasoning_steps"] = reasoning_steps
            
            return state
            
        except Exception as e:
            self.logger.error(f"Error retrieving documents: {str(e)}")
            state["reasoning_steps"].append(f"Error in document retrieval: {str(e)}")
            return state
    
    async def _analyze_relevance(self, state: AgentState) -> AgentState:
        """Analyze relevance of retrieved chunks."""
        try:
            query = state["query"]
            chunks = state["retrieved_chunks"]
            reasoning_steps = state["reasoning_steps"]
            
            reasoning_steps.append("Analyzing relevance of retrieved content")
            
            # Filter chunks by relevance (simple threshold for now)
            relevant_chunks = []
            for chunk in chunks:
                # Use distance/similarity score to filter - more lenient threshold
                if chunk.get("distance") is None or chunk["distance"] < 2.0:  # More lenient threshold
                    relevant_chunks.append(chunk)
            
            # If no chunks pass the threshold, keep the top 3 anyway
            if not relevant_chunks and chunks:
                relevant_chunks = chunks[:3]
            
            reasoning_steps.append(f"Filtered to {len(relevant_chunks)} highly relevant chunks")
            
            state["retrieved_chunks"] = relevant_chunks[:5]  # Keep top 5
            state["reasoning_steps"] = reasoning_steps
            
            return state
            
        except Exception as e:
            self.logger.error(f"Error analyzing relevance: {str(e)}")
            state["reasoning_steps"].append(f"Error in relevance analysis: {str(e)}")
            return state
    
    async def _generate_response(self, state: AgentState) -> AgentState:
        """Generate response using Gemini with enhanced ontological reasoning."""
        try:
            query = state["query"]
            chunks = state["retrieved_chunks"]
            domain = state.get("domain", "healthcare")
            reasoning_steps = state["reasoning_steps"]
            
            reasoning_steps.append("Generating response using AI analysis with ontological reasoning")
            
            # Extract concepts from chunks for ontological analysis
            chunk_concepts = []
            for chunk in chunks:
                metadata = chunk.get("metadata", {})
                concepts = metadata.get("ontology_concepts", [])
                chunk_concepts.extend(concepts)
            
            # Get ontological insights for enhanced reasoning
            ontology_insights = await self._get_ontological_insights(query, chunk_concepts, domain)
            
            # Enhanced response generation with ontological context
            enhanced_chunks = []
            for chunk in chunks:
                enhanced_chunk = chunk.copy()
                enhanced_chunk["ontology_context"] = ontology_insights
                enhanced_chunks.append(enhanced_chunk)
            
            # Generate response using enhanced context
            response = await self.gemini_client.generate_insights(
                query=query,
                context_chunks=enhanced_chunks,
                domain=domain
            )
            
            # Enhanced confidence calculation including ontological factors
            base_confidence = min(1.0, len(chunks) * 0.2)
            ontology_boost = 0.1 if ontology_insights else 0.0
            confidence = min(1.0, base_confidence + ontology_boost)
            
            # Extract related concepts for enhanced understanding
            related_concepts = await self._extract_related_concepts(query, chunk_concepts, domain)
            
            reasoning_steps.append("Generated comprehensive response with ontological insights")
            
            state["final_response"] = response
            state["confidence"] = confidence
            state["related_concepts"] = related_concepts
            state["reasoning_steps"] = reasoning_steps
            
            return state
            
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            state["final_response"] = f"Error generating response: {str(e)}"
            state["confidence"] = 0.0
            state["related_concepts"] = []
            state["reasoning_steps"].append(f"Error in response generation: {str(e)}")
            return state
    
    async def _get_ontological_insights(self, query: str, concepts: List[str], domain: str) -> str:
        """Generate ontological insights for enhanced reasoning."""
        if not concepts:
            return ""
        
        try:
            insights = []
            query_lower = query.lower()
            
            if domain == "healthcare":
                # Financial concept insights
                if any(term in query_lower for term in ['premium', 'cost', 'price', 'pay']):
                    insights.append("FINANCIAL CONTEXT: Premiums are recurring monthly costs. Consider total cost including deductibles and copayments.")
                
                if any(term in query_lower for term in ['deductible']):
                    insights.append("DEDUCTIBLE CONTEXT: Annual amount paid before insurance begins covering costs. Preventive services often exempt.")
                
                if any(term in query_lower for term in ['copay', 'copayment']):
                    insights.append("COPAYMENT CONTEXT: Fixed amounts paid per service. Varies by provider type (primary care vs specialist).")
                
                if any(term in query_lower for term in ['compare', 'vs', 'versus', 'difference']):
                    insights.append("COMPARISON FRAMEWORK: Evaluate total annual cost (premiums + expected out-of-pocket) for meaningful comparisons.")
                
                # Service-specific insights
                if any(term in query_lower for term in ['primary care', 'family doctor']):
                    insights.append("PRIMARY CARE: Usually lowest copayments. Often required for specialist referrals in HMO plans.")
                
                if any(term in query_lower for term in ['specialist', 'specialty']):
                    insights.append("SPECIALIST CARE: Higher copayments than primary care. May require referrals depending on plan type.")
                
                if any(term in query_lower for term in ['emergency', 'er', 'urgent']):
                    insights.append("EMERGENCY CARE: Highest cost-sharing but no referral required. Consider urgent care for non-emergencies.")
                
                # Plan type insights
                if any(term in query_lower for term in ['hmo', 'ppo', 'plan type']):
                    insights.append("PLAN TYPES: HMO requires referrals but lower costs. PPO offers flexibility but higher premiums.")
            
            return " | ".join(insights[:4])  # Limit insights for clarity
            
        except Exception as e:
            self.logger.warning(f"Error generating ontological insights: {str(e)}")
            return ""
    
    async def _extract_related_concepts(self, query: str, concepts: List[str], domain: str) -> List[str]:
        """Extract related concepts for enhanced understanding."""
        related = set()
        
        try:
            query_lower = query.lower()
            
            if domain == "healthcare":
                # Cost-related concepts
                if any(term in query_lower for term in ['cost', 'price', 'money', 'pay', 'premium', 'deductible']):
                    related.update(["Premium", "Deductible", "Copayment", "Coinsurance", "Out-of-Pocket Maximum"])
                
                # Service-related concepts  
                if any(term in query_lower for term in ['visit', 'doctor', 'service', 'care']):
                    related.update(["Primary Care", "Specialist Care", "Emergency Services", "Preventive Care"])
                
                # Plan-related concepts
                if any(term in query_lower for term in ['plan', 'insurance', 'coverage', 'benefit']):
                    related.update(["HMO", "PPO", "EPO", "Benefits", "Provider Network"])
                
                # Medication-related concepts
                if any(term in query_lower for term in ['prescription', 'drug', 'medication', 'pharmacy']):
                    related.update(["Generic Drugs", "Brand Drugs", "Formulary", "Pharmacy Network"])
                
                # Add concepts from document content
                for concept in concepts[:10]:  # Limit processing
                    if any(term in concept.lower() for term in ['premium', 'deductible', 'copay']):
                        related.add(concept.title())
            
            return list(related)[:8]  # Limit return size
            
        except Exception as e:
            self.logger.warning(f"Error extracting related concepts: {str(e)}")
            return []
    
    async def _validate_response(self, state: AgentState) -> AgentState:
        """Validate and refine the response."""
        try:
            response = state["final_response"]
            reasoning_steps = state["reasoning_steps"]
            
            reasoning_steps.append("Validating response quality")
            
            # Simple validation - check if response is meaningful
            if len(response) < 50:
                state["confidence"] *= 0.5
                reasoning_steps.append("Response seems short, reduced confidence")
            
            if "error" in response.lower():
                state["confidence"] *= 0.3
                reasoning_steps.append("Error detected in response, reduced confidence")
            
            reasoning_steps.append("Response validation complete")
            
            state["reasoning_steps"] = reasoning_steps
            
            return state
            
        except Exception as e:
            self.logger.error(f"Error validating response: {str(e)}")
            state["reasoning_steps"].append(f"Error in response validation: {str(e)}")
            return state
    
    def _extract_sources(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Extract source information from chunks."""
        sources = []
        seen_docs = set()
        
        for chunk in chunks:
            metadata = chunk.get("metadata", {})
            filename = metadata.get("filename", "unknown")
            page = metadata.get("page_number", "unknown")
            
            doc_key = f"{filename}_{page}"
            if doc_key not in seen_docs:
                sources.append({
                    "filename": filename,
                    "page": str(page),
                    "chunk_type": metadata.get("chunk_type", "unknown")
                })
                seen_docs.add(doc_key)
        
        return sources
    
    def _extract_concepts(self, chunks: List[Dict[str, Any]]) -> List[str]:
        """Extract ontology concepts from chunks."""
        concepts = set()
        
        for chunk in chunks:
            metadata = chunk.get("metadata", {})
            chunk_concepts = metadata.get("ontology_concepts", [])
            
            if isinstance(chunk_concepts, str):
                try:
                    chunk_concepts = json.loads(chunk_concepts)
                except:
                    chunk_concepts = []
            
            if isinstance(chunk_concepts, list):
                concepts.update(chunk_concepts)
        
        return list(concepts)
