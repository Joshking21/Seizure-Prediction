from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "models" / "seizure_model.h5"
SCALER_PATH = BASE_DIR / "models" / "scaler.joblib"

SAMPLING_RATE = 256
N_CHANNELS = 18
WINDOW_SAMPLES = int(5.0 * SAMPLING_RATE)
STEP_SAMPLES = int(WINDOW_SAMPLES * 0.5)

BUTTER_ORDER = 4
LOWCUT_HZ = 0.5
HIGHCUT_HZ = 40.0

WAVELET = "db4"
DWT_LEVEL = 5
BAND_NAMES = ["delta", "theta", "alpha", "beta", "gamma"]
STAT_NAMES = ["mean", "std", "energy", "entropy"]

THRESHOLD_HIGH = 0.75
THRESHOLD_MEDIUM = 0.50

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8081",
    "http://127.0.0.1:3000",
]
