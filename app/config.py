import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "Mental Health Crisis Early Warning System for Campuses")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "campus-wellbeing-early-warning-secret-key-2026")
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/campus_wellbeing.db")
    SESSION_COOKIE_NAME: str = "wellbeing_session"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    MIN_GROUP_SIZE_FOR_ADMIN_METRICS: int = int(os.getenv("MIN_GROUP_SIZE_FOR_ADMIN_METRICS", "5"))
    DATA_RETENTION_DAYS: int = int(os.getenv("DATA_RETENTION_DAYS", "365"))
    BASELINE_MIN_DAYS: int = int(os.getenv("BASELINE_MIN_DAYS", "3"))
    MODEL_DIR: Path = BASE_DIR / "ml" / "saved_models"
    MODEL_PATH: Path = MODEL_DIR / "wellbeing_model.joblib"

settings = Settings()
settings.MODEL_DIR.mkdir(parents=True, exist_ok=True)
