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
from typing import Dict, List, Tuple, Optional
from PIL import Image

class RadarChartGenerator:
    """Generates radar charts for animal-planet correlations."""
    
    def __init__(self, icons_folder: Optional[str] = None):
        # Define the planets in clockwise order starting with Sun at 12pm
        self.planets = [
            "Sun", "Ascendant", "Moon", "Mercury", "Venus", "Mars",
            "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", "North Node", "MC"
        ]
        
        # Icons folder for custom PNG icons
        self.icons_folder = icons_folder
        
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
        
        # Load custom icons if folder is provided
        self.custom_icons = {}
        if self.icons_folder and os.path.exists(self.icons_folder):
            self._load_custom_icons()
    
    def _load_custom_icons(self):
        """Load custom PNG icons for planets."""
        icon_mapping = {
            "Sun": ["sun.png", "Sun.png", "SUN.png"],
            "Ascendant": ["AC.png", "ac.png", "ascendant.png", "Ascendant.png", "ASC.png", "asc.png"],
            "Moon": ["moon.png", "Moon.png", "MOON.png"],
            "Mercury": ["mercury.png", "Mercury.png", "MERCURY.png"],
            "Venus": ["venus.png", "Venus.png", "VENUS.png"],
            "Mars": ["mars.png", "Mars.png", "MARS.png"],
            "Jupiter": ["jupiter.png", "Jupiter.png", "JUPITER.png"],
            "Saturn": ["saturn.png", "Saturn.png", "SATURN.png"],
            "Uranus": ["uranus.png", "Uranus.png", "URANUS.png"],
            "Neptune": ["neptune.png", "Neptune.png", "NEPTUNE.png"],
            "Pluto": ["pluto.png", "Pluto.png", "PLUTO.png"],
            "North Node": ["north_node.png", "North_Node.png", "northnode.png", "node.png"],
            "MC": ["MC.png", "mc.png", "midheaven.png", "Midheaven.png"]
        }
        
        for planet, possible_names in icon_mapping.items():
            for name in possible_names:
                icon_path = os.path.join(self.icons_folder, name)
                if os.path.exists(icon_path):
                    try:
                        # Load and resize the PNG icon (from 750x750 to 64x64)
                        from PIL import Image
                        icon = Image.open(icon_path)
                        # Resize to a reasonable size for the radar chart
                        icon = icon.resize((64, 64), Image.Resampling.LANCZOS)
                        self.custom_icons[planet] = icon
                        print(f"✅ Loaded custom PNG icon for {planet}: {name} (resized to 64x64)")
                        break
                    except Exception as e:
                        print(f"⚠️  Could not load icon {name} for {planet}: {e}")
    
    def generate_top_animal_radar(self, result_data: Dict, output_path: str = "outputs/top1_animal_radar.png"):
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
                
                # Use custom icon if available, otherwise use symbol
                if planet in self.custom_icons:
                    label = planet  # Will be replaced with icon in the chart
                else:
                    planet_symbol = self.planet_symbols.get(planet, planet)
                    label = planet_symbol
                planet_labels.append(label)
            else:
                planet_values.append(0)
                # Use custom icon if available, otherwise use symbol
                if planet in self.custom_icons:
                    label = planet  # Will be replaced with icon in the chart
                else:
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
    
    def generate_top2_animal_radar(self, result_data: Dict, output_path: str = "outputs/top2_animal_radar.png"):
        """
        Generate a radar chart for the second animal showing correlation with all planets.
        
        Args:
            result_data: The analysis results from the API
            output_path: Where to save the radar chart image
        """
        
        # Extract data
        top2_animal = result_data['data']['top_3_animals'][1]
        animal_name = top2_animal['ANIMAL']
        top2_score = top2_animal['TOTAL_SCORE']
        
        # Get percentage strength data for the top 2 animal
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
                
                # Use custom icon if available, otherwise use symbol
                if planet in self.custom_icons:
                    label = planet  # Will be replaced with icon in the chart
                else:
                    planet_symbol = self.planet_symbols.get(planet, planet)
                    label = planet_symbol
                planet_labels.append(label)
            else:
                planet_values.append(0)
                # Use custom icon if available, otherwise use symbol
                if planet in self.custom_icons:
                    label = planet  # Will be replaced with icon in the chart
                else:
                    planet_symbol = self.planet_symbols.get(planet, planet)
                    label = planet_symbol
                planet_labels.append(label)
        
        # Create the radar chart
        self._create_radar_chart(
            planet_values, 
            planet_labels, 
            animal_name, 
            top2_score,
            output_path
        )
        
        return output_path
    
    def generate_top3_animal_radar(self, result_data: Dict, output_path: str = "outputs/top3_animal_radar.png"):
        """
        Generate a radar chart for the third animal showing correlation with all planets.
        
        Args:
            result_data: The analysis results from the API
            output_path: Where to save the radar chart image
        """
        
        # Extract data
        top3_animal = result_data['data']['top_3_animals'][2]
        animal_name = top3_animal['ANIMAL']
        top3_score = top3_animal['TOTAL_SCORE']
        
        # Get percentage strength data for the top 3 animal
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
                
                # Use custom icon if available, otherwise use symbol
                if planet in self.custom_icons:
                    label = planet  # Will be replaced with icon in the chart
                else:
                    planet_symbol = self.planet_symbols.get(planet, planet)
                    label = planet_symbol
                planet_labels.append(label)
            else:
                planet_values.append(0)
                # Use custom icon if available, otherwise use symbol
                if planet in self.custom_icons:
                    label = planet  # Will be replaced with icon in the chart
                else:
                    planet_symbol = self.planet_symbols.get(planet, planet)
                    label = planet_symbol
                planet_labels.append(label)
        
        # Create the radar chart
        self._create_radar_chart(
            planet_values, 
            planet_labels, 
            animal_name, 
            top3_score,
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
                              facecolor='none')
        
        # Set background to transparent
        ax.set_facecolor('none')
        
        # Configure theta (angle) direction and zero location
        ax.set_theta_zero_location('N')  # North (top) is 0 degrees
        ax.set_theta_direction(-1)  # Clockwise direction
        
        # Remove all grid lines and labels
        ax.grid(False)
        ax.set_rticks([])  # Remove radial ticks
        ax.set_thetagrids([])  # Remove degree labels
        
        # Set the radial limits (0 to 130 for percentages - chart appears smaller)
        # Higher limit makes the chart appear smaller as points are closer to center
        ax.set_ylim(0, 130)
        
        # Draw radial lines from center to 100% radius (all same length)
        max_radius = 100  # 100% radius
        for i, angle in enumerate(angles[:-1]):
            # All lines go to the same radius (100%)
            ax.plot([angle, angle], [0, max_radius], color='black', linewidth=2, alpha=0.8)
        
        # Plot the data polygon
        ax.plot(angles, values, 'o-', linewidth=3, color='black', 
                markersize=0, alpha=0.9)
        
        # Add nodes with size based on planet weight
        for i, (angle, value) in enumerate(zip(angles[:-1], values[:-1])):
            # Get planet name from the planets list
            planet = self.planets[i]
            weight = self.planet_weights.get(planet, 5.0)
            
            # Calculate surface area directly proportional to weight
            # Scale so that weight 23 (Sun) = surface area 900, weight 2 = surface area ~78
            # Formula: surface_area = (weight / max_weight) * max_surface_area
            max_weight = 23.0  # Sun's weight
            max_surface_area = 900.0  # Desired max surface area
            min_surface_area = 50.0   # Minimum surface area for visibility
            
            surface_area = max(min_surface_area, (weight / max_weight) * max_surface_area)
            
            # Draw filled black circle with proportional surface area
            ax.scatter(angle, value, s=surface_area, color='black', zorder=5)
        
        # Set the labels - use custom icons if available, otherwise use text
        if any(planet in self.custom_icons for planet in self.planets):
            # Use custom icons
            self._add_custom_icons_to_chart(ax, angles[:-1], labels, values[:-1])
        else:
            # Use text labels
            ax.set_thetagrids([np.degrees(angle) for angle in angles[:-1]], 
                             labels=labels, fontsize=20, fontweight='bold')
        
        # Remove all spines
        ax.spines['polar'].set_visible(False)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save the chart
        plt.tight_layout()
        plt.savefig(output_path, dpi=100, bbox_inches='tight', facecolor='none', transparent=True)
        plt.close()
        
        print(f"✅ Radar chart saved to: {output_path}")
    
    def _load_rgba_icon(self, icon_path):
        """Load PNG icon as RGBA to avoid colormap issues."""
        from PIL import Image
        img = Image.open(icon_path).convert("RGBA")
        return np.asarray(img)
    
    def _add_icon_polar(self, ax, theta, r, img_rgba, px=64, pad=0.02, z=10):
        """
        Place une icône PNG (RGBA) au bout d'un rayon polaire.
        - theta: angle en radians
        - r: rayon (en unités de l'axe)
        - px: taille souhaitée de l'icône en pixels (largeur)
        - pad: décalage radial relatif (ex: 0.02 = 2% du rmax)
        """
        rmax = ax.get_rmax()
        r_icon = r + pad * rmax  # petit décalage pour être "après" le bout du rayon

        # Taille fixe en pixels, quel que soit le zoom de la figure
        h, w = img_rgba.shape[:2]
        zoom = px / float(w)

        from matplotlib.offsetbox import OffsetImage, AnnotationBbox
        
        oi = OffsetImage(img_rgba, zoom=zoom, interpolation='nearest')  # pas de cmap
        ab = AnnotationBbox(
            oi, (theta, r_icon),
            xycoords='data', frameon=False, pad=0.0,
            box_alignment=(0.5, 0.5),  # centre l'icône sur le point
            bboxprops=dict(fc='none', ec='none')
        )
        ab.set_zorder(z)
        ax.add_artist(ab)

    def _add_custom_icons_to_chart(self, ax, angles, labels, values):
        """Add custom PNG icons to the radar chart using the improved method."""
        # Position icons at the end of each radial line (at 100% + small offset)
        max_radius = 100  # 100% radius where lines end
        
        # Cache for RGBA icons to avoid reloading
        rgba_cache = {}
        
        for i, (angle, label, data_value) in enumerate(zip(angles, labels, values)):
            planet = self.planets[i]
            
            if planet in self.custom_icons:
                # Get the icon path from the original mapping
                icon_mapping = {
                    "Sun": ["sun.png", "Sun.png", "SUN.png"],
                    "Ascendant": ["AC.png", "ac.png", "ascendant.png", "Ascendant.png", "ASC.png", "asc.png"],
                    "Moon": ["moon.png", "Moon.png", "MOON.png"],
                    "Mercury": ["mercury.png", "Mercury.png", "MERCURY.png"],
                    "Venus": ["venus.png", "Venus.png", "VENUS.png"],
                    "Mars": ["mars.png", "Mars.png", "MARS.png"],
                    "Jupiter": ["jupiter.png", "Jupiter.png", "JUPITER.png"],
                    "Saturn": ["saturn.png", "Saturn.png", "SATURN.png"],
                    "Uranus": ["uranus.png", "Uranus.png", "URANUS.png"],
                    "Neptune": ["neptune.png", "Neptune.png", "NEPTUNE.png"],
                    "Pluto": ["pluto.png", "Pluto.png", "PLUTO.png"],
                    "North Node": ["north_node.png", "North_Node.png", "northnode.png", "node.png"],
                    "MC": ["MC.png", "mc.png", "midheaven.png", "Midheaven.png"]
                }
                
                # Find the actual icon path
                icon_path = None
                for name in icon_mapping.get(planet, []):
                    full_path = os.path.join(self.icons_folder, name)
                    if os.path.exists(full_path):
                        icon_path = full_path
                        break
                
                if icon_path and icon_path not in rgba_cache:
                    try:
                        rgba_cache[icon_path] = self._load_rgba_icon(icon_path)
                    except Exception as e:
                        print(f"⚠️  Error loading RGBA icon for {planet}: {e}")
                        continue
                
                if icon_path in rgba_cache:
                    # Use the improved positioning method with smaller icons (40% reduction: 64 -> 38)
                    # Increased pad from 0.08 to 0.12 for maximum distance from the chart
                    self._add_icon_polar(ax, angle, max_radius, rgba_cache[icon_path], 
                                       px=38, pad=0.12, z=10)
                
            else:
                # Fallback to text if no custom icon
                planet_symbol = self.planet_symbols.get(planet, planet)
                icon_radius = max_radius + 12
                ax.text(np.degrees(angle), icon_radius, planet_symbol, 
                       ha='center', va='center', fontsize=20, fontweight='bold')

def generate_radar_charts_from_results(result_file: str = "outputs/result.json", icons_folder: Optional[str] = None):
    """
    Generate radar chart from the analysis results.
    
    Args:
        result_file: Path to the result.json file
        icons_folder: Optional path to folder containing custom PNG icons
    """
    
    try:
        # Load the results
        with open(result_file, 'r', encoding='utf-8') as f:
            result_data = json.load(f)
        
        # Initialize the generator with custom icons folder
        generator = RadarChartGenerator(icons_folder=icons_folder)
        
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
        
        # Generate the top 3 animal radar charts
        top1_chart_path = generator.generate_top_animal_radar(radar_data)
        top2_chart_path = generator.generate_top2_animal_radar(radar_data)
        top3_chart_path = generator.generate_top3_animal_radar(radar_data)
        
        return {
            'top1_animal_chart': top1_chart_path,
            'top2_animal_chart': top2_chart_path,
            'top3_animal_chart': top3_chart_path
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
            print("🎉 Radar charts generated successfully!")
            print(f"📊 Top 1 animal chart: {chart['top1_animal_chart']}")
            print(f"📊 Top 2 animal chart: {chart['top2_animal_chart']}")
            print(f"📊 Top 3 animal chart: {chart['top3_animal_chart']}")
        else:
            print("❌ Failed to generate radar charts")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()