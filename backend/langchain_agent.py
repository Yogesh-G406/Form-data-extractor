import os
import json
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langfuse import Langfuse


class FormField(BaseModel):
    field_name: str = Field(description="The name of the form field")
    value: str = Field(description="The extracted value")
    confidence: str = Field(
        default="high",
        description="Confidence level: high, medium, or low"
    )
    notes: Optional[str] = Field(
        default=None,
        description="Any notes about the extraction"
    )


class FormExtraction(BaseModel):
    form_type: Optional[str] = Field(
        default=None,
        description="Type of form detected"
    )
    fields: List[FormField] = Field(
        description="List of extracted form fields"
    )
    overall_confidence: str = Field(
        default="high",
        description="Overall confidence level of extraction"
    )
    summary: Optional[str] = Field(
        default=None,
        description="Summary of the form content"
    )


class LangChainFormAgent:
    """LangChain-based form field extraction agent"""
    
    def __init__(self):
        self.hf_token = os.getenv("HF_TOKEN")
        self.langfuse_public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        self.langfuse_secret_key = os.getenv("LANGFUSE_SECRET_KEY")
        self.langfuse_host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
        
        self.langfuse: Optional[Langfuse] = None
        self._init_langfuse()
        
        if not self.hf_token:
            print("[WARNING] HuggingFace token not configured for LangChain agent")
            self.llm = None
        else:
            self.llm = ChatOpenAI(
                model="Qwen/Qwen2.5-VL-7B-Instruct:hyperbolic",
                base_url="https://router.huggingface.co/v1",
                api_key=self.hf_token,
                temperature=0.1,
            )
            print("[OK] LangChain HuggingFace integration initialized")
    
    def _init_langfuse(self):
        if self.langfuse_public_key and self.langfuse_secret_key:
            try:
                self.langfuse = Langfuse(
                    public_key=self.langfuse_public_key,
                    secret_key=self.langfuse_secret_key,
                    host=self.langfuse_host
                )
                print("[OK] LangChain agent Langfuse initialized")
            except Exception as e:
                print(f"[WARNING] Langfuse initialization failed in LangChain agent: {e}")
    

    
    def extract_form_fields(
        self,
        extracted_text: Dict[str, Any],
        language: str = "English"
    ) -> Dict[str, Any]:
        """
        Extract and structure form fields from raw extracted text using LangChain
        
        Args:
            extracted_text: Raw extracted text data
            language: Language of the document
            
        Returns:
            Structured form extraction with fields
        """
        if not self.llm:
            return {
                "success": False,
                "error": "LLM not configured",
                "message": "HuggingFace token not set"
            }
        
        try:
            parser = PydanticOutputParser(pydantic_object=FormExtraction)
            
            prompt_template = ChatPromptTemplate.from_template(
                """You are an expert form field extraction system. Analyze the following extracted text and identify all form fields with their values.

The document is in {language}.

EXTRACTED TEXT:
{text}

INSTRUCTIONS:
1. Identify the type of form (invoice, application, survey, etc.)
2. Extract all visible fields and their values
3. For each field, assign a confidence level (high, medium, or low)
4. If a field value is unclear or partially readable, note it in the 'notes' field
5. Provide an overall confidence assessment
6. Generate a brief summary of the form

{format_instructions}

Return ONLY the JSON response, no additional text."""
            )
            
            chain = (
                {
                    "text": RunnablePassthrough(),
                    "language": RunnableLambda(lambda _: language),
                    "format_instructions": RunnableLambda(lambda _: parser.get_format_instructions())
                }
                | prompt_template
                | self.llm
                | parser
            )
            
            result = chain.invoke(json.dumps(extracted_text, ensure_ascii=False))
            
            response = {
                "success": True,
                "form_type": result.form_type,
                "fields": [
                    {
                        "field_name": field.field_name,
                        "value": field.value,
                        "confidence": field.confidence,
                        "notes": field.notes
                    }
                    for field in result.fields
                ],
                "overall_confidence": result.overall_confidence,
                "summary": result.summary,
                "message": "Form fields extracted successfully using LangChain"
            }
            
            if self.langfuse:
                try:
                    self.langfuse.trace(
                        name="langchain_form_extraction",
                        input={"extracted_text": extracted_text},
                        output=response
                    )
                except Exception as e:
                    print(f"[WARNING] Langfuse trace failed: {e}")
            
            return response
            
        except Exception as e:
            error_response = {
                "success": False,
                "error": str(e),
                "message": "Failed to extract form fields using LangChain"
            }
            
            if self.langfuse:
                try:
                    self.langfuse.trace(
                        name="langchain_form_extraction_error",
                        input={"extracted_text": extracted_text},
                        output=error_response
                    )
                except:
                    pass
            
            return error_response
    
    def validate_form_fields(
        self,
        fields: List[Dict[str, Any]],
        expected_fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Validate extracted form fields
        
        Args:
            fields: List of extracted fields
            expected_fields: Optional list of expected field names
            
        Returns:
            Validation result with errors and suggestions
        """
        if not self.llm:
            return {
                "success": False,
                "error": "LLM not configured"
            }
        
        try:
            prompt = PromptTemplate.from_template(
                """You are a form validation expert. Analyze these form fields and provide validation feedback.

Fields:
{fields}

{expected_constraint}

Provide a validation report with:
1. Any obvious errors or inconsistencies
2. Fields that seem incomplete or suspicious
3. Suggestions for improvements
4. Overall form quality assessment

Be concise and practical."""
            )
            
            expected_constraint = ""
            if expected_fields:
                expected_constraint = f"Expected fields: {', '.join(expected_fields)}\n"
            
            chain = prompt | self.llm
            
            result = chain.invoke({
                "fields": json.dumps(fields, indent=2),
                "expected_constraint": expected_constraint
            })
            
            return {
                "success": True,
                "validation_report": result.content,
                "message": "Form validation completed"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Form validation failed"
            }
    
    def classify_form(
        self,
        extracted_text: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Classify the type of form using LangChain
        
        Args:
            extracted_text: Extracted form text data
            
        Returns:
            Form classification result
        """
        if not self.llm:
            return {
                "success": False,
                "error": "LLM not configured"
            }
        
        try:
            prompt = PromptTemplate.from_template(
                """Analyze this form content and classify it into one of these categories:
- Invoice/Receipt
- Application Form
- Survey/Questionnaire
- Medical Form
- Legal Document
- Tax Document
- Educational Form
- Other

Form content:
{content}

Provide:
1. The form category
2. Confidence level (high/medium/low)
3. Key identifiers that helped determine the classification
4. Any subcategory if applicable

Be concise."""
            )
            
            chain = prompt | self.llm
            
            result = chain.invoke({
                "content": json.dumps(extracted_text, ensure_ascii=False, indent=2)
            })
            
            return {
                "success": True,
                "classification": result.content,
                "message": "Form classified successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Form classification failed"
            }
