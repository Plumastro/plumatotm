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

# Cache global pour les icônes redimensionnées
_icon_cache = {}

class BirthChartRenderer:
    """Renders birth charts as PNG images."""
    
    def __init__(self, icons_dir: str = "icons"):
        self.icons_dir = icons_dir
        self.canvas_size = 1000  # Réduit de 1500 à 1000 (-33% de pixels)
        self.dpi = 100  # Restauré à 100 pour une meilleure qualité
        
        # Chart dimensions according to FRS specifications
        # Centre: (500, 500), Rayon utile R ≈ 467px (même proportion)
        self.center = (500, 500)
        self.R = 467  # Rayon utile (1000/1500 * 700)
        
        # Rayons spécifiés dans le FRS (en pixels) - COURONNE DES SIGNES 25% PLUS FINE
        self.sign_ring_outer = self.R * 0.97  # R*0.97 (inchangé)
        
        # Ancienne épaisseur = self.sign_ring_outer - 0.70*R
        old_inner = self.R * 0.70
        old_thick = self.sign_ring_outer - old_inner
        new_thick = old_thick * 0.75  # 25% plus fin (épaisseur de bande inchangée)
        self.sign_ring_inner = self.sign_ring_outer - new_thick
        
        # icône de signe au centre de la bande
        self.sign_icon_radius = (self.sign_ring_outer + self.sign_ring_inner) / 2.0
        
        self.house_ring_outer = self.R * 0.28    # ↓ encore plus vers le centre
        self.house_ring_inner = self.R * 0.18    # ↓ même épaisseur
        self.house_icon_radius = (self.house_ring_inner + self.house_ring_outer) / 2.0  # = 0.23R (toujours au centre)
        
        # --- tout le bloc "position" est poussé vers l'extérieur ---
        # cercle pointillé juste à l'intérieur de la nouvelle couronne des signes
        self.position_radius = self.sign_ring_inner - self.R * 0.03
        self.grid_radii = [self.position_radius]
        
        # géométrie encoche / icône / nœud (on conserve les gaps, simplement *au-dessus*)
        self.planet_tick_len = self.R * 0.020
        self.icon_gap        = self.R * 0.070  # légèrement réduit pour rapprocher les icônes des encoches
        self.node_gap        = self.R * 0.070  # encore plus réduit pour rapprocher les nœuds des icônes
        self.node_radius_px  = 6
        
        self.planet_icon_radius = self.position_radius - (self.planet_tick_len + self.icon_gap)
        self.node_radius        = self.planet_icon_radius - self.node_gap
        
        # garde une marge au-dessus de la couronne des maisons
        self.node_radius = max(self.node_radius, self.house_ring_outer + self.R * 0.04)
        
        self.planet_radius = self.planet_icon_radius
        self.asc_mc_radius = self.planet_icon_radius
        
        # aspects confinés à la limite intérieure des maisons (inchangé)
        self.aspect_max_radius = self.house_ring_inner
        
        # Icon sizes according to FRS - CORRIGÉS (même taille, meilleure qualité)
        self.sign_icon_size = 48  # Taille originale
        self.house_icon_size = 32 # Taille originale
        self.planet_icon_size = 48 # Taille originale
        
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
        """Load an icon from the icons directory with caching."""
        # Check instance cache first
        if name in self.loaded_icons:
            return self.loaded_icons[name]
        
        if name not in self.icon_mappings:
            logger.warning(f"No icon mapping for {name}")
            return None
        
        for filename in self.icon_mappings[name]:
            icon_path = os.path.join(self.icons_dir, filename)
            if os.path.exists(icon_path):
                # Create cache key with path and size
                cache_key = f"{icon_path}_{size}"
                
                # Check global cache first
                if cache_key in _icon_cache:
                    self.loaded_icons[name] = _icon_cache[cache_key]
                    logger.debug(f"Loaded icon from cache: {filename} for {name}")
                    return _icon_cache[cache_key]
                
                try:
                    # Load and resize icon with high quality
                    img = Image.open(icon_path).convert("RGBA")
                    # Utiliser un redimensionnement de haute qualité
                    img = img.resize((size, size), Image.Resampling.LANCZOS)
                    # Assurer que l'image a une bonne qualité
                    icon_array = np.asarray(img)
                    
                    # Store in both caches
                    _icon_cache[cache_key] = icon_array
                    self.loaded_icons[name] = icon_array
                    
                    logger.debug(f"Loaded and cached icon: {filename} for {name}")
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
            # AC à 9h (180°), anti-horaire
            theta_deg = (180 + (longitude - ascendant_longitude)) % 360
            return np.radians(theta_deg)
        else:
            return np.radians((180 + longitude) % 360)
    
    def _angle_to_position(self, angle: float, radius: float) -> Tuple[float, float]:
        """Convert angle and radius to x, y coordinates."""
        x = radius * np.cos(angle)
        y = radius * np.sin(angle)
        return x, y
    
    def _compute_icon_angle_offsets(
        self,
        planet_positions: Dict[str, Any],
        ascendant_longitude: Optional[float],
        angles: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, float]:
        """
        Icons are assumed the SAME size.
        Enforce a constant min center-to-center spacing 'd' (radians)
        and compute minimal-movement offsets for icons only.
        Consider planets + ASC + MC together.
        """
        # ----- 1) Collect desired angles for all bodies -----
        bodies = []
        for name, data in planet_positions.items():
            ang = float(self._longitude_to_angle(data["longitude"], ascendant_longitude))
            bodies.append((name, ang))
        if angles:
            for name, data in angles.items():
                ang = float(self._longitude_to_angle(data["longitude"], ascendant_longitude))
                bodies.append((name, ang))

        if not bodies:
            return {}

        names = [n for n, _ in bodies]
        a_des = np.array([a for _, a in bodies], dtype=float)

        # ----- 2) Constant angular spacing d from icon size on this radius -----
        r = max(self.planet_icon_radius, 1.0)
        icon_px = float(self.planet_icon_size)
        halo_px = 3.5   # moderate pixels to cover antialias/outline
        safety  = 1.15  # moderate cushion for balanced spacing
        half_w  = 0.5 * icon_px + halo_px
        # use arctan for robust geometry (or replace with half_w/r for small-angle approx)
        half_rad = float(np.arctan(half_w / r)) * safety
        d = 2.6 * half_rad   # balanced center-to-center clearance for all neighbors (increased to 2.6)

        # ----- 3) Sort around circle, break at largest natural gap -----
        order = np.argsort(a_des)
        a_sorted = a_des[order]
        names_sorted = [names[i] for i in order]

        # natural free gaps (center-to-center) on the circle
        gaps = np.diff(a_sorted, append=a_sorted[0] + 2*np.pi)
        k_break = int(np.argmax(gaps))  # start after the largest gap

        def rot(x): return np.concatenate([x[k_break+1:], x[:k_break+1]])
        a_rot = rot(a_sorted)
        names_rot = names_sorted[k_break+1:] + names_sorted[:k_break+1]

        # unwrap to a line
        a_unwrap = np.unwrap(a_rot)

        # ----- 4) Isotonic regression (PAV) on u = a - G with constant spacing -----
        # Required min spacing sequence relative to previous: [0, d, d, ...]
        s = np.zeros_like(a_unwrap)
        if len(s) > 1:
            s[1:] = d
        G = np.cumsum(s)        # G[0]=0, G[i]=i*d
        u = a_unwrap - G        # must be non-decreasing

        # Pool-Adjacent-Violators (weights=1)
        def pav(y: np.ndarray) -> np.ndarray:
            n = len(y)
            v = y.copy().tolist()
            w = [1.0] * n
            i0 = list(range(n))  # block starts
            i1 = list(range(n))  # block ends
            k = 0
            while k < len(v) - 1:
                if v[k] <= v[k+1]:
                    k += 1; continue
                # merge k and k+1
                nv = (w[k]*v[k] + w[k+1]*v[k+1]) / (w[k]+w[k+1])
                nw = w[k] + w[k+1]
                v[k] = nv; w[k] = nw; i1[k] = i1[k+1]
                del v[k+1]; del w[k+1]; del i0[k+1]; del i1[k+1]
                while k > 0 and v[k-1] > v[k]:
                    nv = (w[k-1]*v[k-1] + w[k]*v[k]) / (w[k-1]+w[k])
                    nw = w[k-1] + w[k]
                    v[k-1] = nv; w[k-1] = nw; i1[k-1] = i1[k]
                    del v[k]; del w[k]; del i0[k]; del i1[k]
                    k -= 1
            out = np.empty(n, dtype=float)
            for val, a, b in zip(v, i0, i1):
                out[a:b+1] = val
            return out

        u_star = pav(u)
        y = u_star + G  # final angles on the line

        # map back to names and produce offsets near originals
        final_angles = {n: ang for n, ang in zip(names_rot, y)}
        # restore original order names[]/a_des[]
        offsets: Dict[str, float] = {}
        for n, a0 in zip(names, a_des):
            af = final_angles[n]
            dth = (af - a0 + np.pi) % (2*np.pi) - np.pi
            offsets[n] = float(dth)
        return offsets
    
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
            # Create figure with transparent background
            fig, ax = plt.subplots(figsize=(self.canvas_size/self.dpi, self.canvas_size/self.dpi),
                                 dpi=self.dpi, facecolor='none')
            ax.set_facecolor('none')
            
            # Set equal aspect ratio and remove axes
            ax.set_aspect('equal')
            ax.set_xlim(0, self.canvas_size)
            ax.set_ylim(0, self.canvas_size)
            ax.axis('off')
            
            # Get Ascendant longitude for proper positioning
            ascendant_longitude = None
            pp = chart_data.get("planet_positions", {})
            if "Ascendant" in pp:
                ascendant_longitude = pp["Ascendant"]["longitude"]
            
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
            
            # Save with transparent background and high quality
            plt.tight_layout()
            plt.savefig(output_path, dpi=self.dpi, bbox_inches='tight',
                       facecolor='none', transparent=True, pad_inches=0,
                       format='png')
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
                          color='black', linewidth=2, linestyle=(0, (2, 3)), alpha=0.8, zorder=1)
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
            
            # Dotted extension to position circle
            start_radius = self.house_ring_outer
            end_radius = self.position_radius   # stoppe sur le cercle planètes
            
            x1, y1 = self._angle_to_position(angle, start_radius)
            x2, y2 = self._angle_to_position(angle, end_radius)
            
            # Convert to canvas coordinates
            x1 += self.center[0]
            y1 += self.center[1]
            x2 += self.center[0]
            y2 += self.center[1]
            
            ax.plot([x1, x2], [y1, y2], color='black', linewidth=1.5, 
                   linestyle='--', alpha=0.8, zorder=5)

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
        angles = chart_data.get("angles", {})  # include ASC / MC here
        print(f"[DEBUG] planets count = {len(planet_positions)}")
        
        # compute unified offsets (planets + ASC/MC)
        icon_angle_offsets = self._compute_icon_angle_offsets(
            planet_positions, ascendant_longitude, angles=angles
        )
        
        for planet, data in planet_positions.items():
            print(f"[DEBUG] planet={planet}, lon={data['longitude']:.2f}")
            longitude = data["longitude"]
            (x_on, y_on), (x_tick, y_tick), (_, _), (x_node, y_node), base_angle = \
                self._planet_geo(longitude, ascendant_longitude)

            # (a) encoche (à l'angle exact)
            ax.plot([x_on, x_tick], [y_on, y_tick],
                   color='black', linewidth=5, solid_capstyle='round', zorder=18)

            # (b) icône (avec décalage angulaire si nécessaire)
            dth = icon_angle_offsets.get(planet, 0.0)
            icon_angle = base_angle + dth
            xi, yi = self._angle_to_position(icon_angle, self.planet_icon_radius)
            xi += self.center[0]; yi += self.center[1]
            print(f"[DEBUG] {planet} xy_icon=({xi:.1f},{yi:.1f}) xy_node=({x_node:.1f},{y_node:.1f})")
            
            icon = self._load_icon(planet, self.planet_icon_size)
            if icon is not None:
                self._place_icon(ax, icon, xi, yi, self.planet_icon_size)
            else:
                # Fallback: draw a black dot if icon is missing
                ax.plot(xi, yi, 'o', color='black', markersize=12, markeredgewidth=0, zorder=20)

            # (c) nœud (à l'angle exact)
            node = Circle((x_node, y_node), self.node_radius_px, fill=False,
                         linewidth=2.2, edgecolor='black', zorder=19)
            ax.add_patch(node)
    
    def _draw_angles(self, ax, chart_data: Dict[str, Any], ascendant_longitude: float = None):
        """Draw Ascendant and MC with encoche, icon, and node geometry."""
        angles = chart_data.get("angles", {})
        planet_positions = chart_data.get("planet_positions", {})
        
        # reuse the same offsets dict computed once in _draw_planets,
        # or compute here in case you keep functions independent:
        icon_angle_offsets = self._compute_icon_angle_offsets(
            planet_positions, ascendant_longitude, angles=angles
        )
        
        for angle_name, data in angles.items():
            longitude = data["longitude"]
            (x_on, y_on), (x_tick, y_tick), (x_icon, y_icon), (x_node, y_node), base_angle = \
                self._planet_geo(longitude, ascendant_longitude)

            # (a) encoche — trait plein, perpendiculaire au cercle, vers le centre
            ax.plot([x_on, x_tick], [y_on, y_tick],
                   color='black', linewidth=5, solid_capstyle='round', zorder=18)

            # (b) icône — avec décalage angulaire si nécessaire (so ASC/MC also avoid overlap)
            dth = icon_angle_offsets.get(angle_name, 0.0)
            icon_angle = base_angle + dth
            xi, yi = self._angle_to_position(icon_angle, self.planet_icon_radius)
            xi += self.center[0]; yi += self.center[1]
            
            icon = self._load_icon(angle_name, self.planet_icon_size)
            if icon is not None:
                self._place_icon(ax, icon, xi, yi, self.planet_icon_size)
            else:
                # Fallback: draw a black dot if icon is missing
                ax.plot(xi, yi, 'o', color='black', markersize=12, markeredgewidth=0, zorder=20)

            # (c) nœud — petit cercle **vide** (non rempli), le plus proche du centre
            node = Circle((x_node, y_node), self.node_radius_px, fill=False,
                         linewidth=2.2, edgecolor='black', zorder=19)
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
            
            # Pour les conjonctions blanches, ajouter un backing gris pour la visibilité
            if a_type == "conjunction":
                ax.plot([p1[0], p2[0]], [p1[1], p2[1]],
                       color="#111827", linewidth=5.0, alpha=0.15, zorder=11)
            
            ax.plot([p1[0], p2[0]], [p1[1], p2[1]],
                   color=style['color'],
                   linewidth=style['linewidth'],
                   linestyle=style['linestyle'],
                   alpha=0.95, zorder=12)
    
    def _get_aspect_style(self, aspect_type: str) -> Dict[str, Any]:
        """Get styling parameters for different aspect types with darker colors."""
        styles = {
            "conjunction": {"linewidth": 4.2, "linestyle": "-", "color": "#FFFFFF"},  # blanc
            "sextile":     {"linewidth": 4.2, "linestyle": "-", "color": "#2563EB"},  # bleu foncé
            "square":      {"linewidth": 4.2, "linestyle": "-", "color": "#B91C1C"},  # rouge foncé
            "trine":       {"linewidth": 4.2, "linestyle": "-", "color": "#166534"},  # vert foncé
            "opposition":  {"linewidth": 4.2, "linestyle": "-", "color": "#C2410C"},  # orange foncé
        }
        return styles.get(aspect_type, {"linewidth": 3.8, "linestyle": "-", "color": "#111827"})
    
    def _place_icon(self, ax, icon: np.ndarray, x: float, y: float, size: int):
        """Place an icon at the specified position with high quality rendering."""
        try:
            # Calculer le zoom optimal pour la résolution
            zoom_factor = size / icon.shape[0]  # Ajustement automatique du zoom
            
            oi = OffsetImage(icon, zoom=zoom_factor, interpolation='bilinear')
            ab = AnnotationBbox(oi, (x, y), frameon=False, pad=0.0,
                              box_alignment=(0.5, 0.5))
            ab.set_zorder(20)  # icônes tout en haut
            ax.add_artist(ab)
        except Exception as e:
            logger.warning(f"Could not place icon at ({x}, {y}): {e}")
