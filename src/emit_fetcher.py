"""
NASA EMIT Methane Plume Data Fetcher
Downloads and processes methane plume data from NASA EMIT satellite
"""

import pandas as pd
import geopandas as gpd
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import logging
import xarray as xr

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EMITDataFetcher:
    """
    Fetches and processes NASA EMIT methane plume data
    """
    
    def __init__(self, data_dir: str = "./data"):
        """
        Initialize EMIT data fetcher
        
        Args:
            data_dir: Directory to store downloaded data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.earthaccess = None
        self.is_authenticated = False
        
    def authenticate(self, username: str = None, password: str = None) -> bool:
        """Authenticate with NASA Earthdata using provided or cached credentials."""
        try:
            import earthaccess
            self.earthaccess = earthaccess

            login_kwargs = {"persist": True}
            if username:
                login_kwargs["username"] = username
            if password:
                login_kwargs["password"] = password

            earthaccess.login(**login_kwargs)
            self.is_authenticated = True
            logger.info("Successfully authenticated with NASA Earthdata")
            return True
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    def search_methane_plumes(
        self,
        bounding_box: Tuple[float, float, float, float] = None,
        temporal_range: Tuple[str, str] = ("2023-01", "2024-12"),
        count: int = 10
    ) -> List[Dict]:
        """
        Search for methane plume data in the EMIT database
        
        Args:
            bounding_box: (lon_min, lat_min, lon_max, lat_max) - defaults to India
            temporal_range: (start_date, end_date) in format "YYYY-MM"
            count: Number of results to return
            
        Returns:
            List of search results
        """
        if not self.is_authenticated:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        # Default to India bounding box if not provided
        if bounding_box is None:
            bounding_box = (68.0, 6.0, 97.5, 35.5)  # India bbox
        
        logger.info(f"Searching for methane plumes in bbox: {bounding_box}")
        logger.info(f"Temporal range: {temporal_range[0]} to {temporal_range[1]}")
        
        try:
            results = self.earthaccess.search_data(
                short_name="EMITL2BCH4PLM",
                bounding_box=bounding_box,
                temporal=temporal_range,
                count=count
            )
            
            logger.info(f"Found {len(results)} methane plume granules")
            return results
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def download_plumes(
        self,
        results: List[Dict],
        max_files: int = None
    ) -> List[Path]:
        """
        Download methane plume data files
        
        Args:
            results: Search results from search_methane_plumes()
            max_files: Maximum number of files to download (None = all)
            
        Returns:
            List of downloaded file paths
        """
        if not self.is_authenticated:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        if max_files:
            results = results[:max_files]
        
        logger.info(f"Downloading {len(results)} files...")
        
        try:
            files = self.earthaccess.download(results, self.data_dir)
            logger.info(f"Successfully downloaded {len(files)} files")
            return files
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return []

    def load_plume_raster(self, tif_file: Path) -> Optional[xr.DataArray]:
        """Load a plume raster (GeoTIFF/COG) into an xarray DataArray."""
        try:
            da = xr.open_dataarray(tif_file, engine="rasterio")
            return da
        except Exception as e:
            logger.error(f"Failed to load raster {tif_file}: {e}")
            return None
    
    def load_plume_geojson(self, geojson_file: Path) -> gpd.GeoDataFrame:
        """
        Load methane plume GeoJSON file into GeoDataFrame
        
        Args:
            geojson_file: Path to downloaded GeoJSON file
            
        Returns:
            GeoDataFrame with plume data
        """
        try:
            gdf = gpd.read_file(geojson_file)
            logger.info(f"Loaded {len(gdf)} plume features from {geojson_file.name}")
            return gdf
        except Exception as e:
            logger.error(f"Failed to load GeoJSON: {e}")
            return None
    
    def extract_plume_locations(self, geojson_file: Path) -> pd.DataFrame:
        """
        Extract plume center coordinates and metadata
        
        Args:
            geojson_file: Path to GeoJSON file
            
        Returns:
            DataFrame with plume locations and properties
        """
        gdf = self.load_plume_geojson(geojson_file)
        if gdf is None:
            return None
        
        plumes = []
        for idx, row in gdf.iterrows():
            # Get centroid of plume
            geom = row.geometry
            centroid = geom.centroid

            plume_area_km2 = None
            try:
                plume_area_km2 = gpd.GeoSeries([geom], crs="EPSG:4326").to_crs("EPSG:3857").area.iloc[0] / 1_000_000
            except Exception:
                plume_area_km2 = None
            
            plume_data = {
                'plume_id': idx,
                'lat': centroid.y,
                'lon': centroid.x,
                'date': row.get('acq_datetime', row.get('datetime', 'Unknown')),
                'geometry': geom,
                'ch4_enhancement_ppm_m': row.get('ch4_ppm_m', None),
                'uncertainty': row.get('uncertainty', None),
                'plume_area_km2': plume_area_km2
            }
            plumes.append(plume_data)
        
        plumes_df = pd.DataFrame(plumes)
        logger.info(f"Extracted {len(plumes_df)} plume locations")
        return plumes_df

    def fetch_latest_plumes(
        self,
        bounding_box: Tuple[float, float, float, float],
        temporal_range: Tuple[str, str] = ("2023-01", "2024-12"),
        max_results: int = 5
    ) -> pd.DataFrame:
        """Authenticate, search, download, and parse latest plume GeoJSONs."""
        if not self.is_authenticated:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        search_results = self.search_methane_plumes(
            bounding_box=bounding_box,
            temporal_range=temporal_range,
            count=max_results
        )
        if not search_results:
            return pd.DataFrame()

        downloaded = self.download_plumes(search_results, max_files=max_results)
        geojson_files = [Path(f) for f in downloaded if str(f).lower().endswith(('.json', '.geojson'))]

        all_plumes = []
        for gj in geojson_files:
            df = self.extract_plume_locations(gj)
            if df is not None and not df.empty:
                df["source_file"] = gj.name
                all_plumes.append(df)

        if not all_plumes:
            logger.warning("No plume geometries parsed from downloads.")
            return pd.DataFrame()

        return pd.concat(all_plumes, ignore_index=True)
    
    def get_demo_plume_data(self) -> pd.DataFrame:
        """
        Return demo/hardcoded plume data for testing without authentication
        
        Returns:
            DataFrame with sample methane plumes
        """
        demo_plumes = pd.DataFrame([
            {
                'plume_id': 1,
                'lat': 25.95,
                'lon': 71.51,
                'date': '2024-06-15',
                'ch4_enhancement_ppm_m': 450.0,
                'uncertainty': 45.0,
                'source': 'Demo: Mangala Oil Field region',
                'emission_estimate_kg': 950
            },
            {
                'plume_id': 2,
                'lat': 22.35,
                'lon': 69.87,
                'date': '2024-07-03',
                'ch4_enhancement_ppm_m': 620.0,
                'uncertainty': 62.0,
                'source': 'Demo: Jamnagar Refinery region',
                'emission_estimate_kg': 1450
            },
            {
                'plume_id': 3,
                'lat': 21.16,
                'lon': 72.66,
                'date': '2024-05-22',
                'ch4_enhancement_ppm_m': 380.0,
                'uncertainty': 38.0,
                'source': 'Demo: Hazira LNG Terminal region',
                'emission_estimate_kg': 750
            }
        ])
        
        logger.info("Loaded demo plume data (3 samples)")
        return demo_plumes
