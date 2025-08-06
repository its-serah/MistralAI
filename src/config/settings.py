"""Configuration settings for MistralAI application"""

import os
from typing import Optional
from pydantic import BaseSettings, Field, validator


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Mistral AI Configuration
    mistral_api_key: str = Field(..., env="MISTRAL_API_KEY")
    mistral_model: str = Field(default="mistral-small", env="MISTRAL_MODEL")
    mistral_api_url: str = Field(
        default="https://api.mistral.ai/v1/chat/completions",
        env="MISTRAL_API_URL"
    )
    
    # Audio Processing Configuration
    audio_sample_rate: Optional[int] = Field(default=None, env="AUDIO_SAMPLE_RATE")
    max_audio_duration: int = Field(default=300, env="MAX_AUDIO_DURATION")  # seconds
    supported_formats: list = Field(default=[".mp3", ".wav", ".flac", ".m4a"])
    
    # Output Configuration
    output_directory: str = Field(default="./output", env="OUTPUT_DIR")
    temp_directory: str = Field(default="./temp", env="TEMP_DIR")
    
    # LLM Guardrails Configuration
    max_tokens: int = Field(default=1000, env="MAX_TOKENS")
    temperature: float = Field(default=0.7, env="TEMPERATURE")
    max_retries: int = Field(default=3, env="MAX_RETRIES")
    request_timeout: int = Field(default=30, env="REQUEST_TIMEOUT")
    
    # Security Configuration
    allowed_file_size_mb: int = Field(default=50, env="MAX_FILE_SIZE_MB")
    enable_content_filter: bool = Field(default=True, env="ENABLE_CONTENT_FILTER")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @validator("mistral_api_key")
    def validate_api_key(cls, v):
        if not v or len(v) < 10:
            raise ValueError("MISTRAL_API_KEY must be provided and valid")
        return v
    
    @validator("temperature")
    def validate_temperature(cls, v):
        if not 0.0 <= v <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        return v
    
    @validator("max_tokens")
    def validate_max_tokens(cls, v):
        if v <= 0 or v > 4000:
            raise ValueError("Max tokens must be between 1 and 4000")
        return v
    
    def create_directories(self):
        """Create necessary directories if they don't exist"""
        for directory in [self.output_directory, self.temp_directory]:
            os.makedirs(directory, exist_ok=True)


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the application settings singleton"""
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.create_directories()
    return _settings
