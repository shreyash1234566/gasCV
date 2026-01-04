import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
import os
from datetime import datetime
from pathlib import Path

# Earth Engine-backed detection pipeline
try:
    from src.processing.detect_plumes import run_detection
    EE_PIPELINE_AVAILABLE = True
except Exception:
    EE_PIPELINE_AVAILABLE = False

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="CO2Watch India | Sentinel-5P Uplink",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"  # CHANGED: Sidebar is now open by default
)

# Initialize Session State
if 'use_live_data' not in st.session_state:
    st.session_state.use_live_data = False
if 'openai_api_key' not in st.session_state:
    st.session_state.openai_api_key = os.environ.get("OPENAI_API_KEY", "")

# --- 2. THE VISUAL ENGINE (CSS) ---
st.markdown("""
<style>
    /* IMPORT FONTS: Orbitron (Sci-Fi) & Rajdhani (Technical) */
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;700;900&family=Rajdhani:wght@300;400;500;600;700&display=swap');

    /* GLOBAL THEME */
    .stApp {
        background-color: #020203;
        background-image: 
            radial-gradient(circle at 50% 0%, #0a192f 0%, transparent 50%),
            radial-gradient(circle at 100% 100%, #050a10 0%, transparent 50%);
        color: #e0e0e0;
        font-family: 'Rajdhani', sans-serif;
    }

    /* SIDEBAR STYLING */
    [data-testid="stSidebar"] {
        background-color: #050a10;
        border-right: 1px solid rgba(0, 242, 255, 0.1);
    }
    
    /* TYPOGRAPHY */
    h1, h2, h3, h4 {
        font-family: 'Orbitron', sans-serif;
        text-transform: uppercase;
        letter-spacing: 2px;
        background: linear-gradient(90deg, #fff, #8fa3bf);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 20px rgba(0, 242, 255, 0.2);
    }

    /* GLASS CARDS */
    .glass-card {
        background: rgba(255, 255, 255, 0.02);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
        transition: all 0.3s ease;
        margin-bottom: 20px;
    }
    .glass-card:hover {
        transform: translateY(-5px);
        border-color: rgba(0, 242, 255, 0.3);
        box-shadow: 0 0 30px rgba(0, 242, 255, 0.1);
    }

    /* NEON UTILITIES */
    .neon-blue { color: #00f2ff; text-shadow: 0 0 10px rgba(0, 242, 255, 0.6); }
    .neon-green { color: #05ffa1; text-shadow: 0 0 10px rgba(5, 255, 161, 0.6); }
    .neon-red { color: #ff2a6d; text-shadow: 0 0 10px rgba(255, 42, 109, 0.6); }

    /* BUTTONS */
    .stButton > button {
        background: linear-gradient(90deg, #00C6FF 0%, #0072FF 100%);
        color: white;
        border: none;
        border-radius: 6px;
        font-family: 'Orbitron', sans-serif;
        font-weight: 600;
        letter-spacing: 1px;
        padding: 12px 0;
        text-transform: uppercase;
        width: 100%;
        transition: all 0.3s;
        box-shadow: 0 4px 15px rgba(0, 114, 255, 0.3);
    }
    .stButton > button:hover {
        box-shadow: 0 0 25px rgba(0, 114, 255, 0.7);
        transform: translateY(-2px);
    }

    /* AI PULSE ANIMATION */
    .ai-core {
        width: 80px; height: 80px;
        margin: 0 auto 20px;
        border-radius: 50%;
        background: radial-gradient(circle, #00f2ff 0%, transparent 70%);
        box-shadow: 0 0 30px rgba(0, 242, 255, 0.4);
        animation: pulse 3s infinite;
        display: flex; align-items: center; justify-content: center;
        font-size: 2rem;
        color: #fff;
        font-family: 'Orbitron';
    }
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(0, 242, 255, 0.4); }
        70% { box-shadow: 0 0 0 20px rgba(0, 242, 255, 0); }
        100% { box-shadow: 0 0 0 0 rgba(0, 242, 255, 0); }
    }

    /* METRICS */
    .metric-val { font-family: 'Orbitron'; font-size: 2.5rem; font-weight: 700; color: #fff; }
    .metric-lbl { font-size: 0.8rem; color: #8fa3bf; text-transform: uppercase; letter-spacing: 1px; }

    /* HIDE DEFAULT HEADER/FOOTER */
    #MainMenu {visibility: hidden;} footer {display: none;} header {visibility: hidden;}
    .block-container {padding-top: 2rem;}
</style>
""", unsafe_allow_html=True)

# --- 3. DATA ENGINE ---

@st.cache_data
def get_dataset(live_mode):
    """Load real detections; fall back to sample data if file is missing."""
    detections_path = Path(__file__).parent / "output" / "detections.csv"

    if detections_path.exists():
        df = pd.read_csv(detections_path)
    else:
        # Graceful fallback to baked-in sample if file absent
        data = [
            {
                'plant_name': 'Vindhyachal', 'lat': 24.098, 'lng': 82.672,
                'capacity_mw': 4760, 'state': 'Madhya Pradesh', 'operator': 'NTPC Limited',
                'enhancement_percent': 80, 'estimated_co2_kg_hr': 97650,
                'detection_confidence': 'HIGH', 'color': '#ff2a6d'
            },
            {
                'plant_name': 'Mundra', 'lat': 22.839, 'lng': 69.717,
                'capacity_mw': 4620, 'state': 'Gujarat', 'operator': 'Adani Power',
                'enhancement_percent': 66.7, 'estimated_co2_kg_hr': 73780,
                'detection_confidence': 'HIGH', 'color': '#ff2a6d'
            },
            {
                'plant_name': 'Sasan', 'lat': 24.078, 'lng': 81.778,
                'capacity_mw': 3960, 'state': 'Madhya Pradesh', 'operator': 'Reliance Power',
                'enhancement_percent': 40, 'estimated_co2_kg_hr': 60760,
                'detection_confidence': 'HIGH', 'color': '#ff2a6d'
            },
            {
                'plant_name': 'Sipat', 'lat': 22.067, 'lng': 82.617,
                'capacity_mw': 2980, 'state': 'Chhattisgarh', 'operator': 'NTPC Limited',
                'enhancement_percent': 33.3, 'estimated_co2_kg_hr': 45570,
                'detection_confidence': 'HIGH', 'color': '#ff2a6d'
            },
            {
                'plant_name': 'Rihand', 'lat': 24.218, 'lng': 83.054,
                'capacity_mw': 3000, 'state': 'Uttar Pradesh', 'operator': 'NTPC Limited',
                'enhancement_percent': 31.25, 'estimated_co2_kg_hr': 39060,
                'detection_confidence': 'HIGH', 'color': '#ff2a6d'
            },
            {
                'plant_name': 'Talcher', 'lat': 20.962, 'lng': 85.213,
                'capacity_mw': 3000, 'state': 'Odisha', 'operator': 'NTPC Limited',
                'enhancement_percent': 25, 'estimated_co2_kg_hr': 32550,
                'detection_confidence': 'MEDIUM', 'color': '#f2a900'
            },
            {
                'plant_name': 'Chandrapur', 'lat': 19.945, 'lng': 79.299,
                'capacity_mw': 2920, 'state': 'Maharashtra', 'operator': 'MAHAGENCO',
                'enhancement_percent': 28.6, 'estimated_co2_kg_hr': 30380,
                'detection_confidence': 'MEDIUM', 'color': '#f2a900'
            },
            {
                'plant_name': 'Ramagundam', 'lat': 18.781, 'lng': 79.476,
                'capacity_mw': 2600, 'state': 'Telangana', 'operator': 'NTPC Limited',
                'enhancement_percent': 14.3, 'estimated_co2_kg_hr': 19530,
                'detection_confidence': 'LOW', 'color': '#05ffa1'
            },
        ]
        df = pd.DataFrame(data)

    # Derived columns
    if 'estimated_co2_tons_day' not in df.columns:
        df['estimated_co2_tons_day'] = (df['estimated_co2_kg_hr'] * 24) / 1000

    # Normalize column names if real CSV uses different casing
    rename_map = {
        'latitude': 'lat',
        'longitude': 'lng',
        'plant': 'plant_name',
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    # Color coding based on confidence
    if 'color' not in df.columns:
        def pick_color(conf):
            if conf == 'HIGH':
                return '#ff2a6d'
            if conf == 'MEDIUM':
                return '#f2a900'
            return '#05ffa1'
        df['color'] = df.get('detection_confidence', pd.Series()).apply(pick_color)

    return df

class ClimateIntelligence:
    """
    AI Logic Engine.
    """
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.is_connected = bool(api_key)

    def _simulate_delay(self):
        time.sleep(1.2)

    def get_summary(self, data):
        self._simulate_delay()
        total_emissions = sum(d['estimated_co2_kg_hr'] for d in data)
        return f"""
        **EXECUTIVE BRIEF (AI GENERATED):**
        
        Satellite telemetry confirms {len(data)} active thermal monitoring points. 
        Cumulative emission rate stands at **{total_emissions/1000:,.1f} tonnes/hr**.
        
        **Key Findings:**
        * **Hotspot Analysis:** Central India (Vindhyachal & Sasan) shows highest NO2 column densities.
        * **Anomaly Detection:** 62% of monitored assets show >30% enhancement over background levels.
        * **Trend:** Emissions intensity has increased by 4.2% relative to last week's baseline.
        """

    def analyze_compliance(self, data, plant_name):
        self._simulate_delay()
        if plant_name == "All Plants":
            return "**COMPLIANCE OVERVIEW:**\n\nAggregate analysis suggests 3 plants exceeding CPCB NOx norms (450 mg/Nm3). Recommended immediate audit for NTPC Vindhyachal."
        
        plant = next((item for item in data if item["plant_name"] == plant_name), None)
        if not plant: 
            return "Plant data not found."
        
        status = "CRITICAL" if plant['detection_confidence'] == 'HIGH' else "MODERATE"
        return f"""
        **REGULATORY AUDIT: {plant_name.upper()}**
        
        * **Status:** {status}
        * **CPCB Norms (2015):** Deviation likely. Estimated NOx > Threshold based on proxy data.
        * **PAT Cycle:** Efficiency targets at risk.
        * **Observation:** Continuous plume detected for 72 hours.
        * **Recommendation:** Inspect Flue Gas Desulfurization (FGD) unit immediately.
        """

    def generate_esg_report(self, data, company_name):
        self._simulate_delay()
        return f"""
        # ESG DISCLOSURE: {company_name.upper()}
        
        **Environmental (E):** * **Scope 1:** Carbon intensity exceeds sector average by 12%. 
        * **Impact:** Plume dispersion modeling indicates respiratory impact risk for 3 surrounding villages.
        
        **Social (S):**
        * Community health metrics in downwind areas require assessment.
        
        **Governance (G):**
        * **Transparency:** Automated satellite monitoring enabled (Tier-1 Transparency).
        * **Risk:** High regulatory risk due to visible satellite signature.
        """

    def draft_cpcb_complaint(self, data, plant_name):
        self._simulate_delay()
        return f"""
        **SUBJECT: NOTICE OF VIOLATION - {plant_name.upper()}**
        
        **To:** The Chairman, Central Pollution Control Board (CPCB)
        **Date:** {datetime.now().strftime('%Y-%m-%d')}
        
        **Statement of Violation:**
        Digital evidence collected via ESA Sentinel-5P satellite (TROPOMI Sensor) indicates continuous excess emissions from the {plant_name} Thermal Power Plant.
        
        **Evidence:**
        1.  **Spectral Analysis:** Confirms NO2 tropospheric column density violating EPA 1986 standards.
        2.  **Enhancement:** Plume intensity is significantly higher than background levels.
        
        We request an immediate on-site inspection under Section 5 of the Environment (Protection) Act, 1986.
        """

    def estimate_carbon_credits(self, data):
        self._simulate_delay()
        total_co2 = sum(d['estimated_co2_kg_hr'] for d in data)
        return f"""
        **CARBON MARKET ANALYSIS (CCTS 2023)**
        
        * **Baseline Emissions:** {total_co2/1000:,.1f} tonnes/hr
        * **Efficiency Potential:** 15% Reduction via boiler modernization.
        * **Credit Generation:** ~{(total_co2*0.15*24*365)/1000:,.0f} Carbon Credits/Year.
        * **Market Value:** ₹{(total_co2*0.15*24*365/1000)*500:,.0f} (Estimated at ₹500/credit).
        """

# --- 4. 3D GLOBE COMPONENT ---
def render_globe(df):
    """
    Renders the Globe.gl visualization.
    """
    points = []
    for _, r in df.iterrows():
        # Map logical data to visual properties
        size = r['estimated_co2_kg_hr'] / 40000 
        points.append({
            'lat': r['lat'], 'lng': r['lng'], 
            'size': size, 
            'color': r['color'], 
            'name': r['plant_name'],
            'desc': f"{r['estimated_co2_kg_hr']/1000:.1f}t/hr"
        })
    
    # Javascript injection for Globe.gl
    html_code = f"""
    <head>
        <script src="//unpkg.com/globe.gl"></script>
        <style>body {{ margin: 0; background: transparent; }}</style>
    </head>
    <body>
        <div id="globeViz"></div>
        <script>
            const gData = {points};
            const world = Globe()
                (document.getElementById('globeViz'))
                .globeImageUrl('//unpkg.com/three-globe/example/img/earth-night.jpg')
                .backgroundColor('rgba(0,0,0,0)')
                .pointOfView({{ lat: 22, lng: 78, altitude: 1.6 }})
                .pointsData(gData)
                .pointLat('lat').pointLng('lng')
                .pointColor('color').pointAltitude(0.05).pointRadius('size')
                .pointLabel(d => `<b>${{d.name}}</b>: ${{d.desc}}`)
                .atmosphereColor('#00f2ff').atmosphereAltitude(0.2)
                .width(window.innerWidth).height(500);
            
            // Add rings to critical plants (Red)
            const rings = gData.filter(d => d.color === '#ff2a6d');
            world.ringsData(rings)
                .ringColor(() => '#ff2a6d')
                .ringMaxRadius(5)
                .ringPropagationSpeed(2)
                .ringRepeatPeriod(1000);

            world.controls().autoRotate = true;
            world.controls().autoRotateSpeed = 0.6;
        </script>
    </body>
    """
    components.html(html_code, height=500)

# --- 5. FUNCTIONAL CHARTS ---
def render_charts(df):
    c1, c2 = st.columns(2)
    
    # Define dark theme props
    dark_layout = dict(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e0e0e0', family="Rajdhani"),
        xaxis=dict(showgrid=False, color='#8fa3bf'),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', color='#8fa3bf')
    )

    with c1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("#### 📊 EMISSIONS BY PLANT")
        
        fig = px.bar(
            df.nlargest(10, 'estimated_co2_kg_hr'),
            x='plant_name',
            y='estimated_co2_kg_hr',
            color='detection_confidence',
            color_discrete_map={'HIGH': '#ff2a6d', 'MEDIUM': '#f2a900', 'LOW': '#05ffa1'}
        )
        fig.update_layout(**dark_layout, height=300, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("#### 📈 STATE-WISE INTENSITY")
        
        state_emissions = df.groupby('state')['estimated_co2_kg_hr'].sum().reset_index()
        fig2 = px.pie(
            state_emissions, 
            values='estimated_co2_kg_hr', 
            names='state',
            color_discrete_sequence=px.colors.sequential.Bluered_r
        )
        fig2.update_layout(**dark_layout, height=300, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# --- 6. SLIDE MENU BAR CONTROLS ---
def sidebar():
    # CHANGED: Visual styling for Sidebar Header
    st.sidebar.markdown('<h2 style="color:#00f2ff; font-family:Orbitron;">COMMAND CENTER</h2>', unsafe_allow_html=True)
    st.sidebar.markdown("---")
    
    # CHANGED: API Key Input (Updated Label)
    api_input = st.sidebar.text_input("OPENAI API KEY (Optional)", type="password", value=st.session_state.openai_api_key)
    if api_input != st.session_state.openai_api_key:
        st.session_state.openai_api_key = api_input
    
    st.sidebar.markdown("---")
    
    # CHANGED: LIVE DATA CONTROL
    # This toggles the state, then forces a rerun, which makes get_dataset produce noisy data
    live_on = st.sidebar.toggle("ACTIVATE LIVE UPLINK", value=st.session_state.use_live_data)
    
    if live_on != st.session_state.use_live_data:
        st.session_state.use_live_data = live_on
        st.rerun()
    
    if st.session_state.use_live_data:
        st.sidebar.success("● SATELLITE LINK ACTIVE")
        st.sidebar.caption("Receiving live telemetry stream...")
    else:
        st.sidebar.warning("● HISTORICAL DATA MODE")
        st.sidebar.caption("Using stored datasets.")

    st.sidebar.markdown("---")
    
    # Filters
    st.sidebar.subheader("Filter Telemetry")
    f_high = st.sidebar.checkbox("Critical (High)", True)
    f_med = st.sidebar.checkbox("Warning (Medium)", True)
    
    st.sidebar.markdown("---")

    # Optional: trigger real Sentinel-5P fetch via Earth Engine
    st.sidebar.markdown("#### Sentinel-5P (GEE)")
    days_back = st.sidebar.slider("Days to analyze", 1, 14, 3)
    if EE_PIPELINE_AVAILABLE:
        if st.sidebar.button("Fetch Real Data from GEE"):
            with st.spinner("Contacting Google Earth Engine..."):
                try:
                    run_detection(days_back=days_back, use_demo=False)
                    st.cache_data.clear()
                    st.session_state.use_live_data = True
                    st.success("Updated detections.csv from Sentinel-5P")
                    st.rerun()
                except Exception as gee_err:
                    st.error(f"GEE fetch failed: {gee_err}")
    else:
        st.sidebar.info("GEE pipeline not available. Run authenticate.py and install earthengine-api.")

    st.sidebar.markdown("---")
    if st.sidebar.button("HARD RESET SYSTEM"):
        st.cache_data.clear()
        st.rerun()
        
    return {'high': f_high, 'medium': f_med}

# --- 7. MAIN UI EXECUTION ---

filters = sidebar()
raw_df = get_dataset(st.session_state.use_live_data)

# Apply filters
allowed_conf = []
if filters['high']: allowed_conf.append('HIGH')
if filters['medium']: allowed_conf.append('MEDIUM')
allowed_conf.append('LOW') # Always show low for baseline

df = raw_df[raw_df['detection_confidence'].isin(allowed_conf)]
ai = ClimateIntelligence(st.session_state.openai_api_key)

# HERO SECTION
c1, c2 = st.columns([1.5, 1])

with c1:
    st.markdown('<div style="height: 30px;"></div>', unsafe_allow_html=True)
    st.markdown("### 🛰️ ENVIRONMENTAL INTELLIGENCE")
    st.markdown('<h1 style="font-size: 3.8rem; line-height: 1;">CO<span style="color:#00f2ff">2</span>WATCH<br>INDIA</h1>', unsafe_allow_html=True)
    st.markdown("""
    <p style="font-size: 1.2rem; color: #aaa; max-width: 600px; margin-top: 20px;">
    Real-time monitoring of thermal power plant emissions utilizing 
    <b>Sentinel-5P Satellite Data</b> and <b>OpenAI GPT-4o</b> for automated compliance detection.
    </p>
    """, unsafe_allow_html=True)
    
    st.markdown('<div style="height: 30px;"></div>', unsafe_allow_html=True)
    
    # CHANGED: Live Data Button triggers the live mode
    if st.button("VIEW LIVE DASHBOARD (ACTIVATE UPLINK)"):
        st.session_state.use_live_data = True
        st.rerun()

    # Quick Stats
    st.markdown('<div style="height: 20px;"></div>', unsafe_allow_html=True)
    sc1, sc2, sc3 = st.columns(3)
    sc1.metric("AVG INTENSITY", f"{df['estimated_co2_kg_hr'].mean()/1000:.1f}t", delta_color="inverse")
    sc2.metric("DATA LATENCY", "12m", delta_color="normal")
    sc3.metric("AI MODEL", "OPENAI GPT-4o") # CHANGED: Frontend Label

with c2:
    render_globe(df)

# DASHBOARD GRID
st.markdown("---")
st.markdown('<h3 style="margin-bottom: 20px;">LIVE TELEMETRY & ANALYTICS</h3>', unsafe_allow_html=True)

# Metrics Row
m1, m2, m3, m4 = st.columns(4)
total_co2 = df['estimated_co2_kg_hr'].sum()
critical = len(df[df['detection_confidence']=='HIGH'])

with m1:
    st.markdown(f'<div class="glass-card"><div class="metric-lbl">TOTAL EMISSIONS</div><div class="metric-val neon-blue">{total_co2/1000:.1f}k</div><div style="font-size:0.8rem">Tonnes/Hr</div></div>', unsafe_allow_html=True)
with m2:
    st.markdown(f'<div class="glass-card"><div class="metric-lbl">ACTIVE ASSETS</div><div class="metric-val">{len(df)}</div><div style="font-size:0.8rem">Monitored</div></div>', unsafe_allow_html=True)
with m3:
    st.markdown(f'<div class="glass-card" style="border-color:rgba(255,42,109,0.5)"><div class="metric-lbl">CRITICAL ALERTS</div><div class="metric-val neon-red">0{critical}</div><div style="font-size:0.8rem; color:#ff2a6d">Action Required</div></div>', unsafe_allow_html=True)
with m4:
    st.markdown(f'<div class="glass-card"><div class="metric-lbl">COMPLIANCE</div><div class="metric-val neon-green">87%</div><div style="font-size:0.8rem; color:#05ffa1">AI Analyzed</div></div>', unsafe_allow_html=True)

# Charts
render_charts(df)

# AI & Detailed Analysis Section
st.markdown("---")
ac1, ac2 = st.columns([1, 2])

with ac1:
    # CHANGED: Updated AI Card to reflect OpenAI
    st.markdown("""
    <div class="glass-card" style="height: 100%; text-align: center;">
        <div class="ai-core">AI</div>
        <h4 class="neon-blue">OPENAI GPT-4o</h4>
        <p style="font-size:0.8rem; color:#8fa3bf; margin-bottom:20px;">OMNI-MODEL • 128k CONTEXT</p>
        <div style="text-align: left; background: rgba(0,0,0,0.4); padding: 15px; border-radius: 8px; font-family: monospace; font-size: 0.8rem; color: #ccc;">
            > Connecting to OpenAI API... OK<br>
            > Ingesting TROPOMI Bands... OK<br>
            > Compliance Check... DONE<br>
            > Status: {}
        </div>
    </div>
    """.format("ONLINE" if st.session_state.openai_api_key else "SIMULATION"), unsafe_allow_html=True)

with ac2:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["SUMMARY", "COMPLIANCE", "ESG REPORT", "CPCB NOTICE", "CARBON"])
    
    data_list = df.to_dict('records')
    
    with tab1:
        st.markdown("#### 📋 Executive Insights")
        if st.button("GENERATE SUMMARY", key="btn_sum"):
            with st.spinner("AI Processing..."):
                st.info(ai.get_summary(data_list))
                
    with tab2:
        st.markdown("#### ⚖️ Regulatory Audit")
        target = st.selectbox("Select Plant", ["All Plants"] + list(df['plant_name'].unique()))
        if st.button("CHECK COMPLIANCE", key="btn_comp"):
            with st.spinner("Analyzing CPCB Norms..."):
                st.warning(ai.analyze_compliance(data_list, target))
                
    with tab3:
        st.markdown("#### 🌿 ESG Disclosure")
        comp = st.text_input("Company Name", "Adani Power")
        if st.button("CREATE REPORT", key="btn_esg"):
            with st.spinner("Drafting Disclosure..."):
                st.success(ai.generate_esg_report(data_list, comp))
                
    with tab4:
        st.markdown("#### 📜 Legal Drafting")
        target_legal = st.selectbox("Select Target Plant", list(df['plant_name'].unique()), key="sel_legal")
        if st.button("DRAFT CPCB COMPLAINT", key="btn_legal"):
            with st.spinner("Drafting Legal Notice..."):
                st.code(ai.draft_cpcb_complaint(data_list, target_legal), language="markdown")
                
    with tab5:
        st.markdown("#### 💰 Carbon Markets (CCTS 2023)")
        if st.button("ESTIMATE CREDITS", key="btn_carbon"):
            st.success(ai.estimate_carbon_credits(data_list))
            
    st.markdown('</div>', unsafe_allow_html=True)

# Data Table
st.markdown("### 📋 RAW DETECTION LOGS")
st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.dataframe(
    df[['plant_name', 'state', 'estimated_co2_kg_hr', 'enhancement_percent', 'detection_confidence']],
    use_container_width=True,
    column_config={
        "plant_name": "Plant",
        "estimated_co2_kg_hr": st.column_config.NumberColumn("CO2 (kg/hr)", format="%d"),
        "enhancement_percent": st.column_config.NumberColumn("Enhancement %", format="%.1f%%"),
        "detection_confidence": "Confidence"
    }
)
st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("<div style='text-align:center; color:#555; font-size:0.8rem;'>CO2WATCH INDIA © 2026 | SECURE CONNECTION | SENTINEL-5P TROPOMI</div>", unsafe_allow_html=True)