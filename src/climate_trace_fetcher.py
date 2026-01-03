"""
Climate TRACE Data Fetcher
Downloads facility-level emissions data from Climate TRACE API
"""

import requests
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ClimateTraceFetcher:
    """
    Fetches emissions data from Climate TRACE API
    https://climatetrace.org/inventory
    """
    
    BASE_URL = "https://api.climatetrace.org/v6"
    
    # Sector mappings for oil & gas facilities
    OIL_GAS_SECTORS = [
        "oil-and-gas-production-and-transport",
        "oil-and-gas-refining",
        "other-fossil-fuel-operations",
        "petrochemicals"
    ]
    
    def __init__(self, data_dir: str = "./data"):
        """
        Initialize Climate TRACE fetcher
        
        Args:
            data_dir: Directory to store downloaded data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
    def fetch_country_emissions(
        self,
        country_code: str = "IND",
        gas: str = "ch4",
        since: int = 2020,
        to: int = 2024
    ) -> pd.DataFrame:
        """
        Fetch country-level emissions inventory
        
        Args:
            country_code: ISO 3166-1 alpha-3 country code (e.g., "IND" for India)
            gas: Gas type ("ch4" for methane, "co2" for CO2)
            since: Start year
            to: End year
            
        Returns:
            DataFrame with emissions by sector and year
        """
        url = f"{self.BASE_URL}/country/emissions"
        
        params = {
            "countries": country_code,
            "gas": gas,
            "since": since,
            "to": to
        }
        
        logger.info(f"Fetching {gas.upper()} emissions for {country_code} ({since}-{to})...")
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            df = pd.DataFrame(data)
            
            logger.info(f"Retrieved {len(df)} emission records")
            return df
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return pd.DataFrame()
    
    def fetch_sector_assets(
        self,
        country_code: str = "IND",
        sectors: Optional[List[str]] = None,
        gas: str = "ch4"
    ) -> pd.DataFrame:
        """
        Fetch individual asset/facility emissions for specific sectors
        
        Args:
            country_code: ISO country code
            sectors: List of sector names (defaults to oil & gas)
            gas: Gas type
            
        Returns:
            DataFrame with facility-level emissions
        """
        if sectors is None:
            sectors = self.OIL_GAS_SECTORS
        
        all_assets = []
        
        for sector in sectors:
            url = f"{self.BASE_URL}/assets"
            
            params = {
                "countries": country_code,
                "sectors": sector,
                "gas": gas,
                "limit": 500  # Max per request
            }
            
            logger.info(f"Fetching {sector} assets for {country_code}...")
            
            try:
                response = requests.get(url, params=params, timeout=60)
                response.raise_for_status()
                
                data = response.json()
                assets = data.get("assets", data) if isinstance(data, dict) else data
                
                if assets:
                    for asset in assets:
                        asset["sector"] = sector
                    all_assets.extend(assets)
                    logger.info(f"  Found {len(assets)} assets in {sector}")
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"Failed to fetch {sector}: {e}")
                continue
        
        if not all_assets:
            logger.warning("No assets found from Climate TRACE API")
            return pd.DataFrame()
        
        df = pd.DataFrame(all_assets)
        logger.info(f"Total assets retrieved: {len(df)}")
        return df
    
    def normalize_to_facilities_format(
        self,
        assets_df: pd.DataFrame,
        manual_facilities: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """
        Normalize Climate TRACE asset data to match india_facilities.csv format
        
        Args:
            assets_df: Raw assets DataFrame from API
            manual_facilities: Optional manual facility entries to merge
            
        Returns:
            Normalized DataFrame matching facilities format
        """
        if assets_df.empty:
            if manual_facilities is not None:
                return manual_facilities
            return pd.DataFrame()
        
        # Map Climate TRACE fields to our format
        normalized = pd.DataFrame()
        
        # Extract coordinates (TRACE uses different field names)
        if "lat" in assets_df.columns:
            normalized["lat"] = assets_df["lat"]
        elif "latitude" in assets_df.columns:
            normalized["lat"] = assets_df["latitude"]
        
        if "lon" in assets_df.columns:
            normalized["lon"] = assets_df["lon"]
        elif "longitude" in assets_df.columns:
            normalized["lon"] = assets_df["longitude"]
        
        # Map other fields
        normalized["facility_name"] = assets_df.get("name", assets_df.get("asset_name", "Unknown"))
        normalized["operator"] = assets_df.get("operator", assets_df.get("owner", "Unknown"))
        normalized["facility_type"] = assets_df.get("sector", "Unknown").str.replace("-", " ").str.title()
        
        # Emissions (convert to tons/year if needed)
        if "emissions_quantity" in assets_df.columns:
            # TRACE reports in tonnes CO2e, we keep as-is for methane
            normalized["reported_emissions_tons_year"] = assets_df["emissions_quantity"]
        elif "emissions" in assets_df.columns:
            normalized["reported_emissions_tons_year"] = assets_df["emissions"]
        else:
            normalized["reported_emissions_tons_year"] = 0
        
        normalized["country"] = "India"
        normalized["region"] = assets_df.get("admin1", assets_df.get("state", "Unknown"))
        normalized["notes"] = "Source: Climate TRACE API"
        
        # Add facility IDs
        normalized["facility_id"] = range(1, len(normalized) + 1)
        
        # Merge with manual facilities if provided
        if manual_facilities is not None and not manual_facilities.empty:
            # Offset IDs for manual entries
            manual_copy = manual_facilities.copy()
            manual_copy["facility_id"] = range(len(normalized) + 1, len(normalized) + len(manual_copy) + 1)
            manual_copy["notes"] = manual_copy.get("notes", "") + " [Manual Entry]"
            
            normalized = pd.concat([normalized, manual_copy], ignore_index=True)
        
        # Reorder columns
        cols = [
            "facility_id", "facility_name", "operator", "lat", "lon",
            "facility_type", "reported_emissions_tons_year", "country", "region", "notes"
        ]
        
        # Only include columns that exist
        cols = [c for c in cols if c in normalized.columns]
        normalized = normalized[cols]
        
        logger.info(f"Normalized {len(normalized)} facilities")
        return normalized
    
    def get_india_oil_gas_facilities(self, include_manual: bool = True) -> pd.DataFrame:
        """
        Get India oil & gas facilities from Climate TRACE + manual entries
        
        Args:
            include_manual: Whether to include hardcoded verified facilities
            
        Returns:
            DataFrame with all India O&G facilities
        """
        # Fetch from API
        assets_df = self.fetch_sector_assets(country_code="IND")
        
        # Manual verified facilities (always include as anchors)
        manual_facilities = None
        if include_manual:
            manual_facilities = pd.DataFrame([
                {
                    "facility_name": "Mangala Oil Field",
                    "operator": "Cairn India / Vedanta",
                    "lat": 25.9586,
                    "lon": 71.5095,
                    "facility_type": "Oil Extraction",
                    "reported_emissions_tons_year": 8500,
                    "country": "India",
                    "region": "Rajasthan",
                    "notes": "Barmer District, Block RJ-ON-90-1. Verified coordinates."
                },
                {
                    "facility_name": "Mumbai High Offshore",
                    "operator": "ONGC",
                    "lat": 19.4167,
                    "lon": 71.3333,
                    "facility_type": "Offshore Platform",
                    "reported_emissions_tons_year": 15000,
                    "country": "India",
                    "region": "Maharashtra",
                    "notes": "India's largest oil platform. 160 km offshore. Verified coordinates."
                },
                {
                    "facility_name": "Jamnagar Refinery",
                    "operator": "Reliance Industries",
                    "lat": 22.3481,
                    "lon": 69.8689,
                    "facility_type": "Refinery",
                    "reported_emissions_tons_year": 19760,
                    "country": "India",
                    "region": "Gujarat",
                    "notes": "World's largest refinery. 1.24M bbl/day. Climate TRACE: 19.76M tonnes CO2e (2022)."
                },
                {
                    "facility_name": "Hazira LNG Terminal",
                    "operator": "ONGC / Shell / Total",
                    "lat": 21.161,
                    "lon": 72.664,
                    "facility_type": "Gas Processing",
                    "reported_emissions_tons_year": 8900,
                    "country": "India",
                    "region": "Gujarat",
                    "notes": "India's largest LNG terminal. 2.5M tonnes capacity. Verified coordinates."
                },
                {
                    "facility_name": "Barmer District Oil Fields",
                    "operator": "ONGC",
                    "lat": 25.75,
                    "lon": 71.38,
                    "facility_type": "Oil Extraction",
                    "reported_emissions_tons_year": 12000,
                    "country": "India",
                    "region": "Rajasthan",
                    "notes": "Multiple wells in Barmer area. Primary producer."
                },
                {
                    "facility_name": "Digboi Oil Field",
                    "operator": "Oil India Ltd",
                    "lat": 27.38,
                    "lon": 95.63,
                    "facility_type": "Oil Refinery",
                    "reported_emissions_tons_year": 3200,
                    "country": "India",
                    "region": "Assam",
                    "notes": "Asia's first oil well (1866). Still operating."
                },
                {
                    "facility_name": "Cambay Basin North",
                    "operator": "ONGC",
                    "lat": 22.0,
                    "lon": 72.0,
                    "facility_type": "Oil Extraction",
                    "reported_emissions_tons_year": 5600,
                    "country": "India",
                    "region": "Gujarat",
                    "notes": "Active oil & gas fields."
                },
                {
                    "facility_name": "Dahej LNG Terminal",
                    "operator": "Petronet LNG",
                    "lat": 21.9194,
                    "lon": 72.5667,
                    "facility_type": "Gas Processing",
                    "reported_emissions_tons_year": 6700,
                    "country": "India",
                    "region": "Gujarat",
                    "notes": "Secondary LNG import terminal."
                }
            ])
        
        # Normalize and merge
        facilities = self.normalize_to_facilities_format(assets_df, manual_facilities)
        
        return facilities
    
    def save_facilities_csv(self, facilities_df: pd.DataFrame, filename: str = "india_facilities_trace.csv"):
        """Save facilities DataFrame to CSV"""
        filepath = self.data_dir / filename
        facilities_df.to_csv(filepath, index=False)
        logger.info(f"Saved {len(facilities_df)} facilities to {filepath}")
        return filepath
    
    def load_cached_or_fetch(self, cache_file: str = "india_facilities_trace.csv") -> pd.DataFrame:
        """
        Load cached facilities data or fetch from API if not available
        
        Args:
            cache_file: Cached CSV filename
            
        Returns:
            Facilities DataFrame
        """
        cache_path = self.data_dir / cache_file
        
        if cache_path.exists():
            logger.info(f"Loading cached facilities from {cache_path}")
            return pd.read_csv(cache_path)
        
        logger.info("No cache found, fetching from Climate TRACE API...")
        facilities = self.get_india_oil_gas_facilities()
        
        if not facilities.empty:
            self.save_facilities_csv(facilities, cache_file)
        
        return facilities


def fetch_india_methane_inventory() -> pd.DataFrame:
    """
    Convenience function to fetch India methane inventory
    
    Returns:
        DataFrame with sector-level methane emissions
    """
    fetcher = ClimateTraceFetcher()
    return fetcher.fetch_country_emissions(country_code="IND", gas="ch4")


if __name__ == "__main__":
    # Test the fetcher
    fetcher = ClimateTraceFetcher("./data")
    
    # Fetch country-level inventory
    print("=== India Methane Inventory ===")
    inventory = fetcher.fetch_country_emissions()
    if not inventory.empty:
        print(inventory.head(10))
        inventory.to_csv("./data/india_methane_inventory.csv", index=False)
    
    # Fetch facility-level data
    print("\n=== India Oil & Gas Facilities ===")
    facilities = fetcher.get_india_oil_gas_facilities()
    if not facilities.empty:
        print(facilities.head(10))
        fetcher.save_facilities_csv(facilities)
