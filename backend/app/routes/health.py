from fastapi import APIRouter
from app.schemas.prediction import HealthResponse
from app import inference

router = APIRouter(tags=["Health"])


@router.get("/")
async def root():
    return {
        "message": "Seizure Prediction API",
        "project": "Final Year Project",
        "version": "1.0.0",
        "docs": "/docs",
    }


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="ok" if inference.is_ready() else "degraded",
        model_loaded=inference._model is not None,
        scaler_loaded=inference._scaler is not None,
        model_version="1.0.0",
        uptime_seconds=round(inference.get_uptime(), 1),
    )
