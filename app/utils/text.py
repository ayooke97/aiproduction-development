import re
from typing import Dict, List, Any, Optional
from app.core.logging import get_logger

logger = get_logger(__name__)


class IndonesianTextProcessor:
    """Utility class for processing Indonesian text."""
    
    def __init__(self):
        """Initialize the text processor."""
        self.stemmer = None
        self.has_stemmer = False
        
        # Initialize Sastrawi stemmer if available
        try:
            from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
            factory = StemmerFactory()
            self.stemmer = factory.create_stemmer()
            self.has_stemmer = True
            logger.info("Sastrawi stemmer initialized successfully")
        except ImportError:
            logger.warning("Sastrawi not found. Indonesian stemming will be disabled.")
        except Exception as e:
            logger.error(f"Error initializing Sastrawi stemmer: {str(e)}")
        
        # Legal terms dictionary (can be expanded)
        self.legal_terms = {
            "hak": ["hak", "hak asasi"],
            "ulayat": ["ulayat", "hak ulayat", "tanah ulayat", "tanah adat"],
            "tanah": ["tanah", "pertanahan", "agraria"],
            "adat": ["adat", "hukum adat", "masyarakat adat"],
            "hukum": ["hukum", "peraturan", "undang-undang"],
            "undang": ["undang-undang", "peraturan"],
            "peraturan": ["peraturan", "regulasi"],
            "pemerintah": ["pemerintah", "pemerintahan"],
            "keputusan": ["keputusan", "ketetapan"],
            "menteri": ["menteri", "kementerian"],
            "presiden": ["presiden", "kepresidenan"],
            "agraria": ["agraria", "pertanahan"],
            "pertanahan": ["pertanahan", "tanah"],
            "masyarakat": ["masyarakat", "komunitas"],
            "hutan": ["hutan", "kehutanan"],
            "wilayah": ["wilayah", "area", "kawasan"],
            "daerah": ["daerah", "area", "wilayah"],
            "provinsi": ["provinsi", "daerah"],
            "kabupaten": ["kabupaten", "daerah"],
            "kota": ["kota", "perkotaan"]
        }
    
    def stem_text(self, text: str) -> str:
        """
        Stem Indonesian text using Sastrawi.
        
        Args:
            text: The text to stem
            
        Returns:
            Stemmed text
        """
        if not self.has_stemmer:
            return text
            
        try:
            return self.stemmer.stem(text)
        except Exception as e:
            logger.error(f"Error stemming text: {str(e)}")
            return text
    
    def enhance_query_with_legal_terms(self, query: str) -> str:
        """
        Enhance query with related legal terms.
        
        Args:
            query: The original query
            
        Returns:
            Enhanced query with additional legal terms
        """
        try:
            # Process the query (stem if available)
            processed_query = self.stem_text(query.lower()) if self.has_stemmer else query.lower()
            
            # Find matching legal terms
            additional_terms = set()
            for term in processed_query.split():
                if term in self.legal_terms:
                    # Add related terms
                    for related_term in self.legal_terms[term]:
                        additional_terms.add(related_term)
            
            # Add relevant legal terms to the query
            enhanced_query = query
            for term in additional_terms:
                if term.lower() not in query.lower():
                    enhanced_query += f" {term}"
            
            return enhanced_query
        except Exception as e:
            logger.error(f"Error enhancing query: {str(e)}")
            return query
    
    def extract_keywords(self, text: str, max_keywords: int = 5) -> List[str]:
        """
        Extract keywords from text without using external libraries.
        
        Args:
            text: The text to extract keywords from
            max_keywords: Maximum number of keywords to extract
            
        Returns:
            List of extracted keywords
        """
        # Remove special characters and extra whitespace
        cleaned_text = re.sub(r'[^\w\s]', ' ', text)
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip().lower()
        
        # Split into words
        words = cleaned_text.split()
        
        # Count word frequency
        word_counts = {}
        for word in words:
            if len(word) > 3:  # Only consider words longer than 3 characters
                word_counts[word] = word_counts.get(word, 0) + 1
        
        # Sort by frequency
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Get top keywords
        keywords = [word for word, count in sorted_words[:max_keywords]]
        
        return keywords
    
    def clean_html(self, html_text: str) -> str:
        """
        Clean HTML tags from text.
        
        Args:
            html_text: Text with potential HTML tags
            
        Returns:
            Cleaned text
        """
        # Remove HTML tags
        clean_text = re.sub(r'<[^>]+>', ' ', html_text)
        # Remove extra whitespace
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        return clean_text
    
    def normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace in text.
        
        Args:
            text: Text to normalize
            
        Returns:
            Text with normalized whitespace
        """
        return re.sub(r'\s+', ' ', text).strip()
    
    def truncate_text(self, text: str, max_length: int = 1000, add_ellipsis: bool = True) -> str:
        """
        Truncate text to a maximum length.
        
        Args:
            text: Text to truncate
            max_length: Maximum length of the truncated text
            add_ellipsis: Whether to add ellipsis (...) if truncated
            
        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text
            
        # Truncate at the last space before max_length
        truncated = text[:max_length]
        last_space = truncated.rfind(' ')
        
        if last_space > 0:
            truncated = truncated[:last_space]
            
        if add_ellipsis:
            truncated += "..."
            
        return truncated