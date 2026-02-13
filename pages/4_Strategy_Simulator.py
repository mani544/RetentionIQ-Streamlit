import streamlit as st

st.title("Retention Strategy Simulator")

st.write("Estimate revenue protected by reducing churn.")

reduction = st.slider("Reduce churn by (%)", 1, 10)

avg_revenue_loss = 50000000  # adjust from your data

saved = avg_revenue_loss * (reduction / 100)

st.success(f"💰 Potential Revenue Saved: ${saved:,.0f}")

