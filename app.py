"""
MethaneWatch India - Streamlit Dashboard
Interactive visualization of methane plumes and facility underreporting
"""

import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import folium_static
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from emit_fetcher import EMITDataFetcher
from spatial_matcher import FacilityMatcher
from underreporting_analyzer import UnderreportingAnalyzer
from climate_trace_fetcher import ClimateTraceFetcher
from esg_report_generator import ESGReportGenerator

# Page configuration
st.set_page_config(
    page_title="MethaneWatch India",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styling
st.markdown("""
<style>
    .metric-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .violation-high {
        color: #d73027;
        font-weight: bold;
    }
    .violation-medium {
        color: #fc8d59;
        font-weight: bold;
    }
    .violation-low {
        color: #fee090;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SIDEBAR CONFIGURATION
# ============================================================================

st.sidebar.title("🛰️ MethaneWatch India")
st.sidebar.markdown("---")

# Data source selection
st.sidebar.subheader("1. Data Source")
data_source = st.sidebar.radio(
    "Select data source:",
    ["Demo Data (Hardcoded)", "NASA EMIT API (requires credentials)"],
    index=0
)

earthdata_user = st.sidebar.text_input(
    "Earthdata username (for NASA API)",
    value="",
    disabled=data_source == "Demo Data (Hardcoded)"
)
earthdata_pass = st.sidebar.text_input(
    "Earthdata password",
    value="",
    type="password",
    disabled=data_source == "Demo Data (Hardcoded)"
)

# Geographic filters
st.sidebar.subheader("2. Geographic Filters")
region_select = st.sidebar.selectbox(
    "Filter by region:",
    ["All India", "Rajasthan (Barmer)", "Gujarat", "Maharashtra", "Assam"]
)

REGION_BBOX = {
    "All India": (68.0, 6.0, 97.5, 35.5),
    "Rajasthan (Barmer)": (69.0, 23.0, 76.0, 30.0),
    "Gujarat": (68.0, 20.0, 75.0, 24.5),
    "Maharashtra": (71.0, 16.0, 77.0, 21.0),
    "Assam": (92.0, 25.0, 98.0, 29.0)
}

# Analysis parameters
st.sidebar.subheader("3. Analysis Parameters")
max_distance_km = st.sidebar.slider(
    "Max matching distance (km):",
    1, 10, 5,
    help="Maximum distance to match plume to facility"
)

frequency_assumption = st.sidebar.selectbox(
    "Frequency assumption:",
    ["conservative", "moderate", "aggressive"],
    help="How often does the detected plume occur?\n- Conservative: single event\n- Moderate: monthly\n- Aggressive: weekly+"
)

ratio_threshold = st.sidebar.slider(
    "Underreporting ratio threshold:",
    1.0, 50.0, 3.0,
    help="Flag facilities with ratio above this value"
)

# Facility data source
st.sidebar.subheader("4. Facility Data")
facility_source = st.sidebar.radio(
    "Facility database:",
    ["Manual CSV (Verified)", "Climate TRACE API"],
    index=0,
    help="Manual CSV has verified coordinates. Climate TRACE fetches latest from API."
)

# ESG/AI Settings
st.sidebar.subheader("5. ESG Report (Optional)")
openai_api_key = st.sidebar.text_input(
    "OpenAI API Key (for AI narrative)",
    value="",
    type="password",
    help="Optional: Enables GPT-4 generated ESG narratives"
)

st.sidebar.markdown("---")
st.sidebar.info(
    "**About MethaneWatch**: Compares NASA EMIT methane detections against "
    "facility-reported emissions to identify potential underreporting. "
    "Disclaimer: This is a screening tool, not legal evidence."
)

# ============================================================================
# MAIN CONTENT
# ============================================================================

# Title and introduction
st.title("🛰️ MethaneWatch India")
st.markdown(
    "Satellite vs. Self-Reporting: Methane Emissions Audit Tool"
)

# ============================================================================
# LOAD DATA
# ============================================================================

@st.cache_resource
def initialize_components(use_climate_trace: bool = False):
    """Initialize data components (cached)"""
    # Choose facility data source
    if use_climate_trace:
        trace_fetcher = ClimateTraceFetcher("./data")
        facilities_df = trace_fetcher.load_cached_or_fetch()
        if facilities_df.empty:
            # Fallback to manual CSV
            facilities_csv = "./data/india_facilities.csv"
        else:
            trace_fetcher.save_facilities_csv(facilities_df, "india_facilities_trace.csv")
            facilities_csv = "./data/india_facilities_trace.csv"
    else:
        facilities_csv = "./data/india_facilities.csv"
    
    matcher = FacilityMatcher(facilities_csv)
    analyzer = UnderreportingAnalyzer()
    fetcher = EMITDataFetcher("./data")
    
    return matcher, analyzer, fetcher

use_trace = facility_source == "Climate TRACE API"
matcher, analyzer, fetcher = initialize_components(use_trace)

# ESG generator (not cached, depends on API key)
esg_generator = ESGReportGenerator(openai_api_key if openai_api_key else None)

plumes_df = None

if data_source == "Demo Data (Hardcoded)":
    plumes_df = fetcher.get_demo_plume_data()
    st.info("Using demo data (3 sample methane plumes from India)")
    st.session_state["plumes_df_demo"] = plumes_df
else:
    st.info("Provide Earthdata credentials in the sidebar, then click 'Fetch EMIT Plumes'.")
    fetch_button = st.sidebar.button("Fetch EMIT Plumes", type="primary")

    if fetch_button:
        if not earthdata_user and not earthdata_pass:
            st.warning("Enter Earthdata username/password or configure ~/.netrc / environment variables.")
            st.stop()

        with st.spinner("Authenticating with NASA Earthdata..."):
            authenticated = fetcher.authenticate(earthdata_user or None, earthdata_pass or None)

        if not authenticated:
            st.error("Authentication failed. Check credentials or network.")
            st.stop()

        region_bbox = REGION_BBOX.get(region_select, REGION_BBOX["All India"])
        with st.spinner("Fetching latest EMIT methane plumes..."):
            plumes_df = fetcher.fetch_latest_plumes(
                bounding_box=region_bbox,
                temporal_range=("2023-01", "2025-12"),
                max_results=5
            )

        if plumes_df is None or plumes_df.empty:
            st.error("No EMIT plume data retrieved for this region/time window. Try another region or wider dates.")
            st.stop()

        st.session_state["plumes_df_emit"] = plumes_df
        st.success(f"Loaded {len(plumes_df)} plume features from EMIT")

    if plumes_df is None:
        plumes_df = st.session_state.get("plumes_df_emit")

    if plumes_df is None or plumes_df.empty:
        st.warning("No EMIT plumes loaded yet. Click 'Fetch EMIT Plumes' to proceed.")
        st.stop()

# Apply regional filter
if region_select == "Rajasthan (Barmer)":
    facilities_region = matcher.get_facilities_in_region(REGION_BBOX["Rajasthan (Barmer)"])
    if data_source == "Demo Data (Hardcoded)":
        plumes_df = plumes_df[plumes_df['source'].str.contains('Mangala|Barmer', case=False)]
elif region_select == "Gujarat":
    facilities_region = matcher.get_facilities_in_region(REGION_BBOX["Gujarat"])
    if data_source == "Demo Data (Hardcoded)":
        plumes_df = plumes_df[plumes_df['source'].str.contains('Jamnagar|Hazira|Cambay', case=False)]
elif region_select == "Maharashtra":
    facilities_region = matcher.get_facilities_in_region(REGION_BBOX["Maharashtra"])
elif region_select == "Assam":
    facilities_region = matcher.get_facilities_in_region(REGION_BBOX["Assam"])
else:
    facilities_region = matcher.facilities_df

# ============================================================================
# PERFORM MATCHING AND ANALYSIS
# ============================================================================

# Match plumes to facilities
matches_df = matcher.match_plumes_batch(plumes_df, max_distance_km=max_distance_km)

# Analyze matches
if len(matches_df) > 0:
    analysis_df = analyzer.analyze_matches_batch(matches_df, frequency_assumption=frequency_assumption)
    analysis_df = analysis_df.reset_index(drop=True)
    
    # Flag violations
    flagged_df = analyzer.flag_potential_violators(analysis_df, ratio_threshold=ratio_threshold)
    
    # Summary statistics
    summary_stats = analyzer.generate_summary_statistics(analysis_df)
else:
    st.error("No plumes matched to facilities. Try adjusting the max matching distance.")
    st.stop()

# ============================================================================
# DISPLAY SUMMARY METRICS
# ============================================================================

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Plumes Detected", len(plumes_df))

with col2:
    st.metric("Matched to Facilities", len(matches_df))

with col3:
    st.metric("Mean Underreporting Ratio", f"{summary_stats['mean_ratio']:.1f}x")

with col4:
    st.metric("Facilities Flagged", len(flagged_df))

# ============================================================================
# INTERACTIVE MAP
# ============================================================================

st.subheader("📍 Geographic Distribution")

# Create base map
map_center = [20.5937, 78.9629]  # Center of India
m = folium.Map(
    location=map_center,
    zoom_start=4,
    tiles="OpenStreetMap"
)

# Add plume markers
for idx, plume in matches_df.iterrows():
    ratio = analysis_df.iloc[idx]['primary_ratio']
    enh_val = plume.get('ch4_enhancement_ppm_m', np.nan)
    enh_text = f"{enh_val:.0f}" if pd.notnull(enh_val) else "N/A"
    
    # Color based on ratio
    if ratio >= 10:
        color = 'darkred'
        risk = 'CRITICAL'
    elif ratio >= 5:
        color = 'red'
        risk = 'HIGH'
    elif ratio >= 3:
        color = 'orange'
        risk = 'MEDIUM'
    else:
        color = 'yellow'
        risk = 'LOW'
    
    popup_text = f"""
    <b>Methane Plume</b><br>
    Date: {plume['date']}<br>
    Enhancement: {enh_text} ppm·m<br>
    <hr>
    <b>Nearest Facility:</b><br>
    {plume['facility_name']}<br>
    Operator: {plume['operator']}<br>
    Type: {plume['facility_type']}<br>
    Distance: {plume['distance_km']:.1f} km<br>
    <hr>
    <b>Analysis</b><br>
    Reported: {plume['reported_emissions_tons']:.0f} tons/year<br>
    Ratio (if monthly): {ratio:.1f}x<br>
    Risk Level: <span class="violation-{risk.lower()}">{risk}</span>
    """
    
    folium.CircleMarker(
        location=[plume['plume_lat'], plume['plume_lon']],
        radius=10,
        color=color,
        fill=True,
        fillColor=color,
        fillOpacity=0.7,
        weight=2,
        popup=folium.Popup(popup_text, max_width=300)
    ).add_to(m)

# Add facility markers
for idx, facility in facilities_region.iterrows():
    folium.Marker(
        location=[facility['lat'], facility['lon']],
        popup=f"{facility['facility_name']}<br>{facility['operator']}",
        icon=folium.Icon(color='blue', icon='industry', prefix='fa'),
        tooltip=facility['facility_name']
    ).add_to(m)

folium_static(m, width=1200, height=600)

# ============================================================================
# DETAILED RESULTS TABLE
# ============================================================================

st.subheader("📊 Detailed Analysis Results")

# Display all matches
display_cols = [
    'facility_name', 'operator', 'facility_type', 'distance_km',
    'reported_emissions_tons', 'primary_ratio', 'interpretation'
]

analysis_display = analysis_df[display_cols].copy()
analysis_display.columns = [
    'Facility', 'Operator', 'Type', 'Distance (km)',
    'Reported (tons/yr)', 'Ratio', 'Interpretation'
]
analysis_display['Distance (km)'] = analysis_display['Distance (km)'].round(2)
analysis_display['Ratio'] = analysis_display['Ratio'].round(2)

st.dataframe(analysis_display, use_container_width=True)

# ============================================================================
# FLAGGED FACILITIES
# ============================================================================

if len(flagged_df) > 0:
    st.subheader("⚠️ Flagged Facilities (Potential Underreporting)")
    
    for idx, facility in flagged_df.iterrows():
        with st.expander(
            f"🚩 {facility['facility_name']} ({facility['risk_level']}) - Ratio: {facility['primary_ratio']:.1f}x"
        ):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Operator", facility['operator'])
                st.metric("Type", facility['facility_type'])
            
            with col2:
                st.metric("Distance from Plume", f"{facility['distance_km']:.1f} km")
                st.metric("Confidence", f"{facility['confidence_score']*100:.0f}%")
            
            with col3:
                st.metric("Reported Annual", f"{facility['reported_emissions_tons']:.0f} tons")
                st.metric("Detected Mass", f"{facility['satellite_mass_kg']:.0f} kg")
            
            st.markdown(f"**Analysis:**")
            st.write(f"- Satellite detected {facility['satellite_mass_kg']:.0f} kg of methane")
            st.write(f"- Facility reported {facility['reported_emissions_tons']:.0f} tons/year")
            st.write(f"- Assuming monthly occurrence: **{facility['primary_ratio']:.1f}x underreporting**")
            st.write(f"- Risk Level: **{facility['risk_level']}**")
            st.write(f"- **Caveat**: Actual frequency unknown from single detection")
            
            # ESG Report Section
            st.markdown("---")
            st.markdown("**📋 ESG Compliance Report:**")
            
            esg_report = esg_generator.generate_facility_report(facility.to_dict())
            esg_rating = esg_report["esg_rating"]
            
            # ESG Grade display
            grade_col1, grade_col2 = st.columns([1, 3])
            with grade_col1:
                st.markdown(
                    f'<div style="background-color: {esg_rating["color"]}; color: white; '
                    f'padding: 20px; border-radius: 10px; text-align: center; font-size: 36px; font-weight: bold;">'
                    f'{esg_rating["grade"]}</div>',
                    unsafe_allow_html=True
                )
                st.caption(f"ESG Score: {esg_rating['score']:.0f}/100")
            
            with grade_col2:
                st.markdown(f"**Net Zero Alignment:** {esg_report['net_zero_alignment']['status']}")
                st.write(esg_report['net_zero_alignment']['description'])
                st.markdown(f"**Compliance Risk:** {esg_report['regulatory_context']['compliance_risk']}")
            
            # AI Narrative (if available)
            if openai_api_key:
                with st.spinner("Generating AI narrative..."):
                    narrative = esg_generator.generate_ai_narrative(esg_report)
                st.markdown("**AI Assessment:**")
                st.info(narrative)
            else:
                st.markdown("**Recommendations:**")
                for rec in esg_report["recommendations"][:3]:
                    st.write(f"• {rec}")

# ============================================================================
# PORTFOLIO ESG SUMMARY
# ============================================================================

if len(analysis_df) > 0:
    st.subheader("📈 Portfolio ESG Summary")
    
    portfolio_summary = esg_generator.generate_portfolio_summary(analysis_df)
    
    p_col1, p_col2, p_col3, p_col4 = st.columns(4)
    
    with p_col1:
        st.metric("Total Facilities", portfolio_summary["total_facilities"])
    with p_col2:
        st.metric("Avg. Ratio", f"{portfolio_summary['average_ratio']:.1f}x")
    with p_col3:
        st.metric("Above 3x Threshold", portfolio_summary["facilities_above_3x"])
    with p_col4:
        risk_color = {"HIGH": "🔴", "MODERATE": "🟡", "LOW": "🟢"}.get(portfolio_summary["portfolio_risk_level"], "⚪")
        st.metric("Portfolio Risk", f"{risk_color} {portfolio_summary['portfolio_risk_level']}")
    
    # Grade distribution
    if portfolio_summary.get("grade_distribution"):
        st.markdown("**ESG Grade Distribution:**")
        grade_text = " | ".join([f"**{g}**: {c}" for g, c in sorted(portfolio_summary["grade_distribution"].items())])
        st.write(grade_text)

# ============================================================================
# METHODOLOGY & CAVEATS
# ============================================================================

st.subheader("📖 Methodology & Important Caveats")

with st.expander("How This Works"):
    st.markdown("""
    ### Data Pipeline:
    1. **Detection**: NASA EMIT satellite detects methane plumes (60m resolution)
    2. **Matching**: Plumes matched to nearby facilities (<5km away)
    3. **Analysis**: Satellite mass vs. reported annual emissions
    4. **Ratio Calculation**: Estimated annual emissions under different frequency assumptions
    
    ### Frequency Assumptions:
    - **Conservative**: Single annual event
    - **Moderate**: Monthly occurrence
    - **Aggressive**: Weekly occurrence
    """)

with st.expander("Critical Limitations (READ THIS)"):
    st.markdown("""
    ### Major Uncertainty Factors:
    
    ⚠️ **Cannot determine leak frequency from single detection**
    - One satellite plume could be a rare accident or continuous emission
    - Ratio ranges from 1.5x to 60x depending on actual frequency
    - Without 6+ months of monitoring, frequency is essentially unknown
    
    ⚠️ **Attribution uncertainty when multiple facilities nearby**
    - If 3+ facilities within 5km, 40%+ chance of wrong attribution
    - Wind patterns not accounted for in demo version
    
    ⚠️ **Plume mass estimates have ~10x uncertainty**
    - Based on atmospheric assumptions (temperature, pressure, height)
    - Actual mass could be 10x higher or lower
    - Inverse modeling would improve accuracy
    
    ⚠️ **Reported data may already be inaccurate**
    - Companies self-report to EPA
    - Known 40-60% underestimation in US oil/gas sector
    - May be comparing garbage to garbage
    
    ### NOT a Legal Tool:
    - This is investigative/screening analysis only
    - Does not constitute regulatory violation evidence
    - EPA requires ground-truthing + certified measurements
    - Useful for: journalism, investor due diligence, regulatory prioritization
    """)

with st.expander("Data Sources"):
    st.markdown("""
    ### Methane Plume Data:
    - **NASA EMIT**: Level 2B Methane Plume Complexes (EMITL2BCH4PLM)
    - **Resolution**: 60 meters
    - **Revisit**: Variable (depends on ISS orbit)
    - **Data Lag**: 1-7 days (validated by NASA scientists)
    
    ### Facility Data:
    - **Primary**: Global Energy Monitor Oil & Gas Extraction Tracker
    - **Backup**: OpenStreetMap infrastructure data
    - **Emissions**: Company sustainability reports
    
    ### Indian Regulatory Context:
    - MoEFCC (Ministry of Environment): Emissions authority
    - CPCB (Central Pollution Control Board): Monitoring
    - Business Responsibility Reporting (BRSR): Mandatory for large companies
    """)

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: gray; font-size: 12px;">
    <p>MethaneWatch India v0.1 | Created for Climate Hackathon 2026</p>
    <p>Data: NASA EMIT, Global Energy Monitor, OpenStreetMap</p>
    <p><strong>Disclaimer</strong>: This is a screening and analysis tool. 
    Not intended as regulatory or legal evidence.</p>
</div>
""", unsafe_allow_html=True)
