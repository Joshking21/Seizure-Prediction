import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
MOCK_DIR = DATA_DIR / "mock"
PROC_DIR = DATA_DIR / "processed"
MODEL_DIR = BASE_DIR / "models" / "saved"

for _d in [RAW_DIR, MOCK_DIR, PROC_DIR, MODEL_DIR]:
    _d.mkdir(parents=True, exist_ok=True)

SAMPLING_RATE = 256
N_CHANNELS = 18

EEG_CHANNELS = [
    "FP1-F7", "F7-T7",  "T7-P7",  "P7-O1",
    "FP1-F3", "F3-C3",  "C3-P3",  "P3-O1",
    "FP2-F4", "F4-C4",  "C4-P4",  "P4-O2",
    "FP2-F8", "F8-T8",  "T8-P8",  "P8-O2",
    "FZ-CZ",  "CZ-PZ",
]

BUTTER_ORDER = 4
LOWCUT_HZ = 0.5
HIGHCUT_HZ = 40.0

WINDOW_SEC = 5.0
OVERLAP_RATIO = 0.50
WINDOW_SAMPLES = int(WINDOW_SEC * SAMPLING_RATE)
STEP_SAMPLES = int(WINDOW_SAMPLES * (1 - OVERLAP_RATIO))

PRE_ICTAL_MIN = 30
INTER_ICTAL_MIN = 30

WAVELET = "db4"
DWT_LEVEL = 5
BAND_NAMES = ["delta", "theta", "alpha", "beta", "gamma"]
STAT_FEATURES = ["mean", "std", "energy", "entropy"]

N_FEATURES = N_CHANNELS * len(BAND_NAMES) * len(STAT_FEATURES)

CNN_FILTERS = [64, 128, 64]
CNN_KERNEL_SIZE = 3
CNN_POOL_SIZE = 2

LSTM_UNITS = [128, 64]
LSTM_DROPOUT = 0.3

META_DENSE_UNITS = [128, 64]
META_DROPOUT = 0.4

BATCH_SIZE = 64
EPOCHS = 50
LEARNING_RATE = 1e-3
VALIDATION_SPLIT = 0.15
TEST_SPLIT = 0.15
RANDOM_SEED = 42
CLASS_WEIGHT_MULTIPLIER = 3.0

MODEL_H5_PATH = MODEL_DIR / "seizure_model.h5"
SCALER_PATH = MODEL_DIR / "scaler.joblib"
METRICS_PATH = MODEL_DIR / "training_metrics.json"
