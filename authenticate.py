"""
CO2Watch India - Google Earth Engine Authentication
Run this script once to authenticate with Google Earth Engine.

This script handles:
1. One-time OAuth authentication
2. Initialization with project ID
3. Verification of TROPOMI data access
"""

import ee
import sys
import os


def authenticate_gee():
    """
    Authenticate with Google Earth Engine.
    Handles both initial auth and subsequent initializations.
    """
    print("🌍 CO2Watch India - GEE Authentication")
    print("=" * 50)
    print()
    
    try:
        # Try to initialize (works if already authenticated)
        ee.Initialize()
        print("✅ Already authenticated with Earth Engine!")
        print()
        test_collection()
        return True
        
    except Exception as initial_error:
        print("📋 Starting authentication process...")
        print("   A browser window will open for Google OAuth.")
        print("   You'll need a Google account.")
        print()
        
        try:
            # Trigger authentication
            ee.Authenticate()
            print()
            print("✅ Authentication complete!")
            print()
            
            # Now initialize - try with project first, fall back to default
            try:
                ee.Initialize()
            except Exception:
                # Try with a default project
                ee.Initialize(project='CO2Watch-India')
            
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
            print("1. Make sure you have a Google account (gmail.com or similar)")
            print("2. Register for Earth Engine: https://earthengine.google.com/signup/")
            print("3. Wait for approval (usually instant for .edu emails)")
            print("   Non-commercial users: ~24 hours")
            print("4. Try again after approval")
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
    success = authenticate_gee()
    sys.exit(0 if success else 1)
