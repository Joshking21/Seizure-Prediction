import logging
import json
import joblib
import numpy as np
from pathlib import Path
from typing import Tuple, Dict, List
from tqdm import tqdm
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from src.config import (
    PROC_DIR, SCALER_PATH, RANDOM_SEED,
    VALIDATION_SPLIT, TEST_SPLIT,
)
from src.data_loader import load_subject_records
from src.preprocessor import preprocess_record
from src.feature_extractor import extract_features, reshape_for_model

logger = logging.getLogger(__name__)


def build_dataset(
    subject_ids: List[str],
    use_mock: bool = False,
    force_rebuild: bool = False,
) -> Tuple[np.ndarray, np.ndarray]:
    cache_path = PROC_DIR / f"features_{'_'.join(subject_ids)}.npz"

    if cache_path.exists() and not force_rebuild:
        data = np.load(cache_path)
        return data["X"].astype(np.float32), data["y"].astype(np.int8)

    all_X, all_y = [], []

    for subj in subject_ids:
        records = load_subject_records(subj, use_mock=use_mock)

        for rec in tqdm(records, desc=f"  {subj} records", leave=False):
            windows_labels = preprocess_record(rec)
            if not windows_labels:
                continue

            windows = [w for w, _ in windows_labels]
            labels = [l for _, l in windows_labels]

            for win, lbl in zip(windows, labels):
                feat = extract_features(win)
                all_X.append(feat)
                all_y.append(lbl)

    X = np.array(all_X, dtype=np.float32)
    y = np.array(all_y, dtype=np.int8)

    np.savez_compressed(cache_path, X=X, y=y)
    return X, y


def prepare_splits(X, y, balance: bool = True) -> Dict[str, Tuple]:
    if balance:
        X, y = _balance_classes(X, y)

    holdout = VALIDATION_SPLIT + TEST_SPLIT
    X_train, X_holdout, y_train, y_holdout = train_test_split(
        X, y, test_size=holdout, stratify=y, random_state=RANDOM_SEED
    )

    val_fraction = VALIDATION_SPLIT / holdout
    X_val, X_test, y_val, y_test = train_test_split(
        X_holdout, y_holdout,
        test_size=(1 - val_fraction),
        stratify=y_holdout,
        random_state=RANDOM_SEED,
    )

    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_val = scaler.transform(X_val)
    X_test = scaler.transform(X_test)
    joblib.dump(scaler, SCALER_PATH)

    splits = {}
    for name, (Xs, ys) in [("train", (X_train, y_train)),
                           ("val",   (X_val,   y_val)),
                           ("test",  (X_test,  y_test))]:
        X_cnn, X_lstm = reshape_for_model(Xs)
        splits[name] = (X_cnn, X_lstm, ys)

    return splits


def _balance_classes(X, y, ratio: float = 3.0):
    idx_0 = np.where(y == 0)[0]
    idx_1 = np.where(y == 1)[0]

    n_keep = min(len(idx_0), int(len(idx_1) * ratio))
    rng = np.random.default_rng(RANDOM_SEED)
    idx_0_down = rng.choice(idx_0, size=n_keep, replace=False)

    idx_balanced = np.concatenate([idx_0_down, idx_1])
    rng.shuffle(idx_balanced)

    return X[idx_balanced], y[idx_balanced]
