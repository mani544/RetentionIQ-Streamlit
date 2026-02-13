import pandas as pd
import time
from sqlalchemy import create_engine, text
from pathlib import Path

# =====================================================
# DATABASE
# =====================================================
DB_URI = "postgresql://postgres:root@localhost:5432/telecom_churn_analytics"
engine = create_engine(DB_URI)

# =====================================================
# TIME-SERIES FEATURE ENGINEERING
# =====================================================
QUERY = """

-- ============================
-- BILLING TIME FEATURES
-- ============================
WITH billing_ranked AS (
    SELECT
        customer_id,
        billing_month,
        monthly_charges::NUMERIC,
        total_charges::NUMERIC,

        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY billing_month DESC
        ) AS rn,

        LAG(monthly_charges::NUMERIC) OVER (
            PARTITION BY customer_id
            ORDER BY billing_month
        ) AS prev_month_charge

    FROM fact_billing
),

billing_features AS (
    SELECT
        customer_id,

        AVG(monthly_charges) AS avg_monthly_charges,
        STDDEV(monthly_charges) AS charges_volatility,
        SUM(total_charges) AS lifetime_value,

        MAX(monthly_charges) FILTER (WHERE rn = 1) AS last_month_charge,
        MAX(prev_month_charge) FILTER (WHERE rn = 1) AS prev_month_charge,

        MAX(monthly_charges - prev_month_charge)
            FILTER (WHERE rn = 1) AS charge_change

    FROM billing_ranked
    GROUP BY customer_id
),

-- ============================
-- SUPPORT TIME FEATURES
-- ============================
support_ranked AS (
    SELECT
        customer_id,
        month,
        tickets_count::NUMERIC,
        csat_score::NUMERIC,

        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY month DESC
        ) AS rn,

        LAG(tickets_count::NUMERIC) OVER (
            PARTITION BY customer_id
            ORDER BY month
        ) AS prev_tickets

    FROM fact_support
),

support_features AS (
    SELECT
        customer_id,

        SUM(tickets_count) AS total_tickets,
        AVG(tickets_count) AS avg_tickets,
        STDDEV(tickets_count) AS tickets_volatility,

        AVG(csat_score) AS avg_csat,
        STDDEV(csat_score) AS csat_volatility,

        MAX(tickets_count) FILTER (WHERE rn = 1) AS last_month_tickets,
        MAX(prev_tickets) FILTER (WHERE rn = 1) AS prev_month_tickets,

        MAX(tickets_count - prev_tickets)
            FILTER (WHERE rn = 1) AS ticket_change

    FROM support_ranked
    GROUP BY customer_id
),

-- ============================
-- NETWORK TIME FEATURES
-- ============================
network_ranked AS (
    SELECT
        customer_id,
        month,
        downtime_minutes::NUMERIC,
        avg_latency::NUMERIC,
        packet_loss::NUMERIC,

        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY month DESC
        ) AS rn,

        LAG(downtime_minutes::NUMERIC) OVER (
            PARTITION BY customer_id
            ORDER BY month
        ) AS prev_downtime

    FROM fact_network_quality
),

network_features AS (
    SELECT
        customer_id,

        AVG(downtime_minutes) AS avg_downtime,
        STDDEV(downtime_minutes) AS downtime_volatility,

        AVG(avg_latency) AS avg_latency,
        AVG(packet_loss) AS avg_packet_loss,

        MAX(downtime_minutes) FILTER (WHERE rn = 1) AS last_month_downtime,
        MAX(prev_downtime) FILTER (WHERE rn = 1) AS prev_month_downtime,

        MAX(downtime_minutes - prev_downtime)
            FILTER (WHERE rn = 1) AS downtime_change

    FROM network_ranked
    GROUP BY customer_id
),

-- ============================
-- CHURN LABEL
-- ============================
churn AS (
    SELECT
        customer_id,
        MAX(churn_flag::INT) AS churn_flag
    FROM fact_churn
    GROUP BY customer_id
)

-- ============================
-- FINAL DATASET
-- ============================
SELECT
    dc.customer_id,
    dc.region,
    dc.customer_segment,
    EXTRACT(MONTH FROM AGE(CURRENT_DATE, dc.join_date)) AS tenure_months,

    b.*,
    s.*,
    n.*,
    c.churn_flag

FROM dim_customers dc
LEFT JOIN billing_features b USING (customer_id)
LEFT JOIN support_features s USING (customer_id)
LEFT JOIN network_features n USING (customer_id)
LEFT JOIN churn c USING (customer_id)

"""

# =====================================================
# LOAD DATA
# =====================================================
def load_data(query, engine):
    with engine.connect() as conn:
        result = conn.execute(text(query))
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    return df

# =====================================================
# MAIN
# =====================================================
if __name__ == "__main__":

    print("=" * 60)
    print("BUILDING TIME-SERIES TRAINING DATASET")
    print("=" * 60)

    start = time.time()

    df = load_data(QUERY, engine)
    df = df.fillna(0)

    Path("data").mkdir(exist_ok=True)
    df.to_csv("data/ml_training_data.csv", index=False)

    end = time.time()

    print("Rows:", len(df))
    print("Columns:", len(df.columns))
    print("Saved → data/ml_training_data.csv")
    print("Time:", round(end - start, 2), "seconds")
