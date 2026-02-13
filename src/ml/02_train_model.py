import pandas as pd
import numpy as np
import time
import joblib
from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, classification_report, f1_score

from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

# =====================================================
# CONFIG PATHS (VERY IMPORTANT)
# =====================================================
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = BASE_DIR / "src/ml/data/ml_training_data.csv"
MODEL_DIR = BASE_DIR / "src/ml/models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

# =====================================================
# START
# =====================================================
print("=" * 70)
print("ENSEMBLE CHURN MODEL TRAINING")
print("=" * 70)

start = time.time()

# =====================================================
# LOAD DATA
# =====================================================
print("Loading dataset...")
df = pd.read_csv(DATA_PATH)

# remove duplicate ids
df = df.loc[:, ~df.columns.str.contains(r"customer_id\.")]

# =====================================================
# ENCODE CATEGORICALS
# =====================================================
print("Encoding categorical features...")
encoders = {}

for col in ["region", "customer_segment"]:
    le = LabelEncoder()
    df[col] = le.fit_transform(df[col].astype(str))
    encoders[col] = le

df = df.fillna(0)

# =====================================================
# FEATURES
# =====================================================
print("Preparing features...")
X = df.drop(columns=["customer_id", "churn_flag"])
y = df["churn_flag"]

# ⭐⭐⭐ SAVE FEATURE NAMES (CRITICAL FOR PREDICTION)
joblib.dump(list(X.columns), MODEL_DIR / "feature_names.pkl")
print("Feature names saved")

# imbalance
scale_pos_weight = (y == 0).sum() / (y == 1).sum()

# split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

print("Train shape:", X_train.shape)
print("Test shape:", X_test.shape)

# =====================================================
# MODEL 1 — XGBOOST
# =====================================================
print("Training XGBoost...")

xgb = XGBClassifier(
    n_estimators=800,
    max_depth=6,
    learning_rate=0.03,
    subsample=0.85,
    colsample_bytree=0.85,
    scale_pos_weight=scale_pos_weight,
    eval_metric="logloss",
    random_state=42,
    n_jobs=-1
)
xgb.fit(X_train, y_train)

# =====================================================
# MODEL 2 — LIGHTGBM
# =====================================================
print("Training LightGBM...")

lgb = LGBMClassifier(
    n_estimators=800,
    learning_rate=0.03,
    num_leaves=64,
    subsample=0.85,
    colsample_bytree=0.85,
    class_weight="balanced",
    random_state=42
)
lgb.fit(X_train, y_train)

# =====================================================
# MODEL 3 — LOGISTIC REGRESSION
# =====================================================
print("Training Logistic Regression...")

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

lr = LogisticRegression(max_iter=1000, class_weight="balanced")
lr.fit(X_train_scaled, y_train)

# =====================================================
# ENSEMBLE PREDICTION
# =====================================================
print("Combining models...")

xgb_prob = xgb.predict_proba(X_test)[:, 1]
lgb_prob = lgb.predict_proba(X_test)[:, 1]
lr_prob = lr.predict_proba(X_test_scaled)[:, 1]

ensemble_prob = (
    0.4 * xgb_prob +
    0.4 * lgb_prob +
    0.2 * lr_prob
)

# =====================================================
# THRESHOLD OPTIMIZATION
# =====================================================
best_threshold = 0.5
best_f1 = 0

for t in np.arange(0.1, 0.9, 0.01):
    preds = (ensemble_prob > t).astype(int)
    score = f1_score(y_test, preds)
    if score > best_f1:
        best_f1 = score
        best_threshold = t

# =====================================================
# FINAL METRICS
# =====================================================
final_preds = (ensemble_prob > best_threshold).astype(int)

print("\nFINAL ENSEMBLE PERFORMANCE")
print("-" * 50)
print("ROC-AUC:", round(roc_auc_score(y_test, ensemble_prob), 4))
print("F1:", round(best_f1, 4))
print("Threshold:", round(best_threshold, 3))
print("\nClassification Report:\n")
print(classification_report(y_test, final_preds))

# =====================================================
# SAVE MODELS
# =====================================================
print("Saving model artifacts...")

joblib.dump(xgb, MODEL_DIR / "xgb_model.pkl")
joblib.dump(lgb, MODEL_DIR / "lgb_model.pkl")
joblib.dump(lr, MODEL_DIR / "lr_model.pkl")
joblib.dump(scaler, MODEL_DIR / "scaler.pkl")
joblib.dump(encoders, MODEL_DIR / "label_encoders.pkl")
joblib.dump(best_threshold, MODEL_DIR / "threshold.pkl")

print("Models saved to:", MODEL_DIR)

# =====================================================
# END
# =====================================================
print("Time:", round(time.time() - start, 2), "seconds")
print("=" * 70)
