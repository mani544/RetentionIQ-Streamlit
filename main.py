import base64
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components
from services.db import fetch_kpis
from app.src.predict import predict_churn


def img_to_base64(path):
    img_bytes = Path(path).read_bytes()
    return base64.b64encode(img_bytes).decode()


architecture_img = img_to_base64("assets/architecture.png")
dash_overview = img_to_base64("assets/churn_overview.jpg")
dash_trends = img_to_base64("assets/churn_trends.jpg")
dash_revenue = img_to_base64("assets/revenue_risk.jpg")
dash_segment = img_to_base64("assets/segment_deep_dive.jpg")

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="ChurnGuard | Retention Intelligence",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ================= REMOVE STREAMLIT UI LIMITS =================
st.markdown("""
<style>
html, body {
    margin: 0;
    padding: 0;
    background: #000;
}

.block-container {
    padding: 0 !important;
    max-width: 100vw !important;
}

header, footer {
    visibility: hidden;
}
</style>
""", unsafe_allow_html=True)


# ================= LOAD KPI DATA =================
@st.cache_data(ttl=300)
def load_kpis():
    return fetch_kpis()


kpis = load_kpis()

total_customers = kpis["total_customers"] or 0
total_revenue = kpis["total_revenue"] or 0
revenue_at_risk = kpis["revenue_at_risk"] or 0

revenue_protected = max(total_revenue - revenue_at_risk, 0)
arpu = round(total_revenue / total_customers, 2) if total_customers else 0
# ======================================================
# LIVE CHURN PREDICTION PANEL
# ======================================================


st.markdown("## 🔮 AI Churn Risk Prediction")

col1, col2, col3 = st.columns(3)

with col1:
    region = st.selectbox("Region", ["North", "South", "East", "West"])
    segment = st.selectbox("Customer Segment", ["Basic", "Standard", "Premium"])
    tenure = st.slider("Tenure (months)", 0, 60, 12)

with col2:
    monthly_charges = st.number_input("Avg Monthly Charges", 0.0, 500.0, 80.0)
    last_charge = st.number_input("Last Month Charge", 0.0, 500.0, 90.0)
    tickets_30 = st.slider("Tickets last 30 days", 0, 20, 2)

with col3:
    csat = st.slider("CSAT Score", 1.0, 5.0, 3.0)
    downtime = st.number_input("Avg Downtime", 0.0, 300.0, 20.0)
    days_last_ticket = st.slider("Days since last ticket", 0, 365, 10)

if st.button("Predict Churn Risk"):

    features = {
        "region": region,
        "customer_segment": segment,
        "tenure_months": tenure,
        "avg_monthly_charges": monthly_charges,
        "charges_volatility": 10,
        "last_month_charge": last_charge,
        "tickets_last_30d": tickets_30,
        "tickets_last_90d": tickets_30 * 3,
        "days_since_last_ticket": days_last_ticket,
        "avg_csat": csat,
        "csat_volatility": 0.5,
        "avg_downtime": downtime,
        "downtime_volatility": 5,
        "downtime_last_30d": downtime
    }

    prob, pred = predict_churn(features)

    st.markdown("### Prediction Result")
    st.metric("Churn Probability", f"{prob:.2%}")

    if prob > 0.7:
        st.error("HIGH RISK CUSTOMER")
    elif prob > 0.4:
        st.warning("MEDIUM RISK")
    else:
        st.success("LOW RISK")

# ================= SINGLE PAGE HTML =================
components.html(
    f"""
<!DOCTYPE html>
<html>
<head>
<style>
body {{
    margin: 0;
    background: #000;
    font-family: Inter, system-ui, sans-serif;
}}

/* ================= NAVBAR ================= */
.navbar {{
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 72px;
    display: flex;
    align-items: center;
    padding: 0 48px;
    background: linear-gradient(to bottom, #000 70%, rgba(0,0,0,0.9));
    border-bottom: 1px solid rgba(255,255,255,0.06);
    z-index: 1000;
}}

.brand {{
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 26px;
    font-weight: 900;
    color: white;
}}

.logo {{
    width: 40px;
    height: 40px;
    background: #ff1e1e;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
}}

/* ================= HERO ================= */
.hero {{
    padding-top: 80px;
    padding-bottom: 30px;
    display: flex;
    justify-content: center;
    background:
        radial-gradient(circle at center, rgba(220,30,30,0.35), transparent 70%),
        repeating-linear-gradient(0deg, rgba(255,255,255,0.04) 0px, rgba(255,255,255,0.04) 1px, transparent 1px, transparent 60px),
        repeating-linear-gradient(90deg, rgba(255,255,255,0.04) 0px, rgba(255,255,255,0.04) 1px, transparent 1px, transparent 60px),
        #000;
}}


.hero-content {{
    max-width: 1200px;
    text-align: center;
    padding: 20px 24px;
}}

.badge {{
    display: inline-block;
    padding: 12px 22px;
    border-radius: 999px;
    border: 1px solid rgba(255,30,30,0.45);
    background: white;
    color: red;
    font-weight: 700;
    margin-bottom: 30px;
}}

.hero-title-small {{
    font-size: 48px;
    font-weight: 700;
    color: white;
}}

.hero-title-main {{
    font-size: 88px;
    font-weight: 900;
    color: white;
    line-height: 1.05;
}}

.hero-title-main span,
.hero-title-small span {{
    color: #ff1e1e;
}}

.hero-sub {{
    font-size: 22px;
    color: #d6d6d6;
    max-width: 900px;
    margin: 30px auto;
}}

/* ================= KPI ================= */
.kpi-wrapper {{
    padding: 30px 48px;
    padding-bottom: 30px;

}}


.kpi-title {{
    font-size: 40px;
    font-weight: 700;
    display: flex;
    justify-content: center;
    color: white;
    margin-bottom: 32px;
}}

.kpi-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 28px;
}}

.kpi-card {{
    height: 150px;
    background: linear-gradient(180deg, #0b0f17, #020617);
    border-radius: 18px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    box-shadow:
        inset 0 0 0 1px rgba(255,255,255,0.06),
        0 0 40px rgba(255,81,47,0.25);
    transition: all 0.3s ease;
}}

.kpi-card:hover {{
    transform: translateY(-8px);
    box-shadow:
        inset 0 0 0 1px rgba(255,255,255,0.1),
        0 0 70px rgba(255,81,47,0.5);
}}

.kpi-value {{
    font-size: 36px;
    font-weight: 900;
    color: #ff4b2b;
}}

.kpi-label {{
    margin-top: 10px;
    font-size: 15px;
    font-weight: 700;
    letter-spacing: 1px;
    color: #cbd5e1;
    text-transform: uppercase;
}}
/* RESPONSIVE */
@media (max-width: 900px) {{
  .features-grid {{
    grid-template-columns: 1fr;
  }}
}}

/* SECTION */


.features-wrapper {{
    padding: 10px 48px;
    padding-bottom: 30px;
}}

.features {{
  position: relative;
  padding: 50px 80px;
  background:
    radial-gradient(circle at top, rgba(255,30,30,0.15), transparent 5%),
    linear-gradient(to right, rgba(255,255,255,0.03) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(255,255,255,0.03) 1px, transparent 1px);
  background-size: auto, 60px 60px, 60px 60px;
}}

/* HEADER */

.features-header {{
  text-align: center;
  max-width: 900px;
  margin: 0 auto 80px;
}}

.features-header {{
  color: #ef4444;
  font-size: 30px;
  font-weight: 700;
  letter-spacing: 0.15em;

}}

.features-header h2 {{
  color: white;
  font-size: 48px;
  font-weight: 700;
  margin: 16px 0;
}}

.features-header h2 span {{
  color: #ef4444;
}}

.features-header p {{
  color: #94a3b8;
  font-size: 20px;
  line-height: 1.6;
}}

/* GRID */
.features-grid {{
  max-width: 5000px;
  margin: auto;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 28px;
}}


/* CARD */
.feature-card {{
  position: relative;
  padding: 10px;
  border-radius: 18px;
  background: linear-gradient(to bottom, #0b0f17, #020617);
  border: 1px solid rgba(255,255,255,0.1);
  transition: all 0.3s ease;
}}


.feature-card:hover {{
    transform: translateY(-8px);
    box-shadow:
        inset 0 0 0 1px rgba(255,255,255,0.1),
        0 0 70px rgba(255,81,47,0.5);
}}


/* ICON */
.icon-box {{
  width: 56px;
  height: 56px;
  border-radius: 14px;
  background: #dc2626;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 25px rgba(255,30,30,0.6);
  margin-bottom: 22px;
}}

.icon-box svg {{
  width: 26px;
  height: 26px;
  stroke: white;
}}

/* TEXT */
.feature-card h3 {{
  color: white;
  font-size: 25px;
  font-weight: 700;
  margin-bottom: 12px;
}}

.feature-card p {{
  color: #94a3b8;
  font-size: 15.5px;
  line-height: 1.6;
}}

/* RESPONSIVE */
@media (max-width: 900px) {{
  .features-grid {{
    grid-template-columns: 1fr;
  }}
}}

/* ================= ARCHITECTURE ================= */

.architecture-section {{
    width: 100vw;
    padding: 12px 48px;
    background:
        radial-gradient(circle at top, rgba(255,30,30,0.12), transparent 0%),
        #000;
}}
.architecture-header {{
  text-align: center;
  max-width: 900px;
  margin: 0 auto 80px;
}}

.architecture-header {{
  color: #ef4444;
  font-size: 30px;
  font-weight: 700;
  letter-spacing: 0.15em;

}}

.architecture-header h2 {{
  color: white;
  font-size: 48px;
  font-weight: 700;
  margin: 16px 0;
}}

.architecture-header h2 span {{
  color: #ef4444;
}}

.architecture-header p {{
  color: #94a3b8;
  font-size: 20px;
  line-height: 1.6;
}}

 {{
    text-align: center;
    max-width: 1100px;
    margin: 0 auto 80px;
}}

.architecture-tag {{
    color: #ff1e1e;
    font-weight: 800;
    letter-spacing: 3px;
    font-size: 14px;
    margin-bottom: 14px;
}}

.architecture-title {{
    font-size: clamp(44px, 6vw, 72px);
    font-weight: 900;
    color: white;
    line-height: 1.1;
}}

.architecture-title span {{
    color: #ff1e1e;
}}

.architecture-subtitle {{
    margin-top: 22px;
    font-size: 20px;
    color: #cbd5e1;
    line-height: 1.6;
}}

/* ================= ARCHITECTURE SECTION ================= */

.architecture-wrapper {{
    padding: 80px 48px;
    overflow-x: hidden;   /* 🚫 no horizontal scroll */
}}

/* ONE ROW – TIGHT FLOW */
.architecture-grid {{
    display: grid;
    grid-template-columns:
        205px 40px
        205px 40px
        205px 40px
        205px 40px
        205px 40px
        200px;             /* 6 cards + 5 arrows */
    align-items: center;
    gap: 0;               /* 🚫 no extra gap */
}}

/* CARD */
.arch-card {{
    height: 200px;
    background: linear-gradient(180deg, #0b0f17, #020617);
    border-radius: 22px;
    padding: 20px;

    box-shadow:
        inset 0 0 0 1px rgba(255,255,255,0.06),
        0 0 30px rgba(255,30,30,0.18);

    transition: all 0.3s ease;
}}

.arch-card:hover {{
    transform: translateY(-6px);
    box-shadow:
        inset 0 0 0 1px rgba(255,30,30,0.4),
        0 0 60px rgba(255,30,30,0.4);
}}

/* TEXT */
.arch-card h3 {{
    color: white;
    font-size: 20px;
    font-weight: 800;
    margin-bottom: 10px;
}}

.arch-card p {{
    color: #cbd5e1;
    font-size: 16px;
    line-height: 1.55;
}}

/* ARROW */
.arch-arrow {{
    text-align: center;
    font-size: 32px;
    color: #ff1e1e;
}}
/* ================= ARCHITECTURE SECTION ================= */

.architecture-section {{
    width: 100vw;
    padding: 120px 48px;
    background:
        radial-gradient(circle at center, rgba(220,30,30,0.18), transparent 60%),
        repeating-linear-gradient(
            0deg,
            rgba(255,255,255,0.03) 0px,
            rgba(255,255,255,0.03) 1px,
            transparent 1px,
            transparent 60px
        ),
        repeating-linear-gradient(
            90deg,
            rgba(255,255,255,0.03) 0px,
            rgba(255,255,255,0.03) 1px,
            transparent 1px,
            transparent 60px
        ),
        #000;
}}

/* Header */
.architecture-header {{
    text-align: center;
    max-width: 1100px;
    margin: 0 auto 80px;
}}

.architecture-tag {{
    color: #ff1e1e;
    font-weight: 800;
    letter-spacing: 4px;
    font-size: 14px;
}}

.architecture-title {{
    font-size: clamp(42px, 5vw, 64px);
    font-weight: 900;
    color: white;
    margin: 20px 0;
    line-height: 1.1;
}}

.architecture-title span {{
    color: #ff1e1e;
}}

.architecture-subtitle {{
    font-size: 20px;
    color: #cbd5e1;
    line-height: 1.6;
}}

/* Image Container */
.architecture-image-wrapper {{
    width: 100%;
    max-width: 1600px;
    margin: 0 auto;
    padding: 32px;
    border-radius: 26px;

    background: linear-gradient(180deg, #0b0f17, #020617);

    box-shadow:
        inset 0 0 0 1px rgba(255,255,255,0.06),
        0 0 90px rgba(255,30,30,0.35);
}}

/* Image */
.architecture-image {{
    width: 100%;
    height: auto;
    display: block;
    border-radius: 18px;
}}

/* Mobile */
@media (max-width: 768px) {{
    .architecture-section {{
        padding: 80px 20px;
    }}

    .architecture-image-wrapper {{
        padding: 18px;
    }}
}}


/* ================= DASHBOARDS SECTION ================= */

.dashboards-section {{
    padding: 80px 48px;
    background: linear-gradient(to bottom, #f8f9fa);
}}

.dashboards-header {{
    text-align: center;
    max-width: 1100px;
    margin: 0 auto 60px;
}}

.dashboards-tag {{
    color: #ff1e1e;
    font-weight: 800;
    letter-spacing: 4px;
    font-size: 14px;
}}

.dashboards-title {{
    font-size: clamp(42px, 5vw, 64px);
    font-weight: 900;
    color: #white;
    margin: 20px 0;
}}

.dashboards-title span {{
    color: #ff1e1e;
}}

.dashboards-subtitle {{
    font-size: 20px;
    color: #475569;
    line-height: 1.6;
}}

.dashboards-grid {{
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
  margin-top: 18px;
}}

.dashboard-card {{
  background: linear-gradient(135deg, #ffffff, #f8f9fa);
  padding: 24px;
  border-radius: 18px;
  position: relative;
  overflow: hidden;
  border: 2px solid rgba(255,30,30,0.15);
  box-shadow: 0 8px 24px rgba(0,0,0,0.12);
  transition: all 0.3s ease;
}}

.dashboard-card:hover {{
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(255,30,30,0.25);
  border-color: rgba(255,30,30,0.3);
}}

.dashboard-card h3 {{
  margin: 0 0 12px 0;
  font-size: 22px;
  font-weight: 900;
  color: #ff1e1e;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}}

.dashboard-card p {{
  color: #1e293b;
  font-size: 15px;
  font-weight: 500;
  margin-bottom: 16px;
  line-height: 1.5;
}}

.dashboard-image {{
  width: 100%;
  border-radius: 12px;
  display: block;
  object-fit: cover;
  border: 1px solid rgba(0,0,0,0.08);
}}

.img-actions {{
  position: absolute;
  top: 32px;
  right: 32px;
  display: flex;
  gap: 10px;
  z-index: 20;
}}

.img-btn {{
  background: #ff1e1e;
  border: 2px solid #ff1e1e;
  color: white;
  padding: 10px 18px;
  border-radius: 10px;
  font-weight: 800;
  cursor: pointer;
  font-size: 14px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(255,30,30,0.3);
}}

.img-btn:hover {{
  background: #dc1a1a;
  border-color: #dc1a1a;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(255,30,30,0.5);
}}

.img-modal {{
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.95);
  display: none;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 0;
  overflow: hidden;
}}

.img-modal.show {{
  display: flex;
}}

.img-modal img {{
  max-width: 100%;
  max-height: 100%;
  width: auto;
  height: auto;
  object-fit: contain;
  border-radius: 0;
  box-shadow: none;
}}

.modal-close {{
  position: absolute;
  top: 20px;
  right: 20px;
  background: rgba(0,0,0,0.7);
  color: white;
  border: 1px solid rgba(255,255,255,0.2);
  padding: 12px 18px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 700;
  font-size: 14px;
  z-index: 10000;
  transition: all 0.2s ease;
}}

.modal-close:hover {{
  background: rgba(255,30,30,0.8);
  border-color: rgba(255,30,30,0.6);
}}

/* MOBILE */
@media (max-width: 900px) {{
    .dashboards-grid {{
        grid-template-columns: 1fr;
    }}
}}


</style>
</head>

<body>

<div class="navbar">
  <div class="brand">
    <div class="logo">⚡</div>
    Churn<span style="color:#ff1e1e">Guard</span>
  </div>
</div>

<section class="hero">
  <div class="hero-content">
    <div class="badge">● AI-Powered Retention Intelligence</div>
    <div class="hero-title-small">RETENTIONIQ – ENTERPRISE CUSTOMER CHURN<br><span>INTELLIGENCE PLATFORM</span></div>
    <div class="hero-title-main">Stop Churn Before<br><span>It Happens</span></div>
    <div class="hero-sub">
      Built an AI-powered telecom retention analytics platform using PostgreSQL,
      Streamlit, Power BI, Excel, Python, Colab and GPT-based querying.
    </div>
  </div>
</section>

<section class="kpi-wrapper">
  <div class="kpi-title">KPI SNAPSHOT</div>
  <div class="kpi-grid">
    <div class="kpi-card"><div class="kpi-value">{total_customers:,}</div><div class="kpi-label">Total Customers</div></div>
    <div class="kpi-card"><div class="kpi-value">{kpis['churned_customers']:,}</div><div class="kpi-label">Churned Customers</div></div>
    <div class="kpi-card"><div class="kpi-value">{kpis['churn_rate']}%</div><div class="kpi-label">Churn Rate</div></div>
    <div class="kpi-card"><div class="kpi-value">{kpis['retention_rate']}%</div><div class="kpi-label">Retention Rate</div></div>
    <div class="kpi-card"><div class="kpi-value">${int(revenue_at_risk):,}</div><div class="kpi-label">Revenue at Risk</div></div>
    <div class="kpi-card"><div class="kpi-value">${int(total_revenue):,}</div><div class="kpi-label">Total Revenue</div></div>
    <div class="kpi-card"><div class="kpi-value">${int(revenue_protected):,}</div><div class="kpi-label">Revenue Protected</div></div>
    <div class="kpi-card"><div class="kpi-value">${arpu:,}</div><div class="kpi-label">ARPU</div></div>
  </div>

</section>
<section class="features">

  <div class="features-header">
    FEATURES
    <h2>
      Intelligent Retention<br/>
      <span>At Your Fingertips</span>
    </h2>
    <p>
      Everything you need to understand, predict, and prevent customer churn
      in one powerful platform.
    </p>
  </div>


  <div class="features-grid">

    <!-- Predictive AI -->
    <div class="feature-card">
      <div class="icon-box">
        <!-- Brain icon -->
        <svg fill="none" viewBox="0 0 24 24" stroke-width="2">
          <path d="M9 4a3 3 0 0 0-3 3v10a3 3 0 0 0 3 3"/>
          <path d="M15 4a3 3 0 0 1 3 3v10a3 3 0 0 1-3 3"/>
          <path d="M9 8h6M9 12h6M9 16h6"/>
        </svg>
      </div>
      <h3>Predictive AI Engine</h3>
      <p>Machine learning models analyze 200+ behavioral signals to identify at-risk customers before they churn.</p>
    </div>

    <!-- Real-time Analytics (highlight) -->
    <div class="feature-card highlight">
      <div class="icon-box">
        <svg fill="none" viewBox="0 0 24 24" stroke-width="2">
          <path d="M4 19h16"/>
          <path d="M6 16V8M12 16V4M18 16v-6"/>
        </svg>
      </div>
      <h3>Real-Time Analytics</h3>
      <p>Live dashboards showing churn probability scores, retention metrics, and customer health indicators.</p>
    </div>

    <!-- Alerts -->
    <div class="feature-card">
      <div class="icon-box">
        <svg fill="none" viewBox="0 0 24 24" stroke-width="2">
          <path d="M15 17h5l-1.4-1.4A2 2 0 0 1 18 14V11a6 6 0 1 0-12 0v3a2 2 0 0 1-.6 1.4L4 17h5"/>
          <path d="M9 17a3 3 0 0 0 6 0"/>
        </svg>
      </div>
      <h3>Proactive Alerts</h3>
      <p>Automated notifications when high-value customers show early warning signs of potential churn.</p>
    </div>

    <!-- Targeted Campaigns -->
    <div class="feature-card">
      <div class="icon-box">
        <svg fill="none" viewBox="0 0 24 24" stroke-width="2">
          <circle cx="12" cy="12" r="9"/>
          <circle cx="12" cy="12" r="4"/>
          <path d="M12 3v6M21 12h-6"/>
        </svg>
      </div>
      <h3>Targeted Campaigns</h3>
      <p>AI-recommended retention offers and personalized engagement strategies for each customer segment.</p>
    </div>

    <!-- Integration -->
    <div class="feature-card">
      <div class="icon-box">
        <svg fill="none" viewBox="0 0 24 24" stroke-width="2">
          <path d="M13 2L3 14h7l-1 8 10-12h-7l1-8z"/>
        </svg>
      </div>
      <h3>Instant Integration</h3>
      <p>Connect with your existing CRM, billing systems, and support platforms in minutes, not months.</p>
    </div>

    <!-- Security -->
    <div class="feature-card">
      <div class="icon-box">
        <svg fill="none" viewBox="0 0 24 24" stroke-width="2">
          <rect x="3" y="11" width="18" height="11" rx="2"/>
          <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
        </svg>
      </div>
      <h3>Enterprise Security</h3>
      <p>SOC 2 Type II certified with end-to-end encryption protecting your sensitive customer data.</p>
    </div>

  </div>
</section>

<section class="architecture-wrapper">
  <div class="architecture-header">
    <span class="architecture-tag">ARCHITECTURE</span>
    <h2 class="architecture-title">End-to-End Telecom<br><span>Retention Architecture</span></h2>
    <p class="architecture-subtitle">Scalable analytics & AI-driven decision system.</p>
  </div>
  <div class="architecture-grid">

    <div class="arch-card">
      <h3>Data Sources</h3>
      <p>Customer usage logs, billing records, CRM data, network events, and support tickets.</p>
    </div>

    <div class="arch-arrow">➜</div>

    <div class="arch-card">
      <h3>Ingestion & Processing</h3>
      <p>Python pipelines for validation, cleaning, feature engineering, and aggregations.</p>
    </div>

    <div class="arch-arrow">➜</div>

    <div class="arch-card">
      <h3>Data Warehouse</h3>
      <p>PostgreSQL stores fact tables, dimensions, and KPI marts optimized for analytics.</p>
    </div>

    <div class="arch-arrow">➜</div>

    <div class="arch-card">
      <h3>Analytics & ML</h3>
      <p>Churn prediction models, cohort analysis, revenue-at-risk, and health scoring.</p>
    </div>

    <div class="arch-arrow">➜</div>

    <div class="arch-card">
      <h3>Application Layer</h3>
      <p>Streamlit dashboards, Power BI reports, executive KPIs, operational views.</p>
    </div>

    <div class="arch-arrow">➜</div>

    <div class="arch-card">
      <h3>AI Decision Engine</h3>
      <p>GPT-powered insights, natural language queries, recommendations, and actions.</p>
    </div>
    </div>

<div class="architecture-image-wrapper">
  <img
    src="data:image/png;base64,{architecture_img}"
    alt="Telecom Customer Churn Analytics Architecture"
    class="architecture-image"
  />
</div>

</section>

<section class="dashboards-section">

  <div class="dashboards-header">
    <div class="dashboards-tag">DASHBOARDS</div>
    <h2 class="dashboards-title">
      Executive & Operational<br>
      <span>Retention Dashboards</span>
    </h2>
    <p class="dashboards-subtitle">
      Actionable insights across churn, revenue risk, customer segments,
      and retention performance.
    </p>
  </div>

  <div class="dashboards-grid">
      <div class="dashboard-card">
        <div class="img-actions">
          <button class="img-btn" onclick="openFullscreen('data:image/jpeg;base64,{dash_overview}')">Fullscreen</button>
        </div>
        <h3>Churn Overview</h3>
        <p>High-level churn metrics, KPIs, and customer health indicators.</p>
        <img class="dashboard-image" src="data:image/jpeg;base64,{dash_overview}" alt="Churn Overview" />
      </div>

      <div class="dashboard-card">
        <div class="img-actions">
          <button class="img-btn" onclick="openFullscreen('data:image/jpeg;base64,{dash_trends}')">Fullscreen</button>
        </div>
        <h3>Churn Trends</h3>
        <p>Monthly churn patterns, seasonality, and behavioral changes.</p>
        <img class="dashboard-image" src="data:image/jpeg;base64,{dash_trends}" alt="Churn Trends" />
      </div>

      <div class="dashboard-card">
        <div class="img-actions">
          <button class="img-btn" onclick="openFullscreen('data:image/jpeg;base64,{dash_revenue}')">Fullscreen</button>
        </div>
        <h3>Revenue at Risk</h3>
        <p>Revenue exposure analysis with churn probability and ARPU impact.</p>
        <img class="dashboard-image" src="data:image/jpeg;base64,{dash_revenue}" alt="Revenue at Risk" />
      </div>

      <div class="dashboard-card">
        <div class="img-actions">
          <button class="img-btn" onclick="openFullscreen('data:image/jpeg;base64,{dash_segment}')">Fullscreen</button>
        </div>
        <h3>Segment Deep Dive</h3>
        <p>Cohort analysis by plan, tenure, geography, and usage behavior.</p>
        <img class="dashboard-image" src="data:image/jpeg;base64,{dash_segment}" alt="Segment Deep Dive" />
      </div>
    </div>

</section>

<!-- Image Modal -->
<div id="imgModal" class="img-modal" onclick="closeModal()">
  <button class="modal-close" onclick="closeModal()">✕ Close</button>
  <img id="modalImage" src="" alt="Dashboard Preview" />
</div>

<script>
// Open fullscreen modal
function openFullscreen(imageSrc) {{
  const modal = document.getElementById('imgModal');
  const modalImg = document.getElementById('modalImage');

  modalImg.src = imageSrc;
  modal.classList.add('show');

  // Prevent body scroll when modal is open
  document.body.style.overflow = 'hidden';
}}

// Close modal
function closeModal() {{
  const modal = document.getElementById('imgModal');
  modal.classList.remove('show');

  // Restore body scroll
  document.body.style.overflow = 'auto';
}}

// Close modal with Escape key
document.addEventListener('keydown', function(event) {{
  if (event.key === 'Escape') {{
    closeModal();
  }}
}});

// Prevent click propagation on modal image
document.getElementById('modalImage').addEventListener('click', function(event) {{
  event.stopPropagation();
}});

// Prevent click propagation on close button
document.querySelector('.modal-close').addEventListener('click', function(event) {{
  event.stopPropagation();
}});
</script>

</body>
</html>
""",
    height=4500,
    scrolling=True
)