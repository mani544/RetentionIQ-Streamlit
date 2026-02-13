"""
Database Service for ChurnGuard
Handles all PostgreSQL database interactions
"""

import os
import psycopg2
from typing import Dict, Any, List, Optional
from contextlib import contextmanager
from sqlalchemy import create_engine

class DatabaseService:
    """Service for database operations"""

    def __init__(self):
        """Initialize database connection parameters"""
        self.db_params = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'telecom_churn_analytics'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'root')
        }
        # If DATABASE_URL is provided, psycopg2.connect will accept it instead
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            # Try to parse from URL for printing only; keep db_params as fallback
            print(f"✓ Database configured (via DATABASE_URL)")
        else:
            print(f"✓ Database configured: {self.db_params['user']}@{self.db_params['host']}:{self.db_params['port']}/{self.db_params['database']}")

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            database_url = os.getenv("DATABASE_URL")
            if database_url:
                conn = psycopg2.connect(database_url)
            else:
                conn = psycopg2.connect(**self.db_params)
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"❌ Database connection error: {str(e)}")
            raise e
        finally:
            if conn:
                conn.close()

    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute a SELECT query and return results"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]

    def execute_single(self, query: str, params: tuple = None) -> Optional[Dict]:
        """Execute a query and return single result"""
        results = self.execute_query(query, params)
        return results[0] if results else None


# Singleton instance
_db_service = None


def get_db_service() -> DatabaseService:
    """Get or create database service instance"""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service


def get_engine():
    """
    Return SQLAlchemy engine using DATABASE_URL if present, otherwise build from individual env vars.
    Used by queries.py which expects get_engine().
    """
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return create_engine(database_url)
    else:
        user = os.getenv('DB_USER', 'postgres')
        password = os.getenv('DB_PASSWORD', 'root')
        host = os.getenv('DB_HOST', 'localhost')
        port = os.getenv('DB_PORT', '5432')
        dbname = os.getenv('DB_NAME', 'telecom_churn_analytics')
        url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"
        return create_engine(url)


# ==================== KPI QUERIES ====================

def fetch_kpis() -> Dict[str, Any]:
    """
    Fetch all main KPI metrics from mart_retention_kpis

    Returns:
        Dictionary containing aggregated KPI values
    """
    try:
        db = get_db_service()

        query = """
        SELECT 
            SUM(total_customers) as total_customers,
            SUM(churned_customers) as churned_customers,
            ROUND(AVG(churn_rate), 2) as churn_rate,
            ROUND(AVG(retention_rate), 2) as retention_rate,
            ROUND(SUM(total_revenue)::numeric, 2) as total_revenue,
            ROUND(SUM(revenue_at_risk)::numeric, 2) as revenue_at_risk
        FROM mart_retention_kpis
        """

        result = db.execute_single(query)

        if result:
            # Calculate ARPU
            total_customers = result['total_customers'] or 1
            total_revenue = result['total_revenue'] or 0
            arpu = round(total_revenue / total_customers, 2) if total_customers else 0
            result['arpu'] = arpu
            print(f"✓ KPIs loaded: {int(result.get('total_customers', 0)):,} customers, {result.get('churn_rate')}% churn")

        return result if result else {}

    except Exception as e:
        print(f"❌ Error fetching KPIs: {str(e)}")
        print("⚠ Using fallback dashboard data...")
        return {
            "total_customers": 1200000,
            "churned_customers": 222000,
            "churn_rate": 18.5,
            "retention_rate": 81.5,
            "total_revenue": 1490000000,
            "revenue_at_risk": 289310000,
            "arpu": 1241.70
        }


def fetch_segment_data() -> Dict[str, Any]:
    try:
        db = get_db_service()

        query = """
        SELECT 
            customer_segment,
            SUM(total_customers) as customer_count,
            ROUND(AVG(churn_rate), 2) as churn_rate,
            ROUND(AVG(total_revenue / NULLIF(total_customers, 0)), 2) as avg_revenue,
            ROUND(SUM(revenue_at_risk)::numeric, 2) as revenue_at_risk
        FROM mart_retention_kpis
        GROUP BY customer_segment
        ORDER BY churn_rate DESC
        """

        results = db.execute_query(query)

        segments = {}
        for row in results:
            segments[row['customer_segment']] = {
                'count': row['customer_count'],
                'churn_rate': float(row['churn_rate']),
                'avg_revenue': float(row['avg_revenue'] or 0),
                'revenue_at_risk': float(row['revenue_at_risk'])
            }

        return segments

    except Exception as e:
        print(f"Error fetching segment data: {str(e)}")
        return {
            'Retail': {
                'count': 1052448,
                'churn_rate': 19.0,
                'avg_revenue': 1241.86,
                'revenue_at_risk': 254300000
            },
            'SME': {
                'count': 147552,
                'churn_rate': 18.0,
                'avg_revenue': 1240.51,
                'revenue_at_risk': 34900000
            }
        }


def fetch_regional_data() -> Dict[str, Any]:
    try:
        db = get_db_service()

        query = """
        SELECT 
            region,
            SUM(total_customers) as customer_count,
            ROUND(AVG(churn_rate), 2) as churn_rate,
            ROUND(SUM(total_revenue)::numeric, 2) as total_revenue,
            ROUND(SUM(revenue_at_risk)::numeric, 2) as revenue_at_risk
        FROM mart_retention_kpis
        GROUP BY region
        ORDER BY revenue_at_risk DESC
        """

        results = db.execute_query(query)

        regions = {}
        for row in results:
            regions[row['region']] = {
                'customer_count': row['customer_count'],
                'churn_rate': float(row['churn_rate']),
                'total_revenue': float(row['total_revenue']),
                'revenue_at_risk': float(row['revenue_at_risk'])
            }

        return regions

    except Exception as e:
        print(f"Error fetching regional data: {str(e)}")
        return {
            'South': {'customer_count': 300000, 'churn_rate': 24.63, 'total_revenue': 516220000, 'revenue_at_risk': 102000000},
            'West': {'customer_count': 300000, 'churn_rate': 25.18, 'total_revenue': 375030000, 'revenue_at_risk': 73000000},
            'North': {'customer_count': 300000, 'churn_rate': 24.78, 'total_revenue': 372160000, 'revenue_at_risk': 72000000},
            'East': {'customer_count': 300000, 'churn_rate': 25.40, 'total_revenue': 226630000, 'revenue_at_risk': 43000000}
        }


def fetch_revenue_breakdown() -> Dict[str, float]:
    try:
        db = get_db_service()

        query = """
        SELECT 
            dc.acquisition_channel,
            ROUND(SUM(fb.monthly_charges)::numeric, 2) as channel_revenue
        FROM stg_billing fb
        JOIN stg_customers dc ON fb.customer_id = dc.customer_id
        GROUP BY dc.acquisition_channel
        ORDER BY channel_revenue DESC
        """

        results = db.execute_query(query)

        revenue = {}
        for row in results:
            revenue[row['acquisition_channel']] = float(row['channel_revenue'])

        return revenue

    except Exception as e:
        print(f"Error fetching revenue breakdown: {str(e)}")
        return {
            'Online': 4225770000,
            'Store': 3297930000,
            'Agent': 1881880000
        }


def fetch_churn_reasons() -> List[Dict[str, Any]]:
    try:
        db = get_db_service()

        query = """
        SELECT 
            churn_reason,
            COUNT(*) as affected_customers,
            ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM stg_churn WHERE churn_flag = '1'), 2) as percentage
        FROM stg_churn
        WHERE churn_flag = '1' AND churn_reason IS NOT NULL
        GROUP BY churn_reason
        ORDER BY percentage DESC
        LIMIT 10
        """

        return db.execute_query(query)

    except Exception as e:
        print(f"Error fetching churn reasons: {str(e)}")
        return [
            {'churn_reason': 'Service Quality Issues', 'affected_customers': 71040, 'percentage': 32.0},
            {'churn_reason': 'Competitive Pricing', 'affected_customers': 62160, 'percentage': 28.0},
            {'churn_reason': 'Poor Customer Service', 'affected_customers': 53280, 'percentage': 24.0},
            {'churn_reason': 'Lack of Engagement', 'affected_customers': 35520, 'percentage': 16.0}
        ]
