# app/config.py
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Application settings.

    - Replace OPENAI keys with GOOGLE_API_KEY / GEMINI_MODEL for Gemini usage.
    - Keep required fields like SECRET_KEY and API_KEY as before.
    """

    # Tell pydantic to read .env and treat env names case-insensitively
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    # Database
    DATABASE_URL: str

    # Gemini (Google Generative AI)
    # Optional so local dev can run without it; warn at runtime if missing.
    GOOGLE_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "models/gemini-2.5-flash"

    # Application
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = True
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10 MB

    # Security
    SECRET_KEY: str
    API_KEY: str

# instantiate settings for imports across the app
settings = Settings()
