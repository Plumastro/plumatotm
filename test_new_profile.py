#!/usr/bin/env python3
"""
Test script for the new profile with updated CSV scores
"""

import json
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from plumatotm_core import BirthChartAnalyzer
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def test_profile():
    """Test the engine with the new profile data"""
    
    # Test profile data
    profile = {
        "name": "Gui",
        "date": "1995-04-06",
        "time": "12:30",
        "lat": 45.74846,
        "lon": 4.84671,
        "country": "",
        "state": ""
    }
    
    print("🧪 TESTING PLUMATOTM ENGINE WITH NEW PROFILE")
    print("=" * 50)
    print(f"👤 Name: {profile['name']}")
    print(f"📅 Date: {profile['date']}")
    print(f"🕐 Time: {profile['time']}")
    print(f"📍 Location: {profile['lat']}, {profile['lon']}")
    print("=" * 50)
    
    try:
        # Initialize analyzer with updated CSV
        print("🔄 Initializing analyzer with updated CSV...")
        analyzer = BirthChartAnalyzer(
            scores_csv_path="plumatotm_raw_scores_trad.csv",
            weights_csv_path="plumatotm_planets_weights.csv",
            multipliers_csv_path="plumatotm_planets_multiplier.csv"
        )
        print("✅ Analyzer initialized successfully")
        
        # Run analysis
        print("\n🔄 Running analysis...")
        result = analyzer.run_analysis(
            date=profile['date'],
            time=profile['time'],
            lat=profile['lat'],
            lon=profile['lon'],
            user_name=profile['name'],
            openai_api_key=None  # Skip ChatGPT for faster testing
        )
        
        if result and result.get('success'):
            print("\n✅ ANALYSIS SUCCESSFUL!")
            print("=" * 30)
            print(f"🎯 Top 1 Animal (EN): {result.get('top1_animal', 'Unknown')}")
            print(f"🎯 Top 1 Animal (FR): {result.get('top1_animal_fr', 'Unknown')}")
            print(f"📊 Top 1 Score: {result.get('top1_score', 0)}")
            print(f"🆔 PlumID: {result.get('plumid', 'Unknown')}")
            
            # Show top 3 animals if available
            if 'top3_animals' in result:
                print(f"\n🏆 Top 3 Animals:")
                for i, animal in enumerate(result['top3_animals'][:3], 1):
                    score = result.get('top3_scores', [])[i-1] if i-1 < len(result.get('top3_scores', [])) else 0
                    print(f"   {i}. {animal} (Score: {score})")
            
            # Show some statistics
            if 'animal_totals' in result:
                print(f"\n📊 Total animals processed: {len(result['animal_totals'])}")
            
            return True
            
        else:
            print("\n❌ ANALYSIS FAILED!")
            error = result.get('error', 'Unknown error') if result else 'No result returned'
            print(f"Error: {error}")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_profile()
    if success:
        print(f"\n🎉 Test completed successfully!")
    else:
        print(f"\n💥 Test failed!")
