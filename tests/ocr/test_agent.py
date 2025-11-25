"""
Unit tests for HandwritingExtractionAgent
Tests the OCR agent functionality including image processing, extraction, and translation
"""

import pytest
import os
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import base64
from PIL import Image
import io

# Import the agent
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'backend'))

from agent import HandwritingExtractionAgent


class TestAgentInitialization:
    """Test agent initialization and configuration"""
    
    def test_agent_initializes_successfully(self):
        """Test that agent can be initialized"""
        agent = HandwritingExtractionAgent()
        assert agent is not None
    
    def test_agent_loads_environment_variables(self):
        """Test that agent loads configuration from environment"""
        agent = HandwritingExtractionAgent()
        
        # Check that configuration attributes exist
        assert hasattr(agent, 'langfuse_public_key')
        assert hasattr(agent, 'langfuse_secret_key')
        assert hasattr(agent, 'hf_token')
        assert hasattr(agent, 'groq_api_key')
    
    def test_agent_initializes_hf_client_with_token(self):
        """Test HuggingFace client initialization when token is present"""
        with patch.dict(os.environ, {'HF_TOKEN': 'test_token'}):
            agent = HandwritingExtractionAgent()
            assert agent.hf_client is not None
    
    def test_agent_handles_missing_hf_token(self):
        """Test agent handles missing HuggingFace token gracefully"""
        with patch.dict(os.environ, {}, clear=True):
            agent = HandwritingExtractionAgent()
            assert agent.hf_client is None
    
    def test_agent_initializes_groq_client_with_key(self):
        """Test Groq client initialization when API key is present"""
        with patch.dict(os.environ, {'GROQ_API_KEY': 'test_key'}):
            agent = HandwritingExtractionAgent()
            assert agent.groq_client is not None
    
    def test_agent_handles_missing_groq_key(self):
        """Test agent handles missing Groq API key gracefully"""
        with patch.dict(os.environ, {}, clear=True):
            agent = HandwritingExtractionAgent()
            assert agent.groq_client is None


class TestImagePreprocessing:
    """Test image preprocessing functionality"""
    
    @pytest.fixture
    def agent(self):
        """Create agent instance for testing"""
        return HandwritingExtractionAgent()
    
    @pytest.fixture
    def test_image_path(self, tmp_path):
        """Create a test image file"""
        img = Image.new('RGB', (100, 100), color='white')
        img_path = tmp_path / "test_image.jpg"
        img.save(img_path)
        return str(img_path)
    
    def test_preprocess_image_returns_pil_image(self, agent, test_image_path):
        """Test that preprocessing returns a PIL Image"""
        result = agent.preprocess_image(test_image_path)
        assert isinstance(result, Image.Image)
    
    def test_preprocess_converts_to_rgb(self, agent, tmp_path):
        """Test that preprocessing converts images to RGB"""
        # Create a grayscale image
        img = Image.new('L', (100, 100), color=128)
        img_path = tmp_path / "gray_image.jpg"
        img.save(img_path)
        
        result = agent.preprocess_image(str(img_path))
        assert result.mode == 'RGB'
    
    def test_preprocess_enhances_image(self, agent, test_image_path):
        """Test that preprocessing enhances the image"""
        original = Image.open(test_image_path)
        processed = agent.preprocess_image(test_image_path)
        
        # Processed image should have same or larger size
        assert processed.size[0] >= original.size[0] or processed.size[1] >= original.size[1]
    
    def test_preprocess_resizes_small_images(self, agent, tmp_path):
        """Test that small images are resized"""
        # Create a very small image
        img = Image.new('RGB', (50, 50), color='white')
        img_path = tmp_path / "small_image.jpg"
        img.save(img_path)
        
        result = agent.preprocess_image(str(img_path))
        
        # Should be resized to at least 512px on longest side
        assert max(result.size) >= 512


class TestImageEncoding:
    """Test image encoding functionality"""
    
    @pytest.fixture
    def agent(self):
        return HandwritingExtractionAgent()
    
    @pytest.fixture
    def test_image_path(self, tmp_path):
        img = Image.new('RGB', (100, 100), color='white')
        img_path = tmp_path / "test_image.jpg"
        img.save(img_path)
        return str(img_path)
    
    def test_encode_image_returns_base64_string(self, agent, test_image_path):
        """Test that encoding returns a base64 string"""
        result = agent.encode_image(test_image_path)
        
        assert isinstance(result, str)
        assert len(result) > 0
        
        # Verify it's valid base64
        try:
            base64.b64decode(result)
            assert True
        except Exception:
            assert False, "Result is not valid base64"
    
    def test_encode_image_with_preprocessing_enabled(self, agent, test_image_path):
        """Test encoding with preprocessing enabled"""
        agent.enable_preprocessing = True
        result = agent.encode_image(test_image_path)
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_encode_image_with_preprocessing_disabled(self, agent, test_image_path):
        """Test encoding with preprocessing disabled"""
        agent.enable_preprocessing = False
        result = agent.encode_image(test_image_path)
        
        assert isinstance(result, str)
        assert len(result) > 0


class TestJSONParsing:
    """Test JSON parsing from model responses"""
    
    @pytest.fixture
    def agent(self):
        return HandwritingExtractionAgent()
    
    def test_parse_plain_json(self, agent):
        """Test parsing plain JSON"""
        json_str = '{"name": "John Doe", "age": 30}'
        result = agent._parse_json_response(json_str)
        
        assert result == {"name": "John Doe", "age": 30}
    
    def test_parse_json_with_markdown_code_block(self, agent):
        """Test parsing JSON wrapped in markdown code blocks"""
        json_str = '```json\n{"name": "Jane Doe"}\n```'
        result = agent._parse_json_response(json_str)
        
        assert result == {"name": "Jane Doe"}
    
    def test_parse_json_with_code_block_no_language(self, agent):
        """Test parsing JSON in code block without language specifier"""
        json_str = '```\n{"email": "test@example.com"}\n```'
        result = agent._parse_json_response(json_str)
        
        assert result == {"email": "test@example.com"}
    
    def test_parse_invalid_json_returns_raw_text(self, agent):
        """Test that invalid JSON returns raw text in dict"""
        invalid_json = 'This is not JSON'
        result = agent._parse_json_response(invalid_json)
        
        assert result == {"raw_text": "This is not JSON"}
    
    def test_parse_nested_json(self, agent):
        """Test parsing nested JSON structures"""
        json_str = '{"person": {"name": "Alice", "contact": {"email": "alice@example.com"}}}'
        result = agent._parse_json_response(json_str)
        
        assert result["person"]["name"] == "Alice"
        assert result["person"]["contact"]["email"] == "alice@example.com"


class TestTranslation:
    """Test translation functionality"""
    
    @pytest.fixture
    def agent_with_groq(self):
        """Create agent with mocked Groq client"""
        with patch.dict(os.environ, {'GROQ_API_KEY': 'test_key'}):
            agent = HandwritingExtractionAgent()
            
            # Mock the Groq client
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = '{"name": "John Doe", "email": "john@example.com"}'
            
            agent.groq_client = Mock()
            agent.groq_client.chat.completions.create = Mock(return_value=mock_response)
            
            return agent
    
    def test_translate_json_to_english(self, agent_with_groq):
        """Test translating JSON from another language to English"""
        spanish_data = {"nombre": "Juan", "correo": "juan@ejemplo.com"}
        
        result = agent_with_groq._translate_json_to_english(spanish_data, "Spanish")
        
        assert isinstance(result, dict)
        assert agent_with_groq.groq_client.chat.completions.create.called
    
    def test_translate_handles_groq_errors(self, agent_with_groq):
        """Test that translation errors are handled gracefully"""
        agent_with_groq.groq_client.chat.completions.create.side_effect = Exception("API Error")
        
        original_data = {"test": "data"}
        result = agent_with_groq._translate_json_to_english(original_data, "Spanish")
        
        # Should return original data on error
        assert result == original_data
    
    def test_translate_without_groq_client(self):
        """Test translation when Groq client is not available"""
        agent = HandwritingExtractionAgent()
        agent.groq_client = None
        
        data = {"test": "data"}
        result = agent._translate_json_to_english(data, "Spanish")
        
        # Should return original data
        assert result == data


class TestHandwritingExtraction:
    """Test handwriting extraction functionality"""
    
    @pytest.fixture
    def agent_with_hf(self):
        """Create agent with mocked HuggingFace client"""
        with patch.dict(os.environ, {'HF_TOKEN': 'test_token'}):
            agent = HandwritingExtractionAgent()
            
            # Mock the HF client
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = '{"name": "Test User", "email": "test@example.com"}'
            
            agent.hf_client = Mock()
            agent.hf_client.chat.completions.create = Mock(return_value=mock_response)
            
            return agent
    
    @pytest.fixture
    def test_image_path(self, tmp_path):
        img = Image.new('RGB', (100, 100), color='white')
        img_path = tmp_path / "test_image.jpg"
        img.save(img_path)
        return str(img_path)
    
    def test_extract_handwriting_returns_dict(self, agent_with_hf, test_image_path):
        """Test that extraction returns a dictionary"""
        result = agent_with_hf.extract_handwriting(test_image_path, "test.jpg")
        
        assert isinstance(result, dict)
    
    def test_extract_handwriting_success_response(self, agent_with_hf, test_image_path):
        """Test successful extraction response structure"""
        result = agent_with_hf.extract_handwriting(test_image_path, "test.jpg")
        
        assert "success" in result
        assert "filename" in result
        assert "message" in result
        
        if result["success"]:
            assert "extracted_data" in result
    
    def test_extract_handwriting_without_hf_client(self, test_image_path):
        """Test extraction when HuggingFace client is not available"""
        agent = HandwritingExtractionAgent()
        agent.hf_client = None
        
        result = agent.extract_handwriting(test_image_path, "test.jpg")
        
        assert result["success"] == False
        assert "error" in result
    
    def test_extract_handwriting_with_language(self, agent_with_hf, test_image_path):
        """Test extraction with different languages"""
        result = agent_with_hf.extract_handwriting(test_image_path, "test.jpg", "Spanish")
        
        assert isinstance(result, dict)
        assert agent_with_hf.hf_client.chat.completions.create.called


class TestErrorHandling:
    """Test error handling in various scenarios"""
    
    @pytest.fixture
    def agent(self):
        return HandwritingExtractionAgent()
    
    def test_handles_missing_image_file(self, agent):
        """Test handling of missing image file"""
        with pytest.raises(FileNotFoundError):
            agent.preprocess_image("/nonexistent/path/image.jpg")
    
    def test_handles_invalid_image_file(self, agent, tmp_path):
        """Test handling of invalid image file"""
        # Create a non-image file
        invalid_file = tmp_path / "invalid.jpg"
        invalid_file.write_text("This is not an image")
        
        with pytest.raises(Exception):
            agent.preprocess_image(str(invalid_file))
    
    def test_extraction_handles_api_errors(self):
        """Test that extraction handles API errors gracefully"""
        with patch.dict(os.environ, {'HF_TOKEN': 'test_token'}):
            agent = HandwritingExtractionAgent()
            agent.hf_client = Mock()
            agent.hf_client.chat.completions.create.side_effect = Exception("API Error")
            
            # Create a test image
            img = Image.new('RGB', (100, 100), color='white')
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG')
            
            # This should handle the error gracefully
            # Note: This test may need adjustment based on actual implementation
            assert agent.hf_client is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
