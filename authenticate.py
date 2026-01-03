"""
CO2Watch India - Google Earth Engine Authentication
Run this script once to authenticate with Google Earth Engine.

IMPORTANT (2024+): GEE now REQUIRES a Google Cloud Project ID.
Before running this script:
1. Create a Google Cloud Project: https://console.cloud.google.com/
2. Enable Earth Engine API: https://console.cloud.google.com/apis/library/earthengine.googleapis.com
3. Register for Earth Engine: https://earthengine.google.com/signup/
"""

import ee
import sys
import os

# ========================================
# CONFIGURATION - SET YOUR PROJECT ID HERE
# ========================================
# Get your project ID from: https://console.cloud.google.com/
# It looks like: "my-project-12345" or "co2watch-india-123456"
GEE_PROJECT_ID = os.environ.get('GEE_PROJECT_ID', None)

# If you want to hardcode your project ID, uncomment and edit this line:
# GEE_PROJECT_ID = "your-project-id-here"


def authenticate_gee(project_id: str = None):
    """
    Authenticate with Google Earth Engine.
    
    Args:
        project_id: Google Cloud Project ID (REQUIRED since 2024)
    """
    print("🌍 CO2Watch India - GEE Authentication")
    print("=" * 50)
    print()
    
    # Determine project ID
    proj = project_id or GEE_PROJECT_ID
    
    if not proj:
        print("❌ ERROR: Google Cloud Project ID is REQUIRED")
        print()
        print("📋 Setup Steps:")
        print("1. Go to: https://console.cloud.google.com/")
        print("2. Create a new project (or select existing)")
        print("3. Copy your Project ID (looks like: my-project-12345)")
        print("4. Enable Earth Engine API:")
        print("   https://console.cloud.google.com/apis/library/earthengine.googleapis.com")
        print("5. Register for Earth Engine:")
        print("   https://earthengine.google.com/signup/")
        print()
        print("Then run one of these:")
        print("  Option A: Set environment variable:")
        print('    $Env:GEE_PROJECT_ID="your-project-id"; python authenticate.py')
        print()
        print("  Option B: Edit authenticate.py and set GEE_PROJECT_ID")
        print()
        return False
    
    print(f"📋 Using Project ID: {proj}")
    print()
    
    try:
        # Try to initialize (works if already authenticated)
        ee.Initialize(project=proj)
        print("✅ Already authenticated with Earth Engine!")
        print()
        test_collection()
        return True
        
    except Exception as initial_error:
        print("📋 Starting authentication process...")
        print("   A browser window will open for Google OAuth.")
        print()
        
        try:
            # Trigger authentication
            ee.Authenticate()
            print()
            print("✅ Authentication complete!")
            print()
            
            # Now initialize with project ID (REQUIRED)
            ee.Initialize(project=proj)
            
            print("✅ Earth Engine initialized!")
            print()
            
            # Test access
            test_collection()
            return True
            
        except Exception as auth_error:
            print()
            print("❌ Authentication failed")
            print()
            print("Troubleshooting steps:")
            print("1. Verify your Project ID is correct")
            print("2. Make sure Earth Engine API is enabled:")
            print("   https://console.cloud.google.com/apis/library/earthengine.googleapis.com")
            print("3. Register for Earth Engine: https://earthengine.google.com/signup/")
            print("4. Wait for approval if needed (usually instant)")
            print()
            print(f"Error details: {auth_error}")
            return False


def test_collection():
    """Test access to TROPOMI NO2 collection."""
    print("🧪 Testing TROPOMI NO2 data access...")
    
    try:
        # Load collection
        collection = ee.ImageCollection('COPERNICUS/S5P/OFFL/L3_NO2')
        
        # Get count
        count = collection.size().getInfo()
        
        # Get date range
        first = ee.Date(collection.first().get('system:time_start')).format('YYYY-MM-dd').getInfo()
        last = ee.Date(collection.sort('system:time_start', False).first().get('system:time_start')).format('YYYY-MM-dd').getInfo()
        
        print(f"   Collection: COPERNICUS/S5P/OFFL/L3_NO2")
        print(f"   Total images: {count:,}")
        print(f"   Date range: {first} to {last}")
        print()
        print("✅ TROPOMI data access confirmed!")
        print()
        print("🚀 You're ready to run CO2Watch India!")
        print("   Real data: python src/processing/detect_plumes.py")
        print("   Dashboard: streamlit run app.py")
        
    except Exception as e:
        print(f"⚠️ Collection test failed: {e}")
        print("   This may be a temporary issue. Try again later.")
        print("   You can still use demo mode: python src/processing/detect_plumes.py --demo")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Authenticate with Google Earth Engine')
    parser.add_argument('--project', '-p', type=str, help='Google Cloud Project ID')
    args = parser.parse_args()
    
    success = authenticate_gee(project_id=args.project)
    sys.exit(0 if success else 1)
