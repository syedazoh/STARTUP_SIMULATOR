"""Application Configuration"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings from environment variables"""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Startup Simulator"
    app_version: str = "0.1.0"
    debug: bool = True

    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "startup_simulator"

    chroma_persist_dir: str = "./chroma_data"

    groq_api_key: Optional[str] = None
    groq_model: str = "llama-3.3-70b-versatile"

    secret_key: str = "your-secret-key-change-in-production"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # Master key for the credential vault's envelope encryption (see
    # core/crypto.py). Must be a Fernet key — generate one with
    # `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`.
    # Never commit a real value; local dev falls back to a fixed key so the
    # app still runs out of the box, but anything storing real credentials
    # must override this via the environment.
    credential_master_key: str = "iJ7xpFNwPD8CwdnW0NN6viQNZ0OF-87hwCWMbswRUWQ="


settings = Settings()
