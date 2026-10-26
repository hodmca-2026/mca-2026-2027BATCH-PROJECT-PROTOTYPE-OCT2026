"""
Centralized settings, loaded from environment variables (.env supported).

DATABASE_URL defaults to local SQLite for development so the project runs
out-of-the-box with zero external services. For the production-style
SQL Server setup required by the project spec, set DATABASE_URL to a
SQL Server connection string, e.g.:

    DATABASE_URL=mssql+pyodbc://sa:YourPass123@localhost:1433/BrainTumorDB?driver=ODBC+Driver+17+for+SQL+Server

This keeps local dev/demo friction-free (SQLite, no server to install)
while the schema (see app/models/models.py) is plain SQLAlchemy and works
unchanged against SQL Server -- swap the URL, run the same
`Base.metadata.create_all`, done.
"""
from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    PROJECT_NAME: str = "XAI & GenAI Based MRI Brain Tumor Detection"
    ENV: str = "development"

    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'app.db'}"

    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_env_var_SECRET_KEY"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120

    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    MAX_UPLOAD_MB: int = 10
    ALLOWED_IMAGE_TYPES: tuple = ("image/jpeg", "image/png")

    # Looks in backend/models/ first (self-contained deploys, e.g. Render/Docker),
    # then falls back to ml/models/ (local dev right after running ml/train.py).
    MODEL_PATH: Path = (
        BASE_DIR / "models" / "best_model.pth"
        if (BASE_DIR / "models" / "best_model.pth").exists()
        else BASE_DIR.parent / "ml" / "models" / "best_model.pth"
    )
    METRICS_PATH: Path = (
        BASE_DIR / "models" / "metrics.json"
        if (BASE_DIR / "models" / "metrics.json").exists()
        else BASE_DIR.parent / "ml" / "models" / "metrics.json"
    )

    # Optional: if set, GenAI report assistant will call Anthropic's API
    # to phrase the draft report; if unset, a deterministic template is
    # used instead. Either way, only verified case/model data is passed in
    # and the output is always labeled as an AI-generated draft.
    ANTHROPIC_API_KEY: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
