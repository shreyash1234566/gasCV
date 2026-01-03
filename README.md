# gasCV - CO2Watch India 🌍

**Satellite-based CO₂ emissions monitoring for Indian thermal power plants**

## Overview

CO2Watch India uses ESA Sentinel-5P TROPOMI satellite data to monitor NO₂ emissions from thermal power plants and estimate CO₂ emissions using proxy methods. This provides near-real-time, independent verification of power plant emissions across India.

## Features

- 🛰️ **Satellite Data**: Uses Google Earth Engine for TROPOMI NO₂ L3 data
- 🏭 **10 Major Plants**: Monitors India's largest thermal power stations
- 📊 **Plume Detection**: Automated NO₂ plume identification algorithm
- 💨 **CO₂ Estimation**: NO₂-to-CO₂ proxy conversion using emission factors
- 🗺️ **Interactive Dashboard**: Real-time Streamlit visualization
- 🚨 **Alerts**: Automated enforcement notifications

## Quick Start

### 1. Install Dependencies
```bash
cd co2watch-india
pip install -r requirements.txt
```

### 2. Authenticate with Google Earth Engine
```bash
python authenticate.py
# Follow browser prompts to authenticate
```

### 3. Run Detection
```bash
python src/processing/detect_plumes.py
```

### 4. Launch Dashboard
```bash
streamlit run app.py
# Or use: .\start.ps1 (PowerShell)
```

## Project Structure

```
co2watch-india/
├── app.py                          # Streamlit dashboard
├── authenticate.py                 # GEE authentication
├── requirements.txt                # Python dependencies
├── start.ps1                       # Quick start script
├── config/
│   └── target_plant.yaml          # Target plant configuration
├── data/
│   ├── plants/
│   │   └── india_thermal_plants.csv  # Plant database
│   └── s5p/                        # Downloaded satellite data
├── output/
│   ├── detections.csv              # Detection results
│   ├── maps/                       # Generated maps
│   └── reports/                    # Generated reports
└── src/
    ├── ingestion/
    │   └── tropomi_fetcher.py      # GEE data fetcher
    └── processing/
        └── detect_plumes.py        # Plume detection algorithm
```

## Data Sources

| Source | Type | Resolution | Update |
|--------|------|------------|--------|
| Sentinel-5P TROPOMI | NO₂ L3 | 3.5×5.5 km | Daily |
| Global Coal Plant Tracker | Plant DB | Point | Quarterly |

## Plants Monitored

| Plant | State | Capacity | Operator |
|-------|-------|----------|----------|
| Vindhyachal | MP | 4,760 MW | NTPC |
| Mundra | Gujarat | 4,620 MW | Adani |
| Sasan | MP | 3,960 MW | Reliance |
| Sipat | Chhattisgarh | 2,980 MW | NTPC |
| Rihand | UP | 3,000 MW | NTPC |
| Talcher | Odisha | 3,000 MW | NTPC |
| Chandrapur | Maharashtra | 2,920 MW | MAHAGENCO |
| Anpara | UP | 2,630 MW | UPRVUNL |
| Korba | Chhattisgarh | 2,600 MW | NTPC |
| Ramagundam | Telangana | 2,600 MW | NTPC |

## Algorithm

1. **Data Fetch**: Get TROPOMI NO₂ from GEE for India
2. **Zone Definition**: Create plume (downwind) and background (upwind) zones
3. **Enhancement Calculation**: `enhancement = plume_NO₂ - background_NO₂`
4. **Confidence Assignment**: Based on enhancement percentage
5. **CO₂ Estimation**: Using NOx-to-CO₂ emission factors

### Emission Factors
- NO₂ → NOx conversion: 1.32
- NOx → CO₂ (Indian coal): 217 kg CO₂ / kg NOx

## Confidence Levels

| Level | Enhancement | Interpretation |
|-------|-------------|----------------|
| 🔴 HIGH | >30% | Clear plume detected |
| 🟠 MEDIUM | 15-30% | Likely plume |
| 🟡 LOW | 10-15% | Possible plume |
| ⚪ NONE | <10% | No detection |

## Limitations

- **Spatial Resolution**: 3.5×5.5 km may blend nearby sources
- **Cloud Cover**: Monsoon season (Jun-Sep) has data gaps
- **Wind Direction**: Simplified algorithm assumes eastward winds
- **Accuracy**: 20-30% uncertainty in emission estimates

## Future Improvements

- [ ] ERA5 wind integration for plume direction
- [ ] OCO-2/3 validation for CO₂ estimates
- [ ] Machine learning plume detection
- [ ] Automated CPCB complaint filing
- [ ] Time series analysis for trend detection

## License

MIT License - See LICENSE file

## Acknowledgments

- ESA Copernicus for Sentinel-5P data
- Google Earth Engine for data access
- Global Energy Monitor for plant database
