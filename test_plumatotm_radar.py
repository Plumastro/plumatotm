#!/usr/bin/env python3
"""
Test script for radar chart generation
"""

from radar_chart_generator import generate_radar_charts_from_results
import json

def test_radar_generation():
    print("🧪 Testing Radar Chart Generation...")
    
    # Test the radar chart generation
    charts = generate_radar_charts_from_results()
    
    if charts:
        print("✅ Radar chart generated successfully!")
        print(f"📊 Top animal chart: {charts['top_animal_chart']}")
        
        # Let's also check what the top animal is
        with open("outputs/result.json", 'r', encoding='utf-8') as f:
            result_data = json.load(f)
        
        animal_totals = result_data.get("animal_totals", [])
        if animal_totals:
            top_animal = animal_totals[0]
            print(f"🏆 Top animal: {top_animal['ANIMAL']} with score {top_animal['TOTAL_SCORE']:.1f}")
            
            # Show percentage strengths for the top animal
            percentage_strength = result_data.get("top3_percentage_strength", {})
            if top_animal['ANIMAL'] in percentage_strength:
                print(f"📊 Percentage strengths for {top_animal['ANIMAL']}:")
                for planet, strength in percentage_strength[top_animal['ANIMAL']].items():
                    print(f"   {planet}: {strength:.1f}%")
        
    else:
        print("❌ Failed to generate radar charts")

if __name__ == "__main__":
    test_radar_generation()
