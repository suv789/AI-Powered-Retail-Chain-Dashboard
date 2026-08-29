"""
Product Analytics Page
SKU performance, category trends, trending products, profitability analysis.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

from app.database import run_query

# ── Page Config ──────────────────────────────────────────────
st.set_page_config(
    page_title="Product Analytics",
    page_icon="📦",
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
    .gainer { color: #10b981; }
    .loser { color: #ef4444; }
</style>
""", unsafe_allow_html=True)

# ── Session State ────────────────────────────────────────────
if "reset_counter_products" not in st.session_state:
    st.session_state.reset_counter_products = 0

# ── Sidebar Filters ──────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📦 Product Analytics")
    
    st.markdown("#### Date Range")
    default_end   = date.today()
    default_start = default_end - relativedelta(months=6)
    start_date = st.date_input("Start Date", value=default_start, key=f"prod_start_{st.session_state.reset_counter_products}")
    end_date   = st.date_input("End Date",   value=default_end, key=f"prod_end_{st.session_state.reset_counter_products}")

    if start_date >= end_date:
        st.error("Start date must be before end date.")
        st.stop()

    st.markdown("#### Category Filter")
    categories_df = run_query("SELECT category_id, category_name FROM categories ORDER BY category_name")
    category_options = {row['category_name']: row['category_id'] for _, row in categories_df.iterrows()}
    
    selected_category = st.selectbox(
        "Select category",
        list(category_options.keys()),
        key=f"prod_cat_{st.session_state.reset_counter_products}"
    )
    category_id = category_options[selected_category]

    st.markdown("#### Select Products")
    products_df = run_query(f"""
        SELECT product_id, product_name, sku FROM products
        WHERE category_id = {category_id}
        ORDER BY product_name
    """)
    
    product_options = {f"{row['product_name']} ({row['sku']})": row['product_id'] 
                      for _, row in products_df.iterrows()}
    
    selected_products = st.multiselect(
        "Choose products (leave empty to show all in category)",
        list(product_options.keys()),
        key=f"prod_select_{st.session_state.reset_counter_products}"
    )
    
    if selected_products:
        product_ids = [product_options[p] for p in selected_products]
    else:
        product_ids = list(product_options.values())
    
    if not product_ids:
        st.error("No products found in this category.")
        st.stop()

    st.markdown("---")
    if st.button("🔄 Reset Filters", use_container_width=True):
        st.session_state.reset_counter_products += 1
        st.rerun()
    
    st.caption(f"📅 {start_date} → {end_date}")
    st.caption(f"📦 {selected_category}")
    st.caption(f"🏷️ {len(product_ids)} product(s)")


# ── Main Content ───────────────────────────────────────────
st.title("📦 Product Analytics Dashboard")
st.markdown(f"**Period:** {start_date.strftime('%d %b %Y')} → {end_date.strftime('%d %b %Y')} | **Category:** {selected_category}")
st.markdown("---")

# ── Trending Products (Gainers & Losers) ───────────────────
st.markdown('<p class="section-header">🚀 Trending Products (Top Gainers & Losers)</p>', unsafe_allow_html=True)

delta = (end_date - start_date).days
prior_start = start_date - timedelta(days=delta + 1)
prior_end   = start_date - timedelta(days=1)

product_placeholders = ",".join([f":{i}" for i in range(len(product_ids))])
params = {
    "start_date": start_date, "end_date": end_date,
    "prior_start": prior_start, "prior_end": prior_end,
    "category_id": category_id
}
for i, pid in enumerate(product_ids):
    params[str(i)] = pid

trending_sql = f"""
    SELECT
        p.product_name,
        p.sku,
        SUM(CASE WHEN o.order_date BETWEEN :start_date AND :end_date 
                 THEN oi.line_total ELSE 0 END)::numeric AS current_revenue,
        SUM(CASE WHEN o.order_date BETWEEN :prior_start AND :prior_end 
                 THEN oi.line_total ELSE 0 END)::numeric AS prior_revenue,
        CASE WHEN SUM(CASE WHEN o.order_date BETWEEN :prior_start AND :prior_end 
                           THEN oi.line_total ELSE 0 END) = 0 THEN 0
             ELSE ROUND(((SUM(CASE WHEN o.order_date BETWEEN :start_date AND :end_date 
                                    THEN oi.line_total ELSE 0 END) - 
                          SUM(CASE WHEN o.order_date BETWEEN :prior_start AND :prior_end 
                                   THEN oi.line_total ELSE 0 END)) / 
                         SUM(CASE WHEN o.order_date BETWEEN :prior_start AND :prior_end 
                                  THEN oi.line_total ELSE 0 END) * 100)::numeric, 2)
        END AS revenue_growth_pct
    FROM order_items oi
    JOIN orders o ON o.order_id = oi.order_id
    JOIN products p ON p.product_id = oi.product_id
    WHERE o.order_status = 'Completed'
      AND p.category_id = :category_id
      AND o.order_date BETWEEN :prior_start AND :end_date
      AND p.product_id IN ({product_placeholders})
    GROUP BY p.product_id, p.product_name, p.sku
    ORDER BY revenue_growth_pct DESC
"""

trending_data = run_query(trending_sql, params)

if not trending_data.empty:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📈 Top Gainers (Growing)")
        gainers = trending_data[trending_data['revenue_growth_pct'] > 0].head(5).copy()
        if not gainers.empty:
            for _, row in gainers.iterrows():
                growth = float(row['revenue_growth_pct']) if row['revenue_growth_pct'] else 0
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.markdown(f"**{row['product_name']}**  \n{row['sku']}")
                with col_b:
                    st.markdown(f"<span class='gainer'>+{growth:.1f}%</span>", unsafe_allow_html=True)
        else:
            st.info("No products with growth in this period.")
    
    with col2:
        st.markdown("#### 📉 Top Losers (Declining)")
        losers = trending_data[trending_data['revenue_growth_pct'] < 0].head(5).copy()
        if not losers.empty:
            for _, row in losers.iterrows():
                growth = float(row['revenue_growth_pct']) if row['revenue_growth_pct'] else 0
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.markdown(f"**{row['product_name']}**  \n{row['sku']}")
                with col_b:
                    st.markdown(f"<span class='loser'>{growth:.1f}%</span>", unsafe_allow_html=True)
        else:
            st.info("No products with decline in this period.")

st.markdown("---")

# ── Product Metrics Table ────────────────────────────────────
st.markdown('<p class="section-header">📊 Product Performance Metrics</p>', unsafe_allow_html=True)

product_metrics_sql = f"""
    SELECT
        p.product_name,
        p.sku,
        ROUND(SUM(oi.line_total)::numeric, 2)                      AS total_revenue,
        SUM(oi.quantity)                                            AS units_sold,
        ROUND(AVG(oi.line_total)::numeric, 2)                       AS avg_order_value,
        ROUND(SUM(p.cost_price * oi.quantity)::numeric, 2)          AS total_cost,
        ROUND(SUM(oi.line_total) - SUM(p.cost_price * oi.quantity)::numeric, 2) AS gross_profit,
        ROUND(((SUM(oi.line_total) - SUM(p.cost_price * oi.quantity)) / 
               SUM(oi.line_total) * 100)::numeric, 2)               AS profit_margin_pct,
        ROUND(AVG(oi.discount_pct)::numeric, 2)                     AS avg_discount_pct,
        COUNT(DISTINCT o.order_id)                                  AS times_ordered,
        ROUND(SUM(oi.quantity)::numeric / 
              (SELECT COUNT(DISTINCT DATE(order_date)) FROM orders 
               WHERE order_date BETWEEN :start_date AND :end_date AND order_status = 'Completed')::numeric, 2) AS velocity_per_day,
        ROUND(SUM(CASE WHEN o.order_status = 'Completed' THEN 1 ELSE 0 END)::numeric / 
              COUNT(*) * 100, 2)                                    AS completion_rate_pct
    FROM order_items oi
    JOIN orders o ON o.order_id = oi.order_id
    JOIN products p ON p.product_id = oi.product_id
    WHERE o.order_date BETWEEN :start_date AND :end_date
      AND p.category_id = :category_id
      AND p.product_id IN ({product_placeholders})
    GROUP BY p.product_id, p.product_name, p.sku
    ORDER BY total_revenue DESC
    LIMIT 50
"""

product_metrics = run_query(product_metrics_sql, params)

if not product_metrics.empty:
    display_df = product_metrics[[
        "product_name", "sku", "total_revenue", "units_sold", "gross_profit",
        "profit_margin_pct", "avg_discount_pct", "velocity_per_day", "completion_rate_pct"
    ]].copy()
    
    display_df.columns = ["Product", "SKU", "Revenue", "Units", "Profit", "Margin %", "Avg Discount %", "Velocity/Day", "Satisfaction %"]
    display_df["Revenue"] = display_df["Revenue"].astype(float).apply(lambda x: f"₹{x:,.0f}")
    display_df["Profit"] = display_df["Profit"].astype(float).apply(lambda x: f"₹{x:,.0f}")
    display_df["Margin %"] = display_df["Margin %"].astype(str) + "%"
    display_df["Avg Discount %"] = display_df["Avg Discount %"].astype(str) + "%"
    display_df["Satisfaction %"] = display_df["Satisfaction %"].astype(str) + "%"
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)

# ── Revenue vs Profit ────────────────────────────────────────
st.markdown("---")
st.markdown('<p class="section-header">💹 Revenue vs Profit Analysis</p>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    fig_rev = px.bar(
        product_metrics.head(10).sort_values("total_revenue"),
        x="total_revenue", y="product_name",
        orientation="h",
        labels={"total_revenue": "Revenue (₹)", "product_name": ""},
        title="Top 10 Products by Revenue",
        color="total_revenue",
        color_continuous_scale="Blues",
        text_auto=".0f",
    )
    fig_rev.update_layout(height=400, showlegend=False, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig_rev, use_container_width=True)

with col2:
    fig_profit = px.bar(
        product_metrics.head(10).sort_values("gross_profit"),
        x="gross_profit", y="product_name",
        orientation="h",
        labels={"gross_profit": "Profit (₹)", "product_name": ""},
        title="Top 10 Products by Profit",
        color="profit_margin_pct",
        color_continuous_scale="Greens",
        text_auto=".0f",
    )
    fig_profit.update_layout(height=400, showlegend=False, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig_profit, use_container_width=True)

# ── Discount Impact ──────────────────────────────────────────
st.markdown("---")
st.markdown('<p class="section-header">🏷️ Discount Impact Analysis</p>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    fig_discount = px.scatter(
        product_metrics,
        x="avg_discount_pct", y="profit_margin_pct",
        size="total_revenue", color="units_sold",
        hover_name="product_name",
        labels={
            "avg_discount_pct": "Avg Discount %",
            "profit_margin_pct": "Profit Margin %",
            "units_sold": "Units Sold"
        },
        title="Discount vs Margin (size=revenue)",
        color_continuous_scale="Viridis",
    )
    fig_discount.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig_discount, use_container_width=True)

with col2:
    fig_velocity = px.scatter(
        product_metrics,
        x="velocity_per_day", y="profit_margin_pct",
        size="total_revenue", color="completion_rate_pct",
        hover_name="product_name",
        labels={
            "velocity_per_day": "Velocity (units/day)",
            "profit_margin_pct": "Profit Margin %",
            "completion_rate_pct": "Satisfaction %"
        },
        title="Velocity vs Margin (color=satisfaction)",
        color_continuous_scale="RdYlGn",
    )
    fig_velocity.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig_velocity, use_container_width=True)

# ── Category Trends ──────────────────────────────────────────
st.markdown("---")
st.markdown('<p class="section-header">📈 Category Performance Over Time</p>', unsafe_allow_html=True)

category_trend_sql = f"""
    SELECT
        DATE_TRUNC('month', o.order_date)::date AS month,
        ROUND(SUM(oi.line_total)::numeric, 2) AS revenue,
        SUM(oi.quantity) AS units_sold,
        COUNT(DISTINCT o.order_id) AS orders
    FROM order_items oi
    JOIN orders o ON o.order_id = oi.order_id
    JOIN products p ON p.product_id = oi.product_id
    WHERE o.order_status = 'Completed'
      AND o.order_date BETWEEN :start_date AND :end_date
      AND p.category_id = :category_id
    GROUP BY 1
    ORDER BY 1
"""

category_trend = run_query(category_trend_sql, params)

if not category_trend.empty:
    category_trend["month"] = pd.to_datetime(category_trend["month"])
    
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=category_trend["month"], y=category_trend["revenue"],
        mode="lines+markers", name="Revenue",
        line=dict(color="#667eea", width=2.5), marker=dict(size=6),
        fill="tozeroy", fillcolor="rgba(102,126,234,0.1)",
    ))
    fig_trend.add_trace(go.Bar(
        x=category_trend["month"], y=category_trend["units_sold"],
        name="Units Sold", yaxis="y2",
        marker_color="rgba(118,75,162,0.3)",
    ))
    
    fig_trend.update_layout(
        xaxis_title="Month",
        yaxis=dict(
            title=dict(text="Revenue (₹)", font=dict(color="#667eea")),
            showgrid=False
        ),
        yaxis2=dict(
            title=dict(text="Units Sold", font=dict(color="#764ba2")),
            overlaying="y",
            side="right",
            showgrid=False
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=350,
        margin=dict(l=20, r=20, t=20, b=20),
        hovermode="x unified",
    )
    st.plotly_chart(fig_trend, use_container_width=True)

st.markdown("---")
st.caption("📦 Product Analytics Dashboard | Powered by Streamlit + PostgreSQL")
