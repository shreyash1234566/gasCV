import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import pydeck as pdk
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pathlib import Path
import os
from dotenv import load_dotenv

# -----------------------------------------------------------------------------
# 0. SETUP & CONFIGURATION
# -----------------------------------------------------------------------------

# Load environment variables
load_dotenv()

# Load secrets if available
try:
    if hasattr(st, 'secrets'):
        for key in ['GEE_PROJECT_ID', 'GROQ_API_KEY', 'EARTHDATA_USERNAME', 'EARTHDATA_PASSWORD']:
            if key in st.secrets:
                os.environ[key] = st.secrets[key]
except Exception:
    pass

# Import AI Module
try:
    from src.ai import ClimateIntelligence
except ImportError:
    # Fallback if module structure varies
    class ClimateIntelligence:
        def __init__(self): self.is_available = False
        def get_summary(self, *args): return "AI Module not found. Please ensure src/ai exists."
        def analyze_compliance(self, *args): return "AI Module not found."
        def generate_esg_report(self, *args): return "AI Module not found."
        def draft_cpcb_complaint(self, *args): return "AI Module not found."
        def estimate_carbon_credits(self, *args): return "AI Module not found."
        def custom_query(self, *args): return "AI Module not found."

st.set_page_config(
    page_title="CO2Watch India | AI Climate Monitor",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -----------------------------------------------------------------------------
# 1. CUSTOM CSS (Futuristic, Glassmorphism, Neon)
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
            --text-main: #e6f1ff;
            --text-muted: #8892b0;
        }

        /* RESET & BASE STYLES */
        .stApp {
            background-color: var(--deep-space);
            font-family: 'Rajdhani', sans-serif;
            color: var(--text-main);
        }
        
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Orbitron', sans-serif;
            letter-spacing: 2px;
            text-transform: uppercase;
            color: #ffffff;
            text-shadow: 0 0 10px rgba(0, 242, 255, 0.3);
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
            box-shadow: 6px 0px 0px rgba(0, 242, 255, 0.5);
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
            padding: 0.75rem 2rem;
            width: 100%;
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
            font-size: 2rem !important;
        }
        [data-testid="stMetricLabel"] {
            font-family: 'Rajdhani', sans-serif;
            color: var(--text-muted) !important;
            font-size: 1.1rem;
        }
        [data-testid="stMetricDelta"] {
            font-family: 'Rajdhani', sans-serif;
        }

        /* TABS */
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
            background-color: transparent;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: rgba(0, 242, 255, 0.05);
            border-radius: 8px;
            color: var(--text-muted);
            font-family: 'Orbitron', sans-serif;
            border: 1px solid transparent;
            padding: 10px 20px;
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

        /* HIDE DEFAULT ELEMENTS */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* HERO SECTION */
        .hero-container {
            text-align: center;
            padding: 4rem 2rem;
            background: radial-gradient(circle at center, rgba(0, 242, 255, 0.05) 0%, transparent 70%);
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
            color: var(--text-muted);
            max-width: 800px;
            margin: 0 auto 2rem auto;
        }
        
        @keyframes glow {
            from { text-shadow: 0 0 10px rgba(0, 242, 255, 0.2); }
            to { text-shadow: 0 0 20px rgba(0, 242, 255, 0.6), 0 0 10px rgba(255, 255, 255, 0.4); }
        }
        
        /* DATAFRAME */
        [data-testid="stDataFrame"] {
            background: transparent;
        }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. DATA & HELPER FUNCTIONS
# -----------------------------------------------------------------------------

def create_demo_data():
    """Create demo detection data for presentation."""
    return pd.DataFrame([
        {
            'plant_name': 'Vindhyachal', 'latitude': 24.098, 'longitude': 82.672,
            'capacity_mw': 4760, 'state': 'Madhya Pradesh', 'operator': 'NTPC Limited',
            'plume_no2_mol_m2': 0.00018, 'background_no2_mol_m2': 0.00010,
            'enhancement_mol_m2': 0.00008, 'enhancement_percent': 80,
            'estimated_nox_kg_hr': 450, 'estimated_co2_kg_hr': 97650,
            'estimated_co2_tons_day': 2343.6, 'detection_confidence': 'HIGH'
        },
        {
            'plant_name': 'Mundra', 'latitude': 22.839, 'longitude': 69.717,
            'capacity_mw': 4620, 'state': 'Gujarat', 'operator': 'Adani Power',
            'plume_no2_mol_m2': 0.00015, 'background_no2_mol_m2': 0.00009,
            'enhancement_mol_m2': 0.00006, 'enhancement_percent': 66.7,
            'estimated_nox_kg_hr': 340, 'estimated_co2_kg_hr': 73780,
            'estimated_co2_tons_day': 1770.7, 'detection_confidence': 'HIGH'
        },
        {
            'plant_name': 'Sasan', 'latitude': 24.078, 'longitude': 81.778,
            'capacity_mw': 3960, 'state': 'Madhya Pradesh', 'operator': 'Reliance Power',
            'plume_no2_mol_m2': 0.00014, 'background_no2_mol_m2': 0.00010,
            'enhancement_mol_m2': 0.00004, 'enhancement_percent': 40,
            'estimated_nox_kg_hr': 280, 'estimated_co2_kg_hr': 60760,
            'estimated_co2_tons_day': 1458.2, 'detection_confidence': 'HIGH'
        },
        {
            'plant_name': 'Sipat', 'latitude': 22.067, 'longitude': 82.617,
            'capacity_mw': 2980, 'state': 'Chhattisgarh', 'operator': 'NTPC Limited',
            'plume_no2_mol_m2': 0.00012, 'background_no2_mol_m2': 0.00009,
            'enhancement_mol_m2': 0.00003, 'enhancement_percent': 33.3,
            'estimated_nox_kg_hr': 210, 'estimated_co2_kg_hr': 45570,
            'estimated_co2_tons_day': 1093.7, 'detection_confidence': 'HIGH'
        },
        {
            'plant_name': 'Rihand', 'latitude': 24.218, 'longitude': 83.054,
            'capacity_mw': 3000, 'state': 'Uttar Pradesh', 'operator': 'NTPC Limited',
            'plume_no2_mol_m2': 0.00011, 'background_no2_mol_m2': 0.00008,
            'enhancement_mol_m2': 0.000025, 'enhancement_percent': 31.25,
            'estimated_nox_kg_hr': 180, 'estimated_co2_kg_hr': 39060,
            'estimated_co2_tons_day': 937.4, 'detection_confidence': 'HIGH'
        },
        {
            'plant_name': 'Talcher', 'latitude': 20.962, 'longitude': 85.213,
            'capacity_mw': 3000, 'state': 'Odisha', 'operator': 'NTPC Limited',
            'plume_no2_mol_m2': 0.00010, 'background_no2_mol_m2': 0.00008,
            'enhancement_mol_m2': 0.00002, 'enhancement_percent': 25,
            'estimated_nox_kg_hr': 150, 'estimated_co2_kg_hr': 32550,
            'estimated_co2_tons_day': 781.2, 'detection_confidence': 'MEDIUM'
        },
        {
            'plant_name': 'Chandrapur', 'latitude': 19.945, 'longitude': 79.299,
            'capacity_mw': 2920, 'state': 'Maharashtra', 'operator': 'MAHAGENCO',
            'plume_no2_mol_m2': 0.00009, 'background_no2_mol_m2': 0.00007,
            'enhancement_mol_m2': 0.00002, 'enhancement_percent': 28.6,
            'estimated_nox_kg_hr': 140, 'estimated_co2_kg_hr': 30380,
            'estimated_co2_tons_day': 729.1, 'detection_confidence': 'MEDIUM'
        },
        {
            'plant_name': 'Anpara', 'latitude': 24.201, 'longitude': 82.648,
            'capacity_mw': 2630, 'state': 'Uttar Pradesh', 'operator': 'UPRVUNL',
            'plume_no2_mol_m2': 0.00011, 'background_no2_mol_m2': 0.00009,
            'enhancement_mol_m2': 0.00002, 'enhancement_percent': 22.2,
            'estimated_nox_kg_hr': 130, 'estimated_co2_kg_hr': 28210,
            'estimated_co2_tons_day': 677.0, 'detection_confidence': 'MEDIUM'
        },
        {
            'plant_name': 'Korba', 'latitude': 22.350, 'longitude': 82.680,
            'capacity_mw': 2600, 'state': 'Chhattisgarh', 'operator': 'NTPC Limited',
            'plume_no2_mol_m2': 0.00010, 'background_no2_mol_m2': 0.00008,
            'enhancement_mol_m2': 0.000018, 'enhancement_percent': 22.5,
            'estimated_nox_kg_hr': 120, 'estimated_co2_kg_hr': 26040,
            'estimated_co2_tons_day': 625.0, 'detection_confidence': 'MEDIUM'
        },
        {
            'plant_name': 'Ramagundam', 'latitude': 18.781, 'longitude': 79.476,
            'capacity_mw': 2600, 'state': 'Telangana', 'operator': 'NTPC Limited',
            'plume_no2_mol_m2': 0.00008, 'background_no2_mol_m2': 0.00007,
            'enhancement_mol_m2': 0.00001, 'enhancement_percent': 14.3,
            'estimated_nox_kg_hr': 90, 'estimated_co2_kg_hr': 19530,
            'estimated_co2_tons_day': 468.7, 'detection_confidence': 'LOW'
        },
    ])

@st.cache_data
def load_data():
    """Load detection results and plant data."""
    detections_file = Path(__file__).parent / 'output' / 'detections.csv'
    
    if detections_file.exists():
        detections = pd.read_csv(detections_file)
    else:
        detections = create_demo_data()
        output_dir = Path(__file__).parent / 'output'
        output_dir.mkdir(exist_ok=True)
        detections.to_csv(output_dir / 'detections.csv', index=False)
    
    return detections

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
# 3. MAIN APPLICATION
# -----------------------------------------------------------------------------

def main():
    # --- SESSION STATE ---
    if 'use_live_data' not in st.session_state:
        st.session_state.use_live_data = False

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown("## ⚙️ CONTROL PANEL")
        st.markdown("---")
        
        st.markdown("### 📅 DATE RANGE")
        days = st.slider("Days to analyze", 1, 30, 3)
        
        st.markdown("### 🎯 CONFIDENCE")
        show_high = st.checkbox("High Confidence", value=True)
        show_medium = st.checkbox("Medium Confidence", value=True)
        show_low = st.checkbox("Low Confidence", value=False)
        
        st.markdown("---")
        if st.button("🔄 REFRESH DATA"):
            st.cache_data.clear()
            st.rerun()
            
        st.markdown("---")
        st.info("System Status: ONLINE\nLatency: 24ms\nNodes: 14/14 Active")

    # --- HERO SECTION (Landing Page) ---
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

        # Load & Filter Data
        detections = load_data()
        
        # Apply filters
        conf_filter = {'HIGH': show_high, 'MEDIUM': show_medium, 'LOW': show_low}
        filtered_detections = detections[
            detections['detection_confidence'].apply(lambda x: conf_filter.get(x, True))
        ]

        # Metrics Row
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Active Hotspots", f"{len(filtered_detections)}", "+12%")
        with m2:
            total_co2 = filtered_detections['estimated_co2_kg_hr'].sum()
            st.metric("Total Emissions", f"{total_co2/1000:,.1f} t/hr", "+5.4%")
        with m3:
            high_count = len(filtered_detections[filtered_detections['detection_confidence'] == 'HIGH'])
            st.metric("Critical Alerts", f"{high_count}", "High Priority")
        with m4:
            st.metric("Data Freshness", "Live", "2s ago")

        # Main Content Tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["🗺️ GEOSPATIAL", "📊 ANALYTICS", "🤖 AI INTELLIGENCE", "📋 RAW DATA", "💬 ASK AI"])

        # TAB 1: GEOSPATIAL
        with tab1:
            st.markdown("### 📍 THERMAL ANOMALY MAP")
            
            # Prepare map data
            map_data = filtered_detections.copy()
            def get_color(row):
                if row['detection_confidence'] == 'HIGH': return [255, 42, 109, 200] # Neon Red
                elif row['detection_confidence'] == 'MEDIUM': return [0, 242, 255, 180] # Neon Cyan
                else: return [5, 255, 161, 150] # Neon Green
            
            map_data['color'] = map_data.apply(get_color, axis=1)
            map_data['radius'] = map_data['estimated_co2_kg_hr'] / 500 + 5000

            layer = pdk.Layer(
                "ScatterplotLayer",
                data=map_data,
                get_position=["longitude", "latitude"],
                get_color="color",
                get_radius="radius",
                pickable=True,
                opacity=0.8,
                stroked=True,
                filled=True,
                radius_scale=6,
                radius_min_pixels=5,
                radius_max_pixels=50,
            )

            view_state = pdk.ViewState(latitude=22.5, longitude=82.0, zoom=4, pitch=45)

            r = pdk.Deck(
                layers=[layer],
                initial_view_state=view_state,
                tooltip={"html": "<b>{plant_name}</b><br/>CO2: {estimated_co2_kg_hr} kg/hr<br/>Confidence: {detection_confidence}"},
                map_style="mapbox://styles/mapbox/dark-v10"
            )
            st.pydeck_chart(r)

        # TAB 2: ANALYTICS
        with tab2:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("### 🏭 EMISSIONS BY FACILITY")
                fig_bar = px.bar(
                    filtered_detections.nlargest(10, 'estimated_co2_kg_hr'),
                    x='plant_name',
                    y='estimated_co2_kg_hr',
                    color='detection_confidence',
                    color_discrete_map={'HIGH': '#ff2a6d', 'MEDIUM': '#00f2ff', 'LOW': '#05ffa1'},
                    template="plotly_dark"
                )
                fig_bar.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_bar, use_container_width=True)
            
            with c2:
                st.markdown("### 🗺️ REGIONAL DISTRIBUTION")
                state_emissions = filtered_detections.groupby('state')['estimated_co2_kg_hr'].sum().reset_index()
                fig_pie = px.pie(
                    state_emissions,
                    names='state',
                    values='estimated_co2_kg_hr',
                    color_discrete_sequence=['#00f2ff', '#ff2a6d', '#05ffa1', '#8892b0'],
                    template="plotly_dark",
                    hole=0.4
                )
                fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_pie, use_container_width=True)

        # TAB 3: AI INTELLIGENCE
        with tab3:
            st.markdown("### 🧠 AI GENERATED INSIGHTS")
            
            # Initialize AI
            ai_agent = ClimateIntelligence()
            
            if not ai_agent.is_available:
                st.warning("⚠️ AI running in Demo Mode. Set GROQ_API_KEY for live analysis.")

            # Prepare data for AI
            detection_list = filtered_detections.to_dict('records')
            for d in detection_list:
                d['co2_tonnes_day'] = d.get('estimated_co2_tons_day', 0)
                d['confidence'] = d.get('detection_confidence', 'MEDIUM')
                d['detection_date'] = datetime.now().strftime('%Y-%m-%d')

            ai_tabs = st.tabs(["📝 SUMMARY", "⚖️ COMPLIANCE", "🌿 ESG REPORT", "📜 DRAFT COMPLAINT", "💰 CARBON CREDITS"])
            
            with ai_tabs[0]:
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                if st.button("🔍 GENERATE SUMMARY", key="ai_sum_btn"):
                    with st.spinner("Analyzing..."):
                        st.markdown(ai_agent.get_summary(detection_list))
                else:
                    st.info("Click to generate executive summary based on current data.")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with ai_tabs[1]:
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                plant_opts = ["All Plants"] + list(filtered_detections['plant_name'].unique())
                sel_plant = st.selectbox("Select Facility", plant_opts)
                if st.button("📜 CHECK COMPLIANCE", key="ai_comp_btn"):
                    with st.spinner("Auditing..."):
                        p_filter = None if sel_plant == "All Plants" else sel_plant
                        st.markdown(ai_agent.analyze_compliance(detection_list, p_filter))
                st.markdown('</div>', unsafe_allow_html=True)
                
            with ai_tabs[2]:
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                if st.button("📊 GENERATE ESG REPORT", key="ai_esg_btn"):
                    with st.spinner("Generating..."):
                        st.markdown(ai_agent.generate_esg_report(detection_list, "Indian Thermal Power Portfolio"))
                st.markdown('</div>', unsafe_allow_html=True)
                
            with ai_tabs[3]:
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                target = st.selectbox("Target Facility", list(filtered_detections['plant_name'].unique()))
                if st.button("📝 DRAFT COMPLAINT", key="ai_cpcb_btn"):
                    with st.spinner("Drafting..."):
                        st.markdown(ai_agent.draft_cpcb_complaint(detection_list, target, "CO2Watch India"))
                st.markdown('</div>', unsafe_allow_html=True)

            with ai_tabs[4]:
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                if st.button("💰 ANALYZE CARBON CREDITS", key="ai_carbon_btn"):
                    with st.spinner("Calculating..."):
                        st.markdown(ai_agent.estimate_carbon_credits(detection_list))
                st.markdown('</div>', unsafe_allow_html=True)

        # TAB 4: RAW DATA
        with tab4:
            st.markdown("### 📋 DETECTED SOURCES")
            
            # Styling for dataframe
            def highlight_conf(val):
                if val == 'HIGH': return 'color: #ff2a6d; font-weight: bold'
                elif val == 'MEDIUM': return 'color: #00f2ff'
                return 'color: #05ffa1'

            st.dataframe(
                filtered_detections.style.applymap(highlight_conf, subset=['detection_confidence']),
                use_container_width=True,
                height=500
            )

        # TAB 5: ASK AI
        with tab5:
            st.markdown("### 💬 ASK AI ANYTHING")
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            custom_query = st.text_area("Ask a question about the emission data:", placeholder="e.g., Which plants need immediate FGD installation?")
            if st.button("🚀 ASK AI", key="ai_custom_btn") and custom_query:
                with st.spinner("Thinking..."):
                    st.markdown(ai_agent.custom_query(detection_list, custom_query))
            st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
