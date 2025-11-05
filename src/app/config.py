# app/config.py
from typing import Optional, ClassVar
from pathlib import Path
import os

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Application settings.
    """

    # compute .env path relative to the repo (src/.env) and mark it as ClassVar
    env_path: ClassVar[Path] = Path(__file__).resolve().parent.parent / ".env"

    # instruct pydantic to load that env file
    model_config = SettingsConfigDict(env_file=str(env_path), case_sensitive=False)

    # Database
    DATABASE_URL: str

    # Gemini (Google Generative AI)
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

# --- optional quick debug: print env-file used and whether key is present

# instantiate settings for imports across the app
settings = Settings()
