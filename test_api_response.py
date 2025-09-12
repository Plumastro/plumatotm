#!/usr/bin/env python3
"""
Test script to verify the API response format
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

def test_api_response():
    """Test the API response format"""
    
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
    
    print("🧪 TESTING API RESPONSE FORMAT")
    print("=" * 50)
    
    try:
        # Initialize analyzer
        analyzer = BirthChartAnalyzer(
            scores_csv_path="plumatotm_raw_scores_trad.csv",
            weights_csv_path="plumatotm_planets_weights.csv",
            multipliers_csv_path="plumatotm_planets_multiplier.csv"
        )
        
        # Run analysis
        result = analyzer.run_analysis(
            date=profile['date'],
            time=profile['time'],
            lat=profile['lat'],
            lon=profile['lon'],
            user_name=profile['name'],
            openai_api_key=None
        )
        
        if result and result.get('success'):
            print("✅ ANALYSIS SUCCESSFUL!")
            print("=" * 30)
            
            # Display key results
            print(f"🎯 Top 1 Animal (EN): {result.get('top1_animal', 'Unknown')}")
            print(f"🎯 Top 1 Animal (FR): {result.get('top1_animal_fr', 'Unknown')}")
            print(f"📊 Top 1 Score: {result.get('top1_score', 0)}")
            print(f"🆔 PlumID: {result.get('plumid', 'Unknown')}")
            
            # Show top 3 animals
            if 'top3_animals' in result:
                print(f"\n🏆 Top 3 Animals:")
                for i, animal in enumerate(result['top3_animals'][:3], 1):
                    score = result.get('top3_scores', [])[i-1] if i-1 < len(result.get('top3_scores', [])) else 0
                    print(f"   {i}. {animal} (Score: {score})")
            
            # Show some key data
            print(f"\n📊 Analysis Summary:")
            print(f"   - Total animals processed: {len(result.get('animal_totals', []))}")
            print(f"   - Birth chart calculated: {'Yes' if 'birth_chart' in result else 'No'}")
            print(f"   - Radar charts generated: {'Yes' if 'radar_charts' in result else 'No'}")
            print(f"   - Supabase integration: {'Yes' if 'supabase_updated' in result else 'No'}")
            
            return True
            
        else:
            print("❌ ANALYSIS FAILED!")
            error = result.get('error', 'Unknown error') if result else 'No result returned'
            print(f"Error: {error}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_api_response()
    if success:
        print(f"\n🎉 API Response Test completed successfully!")
        print("✅ The engine is working perfectly with the updated CSV file!")
    else:
        print(f"\n💥 API Response Test failed!")
