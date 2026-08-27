import streamlit as st

st.set_page_config(
    page_title="RetailCo Dashboard",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🛒 RetailCo Dashboard")
st.markdown("Welcome to the Retail Chain Analytics Platform")
st.markdown("---")
st.info("👈 Select a page from the sidebar to get started!")

st.markdown("""
### Available Pages:
- **📊 Overview** — Main sales analytics dashboard with KPIs, trends, and AI assistant
- **🏪 Store Performance** — Compare stores, analyze profitability, and track efficiency metrics
- **📦 Product Analytics** — Track product trends, analyze SKU performance, and monitor profitability
""")