"""
Advanced PDF parsing service with table extraction capabilities.
"""
import io
import logging
from typing import Dict, List, Any, Optional
import pdfplumber
import pandas as pd
from dataclasses import dataclass

@dataclass
class ParsedContent:
    """Container for parsed PDF content."""
    text: str
    tables: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    pages: List[Dict[str, Any]]
    structure: Dict[str, Any]

class PDFParser:
    """Advanced PDF parser with semantic structure recognition."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def parse(self, file_content: io.BytesIO, filename: str) -> ParsedContent:
        """Parse PDF with advanced table extraction and structure recognition."""
        try:
            with pdfplumber.open(file_content) as pdf:
                # Extract metadata
                metadata = self._extract_metadata(pdf, filename)
                
                # Process each page
                pages = []
                all_text = []
                all_tables = []
                
                for page_num, page in enumerate(pdf.pages):
                    page_data = await self._process_page(page, page_num)
                    pages.append(page_data)
                    all_text.append(page_data['text'])
                    all_tables.extend(page_data['tables'])
                
                # Combine all text
                full_text = '\n\n'.join(all_text)
                
                # Analyze document structure
                structure = self._analyze_structure(pages, pdf)
                
                return ParsedContent(
                    text=full_text,
                    tables=all_tables,
                    metadata=metadata,
                    pages=pages,
                    structure=structure
                )
                
        except Exception as e:
            self.logger.error(f"Error parsing PDF {filename}: {str(e)}")
            raise Exception(f"Failed to parse PDF: {str(e)}")
    
    def _extract_metadata(self, pdf, filename: str) -> Dict[str, Any]:
        """Extract comprehensive metadata from PDF."""
        metadata = {
            'filename': filename,
            'page_count': len(pdf.pages),
            'title': '',
            'author': '',
            'subject': '',
            'creator': '',
            'creation_date': None,
            'modification_date': None
        }
        
        # Extract PDF metadata if available
        if pdf.metadata:
            metadata.update({
                'title': pdf.metadata.get('Title', ''),
                'author': pdf.metadata.get('Author', ''),
                'subject': pdf.metadata.get('Subject', ''),
                'creator': pdf.metadata.get('Creator', ''),
                'creation_date': pdf.metadata.get('CreationDate'),
                'modification_date': pdf.metadata.get('ModDate')
            })
        
        return metadata
    
    async def _process_page(self, page, page_num: int) -> Dict[str, Any]:
        """Process individual page with text and table extraction."""
        page_data = {
            'page_number': page_num + 1,
            'text': '',
            'tables': [],
            'images': [],
            'bbox': page.bbox,
            'rotation': page.rotation
        }
        
        # Extract text with position information
        text_objects = page.extract_text_lines()
        page_text = []
        
        for text_obj in text_objects:
            page_text.append(text_obj.get('text', ''))
        
        page_data['text'] = '\n'.join(page_text)
        
        # Extract tables with advanced detection
        tables = self._extract_tables_advanced(page)
        page_data['tables'] = tables
        
        # Extract images metadata
        if hasattr(page, 'images'):
            page_data['images'] = [
                {
                    'bbox': img.get('bbox', []),
                    'width': img.get('width', 0),
                    'height': img.get('height', 0)
                }
                for img in page.images
            ]
        
        return page_data
    
    def _extract_tables_advanced(self, page) -> List[Dict[str, Any]]:
        """Advanced table extraction with structure preservation."""
        tables = []
        
        try:
            # Extract tables using multiple strategies
            detected_tables = page.extract_tables()
            
            for table_idx, table in enumerate(detected_tables):
                if not table or len(table) < 2:  # Skip empty or single-row tables
                    continue
                
                # Clean table data first
                if not table or not table[0]:
                    continue
                    
                # Clean headers - remove None values and ensure strings
                headers = []
                for header in table[0]:
                    if header is not None:
                        headers.append(str(header).strip())
                    else:
                        headers.append(f"Column_{len(headers)}")
                
                # Clean data rows
                clean_rows = []
                for row in table[1:]:
                    clean_row = []
                    for cell in row:
                        if cell is not None:
                            clean_row.append(str(cell).strip())
                        else:
                            clean_row.append("")
                    clean_rows.append(clean_row)
                
                if not clean_rows:
                    continue
                
                # Convert to DataFrame with clean data
                df = pd.DataFrame(clean_rows, columns=headers)
                
                # Clean the dataframe
                df = df.dropna(how='all')  # Remove completely empty rows
                df = df.fillna('')  # Fill NaN with empty strings
                
                # Extract table metadata
                table_info = {
                    'table_id': f"table_{table_idx}",
                    'headers': headers,  # Use cleaned headers instead
                    'data': df.to_dict('records'),
                    'row_count': len(df),
                    'column_count': len(df.columns),
                    'bbox': None,  # Would need more advanced detection for bbox
                    'structure_type': self._classify_table_structure(df)
                }
                
                tables.append(table_info)
                
        except Exception as e:
            self.logger.warning(f"Error extracting tables from page: {str(e)}")
        
        return tables
    
    def _classify_table_structure(self, df: pd.DataFrame) -> str:
        """Classify the type of table structure."""
        if df.empty:
            return "empty"
        
        # Simple heuristics for table classification
        if len(df.columns) == 2:
            return "key_value"
        elif len(df.columns) > 5:
            return "complex_data"
        elif any(col and col.lower() in ['name', 'description', 'value', 'amount'] for col in df.columns if col):
            return "structured_data"
        else:
            return "general_table"
    
    def _analyze_structure(self, pages: List[Dict], pdf) -> Dict[str, Any]:
        """Analyze overall document structure."""
        structure = {
            'document_type': 'unknown',
            'has_tables': any(page['tables'] for page in pages),
            'has_images': any(page['images'] for page in pages),
            'total_tables': sum(len(page['tables']) for page in pages),
            'total_images': sum(len(page['images']) for page in pages),
            'text_density': self._calculate_text_density(pages),
            'sections': self._identify_sections(pages)
        }
        
        # Classify document type based on structure
        structure['document_type'] = self._classify_document_type(structure, pages)
        
        return structure
    
    def _calculate_text_density(self, pages: List[Dict]) -> float:
        """Calculate text density across pages."""
        total_chars = sum(len(page['text']) for page in pages)
        total_pages = len(pages)
        return total_chars / max(total_pages, 1)
    
    def _identify_sections(self, pages: List[Dict]) -> List[Dict[str, Any]]:
        """Identify potential document sections."""
        sections = []
        
        for page in pages:
            lines = page['text'].split('\n')
            
            for line in lines:
                stripped = line.strip()
                if len(stripped) > 0:
                    # Simple heuristic for section headers
                    if (stripped.isupper() or 
                        stripped.endswith(':') or 
                        any(word in stripped.lower() for word in ['section', 'chapter', 'part'])):
                        sections.append({
                            'title': stripped,
                            'page': page['page_number'],
                            'type': 'header'
                        })
        
        return sections
    
    def _classify_document_type(self, structure: Dict, pages: List[Dict]) -> str:
        """Classify document type based on content analysis."""
        text_sample = ' '.join(page['text'][:500] for page in pages[:3]).lower()
        
        # Keywords for different document types
        healthcare_keywords = ['insurance', 'coverage', 'medical', 'health', 'policy', 'benefits', 'claims']
        legal_keywords = ['contract', 'agreement', 'terms', 'conditions', 'legal', 'liability', 'clause']
        financial_keywords = ['financial', 'investment', 'portfolio', 'income', 'expense', 'budget', 'revenue']
        
        # Count keyword matches
        healthcare_score = sum(1 for kw in healthcare_keywords if kw in text_sample)
        legal_score = sum(1 for kw in legal_keywords if kw in text_sample)
        financial_score = sum(1 for kw in financial_keywords if kw in text_sample)
        
        # Determine document type
        scores = {
            'healthcare': healthcare_score,
            'legal': legal_score,
            'financial': financial_score
        }
        
        max_score = max(scores.values())
        if max_score == 0:
            return 'general'
        
        return max(scores, key=scores.get)
