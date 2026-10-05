import logging
import numpy as np
import pywt
from typing import Tuple, List

from src.config import (
    WAVELET, DWT_LEVEL, BAND_NAMES, STAT_FEATURES,
    N_CHANNELS, N_FEATURES,
)

logger = logging.getLogger(__name__)

_BAND_COEFF_IDX = {
    "delta": 0,
    "theta": 1,
    "alpha": 2,
    "beta":  3,
    "gamma": 4,
}


def extract_features(window: np.ndarray) -> np.ndarray:
    n_channels = window.shape[0]
    feature_tensor = np.zeros((n_channels, len(BAND_NAMES), len(STAT_FEATURES)), dtype=np.float32)

    for ch_idx in range(n_channels):
        channel_signal = window[ch_idx].astype(np.float64)
        coeffs = pywt.wavedec(channel_signal, wavelet=WAVELET, level=DWT_LEVEL)

        for band_idx, band_name in enumerate(BAND_NAMES):
            coeff_idx = _BAND_COEFF_IDX[band_name]
            coeff_arr = coeffs[coeff_idx]
            stats = _compute_stats(coeff_arr)
            feature_tensor[ch_idx, band_idx, :] = stats

    return feature_tensor.flatten()


def extract_features_batch(windows: List[np.ndarray]) -> np.ndarray:
    X = np.zeros((len(windows), N_FEATURES), dtype=np.float32)
    for i, win in enumerate(windows):
        X[i] = extract_features(win)
    return X


def reshape_for_model(X_flat) -> Tuple[np.ndarray, np.ndarray]:
    batch = X_flat.shape[0]
    n_bands = len(BAND_NAMES)
    n_stats = len(STAT_FEATURES)

    tensor = X_flat.reshape(batch, N_CHANNELS, n_bands, n_stats)
    X_cnn = tensor.reshape(batch, N_CHANNELS, n_bands * n_stats)
    X_lstm = tensor.transpose(0, 2, 1, 3).reshape(batch, n_bands, N_CHANNELS * n_stats)

    return X_cnn.astype(np.float32), X_lstm.astype(np.float32)


def _compute_stats(coeffs: np.ndarray) -> np.ndarray:
    coeffs = coeffs.astype(np.float64)

    mean = float(np.mean(coeffs))
    std = float(np.std(coeffs))
    energy = float(np.sum(coeffs ** 2))

    sq = coeffs ** 2
    total = float(np.sum(sq) + 1e-12)
    p = sq / total
    entropy = float(-np.sum(p * np.log(p + 1e-12)))

    return np.array([mean, std, energy, entropy], dtype=np.float32)
