#!/usr/bin/env python3
"""
PLUMATOTM Animal × Planet Scoring System (Final Working Version)

This program computes animal scores based on birth chart data using astrological
planets and their zodiac signs, applying predefined weights and scoring tables.

This version uses flatlib for accurate astrological calculations.
"""

import argparse
import json
import csv
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Any
import sys
import os

# Charger les variables d'environnement depuis .env
try:
    from dotenv import load_dotenv
    load_dotenv()  # Charge le fichier .env
except ImportError:
    pass  # python-dotenv non installé, continuer sans

# Import des modules de statistiques
try:
    from animal_statistics import AnimalStatisticsGenerator
    STATISTICS_AVAILABLE = True
except ImportError:
    STATISTICS_AVAILABLE = False
    print("⚠️  Module de statistiques non disponible")
from zoneinfo import ZoneInfo

# OpenAI API for ChatGPT interpretation
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    print("Warning: openai library not available, ChatGPT interpretation will be skipped")

# Try to import timezonefinderL (lightweight version), fall back to manual detection if not available
try:
    from timezonefinderL import TimezoneFinder
    HAS_TIMEZONEFINDER = True
except ImportError:
    HAS_TIMEZONEFINDER = False
    print("Warning: timezonefinderL not available. Please install it with: pip install timezonefinderL")

# Import flatlib for astrological calculations
try:
    from flatlib import const
    from flatlib.chart import Chart
    from flatlib.datetime import Datetime
    from flatlib.geopos import GeoPos
    from flatlib.object import Object
except ImportError as e:
    print(f"Error: flatlib is required. Install with: pip install flatlib")
    print(f"Import error details: {e}")
    sys.exit(1)

# Zodiac signs for validation
ZODIAC_SIGNS = [
    "ARIES", "TAURUS", "GEMINI", "CANCER", "LEO", "VIRGO",
    "LIBRA", "SCORPIO", "SAGITTARIUS", "CAPRICORN", "AQUARIUS", "PISCES"
]

# Utility functions to replace pandas functionality
def read_csv_to_dict(csv_path: str, encoding: str = 'utf-8') -> List[Dict[str, Any]]:
    """Read CSV file and return list of dictionaries."""
    data = []
    try:
        with open(csv_path, 'r', encoding=encoding) as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(dict(row))
    except UnicodeDecodeError:
        # Try with latin-1 encoding
        with open(csv_path, 'r', encoding='latin-1') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(dict(row))
    return data

def safe_float(value: Any) -> float:
    """Safely convert value to float, handling NaN and empty strings."""
    if value is None or value == '' or str(value).lower() in ['nan', 'none']:
        return 0.0
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def safe_str(value: Any) -> str:
    """Safely convert value to string, handling NaN."""
    if value is None or str(value).lower() in ['nan', 'none']:
        return ""
    return str(value).strip()

def sort_dict_by_value(data: Dict[str, float], reverse: bool = True) -> List[Tuple[str, float]]:
    """Sort dictionary by values and return list of tuples."""
    return sorted(data.items(), key=lambda x: x[1], reverse=reverse)

def get_top_n(data: List[Tuple[str, float]], n: int = 3) -> List[Tuple[str, float]]:
    """Get top N items from sorted list."""
    return data[:n]

def save_dict_to_csv(data: Dict[str, Dict[str, Any]], filepath: str):
    """Save dictionary data to CSV file."""
    import csv
    if not data:
        return
    
    # Get all unique keys from all dictionaries
    all_keys = set()
    for animal_data in data.values():
        all_keys.update(animal_data.keys())
    
    # Sort keys for consistent output
    sorted_keys = sorted(all_keys)
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Write header
        writer.writerow(['ANIMAL'] + sorted_keys)
        
        # Write data rows
        for animal, animal_data in data.items():
            row = [animal]
            for key in sorted_keys:
                row.append(animal_data.get(key, 0))
            writer.writerow(row)

def save_list_to_csv(data: List[Tuple[str, float]], filepath: str):
    """Save list of tuples to CSV file."""
    import csv
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ANIMAL', 'TOTAL_SCORE'])
        for animal, score in data:
            writer.writerow([animal, score])


def _get_corrected_house_number(planet_lon: float, houses) -> int:
    """Get house number without the problematic -5° offset used by flatlib."""
    # Convert to 0-360 range
    planet_lon = planet_lon % 360
    
    # Convert HouseList to list for easier indexing
    house_list = list(houses)
    
    # Find the house by checking which house cusp the planet is closest to
    # without the -5° offset
    for i, house in enumerate(house_list, 1):
        house_cusp = house.lon % 360
        next_house_cusp = house_list[i % 12].lon % 360 if i < 12 else house_list[0].lon % 360
        
        # Handle the case where we cross 0°
        if next_house_cusp < house_cusp:
            # We're crossing 0°, so the house spans from house_cusp to 360° and from 0° to next_house_cusp
            if planet_lon >= house_cusp or planet_lon < next_house_cusp:
                return i
        else:
            # Normal case, house spans from house_cusp to next_house_cusp
            # Use < for the upper bound (exclusive) as the next house starts at the next cusp
            if house_cusp <= planet_lon < next_house_cusp:
                return i
    
    # If we get here, the planet is exactly on a cusp, return the next house
    # Find the closest house cusp
    min_distance = float('inf')
    correct_house = 1
    
    for i, house in enumerate(house_list, 1):
        house_cusp = house.lon % 360
        distance = abs(planet_lon - house_cusp)
        if distance > 180:
            distance = 360 - distance
        
        if distance < min_distance:
            min_distance = distance
            correct_house = i
    
    return correct_house

def convert_local_to_utc(date: str, local_time: str, lat: float, lon: float) -> tuple[str, str]:
    """
    Convert local time to UTC based on coordinates.
    
    Args:
        date: Date in YYYY-MM-DD format
        local_time: Local time in HH:MM format
        lat: Latitude
        lon: Longitude
    
    Returns:
        Tuple of (UTC time in HH:MM format, timezone detection method)
    """
    try:
        # Force timezonefinderL usage - no manual fallback
        if not HAS_TIMEZONEFINDER:
            raise ValueError("timezonefinderL is required but not available. Please install it with: pip install timezonefinderL")
        
        # Use timezonefinderL for accurate timezone detection
        tf = TimezoneFinder()
        timezone_name = tf.timezone_at(lat=lat, lng=lon)
        
        if not timezone_name:
            raise ValueError(f"timezonefinderL could not determine timezone for coordinates ({lat}, {lon}). Please check coordinates or install timezonefinderL with: pip install timezonefinderL")
        
        # Special correction for Israel coordinates
        # timezonefinderL sometimes returns Asia/Hebron instead of Asia/Jerusalem for Israeli coordinates
        if timezone_name == "Asia/Hebron" and 31.0 <= lat <= 33.5 and 34.0 <= lon <= 35.5:
            timezone_name = "Asia/Jerusalem"
            detection_method = "timezonefinder_corrected_israel"
        else:
            detection_method = "timezonefinder_automatic"
        
        # Parse date and time components
        y, m, d = map(int, date.split("-"))
        hh, mm = map(int, local_time.split(":"))
        
        # Build naive datetime
        local_naive = datetime(y, m, d, hh, mm)
        
        # Attach timezone
        local_dt = local_naive.replace(tzinfo=ZoneInfo(timezone_name))
        
        # Convert to UTC
        utc_dt = local_dt.astimezone(ZoneInfo("UTC"))
        
        # Format as HH:MM
        utc_time = utc_dt.strftime("%H:%M")
        
        # Check if DST is active
        dst_offset = local_dt.dst().total_seconds() / 3600 if local_dt.dst() else 0
        dst_status = "DST ON" if dst_offset > 0 else "DST OFF"
        
        print(f"Timezone detected: {timezone_name} (method: {detection_method})")
        print(f"Local time: {local_time} → Timezone: {timezone_name} → {dst_status} → UTC time: {utc_time}")
        print(f"DST offset: {dst_offset:.1f} hours")
        
        return utc_time, detection_method
        
    except Exception as e:
        raise ValueError(f"Error converting local time to UTC: {e}")


class BirthChartAnalyzer:
    """Main class for analyzing birth charts and computing animal scores."""
    
    def __init__(self, scores_csv_path: str, weights_csv_path: str, multipliers_csv_path: str, translations_csv_path: str = None):
        """Initialize with the animal scores CSV file and planet weights/multipliers."""
        # Store file paths for lazy loading
        self.scores_csv_path = scores_csv_path
        self.weights_csv_path = weights_csv_path
        self.multipliers_csv_path = multipliers_csv_path
        self.translations_csv_path = translations_csv_path
        
        # Initialize lazy loading flags
        self._scores_data_loaded = False
        self._planet_weights_loaded = False
        self._planet_multipliers_loaded = False
        self._animal_translations_loaded = False
        
        # Load only essential data at startup - scores will be loaded on demand
        self.scores_data = None  # Lazy loading
        self.animals = None  # Will be loaded when needed
        
        # Load planet weights and multipliers (small files, keep at startup)
        self.planet_weights = self._load_planet_weights(weights_csv_path)
        self.planet_multipliers = self._load_planet_multipliers(multipliers_csv_path)
        self.supported_planets = list(self.planet_weights.keys())
        
        # Animal translations will be loaded on demand
        self.animal_translations = {}
    
    def _ensure_scores_data_loaded(self):
        """Load scores data on demand if not already loaded."""
        if not self._scores_data_loaded:
            self.scores_data = self._load_scores_from_csv(self.scores_csv_path)
            self.animals = [animal["ANIMAL"] for animal in self.scores_data["animals"]]
            self._scores_data_loaded = True
    
    def _ensure_animal_translations_loaded(self):
        """Load animal translations on demand if not already loaded."""
        if not self._animal_translations_loaded and self.translations_csv_path and os.path.exists(self.translations_csv_path):
            self.animal_translations = self._load_animal_translations(self.translations_csv_path)
            self._animal_translations_loaded = True
        
    def _load_scores_from_csv(self, scores_csv_path: str) -> Dict:
        """Load and validate the animal scores from CSV file."""
        try:
            data = read_csv_to_dict(scores_csv_path)
            
            # Convert CSV data to the expected JSON structure
            animals = []
            for row in data:
                animal_entry = {
                    "ANIMAL": row["AnimalEN"]
                }
                
                # Add scores for each zodiac sign
                for sign in ZODIAC_SIGNS:
                    # Map zodiac sign names to CSV column names
                    csv_column = sign.capitalize()  # ARIES -> Aries
                    if csv_column in row:
                        score = safe_float(row[csv_column])
                        if score < 0 or score > 100:
                            raise ValueError(f"Invalid score for {animal_entry['ANIMAL']} - {sign}: {score}")
                        animal_entry[sign] = score
                    else:
                        raise ValueError(f"Missing score column for {sign} in CSV")
                
                animals.append(animal_entry)
            
            return {"animals": animals}
            
        except FileNotFoundError:
            raise FileNotFoundError(f"Scores CSV file not found: {scores_csv_path}")
        except Exception as e:
            raise ValueError(f"Error loading scores from CSV: {e}")
    
    def _load_planet_weights(self, weights_csv_path: str) -> Dict[str, float]:
        """Load planet weights from CSV file."""
        try:
            data = read_csv_to_dict(weights_csv_path)
            weights = {}
            
            # Find the row with 'PlanetWeight'
            for row in data:
                if row.get('Planet', '').strip() == 'PlanetWeight':
                    for key, value in row.items():
                        if key != 'Planet':  # Skip first column
                            weights[key] = safe_float(value)
                    break
            
            return weights
        except Exception as e:
            raise ValueError(f"Error loading planet weights from {weights_csv_path}: {e}")
    
    def _load_planet_multipliers(self, multipliers_csv_path: str) -> Dict[str, Dict[str, float]]:
        """Load planet multipliers from CSV file."""
        try:
            data = read_csv_to_dict(multipliers_csv_path)
            multipliers = {}
            
            for row in data:
                sign = row.get('Planet', '').upper().strip()
                if sign:
                    multipliers[sign] = {}
                    for key, value in row.items():
                        if key != 'Planet':  # Skip first column
                            multipliers[sign][key] = safe_float(value)
            
            return multipliers
        except Exception as e:
            raise ValueError(f"Error loading planet multipliers from {multipliers_csv_path}: {e}")
    
    def _load_animal_translations(self, translations_csv_path: str) -> Dict[str, Dict[str, str]]:
        """Load animal translations from CSV file including new columns."""
        try:
            translations = {}
            data = read_csv_to_dict(translations_csv_path)
            
            for row in data:
                # Handle NaN values and convert to string
                animal_en = safe_str(row.get('AnimalEN', ''))
                animal_fr = safe_str(row.get('AnimalFR', ''))
                determinant_fr = safe_str(row.get('DeterminantAnimalFR', ''))
                article_fr = safe_str(row.get('ArticleAnimalFR', ''))
                
                # Skip if either name is empty
                if animal_en and animal_fr:
                    translations[animal_en] = {
                        'AnimalFR': animal_fr,
                        'DeterminantAnimalFR': determinant_fr,
                        'ArticleAnimalFR': article_fr
                    }
            
            print(f"✅ Loaded {len(translations)} animal translations from {translations_csv_path}")
            return translations
            
        except Exception as e:
            print(f"⚠️  Warning: Could not load animal translations from {translations_csv_path}: {e}")
            return {}
    
    def compute_birth_chart(self, date: str, time: str, lat: float, lon: float) -> Tuple[Dict[str, str], Dict[str, int], Dict[str, Dict[str, float]]]:
        """Compute birth chart and return planet -> sign mapping and planet -> house mapping."""
        try:
            # Parse date and time - flatlib expects YYYY/MM/DD format
            date_formatted = date.replace('-', '/')
            
            # Get UTC offset for the coordinates
            utc_time, timezone_method = convert_local_to_utc(date, time, lat, lon)
            
            # Calculate UTC offset in hours
            from datetime import datetime, timezone as tz
            y, m, d = map(int, date.split("-"))
            hh, mm = map(int, time.split(":"))
            local_naive = datetime(y, m, d, hh, mm)
            
            # Get timezone info
            if not HAS_TIMEZONEFINDER:
                raise ValueError("timezonefinderL is required but not available")
            
            tf = TimezoneFinder()
            timezone_name = tf.timezone_at(lat=lat, lng=lon)
            if not timezone_name:
                raise ValueError(f"Could not determine timezone for coordinates ({lat}, {lon})")
            
            # Special correction for Israel coordinates
            if timezone_name == "Asia/Hebron" and 31.0 <= lat <= 33.5 and 34.0 <= lon <= 35.5:
                timezone_name = "Asia/Jerusalem"
            
            # Attach timezone and get UTC offset
            local_dt = local_naive.replace(tzinfo=ZoneInfo(timezone_name))
            utc_dt = local_dt.astimezone(ZoneInfo("UTC"))
            
            # Calculate UTC offset in hours (negative for west of UTC)
            utc_offset_hours = (local_dt - utc_dt).total_seconds() / 3600
            
            # Check if date changed during UTC conversion
            utc_date = utc_dt.strftime("%Y/%m/%d")
            print(f"Date conversion check:")
            print(f"  Local date: {date_formatted}")
            print(f"  UTC date: {utc_date}")
            print(f"  Date changed: {date_formatted != utc_date}")
            
            # Use the correct UTC date and time
            print(f"Creating flatlib Datetime with UTC time:")
            print(f"  Date: {utc_date}")
            print(f"  UTC Time: {utc_time}")
            print(f"  UTC Offset: 0 (using UTC time directly)")
            dt = Datetime(utc_date, utc_time, 0)
            
            # Check for high latitude and adjust house system if necessary
            if abs(lat) > 66.0:
                print(f"⚠️  High latitude detected ({lat:.2f}°). Checking if Placidus is valid...")
                # For high latitudes, some systems fallback to Porphyry
                house_system = const.HOUSES_PORPHYRIUS
                print(f"Using Porphyry house system for high latitude")
            else:
                house_system = const.HOUSES_PLACIDUS
                print(f"Using Placidus house system")
            
            # Create chart with coordinates and explicit object list
            pos = GeoPos(lat, lon)
            # Use flatlib's built-in chart creation with custom object list (no Swiss Ephemeris dependency)
            # Include outer planets but use flatlib's built-in calculations
            custom_objects = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto', 'North Node']
            chart = Chart(dt, pos, hsys=house_system, IDs=custom_objects)
            
            # Debug: Print exact house cusps from flatlib
            print(f"\n=== DEBUG: Exact House Cusps ===")
            # Use flatlib's built-in house calculation (no Swiss Ephemeris dependency)
            asc = chart.getAngle(const.ASC)
            mc = chart.getAngle(const.MC)
            print(f"ASC: {asc.lon:.3f}°, MC: {mc.lon:.3f}°")
            
            # Extract planet -> sign mapping and planet -> house mapping
            planet_signs = {}
            planet_houses = {}
            
            # Print house system and cusps for debugging
            house_system_name = "Placidus" if house_system == const.HOUSES_PLACIDUS else "Porphyry"
            print(f"\nHouse system: {house_system_name}")
            print(f"Zodiac: Tropical (Western)")
            print(f"Node: Mean Node")
            print(f"Topocentric: OFF")
            print(f"\nHouse cusps ({house_system_name} system):")
            for i, house in enumerate(chart.houses, 1):
                print(f"House {i}: {house.lon:.1f}°")
            
            for planet_name in self.supported_planets:
                try:
                    if planet_name == "Ascendant":
                        obj = chart.get("Asc")
                    elif planet_name == "North Node":
                        obj = chart.get("North Node")
                    elif planet_name == "MC":
                        obj = chart.get("MC")
                    elif planet_name == "Uranus":
                        obj = chart.get(const.URANUS)
                    elif planet_name == "Neptune":
                        obj = chart.get(const.NEPTUNE)
                    elif planet_name == "Pluto":
                        obj = chart.get(const.PLUTO)
                    else:
                        obj = chart.get(planet_name)
                    
                    # Get sign name and convert to uppercase
                    sign = obj.sign.upper()
                    planet_signs[planet_name] = sign
                    
                    # Get house number for this planet using corrected calculation
                    house_num = _get_corrected_house_number(obj.lon, chart.houses)
                    planet_houses[planet_name] = house_num
                    
                    # Debug: Check house calculation with offset
                    if planet_name in ['Sun', 'Moon', 'Mercury', 'Venus']:
                        print(f"\n=== DEBUG: {planet_name} House Calculation ===")
                        print(f"Planet longitude: {obj.lon:.3f}°")
                        
                        # Show flatlib's calculation with offset
                        flatlib_house = chart.houses.getHouseByLon(obj.lon)
                        flatlib_house_num = flatlib_house.num() if flatlib_house else 0
                        
                        for i, house in enumerate(chart.houses, 1):
                            offset_lon = house.lon + house._OFFSET
                            dist = abs(obj.lon - offset_lon)
                            if dist > 180:
                                dist = 360 - dist
                            in_house = dist < house.size
                            print(f"House {i}: cusp={house.lon:.3f}°, offset_cusp={offset_lon:.3f}°, distance={dist:.3f}°, in_house={in_house}")
                        
                        print(f"Flatlib house (with offset): {flatlib_house_num}")
                        print(f"Corrected house (no offset): {house_num}")
                    
                    # Convert longitude to degrees and minutes
                    degrees = int(obj.lon)
                    minutes = (obj.lon - degrees) * 60
                    
                    # Print detailed information for debugging
                    print(f"{planet_name}: {obj.sign} {degrees}°{minutes:02.0f}' (Maison {house_num}) - Longitude: {obj.lon:.3f}°")
                    
                except Exception as e:
                    print(f"Warning: Could not get {planet_name}: {e}")
                    continue
            
            # Create detailed planet positions for French formatting
            planet_positions = {}
            for planet_name in self.supported_planets:
                try:
                    if planet_name in ["Ascendant", "MC"]:
                        # Handle Ascendant and MC specially - get from chart angles
                        if planet_name == "Ascendant":
                            asc = chart.getAngle(const.ASC)
                            total_degrees = asc.lon
                            sign_degrees = total_degrees % 30
                            degrees = int(sign_degrees)
                            minutes = (sign_degrees - degrees) * 60
                            
                            planet_positions[planet_name] = {
                                "sign": asc.sign,
                                "degrees": degrees,
                                "minutes": minutes,
                                "total_longitude": total_degrees
                            }
                        elif planet_name == "MC":
                            mc = chart.getAngle(const.MC)
                            total_degrees = mc.lon
                            sign_degrees = total_degrees % 30
                            degrees = int(sign_degrees)
                            minutes = (sign_degrees - degrees) * 60
                            
                            planet_positions[planet_name] = {
                                "sign": mc.sign,
                                "degrees": degrees,
                                "minutes": minutes,
                                "total_longitude": total_degrees
                            }
                    else:
                        # Handle regular planets
                        obj = chart.getObject(planet_name)
                        if obj:
                            # Calculate degrees and minutes within the sign
                            total_degrees = obj.lon
                            sign_degrees = total_degrees % 30  # Degrees within the sign (0-29)
                            degrees = int(sign_degrees)
                            minutes = (sign_degrees - degrees) * 60
                            
                            planet_positions[planet_name] = {
                                "sign": obj.sign,
                                "degrees": degrees,
                                "minutes": minutes,
                                "total_longitude": total_degrees
                            }
                except Exception as e:
                    print(f"Warning: Could not get position for {planet_name}: {e}")
                    continue
            
            return planet_signs, planet_houses, planet_positions
            
        except Exception as e:
            raise ValueError(f"Error computing birth chart: {e}")
    
    def compute_dynamic_planet_weights(self, planet_signs: Dict[str, str]) -> Dict[str, float]:
        """Compute dynamic planet weights based on zodiac sign positions."""
        dynamic_weights = {}
        
        for planet, sign in planet_signs.items():
            base_weight = self.planet_weights[planet]
            multiplier = self.planet_multipliers[sign][planet]
            dynamic_weight = base_weight * multiplier
            dynamic_weights[planet] = dynamic_weight
            
            print(f"{planet} weight: {base_weight} × {multiplier} = {dynamic_weight:.2f}")
        
        return dynamic_weights
    
    def compute_raw_scores(self, planet_signs: Dict[str, str]) -> Dict[str, Dict[str, int]]:
        """Compute raw animal scores for each planet."""
        # Ensure scores data is loaded
        self._ensure_scores_data_loaded()
        
        raw_scores = {}
        
        for animal_data in self.scores_data["animals"]:
            animal_name = animal_data["ANIMAL"]
            scores = {}
            
            for planet, sign in planet_signs.items():
                if sign in animal_data:
                    scores[planet] = int(animal_data[sign])
                else:
                    print(f"Warning: No score found for {animal_name} - {sign}")
                    scores[planet] = 0
            
            raw_scores[animal_name] = scores
        
        return raw_scores
    
    def compute_weighted_scores(self, raw_scores: Dict[str, Dict[str, int]], dynamic_weights: Dict[str, float]) -> Dict[str, Dict[str, float]]:
        """Apply dynamic planet weights to raw scores."""
        weighted_scores = {}
        
        for animal, scores in raw_scores.items():
            weighted_scores[animal] = {}
            for planet in self.supported_planets:
                if planet in scores:
                    weighted_scores[animal][planet] = scores[planet] * dynamic_weights[planet]
                else:
                    weighted_scores[animal][planet] = 0.0
        
        return weighted_scores
    
    def compute_animal_totals(self, weighted_scores: Dict[str, Dict[str, float]]) -> List[Tuple[str, float]]:
        """Compute total weighted scores for each animal."""
        totals = {}
        
        for animal, scores in weighted_scores.items():
            total = sum(scores.values())
            totals[animal] = total
        
        # Sort by total score (descending)
        sorted_totals = sort_dict_by_value(totals, reverse=True)
        return sorted_totals
    
    def compute_top3_percentage_strength(self, weighted_scores: Dict[str, Dict[str, float]], animal_totals: List[Tuple[str, float]], dynamic_weights: Dict[str, float]) -> Dict[str, Dict[str, float]]:
        """Compute percentage strength of top 3 animals for each planet and overall strength percentage."""
        top3_animals = [animal for animal, _ in get_top_n(animal_totals, 3)]
        
        # Calculate percentage strength
        percentage_strength = {}
        
        # First, find max scores for each planet
        max_scores = {}
        for planet in self.supported_planets:
            max_score = 0.0
            for animal_scores in weighted_scores.values():
                if planet in animal_scores:
                    max_score = max(max_score, animal_scores[planet])
            max_scores[planet] = max_score
        
        # Calculate percentage strength for top 3 animals
        for animal in top3_animals:
            percentage_strength[animal] = {}
            
            for planet in self.supported_planets:
                if planet in weighted_scores.get(animal, {}) and max_scores[planet] > 0:
                    percentage_strength[animal][planet] = (weighted_scores[animal][planet] / max_scores[planet]) * 100
                else:
                    percentage_strength[animal][planet] = 0.0
        
        # Calculate overall strength percentage (weighted average)
        for animal in top3_animals:
            total_weighted_strength = 0.0
            total_weight = 0.0
            
            for planet in self.supported_planets:
                if planet in dynamic_weights and planet in percentage_strength[animal]:
                    planet_weight = dynamic_weights[planet]
                    planet_strength = percentage_strength[animal][planet]
                    
                    total_weighted_strength += planet_strength * planet_weight
                    total_weight += planet_weight
            
            if total_weight > 0:
                overall_strength = total_weighted_strength / total_weight
                percentage_strength[animal]['OVERALL_STRENGTH'] = overall_strength
            else:
                percentage_strength[animal]['OVERALL_STRENGTH'] = 0.0
        
        # Calculate OVERALL_STRENGTH_ADJUST based on ranking
        for i, animal in enumerate(top3_animals):
            overall_strength = percentage_strength[animal]['OVERALL_STRENGTH']
            
            if i == 0:  # Top 1
                strength_adjust = overall_strength + (100 - overall_strength) * 0.4
            elif i == 1:  # Top 2
                strength_adjust = overall_strength + (100 - overall_strength) * 0.15
            else:  # Top 3
                strength_adjust = overall_strength
            
            percentage_strength[animal]['OVERALL_STRENGTH_ADJUST'] = round(strength_adjust, 1)
        
        return percentage_strength
    
    def compute_top3_true_false(self, weighted_scores: Dict[str, Dict[str, float]], animal_totals: List[Tuple[str, float]]) -> Dict[str, Dict[str, bool]]:
        """Compute TRUE/FALSE table for top 3 animals' top 6 planets."""
        top3_animals = [animal for animal, _ in get_top_n(animal_totals, 3)]
        
        true_false_table = {}
        
        for animal in top3_animals:
            # Get this animal's weighted scores for all planets
            animal_scores = weighted_scores.get(animal, {})
            
            # Sort planets by score (descending) and get top 6
            sorted_planets = sort_dict_by_value(animal_scores, reverse=True)
            top6_planets = [planet for planet, _ in sorted_planets[:6]]
            
            # Mark TRUE for top 6, FALSE for others
            true_false_table[animal] = {}
            for planet in self.supported_planets:
                true_false_table[animal][planet] = planet in top6_planets
        
        return true_false_table
    
    def _format_birth_chart_french(self, planet_signs: Dict[str, str], planet_houses: Dict[str, int], planet_positions: Dict[str, Dict[str, float]] = None) -> Dict[str, str]:
        """Format birth chart in French with degrees and minutes."""
        
        # French planet names
        planet_names_fr = {
            "Sun": "Soleil",
            "Moon": "Lune", 
            "Mercury": "Mercure",
            "Venus": "Vénus",
            "Mars": "Mars",
            "Jupiter": "Jupiter",
            "Saturn": "Saturne",
            "Uranus": "Uranus",
            "Neptune": "Neptune",
            "Pluto": "Pluton",
            "North Node": "Nœud Nord",
            "Ascendant": "Ascendant",
            "MC": "MC"
        }
        
        # French sign names
        sign_names_fr = {
            "ARIES": "Bélier",
            "TAURUS": "Taureau", 
            "GEMINI": "Gémeaux",
            "CANCER": "Cancer",
            "LEO": "Lion",
            "VIRGO": "Vierge",
            "LIBRA": "Balance",
            "SCORPIO": "Scorpion",
            "SAGITTARIUS": "Sagittaire",
            "CAPRICORN": "Capricorne",
            "AQUARIUS": "Verseau",
            "PISCES": "Poissons"
        }
        
        try:
            french_chart = {}
            
            for planet, sign in planet_signs.items():
                if planet in planet_names_fr:
                    planet_fr = planet_names_fr[planet]
                    sign_fr = sign_names_fr.get(sign, sign)
                    
                    # Get exact degrees and minutes if available
                    if planet_positions and planet in planet_positions:
                        pos_data = planet_positions[planet]
                        degrees = int(pos_data["degrees"])
                        minutes = int(pos_data["minutes"])
                        
                        # Get house number if available
                        house_number = planet_houses.get(planet, "")
                        if house_number:
                            french_chart[planet_fr] = f"en {degrees}° {minutes}' {sign_fr} en Maison {house_number}"
                        else:
                            french_chart[planet_fr] = f"en {degrees}° {minutes}' {sign_fr}"
                    else:
                        # Fallback to just sign if no position data
                        house_number = planet_houses.get(planet, "")
                        if house_number:
                            french_chart[planet_fr] = f"en {sign_fr} en Maison {house_number}"
                        else:
                            french_chart[planet_fr] = f"en {sign_fr}"
            
            return french_chart
            
        except Exception as e:
            print(f"Error formatting French birth chart: {e}")
            return {}
    
    def generate_chatgpt_interpretation(self, planet_signs: Dict[str, str], 
                                      planet_houses: Dict[str, int],
                                      true_false_table: Dict[str, Dict[str, bool]], 
                                      animal_totals: List[Tuple[str, float]],
                                      api_key: str = None) -> Dict[str, str]:
        """
        Generate ChatGPT interpretation of why the top1 animal matches the subject's personality.
        
        Args:
            planet_signs: Birth chart data with planet signs
            planet_houses: Birth chart data with planet houses
            true_false_table: TRUE/FALSE table for top 3 animals
            animal_totals: Animal totals with rankings
            
        Returns:
            Dictionary containing the interpretation or None if failed
        """
        if not HAS_OPENAI:
            print("⚠️  OpenAI library not available, skipping ChatGPT interpretation")
            return None
        
        try:
            # Get the top1 animal
            top1_animal = animal_totals[0][0]  # First animal from sorted list
            
            # Get the planets marked TRUE for the top1 animal
            top1_true_planets = []
            for planet in self.supported_planets:
                if true_false_table.get(top1_animal, {}).get(planet, False):
                    top1_true_planets.append(planet)
            
            # Translation dictionaries
            planet_translations = {
                "Sun": "Soleil", "Moon": "Lune", "Mercury": "Mercure", "Venus": "Vénus",
                "Mars": "Mars", "Jupiter": "Jupiter", "Saturn": "Saturne", "Uranus": "Uranus",
                "Neptune": "Neptune", "Pluto": "Pluton", "North Node": "Nœud Nord", "MC": "Milieu du Ciel",
                "Ascendant": "Ascendant"
            }
            
            sign_translations = {
                "ARIES": "Bélier", "TAURUS": "Taureau", "GEMINI": "Gémeaux", "CANCER": "Cancer",
                "LEO": "Lion", "VIRGO": "Vierge", "LIBRA": "Balance", "SCORPIO": "Scorpion",
                "SAGITTARIUS": "Sagittaire", "CAPRICORN": "Capricorne", "AQUARIUS": "Verseau", "PISCES": "Poissons"
            }
            
            # Get French animal name from CSV translations
            self._ensure_animal_translations_loaded()
            animal_translation = self.animal_translations.get(top1_animal, {})
            animal_fr = animal_translation.get('AnimalFR', top1_animal)
            animal_determinant = animal_translation.get('DeterminantAnimalFR', animal_fr)
            
            # Build the prompt for ChatGPT
            prompt = f"""Tu es un astrologue expert spécialisé dans l'interprétation des thèmes de naissance et la compatibilité avec les animaux totems.

Basé sur le thème de naissance suivant et les planètes qui ont une forte corrélation avec l'animal totem, explique pourquoi {animal_determinant} correspond à la personnalité de cette personne.

THÈME DE NAISSANCE:
{json.dumps(planet_signs, indent=2, ensure_ascii=False)}

PLANÈTES AVEC FORTE CORRÉLATION POUR {animal_determinant}:
{', '.join(top1_true_planets)}
Pour chaque planète marquée TRUE, voici son signe et sa maison dans le thème de naissance:
"""
            
            # Add planet-sign-house combinations for TRUE planets
            for planet in top1_true_planets:
                sign = planet_signs.get(planet, "Non défini")
                house = planet_houses.get(planet, 0)
                planet_fr = planet_translations.get(planet, planet)
                sign_fr = sign_translations.get(sign, sign)
                prompt += f"- {planet_fr}: {sign_fr} (Maison {house})\n"
            
            prompt += f"""

Écris une interprétation courte (environ 800 caractères au total) en 3 points bullet points expliquant pourquoi {animal_determinant} correspond à la personnalité de cette personne. Chaque point doit établir une corrélation directe entre des éléments spécifiques du thème natal (planètes dans signes et maisons) et l'archétype de l'animal.

                Format de réponse souhaité (3 points obligatoires):
                • [Titre du trait] : [planète(s) en signe(s) et maison(s)] donne/transmet [qualité]. Comme {animal_determinant}, tu [comportement/qualité], grâce à [aspect astrologique spécifique].
                • [Titre du trait] : [planète(s) en signe(s) et maison(s)] traduit [qualité]. {animal_determinant} incarne [trait], [comportement spécifique], [qualité].
                • [Titre du trait] : [planète(s) en signe(s) et maison(s)] apporte [qualité]. Comme {animal_determinant} qui [comportement animal], ta personnalité associe [qualités], [comportements].

                RÈGLES STRICTES:
                - TOUJOURS utiliser "tu" et "ta" pour s'adresser directement à la personne
                - JAMAIS utiliser "l'individu", "la personne", "il/elle" ou "son/sa"
                - Chaque point DOIT commencer par un titre court suivi de " : " (ex: "Curiosité et liberté intellectuelle : ")
                - Chaque point doit mentionner des planètes spécifiques avec leurs signes et maisons
                - Établir des corrélations directes entre les aspects astrologiques et les traits de l'animal
                - Inclure des références concrètes aux comportements de l'animal
                - ÉCRIRE ENTIÈREMENT EN FRANÇAIS : utiliser Soleil, Lune, Mercure, Vénus, Mars, Jupiter, Saturne, Uranus, Neptune, Pluton (pas Sun, Moon, etc.)
                - Utiliser les signes en français : Bélier, Taureau, Gémeaux, Cancer, Lion, Vierge, Balance, Scorpion, Sagittaire, Capricorne, Verseau, Poissons
                - JAMAIS de mots en anglais ou en majuscules
                - Maximum 800 caractères au total"""
            
            # Get OpenAI API key from parameter, environment, or file
            if not api_key:
                api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                # Try to load from api_key.txt file
                try:
                    if os.path.exists('api_key.txt'):
                        with open('api_key.txt', 'r') as f:
                            api_key = f.read().strip()
                        print("✅ OpenAI API key loaded from api_key.txt")
                except Exception as e:
                    print(f"⚠️  Could not load API key from file: {e}")
            if not api_key:
                print("⚠️  OpenAI API key not provided (use --openai_api_key, set OPENAI_API_KEY env var, or create api_key.txt), skipping ChatGPT interpretation")
                return None
            
            # Initialize OpenAI client
            client = openai.OpenAI(api_key=api_key)
            
            # Call ChatGPT
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Tu es un astrologue expert spécialisé dans l'interprétation des thèmes de naissance et la compatibilité avec les animaux totems. Tu t'adresses TOUJOURS directement à la personne en utilisant 'tu' et 'ta', jamais 'l'individu' ou 'la personne'. Tu écris ENTIÈREMENT en français, y compris les noms des planètes (Soleil, Lune, Mercure, Vénus, Mars, Jupiter, Saturne, Uranus, Neptune, Pluton) et des signes astrologiques (Bélier, Taureau, Gémeaux, Cancer, Lion, Vierge, Balance, Scorpion, Sagittaire, Capricorne, Verseau, Poissons). JAMAIS de mots en anglais ou en majuscules."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            interpretation_text = response.choices[0].message.content.strip()
            
            # Convert \n to actual line breaks
            formatted_interpretation = interpretation_text.replace("\\n", "\n")
            
            return {
                "top1_animal": top1_animal,
                "true_planets": top1_true_planets,
                "interpretation": formatted_interpretation,
                "character_count": len(formatted_interpretation)
            }
            
        except Exception as e:
            print(f"Error generating ChatGPT interpretation: {e}")
            return None
    
    def generate_outputs(self, planet_signs: Dict[str, str], planet_houses: Dict[str, int],
                        dynamic_weights: Dict[str, float], raw_scores: Dict[str, Dict[str, int]],
                        weighted_scores: Dict[str, Dict[str, float]], animal_totals: List[Tuple[str, float]],
                        percentage_strength: Dict[str, Dict[str, float]], true_false_table: Dict[str, Dict[str, bool]],
                        utc_time: str = None, timezone_method: str = None, openai_api_key: str = None, 
                        planet_positions: Dict[str, Dict[str, float]] = None,
                        birth_date: str = None, birth_time: str = None, lat: float = None, lon: float = None):
        """Generate all output files in the outputs directory."""
        
        # Ensure outputs directory exists
        os.makedirs("outputs", exist_ok=True)
        
        # Define output file paths
        output_files = {
            "birth_chart": "outputs/birth_chart.json",
            "planet_weights": "outputs/planet_weights.json",
            "raw_scores_csv": "outputs/raw_scores.csv",
            "raw_scores_json": "outputs/raw_scores.json",
            "weighted_scores_csv": "outputs/weighted_scores.csv",
            "weighted_scores_json": "outputs/weighted_scores.json",
            "animal_totals_csv": "outputs/animal_totals.csv",
            "animal_totals_json": "outputs/animal_totals.json",
            "top3_percentage_strength_csv": "outputs/top3_percentage_strength.csv",
            "top3_percentage_strength_json": "outputs/top3_percentage_strength.json",
            "top3_true_false_csv": "outputs/top3_true_false.csv",
            "top3_true_false_json": "outputs/top3_true_false.json",
            "result": "outputs/result.json"
        }
        
        # Remove existing output files if they exist
        for file_path in output_files.values():
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Removed existing file: {file_path}")
        
        # 1. Birth Chart Data (JSON) - includes both signs and houses
        birth_chart_data = {
            "planet_signs": planet_signs,
            "planet_houses": planet_houses
        }

        # Add UTC time and timezone detection method if provided
        if utc_time:
            birth_chart_data["utc_time"] = utc_time
        if timezone_method:
            birth_chart_data["timezone_detection_method"] = timezone_method
        
        # Add French formatted birth chart
        birth_chart_data["french_birth_chart"] = self._format_birth_chart_french(planet_signs, planet_houses, planet_positions)
        with open(output_files["birth_chart"], 'w', encoding='utf-8') as f:
            json.dump(birth_chart_data, f, indent=2, ensure_ascii=False)
        print(f"Birth chart data saved to: {output_files['birth_chart']}")
        
        # 2. Planet Weights (JSON)
        with open(output_files["planet_weights"], 'w', encoding='utf-8') as f:
            json.dump(dynamic_weights, f, indent=2)
        print(f"Planet weights saved to: {output_files['planet_weights']}")
        
        # 3. Raw Scores Table (JSON only - CSV removed for memory optimization)
        with open(output_files["raw_scores_json"], 'w', encoding='utf-8') as f:
            json.dump(raw_scores, f, separators=(',', ':'))
        print(f"Raw scores saved to: {output_files['raw_scores_json']}")
        
        # 4. Weighted Scores Table (JSON only - CSV removed for memory optimization)
        with open(output_files["weighted_scores_json"], 'w', encoding='utf-8') as f:
            json.dump(weighted_scores, f, separators=(',', ':'))
        print(f"Weighted scores saved to: {output_files['weighted_scores_json']}")
        
        # 5. Animal Totals Table (JSON only - CSV removed for memory optimization)
        animal_totals_dict = [{"ANIMAL": animal, "TOTAL_SCORE": score} for animal, score in animal_totals]
        with open(output_files["animal_totals_json"], 'w', encoding='utf-8') as f:
            json.dump(animal_totals_dict, f, separators=(',', ':'))
        print(f"Animal totals saved to: {output_files['animal_totals_json']}")
        
        # 6. Top 3 % Strength Table (JSON only - CSV removed for memory optimization)
        with open(output_files["top3_percentage_strength_json"], 'w', encoding='utf-8') as f:
            json.dump(percentage_strength, f, separators=(',', ':'))
        print(f"Top 3 percentage strength saved to: {output_files['top3_percentage_strength_json']}")
        
        # 7. Top 3 TRUE/FALSE Table (JSON only - CSV removed for memory optimization)
        with open(output_files["top3_true_false_json"], 'w', encoding='utf-8') as f:
            json.dump(true_false_table, f, separators=(',', ':'))
        print(f"Top 3 TRUE/FALSE table saved to: {output_files['top3_true_false_json']}")
        
        # 8. Combined Results JSON
        combined_results = {
            "birth_chart": {
                "planet_signs": planet_signs,
                "planet_houses": planet_houses
            },
            "planet_weights": dynamic_weights,
            "raw_scores": raw_scores,
            "weighted_scores": weighted_scores,
            "animal_totals": [{"ANIMAL": animal, "TOTAL_SCORE": score} for animal, score in animal_totals],
            "top3_percentage_strength": percentage_strength,
            "top3_true_false": true_false_table
        }
        
        with open(output_files["result"], 'w', encoding='utf-8') as f:
            json.dump(combined_results, f, indent=2)
        print(f"Combined results saved to: {output_files['result']}")
        
        # 9. Generate radar chart automatically
        try:
            from plumatotm_radar import generate_radar_charts_from_results
            print("🎨 Generating radar chart...")
            # Check if icons folder exists
            icons_folder = "icons" if os.path.exists("icons") else None
            if icons_folder:
                print(f"🎨 Using custom icons from: {icons_folder}")
            else:
                print("🎨 Using default planet symbols")
            
            radar_result = generate_radar_charts_from_results(output_files["result"], icons_folder)
            if radar_result:
                print(f"📊 Top 1 radar chart saved: {radar_result['top1_animal_chart']}")
                print(f"📊 Top 2 radar chart saved: {radar_result['top2_animal_chart']}")
                print(f"📊 Top 3 radar chart saved: {radar_result['top3_animal_chart']}")
            else:
                print("⚠️  Radar chart generation failed")
        except ImportError:
            print("⚠️  Radar chart module not available")
        except Exception as e:
            print(f"⚠️  Radar chart generation failed: {e}")
        
        # 10. Generate ChatGPT interpretation
        try:
            interpretation = self.generate_chatgpt_interpretation(
                planet_signs, planet_houses, true_false_table, animal_totals, openai_api_key
            )
            if interpretation:
                interpretation_file = "outputs/chatgpt_interpretation.json"
                interpretation_txt_file = "outputs/chatgpt_interpretation.txt"
                
                # Create a copy with properly formatted interpretation
                formatted_interpretation = interpretation.copy()
                formatted_interpretation["interpretation"] = formatted_interpretation["interpretation"].replace("\\n", "\n")
                
                # Save JSON file
                with open(interpretation_file, 'w', encoding='utf-8') as f:
                    json.dump(formatted_interpretation, f, indent=2, ensure_ascii=False)
                
                # Save text file with proper line breaks
                with open(interpretation_txt_file, 'w', encoding='utf-8') as f:
                    f.write(f"Animal totem: {formatted_interpretation['top1_animal']}\n")
                    f.write(f"Planètes corrélées: {', '.join(formatted_interpretation['true_planets'])}\n\n")
                    f.write("Interprétation:\n")
                    f.write(formatted_interpretation["interpretation"])
                
                print(f"🤖 ChatGPT interpretation saved to: {interpretation_file}")
                print(f"📝 Formatted interpretation saved to: {interpretation_txt_file}")
            else:
                print("⚠️  ChatGPT interpretation generation failed")
        except Exception as e:
            print(f"⚠️  ChatGPT interpretation generation failed: {e}")
        
        # 10. Generate animal statistics if available and birth data provided
        if STATISTICS_AVAILABLE and birth_date and birth_time and lat is not None and lon is not None:
            try:
                print("📊 Generating animal statistics...")
                
                # Get top 1 animal
                top1_animal = animal_totals[0][0]  # First tuple, first element (animal name)
                
                # Generate statistics
                stats_generator = AnimalStatisticsGenerator()
                statistics = stats_generator.run_full_analysis(
                    date=birth_date,
                    time=birth_time,
                    lat=lat,
                    lon=lon,
                    top1_animal=top1_animal
                )
                
                print(f"📊 Animal statistics saved to: outputs/animal_proportion.json")
                print(f"   User animal percentage: {statistics['user_animal_percentage']}%")
                print(f"   Total animals tracked: {len(statistics['all_animals_percentages'])}")
                
            except Exception as e:
                print(f"⚠️  Animal statistics generation failed: {e}")
        else:
            if not STATISTICS_AVAILABLE:
                print("⚠️  Animal statistics module not available")
            else:
                print("⚠️  Birth data not provided for statistics")
        
        # Print summary
        print(f"\n=== ANALYSIS SUMMARY ===")
        print(f"Top 3 animals:")
        for i, (animal, score) in enumerate(get_top_n(animal_totals, 3), 1):
            print(f"{i}. {animal}: {score:.1f}")
        
        # Explicit memory cleanup after analysis
        import gc
        gc.collect()
    
    def run_analysis(self, date: str, time: str, lat: float, lon: float, timezone_method: str = None, openai_api_key: str = None, translations_csv_path: str = None):
        """Run the complete analysis pipeline."""
        # Format coordinates with proper signs
        lat_sign = "N" if lat >= 0 else "S"
        lon_sign = "E" if lon >= 0 else "W"
        lat_abs = abs(lat)
        lon_abs = abs(lon)
        
        print(f"Starting analysis for birth data: {date} {time}")
        print(f"Coordinates: {lat_abs:.5f}°{lat_sign}, {lon_abs:.5f}°{lon_sign}")
        print(f"Raw coordinates: ({lat:.5f}, {lon:.5f})")
        
        # Load animal translations if provided and not already loaded
        self._ensure_animal_translations_loaded()
        
        # Convert local time to UTC automatically
        utc_time, timezone_method = convert_local_to_utc(date, time, lat, lon)
        print(f"Converted to UTC: {utc_time}")
        
        # 1. Compute birth chart with LOCAL time (flatlib expects local time, not UTC)
        planet_signs, planet_houses, planet_positions = self.compute_birth_chart(date, time, lat, lon)
        print(f"\nBirth chart computed: {planet_signs}")
        print(f"Planet houses: {planet_houses}")
        
        # 2. Compute dynamic planet weights
        dynamic_weights = self.compute_dynamic_planet_weights(planet_signs)
        print(f"\nDynamic planet weights calculated")
        
        # 3. Compute raw scores
        raw_scores = self.compute_raw_scores(planet_signs)
        
        # Memory cleanup after raw scores computation
        import gc
        gc.collect()
        
        # 4. Apply dynamic weights
        weighted_scores = self.compute_weighted_scores(raw_scores, dynamic_weights)
        
        # 5. Compute animal totals
        animal_totals = self.compute_animal_totals(weighted_scores)
        
        # 6. Compute top 3 percentage strength
        percentage_strength = self.compute_top3_percentage_strength(weighted_scores, animal_totals, dynamic_weights)
        
        # 7. Compute top 3 TRUE/FALSE table
        true_false_table = self.compute_top3_true_false(weighted_scores, animal_totals)
        
        # 8. Generate outputs
        self.generate_outputs(planet_signs, planet_houses, dynamic_weights, raw_scores, 
                            weighted_scores, animal_totals, percentage_strength, true_false_table, 
                            utc_time, timezone_method, openai_api_key, planet_positions,
                            date, time, lat, lon)
        
        # Memory cleanup after all computations
        del raw_scores  # Free memory after all uses
        gc.collect()


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="PLUMATOTM Animal × Planet Scoring System (Final Working Version)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # For Suzanna (September 1, 1991, 22:45 local time, Basse-Terre, Guadeloupe):
  python plumatotm_core.py \\
    --scores_csv "plumatotm_raw_scores_trad.csv" \\
    --weights_csv "plumatotm_planets_weights.csv" \\
    --multipliers_csv "plumatotm_planets_multiplier.csv" \\
    --date 1991-09-01 --time 22:45 \\
    --lat 16.0167 --lon -61.7500

  # For Cindy (April 13, 1995, 11:30 local time, Suresnes, France):
  python plumatotm_core.py \\
    --scores_csv "plumatotm_raw_scores_trad.csv" \\
    --weights_csv "plumatotm_planets_weights.csv" \\
    --multipliers_csv "plumatotm_planets_multiplier.csv" \\
    --date 1995-04-13 --time 11:30 \\
    --lat 48.8667 --lon 2.2333

  # For new person (August 31, 1990, 18:35 local time, France):
  python plumatotm_core.py \\
    --scores_csv "plumatotm_raw_scores_trad.csv" \\
    --weights_csv "plumatotm_planets_weights.csv" \\
    --multipliers_csv "plumatotm_planets_multiplier.csv" \\
    --date 1990-08-31 --time 18:35 \\
    --lat 47.4000 --lon 0.7000

Note: This version automatically converts local time to UTC based on coordinates.
        """
    )
    
    parser.add_argument("--scores_csv", required=True,
                       help="Path to the animal scores CSV file")
    parser.add_argument("--weights_csv", required=True,
                       help="Path to the planet weights CSV file")
    parser.add_argument("--multipliers_csv", required=True,
                       help="Path to the planet weight multipliers CSV file")
    parser.add_argument("--date", required=True,
                       help="Date of birth (YYYY-MM-DD)")
    parser.add_argument("--time", required=True,
                       help="Local time of birth (HH:MM 24h format)")
    parser.add_argument("--lat", required=True, type=float,
                       help="Latitude of birth place")
    parser.add_argument("--lon", required=True, type=float,
                       help="Longitude of birth place")
    parser.add_argument("--openai_api_key", type=str,
                       help="OpenAI API key for ChatGPT interpretation (optional, can also use OPENAI_API_KEY env var)")
    
    args = parser.parse_args()
    
    try:
        # Validate date format
        datetime.strptime(args.date, "%Y-%m-%d")
        
        # Validate time format
        datetime.strptime(args.time, "%H:%M")
        
        # Validate coordinates
        if not -90 <= args.lat <= 90:
            raise ValueError("Latitude must be between -90 and 90")
        if not -180 <= args.lon <= 180:
            raise ValueError("Longitude must be between -180 and 180")
        
        # Convert local time to UTC
        utc_time, timezone_method = convert_local_to_utc(args.date, args.time, args.lat, args.lon)
        
        # Initialize analyzer
        analyzer = BirthChartAnalyzer(args.scores_csv, args.weights_csv, args.multipliers_csv)
        
        # Run analysis with UTC time (includes radar chart generation)
        analyzer.run_analysis(args.date, utc_time, args.lat, args.lon, timezone_method, args.openai_api_key)
        
        print("\nAnalysis completed successfully!")
        print("All output files have been saved to the 'outputs' directory.")
        
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
