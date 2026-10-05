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
    # chb01 (7 seizure files)
    "chb01_03": [(2996, 3036)],
    "chb01_04": [(1467, 1494)],
    "chb01_15": [(1732, 1772)],
    "chb01_16": [(1015, 1066)],
    "chb01_18": [(1720, 1810)],
    "chb01_21": [(327, 420)],
    "chb01_26": [(1862, 1963)],
    # chb02 (3 seizure files)
    "chb02_16": [(130, 212)],
    "chb02_16+": [(2972, 3053)],
    "chb02_19": [(3369, 3378)],
    # chb03 (7 seizure files)
    "chb03_01": [(362, 414)],
    "chb03_02": [(731, 796)],
    "chb03_03": [(432, 501)],
    "chb03_04": [(2162, 2214)],
    "chb03_34": [(1982, 2029)],
    "chb03_35": [(2592, 2656)],
    "chb03_36": [(1725, 1778)],
    # chb04 (3 seizure files)
    "chb04_05": [(7804, 7853)],
    "chb04_08": [(6446, 6557)],
    "chb04_28": [(1679, 1781), (3782, 3898)],
    # chb05 (5 seizure files)
    "chb05_06": [(417, 532)],
    "chb05_13": [(1086, 1196)],
    "chb05_16": [(2317, 2413)],
    "chb05_17": [(2451, 2571)],
    "chb05_22": [(2348, 2465)],
    # chb06 (7 seizure files)
    "chb06_01": [(1724, 1738), (7461, 7476), (13525, 13540)],
    "chb06_04": [(327, 347), (6211, 6231)],
    "chb06_09": [(12500, 12516)],
    "chb06_10": [(10833, 10845)],
    "chb06_13": [(506, 519)],
    "chb06_18": [(7799, 7811)],
    "chb06_24": [(9387, 9403)],
    # chb08 (5 seizure files)
    "chb08_02": [(2670, 2841)],
    "chb08_05": [(2856, 3046)],
    "chb08_11": [(2988, 3122)],
    "chb08_13": [(2417, 2577)],
    "chb08_21": [(2083, 2347)],
    # chb10 (7 seizure files)
    "chb10_12": [(6313, 6348)],
    "chb10_20": [(6888, 6958)],
    "chb10_27": [(2382, 2447)],
    "chb10_30": [(3021, 3079)],
    "chb10_31": [(3801, 3877)],
    "chb10_38": [(4618, 4707)],
    "chb10_89": [(1383, 1437)],
    # chb14 (7 seizure files)
    "chb14_03": [(1986, 2000)],
    "chb14_04": [(1372, 1392), (2817, 2839)],
    "chb14_06": [(1911, 1925)],
    "chb14_11": [(1838, 1879)],
    "chb14_17": [(3239, 3259)],
    "chb14_18": [(1039, 1061)],
    "chb14_27": [(2833, 2849)],
    # chb20 (6 seizure files)
    "chb20_12": [(94, 123)],
    "chb20_13": [(1440, 1470), (2498, 2537)],
    "chb20_14": [(1971, 2009)],
    "chb20_15": [(390, 425), (1689, 1738)],
    "chb20_16": [(2226, 2261)],
    "chb20_68": [(1393, 1432)],
}


def parse_summary_file(summary_path: Path) -> Dict[str, List[tuple]]:
    """Parse seizure timestamps dynamically from a CHB-MIT summary text file."""
    import re
    if not summary_path.exists():
        return {}
    content = summary_path.read_text(encoding="utf-8", errors="ignore")
    blocks = re.split(r"File Name:\s*", content)
    parsed: Dict[str, List[tuple]] = {}
    for block in blocks[1:]:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        fname_match = re.match(r"^([a-zA-Z0-9_+\-]+(?:\.edf)?)", lines[0])
        if not fname_match:
            continue
        fname = fname_match.group(1)
        rec_name = fname[:-4] if fname.lower().endswith(".edf") else fname
        num_m = re.search(r"Number of Seizures in File:\s*(\d+)", block, re.IGNORECASE)
        num_seizures = int(num_m.group(1)) if num_m else 0
        if num_seizures == 0:
            continue
        starts = [int(s) for s in re.findall(r"Seizure\s*(?:\d*\s*)?Start Time:\s*(\d+)\s*seconds", block, re.IGNORECASE)]
        ends = [int(e) for e in re.findall(r"Seizure\s*(?:\d*\s*)?End Time:\s*(\d+)\s*seconds", block, re.IGNORECASE)]
        pairs = list(zip(starts, ends))
        if pairs:
            parsed[rec_name] = pairs
    return parsed


def load_subject_records(
    subject_id: str,
    use_mock: bool = False,
    only_seizures: bool = True,
) -> List[Dict[str, Any]]:
    if use_mock:
        return _generate_mock_subject(subject_id)

    subject_dir = RAW_DIR / subject_id
    if not subject_dir.exists() or not any(subject_dir.glob("*.edf")):
        return _generate_mock_subject(subject_id)

    if not MNE_AVAILABLE:
        raise ImportError("MNE is required for EDF loading.")

    # Check for summary file in subject dir to load any dynamic/new annotations
    dynamic_annotations: Dict[str, List[tuple]] = {}
    for summary_file in subject_dir.glob("*-summary.txt"):
        dynamic_annotations.update(parse_summary_file(summary_file))

    records = []
    for edf_path in sorted(subject_dir.glob("*.edf")):
        record_name = edf_path.stem
        # Priority: dynamic parsed summary -> static CHB_MIT_ANNOTATIONS -> empty list
        raw_seizures = dynamic_annotations.get(
            record_name,
            CHB_MIT_ANNOTATIONS.get(record_name, [])
        )
        # If configured to only input files with seizures, skip files with 0 seizures
        if only_seizures and not raw_seizures:
            logger.info(f"Skipping non-seizure recording: {record_name}")
            continue

        seizures = [
            {"onset_sec": s, "offset_sec": e}
            for s, e in raw_seizures
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
