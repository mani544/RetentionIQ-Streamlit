import streamlit as st
import plotly.express as px
from services.queries import segment_metrics

st.title("Churn Intelligence")

df = segment_metrics()

fig = px.pie(
    df,
    names="customer_segment",
    values="risk",
    hole=0.5,
    color_discrete_sequence=px.colors.sequential.Reds
)

st.plotly_chart(fig, use_container_width=True)

st.warning("""
High-value segments are driving disproportionate revenue risk.

Deploy loyalty incentives + proactive support immediately.
""")
