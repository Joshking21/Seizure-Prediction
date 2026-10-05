import time
import logging
import numpy as np
import joblib
import pywt
from scipy import signal
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_model = None
_scaler = None
_startup_time = time.time()


def load_artifacts(model_path: Path, scaler_path: Path) -> dict:
    global _model, _scaler
    status = {"model_loaded": False, "scaler_loaded": False}

    try:
        import tensorflow as tf
        tf.get_logger().setLevel("ERROR")
        _model = tf.keras.models.load_model(str(model_path))
        dummy_cnn = np.zeros((1, 18, 20), dtype=np.float32)
        dummy_lstm = np.zeros((1, 5, 72), dtype=np.float32)
        _model.predict([dummy_cnn, dummy_lstm], verbose=0)
        status["model_loaded"] = True
        logger.info(f"Model loaded from {model_path}")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")

    try:
        _scaler = joblib.load(str(scaler_path))
        status["scaler_loaded"] = True
        logger.info(f"Scaler loaded from {scaler_path}")
    except Exception as e:
        logger.error(f"Failed to load scaler: {e}")

    return status


def is_ready() -> bool:
    return _model is not None and _scaler is not None


def get_uptime() -> float:
    return time.time() - _startup_time


def predict_window(eeg_data: list, sampling_rate: int = 256) -> dict:
    if not is_ready():
        raise RuntimeError("Model or scaler not loaded.")

    t_start = time.time()
    signal = np.array(eeg_data, dtype=np.float32)
    if signal.ndim != 2:
        raise ValueError(f"Expected 2D array, got {signal.ndim}D")

    n_channels, n_samples = signal.shape
    expected_samples = int(5.0 * sampling_rate)

    if n_samples < expected_samples:
        pad = expected_samples - n_samples
        signal = np.pad(signal, ((0, 0), (0, pad)), mode="edge")
    elif n_samples > expected_samples:
        signal = signal[:, :expected_samples]

    if n_channels < 18:
        pad_ch = 18 - n_channels
        signal = np.pad(signal, ((0, pad_ch), (0, 0)), mode="constant")
    signal = signal[:18, :]

    filtered = _apply_bandpass(signal, sampling_rate)
    features = _extract_features(filtered)

    if _scaler is None:
        raise RuntimeError("Scaler not loaded.")
    features_scaled = _scaler.transform(features.reshape(1, -1))

    X_cnn, X_lstm = _reshape_for_model(features_scaled)

    if _model is None:
        raise RuntimeError("Model not loaded.")
    prob = float(_model.predict([X_cnn, X_lstm], verbose=0)[0][0])
    processing_ms = (time.time() - t_start) * 1000

    if prob >= 0.75:
        alert_level = "HIGH"
        prediction = "PRE-ICTAL"
    elif prob >= 0.50:
        alert_level = "MEDIUM"
        prediction = "PRE-ICTAL"
    else:
        alert_level = "LOW"
        prediction = "INTER-ICTAL"

    return {
        "probability": round(prob, 4),
        "prediction": prediction,
        "alert_level": alert_level,
        "confidence": f"{prob * 100:.1f}%",
        "processing_ms": round(processing_ms, 2),
    }


def _apply_bandpass(sig_arr: np.ndarray, fs: int) -> np.ndarray:
    nyq = 0.5 * fs
    low = 0.5 / nyq
    high = 40.0 / nyq
    sos = signal.butter(4, [low, high], btype="bandpass", output="sos")
    out = np.zeros_like(sig_arr, dtype=np.float32)
    for ch in range(sig_arr.shape[0]):
        out[ch] = signal.sosfiltfilt(sos, sig_arr[ch]).astype(np.float32)
    return out


def _compute_stats(coeffs: np.ndarray) -> np.ndarray:
    c = coeffs.astype(np.float64)
    sq = c ** 2
    p = sq / float(np.sum(sq) + 1e-12)
    return np.array([
        np.mean(c),
        np.std(c),
        np.sum(sq),
        float(-np.sum(p * np.log(p + 1e-12))),
    ], dtype=np.float32)


def _extract_features(signal: np.ndarray) -> np.ndarray:
    n_channels = signal.shape[0]
    band_idx = {"delta": 0, "theta": 1, "alpha": 2, "beta": 3, "gamma": 4}
    bands = ["delta", "theta", "alpha", "beta", "gamma"]
    tensor = np.zeros((n_channels, 5, 4), dtype=np.float32)

    for ch in range(n_channels):
        coeffs = pywt.wavedec(signal[ch].astype(np.float64), wavelet="db4", level=5)
        for b_idx, band in enumerate(bands):
            tensor[ch, b_idx, :] = _compute_stats(coeffs[band_idx[band]])

    return tensor.flatten()


def _reshape_for_model(X_flat: np.ndarray):
    batch = X_flat.shape[0]
    tensor = X_flat.reshape(batch, 18, 5, 4)
    X_cnn = tensor.reshape(batch, 18, 20).astype(np.float32)
    X_lstm = tensor.transpose(0, 2, 1, 3).reshape(batch, 5, 72).astype(np.float32)
    return X_cnn, X_lstm
