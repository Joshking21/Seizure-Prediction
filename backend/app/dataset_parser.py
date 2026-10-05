import io
import csv
import json
import logging
import tempfile
import numpy as np
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional

logger = logging.getLogger(__name__)

CANONICAL_CHANNELS = [
    "FP1-F7", "F7-T7", "T7-P7", "P7-O1",
    "FP1-F3", "F3-C3", "C3-P3", "P3-O1",
    "FP2-F4", "F4-C4", "C4-P4", "P4-O2",
    "FP2-F8", "F8-T8", "T8-P8", "P8-O2",
    "FZ-CZ",  "CZ-PZ",
]

SAMPLING_RATE = 256
WINDOW_SAMPLES = int(5.0 * SAMPLING_RATE)
DEFAULT_STEP_SAMPLES = WINDOW_SAMPLES


def parse_uploaded_dataset(
    file_bytes: bytes,
    filename: str,
    step_samples: int = DEFAULT_STEP_SAMPLES,
    max_windows: int = 50,
) -> Tuple[List[np.ndarray], Dict[str, Any]]:
    ext = Path(filename).suffix.lower()

    if ext == ".edf":
        signals, fs, detected_channels = _parse_edf(file_bytes, filename)
        file_format = "edf"
    elif ext == ".csv":
        signals, fs, detected_channels = _parse_csv(file_bytes)
        file_format = "csv"
    elif ext == ".json":
        signals, fs, detected_channels = _parse_json(file_bytes)
        file_format = "json"
    else:
        raise ValueError(f"Unsupported file format '{ext}'.")

    n_channels, total_samples = signals.shape

    if n_channels < 18:
        pad_ch = 18 - n_channels
        signals = np.pad(signals, ((0, pad_ch), (0, 0)), mode="constant")
    elif n_channels > 18:
        signals = signals[:18, :]

    total_duration_sec = total_samples / fs

    windows: List[np.ndarray] = []
    for start in range(0, total_samples - WINDOW_SAMPLES + 1, step_samples):
        win = signals[:, start : start + WINDOW_SAMPLES].astype(np.float32)
        windows.append(win)
        if len(windows) >= max_windows:
            break

    if not windows and total_samples > 0:
        pad_needed = WINDOW_SAMPLES - total_samples
        padded_win = np.pad(signals, ((0, 0), (0, pad_needed)), mode="edge").astype(np.float32)
        windows.append(padded_win)

    metadata = {
        "filename": filename,
        "format": file_format,
        "sampling_rate": fs,
        "total_duration_sec": round(total_duration_sec, 2),
        "total_windows": len(windows),
        "detected_channels": detected_channels,
        "channels": CANONICAL_CHANNELS,
    }

    return windows, metadata


def _parse_edf(file_bytes: bytes, filename: str) -> Tuple[np.ndarray, int, List[str]]:
    try:
        import mne
        set_log = getattr(mne, "set_log_level", None)
        if callable(set_log):
            set_log("WARNING")
    except ImportError:
        raise RuntimeError("MNE library is required to read .edf files.")

    with tempfile.NamedTemporaryFile(suffix=".edf", delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = Path(tmp.name)

    try:
        raw = mne.io.read_raw_edf(str(tmp_path), preload=True, verbose=False)

        rename_map = {}
        for ch in raw.ch_names:
            clean = ch.strip().lstrip(".").rstrip("-0").upper()
            rename_map[ch] = clean
        raw.rename_channels(rename_map)

        matched = [ch for ch in CANONICAL_CHANNELS if ch in raw.ch_names]
        if matched:
            raw.pick_channels(matched)

        if int(raw.info["sfreq"]) != SAMPLING_RATE:
            raw.resample(SAMPLING_RATE, npad="auto")

        signals = raw.get_data().astype(np.float32)
        channels = raw.ch_names
        return signals, SAMPLING_RATE, channels

    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except Exception:
                pass


def _parse_csv(file_bytes: bytes) -> Tuple[np.ndarray, int, List[str]]:
    text = file_bytes.decode("utf-8", errors="ignore").strip()
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        raise ValueError("The uploaded CSV file is empty.")

    first_tokens = [tok.strip() for tok in lines[0].split(",")]
    has_header = any(not _is_float(tok) for tok in first_tokens)

    detected_channels = first_tokens if has_header else [f"CH_{i+1}" for i in range(len(first_tokens))]
    data_lines = lines[1:] if has_header else lines

    matrix = []
    for line in data_lines:
        row = [float(val.strip()) for val in line.split(",") if val.strip()]
        if row:
            matrix.append(row)

    arr = np.array(matrix, dtype=np.float32)
    if arr.ndim != 2 or arr.size == 0:
        raise ValueError("Invalid 2D CSV format.")

    if arr.shape[0] > arr.shape[1] and arr.shape[1] <= 32:
        signals = arr.T
    else:
        signals = arr

    return signals, SAMPLING_RATE, detected_channels[:signals.shape[0]]


def _parse_json(file_bytes: bytes) -> Tuple[np.ndarray, int, List[str]]:
    text = file_bytes.decode("utf-8", errors="ignore")
    parsed = json.loads(text)

    if isinstance(parsed, dict):
        if "eeg_data" in parsed:
            raw_matrix = parsed["eeg_data"]
        elif "signals" in parsed:
            raw_matrix = parsed["signals"]
        elif "windows" in parsed and len(parsed["windows"]) > 0:
            raw_matrix = parsed["windows"][0]
        else:
            raise ValueError("JSON file must contain 'eeg_data' or 'signals' list of channel arrays.")
    elif isinstance(parsed, list):
        raw_matrix = parsed
    else:
        raise ValueError("Invalid JSON data structure for EEG recording.")

    arr = np.array(raw_matrix, dtype=np.float32)
    if arr.ndim == 3:
        arr = np.concatenate(arr, axis=1)

    if arr.ndim != 2:
        raise ValueError(f"Expected 2D EEG array, got {arr.ndim}D array.")

    if arr.shape[0] > arr.shape[1] and arr.shape[1] <= 32:
        signals = arr.T
    else:
        signals = arr

    channels = [f"CH_{i+1}" for i in range(signals.shape[0])]
    return signals, SAMPLING_RATE, channels


def _is_float(val: str) -> bool:
    try:
        float(val)
        return True
    except ValueError:
        return False


def generate_sample_eeg(state: str = "interictal", n_windows: int = 4) -> List[np.ndarray]:
    rng = np.random.default_rng(42 if state == "interictal" else 101)
    windows = []
    dt = 1.0 / SAMPLING_RATE
    t = np.arange(WINDOW_SAMPLES) * dt

    for _ in range(n_windows):
        win = np.zeros((18, WINDOW_SAMPLES), dtype=np.float32)
        for ch in range(18):
            delta = (25 + rng.uniform(-5, 5)) * np.sin(2 * np.pi * rng.uniform(1.5, 3.5) * t + rng.uniform(0, 2*np.pi))
            theta = (15 + rng.uniform(-3, 3)) * np.sin(2 * np.pi * rng.uniform(4.5, 7.5) * t + rng.uniform(0, 2*np.pi))
            alpha = (10 + rng.uniform(-2, 2)) * np.sin(2 * np.pi * rng.uniform(8.5, 12.0) * t + rng.uniform(0, 2*np.pi))
            beta  = (4  + rng.uniform(-1, 1)) * np.sin(2 * np.pi * rng.uniform(14.0, 25.0) * t + rng.uniform(0, 2*np.pi))
            noise = rng.normal(0, 3.0, size=WINDOW_SAMPLES)

            sig = delta + theta + alpha + beta + noise

            if state == "preictal":
                gamma = (12 + rng.uniform(0, 8)) * np.sin(2 * np.pi * rng.uniform(32.0, 38.0) * t)
                beta_boost = 10 * np.sin(2 * np.pi * 22.0 * t)
                sig += gamma + beta_boost
                spike_locs = rng.choice(WINDOW_SAMPLES, size=14, replace=False)
                sig[spike_locs] += rng.choice([-1, 1], size=14) * rng.uniform(80, 160)

            win[ch] = (sig * 1e-6).astype(np.float32)

        windows.append(win)

    return windows
