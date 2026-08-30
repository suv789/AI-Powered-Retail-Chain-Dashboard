import streamlit as st
from PIL import Image
import base64

# ── Page Config ──────────────────────────────────────────────
st.set_page_config(
    page_title="RetailCo Dashboard",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Add Background Image ──────────────────────────────────────
def add_bg_from_local(image_file):
    with open(image_file, "rb") as img_file:
        encoded_string = base64.b64encode(img_file.read())
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url(data:image/jpg;base64,{encoded_string.decode()});
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        .stApp::before {{
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            z-index: 1;
        }}
        .main {{
            position: relative;
            z-index: 2;
        }}
        h1 {{
            color: #00D9FF;
            text-shadow: 2px 2px 8px rgba(0,0,0,0.5);
        }}
        h2 {{
            color: #00D9FF;
            text-shadow: 2px 2px 8px rgba(0,0,0,0.5);
        }}
        h3 {{
            color: #00D9FF;
            text-shadow: 2px 2px 8px rgba(0,0,0,0.5);
        }}
        p {{
            color: #FFFFFF;
            text-shadow: 2px 2px 8px rgba(0,0,0,0.5);
        }}
        /* Info container styling */
        .info-container {{
            background: rgba(30, 100, 150, 0.4);
            padding: 20px;
            border-radius: 10px;
            margin: 15px 0;
            backdrop-filter: blur(5px);
        }}
        .info-container h3 {{
            color: #00D9FF;
            text-shadow: 2px 2px 8px rgba(0,0,0,0.9);
        }}
        .info-container ul {{
            color: #FFFFFF;
            text-shadow: 2px 2px 8px rgba(0,0,0,0.9);
        }}
        .info-container li {{
            margin: 10px 0;
            font-size: 16px;
            color: #FFFFFF;
        }}
        .info-container strong {{
            color: #00D9FF;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

# Apply background
add_bg_from_local('images/retail-store.jpg')

# ── Content ───────────────────────────────────────────────────
st.title("🛒 RetailCo Dashboard")
st.markdown("Welcome to the Retail Chain Analytics Platform")
st.markdown("---")
st.info("👈 Select a page from the sidebar to get started!")

# ── Available Pages Section with styling ──────────────────────
st.markdown("""
<div class="info-container">
<h3>Available Pages:</h3>

- <strong>📊 Overview</strong> — Main sales analytics dashboard with KPIs, trends, and AI assistant
- <strong>🏪 Store Performance</strong> — Compare stores, analyze profitability, and track efficiency metrics
- <strong>📦 Product Analytics</strong> — Track product trends, analyze SKU performance, and monitor profitability
</div>
""", unsafe_allow_html=True)

st.markdown("---")
# st.markdown("""
# ### 🚀 [Open the Dashboard →](https://ai-powered-retail-chain-dashboard-42kxp5uelufvsiuf9g8zlj.streamlit.app/)
# """)