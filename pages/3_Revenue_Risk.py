import streamlit as st
import plotly.express as px
from services.queries import revenue_by_region

st.title("📉 Revenue Risk Radar")

df = revenue_by_region()

fig = px.bar(
    df,
    x="region",
    y="revenue",
    color="revenue",
    title="Revenue Concentration by Region"
)

st.plotly_chart(fig, use_container_width=True)
