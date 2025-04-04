import pytest
from unittest.mock import MagicMock, patch

from app.utils.text import IndonesianTextProcessor


class TestIndonesianTextProcessor:
    """Tests for the IndonesianTextProcessor."""
    
    def test_initialization_without_sastrawi(self):
        """Test initialization without Sastrawi."""
        with patch("app.utils.text.IndonesianTextProcessor.has_stemmer", False):
            processor = IndonesianTextProcessor()
            assert processor.has_stemmer is False
            assert processor.stemmer is None
    
    def test_stem_text_without_stemmer(self):
        """Test stem_text method without a stemmer."""
        processor = IndonesianTextProcessor()
        processor.has_stemmer = False
        processor.stemmer = None
        
        text = "Ini adalah teks bahasa Indonesia"
        result = processor.stem_text(text)
        
        # Should return original text unchanged
        assert result == text
    
    def test_stem_text_with_stemmer(self):
        """Test stem_text method with a stemmer."""
        processor = IndonesianTextProcessor()
        
        # Mock the stemmer
        mock_stemmer = MagicMock()
        mock_stemmer.stem.return_value = "ini adalah teks bahasa indonesia"
        processor.stemmer = mock_stemmer
        processor.has_stemmer = True
        
        text = "Ini adalah teks bahasa Indonesia"
        result = processor.stem_text(text)
        
        # Should call stemmer
        mock_stemmer.stem.assert_called_once_with(text)
        assert result == "ini adalah teks bahasa indonesia"
    
    def test_enhance_query_with_legal_terms(self):
        """Test enhance_query_with_legal_terms method."""
        processor = IndonesianTextProcessor()
        
        # Test with query containing legal terms
        query = "hak tanah"
        result = processor.enhance_query_with_legal_terms(query)
        
        # Should add related legal terms for "hak" and "tanah"
        assert "hak asasi" in result
        assert "pertanahan" in result
        assert "agraria" in result
    
    def test_enhance_query_with_legal_terms_no_matches(self):
        """Test enhance_query_with_legal_terms with no matches."""
        processor = IndonesianTextProcessor()
        
        # Test with query containing no legal terms
        query = "ini adalah contoh"
        result = processor.enhance_query_with_legal_terms(query)
        
        # Should return original query unchanged
        assert result == query
    
    def test_extract_keywords(self):
        """Test extract_keywords method."""
        processor = IndonesianTextProcessor()
        
        # Test with a sample text
        text = "Peraturan daerah tentang hak tanah ulayat masyarakat adat di provinsi Papua"
        keywords = processor.extract_keywords(text, max_keywords=5)
        
        # Should extract important keywords
        assert len(keywords) <= 5
        assert "peraturan" in keywords
        assert "daerah" in keywords
        assert "tanah" in keywords
        
        # Words with <= 3 characters should be filtered out
        assert "di" not in keywords
    
    def test_clean_html(self):
        """Test clean_html method."""
        processor = IndonesianTextProcessor()
        
        # Test with HTML content
        html = "<div><h1>Judul</h1><p>Teks <b>tebal</b> dan <i>miring</i>.</p></div>"
        result = processor.clean_html(html)
        
        # Should remove HTML tags
        assert "<div>" not in result
        assert "<h1>" not in result
        assert "<p>" not in result
        assert "<b>" not in result
        assert "<i>" not in result
        
        # Should keep text content
        assert "Judul" in result
        assert "Teks" in result
        assert "tebal" in result
        assert "dan" in result
        assert "miring" in result
    
    def test_normalize_whitespace(self):
        """Test normalize_whitespace method."""
        processor = IndonesianTextProcessor()
        
        # Test with text containing excessive whitespace
        text = "  Ini    adalah  \t  teks  \n  dengan  banyak  spasi  "
        result = processor.normalize_whitespace(text)
        
        # Should normalize whitespace
        assert result == "Ini adalah teks dengan banyak spasi"
    
    def test_truncate_text(self):
        """Test truncate_text method."""
        processor = IndonesianTextProcessor()
        
        # Test with long text
        text = "Ini adalah teks yang sangat panjang dan akan dipotong pada batas maksimum."
        
        # Test with max_length less than text length
        result = processor.truncate_text(text, max_length=20, add_ellipsis=True)
        
        # Should truncate text and add ellipsis
        assert len(result) <= 23  # 20 + 3 for ellipsis
        assert result.endswith("...")
        
        # Test without ellipsis
        result = processor.truncate_text(text, max_length=20, add_ellipsis=False)
        
        # Should truncate text without ellipsis
        assert len(result) <= 20
        assert not result.endswith("...")
        
        # Test with max_length greater than text length
        result = processor.truncate_text(text, max_length=100)
        
        # Should return original text unchanged
        assert result == text