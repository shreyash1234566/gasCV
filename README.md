# MethaneWatch India 🛰️

**Satellite vs. Self-Reporting: Methane Emissions Audit Tool**

Compare NASA EMIT satellite-detected methane plumes against facility-reported emissions to identify potential underreporting in India's oil & gas sector.

---

## Features

✅ **NASA EMIT Integration** - Download and analyze real methane plume data  
✅ **Climate TRACE Support** - Fetch India facility emissions from API  
✅ **Spatial Matching** - Match plumes to nearby facilities using geospatial analysis  
✅ **ESG Reporting** - Generate Net Zero alignment reports (GPT-4 powered)  
✅ **Interactive Dashboard** - Streamlit UI with folium maps  
✅ **Indian Context** - Frames analysis for MoEFCC/CPCB compliance

---

## Quick Start

### 1. Installation

```bash
# Activate virtual environment
.\.venv\Scripts\Activate.ps1  # Windows
# source .venv/bin/activate     # Linux/Mac

# Install dependencies (already done)
pip install -r requirements.txt
```

### 2. Run the Dashboard

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

### 3. Configure Data Sources

**Demo Mode (Recommended for testing):**
- Select "Demo Data (Hardcoded)" in sidebar
- Uses 3 pre-loaded sample plumes
- No credentials needed

**NASA EMIT Mode (Real data):**
1. Create free account: https://urs.earthdata.nasa.gov/
2. Enter credentials in sidebar
3. Click "Fetch EMIT Plumes"

**Climate TRACE Mode (Real facilities):**
- Select "Climate TRACE API" in Facility Data section
- Fetches latest India O&G facility emissions

**ESG AI Reports (Optional):**
- Add OpenAI API key in sidebar
- Enables GPT-4 generated ESG narratives

---

## Project Structure

```
methanCV/
├── app.py                          # Main Streamlit dashboard
├── requirements.txt                # Python dependencies
├── data/
│   ├── india_facilities.csv        # Manual verified facilities
│   └── india_facilities_trace.csv  # Climate TRACE fetched (auto-generated)
├── src/
│   ├── emit_fetcher.py            # NASA EMIT data downloader
│   ├── climate_trace_fetcher.py   # Climate TRACE API client
│   ├── spatial_matcher.py         # Plume-to-facility matching
│   ├── underreporting_analyzer.py # Ratio calculations
│   └── esg_report_generator.py    # ESG compliance reports
└── output/                         # Generated reports (auto-created)
```

---

## How It Works

### 1. **Detection**
NASA EMIT satellite detects methane plumes at 60m resolution over India

### 2. **Matching**
Spatial algorithm matches plumes to nearby facilities (<5km radius)

### 3. **Analysis**
Compares satellite-detected mass vs. facility-reported annual emissions

### 4. **Ratio Calculation**
```python
Ratio = (Detected Mass × Frequency) / Reported Annual
```
Where frequency = conservative (1×), moderate (12×), or aggressive (52×)

### 5. **ESG Grading**
- **A/B**: ≤2x ratio - Aligned with Net Zero
- **C**: 2-3x ratio - Moderate discrepancy
- **D/F**: >3x ratio - Significant underreporting

---

## Data Sources

| Component | Source | Description |
|-----------|--------|-------------|
| Methane Plumes | NASA EMIT | 60m resolution, validated by NASA scientists |
| Facility Locations | Manual CSV + Climate TRACE | Verified coordinates + API-fetched |
| Emissions Baseline | Climate TRACE / Manual | Third-party estimates |
| ESG Framework | Custom | MoEFCC/CPCB/BRSR aligned |

---

## Configuration

### Region Bounding Boxes
```python
REGION_BBOX = {
    "All India": (68.0, 6.0, 97.5, 35.5),
    "Rajasthan (Barmer)": (69.0, 23.0, 76.0, 30.0),
    "Gujarat": (68.0, 20.0, 75.0, 24.5),
    "Maharashtra": (71.0, 16.0, 77.0, 21.0),
    "Assam": (92.0, 25.0, 98.0, 29.0)
}
```

### Verified Facilities (Manual CSV)
- **Mangala Oil Field** (Cairn/Vedanta) - 25.96°N, 71.51°E
- **Jamnagar Refinery** (Reliance) - 22.35°N, 69.87°E
- **Mumbai High Offshore** (ONGC) - 19.42°N, 71.33°E
- **Hazira LNG Terminal** (ONGC/Shell) - 21.16°N, 72.66°E

---

## Critical Limitations ⚠️

### 1. **Frequency Uncertainty**
- Cannot determine leak frequency from single satellite pass
- Ratio ranges 1.5x to 60x depending on actual frequency
- Requires 6+ months monitoring for accurate frequency

### 2. **Attribution Uncertainty**
- If 3+ facilities within 5km → 40% attribution confidence
- Wind patterns not modeled in basic version
- Dense regions (Permian Basin-like) have high ambiguity

### 3. **Mass Estimation**
- Plume mass has ~10x uncertainty
- Based on atmospheric assumptions (temp, pressure, mixing)
- Inverse modeling would improve accuracy

### 4. **Reported Data Quality**
- Companies self-report to regulatory bodies
- Known 40-60% underestimation in global O&G sector
- Comparing "real detection" vs. "estimated report"

---

## Use Cases

✅ **Investigative Journalism** - Find leads on potential underreporting  
✅ **Investor Due Diligence** - ESG risk assessment  
✅ **Regulatory Prioritization** - Help CPCB decide who to inspect  
✅ **Academic Research** - Study industry-wide patterns  

❌ **NOT for Direct Enforcement** - Attribution too uncertain  
❌ **NOT for Carbon Credits** - Requires continuous monitoring  
❌ **NOT for Legal Evidence** - Ground-truthing needed  

---

## Regulatory Context (India)

| Authority | Role |
|-----------|------|
| **MoEFCC** | Ministry of Environment, Forest and Climate Change |
| **CPCB** | Central Pollution Control Board (monitoring) |
| **BRSR** | Business Responsibility Report (mandatory for top 1000 companies) |
| **Net Zero Target** | India committed to Net Zero by 2070 |
| **Methane Pledge** | Global Methane Pledge - 30% reduction by 2030 |

---

## Recommended Demo Focus

### Primary: Barmer, Rajasthan
- **Coordinates**: 25.75°N, 71.38°E
- **Why**: Arid terrain (better satellite visibility), active Cairn/Vedanta oil fields
- **Facilities**: Mangala Oil Field, Barmer District fields

### Backup: Jamnagar, Gujarat
- **Coordinates**: 22.35°N, 69.87°E
- **Why**: World's largest refinery (Reliance, 1.24M bbl/day)
- **Climate TRACE**: 19.76M tonnes CO₂e emissions (2022)

---

## API Keys & Credentials

### NASA Earthdata (Required for EMIT)
- Register: https://urs.earthdata.nasa.gov/
- Free, instant activation
- Enter in sidebar or configure `.netrc`:
  ```
  machine urs.earthdata.nasa.gov
  login YOUR_USERNAME
  password YOUR_PASSWORD
  ```

### OpenAI API (Optional for ESG narratives)
- Get key: https://platform.openai.com/api-keys
- Enter in sidebar "ESG Report" section
- Only used when generating AI narratives

### Climate TRACE (No auth needed)
- Public API, no credentials required
- Rate limits apply (500 assets/request)

---

## Troubleshooting

### "No EMIT plumes found"
- **Solution**: Try wider date range or different region
- EMIT data has 1-7 day lag (not real-time)
- Use Demo mode for guaranteed data

### "Authentication failed"
- **Solution**: Check Earthdata credentials
- Verify account is active
- Try manual login in browser first

### "Climate TRACE API timeout"
- **Solution**: API may be slow, wait and retry
- Fallback to Manual CSV mode
- Check internet connection

### Import errors
- **Solution**: Ensure virtual environment activated
- Re-run: `pip install -r requirements.txt`

---

## Development

### Add New Facility
Edit `data/india_facilities.csv`:
```csv
facility_id,facility_name,operator,lat,lon,facility_type,reported_emissions_tons_year,country,region,notes
11,My New Field,ONGC,23.45,72.67,Oil Extraction,7500,India,Gujarat,"Your notes"
```

### Adjust Matching Distance
In `app.py` sidebar:
```python
max_distance_km = st.sidebar.slider("Max matching distance (km):", 1, 10, 5)
```

### Change Frequency Assumptions
In `underreporting_analyzer.py`:
```python
ratios = {
    'single_event': satellite_detection_kg / reported_kg,
    'monthly': (satellite_detection_kg * 12) / reported_kg,
    'weekly': (satellite_detection_kg * 52) / reported_kg,
    'daily': (satellite_detection_kg * 365) / reported_kg
}
```

---

## Citation

If using this tool for research, please cite:

```
MethaneWatch India (2026)
Satellite-based methane emissions audit tool
Data Sources: NASA EMIT, Climate TRACE, Global Energy Monitor
```

---

## License

This project is for educational and research purposes.

**Disclaimer**: This is a screening and analysis tool. Not intended as regulatory or legal evidence. Satellite measurements have inherent uncertainties. Always verify findings with ground-based measurements.

---

## Credits

- **NASA EMIT**: Earth Surface Mineral Dust Source Investigation
- **Climate TRACE**: Independent emissions tracking
- **Copernicus**: Sentinel satellite data
- **Global Energy Monitor**: Oil & Gas Extraction Tracker

---

## Contact & Support

For questions about methodology or technical issues, refer to:
- NASA EMIT documentation: https://github.com/nasa/EMIT-Data-Resources
- Climate TRACE API: https://climatetrace.org/
- Project repo: [Your GitHub URL]
#   g a s C V  
 