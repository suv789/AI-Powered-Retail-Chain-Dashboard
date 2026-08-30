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
            background: rgba(0, 0, 0, 0.35);
            z-index: 1;
        }}
        .main {{
            position: relative;
            z-index: 2;
        }}
        /* Header background container */
        .header-container {{
            background: rgba(20, 50, 70, 0.6);
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 20px;
            backdrop-filter: blur(10px);
            border-bottom: 3px solid #FFD700;
        }}
        .header-container h1 {{
            color: #FFFFFF;
            text-shadow: 2px 2px 8px rgba(0,0,0,0.7);
            font-weight: 700;
            margin: 0;
        }}
        .header-container p {{
            color: #D0D0D0;
            text-shadow: 2px 2px 6px rgba(0,0,0,0.6);
            margin: 10px 0 0 0;
            font-size: 16px;
        }}
        h1 {{
            color: #FFFFFF;
            text-shadow: 2px 2px 8px rgba(0,0,0,0.7);
            font-weight: 700;
        }}
        h2 {{
            color: #FFFFFF;
            text-shadow: 2px 2px 8px rgba(0,0,0,0.7);
            font-weight: 600;
        }}
        h3 {{
            color: #FFFFFF;
            text-shadow: 2px 2px 8px rgba(0,0,0,0.7);
            font-weight: 600;
        }}
        p {{
            color: #D0D0D0;
            text-shadow: 2px 2px 6px rgba(0,0,0,0.6);
        }}
        /* Info container styling */
        .info-container {{
            background: rgba(30, 60, 80, 0.5);
            padding: 25px;
            border-radius: 12px;
            margin: 20px 0;
            backdrop-filter: blur(8px);
            border-left: 4px solid #FFD700;
        }}
        .info-container h3 {{
            color: #FFFFFF;
            text-shadow: 2px 2px 8px rgba(0,0,0,0.7);
            margin-top: 0;
        }}
        .info-container ul {{
            color: #D0D0D0;
            text-shadow: 2px 2px 6px rgba(0,0,0,0.6);
        }}
        .info-container li {{
            margin: 12px 0;
            font-size: 15px;
            color: #D0D0D0;
            text-shadow: 2px 2px 6px rgba(0,0,0,0.6);
            line-height: 1.6;
        }}
        .info-container strong {{
            color: #FFD700;
            font-weight: 600;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

# Apply background
add_bg_from_local('images/retail-store.jpg')

# ── Content ───────────────────────────────────────────────────
st.markdown("""
<div class="header-container">
<h1>🛒 RetailCo Dashboard</h1>
<p>Welcome to the Retail Chain Analytics Platform</p>
</div>
""", unsafe_allow_html=True)

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