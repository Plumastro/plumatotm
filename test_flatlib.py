#!/usr/bin/env python3
"""
Test script to diagnose flatlib import issues
"""

print("🔍 Testing flatlib import...")

try:
    import flatlib
    print("✅ flatlib module imported successfully")
    print(f"   flatlib version: {flatlib.__version__ if hasattr(flatlib, '__version__') else 'unknown'}")
except ImportError as e:
    print(f"❌ Failed to import flatlib: {e}")
    exit(1)

try:
    from flatlib import const
    print("✅ flatlib.const imported successfully")
except ImportError as e:
    print(f"❌ Failed to import flatlib.const: {e}")
    exit(1)

try:
    from flatlib.chart import Chart
    print("✅ flatlib.chart.Chart imported successfully")
except ImportError as e:
    print(f"❌ Failed to import flatlib.chart.Chart: {e}")
    exit(1)

try:
    from flatlib.datetime import Datetime
    print("✅ flatlib.datetime.Datetime imported successfully")
except ImportError as e:
    print(f"❌ Failed to import flatlib.datetime.Datetime: {e}")
    exit(1)

try:
    from flatlib.geopos import GeoPos
    print("✅ flatlib.geopos.GeoPos imported successfully")
except ImportError as e:
    print(f"❌ Failed to import flatlib.geopos.GeoPos: {e}")
    exit(1)

try:
    from flatlib.object import Object
    print("✅ flatlib.object.Object imported successfully")
except ImportError as e:
    print(f"❌ Failed to import flatlib.object.Object: {e}")
    exit(1)

print("🎉 All flatlib imports successful!")
