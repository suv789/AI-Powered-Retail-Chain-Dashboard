"""
dashboard.py
Main Streamlit dashboard for Retail Chain Sales Analytics.
Run with: python -m streamlit run app/dashboard.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
from dateutil.relativedelta import relativedelta

from app.queries import (
    get_kpi_summary, get_revenue_growth, get_monthly_revenue,
    get_top_products, get_category_revenue,
    get_regional_performance, get_store_performance,
    get_customer_segment_summary, get_rfm_data,
    get_regions, get_categories,  
)
from app.ai_assistant import (
    ask_gemini, generate_sql, run_generated_sql,
    suggest_chart_type, is_data_question, STARTER_QUESTIONS,
)

# ── Page Config ──────────────────────────────────────────────
st.set_page_config(
    page_title="Retail Chain Dashboard",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# st.markdown("""
# <style>
#     .section-header {
#         font-size: 1.1rem; font-weight: 600; color: #374151;
#         margin: 1.5rem 0 0.75rem 0;
#         border-left: 4px solid #667eea; padding-left: 10px;
#     }
#     .ai-result-box {
#         background: #f0f4ff; border: 1.5px solid #667eea;
#         border-radius: 12px; padding: 1rem 1.25rem; margin-bottom: 1.5rem;
#     }
#     .ai-result-title {
#         font-size: 0.85rem; color: #4338ca; font-weight: 600;
#         margin-bottom: 0.5rem;
#     }
#     .sql-box {
#         background: #1e1e2e; color: #cdd6f4; font-family: monospace;
#         font-size: 11px; padding: 8px 12px; border-radius: 8px;
#         margin-bottom: 8px; overflow-x: auto; white-space: pre-wrap;
#     }
#     /* KPI Card Styling */
#     [data-testid="metric-container"] {
#         background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
#         padding: 1rem 1.25rem !important;
#         border-radius: 12px !important;
#         border: 1px solid #e2e8f0 !important;
#         box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04) !important;
#     }
# </style>
# """, unsafe_allow_html=True)

# ── Session State ─────────────────────────────────────────────
# for key, default in [
#     ("chat_history", []),
#     ("chat_display", []),
#     ("dashboard_context", {}),
#     ("ai_result_df", None),
#     ("ai_result_sql", None),
#     ("ai_result_question", None),
#     ("ai_result_answer", None),
# ]:
#     if key not in st.session_state:
#         st.session_state[key] = default
for key, default in [
    ("chat_history", []),
    ("chat_display", []),
    ("dashboard_context", {}),
    ("ai_result_df", None),
    ("ai_result_sql", None),
    ("ai_result_question", None),
    ("ai_result_answer", None),
    
]:
    if key not in st.session_state:
        st.session_state[key] = default

if "reset_counter" not in st.session_state:
    st.session_state.reset_counter = 0

# Apply reset if triggered
# if st.session_state.get("reset_filters"):
#     st.session_state["reset_filters"] = False
#     default_end   = date.today()
#     default_start = default_end - relativedelta(months=6)

# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🛒 RetailCo")
    tab_filters, tab_ai = st.tabs(["🔍 Filters", "🤖 AI Assistant"])

    # ── Filters tab ──────────────────────────────────────────
    with tab_filters:
        st.markdown("#### Date Range")
        
        default_end   = date.today()
        default_start = default_end - relativedelta(months=6)
        start_date = st.date_input("Start Date", value=default_start, key=f"start_date_input_{st.session_state.reset_counter}")
        end_date   = st.date_input("End Date",   value=default_end, key=f"end_date_input_{st.session_state.reset_counter}")

        
        if start_date >= end_date:
            st.error("Start date must be before end date.")
            st.stop()

        ## st.markdown("#### Region")
        regions_df = get_regions()
        region_options = {"All Regions": None}
        region_options.update(dict(zip(regions_df["region_name"], regions_df["region_id"])))
        selected_region_label = st.selectbox("Region", list(region_options.keys()), key=f"region_select_{st.session_state.reset_counter}")
        region_id = region_options[selected_region_label]

        
        ## st.markdown("#### Category")
        categories_df = get_categories()
        category_options = {"All Categories": None}
        category_options.update(dict(zip(categories_df["category_name"], categories_df["category_id"])))
        selected_category_label = st.selectbox("Category", list(category_options.keys()), key=f"category_select_{st.session_state.reset_counter}")
        category_id = category_options[selected_category_label]

       
        st.markdown("---")
        st.caption(f"📅 {start_date} → {end_date}")
        st.caption(f"🗺️ {selected_region_label}")
        st.caption(f"📦 {selected_category_label}")

        # if st.button("🔄 Reset Filters", use_container_width=True):
        #     # Clear widget keys from session state so they reset to defaults
        #     if "start_date_input" in st.session_state:
        #         del st.session_state["start_date_input"]
        #     if "end_date_input" in st.session_state:
        #         del st.session_state["end_date_input"]
        #     if "region_select" in st.session_state:
        #         del st.session_state["region_select"]
        #     if "category_select" in st.session_state:  
        #         del st.session_state["category_select"]
        #     st.rerun()
        # if st.button("🔄 Reset Filters", use_container_width=True):
        #     if "start_date_input" in st.session_state:
        #         del st.session_state["start_date_input"]
        #     if "end_date_input" in st.session_state:
        #         del st.session_state["end_date_input"]
        #     if "region_select" in st.session_state:
        #         del st.session_state["region_select"]
        #     if "category_select" in st.session_state:
        #         del st.session_state["category_select"]
        #     st.rerun()
        if st.button("🔄 Reset Filters", use_container_width=True):
            st.session_state.reset_counter += 1
            st.rerun()

    # ── AI Assistant tab ──────────────────────────────────────
    with tab_ai:
        st.markdown("#### Ask your data")
        st.caption("Powered by Gemini · data questions auto-generate charts")

        # Chat history display
        chat_container = st.container(height=300)
        with chat_container:
            if not st.session_state.chat_display:
                st.info("👋 Ask a question or pick a starter below.")
            for msg in st.session_state.chat_display:
                if msg["role"] == "user":
                    st.markdown(f"**You:** {msg['content']}")
                else:
                    st.markdown(f"**AI:** {msg['content']}")
                st.markdown("---")

        # Input form
        with st.form("chat_form", clear_on_submit=True):
            user_input = st.text_area(
                "Your question",
                placeholder="e.g. Show me revenue by region",
                label_visibility="collapsed",
                height=80,
            )
            submitted = st.form_submit_button("Send ↗", use_container_width=True)

        def handle_question(question: str):
            """Core logic: decide whether to generate SQL+chart or just chat."""
            if is_data_question(question):
                # ── Data question: generate SQL → run → store result ──
                with st.spinner("Generating query..."):
                    try:
                        sql  = generate_sql(question)
                        df   = run_generated_sql(sql)
                        # Also get a plain-English summary
                        summary = ask_gemini(
                            f"In 2 sentences, summarise this result for the question '{question}': {df.head(5).to_string()}",
                            [],
                            st.session_state.dashboard_context,
                        )
                        st.session_state.ai_result_df       = df
                        st.session_state.ai_result_sql      = sql
                        st.session_state.ai_result_question = question
                        st.session_state.ai_result_answer   = summary
                        answer_for_chat = f"📊 Data result ready — scroll up on the dashboard to see the chart & table.\n\n{summary}"
                    except Exception as e:
                        answer_for_chat = f"⚠️ Could not generate query: {e}"
                        st.session_state.ai_result_df = None
            else:
                # ── Conversational question ───────────────────────────
                with st.spinner("Thinking..."):
                    answer_for_chat = ask_gemini(
                        question,
                        st.session_state.chat_history,
                        st.session_state.dashboard_context,
                    )

            st.session_state.chat_history.append({"role": "user",  "parts": [question]})
            st.session_state.chat_history.append({"role": "model", "parts": [answer_for_chat]})
            st.session_state.chat_display.append({"role": "user",  "content": question})
            st.session_state.chat_display.append({"role": "ai",    "content": answer_for_chat})
            st.rerun()

        if submitted and user_input.strip():
            handle_question(user_input.strip())

        # Starter question buttons
        st.markdown("**Suggested:**")
        for q in STARTER_QUESTIONS[:5]:
            if st.button(q, key=f"sq_{q}", use_container_width=True):
                handle_question(q)

        if st.session_state.chat_display:
            if st.button("🗑️ Clear chat", use_container_width=True):
                st.session_state.chat_history        = []
                st.session_state.chat_display        = []
                st.session_state.ai_result_df        = None
                st.session_state.ai_result_sql       = None
                st.session_state.ai_result_question  = None
                st.session_state.ai_result_answer    = None
                st.rerun()


# ── Main Dashboard ────────────────────────────────────────────
st.title("🛒 Retail Chain — Sales Analytics Dashboard")
st.markdown(
    f"**Period:** {start_date.strftime('%d %b %Y')} → {end_date.strftime('%d %b %Y')}"
    f" &nbsp;|&nbsp; **Region:** {selected_region_label}"
)
st.markdown("---")

# ── AI Result Panel (shown at top when available) ─────────────
if st.session_state.ai_result_df is not None:
    df_result = st.session_state.ai_result_df
    question  = st.session_state.ai_result_question
    sql       = st.session_state.ai_result_sql
    answer    = st.session_state.ai_result_answer

    st.markdown('<p class="section-header">🤖 AI Query Result</p>', unsafe_allow_html=True)

    with st.container():
        st.markdown(f"**Question:** {question}")
        if answer:
            st.info(answer)

        # Show SQL in expander
        with st.expander("🔍 View generated SQL"):
            st.code(sql, language="sql")

        if not df_result.empty:
            num_cols = df_result.select_dtypes(include="number").columns.tolist()
            cat_cols = df_result.select_dtypes(exclude="number").columns.tolist()
            date_cols = [c for c in df_result.columns if "date" in c.lower() or "month" in c.lower()]

            chart_type = suggest_chart_type(df_result)

            col_chart, col_table = st.columns([1.4, 1])

            with col_chart:
                try:
                    if chart_type == "line" and date_cols and num_cols:
                        fig = px.line(
                            df_result, x=date_cols[0], y=num_cols[0],
                            title=question, markers=True,
                            color_discrete_sequence=["#667eea"],
                        )
                    elif chart_type == "bar" and cat_cols and num_cols:
                        fig = px.bar(
                            df_result.sort_values(num_cols[0], ascending=False),
                            x=cat_cols[0], y=num_cols[0],
                            title=question,
                            color=num_cols[0],
                            color_continuous_scale="Blues",
                            text_auto=True,
                        )
                        if len(df_result) > 6:
                            fig = px.bar(
                                df_result.sort_values(num_cols[0]),
                                x=num_cols[0], y=cat_cols[0],
                                orientation="h", title=question,
                                color=num_cols[0],
                                color_continuous_scale="Blues",
                                text_auto=True,
                            )
                    elif chart_type == "scatter" and len(num_cols) >= 2:
                        fig = px.scatter(
                            df_result, x=num_cols[0], y=num_cols[1],
                            title=question,
                            color_discrete_sequence=["#667eea"],
                        )
                    else:
                        fig = px.bar(
                            df_result, x=df_result.columns[0], y=num_cols[0] if num_cols else df_result.columns[1],
                            title=question,
                            color_discrete_sequence=["#667eea"],
                        )

                    fig.update_layout(
                        height=350, margin=dict(l=20, r=20, t=40, b=20),
                        coloraxis_showscale=False,
                    )
                    st.plotly_chart(fig, use_container_width=True)
                except Exception:
                    st.warning("Could not render chart for this result.")

            with col_table:
                st.markdown("**Data Table**")
                st.dataframe(df_result, use_container_width=True, hide_index=True, height=320)
        else:
            st.warning("Query returned no results.")

    st.markdown("---")


# ── KPI Cards ────────────────────────────────────────────────
st.markdown('<p class="section-header">📊 Key Performance Indicators</p>', unsafe_allow_html=True)

kpi_df    = get_kpi_summary(start_date, end_date, region_id, category_id)
growth_df = get_revenue_growth(start_date, end_date, region_id, category_id)

if not kpi_df.empty:
    row = kpi_df.iloc[0]
    g   = growth_df.iloc[0]

    curr_rev   = float(g["current_revenue"] or 0)
    prior_rev  = float(g["prior_revenue"] or 1)
    growth_pct = ((curr_rev - prior_rev) / prior_rev * 100) if prior_rev else 0

    total_revenue    = float(row["total_revenue"])
    total_orders     = int(row["total_orders"])
    unique_customers = int(row["unique_customers"])
    avg_order_value  = float(row["avg_order_value"])

    # col1, col2, col3, col4 = st.columns(4)
    # with col1:
    #     st.metric("💰 Total Revenue", f"₹{total_revenue:,.0f}", f"{growth_pct:+.1f}% vs prior period")
    # with col2:
    #     st.metric("🧾 Total Orders", f"{total_orders:,}")
    # with col3:
    #     st.metric("👥 Unique Customers", f"{unique_customers:,}")
    # with col4:
    #     st.metric("🛍️ Avg Order Value", f"₹{avg_order_value:,.2f}")
        # Add custom CSS for metric cards
        # Add custom CSS for metric cards
    st.markdown("""
    <style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 0.5rem;
        min-height: 150px;
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
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">💰 Total Revenue</div>
            <div class="metric-value">₹{total_revenue:,.0f}</div>
            <div class="metric-delta">{growth_pct:+.1f}% vs prior</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">🧾 Total Orders</div>
            <div class="metric-value">{total_orders:,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">👥 Unique Customers</div>
            <div class="metric-value">{unique_customers:,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">🛍️ Avg Order Value</div>
            <div class="metric-value">₹{avg_order_value:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)

    # Update AI dashboard context
    regional_df = get_regional_performance(start_date, end_date, category_id)
    top_prod_df = get_top_products(start_date, end_date, region_id, category_id ,limit=5)
    segment_df  = get_customer_segment_summary(start_date, end_date, category_id)

    st.session_state.dashboard_context = {
        "period": f"{start_date} to {end_date}",
        "region_filter": selected_region_label,
        "kpis": {
            "total_revenue_inr": round(total_revenue, 2),
            "total_orders": total_orders,
            "unique_customers": unique_customers,
            "avg_order_value_inr": round(avg_order_value, 2),
            "revenue_growth_pct": round(growth_pct, 2),
        },
        "top_5_products": top_prod_df[["product_name","category_name","units_sold","revenue"]].to_dict("records") if not top_prod_df.empty else [],
        "regional_performance": regional_df[["region_name","total_orders","unique_customers","revenue"]].to_dict("records") if not regional_df.empty else [],
        "customer_segments": segment_df[["customer_segment","num_customers","total_revenue","avg_spend_per_customer"]].to_dict("records") if not segment_df.empty else [],
    }
else:
    st.warning("No data found for the selected filters.")
    st.stop()

st.markdown("---")


# ── Revenue Trend ────────────────────────────────────────────
st.markdown('<p class="section-header">📈 Monthly Revenue Trend</p>', unsafe_allow_html=True)

trend_df = get_monthly_revenue(start_date, end_date, region_id,category_id)
if not trend_df.empty:
    trend_df["month"]       = pd.to_datetime(trend_df["month"])
    trend_df["revenue_lak"] = trend_df["revenue"].astype(float) / 1e5

    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=trend_df["month"], y=trend_df["revenue_lak"],
        mode="lines+markers", name="Revenue (₹ Lakhs)",
        line=dict(color="#667eea", width=2.5), marker=dict(size=6),
        fill="tozeroy", fillcolor="rgba(102,126,234,0.1)",
    ))
    fig_trend.add_trace(go.Bar(
        x=trend_df["month"], y=trend_df["orders"],
        name="Orders", yaxis="y2",
        marker_color="rgba(118,75,162,0.3)",
    ))
    fig_trend.update_layout(
        xaxis_title="Month",
        yaxis=dict(
            title=dict(text="Revenue (₹ Lakhs)", font=dict(color="#667eea"))
        ),
        yaxis2=dict(
            title=dict(text="Orders", font=dict(color="#764ba2")),
            overlaying="y",
            side="right",
            showgrid=False
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=380,
        margin=dict(l=20, r=20, t=20, b=20),
        hovermode="x unified",
    )
    st.plotly_chart(fig_trend, use_container_width=True)


# ── Products & Categories ─────────────────────────────────────
st.markdown('<p class="section-header">🏷️ Top Products & Categories</p>', unsafe_allow_html=True)

col_left, col_right = st.columns([1.2, 1])

with col_left:
    top_n = st.slider("Show top N products", min_value=5, max_value=20, value=10, step=5)
    top_products_df = get_top_products(start_date, end_date, region_id,category_id, limit=top_n)
    if not top_products_df.empty:
        top_products_df["revenue_k"] = top_products_df["revenue"].astype(float) / 1000
        fig_prod = px.bar(
            top_products_df.sort_values("revenue_k"),
            x="revenue_k", y="product_name", orientation="h",
            color="category_name",
            labels={"revenue_k": "Revenue (₹ '000)", "product_name": "", "category_name": "Category"},
            title=f"Top {top_n} Products by Revenue",
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        fig_prod.update_layout(height=420, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_prod, use_container_width=True)

with col_right:
    cat_df = get_category_revenue(start_date, end_date, region_id, category_id)
    if not cat_df.empty:
        fig_cat = px.pie(
            cat_df, values="revenue", names="category_name",
            title="Revenue Share by Category", hole=0.45,
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        fig_cat.update_traces(textposition="inside", textinfo="percent+label")
        fig_cat.update_layout(height=420, margin=dict(l=20, r=20, t=40, b=20), showlegend=False)
        st.plotly_chart(fig_cat, use_container_width=True)


# ── Regional Performance ──────────────────────────────────────
st.markdown("---")
st.markdown('<p class="section-header">🗺️ Regional Performance</p>', unsafe_allow_html=True)

col_r1, col_r2 = st.columns(2)

with col_r1:
    if not regional_df.empty:
        regional_df["revenue_l"] = regional_df["revenue"].astype(float) / 1e5
        fig_region = px.bar(
            regional_df, x="region_name", y="revenue_l", color="region_name",
            labels={"revenue_l": "Revenue (₹ Lakhs)", "region_name": "Region"},
            title="Revenue by Region", text_auto=".1f",
            color_discrete_sequence=px.colors.qualitative.Safe,
        )
        fig_region.update_layout(height=350, showlegend=False, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_region, use_container_width=True)

with col_r2:
    store_df = get_store_performance(start_date, end_date, region_id, category_id)
    if not store_df.empty:
        fig_store = px.scatter(
            store_df, x="total_orders", y="revenue",
            size="revenue", color="region_name", hover_name="store_name",
            labels={"total_orders": "Total Orders", "revenue": "Revenue (₹)", "region_name": "Region"},
            title="Store Performance: Orders vs Revenue",
            color_discrete_sequence=px.colors.qualitative.Safe,
        )
        fig_store.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_store, use_container_width=True)

with st.expander("📋 Store-level Revenue Table"):
    if not store_df.empty:
        display_df = store_df[["store_name","region_name","city","store_size","total_orders","revenue"]].copy()
        display_df["revenue"] = display_df["revenue"].astype(float).apply(lambda x: f"₹{x:,.0f}")
        display_df.columns = ["Store","Region","City","Size","Orders","Revenue"]
        st.dataframe(display_df, use_container_width=True, hide_index=True)


# ── Customer Segmentation ─────────────────────────────────────
st.markdown("---")
st.markdown('<p class="section-header">👥 Customer Segmentation</p>', unsafe_allow_html=True)

col_s1, col_s2 = st.columns(2)

if not segment_df.empty:
    with col_s1:
        fig_seg = px.bar(
            segment_df, x="customer_segment", y="total_revenue", color="customer_segment",
            labels={"total_revenue": "Revenue (₹)", "customer_segment": "Segment"},
            title="Revenue by Customer Segment",
            color_discrete_map={
                "Bronze":"#CD7F32","Silver":"#C0C0C0",
                "Gold":"#FFD700","Platinum":"#E5E4E2"
            },
            text_auto=True,
        )
        fig_seg.update_layout(height=350, showlegend=False, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_seg, use_container_width=True)

    with col_s2:
        fig_bubble = px.scatter(
            segment_df,
            x="num_customers", y="avg_spend_per_customer",
            size="total_revenue", color="customer_segment",
            hover_name="customer_segment",
            labels={
                "num_customers": "Number of Customers",
                "avg_spend_per_customer": "Avg Spend per Customer (₹)",
                "customer_segment": "Segment",
            },
            title="Segment: Customers vs Avg Spend",
            color_discrete_map={
                "Bronze":"#CD7F32","Silver":"#C0C0C0",
                "Gold":"#FFD700","Platinum":"#E5E4E2"
            },
        )
        fig_bubble.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_bubble, use_container_width=True)

with st.expander("🔬 Top Customers by Monetary Value"):
    rfm_df = get_rfm_data(start_date, end_date, category_id)
    if not rfm_df.empty:
        rfm_df["monetary"] = rfm_df["monetary"].astype(float).apply(lambda x: f"₹{x:,.0f}")
        rfm_df.columns = ["ID","Name","Segment","Last Order","Frequency","Monetary"]
        st.dataframe(rfm_df.head(20), use_container_width=True, hide_index=True)


# ── Footer ───────────────────────────────────────────────────
st.markdown("---")
st.caption("🛒 Retail Chain Dashboard · Streamlit + PostgreSQL + Plotly + Gemini AI")
