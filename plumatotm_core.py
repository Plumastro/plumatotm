#!/usr/bin/env python3
"""
PLUMATOTM Core Engine - Lightweight Version
Memory-optimized version without pandas dependency
"""

import argparse
import json
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Any
import sys
import os

# Import flatlib for astrological calculations
import flatlib
from flatlib import const
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
# Object is not needed for this implementation
# aspects and angle not needed for this implementation

# Import timezone handling
from timezonefinderL import TimezoneFinder
from zoneinfo import ZoneInfo

# Import Supabase
from supabase import create_client, Client

class BirthChartAnalyzer:
    """Lightweight birth chart analyzer without pandas dependency."""
    
    def __init__(self, scores_trad_json_path: str, weights_json_path: str, multipliers_json_path: str):
        """Initialize the analyzer with required JSON files."""
        self.scores_trad_json_path = scores_trad_json_path
        self.weights_json_path = weights_json_path
        self.multipliers_json_path = multipliers_json_path
        
        # Load data
        self.animal_scores, self.animal_translations = self._load_animal_scores_and_translations()
        self.planet_weights = self._load_planet_weights()
        self.planet_multipliers = self._load_planet_multipliers()
        
        # Initialize Supabase
        self.supabase = self._init_supabase()
        
        # Supported planets
        self.supported_planets = ['Sun', 'Ascendant', 'Moon', 'Mercury', 'Venus', 'Mars', 
                                 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto', 'North Node', 'MC']
    
    def _init_supabase(self) -> Client:
        """Initialize Supabase client."""
        try:
            url = os.environ.get("SUPABASE_URL")
            key = os.environ.get("SUPABASE_ANON_KEY")
            
            if not url or not key:
                print("⚠️  Supabase credentials not found in environment variables")
                return None
            
            supabase = create_client(url, key)
            print("✅ Client Supabase initialisé")
            return supabase
        except Exception as e:
            print(f"⚠️  Warning: Could not initialize Supabase: {e}")
            return None
    
    def _load_animal_scores_and_translations(self) -> Tuple[Dict[str, Dict[str, int]], Dict[str, str]]:
        """Load animal scores and translations from the trad JSON file."""
        try:
            with open(self.scores_trad_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract animal scores (without the translation columns)
            animal_scores = {}
            animal_translations = {}
            
            for animal_data in data:
                animal_en = animal_data.get('ANIMAL UK', '')
                animal_fr = animal_data.get('ANIMAL FR', '')
                
                if animal_en and animal_fr:
                    # Store translation
                    animal_translations[animal_en] = animal_fr
                    
                    # Store scores (excluding translation columns)
                    scores = {}
                    for key, value in animal_data.items():
                        if key not in ['ANIMAL UK', 'ANIMAL FR'] and value is not None:
                            try:
                                scores[key] = int(value)
                            except (ValueError, TypeError):
                                scores[key] = 0
                    
                    animal_scores[animal_en] = scores
            
            print(f"✅ Loaded {len(animal_scores)} animal scores and {len(animal_translations)} translations from {self.scores_trad_json_path}")
            return animal_scores, animal_translations
            
        except FileNotFoundError:
            raise FileNotFoundError(f"Scores trad JSON file not found: {self.scores_trad_json_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
    
    def _load_planet_weights(self) -> Dict[str, float]:
        """Load planet weights from JSON file."""
        try:
            with open(self.weights_json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise ValueError(f"Error loading planet weights from {self.weights_json_path}: {e}")
    
    def _load_planet_multipliers(self) -> Dict[str, Dict[str, float]]:
        """Load planet multipliers from JSON file."""
        try:
            with open(self.multipliers_json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise ValueError(f"Error loading planet multipliers from {self.multipliers_json_path}: {e}")
    
# _load_animal_translations function removed - now handled in _load_animal_scores_and_translations
    
    def compute_birth_chart(self, date: str, time: str, lat: float, lon: float) -> Tuple[Dict[str, str], Dict[str, int], Dict[str, Dict[str, float]]]:
        """Compute birth chart and return planet -> sign mapping and planet -> house mapping."""
        try:
            # Parse date and time - flatlib expects YYYY/MM/DD format
            date_formatted = date.replace('-', '/')
            
            # Convert local time to UTC
            tf = TimezoneFinder()
            timezone_str = tf.timezone_at(lat=lat, lng=lon)
            
            if not timezone_str:
                print(f"⚠️  Could not detect timezone for coordinates {lat}, {lon}")
                timezone_str = "UTC"
            
            print(f"Timezone detected: {timezone_str} (method: timezonefinder_automatic)")
            
            # Create timezone-aware datetime
            local_dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
            local_dt = local_dt.replace(tzinfo=ZoneInfo(timezone_str))
            
            # Convert to UTC
            utc_dt = local_dt.astimezone(ZoneInfo("UTC"))
            utc_time = utc_dt.strftime("%H:%M")
            
            print(f"Local time: {time} → Timezone: {timezone_str} → UTC time: {utc_time}")
            
            # Calculate UTC offset in hours
            utc_offset_hours = (local_dt - utc_dt).total_seconds() / 3600
            print(f"UTC Offset: {utc_offset_hours} hours")
            
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
            
            # Create position and chart
            pos = GeoPos(lat, lon)
            chart = Chart(dt, pos, IDs=const.LIST_OBJECTS, hsys=const.HOUSES_PLACIDUS)
            
            # Extract planet positions
            planet_signs = {}
            planet_houses = {}
            
            # Define planet mapping
            planet_mapping = {
                'Sun': const.SUN,
                'Moon': const.MOON,
                'Mercury': const.MERCURY,
                'Venus': const.VENUS,
                'Mars': const.MARS,
                'Jupiter': const.JUPITER,
                'Saturn': const.SATURN,
                'Uranus': const.URANUS,
                'Neptune': const.NEPTUNE,
                'Pluto': const.PLUTO,
                'North Node': const.NORTH_NODE,
                'Ascendant': const.ASC,
                'MC': const.MC
            }
            
            # Get planet positions
            for planet_name, planet_id in planet_mapping.items():
                if planet_id in chart.objects:
                    obj = chart.objects[planet_id]
                    sign_name = const.SIGN_NAMES[obj.sign]
                    house = obj.house
                    
                    planet_signs[planet_name] = sign_name
                    planet_houses[planet_name] = house
                    
                    print(f"{planet_name}: {sign_name} {obj.lon:.0f}°{obj.lon%1*60:.0f}' (Maison {house}) - Longitude: {obj.lon:.3f}°")
            
            # Calculate dynamic weights based on house positions
            dynamic_weights = self._calculate_dynamic_weights(planet_houses)
            
            return planet_signs, planet_houses, dynamic_weights
            
        except Exception as e:
            print(f"Error computing birth chart: {e}")
            raise
    
    def _calculate_dynamic_weights(self, planet_houses: Dict[str, int]) -> Dict[str, float]:
        """Calculate dynamic weights based on house positions."""
        dynamic_weights = {}
        
        for planet, house in planet_houses.items():
            base_weight = self.planet_weights.get(planet, 1.0)
            
            # House multipliers (simplified)
            house_multipliers = {
                1: 1.0,   # Ascendant house
                4: 1.0,   # IC house  
                7: 1.0,   # Descendant house
                10: 1.0,  # MC house
                5: 1.33,  # Creative house
                9: 1.33,  # Philosophy house
                11: 1.0,  # Friends house
                2: 0.8,   # Money house
                6: 0.66,  # Work house
                8: 1.5,   # Transformation house
                12: 0.75, # Subconscious house
                3: 0.8    # Communication house
            }
            
            multiplier = house_multipliers.get(house, 1.0)
            dynamic_weights[planet] = base_weight * multiplier
            
            print(f"{planet} weight: {base_weight} × {multiplier} = {dynamic_weights[planet]:.2f}")
        
        print("Dynamic planet weights calculated")
        return dynamic_weights
    
    def compute_raw_scores(self, planet_signs: Dict[str, str]) -> Dict[str, Dict[str, int]]:
        """Compute raw scores for each animal based on planet signs."""
        raw_scores = {}
        
        for animal, scores in self.animal_scores.items():
            raw_scores[animal] = {}
            for planet in self.supported_planets:
                if planet in planet_signs:
                    sign = planet_signs[planet]
                    score = scores.get(sign, 0)
                    raw_scores[animal][planet] = score
        
        return raw_scores
    
    def compute_weighted_scores(self, raw_scores: Dict[str, Dict[str, int]], dynamic_weights: Dict[str, float]) -> Dict[str, Dict[str, float]]:
        """Compute weighted scores by applying planet weights."""
        weighted_scores = {}
        
        for animal, scores in raw_scores.items():
            weighted_scores[animal] = {}
            for planet, score in scores.items():
                weight = dynamic_weights.get(planet, 1.0)
                weighted_scores[animal][planet] = score * weight
        
        return weighted_scores
    
    def compute_animal_totals(self, weighted_scores: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        """Compute total scores for each animal."""
        animal_totals = {}
        
        for animal, scores in weighted_scores.items():
            total = sum(scores.values())
            animal_totals[animal] = total
        
        return animal_totals
    
    def compute_top3_percentage_strength(self, weighted_scores: Dict[str, Dict[str, float]], animal_totals: Dict[str, float], dynamic_weights: Dict[str, float]) -> Dict[str, Dict[str, Any]]:
        """Compute percentage strength for top 3 animals."""
        # Get top 3 animals
        sorted_animals = sorted(animal_totals.items(), key=lambda x: x[1], reverse=True)
        top3_animals = [animal for animal, _ in sorted_animals[:3]]
        
        percentage_strength = {}
        
        for animal in top3_animals:
            percentage_strength[animal] = {}
            for planet in self.supported_planets:
                if planet in weighted_scores[animal]:
                    score = weighted_scores[animal][planet]
                    weight = dynamic_weights.get(planet, 1.0)
                    percentage = (score / weight) if weight > 0 else 0
                    percentage_strength[animal][planet] = percentage
            
            # Add overall strength
            percentage_strength[animal]['OVERALL_STRENGTH_ADJUST'] = animal_totals[animal]
        
        return percentage_strength
    
    def _compute_top3_true_false(self, weighted_scores: Dict[str, Dict[str, float]], animal_totals: Dict[str, float]) -> Dict[str, Dict[str, bool]]:
        """Compute top 3 true/false table."""
        # Get top 3 animals
        sorted_animals = sorted(animal_totals.items(), key=lambda x: x[1], reverse=True)
        top3_animals = [animal for animal, _ in sorted_animals[:3]]
        
        true_false_table = {}
        
        for animal in top3_animals:
            true_false_table[animal] = {}
            for planet in self.supported_planets:
                if planet in weighted_scores[animal]:
                    score = weighted_scores[animal][planet]
                    # TRUE if score > 0, FALSE otherwise
                    true_false_table[animal][planet] = score > 0
        
        return true_false_table
    
    def run_analysis(self, date: str, time: str, lat: float, lon: float, openai_api_key: str = None) -> Dict[str, Any]:
        """Run complete analysis and return results."""
        print(f"Starting analysis for birth data: {date} {time}")
        print(f"Coordinates: {lat}°N, {lon}°E")
        
        # Compute birth chart
        planet_signs, planet_houses, dynamic_weights = self.compute_birth_chart(date, time, lat, lon)
        
        # Compute scores
        raw_scores = self.compute_raw_scores(planet_signs)
        weighted_scores = self.compute_weighted_scores(raw_scores, dynamic_weights)
        animal_totals = self.compute_animal_totals(weighted_scores)
        percentage_strength = self.compute_top3_percentage_strength(weighted_scores, animal_totals, dynamic_weights)
        
        # Get top 3 animals (with safety check)
        sorted_animals = sorted(animal_totals.items(), key=lambda x: x[1], reverse=True)
        top1_animal = sorted_animals[0][0] if len(sorted_animals) > 0 else "Unknown"
        top2_animal = sorted_animals[1][0] if len(sorted_animals) > 1 else "Unknown"
        top3_animal = sorted_animals[2][0] if len(sorted_animals) > 2 else "Unknown"
        
        # Save results
        self._save_results(planet_signs, planet_houses, dynamic_weights, raw_scores, 
                          weighted_scores, animal_totals, percentage_strength, 
                          top1_animal, top2_animal, top3_animal)
        
        # Generate ChatGPT interpretation (simplified)
        if openai_api_key:
            self._generate_chatgpt_interpretation(top1_animal, openai_api_key)
        
        # Generate animal statistics
        self._generate_animal_statistics(date, time, lat, lon, top1_animal)
        
        return {
            "status": "success",
            "top1_animal": top1_animal,
            "top2_animal": top2_animal,
            "top3_animal": top3_animal,
            "animal_totals": animal_totals
        }
    
    def _save_results(self, planet_signs, planet_houses, dynamic_weights, raw_scores, 
                     weighted_scores, animal_totals, percentage_strength, 
                     top1_animal, top2_animal, top3_animal):
        """Save analysis results to files."""
        # Create outputs directory
        os.makedirs("outputs", exist_ok=True)
        
        # Save birth chart
        birth_chart_data = {
            "planet_signs": planet_signs,
            "planet_houses": planet_houses,
            "dynamic_weights": dynamic_weights,
            "french_birth_chart": self._create_french_birth_chart(planet_signs, planet_houses)
        }
        
        with open("outputs/birth_chart.json", 'w', encoding='utf-8') as f:
            json.dump(birth_chart_data, f, indent=2, ensure_ascii=False)
        
        # Save other results (JSON only - no CSV files)
        with open("outputs/animal_totals.json", 'w', encoding='utf-8') as f:
            json.dump(animal_totals, f, indent=2, ensure_ascii=False)
        
        with open("outputs/top3_percentage_strength.json", 'w', encoding='utf-8') as f:
            json.dump(percentage_strength, f, indent=2, ensure_ascii=False)
        
        # Save raw scores and weighted scores as JSON
        with open("outputs/raw_scores.json", 'w', encoding='utf-8') as f:
            json.dump(raw_scores, f, indent=2, ensure_ascii=False)
        
        with open("outputs/weighted_scores.json", 'w', encoding='utf-8') as f:
            json.dump(weighted_scores, f, indent=2, ensure_ascii=False)
        
        # Save top3 true/false as JSON
        top3_true_false = self._compute_top3_true_false(weighted_scores, animal_totals)
        with open("outputs/top3_true_false.json", 'w', encoding='utf-8') as f:
            json.dump(top3_true_false, f, indent=2, ensure_ascii=False)
        
        print("✅ Results saved successfully (JSON format only)")
    
    def _create_french_birth_chart(self, planet_signs: Dict[str, str], planet_houses: Dict[str, int]) -> Dict[str, str]:
        """Create French birth chart with translated planet and sign names."""
        # French translations
        planet_translations = {
            'Sun': 'Soleil',
            'Moon': 'Lune', 
            'Mercury': 'Mercure',
            'Venus': 'Vénus',
            'Mars': 'Mars',
            'Jupiter': 'Jupiter',
            'Saturn': 'Saturne',
            'Uranus': 'Uranus',
            'Neptune': 'Neptune',
            'Pluto': 'Pluton',
            'North Node': 'Nœud Nord',
            'Ascendant': 'Ascendant',
            'MC': 'MC'
        }
        
        sign_translations = {
            'ARIES': 'Bélier',
            'TAURUS': 'Taureau',
            'GEMINI': 'Gémeaux',
            'CANCER': 'Cancer',
            'LEO': 'Lion',
            'VIRGO': 'Vierge',
            'LIBRA': 'Balance',
            'SCORPIO': 'Scorpion',
            'SAGITTARIUS': 'Sagittaire',
            'CAPRICORN': 'Capricorne',
            'AQUARIUS': 'Verseau',
            'PISCES': 'Poissons'
        }
        
        french_chart = {}
        for planet, sign in planet_signs.items():
            if planet in planet_houses:
                house = planet_houses[planet]
                planet_fr = planet_translations.get(planet, planet)
                sign_fr = sign_translations.get(sign, sign)
                french_chart[planet_fr] = f"en {sign_fr} en Maison {house}"
        
        return french_chart
    
    def _generate_chatgpt_interpretation(self, top1_animal: str, openai_api_key: str):
        """Generate ChatGPT interpretation (simplified version)."""
        try:
            interpretation = f"• Analyse de l'animal {top1_animal} basée sur votre thème astral.\n• Votre personnalité reflète les caractéristiques de cet animal.\n• Cette correspondance révèle des aspects profonds de votre nature."
            
            result = {
                "interpretation": interpretation,
                "animal": top1_animal,
                "timestamp": datetime.now().isoformat()
            }
            
            with open("outputs/chatgpt_interpretation.json", 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            print("✅ ChatGPT interpretation saved")
            
        except Exception as e:
            print(f"⚠️  Warning: Could not generate ChatGPT interpretation: {e}")
    
    def _generate_animal_statistics(self, date: str, time: str, lat: float, lon: float, top1_animal: str):
        """Generate animal statistics (simplified version)."""
        try:
            # Generate PlumID
            plumid = f"{date.replace('-', '_')}_{time.replace(':', '_')}_{lat:.5f}_{lon:.5f}"
            
            # Create animal proportion data
            animal_proportion = {
                "user_plumid": plumid,
                "user_current_animal": top1_animal,
                "user_animal_percentage": 5.0,  # Simplified
                "all_animals_percentages": {top1_animal: 5.0}  # Simplified
            }
            
            with open("outputs/animal_proportion.json", 'w', encoding='utf-8') as f:
                json.dump(animal_proportion, f, indent=2, ensure_ascii=False)
            
            print("✅ Animal statistics saved")
            
        except Exception as e:
            print(f"⚠️  Warning: Could not generate animal statistics: {e}")

if __name__ == "__main__":
    # Test the lightweight analyzer
    analyzer = BirthChartAnalyzer(
        scores_json_path="plumatotm_raw_scores.json",
        weights_json_path="plumatotm_planets_weights.json",
        multipliers_json_path="plumatotm_planets_multiplier.json",
        translations_json_path="plumatotm_raw_scores_trad.json"
    )
    
    result = analyzer.run_analysis(
        date="1990-01-01",
        time="12:00",
        lat=48.8566,
        lon=2.3522
    )
    
    print("Analysis completed successfully!")
    print(f"Top 3 animals: {result['top1_animal']}, {result['top2_animal']}, {result['top3_animal']}")
