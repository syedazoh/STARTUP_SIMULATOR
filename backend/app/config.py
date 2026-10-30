"""Application Configuration"""
from typing import List, Optional, Union

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Insecure out-of-the-box values — fine for local dev (see credential_master_key's
# docstring below), but must never be what a production deploy is actually running
# on. Settings.validate_production_secrets fails startup loudly if debug=False and
# either default is still in effect, instead of silently signing tokens / encrypting
# credentials with a value anyone can read in this file's git history.
_DEFAULT_SECRET_KEY = "your-secret-key-change-in-production"
_DEFAULT_CREDENTIAL_MASTER_KEY = "iJ7xpFNwPD8CwdnW0NN6viQNZ0OF-87hwCWMbswRUWQ="


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

    secret_key: str = _DEFAULT_SECRET_KEY
    access_token_expire_minutes: int = Field(default=15, ge=1, le=60)
    refresh_token_expire_days: int = Field(default=7, ge=1, le=30)

    # Master key for the credential vault's envelope encryption (see
    # core/crypto.py). Must be a Fernet key — generate one with
    # `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`.
    # Never commit a real value; local dev falls back to a fixed key so the
    # app still runs out of the box, but anything storing real credentials
    # must override this via the environment.
    credential_master_key: str = _DEFAULT_CREDENTIAL_MASTER_KEY

    # Comma-separated list of origins allowed to call the API with credentials
    # (see main.py's CORSMiddleware). Defaults cover the Vite dev server and
    # its dev-mode proxy target; override in production with the deployed
    # frontend origin(s).
    # Union permits raw CSV to reach the validator in pydantic-settings 2.2,
    # which otherwise JSON-decodes list fields before validators run.
    allowed_origins: Union[List[str], str] = ["http://localhost:5173", "http://localhost:8000"]

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def _split_csv_origins(cls, value):
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @model_validator(mode="after")
    def _reject_default_secrets_in_production(self) -> "Settings":
        if self.debug:
            return self
        insecure = []
        if not self.secret_key or self.secret_key == _DEFAULT_SECRET_KEY:
            insecure.append("SECRET_KEY")
        if not self.credential_master_key or self.credential_master_key == _DEFAULT_CREDENTIAL_MASTER_KEY:
            insecure.append("CREDENTIAL_MASTER_KEY")
        if insecure:
            raise ValueError(
                f"Refusing to start with debug=False while still using the default "
                f"value for: {', '.join(insecure)}. Set a real secret via the "
                f"environment before running in production."
            )
        return self


settings = Settings()
