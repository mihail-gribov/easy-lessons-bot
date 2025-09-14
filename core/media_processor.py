"""Media processing coordinator for handling audio and image content."""

import asyncio
import logging
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from aiogram import Bot
from settings.config import get_settings

logger = logging.getLogger(__name__)


class MediaProcessor:
    """Main coordinator for processing multimedia content."""

    def __init__(self, bot: Optional[Bot] = None):
        """Initialize media processor with configuration."""
        self.settings = get_settings()
        self.temp_dir = Path(self.settings.temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.bot = bot

    async def process_media(
        self,
        file_id: str,
        file_type: str,
        chat_id: str,
        session_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Process media file and return analysis results.

        Args:
            file_id: Telegram file ID
            file_type: Type of media (audio, image, document)
            chat_id: Chat ID for context
            session_context: Current session context

        Returns:
            Dictionary with analysis results
        """
        try:
            logger.info(f"Processing {file_type} media for chat {chat_id}")

            # Check if media type is supported
            if not await self.is_media_supported(file_type):
                return {"error": f"Unsupported file type: {file_type}"}

            # Download file to temporary location
            file_path = await self._download_file(file_id, file_type)
            if not file_path:
                return {"error": "Failed to download file"}

            # Process based on type
            if file_type in ["audio", "voice"]:
                result = await self._process_audio(file_path, session_context)
            elif file_type in ["image", "photo"]:
                result = await self._process_image(file_path, session_context)
            else:
                result = {"error": f"Unsupported file type: {file_type}"}

            # Clean up temporary file
            await self._cleanup_file(file_path)

            return result

        except Exception as e:
            logger.error(f"Error processing media: {e}", exc_info=True)
            return {"error": f"Media processing failed: {str(e)}"}

    async def _download_file(self, file_id: str, file_type: str) -> Optional[Path]:
        """
        Download file from Telegram to temporary location.

        Args:
            file_id: Telegram file ID
            file_type: Type of file

        Returns:
            Path to downloaded file or None if failed
        """
        try:
            if not self.bot:
                logger.error("Bot instance not available for file download")
                return None

            # Create temporary file
            suffix = self._get_file_suffix(file_type)
            temp_file = tempfile.NamedTemporaryFile(
                dir=self.temp_dir, suffix=suffix, delete=False
            )
            temp_path = Path(temp_file.name)
            temp_file.close()

            logger.info(f"Downloading {file_type} file {file_id} to {temp_path}")
            
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

            logger.info(f"Successfully downloaded {file_type} file to {temp_path}")
            return temp_path

        except Exception as e:
            logger.error(f"Error downloading file: {e}", exc_info=True)
            return None

    async def _process_audio(
        self, file_path: Path, session_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process audio file for speech recognition and analysis.

        Args:
            file_path: Path to audio file
            session_context: Current session context

        Returns:
            Analysis results
        """
        try:
            if not self.settings.audio_enabled:
                return {"error": "Audio processing is disabled"}

            logger.info(f"Processing audio file: {file_path}")
            
            # Import AudioHandler here to avoid circular imports
            from core.audio_handler import AudioHandler
            
            # Initialize audio handler and transcribe
            audio_handler = AudioHandler()
            transcription_result = await audio_handler.transcribe_audio(file_path)
            
            if "error" in transcription_result:
                return transcription_result
            
            # Analyze intent from transcript
            intent_result = await audio_handler.analyze_audio_intent(
                transcription_result["transcript"], session_context
            )
            
            # Combine results
            result = {
                "type": "audio",
                "transcript": transcription_result["transcript"],
                "language": transcription_result.get("language", "ru"),
                "duration": transcription_result.get("duration", 0),
                "confidence": transcription_result.get("confidence", 0.8),
            }
            result.update(intent_result)
            
            logger.info(f"Audio processing completed: {len(result['transcript'])} chars")
            return result

        except Exception as e:
            logger.error(f"Error processing audio: {e}", exc_info=True)
            return {"error": f"Audio processing failed: {str(e)}"}

    async def _process_image(
        self, file_path: Path, session_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process image file for visual analysis.

        Args:
            file_path: Path to image file
            session_context: Current session context

        Returns:
            Analysis results
        """
        try:
            if not self.settings.image_analysis_enabled:
                return {"error": "Image analysis is disabled"}

            logger.info(f"Processing image file: {file_path}")
            
            # Import ImageAnalyzer here to avoid circular imports
            from core.image_analyzer import ImageAnalyzer
            
            # Initialize image analyzer and analyze
            image_analyzer = ImageAnalyzer()
            analysis_result = await image_analyzer.analyze_image(file_path, session_context)
            
            if "error" in analysis_result:
                return analysis_result
            
            # Add type information
            result = {
                "type": "image",
            }
            result.update(analysis_result)
            
            logger.info(f"Image processing completed: {result.get('content_type', 'unknown')}")
            return result

        except Exception as e:
            logger.error(f"Error processing image: {e}", exc_info=True)
            return {"error": f"Image processing failed: {str(e)}"}

    async def _cleanup_file(self, file_path: Path) -> None:
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

    def _get_file_suffix(self, file_type: str) -> str:
        """
        Get appropriate file suffix for file type.

        Args:
            file_type: Type of file

        Returns:
            File suffix
        """
        suffix_map = {
            "audio": ".ogg",
            "voice": ".ogg",
            "image": ".jpg",
            "photo": ".jpg",
            "document": ".pdf",
        }
        return suffix_map.get(file_type, ".tmp")

    async def is_media_supported(self, file_type: str) -> bool:
        """
        Check if media type is supported.

        Args:
            file_type: Type of media

        Returns:
            True if supported, False otherwise
        """
        if file_type in ["audio", "voice"]:
            return self.settings.audio_enabled
        elif file_type in ["image", "photo"]:
            return self.settings.image_analysis_enabled
        return False
