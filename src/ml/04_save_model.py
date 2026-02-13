import joblib

bundle = {
    "xgb": joblib.load("models/xgb_model.pkl"),
    "lgb": joblib.load("models/lgb_model.pkl"),
    "lr": joblib.load("models/lr_model.pkl"),
    "scaler": joblib.load("models/scaler.pkl"),
    "encoders": joblib.load("models/label_encoders.pkl"),
    "threshold": joblib.load("models/threshold.pkl")
}

joblib.dump(bundle, "models/churn_ensemble_bundle.pkl")

print("Ensemble bundle saved")
