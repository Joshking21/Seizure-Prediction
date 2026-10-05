import os
import logging
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

try:
    import mne
    set_log = getattr(mne, "set_log_level", None)
    if callable(set_log):
        set_log("WARNING")
    MNE_AVAILABLE = True
except ImportError:
    MNE_AVAILABLE = False

from src.config import (
    RAW_DIR, MOCK_DIR, SAMPLING_RATE, N_CHANNELS, EEG_CHANNELS,
    RANDOM_SEED,
)

CHB_MIT_ANNOTATIONS: Dict[str, List[tuple]] = {
    "chb01_03": [(2996, 3036)],
    "chb01_04": [(1467, 1494)],
    "chb01_15": [(1732, 1772)],
    "chb01_16": [(1015, 1066)],
    "chb01_18": [(1720, 1810)],
    "chb02_16": [(130,  212)],
    "chb02_16+": [(2972, 3053)],
    "chb03_01": [(362,  414)],
    "chb03_02": [(731,  796)],
    "chb03_03": [(432,  501)],
}


def load_subject_records(subject_id: str, use_mock: bool = False) -> List[Dict[str, Any]]:
    if use_mock:
        return _generate_mock_subject(subject_id)

    subject_dir = RAW_DIR / subject_id
    if not subject_dir.exists() or not any(subject_dir.glob("*.edf")):
        return _generate_mock_subject(subject_id)

    if not MNE_AVAILABLE:
        raise ImportError("MNE is required for EDF loading.")

    records = []
    for edf_path in sorted(subject_dir.glob("*.edf")):
        record_name = edf_path.stem
        seizures = [
            {"onset_sec": s, "offset_sec": e}
            for s, e in CHB_MIT_ANNOTATIONS.get(record_name, [])
        ]
        try:
            rec = _load_edf(edf_path, subject_id, record_name, seizures)
            records.append(rec)
        except Exception as exc:
            logger.error(f"Failed to load {edf_path.name}: {exc}")

    return records


def _load_edf(edf_path: Path, subject_id: str, record_name: str, seizures: List[Dict]) -> Dict[str, Any]:
    raw = mne.io.read_raw_edf(str(edf_path), preload=True, verbose=False)

    rename_map = {}
    for ch in raw.ch_names:
        new_ch = ch.lstrip(".")
        if new_ch.endswith("-0"):
            new_ch = new_ch[:-2]
        rename_map[ch] = new_ch
    raw.rename_channels(rename_map)

    available = [ch for ch in EEG_CHANNELS if ch in raw.ch_names]
    raw.pick_channels(available)

    if int(raw.info["sfreq"]) != SAMPLING_RATE:
        raw.resample(SAMPLING_RATE, npad="auto")

    signals = raw.get_data().astype(np.float32)

    return {
        "signals": signals,
        "fs": SAMPLING_RATE,
        "channels": available,
        "seizures": seizures,
        "subject": subject_id,
        "record": record_name,
    }


def _generate_mock_subject(subject_id: str, n_records: int = 5, record_duration_min: int = 180) -> List[Dict[str, Any]]:
    rng = np.random.default_rng(RANDOM_SEED + hash(subject_id) % 1000)
    n_samp = record_duration_min * 60 * SAMPLING_RATE
    t = np.linspace(0, record_duration_min * 60, n_samp)
    records = []

    for rec_idx in range(n_records):
        record_name = f"{subject_id}_{rec_idx+1:02d}"
        signals = np.zeros((N_CHANNELS, n_samp), dtype=np.float32)

        seizure_onset_sec = 45 * 60
        seizure_offset_sec = seizure_onset_sec + 40
        seizures = [{"onset_sec": seizure_onset_sec, "offset_sec": seizure_offset_sec}]

        for ch in range(N_CHANNELS):
            sig = 20e-6 * np.sin(2 * np.pi * 2 * t)
            sig += 10e-6 * np.sin(2 * np.pi * 6 * t)
            sig += 15e-6 * np.sin(2 * np.pi * 10 * t)
            sig += 8e-6 * np.sin(2 * np.pi * 20 * t)

            phase = rng.uniform(0, 2 * np.pi)
            sig *= (1 + 0.2 * rng.standard_normal(n_samp))
            sig += rng.standard_normal(n_samp) * 3e-6

            pre_onset_samp = int((seizure_onset_sec - 30 * 60) * SAMPLING_RATE)
            seizure_on_samp = int(seizure_onset_sec * SAMPLING_RATE)
            seizure_off_samp = int(seizure_offset_sec * SAMPLING_RATE)

            pre_len = seizure_on_samp - pre_onset_samp
            if pre_onset_samp >= 0:
                ramp = np.linspace(0, 1, pre_len)
                pre_t = t[pre_onset_samp:seizure_on_samp]
                sig[pre_onset_samp:seizure_on_samp] += ramp * 25e-6 * np.sin(2 * np.pi * 30 * pre_t + phase)

            ict_t = t[seizure_on_samp:seizure_off_samp]
            if len(ict_t) > 0:
                sig[seizure_on_samp:seizure_off_samp] += (
                    80e-6 * np.sin(2 * np.pi * 5 * ict_t)
                    + 60e-6 * np.sin(2 * np.pi * 10 * ict_t)
                    + rng.standard_normal(len(ict_t)) * 15e-6
                )

            signals[ch] = sig.astype(np.float32)

        records.append({
            "signals": signals,
            "fs": SAMPLING_RATE,
            "channels": EEG_CHANNELS[:N_CHANNELS],
            "seizures": seizures,
            "subject": subject_id,
            "record": record_name,
        })

    return records
