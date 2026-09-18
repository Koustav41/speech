import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # Bhashini ULCA API Credentials
    BHASHINI_USER_ID: str = Field(default="", description="Bhashini ULCA User ID")
    BHASHINI_API_KEY: str = Field(default="", description="Bhashini ULCA API Key")
    BHASHINI_PIPELINE_ID: str = Field(default="", description="Bhashini ULCA Pipeline ID")
    BHASHINI_INFERENCE_API_KEY: str = Field(default="", description="Bhashini Inference API Key if known")
    
    BHASHINI_PIPELINE_CONFIG_URL: str = Field(
        default="https://meity-auth.ulca.ai/ulca/apis/v0/model/getModelsPipeline",
        description="Endpoint to query pipeline configs"
    )
    BHASHINI_COMPUTE_URL: str = Field(
        default="https://dhruva-api.bhashini.gov.in/services/inference/pipeline",
        description="Endpoint to execute pipeline inference"
    )

    # Google Gemini API Credentials
    GEMINI_API_KEY: str = Field(default="", description="Google Gemini API Key")
    GEMINI_MODEL: str = Field(default="gemini-3.5-flash-lite", description="Gemini model for audio inference")
    
    # Engine routing: "auto" | "bhashini" | "gemini"
    DEFAULT_PROVIDER: str = Field(default="auto", description="Default transcription and translation provider")

    # General
    MOCK_MODE: bool = Field(default=False, description="Enable simulated responses for local offline testing")
    HOST: str = Field(default="0.0.0.0", description="Backend host")
    PORT: int = Field(default=8000, description="Backend port")
    CORS_ORIGINS: List[str] = Field(
        default=["*"],
        description="Allowed CORS origins"
    )

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
