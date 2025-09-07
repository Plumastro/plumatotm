#!/usr/bin/env python3
"""
Test script for PLUMATOTM API
"""

import requests
import json

def test_api():
    """Test the API endpoints"""
    base_url = "http://localhost:5000"  # Change to your Render URL when deployed
    
    print("🧪 Testing PLUMATOTM API...")
    
    # Test home endpoint
    print("\n1. Testing home endpoint...")
    try:
        response = requests.get(f"{base_url}/")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test health endpoint
    print("\n2. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test analysis endpoint
    print("\n3. Testing analysis endpoint...")
    test_data = {
        "date": "1998-12-22",
        "time": "10:13",
        "lat": 42.35843,
        "lon": -71.05977
    }
    
    try:
        response = requests.post(
            f"{base_url}/analyze",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test files endpoint
    print("\n4. Testing files endpoint...")
    try:
        response = requests.get(f"{base_url}/files")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api()
