"""
Underreporting Ratio Calculation Module
Compares satellite-detected emissions against company-reported emissions
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UnderreportingAnalyzer:
    """
    Analyzes potential underreporting based on satellite vs reported emissions
    """
    
    def __init__(self):
        """Initialize underreporting analyzer"""
        self.results = []
    
    def estimate_plume_mass_kg(
        self,
        ch4_enhancement_ppm_m: float,
        plume_area_km2: float = 1.0,
        plume_height_m: float = 100.0
    ) -> float:
        """
        Estimate mass of methane in a detected plume
        
        MAJOR CAVEAT: This is a VERY ROUGH estimate with large uncertainty (±10x)
        
        Args:
            ch4_enhancement_ppm_m: CH4 enhancement in ppm·m (integrated column)
            plume_area_km2: Plume area in km² (defaults to 1 km² if unknown)
            plume_height_m: Boundary layer height (default 100m)
            
        Returns:
            Estimated plume mass in kg
            
        NOTE: ppm·m is an integrated measurement, so height is approximate
        """
        # Convert ppm·m to mass
        # 1 ppm·m of methane ≈ 0.72 kg/km² (at STP, approximate)
        conversion_factor = 0.72
        
        mass_per_km2 = ch4_enhancement_ppm_m * conversion_factor
        total_mass_kg = mass_per_km2 * plume_area_km2
        
        return total_mass_kg
    
    def calculate_underreporting_ratio(
        self,
        satellite_detection_kg: float,
        reported_annual_tons: float,
        frequency_assumption: str = "moderate"
    ) -> Dict:
        """
        Calculate underreporting ratio with different frequency assumptions
        
        CRITICAL LIMITATION: Cannot determine leak frequency from single detection!
        
        Args:
            satellite_detection_kg: Estimated mass from single plume detection
            reported_annual_tons: Company's reported annual emissions (metric tons)
            frequency_assumption: One of "conservative", "moderate", "aggressive"
                - conservative: assumes single annual event
                - moderate: assumes monthly occurrence
                - aggressive: assumes daily occurrence
            
        Returns:
            Dictionary with ratio calculations and interpretations
        """
        # Convert reported to kg
        reported_kg = reported_annual_tons * 1000.0
        
        # Avoid division by zero
        if reported_kg == 0:
            reported_kg = 1.0
        
        # Calculate ratios under different frequency assumptions
        ratios = {
            'single_event': satellite_detection_kg / reported_kg,
            'monthly': (satellite_detection_kg * 12) / reported_kg,
            'weekly': (satellite_detection_kg * 52) / reported_kg,
            'daily': (satellite_detection_kg * 365) / reported_kg
        }
        
        # Select primary ratio based on assumption
        assumption_map = {
            'conservative': 'single_event',
            'moderate': 'monthly',
            'aggressive': 'weekly'
        }
        
        primary_assumption = assumption_map.get(frequency_assumption, 'monthly')
        primary_ratio = ratios[primary_assumption]
        
        return {
            'satellite_mass_kg': satellite_detection_kg,
            'reported_annual_tons': reported_annual_tons,
            'reported_annual_kg': reported_kg,
            'frequency_assumption': frequency_assumption,
            'primary_ratio': primary_ratio,
            'all_ratios': ratios,
            'interpretation': self._interpret_ratio(primary_ratio)
        }
    
    def _interpret_ratio(self, ratio: float) -> str:
        """
        Interpret underreporting ratio
        
        Args:
            ratio: Calculated ratio
            
        Returns:
            Human-readable interpretation
        """
        if ratio < 1.0:
            return "Detection within reported range - appears accurate"
        elif ratio < 1.5:
            return "Marginal discrepancy - likely within measurement uncertainty"
        elif ratio < 3.0:
            return "Moderate discrepancy - possible underreporting"
        elif ratio < 10.0:
            return "Severe discrepancy - significant underreporting indicated"
        else:
            return "Critical discrepancy - major underreporting or data quality issue"
    
    def analyze_match(self, match_data: Dict, frequency_assumption: str = "moderate") -> Dict:
        """
        Perform complete underreporting analysis on a plume-facility match
        
        Args:
            match_data: Dictionary with match information
                Required keys: ch4_enhancement_ppm_m, reported_emissions_tons
                
        Returns:
            Dictionary with full analysis results
        """
        # Estimate plume mass
        mass_kg = self.estimate_plume_mass_kg(
            match_data.get('ch4_enhancement_ppm_m', 0),
            plume_area_km2=match_data.get('plume_area_km2', 1.0)
        )
        
        # Calculate ratios
        analysis = self.calculate_underreporting_ratio(
            mass_kg,
            match_data.get('reported_emissions_tons', 1),
            frequency_assumption=frequency_assumption
        )
        
        # Add match context
        analysis['facility_name'] = match_data.get('facility_name', 'Unknown')
        analysis['facility_type'] = match_data.get('facility_type', 'Unknown')
        analysis['distance_km'] = match_data.get('distance_km', 0)
        analysis['confidence_score'] = match_data.get('confidence_score', 0)
        analysis['date'] = match_data.get('date', 'Unknown')
        
        self.results.append(analysis)
        return analysis
    
    def analyze_matches_batch(self, matches_df: pd.DataFrame, frequency_assumption: str = "moderate") -> pd.DataFrame:
        """
        Analyze multiple plume-facility matches
        
        Args:
            matches_df: DataFrame with matched plume-facility pairs
            
        Returns:
            DataFrame with analysis results
        """
        analyses = []
        
        for idx, match in matches_df.iterrows():
            analysis = self.analyze_match(match.to_dict(), frequency_assumption)
            analyses.append(analysis)
        
        results_df = pd.DataFrame(analyses)
        logger.info(f"Completed analysis of {len(results_df)} matches")
        
        return results_df
    
    def flag_potential_violators(
        self,
        analysis_df: pd.DataFrame,
        ratio_threshold: float = 3.0
    ) -> pd.DataFrame:
        """
        Flag facilities with concerning underreporting ratios
        
        Args:
            analysis_df: DataFrame from analyze_matches_batch()
            ratio_threshold: Ratio above which to flag (default 3.0x)
            
        Returns:
            Filtered DataFrame of flagged facilities
        """
        flagged = analysis_df[analysis_df['primary_ratio'] >= ratio_threshold].copy()
        flagged['risk_level'] = flagged['primary_ratio'].apply(
            lambda x: 'HIGH' if x >= 10 else ('MEDIUM' if x >= 5 else 'LOW')
        )
        
        logger.info(f"Flagged {len(flagged)} facilities for potential underreporting")
        return flagged.sort_values('primary_ratio', ascending=False)
    
    def generate_summary_statistics(self, analysis_df: pd.DataFrame) -> Dict:
        """
        Generate summary statistics for all analyses
        
        Args:
            analysis_df: DataFrame from analyze_matches_batch()
            
        Returns:
            Dictionary with summary statistics
        """
        return {
            'total_matches': len(analysis_df),
            'mean_ratio': analysis_df['primary_ratio'].mean(),
            'median_ratio': analysis_df['primary_ratio'].median(),
            'max_ratio': analysis_df['primary_ratio'].max(),
            'min_ratio': analysis_df['primary_ratio'].min(),
            'std_ratio': analysis_df['primary_ratio'].std(),
            'matches_above_3x': len(analysis_df[analysis_df['primary_ratio'] >= 3]),
            'matches_above_5x': len(analysis_df[analysis_df['primary_ratio'] >= 5]),
            'matches_above_10x': len(analysis_df[analysis_df['primary_ratio'] >= 10])
        }
