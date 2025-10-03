#!/usr/bin/env python3
"""
Test simple pour l'API PLUMATOTM avec la nouvelle fonctionnalite PLANETARY POSITIONS SUMMARY
"""

import requests
import json

def test_api():
    """Test the API endpoints"""
    base_url = "http://localhost:5000"
    
    print("Testing PLUMATOTM API...")
    
    # Test home endpoint
    print("\n1. Testing home endpoint...")
    try:
        response = requests.get(f"{base_url}/")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("Home endpoint OK")
        else:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test health endpoint
    print("\n2. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"Analyzer ready: {health_data.get('analyzer_ready', False)}")
        else:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test analysis endpoint
    print("\n3. Testing analysis endpoint...")
    test_data = {
        "name": "Test User",
        "date": "1995-11-17",
        "time": "12:12",
        "lat": 45.7578137,
        "lon": 4.8320114,
        "country": "France",
        "state": "Auvergne-Rhone-Alpes",
        "city": "Lyon"
    }
    
    try:
        response = requests.post(
            f"{base_url}/analyze",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("Analysis completed successfully!")
            
            # Check if PLANETARY POSITIONS SUMMARY is present
            if "PLANETARY POSITIONS SUMMARY" in result:
                planetary_summary = result["PLANETARY POSITIONS SUMMARY"]
                print(f"PLANETARY POSITIONS SUMMARY found with {len(planetary_summary)} entries")
                
                # Show first few entries
                print("\nFirst 3 planetary positions:")
                for i, entry in enumerate(planetary_summary[:3]):
                    print(f"{i+1}. {entry['PLANETE']}: {entry['SIGNE']} {entry['ANGLE']} - {entry['MAISON']}")
                
                # Verify structure
                required_fields = ["PLANETE", "DESCRIPTION", "SIGNE", "ANGLE", "MAISON", "MAISON EXPLICATION"]
                all_fields_present = True
                for entry in planetary_summary:
                    for field in required_fields:
                        if field not in entry:
                            print(f"Missing field: {field}")
                            all_fields_present = False
                            break
                    if not all_fields_present:
                        break
                
                if all_fields_present:
                    print("All required fields present in PLANETARY POSITIONS SUMMARY")
                else:
                    print("Some required fields missing")
                    
            else:
                print("PLANETARY POSITIONS SUMMARY NOT FOUND in response!")
            
            # Save full response for inspection
            with open("api_test_response.json", "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print("Full response saved to api_test_response.json")
            
        else:
            print(f"Error response: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api()
