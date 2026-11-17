"""
Configuration module for Kinochi Bot Pro.
Loads settings from .env file or environment variables.
"""
import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

# Base Directory
BASE_DIR = Path(__file__).resolve().parent

# Load .env file
load_dotenv(BASE_DIR / ".env")

class Settings(BaseModel):
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
    BOT_USERNAME: str = os.getenv("BOT_USERNAME", "kinochi_robot")
    ADMIN_IDS: list[int] = [
        int(x.strip()) for x in os.getenv("ADMIN_IDS", "123456789").split(",") if x.strip().isdigit()
    ]
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", str(BASE_DIR / "kinochi.db"))
    
    # Web Dashboard Settings
    WEB_HOST: str = os.getenv("WEB_HOST", "0.0.0.0")
    WEB_PORT: int = int(os.getenv("WEB_PORT", "8080"))
    WEB_ADMIN_USERNAME: str = os.getenv("WEB_ADMIN_USERNAME", "admin")
    WEB_ADMIN_PASSWORD: str = os.getenv("WEB_ADMIN_PASSWORD", "kinochi2026")
    WEB_SECRET_KEY: str = os.getenv("WEB_SECRET_KEY", "super-secret-kino-key-2026")
    
    # Defaults
    DEFAULT_DAILY_LIMIT: int = int(os.getenv("DEFAULT_DAILY_LIMIT", "10"))
    TIMEZONE: str = os.getenv("TIMEZONE", "Asia/Tashkent")

settings = Settings()
