"""
Store Performance Page
Multi-store comparison with detailed metrics including profitability analysis.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
from dateutil.relativedelta import relativedelta

from app.queries import (
    get_regions, get_categories,
)

# Import store-specific queries
from app.database import run_query

# ── Page Config ──────────────────────────────────────────────
st.set_page_config(
    page_title="Store Performance",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .section-header {
        font-size: 1.1rem; font-weight: 600; color: #374151;
        margin: 1.5rem 0 0.75rem 0;
        border-left: 4px solid #667eea; padding-left: 10px;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 0.5rem;
        min-height: 140px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .metric-label {
        font-size: 0.85rem;
        opacity: 0.9;
        margin-bottom: 0.5rem;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
    }
    .metric-delta {
        font-size: 0.75rem;
        margin-top: 0.5rem;
        opacity: 0.85;
    }
</style>
""", unsafe_allow_html=True)

# ── Sidebar Filters ──────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏪 Store Performance")
    
    st.markdown("#### Date Range")
    default_end   = date.today()
    default_start = default_end - relativedelta(months=6)
    start_date = st.date_input("Start Date", value=default_start)
    end_date   = st.date_input("End Date",   value=default_end)

    if start_date >= end_date:
        st.error("Start date must be before end date.")
        st.stop()

    st.markdown("#### Select Stores to Compare")
    
    # Get all stores
    stores_df = run_query("SELECT store_id, store_name, city, region_id FROM stores ORDER BY store_name")
    store_options = {f"{row['store_name']} ({row['city']})": row['store_id'] 
                     for _, row in stores_df.iterrows()}
    
    selected_stores = st.multiselect(
        "Choose stores",
        list(store_options.keys()),
        default=list(store_options.keys())[:1] if store_options else [],
        help="Select one or more stores to compare"
    )
    
    if not selected_stores:
        st.error("Please select at least one store.")
        st.stop()
    
    store_ids = [store_options[s] for s in selected_stores]
    
    st.markdown("---")
    st.caption(f"📅 {start_date} → {end_date}")
    st.caption(f"🏪 {len(selected_stores)} store(s) selected")


# ── Main Content ───────────────────────────────────────────
st.title("🏪 Store Performance Analysis")
st.markdown(f"**Period:** {start_date.strftime('%d %b %Y')} → {end_date.strftime('%d %b %Y')} | **Stores:** {len(selected_stores)}")
st.markdown("---")

# Get store summary data
placeholders = ",".join([f":{i}" for i in range(len(store_ids))])
params = {"start_date": start_date, "end_date": end_date}
for i, sid in enumerate(store_ids):
    params[str(i)] = sid

store_summary_sql = f"""
    SELECT
        s.store_id,
        s.store_name,
        r.region_name,
        s.city,
        s.store_size,
        COUNT(DISTINCT o.order_id)               AS total_orders,
        COUNT(DISTINCT o.customer_id)            AS unique_customers,
        ROUND(SUM(oi.line_total)::numeric, 2)    AS total_revenue,
        ROUND(AVG(order_totals.order_revenue)::numeric, 2) AS avg_order_value,
        ROUND(SUM(p.cost_price * oi.quantity)::numeric, 2) AS total_cost,
        ROUND(SUM(oi.line_total) - SUM(p.cost_price * oi.quantity)::numeric, 2) AS gross_profit,
        ROUND(((SUM(oi.line_total) - SUM(p.cost_price * oi.quantity)) / SUM(oi.line_total) * 100)::numeric, 2) AS profit_margin_pct
    FROM orders o
    JOIN stores s ON s.store_id = o.store_id
    JOIN regions r ON r.region_id = s.region_id
    JOIN order_items oi ON oi.order_id = o.order_id
    JOIN products p ON p.product_id = oi.product_id
    JOIN (
        SELECT order_id, SUM(line_total) AS order_revenue
        FROM order_items GROUP BY order_id
    ) order_totals ON order_totals.order_id = o.order_id
    WHERE o.order_status = 'Completed'
      AND o.order_date BETWEEN :start_date AND :end_date
      AND s.store_id IN ({placeholders})
    GROUP BY s.store_id, s.store_name, r.region_name, s.city, s.store_size
    ORDER BY total_revenue DESC
"""

store_data = run_query(store_summary_sql, params)

if store_data.empty:
    st.warning("No data found for selected stores.")
    st.stop()

# ── Store Comparison Table ───────────────────────────────────
st.markdown('<p class="section-header">📋 Store Comparison Summary</p>', unsafe_allow_html=True)

display_df = store_data[[
    "store_name", "region_name", "city", "store_size",
    "total_orders", "unique_customers", "total_revenue",
    "avg_order_value", "gross_profit", "profit_margin_pct"
]].copy()

display_df.columns = ["Store", "Region", "City", "Size", "Orders", "Customers", "Revenue", "AOV", "Profit", "Margin %"]
display_df["Revenue"] = display_df["Revenue"].astype(float).apply(lambda x: f"₹{x:,.0f}")
display_df["AOV"] = display_df["AOV"].astype(float).apply(lambda x: f"₹{x:,.2f}")
display_df["Profit"] = display_df["Profit"].astype(float).apply(lambda x: f"₹{x:,.0f}")
display_df["Margin %"] = display_df["Margin %"].astype(str) + "%"

st.dataframe(display_df, use_container_width=True, hide_index=True)

# ── Revenue vs Profit Comparison ─────────────────────────────
st.markdown('<p class="section-header">💹 Revenue vs Profit Analysis</p>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    fig_rev = px.bar(
        store_data, x="store_name", y="total_revenue",
        color="total_revenue",
        labels={"total_revenue": "Revenue (₹)", "store_name": "Store"},
        title="Total Revenue by Store",
        color_continuous_scale="Blues",
        text_auto=True,
    )
    fig_rev.update_layout(height=350, showlegend=False, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig_rev, use_container_width=True)

with col2:
    fig_profit = px.bar(
        store_data, x="store_name", y="gross_profit",
        color="profit_margin_pct",
        labels={"gross_profit": "Profit (₹)", "store_name": "Store", "profit_margin_pct": "Margin %"},
        title="Gross Profit & Margin % by Store",
        color_continuous_scale="Greens",
        text_auto=True,
    )
    fig_profit.update_layout(height=350, showlegend=True, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig_profit, use_container_width=True)

# ── Efficiency Metrics ───────────────────────────────────────
st.markdown('<p class="section-header">📊 Store Efficiency Metrics</p>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    fig_aov = px.bar(
        store_data.sort_values("avg_order_value", ascending=True),
        x="avg_order_value", y="store_name",
        orientation="h",
        labels={"avg_order_value": "AOV (₹)", "store_name": ""},
        title="Average Order Value",
        color="avg_order_value",
        color_continuous_scale="Viridis",
        text_auto=".0f",
    )
    fig_aov.update_layout(height=350, showlegend=False, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig_aov, use_container_width=True)

with col2:
    fig_cust = px.bar(
        store_data.sort_values("unique_customers", ascending=True),
        x="unique_customers", y="store_name",
        orientation="h",
        labels={"unique_customers": "Customers", "store_name": ""},
        title="Unique Customers",
        color="unique_customers",
        color_continuous_scale="Reds",
        text_auto=True,
    )
    fig_cust.update_layout(height=350, showlegend=False, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig_cust, use_container_width=True)

with col3:
    fig_margin = px.bar(
        store_data.sort_values("profit_margin_pct", ascending=True),
        x="profit_margin_pct", y="store_name",
        orientation="h",
        labels={"profit_margin_pct": "Margin %", "store_name": ""},
        title="Profit Margin %",
        color="profit_margin_pct",
        color_continuous_scale="Purples",
        text_auto=".1f",
    )
    fig_margin.update_layout(height=350, showlegend=False, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig_margin, use_container_width=True)

# ── Detailed Store Analysis (if single store selected) ────────
if len(store_ids) == 1:
    st.markdown("---")
    st.markdown('<p class="section-header">🔍 Detailed Store Analysis</p>', unsafe_allow_html=True)
    
    store_id = store_ids[0]
    store_name = store_data.iloc[0]["store_name"]
    
    # Monthly trend
    trend_sql = """
        SELECT
            DATE_TRUNC('month', o.order_date)::date  AS month,
            ROUND(SUM(oi.line_total)::numeric, 2)    AS revenue,
            ROUND(SUM(p.cost_price * oi.quantity)::numeric, 2) AS cost,
            ROUND(SUM(oi.line_total) - SUM(p.cost_price * oi.quantity)::numeric, 2) AS profit,
            COUNT(DISTINCT o.order_id)               AS orders
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.order_id
        JOIN products p ON p.product_id = oi.product_id
        WHERE o.order_status = 'Completed'
          AND o.order_date BETWEEN :start_date AND :end_date
          AND o.store_id = :store_id
        GROUP BY 1
        ORDER BY 1
    """
    
    trend_data = run_query(trend_sql, {"start_date": start_date, "end_date": end_date, "store_id": store_id})
    
    if not trend_data.empty:
        trend_data["month"] = pd.to_datetime(trend_data["month"])
        
        st.markdown(f"#### 📈 Monthly Trend for {store_name}")
        
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=trend_data["month"], y=trend_data["revenue"],
            mode="lines+markers", name="Revenue",
            line=dict(color="#667eea", width=2.5), marker=dict(size=6),
            fill="tozeroy", fillcolor="rgba(102,126,234,0.1)",
        ))
        fig_trend.add_trace(go.Scatter(
            x=trend_data["month"], y=trend_data["profit"],
            mode="lines+markers", name="Profit",
            line=dict(color="#10b981", width=2.5), marker=dict(size=6),
        ))
        
        fig_trend.update_layout(
            xaxis_title="Month", yaxis_title="Amount (₹)",
            height=350, margin=dict(l=20, r=20, t=20, b=20),
            hovermode="x unified",
        )
        st.plotly_chart(fig_trend, use_container_width=True)
    
    # Top products for this store
    st.markdown(f"#### 📦 Top Products in {store_name}")
    
    products_sql = """
        SELECT
            p.product_name,
            cat.category_name,
            SUM(oi.quantity)                         AS units_sold,
            ROUND(SUM(oi.line_total)::numeric, 2)    AS revenue,
            ROUND(SUM(p.cost_price * oi.quantity)::numeric, 2) AS cost,
            ROUND(SUM(oi.line_total) - SUM(p.cost_price * oi.quantity)::numeric, 2) AS profit
        FROM order_items oi
        JOIN orders o ON o.order_id = oi.order_id
        JOIN products p ON p.product_id = oi.product_id
        JOIN categories cat ON cat.category_id = p.category_id
        WHERE o.order_status = 'Completed'
          AND o.order_date BETWEEN :start_date AND :end_date
          AND o.store_id = :store_id
        GROUP BY p.product_name, cat.category_name
        ORDER BY revenue DESC
        LIMIT 10
    """
    
    products_data = run_query(products_sql, {"start_date": start_date, "end_date": end_date, "store_id": store_id})
    
    if not products_data.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            fig_prod_rev = px.bar(
                products_data.sort_values("revenue"),
                x="revenue", y="product_name",
                orientation="h",
                labels={"revenue": "Revenue (₹)", "product_name": ""},
                title="Top Products by Revenue",
                color_discrete_sequence=["#667eea"],
                text_auto=".0f",
            )
            fig_prod_rev.update_layout(height=350, showlegend=False, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_prod_rev, use_container_width=True)
        
        with col2:
            fig_prod_profit = px.bar(
                products_data.sort_values("profit"),
                x="profit", y="product_name",
                orientation="h",
                labels={"profit": "Profit (₹)", "product_name": ""},
                title="Top Products by Profit",
                color_discrete_sequence=["#10b981"],
                text_auto=".0f",
            )
            fig_prod_profit.update_layout(height=350, showlegend=False, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_prod_profit, use_container_width=True)

st.markdown("---")
st.caption("🏪 Store Performance Dashboard | Powered by Streamlit + PostgreSQL")
