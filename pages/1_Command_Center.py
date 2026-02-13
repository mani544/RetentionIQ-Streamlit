import streamlit as st
import plotly.express as px
from services.queries import load_kpis, churn_by_region

st.title("Command Center")

kpi = load_kpis().iloc[0]

c1,c2,c3,c4,c5,c6 = st.columns(6)

c1.metric("Customers", f"{int(kpi.total_customers):,}")
c2.metric("Churned", f"{int(kpi.churned):,}")
c3.metric("Churn Rate", f"{kpi.churn_rate:.2%}")
c4.metric("Retention", f"{kpi.retention_rate:.2%}")
c5.metric("Revenue", f"${kpi.revenue/1e9:.2f}B")
c6.metric("Revenue Risk", f"${kpi.risk/1e6:.0f}M")

st.divider()

df = churn_by_region()

fig = px.bar(
    df,
    x="region",
    y="churn_rate",
    color="churn_rate",
    color_continuous_scale="Reds"
)

st.plotly_chart(fig, use_container_width=True)

st.info("""
### Executive Recommendation

Retail-heavy regions with elevated churn represent immediate revenue leakage.
Prioritize targeted retention programs — even a 3% reduction could protect tens of millions annually.
""")
