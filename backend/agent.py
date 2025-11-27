import os
import base64
import json
import time
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
        
        # Ensure image is not too small before processing
        width, height = img.size
        if width < 28 or height < 28:
            img = img.resize((max(28, width), max(28, height)))
        
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
            # Ensure image is not too small (causes issues with some models)
            try:
                with Image.open(image_path) as img:
                    width, height = img.size
                    if width < 28 or height < 28:
                        # Resize to minimum supported size
                        img = img.resize((max(28, width), max(28, height)))
                        buffer = io.BytesIO()
                        img.save(buffer, format='JPEG')
                        image_bytes = buffer.getvalue()
                    else:
                        with open(image_path, "rb") as image_file:
                            image_bytes = image_file.read()
            except Exception as e:
                print(f"[WARNING] Image size check failed: {e}")
                with open(image_path, "rb") as image_file:
                    image_bytes = image_file.read()
        
        return base64.b64encode(image_bytes).decode('utf-8')
    
    def extract_handwriting(self, image_path: str, filename: str, language: str = "English", parent_trace=None) -> Dict[str, Any]:
        return self.extract_handwriting_huggingface(image_path, filename, language, parent_trace=parent_trace)
    
    def extract_handwriting_huggingface(self, image_path, filename, language="English", parent_trace=None):
        """
        Extract handwriting using Hugging Face Inference API (Qwen/Qwen2.5-VL-7B-Instruct)
        """
        if not self.hf_client:
            return {
                "success": False,
                "error": "HuggingFace client not initialized",
                "prompt": None
            }
        
        prompt = None
        trace = None
        generation = None
        start_time = time.time()
        
        try:
            # Get image size for metadata
            from PIL import Image
            img = Image.open(image_path)
            image_size = {"width": img.width, "height": img.height}
            
            # Use encode_image to handle resizing/preprocessing
            image_data = self.encode_image(image_path)
            
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
            
            # Create Langfuse trace/span
            if self.langfuse:
                try:
                    # If parent trace provided, create a span under it
                    if parent_trace:
                        trace = parent_trace.start_span(
                            name="handwriting_extraction",
                            input=prompt,
                            metadata={
                                "filename": filename,
                                "language": language,
                                "image_size": image_size,
                                "preprocessing_enabled": self.enable_preprocessing,
                                "model": "Qwen/Qwen2.5-VL-7B-Instruct"
                            }
                        )
                    # Otherwise create a new root span
                    else:
                        trace = self.langfuse.start_span(
                            name="handwriting_extraction",
                            input=prompt,
                            metadata={
                                "filename": filename,
                                "language": language,
                                "image_size": image_size,
                                "preprocessing_enabled": self.enable_preprocessing,
                                "model": "Qwen/Qwen2.5-VL-7B-Instruct"
                            }
                        )
                    
                    # Create generation for LLM call
                    generation = trace.start_generation(
                        name="ocr_extraction",
                        model="Qwen/Qwen2.5-VL-7B-Instruct:hyperbolic",
                        input=prompt,
                        metadata={
                            "provider": "huggingface",
                            "image_included": True
                        }
                    )
                except Exception as lf_error:
                    print(f"[WARNING] Langfuse trace creation failed: {lf_error}")
                    trace = None
                    generation = None
            
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
            
            # Update generation with response
            if generation:
                try:
                    generation.update(
                        output=extracted_text,
                        usage={
                            "input": len(prompt),
                            "output": len(extracted_text)
                        }
                    )
                    generation.end()
                except Exception as lf_error:
                    print(f"[WARNING] Langfuse generation update failed: {lf_error}")
            
            structured_data = self._parse_json_response(extracted_text)
            
            # Track translation if needed
            if language.lower() != "english" and self.groq_client:
                try:
                    structured_data = self._translate_json_to_english(structured_data, language, trace)
                except Exception as e:
                    print(f"[WARNING] Translation failed: {e}")
            
            duration = time.time() - start_time
            
            result = {
                "success": True,
                "filename": filename,
                "extracted_data": structured_data,
                "prompt": prompt,
                "message": f"Handwriting extracted successfully using HuggingFace{' and translated to English' if language.lower() != 'english' else ''}"
            }
            
            # Update trace with final result
            if trace:
                try:
                    trace.update(
                        output=structured_data,
                        metadata={
                            "duration_seconds": round(duration, 2),
                            "fields_extracted": len(structured_data),
                            "translated": language.lower() != "english",
                            "full_result": result
                        }
                    )
                    trace.end()
                except Exception as lf_error:
                    print(f"[WARNING] Langfuse trace update failed: {lf_error}")
            
            return result
            
        except Exception as e:
            import traceback
            duration = time.time() - start_time
            
            error_result = {
                "success": False,
                "filename": filename,
                "error": str(e),
                "message": "Failed to extract handwriting using HuggingFace",
                "prompt": prompt,
                "metadata": {
                    "error_type": type(e).__name__
                }
            }
            
            # Track error in Langfuse
            if self.langfuse:
                try:
                    if not trace:
                        trace = self.langfuse.start_span(name="handwriting_extraction_error")
                    
                    trace.update(
                        output=error_result,
                        metadata={
                            "error_type": type(e).__name__,
                            "error_message": str(e),
                            "stack_trace": traceback.format_exc(),
                            "duration_seconds": round(duration, 2)
                        }
                    )
                    trace.end()
                except Exception as lf_error:
                    print(f"[WARNING] Langfuse error tracking failed: {lf_error}")
            
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
    
    def _translate_json_to_english(self, data: Dict[str, Any], source_language: str, trace=None) -> Dict[str, Any]:
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
        
        generation = None
        try:
            # Create generation for translation if trace exists
            if trace and self.langfuse:
                try:
                    generation = trace.start_generation(
                        name="translation",
                        model="mixtral-8x7b-32768",
                        input=translation_prompt,
                        metadata={
                            "provider": "groq",
                            "source_language": source_language,
                            "target_language": "English"
                        }
                    )
                except Exception as lf_error:
                    print(f"[WARNING] Langfuse translation generation failed: {lf_error}")
                    generation = None
            
            response = self.groq_client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[
                    {"role": "user", "content": translation_prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            translated_text = response.choices[0].message.content
            
            # Update generation with response
            if generation:
                try:
                    generation.update(
                        output=translated_text,
                        usage={
                            "input": len(translation_prompt),
                            "output": len(translated_text)
                        }
                    )
                    generation.end()
                except Exception as lf_error:
                    print(f"[WARNING] Langfuse translation update failed: {lf_error}")
            
            return self._parse_json_response(translated_text)
        except Exception as e:
            print(f"[ERROR] Translation error: {e}")
            
            # Track translation error
            if generation:
                try:
                    generation.update(
                        output={"error": str(e)},
                        metadata={"error_type": type(e).__name__}
                    )
                    generation.end()
                except Exception:
                    pass
            
            return data