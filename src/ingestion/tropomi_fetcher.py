"""
CO2Watch India - TROPOMI NO2 Data Fetcher
Uses Google Earth Engine to fetch Sentinel-5P TROPOMI NO2 data.
"""

import ee
import pandas as pd
import os
from datetime import datetime, timedelta
from pathlib import Path

# Initialize Earth Engine
try:
    ee.Initialize()
except Exception:
    print("⚠️ Earth Engine not initialized. Run 'python authenticate.py' first.")
    raise


class TROPOMIFetcher:
    """
    Fetches TROPOMI NO2 data from Google Earth Engine.
    Uses the pre-processed L3 collection for faster analysis.
    """
    
    # India bounding box
    INDIA_BOUNDS = [68, 8, 97, 35]  # [west, south, east, north]
    
    # TROPOMI collection IDs
    COLLECTION_OFFL = 'COPERNICUS/S5P/OFFL/L3_NO2'  # Offline (higher quality)
    COLLECTION_NRTI = 'COPERNICUS/S5P/NRTI/L3_NO2'  # Near real-time
    
    # NO2 band name
    NO2_BAND = 'NO2_column_number_density'
    TROPO_NO2_BAND = 'tropospheric_NO2_column_number_density'
    
    def __init__(self, use_nrt: bool = False):
        """
        Initialize the TROPOMI fetcher.
        
        Args:
            use_nrt: Use near-real-time data (faster, lower quality)
        """
        self.collection_id = self.COLLECTION_NRTI if use_nrt else self.COLLECTION_OFFL
        self.india_geometry = ee.Geometry.Rectangle(self.INDIA_BOUNDS)
        
    def get_no2_composite(
        self,
        start_date: str,
        end_date: str,
        region: ee.Geometry = None,
        use_tropospheric: bool = True
    ) -> ee.Image:
        """
        Get NO2 composite image for a date range.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            region: Region of interest (default: India)
            use_tropospheric: Use tropospheric column (recommended for surface sources)
            
        Returns:
            ee.Image: Mean NO2 composite
        """
        if region is None:
            region = self.india_geometry
            
        band = self.TROPO_NO2_BAND if use_tropospheric else self.NO2_BAND
        
        collection = (
            ee.ImageCollection(self.collection_id)
            .filterBounds(region)
            .filterDate(start_date, end_date)
            .select(band)
        )
        
        # Mean composite to handle cloud gaps
        composite = collection.mean()
        
        return composite
    
    def get_no2_timeseries(
        self,
        start_date: str,
        end_date: str,
        point_lat: float,
        point_lon: float,
        buffer_km: float = 30
    ) -> pd.DataFrame:
        """
        Get NO2 time series for a specific location.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            point_lat: Latitude of point
            point_lon: Longitude of point
            buffer_km: Buffer radius in km
            
        Returns:
            DataFrame with date and NO2 values
        """
        # Create buffer geometry
        buffer_deg = buffer_km / 111  # Approximate km to degrees
        roi = ee.Geometry.Rectangle([
            point_lon - buffer_deg,
            point_lat - buffer_deg,
            point_lon + buffer_deg,
            point_lat + buffer_deg
        ])
        
        collection = (
            ee.ImageCollection(self.collection_id)
            .filterBounds(roi)
            .filterDate(start_date, end_date)
            .select(self.TROPO_NO2_BAND)
        )
        
        def extract_value(image):
            """Extract mean NO2 value for the ROI."""
            stats = image.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=roi,
                scale=5600,  # TROPOMI native resolution
                maxPixels=1e9
            )
            return ee.Feature(None, {
                'date': image.date().format('YYYY-MM-dd'),
                'no2': stats.get(self.TROPO_NO2_BAND)
            })
        
        features = collection.map(extract_value)
        
        # Get as list
        data = features.getInfo()
        
        # Convert to DataFrame
        records = [
            {
                'date': f['properties']['date'],
                'no2_mol_m2': f['properties']['no2']
            }
            for f in data['features']
            if f['properties']['no2'] is not None
        ]
        
        df = pd.DataFrame(records)
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
        
        return df
    
    def get_plant_observations(
        self,
        plants_df: pd.DataFrame,
        start_date: str,
        end_date: str,
        buffer_km: float = 30
    ) -> pd.DataFrame:
        """
        Get NO2 observations for multiple plants.
        
        Args:
            plants_df: DataFrame with 'name', 'latitude', 'longitude' columns
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            buffer_km: Buffer radius in km
            
        Returns:
            DataFrame with plant observations
        """
        # Get composite for the period
        composite = self.get_no2_composite(start_date, end_date)
        
        observations = []
        
        for _, plant in plants_df.iterrows():
            # Create buffer geometry
            buffer_deg = buffer_km / 111
            roi = ee.Geometry.Rectangle([
                plant['longitude'] - buffer_deg,
                plant['latitude'] - buffer_deg,
                plant['longitude'] + buffer_deg,
                plant['latitude'] + buffer_deg
            ])
            
            # Extract statistics
            stats = composite.reduceRegion(
                reducer=ee.Reducer.mean().combine(
                    ee.Reducer.stdDev(), '', True
                ).combine(
                    ee.Reducer.max(), '', True
                ),
                geometry=roi,
                scale=5600,
                maxPixels=1e9
            ).getInfo()
            
            observations.append({
                'plant_name': plant['name'],
                'latitude': plant['latitude'],
                'longitude': plant['longitude'],
                'capacity_mw': plant.get('capacity_mw', None),
                'state': plant.get('state', None),
                'no2_mean_mol_m2': stats.get(f'{self.TROPO_NO2_BAND}_mean'),
                'no2_std_mol_m2': stats.get(f'{self.TROPO_NO2_BAND}_stdDev'),
                'no2_max_mol_m2': stats.get(f'{self.TROPO_NO2_BAND}_max'),
                'observation_start': start_date,
                'observation_end': end_date
            })
        
        return pd.DataFrame(observations)


def fetch_latest_india_data(days_back: int = 3) -> pd.DataFrame:
    """
    Fetch latest TROPOMI data for all Indian thermal plants.
    
    Args:
        days_back: Number of days to look back
        
    Returns:
        DataFrame with plant observations
    """
    print("🛰️ CO2Watch India - TROPOMI Data Fetcher")
    print("=" * 50)
    
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
    
    # Fetch data
    fetcher = TROPOMIFetcher()
    
    print("⏳ Fetching NO2 observations...")
    observations = fetcher.get_plant_observations(
        plants,
        start_str,
        end_str,
        buffer_km=30
    )
    
    # Save results
    output_dir = Path(__file__).parent.parent.parent / 'output'
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / 'latest_observations.csv'
    observations.to_csv(output_file, index=False)
    
    print()
    print(f"✅ Saved {len(observations)} observations to {output_file}")
    print()
    print("Top 5 by NO2 concentration:")
    print(observations.nlargest(5, 'no2_mean_mol_m2')[
        ['plant_name', 'state', 'no2_mean_mol_m2']
    ].to_string(index=False))
    
    return observations


if __name__ == "__main__":
    fetch_latest_india_data(days_back=3)
