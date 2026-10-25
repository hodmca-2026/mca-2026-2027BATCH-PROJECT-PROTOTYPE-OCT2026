from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.core.config import settings
from app.core.database import Base, engine
from app.core.seed import seed_demo_doctors
from app.models import models  # noqa: F401 -- registers tables before create_all
from app.routers import auth, cases, doctors, health, models_router, predictions, reports, symptoms

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Research/educational MRI decision-support system: symptom questionnaire, CNN "
                "prediction, Grad-CAM explainability, an AI-assisted draft report reviewed by a "
                "doctor/researcher, and specialist suggestions. NOT an autonomous diagnostic tool.",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)
seed_demo_doctors()

for r in (health.router, auth.router, symptoms.router, cases.router, predictions.router,
          reports.router, doctors.router, models_router.router):
    app.include_router(r)


@app.get("/api/files/{file_path:path}")
def serve_file(file_path: str):
    """Serves uploaded MRIs and Grad-CAM images. Paths are relative to UPLOAD_DIR and
    resolved safely so '..' tricks cannot escape the uploads folder."""
    base = settings.UPLOAD_DIR.resolve()
    target = (base / file_path).resolve()
    if base not in target.parents or not target.is_file():
        raise HTTPException(404, "File not found")
    return FileResponse(target)


@app.get("/")
def root():
    return {
        "project": settings.PROJECT_NAME, "docs": "/docs",
        "disclaimer": "Research and educational decision-support tool only. Not an autonomous diagnostic device.",
    }
