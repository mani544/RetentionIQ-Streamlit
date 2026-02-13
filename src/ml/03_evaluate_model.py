import pandas as pd
import joblib
from sklearn.metrics import roc_auc_score, classification_report, f1_score

print("=" * 60)
print("EVALUATING ENSEMBLE MODEL")
print("=" * 60)

# --------------------------------------------------
# LOAD MODELS
# --------------------------------------------------
xgb = joblib.load("models/xgb_model.pkl")
lgb = joblib.load("models/lgb_model.pkl")
lr = joblib.load("models/lr_model.pkl")
scaler = joblib.load("models/scaler.pkl")
encoders = joblib.load("models/label_encoders.pkl")
threshold = joblib.load("models/threshold.pkl")

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------
df = pd.read_csv("data/ml_training_data.csv")

# remove duplicate id columns if present
df = df.loc[:, ~df.columns.str.contains(r"customer_id\.")]

# encode categoricals
for col, encoder in encoders.items():
    df[col] = encoder.transform(df[col].astype(str))

df = df.fillna(0)

# --------------------------------------------------
# FEATURES
# --------------------------------------------------
X = df.drop(columns=["customer_id", "churn_flag"])
y = df["churn_flag"]

# scale for logistic regression
X_scaled = scaler.transform(X)

# --------------------------------------------------
# ENSEMBLE PREDICTION
# --------------------------------------------------
xgb_prob = xgb.predict_proba(X)[:, 1]
lgb_prob = lgb.predict_proba(X)[:, 1]
lr_prob = lr.predict_proba(X_scaled)[:, 1]

ensemble_prob = (
    0.4 * xgb_prob +
    0.4 * lgb_prob +
    0.2 * lr_prob
)

preds = (ensemble_prob > threshold).astype(int)

# --------------------------------------------------
# METRICS
# --------------------------------------------------
print("\nRESULTS")
print("-" * 40)
print("ROC-AUC:", round(roc_auc_score(y, ensemble_prob), 4))
print("F1:", round(f1_score(y, preds), 4))
print("Threshold:", threshold)

print("\nClassification Report:\n")
print(classification_report(y, preds))
