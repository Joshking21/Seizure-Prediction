import logging
import numpy as np
from typing import List, Tuple, Dict, Any
from scipy import signal

from src.config import (
    SAMPLING_RATE, BUTTER_ORDER, LOWCUT_HZ, HIGHCUT_HZ,
    WINDOW_SAMPLES, STEP_SAMPLES,
    PRE_ICTAL_MIN, INTER_ICTAL_MIN,
)

logger = logging.getLogger(__name__)

WindowLabel = Tuple[np.ndarray, int]


def preprocess_record(record: Dict[str, Any]) -> List[WindowLabel]:
    signals = record["signals"]
    fs = record["fs"]
    seizures = record["seizures"]

    filtered = _apply_bandpass(signals, fs)
    n_samples = filtered.shape[1]
    sample_map = _build_label_map(n_samples, fs, seizures)
    windows = _extract_windows(filtered, sample_map)
    return windows


def preprocess_realtime_buffer(buffer, fs: int = SAMPLING_RATE) -> np.ndarray:
    if buffer.shape[1] < WINDOW_SAMPLES:
        raise ValueError(
            f"Buffer too short: need {WINDOW_SAMPLES} samples, got {buffer.shape[1]}."
        )
    filtered = _apply_bandpass(buffer, fs)
    window = filtered[:, -WINDOW_SAMPLES:]
    return window[np.newaxis, :, :].astype(np.float32)


def _butter_bandpass_sos(lowcut: float, highcut: float, fs: int, order: int) -> np.ndarray:
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    return signal.butter(order, [low, high], btype="bandpass", output="sos")


def _apply_bandpass(signals, fs: int) -> np.ndarray:
    sos = _butter_bandpass_sos(LOWCUT_HZ, HIGHCUT_HZ, fs, BUTTER_ORDER)
    filtered = np.zeros_like(signals, dtype=np.float32)
    for ch_idx in range(signals.shape[0]):
        filtered[ch_idx] = signal.sosfiltfilt(sos, signals[ch_idx]).astype(np.float32)
    return filtered


def _build_label_map(n_samples: int, fs: int, seizures: List[Dict]) -> np.ndarray:
    label_map = np.full(n_samples, fill_value=-1, dtype=np.int8)

    pre_ictal_samp = PRE_ICTAL_MIN * 60 * fs
    inter_ictal_samp = INTER_ICTAL_MIN * 60 * fs
    ictal_margin = 5 * 60 * fs

    if not seizures:
        label_map[:] = 0
        return label_map

    ictal_intervals = []
    for sz in seizures:
        on = int(sz["onset_sec"] * fs)
        off = int(sz["offset_sec"] * fs)
        ictal_intervals.append((on, min(off + ictal_margin, n_samples)))

    for samp in range(n_samples):
        min_dist = min(
            abs(samp - int(sz["onset_sec"] * fs)) for sz in seizures
        )
        if min_dist >= inter_ictal_samp:
            label_map[samp] = 0

    for sz in seizures:
        on = int(sz["onset_sec"] * fs)
        pre_start = max(0, on - pre_ictal_samp)
        label_map[pre_start:on] = 1

    for (on, off_margin) in ictal_intervals:
        label_map[on:off_margin] = -1

    return label_map


def _extract_windows(filtered, label_map: np.ndarray) -> List[WindowLabel]:
    n_channels, n_samples = filtered.shape
    windows: List[WindowLabel] = []

    start = 0
    while start + WINDOW_SAMPLES <= n_samples:
        end = start + WINDOW_SAMPLES
        centre = (start + end) // 2
        label = int(label_map[centre])

        if label != -1:
            window = filtered[:, start:end].copy()
            windows.append((window, label))

        start += STEP_SAMPLES

    return windows
