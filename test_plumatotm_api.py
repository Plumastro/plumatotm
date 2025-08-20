#!/usr/bin/env python3
"""
Test script for the PLUMATOTM API
"""

import requests
import json
import time

def test_api():
    base_url = "http://localhost:8000"
    
    print("🧪 Testing PLUMATOTM API...")
    
    # Test 1: Health check
    try:
        response = requests.get(f"{base_url}/health")
        print(f"✅ Health check: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return
    
    # Test 2: Get available animals
    try:
        response = requests.get(f"{base_url}/animals")
        print(f"✅ Animals endpoint: {response.status_code}")
        data = response.json()
        print(f"   Total animals: {data['total_count']}")
        print(f"   First 5 animals: {data['animals'][:5]}")
    except Exception as e:
        print(f"❌ Animals endpoint failed: {e}")
    
    # Test 3: Analyze birth data
    test_data = {
        "date": "1994-05-22",
        "time": "11:55",
        "lat": 47.75,
        "lon": 7.3333,
        "name": "Test Person"
    }
    
    try:
        response = requests.post(f"{base_url}/analyze", json=test_data)
        print(f"✅ Analysis endpoint: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print("   ✅ Analysis successful!")
                top_3 = data['data']['top_3_animals']
                print(f"   Top 3 animals:")
                for i, animal in enumerate(top_3, 1):
                    print(f"   {i}. {animal['ANIMAL']}: {animal['TOTAL_SCORE']:.1f}")
            else:
                print(f"   ❌ Analysis failed: {data['error']}")
        else:
            print(f"   ❌ HTTP error: {response.text}")
            
    except Exception as e:
        print(f"❌ Analysis endpoint failed: {e}")

if __name__ == "__main__":
    # Wait a moment for server to start
    print("⏳ Waiting for server to start...")
    time.sleep(3)
    test_api()
