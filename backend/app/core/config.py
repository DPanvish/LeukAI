"""
Application configuration — loaded from environment variables.
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # ── App ──────────────────────────────────────────────
    APP_NAME: str = "Leukemia AI Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # ── Security / JWT ───────────────────────────────────
    SECRET_KEY: str = "super-secret-change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # ── MongoDB ──────────────────────────────────────────
    MONGODB_URL: str = "mongodb+srv://panvishd_db_user:6DNjL0M5tRC6Ta1J@cluster0.tzzfzuf.mongodb.net/?appName=Cluster0"
    MONGODB_DB_NAME: str = "leukemia_ai"

    # ── ML Model ─────────────────────────────────────────
    MODEL_PATH: str = "ml_models/alexnet_leukemia.pt"
    CLASS_NAMES: List[str] = [
        "Benign",
        "Early Pre-B",
        "Pre-B",
        "Pro-B",
    ]

    # ── CORS ─────────────────────────────────────────────
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    # ── Upload ───────────────────────────────────────────
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10 MB
    ALLOWED_EXTENSIONS: List[str] = ["jpg", "jpeg", "png", "bmp", "tiff"]

    class Config:
        env_file = ".env"


settings = Settings()
