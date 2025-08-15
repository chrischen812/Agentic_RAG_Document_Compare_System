"""
Gemini API client service for AI-powered analysis and generation.
"""
import json
import logging
from typing import Dict, List, Any, Optional
from google import genai
from google.genai import types
from pydantic import BaseModel

from app.core.config import settings

class AnalysisResult(BaseModel):
    """Structured analysis result from Gemini."""
    summary: str
    key_points: List[str]
    insights: List[str]
    confidence: float

class ComparisonResult(BaseModel):
    """Structured comparison result from Gemini."""
    similarities: List[str]
    differences: List[str]
    key_insights: List[str]
    overall_analysis: str
    confidence: float

class GeminiClient:
    """Service for interacting with Gemini API for analysis tasks."""
    
    def __init__(self):
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.logger = logging.getLogger(__name__)
    
    async def analyze_content(
        self,
        content: str,
        analysis_type: str = "general",
        context: Optional[Dict[str, Any]] = None
    ) -> AnalysisResult:
        """Analyze content using Gemini for insights and understanding."""
        try:
            system_prompt = self._get_analysis_system_prompt(analysis_type, context)
            user_prompt = f"""
            Analyze the following content:
            
            {content}
            
            Provide a comprehensive analysis with:
            1. A clear summary
            2. Key points extracted from the content
            3. Important insights and implications
            4. Confidence score (0.0 to 1.0)
            
            Focus on actionable insights and important details that would be valuable for understanding and comparison.
            """
            
            response = self.client.models.generate_content(
                model=settings.gemini_model,
                contents=[
                    types.Content(role="user", parts=[types.Part(text=user_prompt)])
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    response_schema=AnalysisResult,
                    temperature=settings.gemini_temperature,
                    max_output_tokens=settings.gemini_max_tokens
                ),
            )
            
            if response.text:
                data = json.loads(response.text)
                return AnalysisResult(**data)
            else:
                raise ValueError("Empty response from Gemini")
                
        except Exception as e:
            self.logger.error(f"Error analyzing content: {str(e)}")
            return AnalysisResult(
                summary="Analysis failed",
                key_points=[],
                insights=[],
                confidence=0.0
            )
    
    async def compare_documents(
        self,
        document1_content: str,
        document2_content: str,
        comparison_context: Optional[Dict[str, Any]] = None
    ) -> ComparisonResult:
        """Compare two documents using Gemini with human-like analysis."""
        try:
            # Enhanced system prompt for human-like comparison
            context = comparison_context or {}
            domain = context.get("domain", "general")
            doc1_name = context.get("document1_name", "Document 1")
            doc2_name = context.get("document2_name", "Document 2")
            focus_areas = context.get("focus_areas", [])
            ontology_context = context.get("ontology_context", "")
            
            domain_expertise = {
                "healthcare": "healthcare insurance expert specializing in plan comparisons, coverage analysis, and patient cost evaluation",
                "legal": "legal document analyst with expertise in contract comparison and regulatory compliance",
                "financial": "financial analyst specializing in investment comparison and risk assessment"
            }
            
            expert_role = domain_expertise.get(domain, "document analysis expert")
            
            system_prompt = f"""
            You are a {expert_role} providing human-like document comparison analysis.
            
            Your goal is to help someone understand the practical differences between these documents in a way that's:
            - Specific and detailed (use exact values, percentages, amounts)
            - Human-like and conversational (as if explaining to a friend)
            - Actionable (what does this mean for the person's decisions?)
            - Focused on what matters most in real life
            
            Ontological Context: {ontology_context}
            
            When comparing, emphasize:
            - Specific numeric differences (costs, percentages, limits)
            - Practical implications ("This means you would pay $X more per year")
            - Real-world scenarios ("If you visit a specialist monthly, this difference would cost you...")
            - Clear recommendations based on different needs or situations
            """
            
            focus_instruction = ""
            if focus_areas:
                focus_instruction = f"\nPay special attention to these areas: {', '.join(focus_areas)}"
            
            user_prompt = f"""
            Please compare these two documents in a detailed, human-like way:
            
            **{doc1_name}:**
            {document1_content[:2000]}
            
            **{doc2_name}:**
            {document2_content[:2000]}
            
            {focus_instruction}
            
            Provide your analysis in this format:
            
            **SIMILARITIES** (3-5 specific points):
            - Use exact details from both documents
            - Explain what these similarities mean practically
            
            **DIFFERENCES** (3-7 specific points):
            - Include specific numbers, percentages, or amounts
            - Explain the real-world impact of each difference
            - Use language like "Document A costs $X while Document B costs $Y, meaning you'd save/pay $Z more"
            
            **KEY INSIGHTS** (2-4 actionable insights):
            - What do these differences actually mean for someone choosing between these options?
            - Which document might be better for different types of people or situations?
            - Any important trade-offs or considerations?
            
            **OVERALL ANALYSIS** (2-3 sentences):
            - Summary of which document offers what advantages
            - Bottom-line recommendation or key consideration
            
            Be specific, use actual numbers from the documents, and explain things in everyday language.
            """
            
            response = self.client.models.generate_content(
                model=settings.gemini_model,
                contents=[
                    types.Content(role="user", parts=[types.Part(text=user_prompt)])
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    response_schema=ComparisonResult,
                    temperature=0.3,  # Lower temperature for more consistent results
                    max_output_tokens=settings.gemini_max_tokens
                ),
            )
            
            if response.text:
                data = json.loads(response.text)
                result = ComparisonResult(**data)
                
                # Enhance confidence based on content quality
                if result.similarities and result.differences and result.overall_analysis:
                    result.confidence = min(0.95, result.confidence + 0.1)
                
                return result
            else:
                raise ValueError("Empty response from Gemini")
                
        except Exception as e:
            self.logger.error(f"Error comparing documents: {str(e)}")
            return ComparisonResult(
                similarities=["Both documents contain similar structural information"],
                differences=["Documents have distinct content and specific details that vary"],
                key_insights=["A detailed comparison would require access to the full document content"],
                overall_analysis="Unable to perform detailed comparison due to processing limitations. Please try again or ensure documents are properly uploaded.",
                confidence=0.3
            )
    
    async def generate_insights(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        domain: Optional[str] = None
    ) -> str:
        """Generate insights based on query and retrieved context with enhanced ontological reasoning."""
        try:
            # Prepare context from chunks with ontological enhancement
            context_parts = []
            ontology_context = ""
            
            for chunk in context_chunks[:5]:  # Limit to top 5 chunks
                content = chunk.get("content", "")
                metadata = chunk.get("metadata", {})
                
                # Get ontological context if available
                chunk_ontology = chunk.get("ontology_context", "")
                if chunk_ontology and not ontology_context:
                    ontology_context = chunk_ontology
                
                if content:
                    source_info = f"Source: {metadata.get('filename', 'unknown')} (Page {metadata.get('page_number', 'unknown')})"
                    context_parts.append(f"{source_info}\n{content}")
            
            context_text = "\n\n---\n\n".join(context_parts)
            
            # Enhanced system prompt with ontological reasoning
            domain_expertise = {
                "healthcare": "healthcare insurance, medical coverage, patient financial responsibilities, and insurance plan structures",
                "legal": "legal documents, contracts, regulatory compliance, and legal terminology",
                "financial": "financial analysis, investments, risk assessment, and financial planning"
            }
            
            expertise_area = domain_expertise.get(domain, "general document analysis")
            
            system_prompt = f"""
            You are an expert analyst specializing in {expertise_area}.
            Your expertise includes understanding complex relationships between concepts and providing intelligent, contextual insights.
            
            Guidelines:
            - Use the ontological context to provide deeper understanding
            - Explain relationships between concepts (e.g., how premiums relate to deductibles)
            - Provide practical implications and actionable advice
            - Base answers strictly on the provided context
            - Include specific values and exact references from documents
            - If information is missing, clearly state what additional information would be helpful
            - Structure responses with clear sections for better readability
            """
            
            user_prompt = f"""
            ONTOLOGICAL CONTEXT:
            {ontology_context}
            
            DOCUMENT CONTEXT:
            {context_text}
            
            USER QUESTION: {query}
            
            Using your expertise and the ontological context, provide a comprehensive response that includes:
            
            **DIRECT ANSWER:**
            - Clear answer to the user's question with specific details from documents
            
            **CONTEXTUAL INSIGHTS:**
            - Relationships between concepts and practical implications
            - Important considerations or trade-offs
            
            **SOURCE REFERENCES:**
            - Exact document and page references for all information
            
            **RECOMMENDATIONS:**
            - Actionable advice based on the information
            - What to look for or consider next
            
            Format your response clearly and use the ontological context to provide more intelligent explanations.
            """
            
            response = self.client.models.generate_content(
                model=settings.gemini_model,
                contents=[
                    types.Content(role="user", parts=[types.Part(text=user_prompt)])
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=settings.gemini_temperature,
                    max_output_tokens=settings.gemini_max_tokens
                ),
            )
            
            return response.text if response.text else "Unable to generate insights"
            
        except Exception as e:
            self.logger.error(f"Error generating insights: {str(e)}")
            return f"Error generating insights: {str(e)}"
    
    def _get_analysis_system_prompt(self, analysis_type: str, context: Optional[Dict[str, Any]]) -> str:
        """Get system prompt for content analysis."""
        base_prompt = "You are an expert document analyst with deep knowledge across multiple domains."
        
        if analysis_type == "healthcare":
            return f"{base_prompt} Specialize in healthcare documents, insurance policies, medical records, and healthcare terminology."
        elif analysis_type == "legal":
            return f"{base_prompt} Specialize in legal documents, contracts, agreements, and legal terminology."
        elif analysis_type == "financial":
            return f"{base_prompt} Specialize in financial documents, reports, investment materials, and financial terminology."
        else:
            return f"{base_prompt} Analyze documents with general expertise across multiple domains."
    
    def _get_comparison_system_prompt(self, context: Optional[Dict[str, Any]]) -> str:
        """Get system prompt for document comparison."""
        domain = context.get('domain', 'general') if context else 'general'
        
        base_prompt = f"""
        You are an expert comparative analyst specializing in {domain} documents.
        Your task is to perform detailed comparisons between documents, identifying:
        - Key similarities and differences
        - Important implications of those differences
        - Actionable insights for decision-making
        
        Be thorough, objective, and focus on substantive differences that matter.
        """
        
        if domain == "healthcare":
            return f"{base_prompt} Focus on coverage differences, benefit variations, limitations, exclusions, and policy terms."
        elif domain == "legal":
            return f"{base_prompt} Focus on contractual differences, legal obligations, rights, responsibilities, and compliance requirements."
        elif domain == "financial":
            return f"{base_prompt} Focus on financial metrics, investment terms, risk factors, and performance indicators."
        else:
            return base_prompt
