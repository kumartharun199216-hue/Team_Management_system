import os
from pydantic_settings import BaseSettings

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

class Settings(BaseSettings):
    PROJECT_NAME: str = "Advanced Project & Team Management System"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "project-manager-super-secret-key-2025"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    DATABASE_URL: str = f"sqlite:///{os.path.join(BASE_DIR, 'project_management.db')}"

    model_config = {
        "case_sensitive": True,
        "env_file": ".env"
    }

settings = Settings()
