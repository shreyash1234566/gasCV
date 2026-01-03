"""
CO2Watch India - Plume Detection Algorithm
Detects NO2 plumes from thermal power plants and estimates CO2 emissions.
"""

import ee
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Get project ID from environment
GEE_PROJECT_ID = os.environ.get('GEE_PROJECT_ID', None)

# Initialize Earth Engine (with graceful demo mode fallback)
GEE_AVAILABLE = False
try:
    if GEE_PROJECT_ID:
        ee.Initialize(project=GEE_PROJECT_ID)
        GEE_AVAILABLE = True
    else:
        ee.Initialize()
        GEE_AVAILABLE = True
except Exception as e:
    print("⚠️ Earth Engine not initialized (demo mode enabled)")
    print(f"   Error: {str(e)}")
    print("   Run 'python authenticate.py' for real data")
    GEE_AVAILABLE = False


class PlumeDetector:
    """
    Detects NO2 plumes and estimates CO2 emissions using proxy method.
    
    The algorithm:
    1. Define downwind (plume) and upwind (background) zones around plant
    2. Calculate NO2 enhancement (plume - background)
    3. Convert NO2 to CO2 using emission factor ratios
    """
    
    # TROPOMI collection
    COLLECTION = 'COPERNICUS/S5P/OFFL/L3_NO2'
    NO2_BAND = 'tropospheric_NO2_column_number_density'
    
    # Emission conversion factors (from literature)
    # These are approximate and can be refined with plant-specific data
    EMISSION_FACTORS = {
        'wind_speed_ms': 5.0,         # Default wind speed (m/s)
        'mol_weight_no2': 0.046,      # kg/mol
        'no2_to_nox': 1.32,           # NO2 → NOx factor
        'nox_to_co2_coal': 217,       # NOx → CO2 for Indian coal
        'nox_to_co2_gas': 350,        # NOx → CO2 for natural gas
    }
    
    # Detection thresholds
    THRESHOLDS = {
        'min_enhancement_pct': 10,    # Minimum % enhancement for detection
        'high_confidence_pct': 30,    # High confidence threshold
        'medium_confidence_pct': 15,  # Medium confidence threshold
    }
    
    def __init__(self, buffer_km: float = 30):
        """
        Initialize the plume detector.
        
        Args:
            buffer_km: Buffer radius around plants in km
        """
        self.buffer_km = buffer_km
        self.buffer_deg = buffer_km / 111  # Convert to degrees
        
    def detect_plume(
        self,
        plant_lat: float,
        plant_lon: float,
        plant_name: str,
        start_date: str,
        end_date: str,
        capacity_mw: Optional[float] = None,
        fuel_type: str = 'coal'
    ) -> Optional[Dict]:
        """
        Detect NO2 plume at a power plant location.
        
        Args:
            plant_lat: Plant latitude
            plant_lon: Plant longitude
            plant_name: Plant name
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            capacity_mw: Plant capacity in MW (optional)
            fuel_type: 'coal' or 'gas'
            
        Returns:
            Detection dictionary or None if no data
        """
        # Define zones
        # Simplified: assume east is downwind (can use ERA5 winds for accuracy)
        plume_zone = ee.Geometry.Rectangle([
            plant_lon,
            plant_lat - self.buffer_deg / 2,
            plant_lon + self.buffer_deg,
            plant_lat + self.buffer_deg / 2
        ])
        
        background_zone = ee.Geometry.Rectangle([
            plant_lon - self.buffer_deg,
            plant_lat - self.buffer_deg / 2,
            plant_lon,
            plant_lat + self.buffer_deg / 2
        ])
        
        # Get NO2 composite
        collection = (
            ee.ImageCollection(self.COLLECTION)
            .filterDate(start_date, end_date)
            .select(self.NO2_BAND)
        )
        
        no2_mean = collection.mean()
        
        # Extract statistics
        try:
            plume_stats = no2_mean.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=plume_zone,
                scale=5600,
                maxPixels=1e9
            ).getInfo()
            
            background_stats = no2_mean.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=background_zone,
                scale=5600,
                maxPixels=1e9
            ).getInfo()
        except Exception as e:
            print(f"⚠️ Error fetching data for {plant_name}: {e}")
            return None
        
        # Check for valid data
        plume_no2 = plume_stats.get(self.NO2_BAND)
        background_no2 = background_stats.get(self.NO2_BAND)
        
        if plume_no2 is None or background_no2 is None:
            return None
        
        # Calculate enhancement
        enhancement = plume_no2 - background_no2
        enhancement_pct = (enhancement / background_no2 * 100) if background_no2 > 0 else 0
        
        # Estimate emissions
        emissions = self._estimate_emissions(enhancement, fuel_type)
        
        # Determine confidence
        if enhancement_pct >= self.THRESHOLDS['high_confidence_pct']:
            confidence = 'HIGH'
        elif enhancement_pct >= self.THRESHOLDS['medium_confidence_pct']:
            confidence = 'MEDIUM'
        elif enhancement_pct >= self.THRESHOLDS['min_enhancement_pct']:
            confidence = 'LOW'
        else:
            confidence = 'NONE'
        
        return {
            'plant_name': plant_name,
            'latitude': plant_lat,
            'longitude': plant_lon,
            'capacity_mw': capacity_mw,
            'date_start': start_date,
            'date_end': end_date,
            'plume_no2_mol_m2': plume_no2,
            'background_no2_mol_m2': background_no2,
            'enhancement_mol_m2': enhancement,
            'enhancement_percent': enhancement_pct,
            'estimated_nox_kg_hr': emissions['nox_kg_hr'],
            'estimated_co2_kg_hr': emissions['co2_kg_hr'],
            'estimated_co2_tons_day': emissions['co2_tons_day'],
            'detection_confidence': confidence,
            'fuel_type': fuel_type
        }
    
    def _estimate_emissions(self, enhancement_mol_m2: float, fuel_type: str) -> Dict:
        """
        Estimate emissions from NO2 enhancement.
        
        This is a simplified calculation. Full implementation would:
        - Use actual wind speed/direction from ERA5
        - Apply cross-sectional flux method
        - Account for NO2 photochemistry
        
        Args:
            enhancement_mol_m2: NO2 enhancement in mol/m²
            fuel_type: 'coal' or 'gas'
            
        Returns:
            Dict with emission estimates
        """
        factors = self.EMISSION_FACTORS
        
        # Get appropriate NOx to CO2 ratio
        nox_to_co2 = (
            factors['nox_to_co2_coal'] if fuel_type == 'coal'
            else factors['nox_to_co2_gas']
        )
        
        # Estimate NOx flux
        # Simplified: NO2 column × effective area × wind × conversion
        area_m2 = (self.buffer_km * 1000) ** 2
        
        nox_flux = (
            enhancement_mol_m2 *
            area_m2 *
            factors['wind_speed_ms'] *
            factors['mol_weight_no2'] *
            factors['no2_to_nox'] *
            3600  # seconds to hours
        ) / 1e6  # Scale factor
        
        co2_flux = nox_flux * nox_to_co2
        
        return {
            'nox_kg_hr': max(0, nox_flux),
            'co2_kg_hr': max(0, co2_flux),
            'co2_tons_day': max(0, co2_flux * 24 / 1000)
        }

    def detect_all_plants(
        self,
        plants_df: pd.DataFrame,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """
        Run detection for all plants in a DataFrame.
        
        Args:
            plants_df: DataFrame with plant info
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with detection results
        """
        detections = []
        
        for idx, plant in plants_df.iterrows():
            print(f"🔍 Processing {plant['name']}...")
            
            result = self.detect_plume(
                plant_lat=plant['latitude'],
                plant_lon=plant['longitude'],
                plant_name=plant['name'],
                start_date=start_date,
                end_date=end_date,
                capacity_mw=plant.get('capacity_mw'),
                fuel_type=plant.get('fuel_type', 'coal').lower()
            )
            
            if result:
                result['state'] = plant.get('state')
                result['operator'] = plant.get('operator')
                detections.append(result)
        
        return pd.DataFrame(detections)


def _create_demo_detections(plants_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create realistic demo detection data for testing/presentation.
    Uses slight variations on base values to simulate realistic observations.
    """
    np.random.seed(42)  # For reproducible demo data
    
    base_detections = [
        {'name': 'Vindhyachal', 'base_co2': 97650, 'confidence': 'HIGH'},
        {'name': 'Mundra', 'base_co2': 73780, 'confidence': 'HIGH'},
        {'name': 'Sasan', 'base_co2': 60760, 'confidence': 'HIGH'},
        {'name': 'Sipat', 'base_co2': 45570, 'confidence': 'HIGH'},
        {'name': 'Rihand', 'base_co2': 39060, 'confidence': 'HIGH'},
        {'name': 'Talcher', 'base_co2': 32550, 'confidence': 'MEDIUM'},
        {'name': 'Chandrapur', 'base_co2': 30380, 'confidence': 'MEDIUM'},
        {'name': 'Anpara', 'base_co2': 28210, 'confidence': 'MEDIUM'},
        {'name': 'Korba', 'base_co2': 26040, 'confidence': 'MEDIUM'},
        {'name': 'Ramagundam', 'base_co2': 19530, 'confidence': 'LOW'},
    ]
    
    detections = []
    
    for base_det in base_detections:
        plant = plants_df[plants_df['name'] == base_det['name']].iloc[0]
        
        # Add realistic variation (±10%)
        co2_var = base_det['base_co2'] * (1 + np.random.uniform(-0.1, 0.1))
        enhancement = co2_var / 217 / 30  # Reverse calculate enhancement
        
        detection = {
            'plant_name': base_det['name'],
            'latitude': plant['latitude'],
            'longitude': plant['longitude'],
            'capacity_mw': plant['capacity_mw'],
            'state': plant['state'],
            'operator': plant['operator'],
            'date_start': (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d'),
            'date_end': datetime.now().strftime('%Y-%m-%d'),
            'plume_no2_mol_m2': 0.00015,
            'background_no2_mol_m2': 0.00009,
            'enhancement_mol_m2': enhancement,
            'enhancement_percent': (enhancement / 0.00009) * 100,
            'estimated_nox_kg_hr': co2_var / 217,
            'estimated_co2_kg_hr': co2_var,
            'estimated_co2_tons_day': co2_var * 24 / 1000,
            'detection_confidence': base_det['confidence'],
            'fuel_type': 'coal'
        }
        detections.append(detection)
    
    return pd.DataFrame(detections)


def run_detection(days_back: int = 3, use_demo: bool = False) -> pd.DataFrame:
    """
    Run plume detection for all Indian thermal plants.
    
    Args:
        days_back: Number of days to analyze
        use_demo: Force demo mode (useful when GEE not available)
        
    Returns:
        DataFrame with detections
    """
    print("🔬 CO2Watch India - Plume Detection")
    print("=" * 50)
    print()
    
    # Load plants
    plants_file = Path(__file__).parent.parent.parent / 'data' / 'plants' / 'india_thermal_plants.csv'
    plants = pd.read_csv(plants_file)
    print(f"📋 Loaded {len(plants)} thermal plants")
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    
    print(f"📅 Date range: {start_str} to {end_str}")
    print()
    
    # Check if using demo mode
    if not GEE_AVAILABLE or use_demo:
        print("📊 Using DEMO DATA (Earth Engine not available)")
        print("   For real data, authenticate: python authenticate.py")
        print()
        detections = _create_demo_detections(plants)
    else:
        print("⏳ Fetching real NO2 observations from Sentinel-5P...")
        # Run detection with real data
        detector = PlumeDetector(buffer_km=30)
        detections = detector.detect_all_plants(plants, start_str, end_str)
    
    # Save results
    output_dir = Path(__file__).parent.parent.parent / 'output'
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / 'detections.csv'
    detections.to_csv(output_file, index=False)
    
    print()
    print("=" * 50)
    print(f"✅ Detection complete! Found {len(detections)} plants with data")
    print()
    
    # Summary (handle empty DataFrame)
    if not detections.empty and 'detection_confidence' in detections.columns:
        high_conf = detections[detections['detection_confidence'] == 'HIGH']
        medium_conf = detections[detections['detection_confidence'] == 'MEDIUM']
        
        print(f"🔴 High confidence detections: {len(high_conf)}")
        print(f"🟠 Medium confidence detections: {len(medium_conf)}")
        print()
        
        print("Top 5 emitters by estimated CO2:")
        print(detections.nlargest(5, 'estimated_co2_kg_hr')[
            ['plant_name', 'state', 'estimated_co2_kg_hr', 'detection_confidence']
        ].to_string(index=False))
    else:
        print("⚠️ No detections found - try increasing --days parameter")
        print("   Example: python src/processing/detect_plumes.py --days 14")
    
    print()
    print(f"📁 Results saved to: {output_file}")
    
    return detections


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='CO2Watch India Plume Detection')
    parser.add_argument('--demo', action='store_true', help='Force demo mode')
    parser.add_argument('--days', type=int, default=3, help='Days to analyze')
    args = parser.parse_args()
    
    run_detection(days_back=args.days, use_demo=args.demo)
