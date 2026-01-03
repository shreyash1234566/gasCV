"""
Spatial Matching Module
Matches detected methane plumes to facility locations
"""

import pandas as pd
import geopandas as gpd
import numpy as np
from scipy.spatial import cKDTree
from shapely.geometry import Point
from pathlib import Path
from typing import List, Dict, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FacilityMatcher:
    """
    Matches methane plume detections to nearby facilities
    """
    
    def __init__(self, facilities_csv: str = "./data/india_facilities.csv"):
        """
        Initialize facility matcher
        
        Args:
            facilities_csv: Path to CSV file with facility locations
        """
        self.facilities_df = pd.read_csv(facilities_csv)
        self.facilities_gdf = gpd.GeoDataFrame(
            self.facilities_df,
            geometry=gpd.points_from_xy(self.facilities_df.lon, self.facilities_df.lat),
            crs='EPSG:4326'
        )
        
        # Build spatial index for fast nearest-neighbor queries
        self.facility_coords = np.array([
            [geom.x, geom.y] for geom in self.facilities_gdf.geometry
        ])
        self.spatial_index = cKDTree(self.facility_coords)
        
        logger.info(f"Loaded {len(self.facilities_df)} facilities from database")
    
    def match_plume_to_facility(
        self,
        plume_lat: float,
        plume_lon: float,
        max_distance_km: float = 5.0
    ) -> Dict:
        """
        Find nearest facility to a detected plume
        
        Args:
            plume_lat: Plume latitude
            plume_lon: Plume longitude
            max_distance_km: Maximum distance to search (default 5 km)
            
        Returns:
            Dictionary with matched facility info or None if no match
        """
        plume_coords = np.array([[plume_lon, plume_lat]])
        
        # Find nearest neighbor
        distance, index = self.spatial_index.query(plume_coords)
        
        # Convert degree distance to km (approximate)
        distance_km = distance[0] * 111.0
        
        if distance_km <= max_distance_km:
            facility = self.facilities_gdf.iloc[index[0]]
            
            return {
                'facility_id': facility['facility_id'],
                'facility_name': facility['facility_name'],
                'operator': facility['operator'],
                'facility_type': facility['facility_type'],
                'facility_lat': facility['lat'],
                'facility_lon': facility['lon'],
                'distance_km': distance_km,
                'reported_emissions_tons': facility.get('reported_emissions_tons_year', 0),
                'confidence_score': self._calculate_confidence(distance_km, facility)
            }
        else:
            return None
    
    def match_plumes_batch(
        self,
        plumes_df: pd.DataFrame,
        max_distance_km: float = 5.0
    ) -> pd.DataFrame:
        """
        Match multiple plumes to facilities
        
        Args:
            plumes_df: DataFrame with columns: lat, lon
            max_distance_km: Maximum matching distance
            
        Returns:
            DataFrame with matched plume-facility pairs
        """
        matches = []
        
        for idx, plume in plumes_df.iterrows():
            match = self.match_plume_to_facility(
                plume['lat'],
                plume['lon'],
                max_distance_km
            )
            
            if match:
                # Add plume information to match
                match['plume_id'] = idx
                match['plume_lat'] = plume['lat']
                match['plume_lon'] = plume['lon']
                match['date'] = plume.get('date', 'Unknown')
                match['ch4_enhancement_ppm_m'] = plume.get('ch4_enhancement_ppm_m', None)
                
                matches.append(match)
        
        matches_df = pd.DataFrame(matches)
        logger.info(f"Matched {len(matches_df)} plumes to {len(matches_df['facility_id'].unique())} unique facilities")
        
        return matches_df
    
    def _calculate_confidence(self, distance_km: float, facility: pd.Series) -> float:
        """
        Calculate confidence score for plume-facility match
        
        Args:
            distance_km: Distance between plume and facility
            facility: Facility data row
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        confidence = 1.0
        
        # Factor 1: Distance penalty
        if distance_km < 1.0:
            confidence *= 1.0
        elif distance_km < 3.0:
            confidence *= 0.8
        elif distance_km < 5.0:
            confidence *= 0.6
        else:
            confidence *= 0.3
        
        # Factor 2: Facility type match (oil/gas facilities have highest confidence)
        facility_type = facility.get('facility_type', '').lower()
        if any(x in facility_type for x in ['oil', 'gas', 'extraction', 'pipeline']):
            confidence *= 1.0
        elif any(x in facility_type for x in ['refinery', 'processing']):
            confidence *= 0.9
        elif any(x in facility_type for x in ['lng', 'terminal']):
            confidence *= 0.85
        else:
            confidence *= 0.7
        
        return min(confidence, 1.0)
    
    def get_facilities_in_region(
        self,
        region_bbox: Tuple[float, float, float, float]
    ) -> pd.DataFrame:
        """
        Get all facilities in a geographic region
        
        Args:
            region_bbox: (lon_min, lat_min, lon_max, lat_max)
            
        Returns:
            DataFrame of facilities in region
        """
        lon_min, lat_min, lon_max, lat_max = region_bbox
        
        region_facilities = self.facilities_df[
            (self.facilities_df['lon'] >= lon_min) &
            (self.facilities_df['lon'] <= lon_max) &
            (self.facilities_df['lat'] >= lat_min) &
            (self.facilities_df['lat'] <= lat_max)
        ]
        
        logger.info(f"Found {len(region_facilities)} facilities in specified region")
        return region_facilities
