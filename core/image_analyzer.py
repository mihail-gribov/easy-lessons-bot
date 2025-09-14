"""Image analysis handler using GPT-4 Vision API."""

import asyncio
import base64
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import openai
from PIL import Image
from settings.config import get_settings

logger = logging.getLogger(__name__)


class ImageAnalyzer:
    """Handles image analysis using GPT-4 Vision API."""

    def __init__(self):
        """Initialize image analyzer with configuration."""
        self.settings = get_settings()
        self.vision_model = self.settings.vision_model
        
        # Initialize OpenAI client for Vision API
        self.openai_client = openai.AsyncOpenAI(
            api_key=self.settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1"
        )

    async def analyze_image(
        self, file_path: Path, session_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze image using GPT-4 Vision API.

        Args:
            file_path: Path to image file
            session_context: Current session context

        Returns:
            Image analysis results
        """
        try:
            if not self.settings.image_analysis_enabled:
                return {"error": "Image analysis is disabled"}

            logger.info(f"Analyzing image file: {file_path}")

            # Validate image file
            if not await self.validate_image_file(file_path):
                return {"error": "Invalid image file"}

            # Process image
            processed_image = await self._process_image(file_path)
            if not processed_image:
                return {"error": "Failed to process image"}

            # Analyze with Vision API
            analysis_result = await self._analyze_with_vision_api(
                processed_image, session_context
            )

            logger.info(f"Image analysis completed: {analysis_result}")
            return analysis_result

        except Exception as e:
            logger.error(f"Error analyzing image: {e}", exc_info=True)
            return {"error": f"Image analysis failed: {str(e)}"}

    async def validate_image_file(self, file_path: Path) -> bool:
        """
        Validate image file format and size.

        Args:
            file_path: Path to image file

        Returns:
            True if valid, False otherwise
        """
        try:
            if not file_path.exists():
                logger.warning(f"Image file does not exist: {file_path}")
                return False

            # Check file size
            file_size = file_path.stat().st_size
            if file_size > self.settings.max_image_size:
                logger.warning(f"Image file too large: {file_size} bytes")
                return False

            # Validate image format
            try:
                with Image.open(file_path) as img:
                    img.verify()
                logger.info(f"Image file validation passed: {file_path}")
                return True
            except Exception as e:
                logger.warning(f"Invalid image format: {e}")
                return False

        except Exception as e:
            logger.error(f"Error validating image file: {e}", exc_info=True)
            return False

    async def _process_image(self, file_path: Path) -> Optional[str]:
        """
        Process image for Vision API (resize, convert format).

        Args:
            file_path: Path to image file

        Returns:
            Base64 encoded image data or None if failed
        """
        try:
            logger.info(f"Processing image for Vision API: {file_path}")

            # Open and process image
            with Image.open(file_path) as img:
                # Convert to RGB if necessary
                if img.mode != "RGB":
                    img = img.convert("RGB")

                # Resize if too large (max 2048x2048 for Vision API)
                max_size = 2048
                if img.width > max_size or img.height > max_size:
                    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

                # Convert to base64
                import io
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=85)
                image_data = base64.b64encode(buffer.getvalue()).decode("utf-8")

                logger.info("Image processing completed")
                return image_data

        except Exception as e:
            logger.error(f"Error processing image: {e}", exc_info=True)
            return None

    async def _analyze_with_vision_api(
        self, image_data: str, session_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze image using GPT-4 Vision API.

        Args:
            image_data: Base64 encoded image data
            session_context: Current session context

        Returns:
            Analysis results
        """
        try:
            logger.info("Analyzing image with Vision API")

            # Create prompt for image analysis
            prompt = f"""
            Analyze this image for educational content and context.
            
            Current session context: {session_context or "No context available"}
            
            Please provide a JSON response with the following fields:
            - content_type: "text", "math_problem", "diagram", "photo", "chart", or "other"
            - extracted_text: any text visible in the image
            - subject: educational subject (e.g., "mathematics", "physics", "language", "general")
            - topic: specific topic within the subject
            - complexity_level: integer from 0-9 indicating complexity
            - questions: list of potential questions about the content
            - context_match: boolean indicating if this relates to current session context
            - educational_value: "high", "medium", "low", or "none"
            - confidence: float from 0.0-1.0 indicating confidence in the analysis
            
            Respond only with valid JSON, no additional text.
            """

            # Call Vision API
            response = await self.openai_client.chat.completions.create(
                model=self.vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                temperature=0.3,
                max_tokens=1000
            )

            # Parse JSON response
            import json
            result = json.loads(response.choices[0].message.content)
            
            # Validate and set defaults
            result.setdefault("content_type", "unknown")
            result.setdefault("extracted_text", "")
            result.setdefault("subject", "general")
            result.setdefault("topic", "unknown")
            result.setdefault("complexity_level", 5)
            result.setdefault("questions", [])
            result.setdefault("context_match", False)
            result.setdefault("educational_value", "medium")
            result.setdefault("confidence", 0.7)

            logger.info(f"Vision API analysis completed: {result}")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Vision API response as JSON: {e}")
            # Fallback result
            return {
                "content_type": "unknown",
                "extracted_text": "",
                "subject": "general",
                "topic": "unknown",
                "complexity_level": 5,
                "questions": [],
                "context_match": False,
                "educational_value": "medium",
                "confidence": 0.5,
            }
        except Exception as e:
            logger.error(f"Error in Vision API analysis: {e}", exc_info=True)
            return {"error": f"Vision API analysis failed: {str(e)}"}

    async def extract_text_from_image(self, file_path: Path) -> str:
        """
        Extract text from image using OCR.

        Args:
            file_path: Path to image file

        Returns:
            Extracted text
        """
        try:
            logger.info(f"Extracting text from image: {file_path}")

            # TODO: Implement actual OCR extraction
            # This is a placeholder for the actual implementation
            await asyncio.sleep(0.1)  # Simulate processing time

            # Placeholder result
            extracted_text = "OCR text extraction not yet implemented"
            logger.info(f"Text extraction completed: {len(extracted_text)} characters")
            return extracted_text

        except Exception as e:
            logger.error(f"Error extracting text from image: {e}", exc_info=True)
            return ""

    async def identify_content_type(self, file_path: Path) -> str:
        """
        Identify the type of content in the image.

        Args:
            file_path: Path to image file

        Returns:
            Content type description
        """
        try:
            logger.info(f"Identifying content type: {file_path}")

            # TODO: Implement actual content type identification
            # This is a placeholder for the actual implementation
            await asyncio.sleep(0.1)  # Simulate processing time

            # Placeholder result
            content_type = "unknown"
            logger.info(f"Content type identification completed: {content_type}")
            return content_type

        except Exception as e:
            logger.error(f"Error identifying content type: {e}", exc_info=True)
            return "unknown"

    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported image formats.

        Returns:
            List of supported format extensions
        """
        return [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]

    async def optimize_image_for_analysis(
        self, input_path: Path, output_path: Path
    ) -> bool:
        """
        Optimize image for better analysis results.

        Args:
            input_path: Input image path
            output_path: Output image path

        Returns:
            True if optimization successful, False otherwise
        """
        try:
            logger.info(f"Optimizing image: {input_path} -> {output_path}")

            with Image.open(input_path) as img:
                # Convert to RGB
                if img.mode != "RGB":
                    img = img.convert("RGB")

                # Enhance contrast and brightness
                from PIL import ImageEnhance
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.2)

                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(1.1)

                # Save optimized image
                img.save(output_path, "JPEG", quality=90)

            logger.info("Image optimization completed")
            return True

        except Exception as e:
            logger.error(f"Error optimizing image: {e}", exc_info=True)
            return False
