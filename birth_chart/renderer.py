"""
Birth Chart Renderer

Handles the visual rendering of birth charts using matplotlib and PIL.
Creates minimalist black and white circular charts.
"""

import os
import logging
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from PIL import Image

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

logger = logging.getLogger(__name__)

class BirthChartRenderer:
    """Renders birth charts as PNG images."""
    
    def __init__(self, icons_dir: str = "icons"):
        self.icons_dir = icons_dir
        self.canvas_size = 1500
        self.dpi = 100
        
        # Chart dimensions according to FRS specifications
        # Centre: (750, 750), Rayon utile R ≈ 700px
        self.center = (750, 750)
        self.R = 700  # Rayon utile
        
        # Rayons spécifiés dans le FRS (en pixels) - CORRIGÉS
        self.sign_ring_outer = self.R * 0.97  # R*0.97 (inchangé)
        self.sign_ring_inner = self.R * 0.70  # R*0.70 (élargi de 0.83 à 0.70)
        self.sign_icon_radius = self.R * 0.83  # R*0.83 (centre de la bande élargie)
        
        self.house_ring_outer = self.R * 0.45  # R*0.45 (agrandi de 0.42 à 0.45)
        self.house_ring_inner = self.R * 0.35  # R*0.35 (réduit de 0.27 à 0.35)
        self.house_icon_radius = self.R * 0.40  # R*0.40 (centre de la bande ajustée)
        
        # Cercle pointillé = rayon d'ancrage planétaire
        self.position_radius = self.sign_ring_inner - self.R * 0.02
        self.grid_radii = [self.position_radius]
        
        # Géométrie de l'encoche / icône / nœud (distances vers le centre)
        self.planet_tick_len = self.R * 0.03     # longueur encoche (≈ 2–3% R)
        self.icon_gap = self.R * 0.01            # espace entre encoche et icône
        self.node_gap = self.R * 0.01            # espace entre icône et nœud
        self.node_radius_px = 6                  # rayon visuel du petit nœud (cercle vide)
        
        # Rayons de placement le long du même rayon
        self.planet_icon_radius = self.position_radius - (self.planet_tick_len + self.icon_gap)
        self.node_radius = self.planet_icon_radius - self.node_gap
        
        # S'assurer que le nœud reste au-dessus de la couronne des maisons
        self.node_radius = max(self.node_radius, self.house_ring_outer + self.R * 0.03)
        
        # Rayons pour planètes et angles (utilisent la nouvelle géométrie)
        self.planet_radius = self.planet_icon_radius
        self.asc_mc_radius = self.planet_icon_radius
        
        # Rayon maximum pour les aspects (synchronisé avec house_ring_inner)
        self.aspect_max_radius = self.house_ring_inner  # garantis le confinement
        
        # Icon sizes according to FRS - CORRIGÉS
        self.sign_icon_size = 48  # 42-52px (inchangé)
        self.house_icon_size = 26  # 22-28px (inchangé)
        self.planet_icon_size = 40  # 40px (fixé pour visibilité)
        
        # Load icon mappings
        self.icon_mappings = self._create_icon_mappings()
        self.loaded_icons = {}
    
    def _create_icon_mappings(self) -> Dict[str, List[str]]:
        """Create mappings for icon file names."""
        return {
            # Planets
            "Sun": ["sun.png", "Sun.png", "SUN.png"],
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
            "Ascendant": ["AC.png", "ac.png", "ascendant.png", "Ascendant.png", "ASC.png", "asc.png"],
            "MC": ["MC.png", "mc.png", "midheaven.png", "Midheaven.png"],
            
            # Signs
            "ARIES": ["ARIES.png", "aries.png", "Aries.png"],
            "TAURUS": ["TAURUS.png", "taurus.png", "Taurus.png"],
            "GEMINI": ["GEMINI.png", "gemini.png", "Gemini.png"],
            "CANCER": ["CANCER.png", "cancer.png", "Cancer.png"],
            "LEO": ["LEO.png", "leo.png", "Leo.png"],
            "VIRGO": ["VIRGO.png", "virgo.png", "Virgo.png"],
            "LIBRA": ["LIBRA.png", "libra.png", "Libra.png"],
            "SCORPIO": ["SCORPIO.png", "scorpio.png", "Scorpio.png"],
            "SAGITTARIUS": ["SAGITTARIUS.png", "sagittarius.png", "Sagittarius.png"],
            "CAPRICORN": ["CAPRICORN.png", "capricorn.png", "Capricorn.png"],
            "AQUARIUS": ["AQUARIUS.png", "aquarius.png", "Aquarius.png"],
            "PISCES": ["PISCES.png", "pisces.png", "Pisces.png"],
            
            # Houses
            "1": ["1.png"],
            "2": ["2.png"],
            "3": ["3.png"],
            "4": ["4.png"],
            "5": ["5.png"],
            "6": ["6.png"],
            "7": ["7.png"],
            "8": ["8.png"],
            "9": ["9.png"],
            "10": ["10.png"],
            "11": ["11.png"],
            "12": ["12.png"]
        }
    
    def _load_icon(self, name: str, size: int) -> Optional[np.ndarray]:
        """Load an icon from the icons directory."""
        if name in self.loaded_icons:
            return self.loaded_icons[name]
        
        if name not in self.icon_mappings:
            logger.warning(f"No icon mapping for {name}")
            return None
        
        for filename in self.icon_mappings[name]:
            icon_path = os.path.join(self.icons_dir, filename)
            if os.path.exists(icon_path):
                try:
                    # Load and resize icon
                    img = Image.open(icon_path).convert("RGBA")
                    img = img.resize((size, size), Image.Resampling.LANCZOS)
                    icon_array = np.asarray(img)
                    self.loaded_icons[name] = icon_array
                    logger.debug(f"Loaded icon: {filename} for {name}")
                    print(f"DEBUG: Loaded icon: {filename} for {name}")  # Debug visible
                    return icon_array
                except Exception as e:
                    logger.warning(f"Could not load icon {filename}: {e}")
                    continue
        
        logger.warning(f"No icon found for {name}")
        return None
    
    def _longitude_to_angle(self, longitude: float, ascendant_longitude: float = None) -> float:
        """Convert longitude to matplotlib angle (radians)."""
        if ascendant_longitude is not None:
            # Place AC à gauche (180°/pi), et tourner en SENS ANTIHORAIRE.
            # Formule robuste : theta = 180° + (longitude - AC)  (mod 360), en radians
            theta_deg = (180 + (longitude - ascendant_longitude)) % 360
            return np.radians(theta_deg)
        else:
            # Zodiaque standard anti-horaire si jamais AC absent
            return np.radians((180 + longitude) % 360)
    
    def _angle_to_position(self, angle: float, radius: float) -> Tuple[float, float]:
        """Convert angle and radius to x, y coordinates."""
        x = radius * np.cos(angle)
        y = radius * np.sin(angle)
        return x, y
    
    def _planet_geo(self, longitude: float, ascendant_longitude: float):
        """Retourne (point sur cercle pointillé, bout encoche, pos icône, pos nœud, angle) en coords canvas."""
        angle = self._longitude_to_angle(longitude, ascendant_longitude)

        # 1) point sur le cercle pointillé (départ encoche)
        x_on, y_on = self._angle_to_position(angle, self.position_radius)

        # 2) bout intérieur de l'encoche
        x_tick, y_tick = self._angle_to_position(angle, self.position_radius - self.planet_tick_len)

        # 3) position icône (entre encoche et nœud)
        x_icon, y_icon = self._angle_to_position(angle, self.planet_icon_radius)

        # 4) position nœud (cercle vide, le plus proche du centre)
        x_node, y_node = self._angle_to_position(angle, self.node_radius)

        cx, cy = self.center
        return (x_on+cx, y_on+cy), (x_tick+cx, y_tick+cy), (x_icon+cx, y_icon+cy), (x_node+cx, y_node+cy), angle
    
    def render_birth_chart(self, chart_data: Dict[str, Any], output_path: str) -> str:
        """
        Render a complete birth chart.
        
        Args:
            chart_data: Birth chart data from calculator
            output_path: Path to save the PNG file
        
        Returns:
            Path to the saved image
        """
        try:
            # Create figure with white background
            fig, ax = plt.subplots(figsize=(self.canvas_size/self.dpi, self.canvas_size/self.dpi),
                                 dpi=self.dpi, facecolor='white')
            ax.set_facecolor('white')
            
            # Set equal aspect ratio and remove axes
            ax.set_aspect('equal')
            ax.set_xlim(0, self.canvas_size)
            ax.set_ylim(0, self.canvas_size)
            ax.axis('off')
            
            # Get Ascendant longitude for proper positioning
            ascendant_longitude = None
            angles = chart_data.get("angles", {})
            if "Ascendant" in angles:
                ascendant_longitude = angles["Ascendant"]["longitude"]
            
            # Draw in correct z-order according to FRS
            # 1. Grid circles (background)
            self._draw_grid_circles(ax)
            
            # 2. Aspect lines (under planets)
            self._draw_aspects(ax, chart_data, ascendant_longitude)
            
            # 3. Radial ticks and house cusps
            self._draw_radial_ticks(ax, chart_data, ascendant_longitude)
            self._draw_house_ring(ax, chart_data, ascendant_longitude)
            
            # 4. Zodiac signs ring
            self._draw_zodiac_ring(ax, chart_data, ascendant_longitude)
            
            # 5. Planets and angles (on top)
            self._draw_planets(ax, chart_data, ascendant_longitude)
            self._draw_angles(ax, chart_data, ascendant_longitude)
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save with white background
            plt.tight_layout()
            plt.savefig(output_path, dpi=self.dpi, bbox_inches='tight',
                       facecolor='white', transparent=False, pad_inches=0)
            plt.close()
            
            logger.info(f"Birth chart saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error rendering birth chart: {e}")
            raise
    
    def _draw_grid_circles(self, ax):
        """Draw concentric dotted circles for grid structure."""
        for radius in self.grid_radii:
            circle = Circle(self.center, radius, fill=False, 
                          color='black', linewidth=1, linestyle='--', alpha=0.3, zorder=1)
            ax.add_patch(circle)
    
    def _draw_radial_ticks(self, ax, chart_data: Dict[str, Any], ascendant_longitude: float = None):
        """Draw radial ticks for house cusps only."""
        # Ne tracer ici QUE les cuspides de maisons (plein + pointillé)
        # Draw house cusp ticks
        house_cusps = chart_data.get("house_cusps", [])
        for house_data in house_cusps:
            longitude = house_data["longitude"]
            angle = self._longitude_to_angle(longitude, ascendant_longitude)
            
            # Solid line in house ring
            start_radius = self.house_ring_inner
            end_radius = self.house_ring_outer
            
            x1, y1 = self._angle_to_position(angle, start_radius)
            x2, y2 = self._angle_to_position(angle, end_radius)
            
            # Convert to canvas coordinates
            x1 += self.center[0]
            y1 += self.center[1]
            x2 += self.center[0]
            y2 += self.center[1]
            
            ax.plot([x1, x2], [y1, y2], color='black', linewidth=2, zorder=5)
            
            # Dotted extension to sign ring
            start_radius = self.house_ring_outer
            end_radius = self.sign_ring_inner
            
            x1, y1 = self._angle_to_position(angle, start_radius)
            x2, y2 = self._angle_to_position(angle, end_radius)
            
            # Convert to canvas coordinates
            x1 += self.center[0]
            y1 += self.center[1]
            x2 += self.center[0]
            y2 += self.center[1]
            
            ax.plot([x1, x2], [y1, y2], color='black', linewidth=1, 
                   linestyle='--', alpha=0.6, zorder=5)

    def _draw_zodiac_ring(self, ax, chart_data: Dict[str, Any], ascendant_longitude: float = None):
        """Draw the outer zodiac signs ring."""
        # Draw outer circle
        outer_circle = Circle(self.center, self.sign_ring_outer, fill=False, 
                            color='black', linewidth=2)
        ax.add_patch(outer_circle)
        
        # Draw inner circle
        inner_circle = Circle(self.center, self.sign_ring_inner, fill=False, 
                            color='black', linewidth=2)
        ax.add_patch(inner_circle)
        
        # Draw sector dividers (every 30°)
        for i in range(12):
            angle = self._longitude_to_angle(i * 30, ascendant_longitude)
            start_radius = self.sign_ring_inner
            end_radius = self.sign_ring_outer
            
            x1, y1 = self._angle_to_position(angle, start_radius)
            x2, y2 = self._angle_to_position(angle, end_radius)
            
            # Convert to canvas coordinates
            x1 += self.center[0]
            y1 += self.center[1]
            x2 += self.center[0]
            y2 += self.center[1]
            
            ax.plot([x1, x2], [y1, y2], color='black', linewidth=2)
        
        # Place zodiac sign icons at 30° intervals
        signs = ["ARIES", "TAURUS", "GEMINI", "CANCER", "LEO", "VIRGO",
                "LIBRA", "SCORPIO", "SAGITTARIUS", "CAPRICORN", "AQUARIUS", "PISCES"]
        
        for i, sign in enumerate(signs):
            angle = self._longitude_to_angle(i * 30 + 15, ascendant_longitude)  # Center of sector
            x, y = self._angle_to_position(angle, self.sign_icon_radius)
            
            # Convert to canvas coordinates
            x += self.center[0]
            y += self.center[1]
            
            # Load and place sign icon
            icon = self._load_icon(sign, self.sign_icon_size)
            if icon is not None:
                self._place_icon(ax, icon, x, y, self.sign_icon_size)
    
    def _draw_house_ring(self, ax, chart_data: Dict[str, Any], ascendant_longitude: float = None):
        """Draw the inner house cusps ring."""
        # Draw outer circle of house ring
        outer_circle = Circle(self.center, self.house_ring_outer, fill=False, 
                            color='black', linewidth=2)
        ax.add_patch(outer_circle)
        
        # Draw inner circle of house ring
        inner_circle = Circle(self.center, self.house_ring_inner, fill=False, 
                            color='black', linewidth=2)
        ax.add_patch(inner_circle)
        
        # Place house icons at center of each house sector
        house_cusps = chart_data.get("house_cusps", [])
        for i, house_data in enumerate(house_cusps):
            house_number = str(house_data["house_number"])
            
            # Calculate center angle of house sector
            current_cusp = house_data["longitude"]
            next_cusp = house_cusps[(i + 1) % 12]["longitude"]
            
            # Handle 0° crossing
            if next_cusp < current_cusp:
                next_cusp += 360
            
            center_angle = (current_cusp + next_cusp) / 2
            if center_angle >= 360:
                center_angle -= 360
            
            angle = self._longitude_to_angle(center_angle, ascendant_longitude)
            x, y = self._angle_to_position(angle, self.house_icon_radius)
            
            # Convert to canvas coordinates
            x += self.center[0]
            y += self.center[1]
            
            # Load and place house icon
            icon = self._load_icon(house_number, self.house_icon_size)
            if icon is not None:
                self._place_icon(ax, icon, x, y, self.house_icon_size)
    
    def _draw_planets(self, ax, chart_data: Dict[str, Any], ascendant_longitude: float = None):
        """Draw planets with encoche, icon, and node geometry."""
        planet_positions = chart_data.get("planet_positions", {})
        
        for planet, data in planet_positions.items():
            longitude = data["longitude"]
            (x_on, y_on), (x_tick, y_tick), (x_icon, y_icon), (x_node, y_node), angle = \
                self._planet_geo(longitude, ascendant_longitude)

            # (a) encoche — trait plein, perpendiculaire au cercle, vers le centre
            ax.plot([x_on, x_tick], [y_on, y_tick],
                   color='black', linewidth=3, solid_capstyle='round', zorder=6)

            # (b) icône — juste en dessous de l'encoche
            icon = self._load_icon(planet, self.planet_icon_size)
            if icon is not None:
                self._place_icon(ax, icon, x_icon, y_icon, self.planet_icon_size)
            else:
                # Fallback: draw a black dot if icon is missing
                ax.plot(x_icon, y_icon, 'o', color='black', markersize=10, markeredgewidth=0, zorder=10)

            # (c) nœud — petit cercle **vide** (non rempli), le plus proche du centre
            node = Circle((x_node, y_node), self.node_radius_px, fill=False,
                         linewidth=2, edgecolor='black', zorder=7)
            ax.add_patch(node)
    
    def _draw_angles(self, ax, chart_data: Dict[str, Any], ascendant_longitude: float = None):
        """Draw Ascendant and MC with encoche, icon, and node geometry."""
        angles = chart_data.get("angles", {})
        
        for angle_name, data in angles.items():
            longitude = data["longitude"]
            (x_on, y_on), (x_tick, y_tick), (x_icon, y_icon), (x_node, y_node), angle = \
                self._planet_geo(longitude, ascendant_longitude)

            # (a) encoche — trait plein, perpendiculaire au cercle, vers le centre
            ax.plot([x_on, x_tick], [y_on, y_tick],
                   color='black', linewidth=3, solid_capstyle='round', zorder=6)

            # (b) icône — juste en dessous de l'encoche
            icon = self._load_icon(angle_name, self.planet_icon_size)
            if icon is not None:
                self._place_icon(ax, icon, x_icon, y_icon, self.planet_icon_size)
            else:
                # Fallback: draw a black dot if icon is missing
                ax.plot(x_icon, y_icon, 'o', color='black', markersize=10, markeredgewidth=0, zorder=10)

            # (c) nœud — petit cercle **vide** (non rempli), le plus proche du centre
            node = Circle((x_node, y_node), self.node_radius_px, fill=False,
                         linewidth=2, edgecolor='black', zorder=7)
            ax.add_patch(node)
    
    def _draw_aspects(self, ax, chart_data: Dict[str, Any], ascendant_longitude: float = None):
        """Draw aspect lines between planet nodes with differentiated styles."""
        aspects = chart_data.get("aspects", [])
        planet_positions = chart_data.get("planet_positions", {})
        angles = chart_data.get("angles", {})

        for asp in aspects:
            b1, b2, a_type = asp["body1"], asp["body2"], asp["aspect"]

            def node_pos(body):
                if body in planet_positions:
                    lon = planet_positions[body]["longitude"]
                    _, _, _, (x_n, y_n), _ = self._planet_geo(lon, ascendant_longitude)
                    return x_n, y_n
                elif body in angles:
                    lon = angles[body]["longitude"]
                    _, _, _, (x_n, y_n), _ = self._planet_geo(lon, ascendant_longitude)
                    return x_n, y_n
                return None

            p1 = node_pos(b1)
            p2 = node_pos(b2)
            if not p1 or not p2:
                continue

            style = self._get_aspect_style(a_type)
            ax.plot([p1[0], p2[0]], [p1[1], p2[1]],
                   color=style['color'],
                   linewidth=style['linewidth'],
                   linestyle=style['linestyle'],
                   alpha=0.95, zorder=8)
    
    def _get_aspect_style(self, aspect_type: str) -> Dict[str, Any]:
        """Get styling parameters for different aspect types with colors."""
        styles = {
            "conjunction": {"linewidth": 3, "linestyle": "-", "color": "black"},
            "sextile": {"linewidth": 2, "linestyle": (0, (6, 6)), "color": "violet"},  # 6 on / 6 off
            "square": {"linewidth": 2, "linestyle": "-", "color": "red"},
            "trine": {"linewidth": 2, "linestyle": (0, (10, 8)), "color": "green"},   # 10 on / 8 off
            "opposition": {"linewidth": 2, "linestyle": (0, (4, 4, 1, 4)), "color": "blue"}  # dash-dot
        }
        return styles.get(aspect_type, {"linewidth": 2, "linestyle": "-", "color": "black"})
    
    def _place_icon(self, ax, icon: np.ndarray, x: float, y: float, size: int):
        """Place an icon at the specified position."""
        try:
            oi = OffsetImage(icon, zoom=1.0, interpolation='nearest')
            ab = AnnotationBbox(oi, (x, y), frameon=False, pad=0.0,
                              box_alignment=(0.5, 0.5), zorder=10)
            ax.add_artist(ab)
        except Exception as e:
            logger.warning(f"Could not place icon at ({x}, {y}): {e}")
