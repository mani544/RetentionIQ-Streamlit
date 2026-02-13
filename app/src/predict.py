from pathlib import Path
import pandas as pd
import joblib

# ======================================================
# PATHS (FIXED)
# ======================================================
MODEL_DIR = Path(__file__).parent / "models"



# ======================================================
# LOAD MODELS
# ======================================================
xgb = joblib.load(MODEL_DIR / "xgb_model.pkl")
lgb = joblib.load(MODEL_DIR / "lgb_model.pkl")
lr = joblib.load(MODEL_DIR / "lr_model.pkl")

scaler = joblib.load(MODEL_DIR / "scaler.pkl")
encoders = joblib.load(MODEL_DIR / "label_encoders.pkl")
threshold = joblib.load(MODEL_DIR / "threshold.pkl")
EXPECTED_FEATURES = joblib.load(MODEL_DIR / "feature_names.pkl")

# ======================================================
# PREDICTION FUNCTION
# ======================================================
def predict_churn(features: dict):

    df = pd.DataFrame([features])

    # -----------------------------
    # ENCODE CATEGORICALS
    # -----------------------------
    for col, encoder in encoders.items():
        if col in df.columns:
            df[col] = df[col].astype(str)
            df[col] = df[col].apply(
                lambda x: x if x in encoder.classes_ else encoder.classes_[0]
            )
            df[col] = encoder.transform(df[col])

    # -----------------------------
    # ALIGN FEATURES
    # -----------------------------
    for col in EXPECTED_FEATURES:
        if col not in df.columns:
            df[col] = 0

    df = df[EXPECTED_FEATURES]

    # -----------------------------
    # SCALE FOR LR ONLY
    # -----------------------------
    scaled = scaler.transform(df)

    # -----------------------------
    # GET PROBABILITIES
    # -----------------------------
    xgb_prob = xgb.predict_proba(df)[0][1]
    lgb_prob = lgb.predict_proba(df)[0][1]
    lr_prob = lr.predict_proba(scaled)[0][1]

    # -----------------------------
    # ENSEMBLE (same weights as training)
    # -----------------------------
    prob = (
        0.4 * xgb_prob +
        0.4 * lgb_prob +
        0.2 * lr_prob
    )

    pred = int(prob >= threshold)

    return prob, pred
