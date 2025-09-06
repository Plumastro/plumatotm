#!/usr/bin/env python3
"""
Setup Swiss Ephemeris files for astrological calculations
"""

import os
import shutil
import pyswisseph as swe

def setup_ephemeris():
    """Setup Swiss Ephemeris files"""
    
    print("🔧 Setting up Swiss Ephemeris files...")
    
    # Get the path where pyswisseph is installed
    try:
        swe_path = os.path.dirname(swe.__file__)
        print(f"📁 pyswisseph path: {swe_path}")
        
        # Look for ephemeris files in the package
        possible_paths = [
            os.path.join(swe_path, "ephe"),
            os.path.join(swe_path, "sweph"),
            os.path.join(swe_path, "data"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                print(f"✅ Found ephemeris directory: {path}")
                files = os.listdir(path)
                print(f"📋 Found {len(files)} files")
                return path
        
        # If no ephemeris files found, create a minimal setup
        print("⚠️  No ephemeris files found in pyswisseph package")
        print("💡 This might work with basic calculations")
        
        return None
        
    except Exception as e:
        print(f"❌ Error setting up ephemeris: {e}")
        return None

def test_swisseph():
    """Test if Swiss Ephemeris works"""
    try:
        print("🧪 Testing Swiss Ephemeris...")
        
        # Test basic calculation
        jd = swe.julday(2000, 1, 1, 12.0, swe.GREG_CAL)
        print(f"✅ Julian day calculation works: {jd}")
        
        # Test planet position
        xx, ret = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH)
        if ret >= 0:
            print(f"✅ Planet calculation works: Sun longitude = {xx[0]}")
        else:
            print(f"⚠️  Planet calculation returned error: {ret}")
        
        return True
        
    except Exception as e:
        print(f"❌ Swiss Ephemeris test failed: {e}")
        return False

if __name__ == "__main__":
    setup_ephemeris()
    test_swisseph()
