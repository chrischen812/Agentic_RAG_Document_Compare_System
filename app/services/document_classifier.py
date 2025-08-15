"""
AI-powered document classification using Gemini API.
"""
import json
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from google import genai
from google.genai import types
from pydantic import BaseModel

from app.core.config import settings
from app.services.pdf_parser import ParsedContent

@dataclass
class DocumentClassification:
    """Document classification result."""
    domain: str
    document_type: str
    confidence: float
    key_entities: List[str]
    metadata: Dict[str, any]
    ontology_mapping: Dict[str, str]

class ClassificationSchema(BaseModel):
    """Pydantic schema for structured classification response."""
    domain: str
    document_type: str
    confidence: float
    key_entities: List[str]
    metadata: Dict[str, str]
    ontology_mapping: Dict[str, str]

class DocumentClassifier:
    """AI-powered document classifier using Gemini."""
    
    def __init__(self):
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.logger = logging.getLogger(__name__)
    
    async def classify(self, parsed_content: ParsedContent) -> DocumentClassification:
        """Classify document using AI analysis."""
        try:
            # Prepare content for classification
            content_summary = self._prepare_content_summary(parsed_content)
            
            # Get classification from Gemini
            classification_data = await self._classify_with_gemini(content_summary)
            
            # Create classification object
            classification = DocumentClassification(
                domain=classification_data.domain,
                document_type=classification_data.document_type,
                confidence=classification_data.confidence,
                key_entities=classification_data.key_entities,
                metadata=classification_data.metadata,
                ontology_mapping=classification_data.ontology_mapping
            )
            
            return classification
            
        except Exception as e:
            self.logger.error(f"Error classifying document: {str(e)}")
            # Return default classification on error
            return DocumentClassification(
                domain="general",
                document_type="unknown",
                confidence=0.0,
                key_entities=[],
                metadata={},
                ontology_mapping={}
            )
    
    def _prepare_content_summary(self, parsed_content: ParsedContent) -> str:
        """Prepare content summary for classification."""
        summary_parts = []
        
        # Add metadata
        summary_parts.append(f"Filename: {parsed_content.metadata.get('filename', 'unknown')}")
        summary_parts.append(f"Pages: {parsed_content.metadata.get('page_count', 0)}")
        
        # Add text sample (first 2000 characters)
        text_sample = ""
        if parsed_content.text and isinstance(parsed_content.text, str):
            text_sample = parsed_content.text[:2000]
        elif hasattr(parsed_content, 'pages') and parsed_content.pages:
            # Extract text from pages if direct text is not available
            page_texts = []
            for page in parsed_content.pages[:3]:  # First 3 pages
                if isinstance(page, dict) and 'text' in page and page['text']:
                    page_texts.append(str(page['text']))
            text_sample = " ".join(page_texts)[:2000]
        
        if text_sample:
            # Clean the text sample to remove None values
            text_sample = str(text_sample).replace('None', '').strip()
            summary_parts.append(f"Text sample: {text_sample}")
        
        # Add table information
        if parsed_content.tables:
            table_info = []
            for table in parsed_content.tables[:3]:  # First 3 tables
                headers = table.get('headers', [])
                # Ensure headers are strings and not None
                clean_headers = [str(h) for h in headers if h is not None][:5]
                if clean_headers:
                    table_info.append(f"Table with headers: {', '.join(clean_headers)}")
            if table_info:
                summary_parts.append(f"Tables: {'; '.join(table_info)}")
        
        # Add structure information
        structure = parsed_content.structure
        summary_parts.append(f"Document structure: {structure.get('document_type', 'unknown')}")
        if structure.get('sections'):
            section_titles = [s['title'] for s in structure['sections'][:5]]
            summary_parts.append(f"Sections: {', '.join(section_titles)}")
        
        return "\n".join(summary_parts)
    
    async def _classify_with_gemini(self, content_summary: str) -> ClassificationSchema:
        """Use Gemini to classify the document."""
        system_prompt = """
        You are an expert document classifier with knowledge across multiple domains.
        Analyze the provided document content and classify it accurately.
        
        DOMAINS to choose from:
        - healthcare: Medical documents, insurance policies, health records, treatment plans
        - legal: Contracts, agreements, legal documents, terms and conditions
        - financial: Financial reports, investment documents, banking information, budgets
        - academic: Research papers, educational content, academic reports
        - general: Other document types
        
        DOCUMENT TYPES (examples):
        Healthcare: insurance_policy, medical_record, treatment_plan, health_report
        Legal: contract, agreement, terms_of_service, legal_brief
        Financial: financial_report, investment_portfolio, bank_statement, budget
        Academic: research_paper, thesis, educational_material, academic_report
        General: manual, guide, report, presentation
        
        Extract key entities relevant to the domain (e.g., for healthcare: coverage types, medical conditions, etc.)
        
        Provide ontology mapping suggestions for important concepts found in the document.
        
        Return confidence as a float between 0.0 and 1.0.
        """
        
        user_prompt = f"""
        Classify the following document:
        
        {content_summary}
        
        Respond with JSON in the exact format:
        {{
            "domain": "healthcare|legal|financial|academic|general",
            "document_type": "specific_document_type",
            "confidence": 0.95,
            "key_entities": ["entity1", "entity2", "entity3"],
            "metadata": {{
                "primary_topic": "main topic",
                "complexity": "low|medium|high",
                "language": "detected language"
            }},
            "ontology_mapping": {{
                "concept1": "ontology_class1",
                "concept2": "ontology_class2"
            }}
        }}
        """
        
        try:
            response = self.client.models.generate_content(
                model=settings.gemini_model,
                contents=[
                    types.Content(role="user", parts=[types.Part(text=user_prompt)])
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    temperature=settings.gemini_temperature,
                    max_output_tokens=settings.gemini_max_tokens
                ),
            )
            
            if response.text:
                data = json.loads(response.text)
                return ClassificationSchema(**data)
            else:
                raise ValueError("Empty response from Gemini")
                
        except Exception as e:
            self.logger.error(f"Error in Gemini classification: {str(e)}")
            # Return default classification
            return ClassificationSchema(
                domain="general",
                document_type="unknown",
                confidence=0.0,
                key_entities=[],
                metadata={"error": str(e)},
                ontology_mapping={}
            )
