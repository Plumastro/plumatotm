#!/usr/bin/env python3
"""
Single Axis Animation Generator (Optional Module)

This is a COMPLETELY SEPARATE module for creating simple single-axis animations.
It has NO IMPACT on the main engine or API.

Usage:
    python single_axis_animation.py
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.animation import PillowWriter
import numpy as np
import os
from PIL import Image

class SingleAxisAnimationGenerator:
    """Generates simple single-axis animations - completely separate from main engine."""
    
    def __init__(self, icons_folder: str = None):
        self.icons_folder = icons_folder
        self.custom_icons = {}
        
        # Load custom icons if folder is provided
        if self.icons_folder and os.path.exists(self.icons_folder):
            self._load_custom_icons()
    
    def _load_custom_icons(self):
        """Load custom PNG icons for planets."""
        icon_mapping = {
            "Sun": ["sun.png", "Sun.png", "SUN.png"]
        }
        
        for planet, possible_names in icon_mapping.items():
            for name in possible_names:
                icon_path = os.path.join(self.icons_folder, name)
                if os.path.exists(icon_path):
                    try:
                        icon = Image.open(icon_path)
                        icon = icon.resize((64, 64), Image.Resampling.LANCZOS)
                        self.custom_icons[planet] = icon
                        print(f"✅ Loaded custom PNG icon for {planet}: {name}")
                        break
                    except Exception as e:
                        print(f"⚠️  Could not load icon {name} for {planet}: {e}")
    
    def _load_rgba_icon(self, icon_path):
        """Load PNG icon as RGBA to avoid colormap issues."""
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
    
    def create_sun_axis_animation(self, output_path: str = "outputs/sun_axis_animation.gif", 
                                duration: float = 3.0) -> str:
        """
        Create a simple single-axis animation for the Sun.
        
        Args:
            output_path: Where to save the GIF
            duration: Animation duration in seconds
            
        Returns:
            Path to the saved GIF file
        """
        
        # Animation parameters
        frames = 90  # 3 seconds at 30 FPS
        fps = frames // duration
        
        # Create the figure
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))
        
        # Base configuration
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        ax.grid(False)
        ax.set_rticks([])
        ax.set_thetagrids([])
        ax.set_ylim(0, 130)
        ax.set_facecolor('none')
        
        # Single axis for Sun (at 0 degrees - top)
        sun_angle = 0  # Top of the circle
        max_radius = 100
        
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
            
            # Calculate current value with smooth up-down motion
            # Start at 25%, go to 92%, then back to 25%
            progress = frame / (frames - 1)
            
            if progress <= 0.5:
                # First half: go up from 25% to 92%
                phase_progress = progress * 2  # 0 to 1
                eased_progress = phase_progress * phase_progress * (3 - 2 * phase_progress)  # Smooth step
                current_value = 25.0 + (92.0 - 25.0) * eased_progress
            else:
                # Second half: go down from 92% to 25%
                phase_progress = (progress - 0.5) * 2  # 0 to 1
                eased_progress = phase_progress * phase_progress * (3 - 2 * phase_progress)  # Smooth step
                current_value = 92.0 - (92.0 - 25.0) * eased_progress
            
            # Draw single radial line
            ax.plot([sun_angle, sun_angle], [0, max_radius], color='black', linewidth=2, alpha=0.8)
            
            # Draw the point
            ax.scatter(sun_angle, current_value, s=400, color='black', zorder=5)  # Larger point for visibility
            
            # Add Sun icon if available
            if "Sun" in self.custom_icons:
                # Get the icon path
                icon_mapping = {
                    "Sun": ["sun.png", "Sun.png", "SUN.png"]
                }
                
                icon_path = None
                for name in icon_mapping.get("Sun", []):
                    full_path = os.path.join(self.icons_folder, name)
                    if os.path.exists(full_path):
                        icon_path = full_path
                        break
                
                if icon_path:
                    try:
                        img_rgba = self._load_rgba_icon(icon_path)
                        # Use smaller icon for single axis (50px)
                        self._add_icon_polar(ax, sun_angle, max_radius, img_rgba, 
                                           px=50, pad=0.15, z=10)
                    except Exception as e:
                        print(f"⚠️  Error loading Sun icon: {e}")
            else:
                # Fallback to text symbol
                ax.text(np.degrees(sun_angle), max_radius + 15, "☉", 
                       ha='center', va='center', fontsize=30, fontweight='bold')
        
        # Create animation
        anim = animation.FuncAnimation(fig, animate, frames=frames, interval=33, blit=False)  # ~30 FPS
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        
        # Save as GIF
        writer = PillowWriter(fps=fps)
        anim.save(output_path, writer=writer, dpi=100)
        
        plt.close()
        print(f"✅ Single axis animation GIF saved: {output_path}")
        return output_path


def main():
    """Main function for command line usage."""
    
    print("🌞 Single Axis Animation Generator")
    print("=" * 40)
    print("⚠️  This module is COMPLETELY SEPARATE from the main engine")
    print("⚠️  NO IMPACT on main calculations or API")
    print("=" * 40)
    
    # Check for icons folder
    icons_folder = "icons" if os.path.exists("icons") else None
    if icons_folder:
        print(f"🎨 Using custom icons from: {icons_folder}")
    else:
        print("🎨 Using default Sun symbol")
    
    # Create animation
    generator = SingleAxisAnimationGenerator(icons_folder=icons_folder)
    
    # Create the Sun axis animation
    output_path = "outputs/sun_axis_animation.gif"
    animation_path = generator.create_sun_axis_animation(output_path, duration=3.0)
    
    print(f"\n🎉 Single axis animation created successfully!")
    print(f"📊 Animation saved: {animation_path}")
    print(f"📝 Duration: 3 seconds, loopable GIF")
    print(f"📝 Sun moves from 25% to 92% and back to 25%")


if __name__ == "__main__":
    main()
