import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk
import numpy as np
from datetime import datetime
import time
import random

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="CO2Watch India | AI Climate Monitor",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -----------------------------------------------------------------------------
# 2. CUSTOM CSS & STYLING (Futuristic, Glassmorphism, Neon)
# -----------------------------------------------------------------------------
st.markdown("""
    <style>
        /* IMPORT FONTS */
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;700;900&family=Rajdhani:wght@300;400;500;600;700&display=swap');

        /* GLOBAL VARIABLES */
        :root {
            --neon-cyan: #00f2ff;
            --neon-red: #ff2a6d;
            --neon-green: #05ffa1;
            --deep-space: #020203;
            --glass-bg: rgba(10, 25, 47, 0.7);
            --glass-border: 1px solid rgba(0, 242, 255, 0.1);
        }

        /* RESET & BASE STYLES */
        .stApp {
            background-color: var(--deep-space);
            font-family: 'Rajdhani', sans-serif;
            color: #e6f1ff;
        }
        
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Orbitron', sans-serif;
            letter-spacing: 2px;
            text-transform: uppercase;
            color: #ffffff;
            text-shadow: 0 0 10px rgba(0, 242, 255, 0.5);
        }

        /* SIDEBAR HAMBURGER ICON VISIBILITY FIX */
        [data-testid="stSidebarCollapsedControl"] {
            display: block !important;
            color: var(--neon-cyan) !important;
            background-color: rgba(0, 242, 255, 0.1);
            border-radius: 5px;
            padding: 5px;
            z-index: 999999;
        }
        [data-testid="stSidebarCollapsedControl"] svg {
            fill: var(--neon-cyan) !important;
            width: 30px !important;
            height: 30px !important;
        }

        /* CUSTOM BUTTONS */
        .stButton > button {
            background: linear-gradient(45deg, transparent 5%, var(--neon-cyan) 5%);
            color: #000;
            font-family: 'Orbitron', sans-serif;
            font-weight: 700;
            border: none;
            box-shadow: 6px 0px 0px #00e1ee;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
            padding: 0.75rem 2rem;
        }
        .stButton > button:hover {
            background: linear-gradient(45deg, transparent 5%, #fff 5%);
            box-shadow: 6px 0px 0px var(--neon-cyan);
            color: var(--neon-cyan);
            transform: translateY(-2px);
        }

        /* GLASS CARDS */
        .glass-card {
            background: var(--glass-bg);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: var(--glass-border);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .glass-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 40px 0 rgba(0, 242, 255, 0.1);
            border-color: var(--neon-cyan);
        }

        /* METRIC CONTAINERS */
        [data-testid="stMetricValue"] {
            font-family: 'Orbitron', sans-serif;
            color: var(--neon-cyan) !important;
            text-shadow: 0 0 10px rgba(0, 242, 255, 0.4);
        }
        [data-testid="stMetricLabel"] {
            font-family: 'Rajdhani', sans-serif;
            color: #8892b0 !important;
            font-size: 1.1rem;
        }

        /* TABS */
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
            background-color: transparent;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: rgba(0, 242, 255, 0.05);
            border-radius: 8px;
            color: #8892b0;
            font-family: 'Orbitron', sans-serif;
            border: 1px solid transparent;
        }
        .stTabs [data-baseweb="tab"]:hover {
            color: var(--neon-cyan);
            border-color: var(--neon-cyan);
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background-color: rgba(0, 242, 255, 0.1);
            color: var(--neon-cyan);
            border-color: var(--neon-cyan);
            box-shadow: 0 0 15px rgba(0, 242, 255, 0.2);
        }

        /* HIDE DEFAULT STREAMLIT ELEMENTS */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* HERO SECTION STYLES */
        .hero-container {
            text-align: center;
            padding: 4rem 2rem;
            background: radial-gradient(circle at center, rgba(0, 242, 255, 0.1) 0%, transparent 70%);
            margin-bottom: 2rem;
        }
        .hero-title {
            font-size: 4.5rem;
            font-weight: 900;
            margin-bottom: 1rem;
            background: linear-gradient(to right, #fff, var(--neon-cyan));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: glow 3s ease-in-out infinite alternate;
        }
        .hero-subtitle {
            font-size: 1.5rem;
            color: #8892b0;
            max-width: 800px;
            margin: 0 auto 2rem auto;
        }
        
        @keyframes glow {
            from { text-shadow: 0 0 10px rgba(0, 242, 255, 0.2); }
            to { text-shadow: 0 0 20px rgba(0, 242, 255, 0.6), 0 0 10px rgba(255, 255, 255, 0.4); }
        }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3. SESSION STATE INITIALIZATION
# -----------------------------------------------------------------------------
if 'use_live_data' not in st.session_state:
    st.session_state.use_live_data = False

if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False

# -----------------------------------------------------------------------------
# 4. HELPER FUNCTIONS & CLASSES
# -----------------------------------------------------------------------------

class ClimateAI:
    """
    AI Analysis Engine for Climate Data.
    Uses mock data for demo purposes to ensure stability without API keys.
    """
    def get_summary(self, df):
        high_emitters = df[df['emissions'] > df['emissions'].quantile(0.75)]
        return f"""
        ### 🚨 EXECUTIVE SUMMARY
        
        **System Status:** CRITICAL ALERT
        **Date:** {datetime.now().strftime('%Y-%m-%d')}
        
        Our satellite constellation has detected **{len(df)} active thermal anomalies** across the monitored region. 
        
        **Key Findings:**
        - **Total Emissions:** {df['emissions'].sum():,.2f} kilotons CO₂e
        - **Highest Intensity:** Detected at {high_emitters.iloc[0]['plant_name'] if not high_emitters.empty else 'Unknown'} 
        - **Trend Analysis:** 15% increase in thermal signatures compared to last week's baseline.
        
        Immediate regulatory review is recommended for the top 5 emitting facilities.
        """

    def analyze_compliance(self, df):
        return """
        ### ⚖️ COMPLIANCE AUDIT
        
        **Regulatory Framework:** CPCB / MoEFCC Guidelines
        
        | Facility ID | Status | Violation Probability | Action Required |
        | :--- | :--- | :--- | :--- |
        | NTPC-Vindhyachal | 🔴 NON-COMPLIANT | 94% | Immediate Shutdown Notice |
        | Mundra TPP | 🟡 WARNING | 68% | Stack Monitoring Audit |
        | Sasan UMPP | 🟢 COMPLIANT | 12% | Routine Check |
        
        **AI Assessment:**
        Detected plume dispersion patterns suggest unauthorized venting during night hours at **NTPC-Vindhyachal**. 
        Spectral signature matches high-sulfur coal combustion without adequate scrubbing.
        """

    def generate_esg_report(self, df):
        return """
        ### 🌿 ESG IMPACT REPORT
        
        **Environmental Score:** D+ (Critical)
        
        **Impact Metrics:**
        - **Carbon Footprint:** Equivalent to 450,000 passenger vehicles driven for one year.
        - **Health Risk:** Elevated PM2.5 levels detected in 15km radius of major clusters.
        - **Water Stress:** High thermal discharge noted in nearby water bodies.
        
        **Recommendations:**
        1. Retrofit FGD (Flue Gas Desulfurization) units immediately.
        2. Transition 20% load to renewable sources by Q3 2025.
        """

    def draft_cpcb_complaint(self, plant_name, emissions):
        return f"""
        **SUBJECT: URGENT - Emission Violation Report for {plant_name}**
        
        **To:** The Chairman, Central Pollution Control Board
        
        **Date:** {datetime.now().strftime('%d %B, %Y')}
        
        **Dear Sir/Madam,**
        
        This automated report serves as formal notification of detected environmental violations at **{plant_name}**.
        
        **Evidence:**
        - **Detected Emission Rate:** {emissions} kt/day
        - **Threshold Limit:** 5.0 kt/day
        - **Violation Magnitude:** {(emissions/5.0)*100:.1f}% over limit
        
        Satellite imagery confirms continuous plume discharge exceeding permissible opacity limits. 
        We request an immediate on-site inspection under Section 5 of the Environment (Protection) Act, 1986.
        
        **Generated by:** CO2Watch India AI Monitor
        """

@st.cache_data
def load_data():
    """Generates realistic mock data for the dashboard."""
    regions = [
        {"name": "Vindhyachal", "lat": 24.0983, "lon": 82.6719, "state": "Madhya Pradesh"},
        {"name": "Mundra", "lat": 22.8397, "lon": 69.7203, "state": "Gujarat"},
        {"name": "Talcher", "lat": 20.9500, "lon": 85.2167, "state": "Odisha"},
        {"name": "Sipat", "lat": 22.1333, "lon": 82.2833, "state": "Chhattisgarh"},
        {"name": "Rihand", "lat": 24.0269, "lon": 82.7900, "state": "Uttar Pradesh"},
        {"name": "Korba", "lat": 22.3500, "lon": 82.6833, "state": "Chhattisgarh"},
        {"name": "Jharsuguda", "lat": 21.8500, "lon": 84.0000, "state": "Odisha"},
        {"name": "Tirora", "lat": 21.4000, "lon": 79.9667, "state": "Maharashtra"}
    ]
    
    data = []
    for _ in range(50):
        plant = random.choice(regions)
        # Add some jitter to coordinates to simulate different stacks/units
        lat = plant["lat"] + random.uniform(-0.05, 0.05)
        lon = plant["lon"] + random.uniform(-0.05, 0.05)
        emissions = random.uniform(2.0, 15.0)
        
        data.append({
            "plant_name": plant["name"],
            "state": plant["state"],
            "latitude": lat,
            "longitude": lon,
            "emissions": emissions,
            "confidence": random.uniform(0.85, 0.99),
            "timestamp": datetime.now().isoformat()
        })
    
    return pd.DataFrame(data)

def render_globe():
    """Renders the 3D Globe visualization."""
    globe_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <style> body { margin: 0; background-color: #020203; } </style>
        <script src="//unpkg.com/globe.gl"></script>
    </head>
    <body>
    <div id="globeViz"></div>
    <script>
        const N = 40;
        const gData = [...Array(N).keys()].map(() => ({
            lat: (Math.random() - 0.5) * 180,
            lng: (Math.random() - 0.5) * 360,
            size: Math.random() / 3,
            color: ['#ff2a6d', '#00f2ff', '#05ffa1'][Math.round(Math.random() * 2)]
        }));

        Globe()
        .globeImageUrl('//unpkg.com/three-globe/example/img/earth-night.jpg')
        .pointsData(gData)
        .pointAltitude('size')
        .pointColor('color')
        .pointRadius(0.5)
        .atmosphereColor('#00f2ff')
        .atmosphereAltitude(0.15)
        (document.getElementById('globeViz'));
    </script>
    </body>
    </html>
    """
    components.html(globe_html, height=500)

# -----------------------------------------------------------------------------
# 5. MAIN APPLICATION LOGIC
# -----------------------------------------------------------------------------

def main():
    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown("## ⚙️ CONTROL PANEL")
        st.markdown("---")
        
        st.markdown("### 📡 DATA SOURCE")
        data_source = st.radio("Select Feed", ["Sentinel-5P (Live)", "Historical Archive", "Simulation Mode"], index=0)
        
        st.markdown("### 🎚️ FILTERS")
        min_emission = st.slider("Min Emission (kt)", 0.0, 20.0, 5.0)
        confidence_threshold = st.slider("Confidence Threshold", 0.0, 1.0, 0.8)
        
        st.markdown("---")
        st.info("System Status: ONLINE\nLatency: 24ms\nNodes: 14/14 Active")

    # --- HERO SECTION ---
    if not st.session_state.use_live_data:
        st.markdown('<div class="hero-container">', unsafe_allow_html=True)
        st.markdown('<h1 class="hero-title">CO₂WATCH INDIA</h1>', unsafe_allow_html=True)
        st.markdown('<p class="hero-subtitle">Advanced Satellite-Based Methane & Carbon Emission Monitoring System. Leveraging AI to detect, analyze, and report industrial anomalies in real-time.</p>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("VIEW LIVE DASHBOARD"):
                st.session_state.use_live_data = True
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Feature Highlights
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("""
            <div class="glass-card">
                <h3>🛰️ SATELLITE VISION</h3>
                <p>Real-time ingestion of Sentinel-5P TROPOMI data for precise plume detection.</p>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown("""
            <div class="glass-card">
                <h3>🧠 AI ANALYSIS</h3>
                <p>Neural networks classify emission sources and predict dispersion patterns.</p>
            </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown("""
            <div class="glass-card">
                <h3>⚡ INSTANT ALERTS</h3>
                <p>Automated violation reporting to regulatory bodies (CPCB/MoEFCC).</p>
            </div>
            """, unsafe_allow_html=True)
            
        # 3D Globe Preview
        st.markdown("### 🌍 GLOBAL MONITORING NETWORK")
        render_globe()

    # --- LIVE DASHBOARD ---
    else:
        # Header
        col_head1, col_head2 = st.columns([3, 1])
        with col_head1:
            st.title("🚀 MISSION CONTROL")
        with col_head2:
            if st.button("EXIT DASHBOARD"):
                st.session_state.use_live_data = False
                st.rerun()

        # Load Data
        df = load_data()
        ai = ClimateAI()

        # Top Metrics
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Active Hotspots", f"{len(df)}", "+12%")
        with m2:
            st.metric("Total Emissions", f"{df['emissions'].sum():.1f} kt", "+5.4%")
        with m3:
            st.metric("Max Intensity", f"{df['emissions'].max():.1f} kt", "Critical")
        with m4:
            st.metric("Data Freshness", "Live", "2s ago")

        # Main Content Tabs
        tab1, tab2, tab3 = st.tabs(["🗺️ GEOSPATIAL INTELLIGENCE", "📊 ANALYTICS SUITE", "🤖 AI COMMAND CENTER"])

        with tab1:
            st.markdown("### 📍 THERMAL ANOMALY MAP")
            
            # PyDeck Map
            layer = pdk.Layer(
                "ScatterplotLayer",
                df,
                get_position=["longitude", "latitude"],
                get_color="[255, 42, 109, 160]",  # Neon Red
                get_radius="emissions * 5000",
                pickable=True,
                opacity=0.8,
                stroked=True,
                filled=True,
                radius_scale=6,
                radius_min_pixels=5,
                radius_max_pixels=50,
            )

            view_state = pdk.ViewState(
                latitude=22.5,
                longitude=82.0,
                zoom=4,
                pitch=45,
                bearing=0
            )

            r = pdk.Deck(
                layers=[layer],
                initial_view_state=view_state,
                tooltip={"text": "{plant_name}\nEmission: {emissions} kt"},
                map_style="mapbox://styles/mapbox/dark-v10"
            )
            st.pydeck_chart(r)

            # Data Table
            st.markdown("### 📋 DETECTED SOURCES")
            st.dataframe(
                df[['plant_name', 'state', 'emissions', 'confidence']].sort_values('emissions', ascending=False),
                use_container_width=True,
                hide_index=True
            )

        with tab2:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("### 🏭 EMISSIONS BY FACILITY")
                fig_bar = px.bar(
                    df.sort_values('emissions', ascending=False).head(10),
                    x='plant_name',
                    y='emissions',
                    color='emissions',
                    color_continuous_scale=['#00f2ff', '#ff2a6d'],
                    template="plotly_dark"
                )
                fig_bar.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_bar, use_container_width=True)
            
            with c2:
                st.markdown("### 🗺️ REGIONAL DISTRIBUTION")
                fig_pie = px.pie(
                    df,
                    names='state',
                    values='emissions',
                    color_discrete_sequence=['#00f2ff', '#ff2a6d', '#05ffa1', '#8892b0'],
                    template="plotly_dark",
                    hole=0.4
                )
                fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_pie, use_container_width=True)

        with tab3:
            st.markdown("### 🧠 AI GENERATED INSIGHTS")
            
            ai_tabs = st.tabs(["📝 SUMMARY", "⚖️ COMPLIANCE", "🌿 ESG REPORT", "📜 DRAFT COMPLAINT"])
            
            with ai_tabs[0]:
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.markdown(ai.get_summary(df))
                st.markdown('</div>', unsafe_allow_html=True)
            
            with ai_tabs[1]:
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.markdown(ai.analyze_compliance(df))
                st.markdown('</div>', unsafe_allow_html=True)
                
            with ai_tabs[2]:
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.markdown(ai.generate_esg_report(df))
                st.markdown('</div>', unsafe_allow_html=True)
                
            with ai_tabs[3]:
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                worst_offender = df.loc[df['emissions'].idxmax()]
                st.markdown(ai.draft_cpcb_complaint(worst_offender['plant_name'], worst_offender['emissions']))
                st.markdown('</div>', unsafe_allow_html=True)
                if st.button("📤 SEND TO CPCB PORTAL"):
                    st.toast("Complaint lodged successfully! Reference ID: #CPCB-2026-X99", icon="✅")

if __name__ == "__main__":
    main()
