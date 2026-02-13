import pd


def predict_churn(input_dict):

    df = pd.DataFrame([input_dict])

    # SAFE categorical encoding
    for col, encoder in encoders.items():
        value = str(df[col].iloc[0])

        if value in encoder.classes_:
            df[col] = encoder.transform([value])[0]
        else:
            df[col] = -1   # unseen category fallback

    df = df.fillna(0)

    df_scaled = scaler.transform(df)

    xgb_prob = xgb.predict_proba(df)[:, 1]
    lgb_prob = lgb.predict_proba(df)[:, 1]
    lr_prob = lr.predict_proba(df_scaled)[:, 1]

    ensemble_prob = (
        0.4 * xgb_prob +
        0.4 * lgb_prob +
        0.2 * lr_prob
    )[0]

    churn_prediction = int(ensemble_prob > threshold)

    return {
        "churn_probability": float(round(ensemble_prob, 4)),
        "prediction": churn_prediction,
        "risk_level": (
            "HIGH" if ensemble_prob > 0.7 else
            "MEDIUM" if ensemble_prob > 0.4 else
            "LOW"
        )
    }
