import os
import json
import logging
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.metrics import (
    confusion_matrix, classification_report,
    roc_auc_score, average_precision_score,
    roc_curve, precision_recall_curve,
)

from src.config import (
    BATCH_SIZE, EPOCHS, RANDOM_SEED, CLASS_WEIGHT_MULTIPLIER,
    MODEL_H5_PATH, METRICS_PATH, MODEL_DIR,
)
from src.model import build_model, get_callbacks

import tensorflow as tf
tf.random.set_seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def train_model(splits: dict) -> dict:
    X_cnn_tr, X_lstm_tr, y_tr = splits["train"]
    X_cnn_val, X_lstm_val, y_val = splits["val"]
    X_cnn_te, X_lstm_te, y_te = splits["test"]

    logger.info(
        f"\n{'='*50}\n"
        f"Training set:   {len(y_tr)} windows\n"
        f"Validation set: {len(y_val)} windows\n"
        f"Test set:       {len(y_te)} windows\n"
        f"{'='*50}"
    )

    model = build_model()
    model.summary(print_fn=logger.info, expand_nested=True)

    n_neg = np.sum(y_tr == 0)
    n_pos = np.sum(y_tr == 1)
    weight_pos = (n_neg / max(n_pos, 1)) * CLASS_WEIGHT_MULTIPLIER
    class_weights = {0: 1.0, 1: float(weight_pos)}

    callbacks = get_callbacks(str(MODEL_H5_PATH))

    history = model.fit(
        x=[X_cnn_tr, X_lstm_tr],
        y=y_tr,
        validation_data=([X_cnn_val, X_lstm_val], y_val),
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        class_weight=class_weights,
        callbacks=callbacks,
        verbose=1,
    )

    metrics = evaluate_model(model, X_cnn_te, X_lstm_te, y_te)

    _plot_training_history(history)
    _plot_roc_pr_curves(model, X_cnn_te, X_lstm_te, y_te)
    _plot_confusion_matrix(metrics["confusion_matrix"])

    metrics_serialisable = {
        k: (v.tolist() if hasattr(v, "tolist") else v)
        for k, v in metrics.items()
    }
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics_serialisable, f, indent=2)

    return metrics


def evaluate_model(model,
                   X_cnn,
                   X_lstm,
                   y_true,
                   threshold: float = 0.5) -> dict:
    y_prob = model.predict([X_cnn, X_lstm], verbose=0).flatten()
    y_pred = (y_prob >= threshold).astype(int)

    cm = confusion_matrix(y_true, y_pred)
    if cm.size == 1:
        if y_true[0] == 0:
            tn, fp, fn, tp = cm[0, 0], 0, 0, 0
        else:
            tn, fp, fn, tp = 0, 0, 0, cm[0, 0]
    else:
        tn, fp, fn, tp = cm.ravel()

    accuracy = (tp + tn) / (tp + tn + fp + fn)
    sensitivity = tp / max(tp + fn, 1)
    specificity = tn / max(tn + fp, 1)
    precision = tp / max(tp + fp, 1)
    f1 = 2 * precision * sensitivity / max(precision + sensitivity, 1e-9)
    fpr = fp / max(fp + tn, 1)

    windows_per_hour = 3600 / 2.5
    fpr_per_hour = fpr * windows_per_hour

    auc_roc = roc_auc_score(y_true, y_prob) if len(np.unique(y_true)) > 1 else 0.0
    auc_pr = average_precision_score(y_true, y_prob) if len(np.unique(y_true)) > 1 else 0.0

    report = classification_report(
        y_true, y_pred,
        target_names=["Inter-ictal", "Pre-ictal"],
        digits=4,
        zero_division=0,
    )

    metrics = {
        "accuracy": round(float(accuracy * 100), 2),
        "sensitivity": round(float(sensitivity * 100), 2),
        "specificity": round(float(specificity * 100), 2),
        "precision": round(float(precision * 100), 2),
        "f1_score": round(float(f1 * 100), 2),
        "fpr_raw": round(float(fpr), 4),
        "fpr_per_hour": round(float(fpr_per_hour), 3),
        "auc_roc": round(float(auc_roc), 4),
        "auc_pr": round(float(auc_pr), 4),
        "confusion_matrix": cm,
        "tp": int(tp), "tn": int(tn), "fp": int(fp), "fn": int(fn),
        "classification_report": report,
    }

    logger.info(f"\n{'='*50}")
    logger.info("  EVALUATION RESULTS - TEST SET")
    logger.info(f"{'-'*50}")
    logger.info(f"  Accuracy:      {metrics['accuracy']:.2f}%")
    logger.info(f"  Sensitivity:   {metrics['sensitivity']:.2f}%")
    logger.info(f"  Specificity:   {metrics['specificity']:.2f}%")
    logger.info(f"  Precision:     {metrics['precision']:.2f}%")
    logger.info(f"  F1 Score:      {metrics['f1_score']:.2f}%")
    logger.info(f"  FPR / hour:    {metrics['fpr_per_hour']:.3f}")
    logger.info(f"  AUC-ROC:       {metrics['auc_roc']:.4f}")
    logger.info(f"  AUC-PR:        {metrics['auc_pr']:.4f}")
    logger.info(f"{'-'*50}")
    logger.info(f"  TN={tn}  FP={fp}  FN={fn}  TP={tp}")
    logger.info(f"{'='*50}\n")
    logger.info(f"\n{report}")

    return metrics


def _plot_training_history(history) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(16, 4))
    fig.suptitle("Training History - Dual-Stream CNN-LSTM", fontsize=13, fontweight="bold")

    for ax, metric, title, colour in zip(
        axes,
        ["loss", "accuracy", "auc"],
        ["Loss", "Accuracy", "AUC-ROC"],
        ["#e74c3c", "#2ecc71", "#3498db"],
    ):
        ax.plot(history.history[metric], color=colour, label="Train", linewidth=2)
        val_key = f"val_{metric}"
        if val_key in history.history:
            ax.plot(history.history[val_key], color=colour, linestyle="--", label="Validation", linewidth=2)
        ax.set_title(title)
        ax.set_xlabel("Epoch")
        ax.legend()
        ax.grid(alpha=0.3)

    plt.tight_layout()
    path = MODEL_DIR / "training_history.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()


def _plot_roc_pr_curves(model, X_cnn, X_lstm, y_true) -> None:
    if len(np.unique(y_true)) < 2:
        return

    y_prob = model.predict([X_cnn, X_lstm], verbose=0).flatten()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle("Dual-Stream CNN-LSTM - Test Set Curves", fontsize=13, fontweight="bold")

    fpr_arr, tpr_arr, _ = roc_curve(y_true, y_prob)
    auc_roc = roc_auc_score(y_true, y_prob)
    ax1.plot(fpr_arr, tpr_arr, "#3498db", linewidth=2, label=f"AUC = {auc_roc:.4f}")
    ax1.plot([0, 1], [0, 1], "k--", linewidth=1, alpha=0.5)
    ax1.set_xlabel("False Positive Rate")
    ax1.set_ylabel("True Positive Rate (Sensitivity)")
    ax1.set_title("ROC Curve")
    ax1.legend()
    ax1.grid(alpha=0.3)

    prec_arr, rec_arr, _ = precision_recall_curve(y_true, y_prob)
    auc_pr = average_precision_score(y_true, y_prob)
    ax2.plot(rec_arr, prec_arr, "#e74c3c", linewidth=2, label=f"AP = {auc_pr:.4f}")
    ax2.set_xlabel("Recall (Sensitivity)")
    ax2.set_ylabel("Precision")
    ax2.set_title("Precision-Recall Curve")
    ax2.legend()
    ax2.grid(alpha=0.3)

    plt.tight_layout()
    path = MODEL_DIR / "roc_pr_curves.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()


def _plot_confusion_matrix(cm) -> None:
    labels = ["Inter-ictal\n(Class 0)", "Pre-ictal\n(Class 1)"]
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(
        cm, annot=True, fmt="d", cmap="Blues",
        xticklabels=labels, yticklabels=labels,
        ax=ax, linewidths=0.5, annot_kws={"size": 14},
    )
    ax.set_title("Confusion Matrix - Test Set", fontsize=13, fontweight="bold")
    ax.set_ylabel("True Label", fontsize=11)
    ax.set_xlabel("Predicted Label", fontsize=11)
    plt.tight_layout()
    path = MODEL_DIR / "confusion_matrix.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
