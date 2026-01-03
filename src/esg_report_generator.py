"""
ESG Report Generator
Generates Net Zero alignment and ESG compliance reports using AI
"""

import json
from typing import Dict, List, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ESGReportGenerator:
    """
    Generates ESG/Net Zero compliance reports for detected emissions
    Frames analysis for Indian regulatory context (MoEFCC/CPCB)
    """
    
    # Indian regulatory context
    REGULATORY_FRAMEWORK = {
        "primary_authority": "MoEFCC (Ministry of Environment, Forest and Climate Change)",
        "monitoring_body": "CPCB (Central Pollution Control Board)",
        "reporting_requirement": "Business Responsibility and Sustainability Report (BRSR)",
        "net_zero_target": "India Net Zero by 2070",
        "methane_pledge": "Global Methane Pledge (30% reduction by 2030)"
    }
    
    # ESG rating thresholds
    ESG_THRESHOLDS = {
        "excellent": {"max_ratio": 1.5, "grade": "A", "color": "#22c55e"},
        "good": {"max_ratio": 2.0, "grade": "B", "color": "#84cc16"},
        "moderate": {"max_ratio": 3.0, "grade": "C", "color": "#eab308"},
        "poor": {"max_ratio": 5.0, "grade": "D", "color": "#f97316"},
        "critical": {"max_ratio": float("inf"), "grade": "F", "color": "#ef4444"}
    }
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Initialize ESG report generator
        
        Args:
            openai_api_key: OpenAI API key for GPT-4 report generation (optional)
        """
        self.openai_api_key = openai_api_key
        self.openai_client = None
        
        if openai_api_key:
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=openai_api_key)
                logger.info("OpenAI client initialized for ESG report generation")
            except ImportError:
                logger.warning("OpenAI package not installed. Install with: pip install openai")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
    
    def calculate_esg_grade(self, ratio: float) -> Dict:
        """
        Calculate ESG grade based on underreporting ratio
        
        Args:
            ratio: Underreporting ratio (satellite / reported)
            
        Returns:
            Dict with grade, description, and color
        """
        for level, thresholds in self.ESG_THRESHOLDS.items():
            if ratio <= thresholds["max_ratio"]:
                return {
                    "level": level,
                    "grade": thresholds["grade"],
                    "color": thresholds["color"],
                    "ratio": ratio
                }
        
        return {
            "level": "critical",
            "grade": "F",
            "color": "#ef4444",
            "ratio": ratio
        }
    
    def generate_facility_report(self, analysis_data: Dict) -> Dict:
        """
        Generate ESG compliance report for a single facility
        
        Args:
            analysis_data: Analysis results from UnderreportingAnalyzer
            
        Returns:
            Structured ESG report
        """
        ratio = analysis_data.get("primary_ratio", 1.0)
        esg_grade = self.calculate_esg_grade(ratio)
        
        report = {
            "facility_name": analysis_data.get("facility_name", "Unknown"),
            "operator": analysis_data.get("operator", "Unknown"),
            "facility_type": analysis_data.get("facility_type", "Unknown"),
            "assessment_date": datetime.now().isoformat(),
            
            # ESG Score
            "esg_rating": {
                "grade": esg_grade["grade"],
                "level": esg_grade["level"],
                "color": esg_grade["color"],
                "score": max(0, 100 - (ratio - 1) * 20)  # 0-100 scale
            },
            
            # Emissions Analysis
            "emissions_analysis": {
                "satellite_detected_kg": analysis_data.get("satellite_mass_kg", 0),
                "reported_annual_tons": analysis_data.get("reported_emissions_tons", 0),
                "discrepancy_ratio": ratio,
                "frequency_assumption": analysis_data.get("frequency_assumption", "moderate"),
                "confidence_score": analysis_data.get("confidence_score", 0)
            },
            
            # Net Zero Alignment
            "net_zero_alignment": self._assess_net_zero_alignment(ratio),
            
            # Regulatory Context
            "regulatory_context": self._get_regulatory_context(ratio),
            
            # Recommendations
            "recommendations": self._generate_recommendations(ratio, analysis_data),
            
            # Caveats
            "methodology_caveats": [
                "Satellite detection represents snapshot, not continuous monitoring",
                "Frequency assumption affects ratio calculation significantly",
                "Attribution confidence depends on facility proximity and density",
                "This is a screening tool, not regulatory evidence"
            ]
        }
        
        return report
    
    def _assess_net_zero_alignment(self, ratio: float) -> Dict:
        """Assess alignment with Net Zero targets"""
        if ratio <= 1.5:
            status = "ALIGNED"
            description = "Emissions reporting appears consistent with satellite observations. On track for Net Zero pathway."
        elif ratio <= 3.0:
            status = "AT RISK"
            description = "Moderate discrepancy detected. May require improved monitoring and reporting accuracy."
        else:
            status = "MISALIGNED"
            description = "Significant emissions discrepancy. Urgent action needed to align with Net Zero commitments."
        
        return {
            "status": status,
            "description": description,
            "india_2070_target": "Net Zero by 2070",
            "methane_pledge_2030": "30% reduction by 2030 (Global Methane Pledge)"
        }
    
    def _get_regulatory_context(self, ratio: float) -> Dict:
        """Get relevant regulatory context for India"""
        context = self.REGULATORY_FRAMEWORK.copy()
        
        if ratio > 3.0:
            context["compliance_risk"] = "HIGH"
            context["potential_actions"] = [
                "CPCB inspection may be warranted",
                "BRSR disclosure may require revision",
                "Investor ESG queries likely"
            ]
        elif ratio > 2.0:
            context["compliance_risk"] = "MODERATE"
            context["potential_actions"] = [
                "Enhanced monitoring recommended",
                "Voluntary disclosure improvement suggested"
            ]
        else:
            context["compliance_risk"] = "LOW"
            context["potential_actions"] = [
                "Continue current monitoring practices",
                "Consider third-party verification for ESG ratings"
            ]
        
        return context
    
    def _generate_recommendations(self, ratio: float, analysis_data: Dict) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if ratio > 5.0:
            recommendations.extend([
                "URGENT: Deploy continuous emissions monitoring system (CEMS)",
                "Conduct immediate leak detection and repair (LDAR) survey",
                "Engage third-party auditor for emissions verification",
                "Review and update emissions calculation methodology"
            ])
        elif ratio > 3.0:
            recommendations.extend([
                "Implement quarterly aerial/drone methane surveys",
                "Review emission factors used in inventory calculations",
                "Consider joining Oil & Gas Methane Partnership 2.0 (OGMP)"
            ])
        elif ratio > 1.5:
            recommendations.extend([
                "Enhance measurement accuracy at major emission points",
                "Document uncertainty ranges in emissions reporting"
            ])
        else:
            recommendations.extend([
                "Maintain current monitoring and reporting practices",
                "Consider publishing emissions data for transparency"
            ])
        
        return recommendations
    
    def generate_portfolio_summary(self, analysis_df) -> Dict:
        """
        Generate summary report for multiple facilities
        
        Args:
            analysis_df: DataFrame with analysis results
            
        Returns:
            Portfolio-level ESG summary
        """
        if analysis_df.empty:
            return {"error": "No analysis data provided"}
        
        ratios = analysis_df["primary_ratio"].values
        grades = [self.calculate_esg_grade(r) for r in ratios]
        
        grade_counts = {}
        for g in grades:
            grade = g["grade"]
            grade_counts[grade] = grade_counts.get(grade, 0) + 1
        
        return {
            "assessment_date": datetime.now().isoformat(),
            "total_facilities": len(analysis_df),
            "average_ratio": float(ratios.mean()),
            "median_ratio": float(analysis_df["primary_ratio"].median()),
            "max_ratio": float(ratios.max()),
            "grade_distribution": grade_counts,
            "facilities_above_3x": int((ratios >= 3.0).sum()),
            "facilities_above_5x": int((ratios >= 5.0).sum()),
            "portfolio_risk_level": "HIGH" if (ratios >= 3.0).mean() > 0.3 else "MODERATE" if (ratios >= 2.0).mean() > 0.3 else "LOW"
        }
    
    def generate_ai_narrative(self, report: Dict) -> str:
        """
        Generate AI-written narrative using GPT-4 (if available)
        
        Args:
            report: Structured report from generate_facility_report()
            
        Returns:
            Natural language narrative
        """
        if not self.openai_client:
            return self._generate_template_narrative(report)
        
        try:
            prompt = f"""You are an ESG analyst specializing in methane emissions in the Indian oil & gas sector.

Generate a professional, balanced ESG assessment narrative for the following facility:

Facility: {report['facility_name']}
Operator: {report['operator']}
Type: {report['facility_type']}
ESG Grade: {report['esg_rating']['grade']}
Emissions Discrepancy Ratio: {report['emissions_analysis']['discrepancy_ratio']:.1f}x

Context:
- Satellite detected: {report['emissions_analysis']['satellite_detected_kg']:.0f} kg methane
- Company reported: {report['emissions_analysis']['reported_annual_tons']:.0f} tons/year
- Net Zero Status: {report['net_zero_alignment']['status']}

Write a 3-paragraph assessment covering:
1. Current emissions status and discrepancy analysis
2. Implications for India's Net Zero 2070 target and Global Methane Pledge
3. Key recommendations for the operator

Use professional ESG language. Be balanced - acknowledge uncertainty in satellite measurements.
Frame for Indian regulatory context (MoEFCC/CPCB).
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional ESG analyst."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.warning(f"GPT-4 narrative generation failed: {e}")
            return self._generate_template_narrative(report)
    
    def _generate_template_narrative(self, report: Dict) -> str:
        """Generate template-based narrative (fallback when no API)"""
        grade = report["esg_rating"]["grade"]
        ratio = report["emissions_analysis"]["discrepancy_ratio"]
        facility = report["facility_name"]
        operator = report["operator"]
        
        if grade in ["A", "B"]:
            assessment = f"{facility} operated by {operator} demonstrates strong alignment between satellite-observed and reported methane emissions (ratio: {ratio:.1f}x). This suggests robust emissions monitoring and reporting practices."
        elif grade == "C":
            assessment = f"{facility} operated by {operator} shows moderate discrepancy between satellite observations and reported emissions (ratio: {ratio:.1f}x). While not critical, this indicates potential for improved measurement accuracy."
        else:
            assessment = f"{facility} operated by {operator} exhibits significant discrepancy between satellite-detected and reported methane emissions (ratio: {ratio:.1f}x). This raises concerns about reporting accuracy and Net Zero alignment."
        
        alignment = report["net_zero_alignment"]
        recommendations = "; ".join(report["recommendations"][:3])
        
        return f"""{assessment}

**Net Zero Alignment**: {alignment['status']} - {alignment['description']}

**Key Recommendations**: {recommendations}

*Note: This assessment is based on satellite snapshot data with inherent uncertainties. Frequency assumptions significantly affect ratio calculations. This is a screening tool for prioritization, not definitive regulatory evidence.*"""


def generate_esg_report(analysis_data: Dict, api_key: Optional[str] = None) -> Dict:
    """
    Convenience function to generate ESG report
    
    Args:
        analysis_data: Analysis results from UnderreportingAnalyzer
        api_key: Optional OpenAI API key
        
    Returns:
        Complete ESG report
    """
    generator = ESGReportGenerator(api_key)
    report = generator.generate_facility_report(analysis_data)
    report["narrative"] = generator.generate_ai_narrative(report)
    return report
