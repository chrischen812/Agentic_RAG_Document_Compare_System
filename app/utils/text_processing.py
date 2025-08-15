"""
Text processing utilities for document analysis and preparation.
"""
import re
import string
from typing import List, Dict, Any, Optional
import nltk
from collections import Counter

class TextProcessor:
    """Utility class for text processing operations."""
    
    def __init__(self):
        self.stopwords = self._get_stopwords()
    
    def _get_stopwords(self) -> set:
        """Get stopwords, with fallback if NLTK not available."""
        try:
            nltk.download('stopwords', quiet=True)
            from nltk.corpus import stopwords
            return set(stopwords.words('english'))
        except:
            # Fallback stopwords
            return {
                'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
                'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
                'to', 'was', 'will', 'with', 'shall', 'may', 'can', 'would',
                'could', 'should', 'this', 'these', 'those', 'or', 'but', 'if'
            }
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)]', '', text)
        
        # Normalize quotes
        text = re.sub(r'["""]', '"', text)
        text = re.sub(r'['']', "'", text)
        
        return text.strip()
    
    def extract_keywords(self, text: str, top_k: int = 20) -> List[str]:
        """Extract important keywords from text."""
        if not text:
            return []
        
        # Clean and tokenize
        cleaned_text = self.clean_text(text.lower())
        words = re.findall(r'\b\w+\b', cleaned_text)
        
        # Filter out stopwords and short words
        keywords = [
            word for word in words 
            if word not in self.stopwords and len(word) > 2
        ]
        
        # Count frequency and return top keywords
        word_freq = Counter(keywords)
        return [word for word, _ in word_freq.most_common(top_k)]
    
    def extract_sentences(self, text: str) -> List[str]:
        """Extract sentences from text."""
        if not text:
            return []
        
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        
        # Clean and filter
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10:  # Filter very short sentences
                cleaned_sentences.append(sentence)
        
        return cleaned_sentences
    
    def extract_phrases(self, text: str, min_length: int = 3, max_length: int = 6) -> List[str]:
        """Extract meaningful phrases from text."""
        if not text:
            return []
        
        words = re.findall(r'\b\w+\b', text.lower())
        phrases = []
        
        for i in range(len(words) - min_length + 1):
            for length in range(min_length, min(max_length + 1, len(words) - i + 1)):
                phrase = ' '.join(words[i:i + length])
                
                # Filter out phrases with too many stopwords
                phrase_words = phrase.split()
                stopword_count = sum(1 for word in phrase_words if word in self.stopwords)
                
                if stopword_count < len(phrase_words) * 0.6:  # Less than 60% stopwords
                    phrases.append(phrase)
        
        return list(set(phrases))  # Remove duplicates
    
    def calculate_readability(self, text: str) -> Dict[str, float]:
        """Calculate readability metrics."""
        if not text:
            return {"flesch_reading_ease": 0.0, "complexity_score": 0.0}
        
        sentences = self.extract_sentences(text)
        words = re.findall(r'\b\w+\b', text)
        
        if not sentences or not words:
            return {"flesch_reading_ease": 0.0, "complexity_score": 0.0}
        
        # Basic metrics
        avg_sentence_length = len(words) / len(sentences)
        
        # Count syllables (approximation)
        syllable_count = sum(self._count_syllables(word) for word in words)
        avg_syllables_per_word = syllable_count / len(words)
        
        # Flesch Reading Ease (approximation)
        flesch_score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
        flesch_score = max(0, min(100, flesch_score))  # Clamp between 0-100
        
        # Complexity score (custom metric)
        unique_words = len(set(word.lower() for word in words))
        vocabulary_diversity = unique_words / len(words)
        complexity_score = (avg_sentence_length * 0.3 + 
                          avg_syllables_per_word * 0.4 + 
                          vocabulary_diversity * 0.3) * 10
        
        return {
            "flesch_reading_ease": round(flesch_score, 2),
            "complexity_score": round(complexity_score, 2),
            "avg_sentence_length": round(avg_sentence_length, 2),
            "avg_syllables_per_word": round(avg_syllables_per_word, 2),
            "vocabulary_diversity": round(vocabulary_diversity, 2)
        }
    
    def _count_syllables(self, word: str) -> int:
        """Approximate syllable count for a word."""
        word = word.lower()
        if len(word) <= 3:
            return 1
        
        # Remove common endings
        word = re.sub(r'(es|ed|ing|ly|er|est)$', '', word)
        
        # Count vowel groups
        vowels = 'aeiouy'
        syllable_count = 0
        prev_was_vowel = False
        
        for char in word:
            if char in vowels:
                if not prev_was_vowel:
                    syllable_count += 1
                prev_was_vowel = True
            else:
                prev_was_vowel = False
        
        # Ensure at least 1 syllable
        return max(1, syllable_count)
    
    def extract_domain_terms(self, text: str, domain: str) -> List[str]:
        """Extract domain-specific terms."""
        domain_patterns = {
            'healthcare': [
                r'\b(?:coverage|benefit|deductible|copay|premium|claim|policy|medical|health|insurance|treatment|diagnosis|procedure|medication|hospital|doctor|physician|patient|condition|disease|illness|therapy|prescription|plan|provider|network|exclusion|limitation)\b'
            ],
            'legal': [
                r'\b(?:contract|agreement|clause|term|condition|liability|obligation|right|duty|breach|damages|penalty|jurisdiction|governing|law|legal|court|dispute|arbitration|mediation|settlement|party|parties|execution|amendment|termination|notice|consent|waiver)\b'
            ],
            'financial': [
                r'\b(?:investment|portfolio|asset|liability|equity|debt|revenue|income|expense|profit|loss|balance|cash|flow|budget|forecast|risk|return|dividend|interest|principal|loan|credit|deposit|account|financial|banking|fund|market|trading|securities)\b'
            ]
        }
        
        if domain not in domain_patterns:
            return []
        
        terms = set()
        for pattern in domain_patterns[domain]:
            matches = re.findall(pattern, text.lower())
            terms.update(matches)
        
        return list(terms)
    
    def extract_numbers_and_amounts(self, text: str) -> List[Dict[str, Any]]:
        """Extract numbers, percentages, and monetary amounts."""
        extractions = []
        
        # Money patterns
        money_pattern = r'\$[\d,]+(?:\.\d{2})?'
        money_matches = re.finditer(money_pattern, text)
        for match in money_matches:
            extractions.append({
                'type': 'currency',
                'value': match.group(),
                'position': match.start()
            })
        
        # Percentage patterns
        percent_pattern = r'\d+(?:\.\d+)?%'
        percent_matches = re.finditer(percent_pattern, text)
        for match in percent_matches:
            extractions.append({
                'type': 'percentage',
                'value': match.group(),
                'position': match.start()
            })
        
        # General numbers
        number_pattern = r'\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\b'
        number_matches = re.finditer(number_pattern, text)
        for match in number_matches:
            # Skip if it's already captured as money or percentage
            if not any(abs(match.start() - ext['position']) < 5 for ext in extractions):
                extractions.append({
                    'type': 'number',
                    'value': match.group(),
                    'position': match.start()
                })
        
        return sorted(extractions, key=lambda x: x['position'])
