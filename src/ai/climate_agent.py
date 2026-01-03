"""
CO2Watch India - Climate Intelligence Agent
============================================
AI-powered compliance analysis, ESG report generation, and regulatory support
using FREE Groq API (Llama 3.3 70B / Mixtral 8x7B).

FREE TIER LIMITS (as of 2025):
- 30 requests/minute
- 14,400 requests/day
- No credit card required

Setup:
1. Get FREE API key at: https://console.groq.com/keys
2. Set environment variable: GROQ_API_KEY=your_key_here
"""

import os
import json
from datetime import datetime
from typing import Optional, Dict, List, Any

# Load environment variables from .env file FIRST
from dotenv import load_dotenv
load_dotenv()

# Check if groq is installed
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    Groq = None


class ClimateIntelligence:
    """
    AI-powered climate compliance and reporting agent.
    
    Features:
    - Compliance analysis against CPCB/MoEFCC regulations
    - ESG report generation
    - CPCB complaint letter drafting
    - Carbon credit estimation (Article 6 alignment)
    - Risk assessment and recommendations
    """
    
    # Indian Regulatory Framework
    REGULATIONS = {
        "CPCB": {
            "name": "Central Pollution Control Board",
            "thermal_limits": {
                "SO2": "100 mg/Nm³ (units <500MW), 200 mg/Nm³ (units ≥500MW)",
                "NOx": "100 mg/Nm³ (units <500MW)",
                "PM": "30 mg/Nm³",
                "Mercury": "0.03 mg/Nm³"
            },
            "deadlines": "December 2027 (extended)",
            "reference": "Environment Protection (Amendment) Rules, 2022"
        },
        "PAT": {
            "name": "Perform Achieve Trade Scheme",
            "description": "Energy efficiency trading for designated consumers",
            "thermal_target": "3-5% specific energy consumption reduction per cycle"
        },
        "NDC": {
            "name": "Nationally Determined Contribution",
            "targets": {
                "emissions_intensity": "45% reduction by 2030 (from 2005 levels)",
                "renewable": "50% cumulative electric power from non-fossil sources by 2030",
                "carbon_sink": "2.5-3 billion tonnes CO2 equivalent by 2030"
            }
        },
        "CCTS": {
            "name": "Carbon Credit Trading Scheme (2023)",
            "description": "India's emerging carbon market aligned with Paris Agreement Article 6",
            "authority": "Bureau of Energy Efficiency (BEE)"
        }
    }
    
    # System prompts for different tasks
    PROMPTS = {
        "compliance": """You are an expert environmental compliance analyst specializing in Indian thermal power plant regulations. 

REGULATORY FRAMEWORK:
- CPCB emission norms (SO2, NOx, PM limits)
- PAT Scheme for energy efficiency
- India's NDC commitments (45% emissions intensity reduction by 2030)
- CCTS 2023 (Carbon Credit Trading Scheme)

Analyze the provided emission data and provide:
1. COMPLIANCE STATUS (Compliant/Non-Compliant/At Risk)
2. SPECIFIC VIOLATIONS with regulatory references
3. RISK LEVEL (High/Medium/Low) with justification
4. ACTIONABLE RECOMMENDATIONS
5. ESTIMATED TIMELINE for compliance

Be specific, cite regulations, and provide practical recommendations.""",

        "esg_report": """You are an ESG (Environmental, Social, Governance) report writer for the power sector.

Generate a professional ESG disclosure section based on the satellite-verified emission data provided. Include:
1. ENVIRONMENTAL METRICS (emissions, efficiency)
2. REGULATORY COMPLIANCE STATUS
3. CLIMATE RISK ASSESSMENT
4. DECARBONIZATION PATHWAY
5. TCFD-ALIGNED DISCLOSURES

Use professional language suitable for investor relations and annual reports.
Reference India's NDC targets and CCTS alignment where relevant.""",

        "cpcb_complaint": """You are a legal expert drafting formal complaints to the Central Pollution Control Board (CPCB).

Draft a formal complaint letter based on satellite-verified emission data. Include:
1. COMPLAINANT DETAILS (placeholder)
2. RESPONDENT (power plant details)
3. FACTUAL BACKGROUND with satellite data evidence
4. ALLEGED VIOLATIONS with regulatory references
5. RELIEF SOUGHT
6. SUPPORTING EVIDENCE (satellite monitoring data)

Use formal legal language. Reference:
- Environment Protection Act, 1986
- Air (Prevention and Control of Pollution) Act, 1981
- CPCB emission norms for thermal power plants""",

        "carbon_credit": """You are a carbon market analyst specializing in India's CCTS and Article 6 mechanisms.

Based on the emission data provided, analyze:
1. CARBON CREDIT POTENTIAL (estimated tonnes CO2e)
2. CCTS ELIGIBILITY under Indian framework
3. ARTICLE 6.4 MECHANISM alignment
4. MONETIZATION POTENTIAL (current carbon prices)
5. RECOMMENDATIONS for credit generation

Reference India's CCTS 2023 framework and international carbon markets.""",

        "summary": """You are a climate data analyst. Provide a concise, actionable summary of the emission monitoring data.

Include:
1. KEY FINDINGS (2-3 bullet points)
2. HIGHEST PRIORITY CONCERN
3. IMMEDIATE ACTION REQUIRED
4. TREND ANALYSIS

Be brief but impactful. Use data-driven insights."""
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Climate Intelligence agent.
        
        Args:
            api_key: Groq API key. If not provided, reads from GROQ_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.client = None
        self.model = "llama-3.3-70b-versatile"  # Best FREE model on Groq
        self.fallback_model = "mixtral-8x7b-32768"  # Backup model
        
        if GROQ_AVAILABLE and self.api_key:
            try:
                self.client = Groq(api_key=self.api_key)
            except Exception as e:
                print(f"⚠️ Groq initialization failed: {e}")
                self.client = None
    
    @property
    def is_available(self) -> bool:
        """Check if AI capabilities are available."""
        return self.client is not None
    
    def _format_detection_data(self, detections: List[Dict]) -> str:
        """Format detection data for LLM context."""
        if not detections:
            return "No detection data available."
        
        formatted = "## Satellite Emission Detection Data\n\n"
        formatted += "| Plant | State | Capacity (MW) | CO2 (tonnes/day) | Confidence | Date |\n"
        formatted += "|-------|-------|---------------|------------------|------------|------|\n"
        
        for d in detections:
            formatted += f"| {d.get('plant_name', 'Unknown')} | {d.get('state', 'N/A')} | "
            formatted += f"{d.get('capacity_mw', 'N/A')} | {d.get('co2_tonnes_day', 'N/A'):,.0f} | "
            formatted += f"{d.get('confidence', 'N/A')} | {d.get('detection_date', 'N/A')} |\n"
        
        # Add summary stats
        total_co2 = sum(d.get('co2_tonnes_day', 0) for d in detections)
        high_confidence = sum(1 for d in detections if d.get('confidence') == 'HIGH')
        
        formatted += f"\n**Total Daily Emissions:** {total_co2:,.0f} tonnes CO2\n"
        formatted += f"**High Confidence Detections:** {high_confidence}/{len(detections)}\n"
        formatted += f"**Monitoring Date Range:** {detections[0].get('detection_date', 'N/A')}\n"
        
        return formatted
    
    def _call_llm(self, system_prompt: str, user_content: str, max_tokens: int = 2000) -> str:
        """
        Call Groq LLM with fallback handling.
        
        Args:
            system_prompt: System instructions
            user_content: User query/data
            max_tokens: Maximum response tokens
            
        Returns:
            LLM response text or error message
        """
        if not self.is_available:
            return self._get_demo_response(system_prompt)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                max_tokens=max_tokens,
                temperature=0.3  # Lower temperature for factual responses
            )
            return response.choices[0].message.content
            
        except Exception as e:
            # Try fallback model
            try:
                response = self.client.chat.completions.create(
                    model=self.fallback_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content}
                    ],
                    max_tokens=max_tokens,
                    temperature=0.3
                )
                return response.choices[0].message.content
            except Exception as e2:
                return f"⚠️ AI analysis unavailable: {str(e2)}"
    
    def _get_demo_response(self, prompt_type: str) -> str:
        """Generate demo response when API is not available."""
        demo_responses = {
            "compliance": """## 🔍 Compliance Analysis (DEMO MODE)

**Status:** ⚠️ REQUIRES ATTENTION

### Key Findings:
1. **Vindhyachal STPS** - HIGH emissions detected (15,234 tonnes CO2/day)
   - Exceeds expected baseline by 23%
   - CPCB SO2 norm compliance deadline: Dec 2027
   
2. **Mundra UMPP** - MEDIUM concern
   - Emission levels within normal range
   - FGD installation status: In progress

### Regulatory References:
- CPCB Notification S.O. 3305(E), Dec 2015
- Environment Protection (Amendment) Rules, 2022

### Recommendations:
1. Prioritize FGD installation at high-emission units
2. Implement real-time CEMS integration
3. Submit PAT Cycle VII compliance report

---
*🤖 Demo Mode - Connect Groq API for live analysis*
*Get FREE key: https://console.groq.com/keys*""",

            "esg_report": """## 📊 ESG Report Section (DEMO MODE)

### Environmental Performance - Thermal Fleet

**Scope 1 Emissions (Satellite-Verified)**
| Metric | Value | YoY Change |
|--------|-------|------------|
| Total CO2 | 89,456 tonnes/day | +3.2% |
| Emission Intensity | 0.89 tCO2/MWh | -1.1% |
| Capacity Utilization | 67% | +5% |

### Climate Risk Assessment
- **Physical Risk:** Medium (water stress at 3 locations)
- **Transition Risk:** High (CCTS 2023 exposure)
- **Regulatory Risk:** Medium (FGD deadline Dec 2027)

### NDC Alignment
Our thermal portfolio contributes to India's 45% emissions intensity reduction target through:
- 12% improvement in heat rate (2020-2025)
- 2,400 MW under renovation/modernization
- 500 MW biomass co-firing pilot

---
*🤖 Demo Mode - Connect Groq API for customized reports*
*Get FREE key: https://console.groq.com/keys*""",

            "cpcb_complaint": """## 📝 CPCB Complaint Draft (DEMO MODE)

**BEFORE THE CENTRAL POLLUTION CONTROL BOARD**
**COMPLAINT UNDER SECTION 19 OF THE AIR ACT, 1981**

---

**COMPLAINANT:** [Your Name/Organization]

**RESPONDENT:** [Power Plant Name], [Location]

---

### FACTUAL BACKGROUND

1. The Complainant has obtained satellite-based emission monitoring data from ESA Sentinel-5P TROPOMI sensor for the period [Date Range].

2. Analysis reveals emission levels of approximately [X] tonnes CO2/day, which corresponds to elevated NO2 concentrations of [Y] µmol/m².

3. The detected emission levels exceed the expected baseline for a plant of this capacity by approximately [Z]%.

### ALLEGED VIOLATIONS

1. Non-compliance with emission norms under Environment Protection (Amendment) Rules, 2022
2. Failure to install/operate Flue Gas Desulphurization (FGD) as per CPCB timeline
3. Inadequate Continuous Emission Monitoring System (CEMS) reporting

### RELIEF SOUGHT

[Specific remedies requested]

---
*🤖 Demo Mode - Connect Groq API for complete drafts*
*Get FREE key: https://console.groq.com/keys*""",

            "carbon_credit": """## 💰 Carbon Credit Analysis (DEMO MODE)

### CCTS 2023 Eligibility Assessment

**Plant Portfolio Analysis:**
| Plant | Baseline | Actual | Gap (tCO2) | Credit Potential |
|-------|----------|--------|------------|------------------|
| Vindhyachal | 14,000 | 15,234 | -1,234 | ❌ Deficit |
| Sasan | 8,500 | 7,892 | +608 | ✅ 608 credits |
| Mundra | 9,200 | 8,456 | +744 | ✅ 744 credits |

### Estimated Value
- **Net Credit Position:** 118 credits (after deficits)
- **CCTS Price (est.):** ₹1,500-2,500/tCO2e
- **Potential Value:** ₹1.77-2.95 lakhs/day

### Article 6 Alignment
- ITMO eligibility: Under review
- Corresponding adjustments: Required
- BEE registration: Mandatory

---
*🤖 Demo Mode - Connect Groq API for live pricing*
*Get FREE key: https://console.groq.com/keys*""",

            "summary": """## 📋 Emission Summary (DEMO MODE)

### Key Findings
- 🔴 **3 plants** showing elevated emissions (>20% above baseline)
- 🟡 **4 plants** within normal operating range
- 🟢 **3 plants** below baseline (potential carbon credits)

### Highest Priority
**Vindhyachal STPS** requires immediate attention - highest absolute emissions in portfolio

### Recommended Action
Deploy mobile CEMS verification within 7 days

---
*🤖 Demo Mode - Get FREE Groq API key for live analysis*
*https://console.groq.com/keys*"""
        }
        
        # Match prompt type
        for key in demo_responses:
            if key in prompt_type.lower():
                return demo_responses[key]
        
        return demo_responses["summary"]
    
    def analyze_compliance(self, detections: List[Dict], 
                          plant_name: Optional[str] = None) -> str:
        """
        Analyze emission data against Indian regulatory requirements.
        
        Args:
            detections: List of detection dictionaries
            plant_name: Optional specific plant to analyze
            
        Returns:
            Compliance analysis report
        """
        data = self._format_detection_data(detections)
        
        query = f"""Analyze the following satellite-detected emission data for compliance with Indian regulations:

{data}

{"Focus specifically on: " + plant_name if plant_name else "Analyze all plants in the dataset."}

Provide a detailed compliance assessment."""
        
        return self._call_llm(self.PROMPTS["compliance"], query)
    
    def generate_esg_report(self, detections: List[Dict], 
                           company_name: str = "Power Generation Company") -> str:
        """
        Generate ESG report section based on emission data.
        
        Args:
            detections: List of detection dictionaries
            company_name: Company name for the report
            
        Returns:
            ESG report section
        """
        data = self._format_detection_data(detections)
        
        query = f"""Generate an ESG report section for {company_name} based on this satellite-verified emission data:

{data}

The report should be suitable for:
- Annual sustainability reports
- Investor disclosures
- TCFD-aligned reporting
- BRSR (Business Responsibility and Sustainability Reporting) compliance"""
        
        return self._call_llm(self.PROMPTS["esg_report"], query, max_tokens=3000)
    
    def draft_cpcb_complaint(self, detections: List[Dict], 
                            target_plant: str,
                            complainant_name: str = "[Your Name]") -> str:
        """
        Draft a formal complaint to CPCB based on satellite evidence.
        
        Args:
            detections: List of detection dictionaries
            target_plant: Name of the plant to complain about
            complainant_name: Name of the complainant
            
        Returns:
            Formal complaint letter draft
        """
        # Filter to specific plant
        plant_data = [d for d in detections if d.get('plant_name') == target_plant]
        if not plant_data:
            plant_data = detections[:1]  # Use first if not found
        
        data = self._format_detection_data(plant_data)
        
        query = f"""Draft a formal CPCB complaint for:

**Complainant:** {complainant_name}
**Target Plant:** {target_plant}

**Satellite Evidence:**
{data}

Generate a complete, formal complaint letter ready for submission."""
        
        return self._call_llm(self.PROMPTS["cpcb_complaint"], query, max_tokens=3000)
    
    def estimate_carbon_credits(self, detections: List[Dict]) -> str:
        """
        Estimate carbon credit potential under CCTS 2023.
        
        Args:
            detections: List of detection dictionaries
            
        Returns:
            Carbon credit analysis
        """
        data = self._format_detection_data(detections)
        
        query = f"""Analyze carbon credit potential based on this emission data:

{data}

Consider:
1. CCTS 2023 framework
2. PAT Scheme ESCerts
3. Article 6.4 mechanism potential
4. Current carbon prices (India and international)"""
        
        return self._call_llm(self.PROMPTS["carbon_credit"], query)
    
    def get_summary(self, detections: List[Dict]) -> str:
        """
        Get a quick summary of emission monitoring data.
        
        Args:
            detections: List of detection dictionaries
            
        Returns:
            Brief summary with key findings
        """
        data = self._format_detection_data(detections)
        
        query = f"""Provide a brief executive summary of this emission monitoring data:

{data}

Focus on actionable insights for decision-makers."""
        
        return self._call_llm(self.PROMPTS["summary"], query, max_tokens=500)
    
    def custom_query(self, detections: List[Dict], question: str) -> str:
        """
        Answer a custom question about the emission data.
        
        Args:
            detections: List of detection dictionaries
            question: User's question
            
        Returns:
            AI response to the question
        """
        data = self._format_detection_data(detections)
        
        system = """You are an expert climate and environmental analyst. 
Answer questions about emission monitoring data accurately and concisely.
Reference Indian regulations (CPCB, PAT, NDC, CCTS) where relevant.
Always base your answers on the provided satellite data."""
        
        query = f"""Based on this satellite emission data:

{data}

**Question:** {question}"""
        
        return self._call_llm(system, query)


# Utility function for quick access
def get_ai_agent(api_key: Optional[str] = None) -> ClimateIntelligence:
    """
    Get a ClimateIntelligence agent instance.
    
    Args:
        api_key: Optional Groq API key
        
    Returns:
        ClimateIntelligence instance
    """
    return ClimateIntelligence(api_key)


# Demo usage
if __name__ == "__main__":
    # Demo data
    demo_detections = [
        {
            "plant_name": "Vindhyachal STPS",
            "state": "Madhya Pradesh",
            "capacity_mw": 4760,
            "co2_tonnes_day": 15234,
            "confidence": "HIGH",
            "detection_date": "2025-12-28"
        },
        {
            "plant_name": "Mundra UMPP",
            "state": "Gujarat",
            "capacity_mw": 4620,
            "co2_tonnes_day": 8456,
            "confidence": "HIGH",
            "detection_date": "2025-12-28"
        }
    ]
    
    agent = ClimateIntelligence()
    
    print("=" * 60)
    print("CO2Watch India - Climate Intelligence Agent")
    print("=" * 60)
    print(f"\n🤖 AI Available: {agent.is_available}")
    
    if not agent.is_available:
        print("\n⚠️ Running in DEMO MODE")
        print("To enable AI: Set GROQ_API_KEY environment variable")
        print("Get FREE key: https://console.groq.com/keys")
    
    print("\n" + "=" * 60)
    print("Sample Compliance Analysis:")
    print("=" * 60)
    print(agent.analyze_compliance(demo_detections))
