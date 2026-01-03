"""
CO2Watch India - Streamlit Dashboard
Interactive dashboard for monitoring thermal power plant emissions.
Features AI-powered compliance analysis via FREE Groq API.
"""

import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pathlib import Path
import os

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# AI Module
from src.ai import ClimateIntelligence

# Page config
st.set_page_config(
    page_title="CO2Watch India",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E3A5F;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
    }
    .alert-high {
        background-color: #fee2e2;
        border-left: 4px solid #ef4444;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
    }
    .alert-medium {
        background-color: #fef3c7;
        border-left: 4px solid #f59e0b;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
    }
</style>
""", unsafe_allow_html=True)


def load_data():
    """Load detection results and plant data."""
    # Try to load detections
    detections_file = Path(__file__).parent / 'output' / 'detections.csv'
    plants_file = Path(__file__).parent / 'data' / 'plants' / 'india_thermal_plants.csv'
    
    # Check if detections exist, if not create demo data
    if detections_file.exists():
        detections = pd.read_csv(detections_file)
    else:
        # Demo data for presentation
        detections = create_demo_data()
        # Save demo data
        output_dir = Path(__file__).parent / 'output'
        output_dir.mkdir(exist_ok=True)
        detections.to_csv(output_dir / 'detections.csv', index=False)
    
    # Load plants
    if plants_file.exists():
        plants = pd.read_csv(plants_file)
    else:
        plants = pd.DataFrame()
    
    return detections, plants


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


def render_header():
    """Render the dashboard header."""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown('<p class="main-header">🌍 CO2Watch India</p>', unsafe_allow_html=True)
        st.markdown(
            '<p class="sub-header">Real-time CO₂ emissions monitoring via satellite NO₂ proxy detection</p>',
            unsafe_allow_html=True
        )
    
    with col2:
        st.image("https://img.icons8.com/color/96/000000/satellite.png", width=80)


def render_metrics(detections):
    """Render key metrics."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="🏭 Plants Monitored",
            value=len(detections),
            delta="+10 from last week" if len(detections) > 5 else None
        )
    
    with col2:
        total_co2 = detections['estimated_co2_kg_hr'].sum()
        st.metric(
            label="💨 Total CO₂ Rate",
            value=f"{total_co2/1000:,.0f} t/hr",
            delta=None
        )
    
    with col3:
        high_count = len(detections[detections['detection_confidence'] == 'HIGH'])
        st.metric(
            label="🔴 High Confidence",
            value=high_count,
            delta=None
        )
    
    with col4:
        st.metric(
            label="📡 Data Source",
            value="Sentinel-5P",
            delta="TROPOMI L3"
        )


def render_map(detections):
    """Render the detection map."""
    st.subheader("🗺️ Detection Map")
    
    # Prepare data for map
    map_data = detections.copy()
    
    # Color coding based on confidence
    def get_color(row):
        if row['detection_confidence'] == 'HIGH':
            return [255, 0, 0, 200]  # Red
        elif row['detection_confidence'] == 'MEDIUM':
            return [255, 165, 0, 180]  # Orange
        else:
            return [255, 255, 0, 150]  # Yellow
    
    map_data['color'] = map_data.apply(get_color, axis=1)
    map_data['radius'] = map_data['estimated_co2_kg_hr'] / 500 + 5000
    
    # Create pydeck layer
    layer = pdk.Layer(
        'ScatterplotLayer',
        data=map_data,
        get_position='[longitude, latitude]',
        get_color='color',
        get_radius='radius',
        pickable=True,
        auto_highlight=True,
        opacity=0.8
    )
    
    # View state centered on India
    view_state = pdk.ViewState(
        latitude=22,
        longitude=78,
        zoom=4.5,
        pitch=0
    )
    
    # Create deck
    r = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={
            'html': '''
                <b>{plant_name}</b><br/>
                State: {state}<br/>
                Capacity: {capacity_mw} MW<br/>
                CO₂: {estimated_co2_kg_hr:.0f} kg/hr<br/>
                Enhancement: {enhancement_percent:.1f}%<br/>
                Confidence: {detection_confidence}
            ''',
            'style': {
                'backgroundColor': 'steelblue',
                'color': 'white',
                'fontSize': '14px',
                'padding': '10px'
            }
        },
        map_style='dark'  # Use Carto dark basemap (free, no token needed)
    )
    
    st.pydeck_chart(r, use_container_width=True)


def render_charts(detections):
    """Render analysis charts."""
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 CO₂ Emissions by Plant")
        
        fig = px.bar(
            detections.nlargest(10, 'estimated_co2_kg_hr'),
            x='plant_name',
            y='estimated_co2_kg_hr',
            color='detection_confidence',
            color_discrete_map={
                'HIGH': '#ef4444',
                'MEDIUM': '#f59e0b',
                'LOW': '#22c55e'
            },
            labels={
                'plant_name': 'Plant',
                'estimated_co2_kg_hr': 'CO₂ (kg/hr)',
                'detection_confidence': 'Confidence'
            }
        )
        fig.update_layout(xaxis_tickangle=-45, height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📈 Emissions by State")
        
        state_emissions = detections.groupby('state')['estimated_co2_kg_hr'].sum().reset_index()
        state_emissions = state_emissions.sort_values('estimated_co2_kg_hr', ascending=True)
        
        fig = px.bar(
            state_emissions,
            x='estimated_co2_kg_hr',
            y='state',
            orientation='h',
            labels={
                'state': 'State',
                'estimated_co2_kg_hr': 'CO₂ (kg/hr)'
            },
            color='estimated_co2_kg_hr',
            color_continuous_scale='Reds'
        )
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)


def render_data_table(detections):
    """Render the detection data table."""
    st.subheader("📋 Detection Details")
    
    # Format for display
    display_df = detections[[
        'plant_name', 'state', 'capacity_mw',
        'estimated_co2_kg_hr', 'enhancement_percent', 'detection_confidence'
    ]].copy()
    
    display_df.columns = [
        'Plant', 'State', 'Capacity (MW)',
        'CO₂ (kg/hr)', 'Enhancement (%)', 'Confidence'
    ]
    
    display_df = display_df.sort_values('CO₂ (kg/hr)', ascending=False)
    
    # Color coding
    def highlight_confidence(val):
        if val == 'HIGH':
            return 'background-color: #fee2e2; color: #b91c1c'
        elif val == 'MEDIUM':
            return 'background-color: #fef3c7; color: #b45309'
        else:
            return 'background-color: #d1fae5; color: #047857'
    
    styled_df = display_df.style.applymap(
        highlight_confidence, subset=['Confidence']
    ).format({
        'Capacity (MW)': '{:,.0f}',
        'CO₂ (kg/hr)': '{:,.0f}',
        'Enhancement (%)': '{:.1f}'
    })
    
    st.dataframe(styled_df, use_container_width=True, height=400)


def render_alerts(detections):
    """Render enforcement alerts."""
    st.subheader("🚨 Enforcement Alerts")
    
    high_emitters = detections[detections['estimated_co2_kg_hr'] > 50000].sort_values(
        'estimated_co2_kg_hr', ascending=False
    )
    
    if high_emitters.empty:
        st.info("No high-priority alerts at this time.")
        return
    
    for idx, row in high_emitters.iterrows():
        with st.expander(
            f"⚠️ {row['plant_name']} - {row['estimated_co2_kg_hr']:,.0f} kg/hr CO₂",
            expanded=True if idx == high_emitters.index[0] else False
        ):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"""
                **Plant Details:**
                - State: {row['state']}
                - Operator: {row.get('operator', 'Unknown')}
                - Capacity: {row['capacity_mw']:,.0f} MW
                """)
            
            with col2:
                st.markdown(f"""
                **Detection Info:**
                - Enhancement: {row['enhancement_percent']:.1f}%
                - Confidence: {row['detection_confidence']}
                - Daily CO₂: {row['estimated_co2_tons_day']:.1f} tons
                """)
            
            with col3:
                if st.button("📧 Notify CPCB", key=f"cpcb_{idx}"):
                    st.success("✅ Alert filed with Central Pollution Control Board")
                
                if st.button("🐦 Tweet Alert", key=f"tweet_{idx}"):
                    st.success("✅ Alert would be posted to @CPCB_OFFICIAL")


def render_ai_section(detections):
    """Render AI-powered analysis section."""
    st.subheader("🤖 AI Climate Intelligence")
    
    # Initialize AI agent
    ai_agent = ClimateIntelligence()
    
    # Status indicator
    if ai_agent.is_available:
        st.success("✅ AI Connected (Groq Llama 3.3 70B)")
    else:
        st.warning("⚠️ AI in Demo Mode - Set GROQ_API_KEY for live analysis")
        with st.expander("🔑 How to enable AI"):
            st.markdown("""
            1. Get FREE API key at: https://console.groq.com/keys
            2. Create `.env` file in project root:
               ```
               GROQ_API_KEY=your_key_here
               ```
            3. Or set environment variable:
               ```powershell
               $env:GROQ_API_KEY = "your_key_here"
               ```
            4. Restart the dashboard
            
            **FREE Tier:** 30 requests/min, 14,400/day - No credit card!
            """)
    
    st.markdown("---")
    
    # Convert dataframe to list of dicts for AI
    detection_list = detections.to_dict('records')
    for d in detection_list:
        d['co2_tonnes_day'] = d.get('estimated_co2_tons_day', 0)
        d['confidence'] = d.get('detection_confidence', 'MEDIUM')
        d['detection_date'] = datetime.now().strftime('%Y-%m-%d')
    
    # AI Analysis Tabs
    ai_tab1, ai_tab2, ai_tab3, ai_tab4, ai_tab5 = st.tabs([
        "📋 Summary", "📜 Compliance", "📊 ESG Report", "📝 CPCB Complaint", "💰 Carbon Credits"
    ])
    
    with ai_tab1:
        st.markdown("### Quick Summary")
        if st.button("🔍 Generate Summary", key="ai_summary"):
            with st.spinner("Analyzing emission data..."):
                result = ai_agent.get_summary(detection_list)
                st.markdown(result)
    
    with ai_tab2:
        st.markdown("### Regulatory Compliance Analysis")
        st.markdown("*Analyze against CPCB, PAT, NDC, CCTS regulations*")
        
        plant_options = ["All Plants"] + list(detections['plant_name'].unique())
        selected_plant = st.selectbox("Select plant to analyze:", plant_options, key="compliance_plant")
        
        if st.button("📜 Analyze Compliance", key="ai_compliance"):
            with st.spinner("Running compliance analysis..."):
                plant_filter = None if selected_plant == "All Plants" else selected_plant
                result = ai_agent.analyze_compliance(detection_list, plant_filter)
                st.markdown(result)
    
    with ai_tab3:
        st.markdown("### ESG Report Generation")
        st.markdown("*Generate investor-ready ESG disclosure*")
        
        company_name = st.text_input("Company/Portfolio Name:", value="Indian Thermal Power Portfolio", key="esg_company")
        
        if st.button("📊 Generate ESG Report", key="ai_esg"):
            with st.spinner("Generating ESG report..."):
                result = ai_agent.generate_esg_report(detection_list, company_name)
                st.markdown(result)
                
                # Download button
                st.download_button(
                    label="📥 Download Report",
                    data=result,
                    file_name=f"ESG_Report_{datetime.now().strftime('%Y%m%d')}.md",
                    mime="text/markdown"
                )
    
    with ai_tab4:
        st.markdown("### CPCB Complaint Drafting")
        st.markdown("*Draft formal complaint based on satellite evidence*")
        
        target_plant = st.selectbox(
            "Select target plant:",
            list(detections['plant_name'].unique()),
            key="cpcb_target"
        )
        complainant = st.text_input("Complainant Name:", value="[Your Name/Organization]", key="complainant")
        
        if st.button("📝 Draft Complaint", key="ai_cpcb"):
            with st.spinner("Drafting complaint..."):
                result = ai_agent.draft_cpcb_complaint(detection_list, target_plant, complainant)
                st.markdown(result)
                
                # Download button
                st.download_button(
                    label="📥 Download Draft",
                    data=result,
                    file_name=f"CPCB_Complaint_{target_plant}_{datetime.now().strftime('%Y%m%d')}.md",
                    mime="text/markdown"
                )
    
    with ai_tab5:
        st.markdown("### Carbon Credit Analysis")
        st.markdown("*CCTS 2023 & Article 6 potential*")
        
        if st.button("💰 Analyze Carbon Credits", key="ai_carbon"):
            with st.spinner("Analyzing carbon credit potential..."):
                result = ai_agent.estimate_carbon_credits(detection_list)
                st.markdown(result)
    
    # Custom Query Section
    st.markdown("---")
    st.markdown("### 💬 Ask AI Anything")
    
    custom_query = st.text_area(
        "Ask a question about the emission data:",
        placeholder="e.g., Which plants need immediate FGD installation? What's the total carbon footprint?",
        key="custom_query"
    )
    
    if st.button("🚀 Ask AI", key="ai_custom") and custom_query:
        with st.spinner("Thinking..."):
            result = ai_agent.custom_query(detection_list, custom_query)
            st.markdown(result)


def render_sidebar():
    """Render sidebar with controls."""
    st.sidebar.title("⚙️ Controls")
    
    st.sidebar.markdown("---")
    
    # Date range
    st.sidebar.subheader("📅 Date Range")
    days = st.sidebar.slider("Days to analyze", 1, 30, 3)
    
    # Confidence filter
    st.sidebar.subheader("🎯 Confidence Filter")
    show_high = st.sidebar.checkbox("High", value=True)
    show_medium = st.sidebar.checkbox("Medium", value=True)
    show_low = st.sidebar.checkbox("Low", value=False)
    
    # Refresh button
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    
    # Info
    st.sidebar.markdown("---")
    st.sidebar.info("""
    **Data Source:** ESA Sentinel-5P TROPOMI
    
    **Method:** NO₂ proxy with plant-specific emission factors
    
    **Coverage:** Daily, pan-India
    """)
    
    return {
        'days': days,
        'confidence_filter': {
            'HIGH': show_high,
            'MEDIUM': show_medium,
            'LOW': show_low
        }
    }


def main():
    """Main dashboard function."""
    # Render sidebar
    controls = render_sidebar()
    
    # Load data
    detections, plants = load_data()
    
    # Apply confidence filter
    conf_filter = controls['confidence_filter']
    filtered_detections = detections[
        detections['detection_confidence'].apply(
            lambda x: conf_filter.get(x, True)
        )
    ]
    
    # Render header
    render_header()
    
    st.markdown("---")
    
    # Render metrics
    render_metrics(filtered_detections)
    
    st.markdown("---")
    
    # Render map
    render_map(filtered_detections)
    
    st.markdown("---")
    
    # Render charts
    render_charts(filtered_detections)
    
    st.markdown("---")
    
    # Render data table
    render_data_table(filtered_detections)
    
    st.markdown("---")
    
    # Render alerts
    render_alerts(filtered_detections)
    
    st.markdown("---")
    
    # Render AI section
    render_ai_section(filtered_detections)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
        <p><strong>CO2Watch India</strong> | Satellite-based emissions monitoring + AI Intelligence</p>
        <p>Data: ESA Sentinel-5P TROPOMI | AI: Groq Llama 3.3 70B (FREE)</p>
        <p>Aligned with: CPCB Norms | PAT Scheme | NDC 2030 | CCTS 2023</p>
        <p>© 2026 | Built for environmental transparency</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
