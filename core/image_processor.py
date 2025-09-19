"""Image processor for downloading and preparing images for analysis."""

import asyncio
import base64
import logging
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import openai
from PIL import Image
from aiogram import Bot
from settings.config import get_settings

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Handles image downloading, processing, and preparation for analysis."""

    def __init__(self, bot: Optional[Bot] = None):
        """Initialize image processor with configuration."""
        self.settings = get_settings()
        self.bot = bot
        self.temp_dir = Path(self.settings.temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize OpenAI client for Vision API
        self.openai_client = openai.AsyncOpenAI(
            api_key=self.settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1"
        )

    async def download_image(self, file_id: str) -> Optional[Path]:
        """
        Download image from Telegram to temporary location.

        Args:
            file_id: Telegram file ID

        Returns:
            Path to downloaded file or None if failed
        """
        try:
            if not self.bot:
                logger.error("Bot instance not available for file download")
                return None

            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(
                dir=self.temp_dir, suffix=".jpg", delete=False
            )
            temp_path = Path(temp_file.name)
            temp_file.close()

            logger.info(f"Downloading image file {file_id} to {temp_path}")
            
            # Download file from Telegram
            file = await self.bot.get_file(file_id)
            if not file:
                logger.error(f"Failed to get file info for {file_id}")
                return None

            # Download file content
            file_content = await self.bot.download_file(file.file_path)
            if not file_content:
                logger.error(f"Failed to download file content for {file_id}")
                return None

            # Write content to temporary file
            with open(temp_path, 'wb') as f:
                f.write(file_content.read())

            logger.info(f"Successfully downloaded image file to {temp_path}")
            return temp_path

        except Exception as e:
            logger.error(f"Error downloading image: {e}", exc_info=True)
            return None

    async def prepare_image(self, file_path: Path) -> Optional[str]:
        """
        Prepare image for analysis by resizing and converting to base64.

        Args:
            file_path: Path to image file

        Returns:
            Base64 encoded image data or None if failed
        """
        try:
            logger.info(f"Preparing image for analysis: {file_path}")

            # Validate image file
            if not await self.validate_image_file(file_path):
                return None

            # Open and process image
            with Image.open(file_path) as img:
                # Convert to RGB if necessary
                if img.mode != "RGB":
                    img = img.convert("RGB")

                # Resize if too large (max 1024x1024 as per plan)
                max_size = 1024
                if img.width > max_size or img.height > max_size:
                    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

                # Convert to base64
                import io
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=85)
                image_data = base64.b64encode(buffer.getvalue()).decode("utf-8")

                logger.info("Image preparation completed")
                return image_data

        except Exception as e:
            logger.error(f"Error preparing image: {e}", exc_info=True)
            return None

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

            # Check file size (max 20MB as per plan)
            file_size = file_path.stat().st_size
            max_size_mb = 20 * 1024 * 1024  # 20MB
            if file_size > max_size_mb:
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

    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported image formats.

        Returns:
            List of supported format extensions
        """
        return [".jpg", ".jpeg", ".png", ".gif", ".webp"]

    async def cleanup_file(self, file_path: Path) -> None:
        """
        Clean up temporary file.

        Args:
            file_path: Path to file to clean up
        """
        try:
            if file_path.exists():
                file_path.unlink()
                logger.debug(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup file {file_path}: {e}")

    async def process_image_for_analysis(
        self, file_id: str, session_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Complete image processing pipeline: download, prepare, and analyze.

        Args:
            file_id: Telegram file ID
            session_context: Current session context

        Returns:
            Analysis results
        """
        try:
            logger.info(f"Processing image for analysis: {file_id}")

            # Download image
            file_path = await self.download_image(file_id)
            if not file_path:
                return {"error": "Failed to download image"}

            # Prepare image
            image_data = await self.prepare_image(file_path)
            if not image_data:
                await self.cleanup_file(file_path)
                return {"error": "Failed to prepare image"}

            # Analyze with Vision API
            analysis_result = await self._analyze_with_vision_api(
                image_data, session_context
            )

            # Clean up temporary file
            await self.cleanup_file(file_path)

            logger.info(f"Image processing completed: {analysis_result}")
            return analysis_result

        except Exception as e:
            logger.error(f"Error processing image: {e}", exc_info=True)
            return {"error": f"Image processing failed: {str(e)}"}

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
            - visual_elements: description of key visual elements that could be discussed
            - discussion_points: list of suggested topics for engaging conversation
            - interest_level: "high", "medium", or "low" indicating how interesting/engaging this content might be
            - confidence: float from 0.0-1.0 indicating confidence in the analysis
            
            Respond only with valid JSON, no additional text.
            """

            # Call Vision API
            response = await self.openai_client.chat.completions.create(
                model=self.settings.vision_model,
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
            import re
            response_content = response.choices[0].message.content
            logger.info(f"Vision API raw response: {repr(response_content)}")
            
            if not response_content:
                logger.error("Vision API returned empty response")
                raise json.JSONDecodeError("Empty response", "", 0)
            
            # Extract JSON from markdown code block if present
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_content, re.DOTALL)
            if json_match:
                json_content = json_match.group(1)
                logger.info(f"Extracted JSON from markdown: {json_content}")
            else:
                json_content = response_content.strip()
            
            result = json.loads(json_content)
            
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
