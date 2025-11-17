import os
import base64
import json
from typing import Dict, Any, Optional
import requests
from PIL import Image, ImageEnhance, ImageFilter
import io
from langfuse import Langfuse
from openai import OpenAI
try:
    from groq import Groq
except ImportError:
    Groq = None
try:
    from langfuse.callback import CallbackHandler  # type: ignore
except ImportError:
    CallbackHandler = None


class HandwritingExtractionAgent:
    def __init__(self):
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "bakllava:latest")
        self.langfuse_public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        self.langfuse_secret_key = os.getenv("LANGFUSE_SECRET_KEY")
        self.langfuse_host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
        self.request_timeout = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "120"))
        self.temperature = float(os.getenv("OLLAMA_TEMPERATURE", "0.1"))
        self.num_predict = int(os.getenv("OLLAMA_NUM_PREDICT", "2048"))
        self.enable_preprocessing = os.getenv("ENABLE_IMAGE_PREPROCESSING", "true").lower() == "true"
        self.use_consensus = os.getenv("USE_CONSENSUS_MODE", "true").lower() == "true"
        
        self.hf_token = os.getenv("HF_TOKEN")
        if self.hf_token:
            self.hf_client = OpenAI(
                base_url="https://router.huggingface.co/v1",
                api_key=self.hf_token,
            )
        else:
            self.hf_client = None
        
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        # Check if API key is set and not a placeholder
        if self.groq_api_key and self.groq_api_key.strip() and self.groq_api_key != "your_groq_api_key_here" and Groq:
            try:
                self.groq_client = Groq(api_key=self.groq_api_key)
            except Exception as e:
                print(f"[WARNING] Failed to initialize Groq client: {e}")
                self.groq_client = None
        else:
            self.groq_client = None
        
        self.langfuse: Optional[Langfuse] = None
        self.langfuse_handler = None
        
        if self.langfuse_public_key and self.langfuse_secret_key:
            try:
                self.langfuse = Langfuse(
                    public_key=self.langfuse_public_key,
                    secret_key=self.langfuse_secret_key,
                    host=self.langfuse_host
                )
                if CallbackHandler:
                    self.langfuse_handler = CallbackHandler(
                        public_key=self.langfuse_public_key,
                        secret_key=self.langfuse_secret_key,
                        host=self.langfuse_host
                    )
                print("[OK] Langfuse initialized successfully")
            except Exception as e:
                print(f"[WARNING] Langfuse initialization failed: {e}")
                print("Continuing without Langfuse tracing...")
        else:
            print("[WARNING] Langfuse credentials not found. Continuing without tracing...")
        
        if self.hf_client:
            print("[OK] HuggingFace API configured (Qwen2.5-VL-7B-Instruct)")
        else:
            print("[WARNING] HuggingFace token not configured")
        
        if self.groq_client:
            print("[OK] Groq API configured (Qwen-2.5-32b)")
        else:
            print("[WARNING] Groq API key not configured")
        
        print(f"[OK] Ollama configured (host={self.ollama_host}, model={self.ollama_model})")
    
    def preprocess_image(self, image_path: str) -> Image.Image:
        """Enhance image quality for better OCR accuracy"""
        img = Image.open(image_path)
        
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.5)
        
        # Enhance sharpness
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.3)
        
        # Apply slight denoising
        img = img.filter(ImageFilter.MedianFilter(size=3))
        
        # Resize if too small (minimum 512px on longest side for better detail)
        width, height = img.size
        min_size = 512
        if max(width, height) < min_size:
            scale = min_size / max(width, height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        return img
    
    def encode_image(self, image_path: str) -> str:
        """Encode image to base64, with optional preprocessing"""
        if self.enable_preprocessing:
            try:
                img = self.preprocess_image(image_path)
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=95)
                image_bytes = buffer.getvalue()
            except Exception as e:
                print(f"[WARNING] Image preprocessing failed, using original: {e}")
                with open(image_path, "rb") as image_file:
                    image_bytes = image_file.read()
        else:
            with open(image_path, "rb") as image_file:
                image_bytes = image_file.read()
        
        return base64.b64encode(image_bytes).decode('utf-8')
    
    def extract_handwriting(self, image_path: str, filename: str) -> Dict[str, Any]:
        # Prefer HuggingFace for vision tasks (supports images)
        # Fall back to Groq if HuggingFace is not available (though Groq doesn't support vision)
        if self.hf_client:
            return self.extract_handwriting_huggingface(image_path, filename)
        else:
            # Try Groq (will fall back to HuggingFace if available, or return error)
            return self.extract_handwriting_groq(image_path, filename)
    
    def extract_handwriting_huggingface(self, image_path: str, filename: str) -> Dict[str, Any]:
        """Extract handwriting using HuggingFace Qwen2.5-VL model via OpenAI API"""
        if not self.hf_client:
            return {
                "success": False,
                "filename": filename,
                "error": "HuggingFace token not configured",
                "message": "HF_TOKEN environment variable not set"
            }
        
        try:
            with open(image_path, "rb") as image_file:
                image_data = base64.standard_b64encode(image_file.read()).decode("utf-8")
            
            prompt = """You are an expert OCR system specialized in reading handwritten text with maximum accuracy.

Analyze this handwritten document with extreme care and extract ALL the information you can see.

CRITICAL INSTRUCTIONS FOR MAXIMUM ACCURACY:
1. Read each character and word carefully - examine the image in detail
2. DO NOT assume or hallucinate any fields - only extract what is clearly visible
3. Pay special attention to:
   - Numbers (phone numbers, dates, policy numbers, etc.) - read each digit precisely
   - Names - read each letter carefully, including capitalization
   - Addresses - read street names, numbers, and city names accurately
   - Email addresses - verify @ symbols and domain names
4. For partially readable text, extract what you can see clearly, even if incomplete
5. If text is completely illegible or blank, mark it as "unreadable" (not null)
6. Return the data as clean, structured JSON with proper nesting
7. Create field names based on actual labels, headings, and form structure you see
8. Preserve the exact logical structure and grouping of information
9. Be extremely precise with values - read numbers and text character by character
10. Double-check your extraction before returning the JSON

IMPORTANT: Read slowly and carefully. Accuracy is more important than speed.
Return ONLY valid JSON with no additional text, markdown, or explanation before or after.
The JSON should have descriptive keys based on the actual content structure."""
            
            completion = self.hf_client.chat.completions.create(
                model="Qwen/Qwen2.5-VL-7B-Instruct:hyperbolic",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
            )
            
            extracted_text = completion.choices[0].message.content
            structured_data = self._parse_json_response(extracted_text)
            
            result = {
                "success": True,
                "filename": filename,
                "extracted_data": structured_data,
                "message": "Handwriting extracted successfully using HuggingFace"
            }
            
            if self.langfuse:
                try:
                    trace = self.langfuse.trace(name="handwriting_extraction_hf")  # type: ignore
                    trace.update(input={"filename": filename}, output=result)
                except Exception as e:
                    print(f"[WARNING] Langfuse trace failed: {e}")
            
            return result
            
        except Exception as e:
            error_result = {
                "success": False,
                "filename": filename,
                "error": str(e),
                "message": "Failed to extract handwriting using HuggingFace"
            }
            
            if self.langfuse:
                try:
                    trace = self.langfuse.trace(name="handwriting_extraction_hf_error")  # type: ignore
                    trace.update(input={"filename": filename}, output=error_result)
                except:
                    pass
            
            return error_result
    
    def extract_handwriting_groq(self, image_path: str, filename: str) -> Dict[str, Any]:
        """Extract handwriting using Groq API with Qwen-2.5-32b model"""
        if not self.groq_client:
            return {
                "success": False,
                "filename": filename,
                "error": "Groq API key not configured",
                "message": "GROQ_API_KEY environment variable not set"
            }
        
        try:
            with open(image_path, "rb") as image_file:
                image_data = base64.standard_b64encode(image_file.read()).decode("utf-8")
            
            prompt = """You are an expert OCR system specialized in reading handwritten text with maximum accuracy.

Analyze this handwritten document with extreme care and extract ALL the information you can see.

CRITICAL INSTRUCTIONS FOR MAXIMUM ACCURACY:
1. Read each character and word carefully - examine the image in detail
2. DO NOT assume or hallucinate any fields - only extract what is clearly visible
3. Pay special attention to:
   - Numbers (phone numbers, dates, policy numbers, etc.) - read each digit precisely
   - Names - read each letter carefully, including capitalization
   - Addresses - read street names, numbers, and city names accurately
   - Email addresses - verify @ symbols and domain names
4. For partially readable text, extract what you can see clearly, even if incomplete
5. If text is completely illegible or blank, mark it as "unreadable" (not null)
6. Return the data as clean, structured JSON with proper nesting
7. Create field names based on actual labels, headings, and form structure you see
8. Preserve the exact logical structure and grouping of information
9. Be extremely precise with values - read numbers and text character by character
10. Double-check your extraction before returning the JSON

IMPORTANT: Read slowly and carefully. Accuracy is more important than speed.
Return ONLY valid JSON with no additional text, markdown, or explanation before or after.
The JSON should have descriptive keys based on the actual content structure."""
            
            # Note: Groq's text models (like qwen-2.5-32b) don't support vision/image inputs.
            # We need to fall back to HuggingFace which supports vision models.
            
            # Check if HuggingFace is available as fallback
            if self.hf_client:
                print("[INFO] Groq doesn't support vision, falling back to HuggingFace vision model")
                return self.extract_handwriting_huggingface(image_path, filename)
            
            # If no fallback, return error
            return {
                "success": False,
                "filename": filename,
                "error": "Groq API models don't support vision/image inputs",
                "message": "Please configure HF_TOKEN for HuggingFace vision model (Qwen2.5-VL-7B-Instruct) to process images"
            }
            
        except Exception as e:
            error_message = str(e)
            error_type = type(e).__name__
            print(f"[ERROR] Groq API error: {error_type}: {error_message}")
            import traceback
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
            
            error_result = {
                "success": False,
                "filename": filename,
                "error": f"{error_type}: {error_message}",
                "message": "Failed to extract handwriting using Groq API"
            }
            
            if self.langfuse:
                try:
                    trace = self.langfuse.trace(name="handwriting_extraction_groq_error")  # type: ignore
                    trace.update(input={"filename": filename}, output=error_result)
                except:
                    pass
            
            return error_result
    
    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """Parse JSON from model response, handling markdown code blocks"""
        extracted_text = text.strip()
        
        # Remove markdown code blocks
        if extracted_text.startswith("```json"):
            extracted_text = extracted_text[7:]
        if extracted_text.startswith("```"):
            extracted_text = extracted_text[3:]
        if extracted_text.endswith("```"):
            extracted_text = extracted_text[:-3]
        extracted_text = extracted_text.strip()
        
        try:
            return json.loads(extracted_text)
        except json.JSONDecodeError:
            return {"raw_text": extracted_text}
    
    def _merge_extractions(self, data1: Dict[str, Any], data2: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two extraction results, preferring more complete/accurate values"""
        def merge_dicts(d1: Dict, d2: Dict) -> Dict:
            result = {}
            all_keys = set(d1.keys()) | set(d2.keys())
            
            for key in all_keys:
                val1 = d1.get(key)
                val2 = d2.get(key)
                
                if val1 == val2:
                    # Both agree - use the value
                    result[key] = val1
                elif isinstance(val1, dict) and isinstance(val2, dict):
                    # Both are dicts - merge recursively
                    result[key] = merge_dicts(val1, val2)
                elif val1 is None or val1 == "unreadable":
                    # Prefer val2 if val1 is unreadable
                    result[key] = val2
                elif val2 is None or val2 == "unreadable":
                    # Prefer val1 if val2 is unreadable
                    result[key] = val1
                elif isinstance(val1, str) and isinstance(val2, str):
                    # Both have values - prefer longer/more complete one
                    result[key] = val1 if len(val1) >= len(val2) else val2
                else:
                    # Default to first value
                    result[key] = val1 if val1 is not None else val2
            
            return result
        
        return merge_dicts(data1, data2)
