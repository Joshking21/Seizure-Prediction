import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import tensorflow as tf
import joblib
from pathlib import Path
from sklearn.metrics import (confusion_matrix, roc_curve, roc_auc_score,
                             precision_recall_curve, average_precision_score)
from sklearn.model_selection import train_test_split

tf.get_logger().setLevel('ERROR')
MODEL_DIR = Path('models/saved')
DATA_PATH = Path('data/processed')

model = tf.keras.models.load_model(str(MODEL_DIR / 'seizure_model.h5'))
scaler = joblib.load(str(MODEL_DIR / 'scaler.joblib'))

data = np.load(list(DATA_PATH.glob('*.npz'))[0])
X, y = data['X'].astype(np.float32), data['y'].astype(np.int8)

n_feat = X.shape[1]
n_bands, n_stats = 5, 4
n_ch = n_feat // (n_bands * n_stats)

_, X_test, _, y_test = train_test_split(X, y, test_size=0.30, stratify=y, random_state=42)
X_test, _, y_test, _ = train_test_split(X_test, y_test, test_size=0.50, stratify=y_test, random_state=42)

X_scaled = scaler.transform(X_test)
n = X_scaled.shape[0]
tensor = X_scaled.reshape(n, n_ch, n_bands, n_stats)
X_cnn = tensor.reshape(n, n_ch, n_bands * n_stats).astype(np.float32)
X_lstm = tensor.transpose(0, 2, 1, 3).reshape(n, n_bands, n_ch * n_stats).astype(np.float32)

y_prob = model.predict([X_cnn, X_lstm], verbose=0).flatten()
y_pred = (y_prob >= 0.5).astype(int)

cm = confusion_matrix(y_test, y_pred)

fig, ax = plt.subplots(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=['Inter-ictal\n(Class 0)', 'Pre-ictal\n(Class 1)'],
            yticklabels=['Inter-ictal\n(Class 0)', 'Pre-ictal\n(Class 1)'],
            ax=ax, linewidths=0.5, annot_kws={'size': 14})
ax.set_title('Confusion Matrix - Test Set', fontsize=13, fontweight='bold')
ax.set_ylabel('True Label', fontsize=11)
ax.set_xlabel('Predicted Label', fontsize=11)
plt.tight_layout()
plt.savefig(MODEL_DIR / 'confusion_matrix.png', dpi=150, bbox_inches='tight')
plt.close()

if len(np.unique(y_test)) > 1:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle('Dual-Stream CNN-LSTM - Test Set Curves', fontsize=13, fontweight='bold')
    fpr_arr, tpr_arr, _ = roc_curve(y_test, y_prob)
    auc_roc = roc_auc_score(y_test, y_prob)
    ax1.plot(fpr_arr, tpr_arr, '#3498db', linewidth=2, label=f'AUC = {auc_roc:.4f}')
    ax1.plot([0, 1], [0, 1], 'k--', linewidth=1, alpha=0.5)
    ax1.set_xlabel('False Positive Rate')
    ax1.set_ylabel('True Positive Rate')
    ax1.set_title('ROC Curve')
    ax1.legend()
    ax1.grid(alpha=0.3)
    prec_arr, rec_arr, _ = precision_recall_curve(y_test, y_prob)
    auc_pr = average_precision_score(y_test, y_prob)
    ax2.plot(rec_arr, prec_arr, '#e74c3c', linewidth=2, label=f'AP = {auc_pr:.4f}')
    ax2.set_xlabel('Recall')
    ax2.set_ylabel('Precision')
    ax2.set_title('Precision-Recall Curve')
    ax2.legend()
    ax2.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(MODEL_DIR / 'roc_pr_curves.png', dpi=150, bbox_inches='tight')
    plt.close()

tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (cm[0, 0], 0, 0, 0)
acc = (tp + tn) / (tp + tn + fp + fn)
sens = tp / max(tp + fn, 1)
spec = tn / max(tn + fp, 1)
fprh = (fp / max(fp + tn, 1)) * (3600 / 2.5)

print('=== FINAL METRICS ===')
print(f'Accuracy    : {acc*100:.2f}%')
print(f'Sensitivity : {sens*100:.2f}%')
print(f'Specificity : {spec*100:.2f}%')
print(f'FPR/hour    : {fprh:.3f}')
print(f'TN={tn}  FP={fp}  FN={fn}  TP={tp}')
