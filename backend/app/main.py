import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import MODEL_PATH, SCALER_PATH, ALLOWED_ORIGINS
from app import inference
from app.routes import predict, health

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    status = inference.load_artifacts(MODEL_PATH, SCALER_PATH)
    if status["model_loaded"] and status["scaler_loaded"]:
        logger.info("Artifacts loaded successfully - server ready")
    else:
        logger.warning(f"Failed to load artifacts: Model={MODEL_PATH}, Scaler={SCALER_PATH}")
    yield


app = FastAPI(
    title="Epileptic Seizure Prediction API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(predict.router)
