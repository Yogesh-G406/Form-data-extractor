import os
import base64
import json
from typing import Dict, Any, Optional
from PIL import Image, ImageEnhance, ImageFilter
import io
from langfuse import Langfuse
from openai import OpenAI
from groq import Groq


class HandwritingExtractionAgent:
    def __init__(self):
        self.langfuse_public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        self.langfuse_secret_key = os.getenv("LANGFUSE_SECRET_KEY")
        self.langfuse_host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
        self.enable_preprocessing = os.getenv("ENABLE_IMAGE_PREPROCESSING", "true").lower() == "true"
        
        self.hf_token = os.getenv("HF_TOKEN")
        if self.hf_token:
            self.hf_client = OpenAI(
                base_url="https://router.huggingface.co/v1",
                api_key=self.hf_token,
            )
        else:
            self.hf_client = None
        
        self.langfuse: Optional[Langfuse] = None
        
        if self.langfuse_public_key and self.langfuse_secret_key:
            try:
                self.langfuse = Langfuse(
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
        
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        if self.groq_api_key:
            self.groq_client = Groq(api_key=self.groq_api_key)
            print("[OK] Groq API configured for translation")
        else:
            self.groq_client = None
            print("[WARNING] Groq API key not configured")
    
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
    
    def extract_handwriting(self, image_path: str, filename: str, language: str = "English") -> Dict[str, Any]:
        return self.extract_handwriting_huggingface(image_path, filename, language)
    
    def extract_handwriting_huggingface(self, image_path: str, filename: str, language: str = "English") -> Dict[str, Any]:
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
            
            prompt = f"""You are an expert OCR system specialized in reading handwritten text with maximum accuracy.

This document is written in {language}. Please read and extract the text in {language}.

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
7. Create field names based on actual labels, headings, and form structure you see (in {language})
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
            
            if language.lower() != "english" and self.groq_client:
                try:
                    structured_data = self._translate_json_to_english(structured_data, language)
                except Exception as e:
                    print(f"[WARNING] Translation failed: {e}")
            
            result = {
                "success": True,
                "filename": filename,
                "extracted_data": structured_data,
                "message": f"Handwriting extracted successfully using HuggingFace{' and translated to English' if language.lower() != 'english' else ''}"
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
    
    def _translate_json_to_english(self, data: Dict[str, Any], source_language: str) -> Dict[str, Any]:
        """Recursively translate JSON keys and string values to English using Groq API"""
        if not self.groq_client:
            return data
        
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        
        translation_prompt = f"""You are a translation assistant. Translate the following JSON from {source_language} to English.

IMPORTANT RULES:
1. Translate ONLY the keys (field names) and string values
2. Keep all numbers, dates, and special characters unchanged
3. Preserve the exact JSON structure
4. Return ONLY valid JSON with no additional text before or after
5. Do not translate values that are already partially in English
6. If a value is "unreadable", keep it as is

JSON to translate:
{json_str}"""
        
        try:
            response = self.groq_client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[
                    {"role": "user", "content": translation_prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            translated_text = response.choices[0].message.content
            return self._parse_json_response(translated_text)
        except Exception as e:
            print(f"[ERROR] Translation error: {e}")
            return data