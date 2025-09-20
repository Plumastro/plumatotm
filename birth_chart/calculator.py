"""
Birth Chart Calculator

Handles all astrological calculations using flatlib:
- Planetary positions
- House cusps
- Major aspects
"""

import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from zoneinfo import ZoneInfo

try:
    from timezonefinderL import TimezoneFinder
    HAS_TIMEZONEFINDER = True
except ImportError:
    HAS_TIMEZONEFINDER = False

try:
    from flatlib import const
    from flatlib.chart import Chart
    from flatlib.datetime import Datetime
    from flatlib.geopos import GeoPos
    from flatlib.object import Object
    HAS_FLATLIB = True
except ImportError:
    HAS_FLATLIB = False

logger = logging.getLogger(__name__)

class BirthChartCalculator:
    """Calculates astrological birth chart data using flatlib."""
    
    def __init__(self):
        if not HAS_FLATLIB:
            raise ImportError("flatlib is required. Install with: pip install flatlib")
        if not HAS_TIMEZONEFINDER:
            raise ImportError("timezonefinderL is required. Install with: pip install timezonefinderL")
        
        # Supported planets and points
        self.planets = [
            "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", 
            "Saturn", "Uranus", "Neptune", "Pluto", "North Node"
        ]
        
        # Major aspects with orbs (in degrees)
        self.major_aspects = {
            "conjunction": 8.0,    # 0° ± 8°
            "sextile": 6.0,        # 60° ± 6°
            "square": 6.0,         # 90° ± 6°
            "trine": 6.0,          # 120° ± 6°
            "opposition": 8.0      # 180° ± 8°
        }
        
        # Aspect angles
        self.aspect_angles = {
            "conjunction": 0,
            "sextile": 60,
            "square": 90,
            "trine": 120,
            "opposition": 180
        }
    
    def convert_local_to_utc(self, date: str, time: str, lat: float, lon: float) -> Tuple[str, str]:
        """
        Convert local time to UTC based on coordinates.
        
        Args:
            date: Date in YYYY-MM-DD format
            time: Local time in HH:MM format
            lat: Latitude
            lon: Longitude
        
        Returns:
            Tuple of (UTC time in HH:MM format, timezone detection method)
        """
        try:
            # Use timezonefinderL for accurate timezone detection
            tf = TimezoneFinder()
            timezone_name = tf.timezone_at(lat=lat, lng=lon)
            
            if not timezone_name:
                raise ValueError(f"Could not determine timezone for coordinates ({lat}, {lon})")
            
            # Special correction for Israel coordinates
            if timezone_name == "Asia/Hebron" and 31.0 <= lat <= 33.5 and 34.0 <= lon <= 35.5:
                timezone_name = "Asia/Jerusalem"
                detection_method = "timezonefinder_corrected_israel"
            else:
                detection_method = "timezonefinder_automatic"
            
            # Parse date and time components
            y, m, d = map(int, date.split("-"))
            hh, mm = map(int, time.split(":"))
            
            # Build naive datetime
            local_naive = datetime(y, m, d, hh, mm)
            
            # Attach timezone
            local_dt = local_naive.replace(tzinfo=ZoneInfo(timezone_name))
            
            # Convert to UTC
            utc_dt = local_dt.astimezone(ZoneInfo("UTC"))
            
            # Format as HH:MM
            utc_time = utc_dt.strftime("%H:%M")
            
            logger.info(f"Timezone detected: {timezone_name} (method: {detection_method})")
            logger.info(f"Local time: {time} → UTC time: {utc_time}")
            
            return utc_time, detection_method
            
        except Exception as e:
            raise ValueError(f"Error converting local time to UTC: {e}")
    
    def calculate_birth_chart(self, date: str, time: str, lat: float, lon: float, 
                            house_system: str = "placidus") -> Dict[str, Any]:
        """
        Calculate complete birth chart data.
        
        Args:
            date: Date in YYYY-MM-DD format
            time: Local time in HH:MM format
            lat: Latitude
            lon: Longitude
            house_system: House system ("placidus" or "porphyry")
        
        Returns:
            Dictionary containing all birth chart data
        """
        try:
            # Convert local time to UTC
            utc_time, timezone_method = self.convert_local_to_utc(date, time, lat, lon)
            
            # Parse date and format for flatlib
            date_formatted = date.replace('-', '/')
            utc_date = date_formatted  # Will be updated if date changes during conversion
            
            # Check if date changed during UTC conversion
            y, m, d = map(int, date.split("-"))
            hh, mm = map(int,time.split(":"))
            local_naive = datetime(y, m, d, hh, mm)
            
            tf = TimezoneFinder()
            timezone_name = tf.timezone_at(lat=lat, lng=lon)
            if timezone_name == "Asia/Hebron" and 31.0 <= lat <= 33.5 and 34.0 <= lon <= 35.5:
                timezone_name = "Asia/Jerusalem"
            
            local_dt = local_naive.replace(tzinfo=ZoneInfo(timezone_name))
            utc_dt = local_dt.astimezone(ZoneInfo("UTC"))
            utc_date = utc_dt.strftime("%Y/%m/%d")
            
            # Create flatlib Datetime
            dt = Datetime(utc_date, utc_time, 0)
            
            # Choose house system
            if house_system.lower() == "porphyry" or abs(lat) > 66.0:
                house_sys = const.HOUSES_PORPHYRIUS
                logger.info(f"Using Porphyry house system (high latitude: {lat:.2f}°)")
            else:
                house_sys = const.HOUSES_PLACIDUS
                logger.info(f"Using Placidus house system")
            
            # Create chart
            pos = GeoPos(lat, lon)
            custom_objects = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 
                            'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto', 'North Node']
            chart = Chart(dt, pos, hsys=house_sys, IDs=custom_objects)
            
            # Extract planetary positions
            planet_positions = self._extract_planet_positions(chart)
            
            # Extract house cusps
            house_cusps = self._extract_house_cusps(chart)
            
            # Extract angles (AC, MC)
            angles = self._extract_angles(chart)
            
            # Calculate major aspects
            aspects = self._calculate_major_aspects(planet_positions)
            
            return {
                "birth_data": {
                    "date": date,
                    "time": time,
                    "utc_time": utc_time,
                    "lat": lat,
                    "lon": lon,
                    "timezone_method": timezone_method
                },
                "planet_positions": planet_positions,
                "house_cusps": house_cusps,
                "angles": angles,
                "aspects": aspects,
                "chart_metadata": {
                    "house_system": house_system,
                    "zodiac": "tropical",
                    "node_type": "mean"
                }
            }
            
        except Exception as e:
            raise ValueError(f"Error calculating birth chart: {e}")
    
    def _extract_planet_positions(self, chart: Chart) -> Dict[str, Dict[str, Any]]:
        """Extract planetary positions from chart."""
        positions = {}
        
        for planet in self.planets:
            try:
                if planet == "North Node":
                    obj = chart.get("North Node")
                else:
                    obj = chart.get(planet)
                
                positions[planet] = {
                    "longitude": obj.lon,
                    "sign": obj.sign,
                    "sign_degrees": obj.lon % 30,
                    "house": self._get_house_number(obj.lon, chart.houses)
                }
                
                logger.debug(f"{planet}: {obj.sign} {obj.lon:.3f}° (House {positions[planet]['house']})")
                
            except Exception as e:
                logger.warning(f"Could not get {planet}: {e}")
                continue
        
        return positions
    
    def _extract_house_cusps(self, chart: Chart) -> List[Dict[str, Any]]:
        """Extract house cusps from chart."""
        cusps = []
        
        for i, house in enumerate(chart.houses, 1):
            cusps.append({
                "house_number": i,
                "longitude": house.lon,
                "sign": self._longitude_to_sign(house.lon),
                "sign_degrees": house.lon % 30
            })
        
        return cusps
    
    def _extract_angles(self, chart: Chart) -> Dict[str, Dict[str, Any]]:
        """Extract Ascendant and MC from chart."""
        asc = chart.getAngle(const.ASC)
        mc = chart.getAngle(const.MC)
        
        return {
            "Ascendant": {
                "longitude": asc.lon,
                "sign": asc.sign,
                "sign_degrees": asc.lon % 30
            },
            "MC": {
                "longitude": mc.lon,
                "sign": mc.sign,
                "sign_degrees": mc.lon % 30
            }
        }
    
    def _get_house_number(self, longitude: float, houses) -> int:
        """Get house number for a given longitude."""
        longitude = longitude % 360
        
        for i, house in enumerate(houses, 1):
            house_cusp = house.lon % 360
            next_house_cusp = houses[i % 12].lon % 360 if i < 12 else houses[0].lon % 360
            
            # Handle crossing 0°
            if next_house_cusp < house_cusp:
                if longitude >= house_cusp or longitude < next_house_cusp:
                    return i
            else:
                if house_cusp <= longitude < next_house_cusp:
                    return i
        
        return 1  # Fallback
    
    def _longitude_to_sign(self, longitude: float) -> str:
        """Convert longitude to zodiac sign."""
        signs = ["ARIES", "TAURUS", "GEMINI", "CANCER", "LEO", "VIRGO",
                "LIBRA", "SCORPIO", "SAGITTARIUS", "CAPRICORN", "AQUARIUS", "PISCES"]
        return signs[int(longitude // 30)]
    
    def _calculate_major_aspects(self, planet_positions: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate major aspects between planets."""
        aspects = []
        
        # Get all planets including angles
        all_bodies = list(planet_positions.keys()) + ["Ascendant", "MC"]
        
        for i, body1 in enumerate(all_bodies):
            for body2 in all_bodies[i+1:]:
                try:
                    # Get longitudes
                    if body1 in planet_positions:
                        lon1 = planet_positions[body1]["longitude"]
                    elif body1 == "Ascendant":
                        # We need to get this from the chart, but for now skip
                        continue
                    elif body1 == "MC":
                        # We need to get this from the chart, but for now skip
                        continue
                    else:
                        continue
                    
                    if body2 in planet_positions:
                        lon2 = planet_positions[body2]["longitude"]
                    elif body2 == "Ascendant":
                        continue
                    elif body2 == "MC":
                        continue
                    else:
                        continue
                    
                    # Calculate angular distance
                    angular_distance = abs(lon1 - lon2)
                    if angular_distance > 180:
                        angular_distance = 360 - angular_distance
                    
                    # Check for major aspects
                    for aspect_name, target_angle in self.aspect_angles.items():
                        orb = self.major_aspects[aspect_name]
                        if abs(angular_distance - target_angle) <= orb:
                            aspects.append({
                                "body1": body1,
                                "body2": body2,
                                "aspect": aspect_name,
                                "orb": abs(angular_distance - target_angle),
                                "angular_distance": angular_distance
                            })
                            break
                
                except Exception as e:
                    logger.warning(f"Error calculating aspect between {body1} and {body2}: {e}")
                    continue
        
        return aspects
