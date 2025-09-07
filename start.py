#!/usr/bin/env python3
"""
Startup script for Render deployment
Tests all imports before starting the Flask app
"""

import sys
import os

print("🚀 Starting PLUMATOTM API...")
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")

# Test critical imports
print("\n🔍 Testing critical imports...")

try:
    import flatlib
    print(f"✅ flatlib: {getattr(flatlib, '__version__', 'unknown')}")
except ImportError as e:
    print(f"❌ flatlib import failed: {e}")
    sys.exit(1)

try:
    import flask
    print(f"✅ flask: {flask.__version__}")
except ImportError as e:
    print(f"❌ flask import failed: {e}")
    sys.exit(1)

try:
    import pandas
    print(f"✅ pandas: {pandas.__version__}")
except ImportError as e:
    print(f"❌ pandas import failed: {e}")
    sys.exit(1)

try:
    import numpy
    print(f"✅ numpy: {numpy.__version__}")
except ImportError as e:
    print(f"❌ numpy import failed: {e}")
    sys.exit(1)

try:
    import matplotlib
    print(f"✅ matplotlib: {matplotlib.__version__}")
except ImportError as e:
    print(f"❌ matplotlib import failed: {e}")
    sys.exit(1)

# Test plumatotm_core import
print("\n🔍 Testing plumatotm_core import...")
try:
    import plumatotm_core
    print("✅ plumatotm_core imported successfully")
except ImportError as e:
    print(f"❌ plumatotm_core import failed: {e}")
    sys.exit(1)

# Test main import
print("\n🔍 Testing main import...")
try:
    import main
    print("✅ main imported successfully")
except ImportError as e:
    print(f"❌ main import failed: {e}")
    sys.exit(1)

print("\n🎉 All imports successful! Starting Flask app...")

# Start the Flask app
if __name__ == "__main__":
    from main import app, initialize_analyzer
    
    # Initialize analyzer
    if initialize_analyzer():
        print("✅ API ready to serve requests")
        # Get port from environment (Render sets PORT)
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port, debug=False)
    else:
        print("❌ Failed to start API - analyzer initialization failed")
        sys.exit(1)
