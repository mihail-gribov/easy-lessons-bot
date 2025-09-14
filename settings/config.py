"""Application configuration using pydantic-settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="",
    )

    # Telegram Bot Configuration
    telegram_bot_token: str = Field(
        ...,
        description="Telegram bot token from BotFather",
        min_length=1,
    )

    # OpenRouter API Configuration
    openrouter_api_key: str = Field(
        ...,
        description="OpenRouter API key for LLM access",
        min_length=1,
    )
    
    # OpenAI API Configuration (for Whisper)
    openai_api_key: str = Field(
        default="",
        description="OpenAI API key for Whisper transcription (optional)",
    )
    openrouter_model: str = Field(
        default="gpt-4o-mini",
        description="OpenRouter model to use",
    )

    # LLM Parameters
    llm_temperature: float = Field(
        default=0.9,
        description="LLM temperature parameter (0.0-2.0)",
        ge=0.0,
        le=2.0,
    )
    llm_max_tokens: int = Field(
        default=6000,
        description="Maximum tokens for LLM response",
        ge=1,
        le=32000,
    )

    # Application Settings
    history_limit: int = Field(
        default=30,
        description="Maximum number of messages to keep in history",
        ge=1,
        le=100,
    )

    # Database Configuration
    database_enabled: bool = Field(
        default=True,
        description="Enable database persistence",
    )
    database_path: str = Field(
        default="data/bot.db",
        description="Path to SQLite database file",
    )
    database_cleanup_hours: int = Field(
        default=168,  # 7 days
        description="Hours after which to cleanup old sessions",
        ge=1,
        le=8760,  # 1 year
    )

    # Multimedia Configuration
    audio_enabled: bool = Field(
        default=True,
        description="Enable audio processing (voice messages)",
    )
    image_analysis_enabled: bool = Field(
        default=True,
        description="Enable image analysis through Vision API",
    )
    whisper_model: str = Field(
        default="whisper-1",
        description="Whisper model for speech recognition",
    )
    tts_enabled: bool = Field(
        default=False,
        description="Enable text-to-speech synthesis",
    )
    tts_provider: str = Field(
        default="gtts",
        description="TTS provider (gtts, pyttsx3)",
    )
    vision_model: str = Field(
        default="gpt-4o",
        description="Vision model for image analysis",
    )
    max_image_size: int = Field(
        default=5242880,  # 5MB
        description="Maximum image file size in bytes",
        ge=1024,
        le=20971520,  # 20MB
    )
    max_audio_duration: int = Field(
        default=60,
        description="Maximum audio duration in seconds",
        ge=1,
        le=300,  # 5 minutes
    )
    temp_dir: str = Field(
        default="data/temp",
        description="Directory for temporary media files",
    )


# Global settings instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get application settings singleton instance."""
    global _settings  # noqa: PLW0603
    if _settings is None:
        _settings = Settings()
    return _settings
