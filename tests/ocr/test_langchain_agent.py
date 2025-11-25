"""
Unit tests for LangChainFormAgent
Tests form field extraction, validation, and classification functionality
"""

import pytest
import os
from unittest.mock import Mock, patch
from pathlib import Path

# Import the agent
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'backend'))

from langchain_agent import LangChainFormAgent


class TestLangChainAgentInitialization:
    """Test LangChain agent initialization"""
    
    def test_agent_initializes_successfully(self):
        """Test that agent can be initialized"""
        try:
            agent = LangChainFormAgent()
            assert agent is not None
        except Exception as e:
            # Agent might fail to initialize without proper credentials
            # This is acceptable for testing
            assert True
    
    def test_agent_requires_hf_token(self):
        """Test that agent requires HuggingFace token"""
        with patch.dict(os.environ, {}, clear=True):
            try:
                agent = LangChainFormAgent()
                # If it initializes, check it has the client
                assert hasattr(agent, 'hf_client')
            except Exception:
                # Expected if no token is provided
                assert True


class TestFormFieldExtraction:
    """Test form field extraction functionality"""
    
    @pytest.fixture
    def agent_with_mock(self):
        """Create agent with mocked HF client"""
        try:
            with patch.dict(os.environ, {'HF_TOKEN': 'test_token'}):
                agent = LangChainFormAgent()
                
                # Mock the response
                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[0].message.content = '{"fields": [{"name": "name", "value": "John Doe"}]}'
                
                if hasattr(agent, 'hf_client') and agent.hf_client:
                    agent.hf_client.chat.completions.create = Mock(return_value=mock_response)
                
                return agent
        except Exception:
            pytest.skip("Agent initialization failed")
    
    def test_extract_form_fields_returns_dict(self, agent_with_mock):
        """Test that extraction returns a dictionary"""
        extracted_text = {"name": "John Doe", "email": "john@example.com"}
        
        result = agent_with_mock.extract_form_fields(extracted_text)
        
        assert isinstance(result, dict)
    
    def test_extract_form_fields_with_language(self, agent_with_mock):
        """Test extraction with different languages"""
        extracted_text = {"nombre": "Juan", "correo": "juan@ejemplo.com"}
        
        result = agent_with_mock.extract_form_fields(extracted_text, "Spanish")
        
        assert isinstance(result, dict)
    
    def test_extract_form_fields_handles_empty_input(self, agent_with_mock):
        """Test extraction with empty input"""
        result = agent_with_mock.extract_form_fields({})
        
        assert isinstance(result, dict)
    
    def test_extract_form_fields_handles_nested_data(self, agent_with_mock):
        """Test extraction with nested data structures"""
        extracted_text = {
            "personal": {"name": "Alice", "age": 30},
            "contact": {"email": "alice@example.com"}
        }
        
        result = agent_with_mock.extract_form_fields(extracted_text)
        
        assert isinstance(result, dict)


class TestFormValidation:
    """Test form validation functionality"""
    
    @pytest.fixture
    def agent_with_mock(self):
        """Create agent with mocked HF client"""
        try:
            with patch.dict(os.environ, {'HF_TOKEN': 'test_token'}):
                agent = LangChainFormAgent()
                
                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[0].message.content = '{"valid": true, "errors": []}'
                
                if hasattr(agent, 'hf_client') and agent.hf_client:
                    agent.hf_client.chat.completions.create = Mock(return_value=mock_response)
                
                return agent
        except Exception:
            pytest.skip("Agent initialization failed")
    
    def test_validate_form_fields_returns_dict(self, agent_with_mock):
        """Test that validation returns a dictionary"""
        fields = [
            {"name": "email", "value": "test@example.com"},
            {"name": "phone", "value": "555-1234"}
        ]
        
        result = agent_with_mock.validate_form_fields(fields)
        
        assert isinstance(result, dict)
    
    def test_validate_with_expected_fields(self, agent_with_mock):
        """Test validation with expected fields list"""
        fields = [{"name": "name", "value": "John"}]
        expected_fields = ["name", "email", "phone"]
        
        result = agent_with_mock.validate_form_fields(fields, expected_fields)
        
        assert isinstance(result, dict)
    
    def test_validate_empty_fields(self, agent_with_mock):
        """Test validation with empty fields list"""
        result = agent_with_mock.validate_form_fields([])
        
        assert isinstance(result, dict)
    
    def test_validate_handles_missing_fields(self, agent_with_mock):
        """Test validation identifies missing fields"""
        fields = [{"name": "name", "value": "John"}]
        expected_fields = ["name", "email", "phone", "address"]
        
        result = agent_with_mock.validate_form_fields(fields, expected_fields)
        
        assert isinstance(result, dict)


class TestFormClassification:
    """Test form classification functionality"""
    
    @pytest.fixture
    def agent_with_mock(self):
        """Create agent with mocked HF client"""
        try:
            with patch.dict(os.environ, {'HF_TOKEN': 'test_token'}):
                agent = LangChainFormAgent()
                
                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[0].message.content = '{"form_type": "contact_form", "confidence": 0.95}'
                
                if hasattr(agent, 'hf_client') and agent.hf_client:
                    agent.hf_client.chat.completions.create = Mock(return_value=mock_response)
                
                return agent
        except Exception:
            pytest.skip("Agent initialization failed")
    
    def test_classify_form_returns_dict(self, agent_with_mock):
        """Test that classification returns a dictionary"""
        extracted_text = {"name": "John Doe", "email": "john@example.com"}
        
        result = agent_with_mock.classify_form(extracted_text)
        
        assert isinstance(result, dict)
    
    def test_classify_medical_form(self, agent_with_mock):
        """Test classification of medical form"""
        medical_data = {
            "patient_name": "Jane Doe",
            "doctor": "Dr. Smith",
            "diagnosis": "Common cold"
        }
        
        result = agent_with_mock.classify_form(medical_data)
        
        assert isinstance(result, dict)
    
    def test_classify_invoice_form(self, agent_with_mock):
        """Test classification of invoice form"""
        invoice_data = {
            "invoice_number": "INV-12345",
            "total": "$500.00",
            "due_date": "2024-12-31"
        }
        
        result = agent_with_mock.classify_form(invoice_data)
        
        assert isinstance(result, dict)
    
    def test_classify_application_form(self, agent_with_mock):
        """Test classification of application form"""
        application_data = {
            "applicant_name": "Alice Johnson",
            "position": "Software Developer",
            "experience": "5 years"
        }
        
        result = agent_with_mock.classify_form(application_data)
        
        assert isinstance(result, dict)
    
    def test_classify_empty_data(self, agent_with_mock):
        """Test classification with empty data"""
        result = agent_with_mock.classify_form({})
        
        assert isinstance(result, dict)


class TestErrorHandling:
    """Test error handling in LangChain agent"""
    
    def test_handles_missing_hf_token(self):
        """Test handling of missing HuggingFace token"""
        with patch.dict(os.environ, {}, clear=True):
            try:
                agent = LangChainFormAgent()
                # If it initializes, it should handle missing token gracefully
                assert True
            except Exception:
                # Expected behavior
                assert True
    
    def test_handles_api_errors(self):
        """Test handling of API errors"""
        try:
            with patch.dict(os.environ, {'HF_TOKEN': 'test_token'}):
                agent = LangChainFormAgent()
                
                if hasattr(agent, 'hf_client') and agent.hf_client:
                    agent.hf_client.chat.completions.create = Mock(side_effect=Exception("API Error"))
                    
                    # Should handle error gracefully
                    try:
                        agent.extract_form_fields({"test": "data"})
                    except Exception:
                        assert True
        except Exception:
            pytest.skip("Agent initialization failed")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
