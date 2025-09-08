#!/usr/bin/env python3
"""
PLUMATOTM Radar Chart Animation Generator (Optional Module)

This is an OPTIONAL module for creating animated GIFs of radar charts.
It's separate from the main engine to keep the core project lightweight.

Requirements:
- matplotlib
- pillow (PIL)
- numpy

Usage:
    python plumatotm_animation.py
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.animation import PillowWriter
import numpy as np
import json
import os
import sys
from typing import List, Dict, Optional

class AnimatedRadarGenerator:
    """Generates animated radar charts for PLUMATOTM results."""
    
    def __init__(self, icons_folder: Optional[str] = None):
        # Define the planets in the same order as the main radar generator
        self.planets = [
            "Sun", "Ascendant", "Moon", "Mercury", "Venus", "Mars",
            "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", "North Node", "MC"
        ]
        
        # Planet weights for node sizing (same as main radar)
        self.planet_weights = {
            "Sun": 23.0, "Ascendant": 18.0, "Moon": 15.0, "Mercury": 7.0, 
            "Venus": 6.0, "Mars": 6.0, "Jupiter": 5.0, "Saturn": 5.0, 
            "Uranus": 3.0, "Neptune": 3.0, "Pluto": 2.0, "North Node": 2.0, "MC": 5.0
        }
        
        # Planet symbols (Unicode)
        self.planet_symbols = {
            "Sun": "☉", "Ascendant": "Asc", "Moon": "☽", "Mercury": "☿",
            "Venus": "♀", "Mars": "♂", "Jupiter": "♃", "Saturn": "♄",
            "Uranus": "♅", "Neptune": "♆", "Pluto": "♇", "North Node": "☊", "MC": "MC"
        }
        
        # Icons folder for custom PNG icons
        self.icons_folder = icons_folder
        
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
                        from PIL import Image
                        icon = Image.open(icon_path)
                        icon = icon.resize((64, 64), Image.Resampling.LANCZOS)
                        self.custom_icons[planet] = icon
                        print(f"✅ Loaded custom PNG icon for {planet}: {name}")
                        break
                    except Exception as e:
                        print(f"⚠️  Could not load icon {name} for {planet}: {e}")
    
    def _load_rgba_icon(self, icon_path):
        """Load PNG icon as RGBA to avoid colormap issues."""
        from PIL import Image
        img = Image.open(icon_path).convert("RGBA")
        return np.asarray(img)
    
    def _add_icon_polar(self, ax, theta, r, img_rgba, px=64, pad=0.02, z=10):
        """Place une icône PNG (RGBA) au bout d'un rayon polaire."""
        rmax = ax.get_rmax()
        r_icon = r + pad * rmax

        h, w = img_rgba.shape[:2]
        zoom = px / float(w)

        from matplotlib.offsetbox import OffsetImage, AnnotationBbox
        
        oi = OffsetImage(img_rgba, zoom=zoom, interpolation='nearest')
        ab = AnnotationBbox(
            oi, (theta, r_icon),
            xycoords='data', frameon=False, pad=0.0,
            box_alignment=(0.5, 0.5),
            bboxprops=dict(fc='none', ec='none')
        )
        ab.set_zorder(z)
        ax.add_artist(ab)
    
    def create_animated_radar(self, final_values: List[float], animal_name: str, 
                            output_path: str = "animated_radar.gif", 
                            duration: float = 10.0) -> str:
        """
        Create an animated radar chart with sequential planet rising:
        1. Start at 35% for all planets
        2. Each planet rises one by one in order: Sun, Ascendant, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune, Pluto, North Node, MC
        3. End at final position, then return to 35% for perfect loop
        
        Args:
            final_values: Final percentage values for each planet
            animal_name: Name of the animal
            output_path: Where to save the GIF
            duration: Animation duration in seconds
            
        Returns:
            Path to the saved GIF file
        """
        
        # Animation parameters - even slower animation
        frames = 250  # More frames for even slower, smoother animation
        fps = frames // duration
        
        # Create the figure
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
        
        # Base configuration
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        ax.grid(False)
        ax.set_rticks([])
        ax.set_thetagrids([])
        ax.set_ylim(0, 130)
        ax.set_facecolor('none')
        
        # Angles for each planet
        angles = [n * 2 * np.pi / len(self.planets) for n in range(len(self.planets))]
        angles += angles[:1]  # Close the circle
        
        # Calculate max radius for lines
        max_radius = 100
        
        # Define the order of planets for sequential rising
        planet_order = [
            "Sun", "Ascendant", "Moon", "Mercury", "Venus", "Mars",
            "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", "North Node", "MC"
        ]
        
        # Calculate frames per planet (each planet gets equal time)
        # Reserve some frames at the end for returning to 35%
        rising_frames = int(frames * 0.85)  # 85% for rising sequence
        return_frames = frames - rising_frames  # 15% for returning to 35%
        frames_per_planet = rising_frames // len(planet_order)
        
        def animate(frame):
            ax.clear()
            
            # Reconfigure for each frame
            ax.set_theta_zero_location('N')
            ax.set_theta_direction(-1)
            ax.grid(False)
            ax.set_rticks([])
            ax.set_thetagrids([])
            ax.set_ylim(0, 130)
            ax.set_facecolor('none')
            
            # Calculate current values based on sequential rising
            current_values = []
            
            # Check if we're in the return phase (back to 35%)
            if frame >= rising_frames:
                # Return phase: all planets go back to 35%
                return_progress = (frame - rising_frames) / return_frames
                eased_return_progress = return_progress * return_progress * (3 - 2 * return_progress)  # Smooth step
                
                for i, final_value in enumerate(final_values):
                    current_value = final_value - (final_value - 35.0) * eased_return_progress
                    current_values.append(current_value)
            else:
                # Rising phase: sequential planet rising
                for i, final_value in enumerate(final_values):
                    planet = self.planets[i]
                    
                    # Find the position of this planet in the rising order
                    planet_index = planet_order.index(planet)
                    
                    # Calculate when this planet should start rising
                    start_frame = planet_index * frames_per_planet
                    end_frame = (planet_index + 1) * frames_per_planet
                    
                    if frame < start_frame:
                        # Planet hasn't started rising yet - stay at 35%
                        current_value = 35.0
                    elif frame >= end_frame:
                        # Planet has finished rising - stay at final value
                        current_value = final_value
                    else:
                        # Planet is currently rising
                        progress = (frame - start_frame) / (end_frame - start_frame)
                        # Smooth easing function
                        eased_progress = progress * progress * (3 - 2 * progress)  # Smooth step
                        current_value = 35.0 + (final_value - 35.0) * eased_progress
                    
                    current_values.append(current_value)
            
            # Add first value to end to close polygon
            current_values += current_values[:1]
            
            # Draw radial lines (no circle around planets)
            for angle in angles[:-1]:
                ax.plot([angle, angle], [0, max_radius], color='black', linewidth=2, alpha=0.8)
            
            # Draw the polygon
            ax.plot(angles, current_values, 'o-', linewidth=3, color='black', 
                    markersize=0, alpha=0.9)
            
            # Add nodes with size based on planet weight
            for i, (angle, value) in enumerate(zip(angles[:-1], current_values[:-1])):
                planet = self.planets[i]
                weight = self.planet_weights.get(planet, 5.0)
                node_size = max(6, min(30, weight * 4))
                
                # Only draw node if value > 0
                if value > 0:
                    ax.scatter(angle, value, s=node_size**2, color='black', zorder=5)
            
            # Add planet icons or symbols
            if any(planet in self.custom_icons for planet in self.planets):
                # Use custom icons
                self._add_custom_icons_to_chart(ax, angles[:-1], current_values[:-1])
            else:
                # Use text symbols
                for i, (angle, value) in enumerate(zip(angles[:-1], current_values[:-1])):
                    planet = self.planets[i]
                    planet_symbol = self.planet_symbols.get(planet, planet)
                    icon_radius = max_radius + 12
                    ax.text(np.degrees(angle), icon_radius, planet_symbol, 
                           ha='center', va='center', fontsize=20, fontweight='bold')
            
            # Dynamic score calculation
            current_score = sum(current_values[:-1]) / len(current_values[:-1])
            
            # Title with dynamic score
            ax.set_title(f"{animal_name}\nScore: {current_score:.1f}%", 
                        fontsize=16, fontweight='bold', pad=20)
        
        # Create animation
        anim = animation.FuncAnimation(fig, animate, frames=frames, interval=50, blit=False)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        
        # Save as GIF
        writer = PillowWriter(fps=fps)
        anim.save(output_path, writer=writer, dpi=100)
        
        plt.close()
        print(f"✅ Animation GIF saved: {output_path}")
        return output_path
    
    def _add_custom_icons_to_chart(self, ax, angles, values):
        """Add custom PNG icons to the radar chart."""
        max_radius = 100
        
        # Cache for RGBA icons to avoid reloading
        rgba_cache = {}
        
        for i, (angle, data_value) in enumerate(zip(angles, values)):
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
                    # Use smaller icons for animation (38px) - no circle around icons
                    self._add_icon_polar(ax, angle, max_radius, rgba_cache[icon_path], 
                                       px=38, pad=0.12, z=10)
    
    def create_animation_from_results(self, result_file: str = "outputs/result.json", 
                                    output_dir: str = "outputs", icons_folder: Optional[str] = None) -> Dict[str, str]:
        """
        Create animated radar charts from PLUMATOTM results.
        
        Args:
            result_file: Path to the result.json file
            output_dir: Directory to save animations
            icons_folder: Optional path to folder containing custom PNG icons
            
        Returns:
            Dictionary with paths to created animations
        """
        
        try:
            # Load results
            with open(result_file, 'r', encoding='utf-8') as f:
                result_data = json.load(f)
            
            # Extract top 3 animals
            animal_totals = result_data.get("animal_totals", [])
            if len(animal_totals) < 3:
                print("⚠️  Need at least 3 animals in results")
                return {}
            
            percentage_strength = result_data.get("top3_percentage_strength", {})
            
            animations = {}
            
            # Create animation for each of the top 3 animals
            for i, animal_data in enumerate(animal_totals[:3], 1):
                animal_name = animal_data['ANIMAL']
                
                if animal_name not in percentage_strength:
                    print(f"⚠️  No percentage strength data for {animal_name}")
                    continue
                
                # Prepare final values
                final_values = []
                for planet in self.planets:
                    final_values.append(percentage_strength[animal_name].get(planet, 0))
                
                # Create animation
                output_path = os.path.join(output_dir, f"animated_top{i}_{animal_name.lower()}_radar.gif")
                animation_path = self.create_animated_radar(
                    final_values, animal_name, output_path
                )
                
                animations[f"top{i}_animation"] = animation_path
            
            return animations
            
        except FileNotFoundError:
            print(f"❌ Results file not found: {result_file}")
            return {}
        except Exception as e:
            print(f"❌ Error creating animations: {e}")
            return {}


def main():
    """Main function for command line usage."""
    
    print("🎬 PLUMATOTM Radar Chart Animation Generator")
    print("=" * 50)
    
    # Check for icons folder
    icons_folder = "icons" if os.path.exists("icons") else None
    if icons_folder:
        print(f"🎨 Using custom icons from: {icons_folder}")
    else:
        print("🎨 Using default planet symbols")
    
    # Create a single example animation with fictional data
    generator = AnimatedRadarGenerator(icons_folder=icons_folder)
    
    # Example values for demonstration (respecting new constraints)
    # Sun, Ascendant > 95%, Moon > 90%, Jupiter, Uranus, Neptune > 40%, all others > 30%
    example_values = [
        96,  # Sun (> 95%)
        97,  # Ascendant (> 95%)  
        92,  # Moon (> 90%)
        67,  # Mercury (> 30%)
        45,  # Venus (> 30%)
        89,  # Mars (> 30%)
        45,  # Jupiter (> 40%)
        56,  # Saturn (> 30%)
        42,  # Uranus (> 40%)
        41,  # Neptune (> 40%)
        78,  # Pluto (> 30%)
        45,  # North Node (> 30%)
        67   # MC (> 30%)
    ]
    
    # Create the example animation
    output_path = "outputs/example_radar_animation.gif"
    animation_path = generator.create_animated_radar(
        final_values=example_values,
        animal_name="Fox",
        output_path=output_path,
        duration=5.0
    )
    
    print(f"\n🎉 Example animation created successfully!")
    print(f"📊 Animation saved: {animation_path}")
    print(f"📝 This demonstrates the radar chart animation with fictional data")


if __name__ == "__main__":
    main()
