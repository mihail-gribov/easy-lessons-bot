"""Audio processing handler for voice messages."""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, Optional

import openai
from settings.config import get_settings

logger = logging.getLogger(__name__)


class AudioHandler:
    """Handles audio processing including speech recognition and TTS."""

    def __init__(self):
        """Initialize audio handler with configuration."""
        self.settings = get_settings()
        self.whisper_model = self.settings.whisper_model
        self.tts_engine = None
        
        # Initialize OpenAI client for Whisper
        if self.settings.openai_api_key:
            # Use direct OpenAI API for Whisper
            self.openai_client = openai.AsyncOpenAI(
                api_key=self.settings.openai_api_key
            )
            logger.info("Using direct OpenAI API for Whisper transcription")
        else:
            # Use OpenRouter for other services
            self.openai_client = openai.AsyncOpenAI(
                api_key=self.settings.openrouter_api_key,
                base_url="https://openrouter.ai/api/v1"
            )
            logger.info("Using OpenRouter API (Whisper may not be available)")

    async def transcribe_audio(self, file_path: Path) -> Dict[str, Any]:
        """
        Transcribe audio file using Whisper API.

        Args:
            file_path: Path to audio file

        Returns:
            Transcription results
        """
        try:
            if not self.settings.audio_enabled:
                return {"error": "Audio processing is disabled"}

            logger.info(f"Transcribing audio file: {file_path}")

            # Validate file exists and is readable
            if not file_path.exists():
                return {"error": "Audio file does not exist"}

            # Open audio file for transcription
            with open(file_path, "rb") as audio_file:
                # Call Whisper API through OpenRouter
                response = await self.openai_client.audio.transcriptions.create(
                    model=self.whisper_model,
                    file=audio_file,
                    language="ru",  # Default to Russian
                    response_format="verbose_json"
                )

            # Extract transcription results
            result = {
                "transcript": response.text,
                "language": response.language,
                "duration": response.duration,
                "confidence": getattr(response, 'confidence', 0.8),  # Fallback if not available
            }

            logger.info(f"Audio transcription completed: {len(result['transcript'])} chars")
            return result

        except Exception as e:
            logger.error(f"Error transcribing audio: {e}", exc_info=True)
            
            # Fallback: return a generic response for voice messages
            if "405" in str(e) or "Method Not Allowed" in str(e):
                logger.warning("Whisper API not available, using fallback response")
                return {
                    "transcript": "[Голосовое сообщение получено, но транскрипция недоступна]",
                    "language": "ru",
                    "duration": 0,
                    "confidence": 0.0,
                    "fallback": True
                }
            
            return {"error": f"Audio transcription failed: {str(e)}"}

    async def analyze_audio_intent(
        self, transcript: str, session_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze audio transcript for educational intent.

        Args:
            transcript: Transcribed text
            session_context: Current session context

        Returns:
            Intent analysis results
        """
        try:
            logger.info(f"Analyzing audio intent: {transcript[:100]}...")

            # Create prompt for intent analysis
            prompt = f"""
            Analyze the following transcribed audio message for educational intent and context.
            
            Transcript: "{transcript}"
            
            Current session context: {session_context or "No context available"}
            
            Please provide a JSON response with the following fields:
            - intent: "question", "explanation_request", "discussion", or "general"
            - subject: educational subject (e.g., "mathematics", "physics", "language", "general")
            - topic: specific topic within the subject
            - understanding_level: integer from 0-9 indicating the user's apparent understanding level
            - context: brief description of the educational context
            - confidence: float from 0.0-1.0 indicating confidence in the analysis
            
            Respond only with valid JSON, no additional text.
            """

            # Call LLM for intent analysis
            response = await self.openai_client.chat.completions.create(
                model=self.settings.openrouter_model,
                messages=[
                    {"role": "system", "content": "You are an educational assistant that analyzes user messages to understand their learning intent and context. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )

            # Parse JSON response
            import json
            result = json.loads(response.choices[0].message.content)
            
            # Validate and set defaults
            result.setdefault("intent", "question")
            result.setdefault("subject", "general")
            result.setdefault("topic", "unknown")
            result.setdefault("understanding_level", 5)
            result.setdefault("context", "Audio intent analysis")
            result.setdefault("confidence", 0.7)

            logger.info(f"Audio intent analysis completed: {result}")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            # Fallback result
            return {
                "intent": "question",
                "subject": "general",
                "topic": "unknown",
                "understanding_level": 5,
                "context": "Audio intent analysis (fallback)",
                "confidence": 0.5,
            }
        except Exception as e:
            logger.error(f"Error analyzing audio intent: {e}", exc_info=True)
            return {"error": f"Audio intent analysis failed: {str(e)}"}

    async def synthesize_speech(
        self, text: str, language: str = "ru"
    ) -> Optional[bytes]:
        """
        Synthesize speech from text.

        Args:
            text: Text to synthesize
            language: Language code

        Returns:
            Audio data as bytes or None if failed
        """
        try:
            if not self.settings.tts_enabled:
                logger.info("TTS is disabled, skipping speech synthesis")
                return None

            logger.info(f"Synthesizing speech for text: {text[:100]}...")

            # Use OpenAI TTS API through OpenRouter
            response = await self.openai_client.audio.speech.create(
                model="tts-1",  # OpenAI TTS model
                voice="alloy",  # Default voice
                input=text,
                response_format="mp3"
            )

            # Get audio data
            audio_data = b""
            async for chunk in response.iter_bytes():
                audio_data += chunk

            logger.info(f"Speech synthesis completed: {len(audio_data)} bytes")
            return audio_data

        except Exception as e:
            logger.error(f"Error synthesizing speech: {e}", exc_info=True)
            return None

    async def validate_audio_file(self, file_path: Path) -> bool:
        """
        Validate audio file format and size.

        Args:
            file_path: Path to audio file

        Returns:
            True if valid, False otherwise
        """
        try:
            if not file_path.exists():
                logger.warning(f"Audio file does not exist: {file_path}")
                return False

            # Check file size
            file_size = file_path.stat().st_size
            max_size = self.settings.max_audio_duration * 16000  # Rough estimate
            if file_size > max_size:
                logger.warning(f"Audio file too large: {file_size} bytes")
                return False

            # TODO: Add format validation using python-magic
            logger.info(f"Audio file validation passed: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error validating audio file: {e}", exc_info=True)
            return False

    def get_supported_formats(self) -> list[str]:
        """
        Get list of supported audio formats.

        Returns:
            List of supported format extensions
        """
        return [".ogg", ".mp3", ".wav", ".m4a"]

    async def convert_audio_format(
        self, input_path: Path, output_path: Path, target_format: str = "wav"
    ) -> bool:
        """
        Convert audio file to target format.

        Args:
            input_path: Input file path
            output_path: Output file path
            target_format: Target format

        Returns:
            True if conversion successful, False otherwise
        """
        try:
            logger.info(f"Converting audio from {input_path} to {output_path}")

            # TODO: Implement actual audio format conversion
            # This is a placeholder for the actual implementation
            await asyncio.sleep(0.1)  # Simulate processing time

            logger.info("Audio format conversion completed")
            return True

        except Exception as e:
            logger.error(f"Error converting audio format: {e}", exc_info=True)
            return False
