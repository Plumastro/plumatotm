#!/usr/bin/env python3
"""
Radar Chart Generator for PLUMATOTM Animal Analysis

This module generates radar charts showing the correlation strength
between animals and astrological planets/points.
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import json
import os
from typing import Dict, List, Tuple

class RadarChartGenerator:
    """Generates radar charts for animal-planet correlations."""
    
    def __init__(self):
        # Define the planets in clockwise order starting with Sun at 12pm
        self.planets = [
            "Sun", "Ascendant", "Moon", "Mercury", "Venus", "Mars",
            "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", "North Node"
        ]
        
        # Planet symbols (Unicode)
        self.planet_symbols = {
            "Sun": "☉",
            "Ascendant": "Asc",
            "Moon": "☽",
            "Mercury": "☿",
            "Venus": "♀",
            "Mars": "♂",
            "Jupiter": "♃",
            "Saturn": "♄",
            "Uranus": "♅",
            "Neptune": "♆",
            "Pluto": "♇",
            "North Node": "☊",
            "MC": "MC"
        }
        
        # Zodiac sign symbols (Unicode)
        self.sign_symbols = {
            "ARIES": "♈",
            "TAURUS": "♉",
            "GEMINI": "♊",
            "CANCER": "♋",
            "LEO": "♌",
            "VIRGO": "♍",
            "LIBRA": "♎",
            "SCORPIO": "♏",
            "SAGITTARIUS": "♐",
            "CAPRICORN": "♑",
            "AQUARIUS": "♒",
            "PISCES": "♓"
        }
        
        # Planet weights for node sizing
        self.planet_weights = {
            "Sun": 23.0, "Ascendant": 18.0, "Moon": 15.0, "Mercury": 7.0, 
            "Venus": 6.0, "Mars": 6.0, "Jupiter": 5.0, "Saturn": 5.0, 
            "Uranus": 3.0, "Neptune": 3.0, "Pluto": 2.0, "North Node": 2.0, "MC": 5.0
        }
    
    def generate_top_animal_radar(self, result_data: Dict, output_path: str = "outputs/top_animal_radar.png"):
        """
        Generate a radar chart for the top animal showing correlation with all planets.
        
        Args:
            result_data: The analysis results from the API
            output_path: Where to save the radar chart image
        """
        
        # Extract data
        top_animal = result_data['data']['top_3_animals'][0]
        animal_name = top_animal['ANIMAL']
        top_score = top_animal['TOTAL_SCORE']
        
        # Get percentage strength data for the top animal
        percentage_strength = result_data['data']['top3_percentage_strength']
        animal_percentages = percentage_strength[animal_name]
        
        # Get birth chart data for planet signs
        birth_chart = result_data.get('birth_chart', {})
        
        # Prepare data for radar chart
        planet_values = []
        planet_labels = []
        
        for planet in self.planets:
            if planet in animal_percentages:
                value = animal_percentages[planet]
                planet_values.append(value)
                
                # Create label with just planet symbol
                planet_symbol = self.planet_symbols.get(planet, planet)
                label = planet_symbol
                planet_labels.append(label)
            else:
                planet_values.append(0)
                planet_symbol = self.planet_symbols.get(planet, planet)
                label = planet_symbol
                planet_labels.append(label)
        
        # Create the radar chart
        self._create_radar_chart(
            planet_values, 
            planet_labels, 
            animal_name, 
            top_score,
            output_path
        )
        
        return output_path
    
    def _create_radar_chart(self, values: List[float], labels: List[str], 
                           animal_name: str, total_score: float, output_path: str):
        """
        Create and save a radar chart with clean, minimalist design.
        
        Args:
            values: Percentage values for each planet
            labels: Planet names
            animal_name: Name of the animal
            total_score: Total score for the animal
            output_path: Where to save the chart
        """
        
        # Number of variables
        num_vars = len(values)
        
        # Compute angles for each axis - evenly spaced around the full circle
        # Since we set theta_zero_location to 'N' and direction to clockwise,
        # 0 degrees is at the top and angles increase clockwise
        angles = []
        for n in range(num_vars):
            angle = n * 2 * np.pi / num_vars  # Evenly spaced around the circle
            angles.append(angle)
        angles += angles[:1]  # Complete the circle
        

        
        # Add the first value to the end to close the polygon
        values += values[:1]
        
        # Create the figure
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'), 
                              facecolor='white')
        
        # Set background to white
        ax.set_facecolor('white')
        
        # Configure theta (angle) direction and zero location
        ax.set_theta_zero_location('N')  # North (top) is 0 degrees
        ax.set_theta_direction(-1)  # Clockwise direction
        
        # Remove all grid lines and labels
        ax.grid(False)
        ax.set_rticks([])  # Remove radial ticks
        
        # Set the radial limits (0 to 100 for percentages)
        ax.set_ylim(0, 100)
        
        # Draw radial lines from center to edge
        for i, angle in enumerate(angles[:-1]):
            ax.plot([angle, angle], [0, 100], color='black', linewidth=2, alpha=0.8)
        
        # Plot the data polygon
        ax.plot(angles, values, 'o-', linewidth=3, color='black', 
                markersize=0, alpha=0.9)
        
        # Add nodes with size based on planet weight
        for i, (angle, value) in enumerate(zip(angles[:-1], values[:-1])):
            # Get planet name from the planets list
            planet = self.planets[i]
            weight = self.planet_weights.get(planet, 5.0)
            
            # Calculate node size (doubled)
            node_size = max(6, min(30, weight * 4))
            
            # Draw filled black circle
            ax.scatter(angle, value, s=node_size**2, color='black', zorder=5)
        
        # Set the labels with larger font for planet symbols
        ax.set_thetagrids([np.degrees(angle) for angle in angles[:-1]], 
                         labels=labels, fontsize=20, fontweight='bold')
        
        # Remove all spines
        ax.spines['polar'].set_visible(False)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save the chart
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        print(f"✅ Radar chart saved to: {output_path}")

def generate_radar_charts_from_results(result_file: str = "outputs/result.json"):
    """
    Generate radar chart from the analysis results.
    
    Args:
        result_file: Path to the result.json file
    """
    
    try:
        # Load the results
        with open(result_file, 'r', encoding='utf-8') as f:
            result_data = json.load(f)
        
        # Initialize the generator
        generator = RadarChartGenerator()
        
        # Extract top 3 animals and their percentage strengths
        animal_totals = result_data.get("animal_totals", [])
        top_3_animals = animal_totals[:3] if animal_totals else []
        
        # Get percentage strength data
        percentage_strength = result_data.get("top3_percentage_strength", {})
        
        # Create the structure expected by the radar generator
        radar_data = {
            "data": {
                "top_3_animals": top_3_animals,
                "top3_percentage_strength": percentage_strength
            },
            "birth_chart": result_data.get("birth_chart", {})
        }
        
        # Generate the top animal radar chart
        top_chart_path = generator.generate_top_animal_radar(radar_data)
        
        return {
            'top_animal_chart': top_chart_path
        }
        
    except Exception as e:
        print(f"❌ Error generating radar chart: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Test the radar chart generation
    try:
        chart = generate_radar_charts_from_results()
        if chart:
            print("🎉 Radar chart generated successfully!")
            print(f"📊 Top animal chart: {chart['top_animal_chart']}")
        else:
            print("❌ Failed to generate radar chart")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()