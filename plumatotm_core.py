#!/usr/bin/env python3
"""
PLUMATOTM Animal × Planet Scoring System (Final Working Version)

This program computes animal scores based on birth chart data using astrological
planets and their zodiac signs, applying predefined weights and scoring tables.

This version uses flatlib for accurate astrological calculations.
"""

import argparse
import json
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Any
import sys
import os
from zoneinfo import ZoneInfo

# OpenAI API for ChatGPT interpretation
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    print("Warning: openai library not available, ChatGPT interpretation will be skipped")

# Try to import timezonefinder, fall back to manual detection if not available
try:
    from timezonefinder import TimezoneFinder
    HAS_TIMEZONEFINDER = True
except ImportError:
    HAS_TIMEZONEFINDER = False
    print("Warning: timezonefinder not available, using manual timezone detection")

# Import flatlib for astrological calculations
try:
    from flatlib import const
    from flatlib.chart import Chart
    from flatlib.datetime import Datetime
    from flatlib.geopos import GeoPos
    from flatlib.object import Object
except ImportError:
    print("Error: flatlib is required. Install with: pip install flatlib")
    sys.exit(1)

# Zodiac signs for validation
ZODIAC_SIGNS = [
    "ARIES", "TAURUS", "GEMINI", "CANCER", "LEO", "VIRGO",
    "LIBRA", "SCORPIO", "SAGITTARIUS", "CAPRICORN", "AQUARIUS", "PISCES"
]


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

def convert_local_to_utc(date: str, local_time: str, lat: float, lon: float) -> str:
    """
    Convert local time to UTC based on coordinates.
    
    Args:
        date: Date in YYYY-MM-DD format
        local_time: Local time in HH:MM format
        lat: Latitude
        lon: Longitude
    
    Returns:
        UTC time in HH:MM format
    """
    try:
        timezone_name = None
        
        if HAS_TIMEZONEFINDER:
            # Use timezonefinder for accurate timezone detection
            tf = TimezoneFinder()
            timezone_name = tf.timezone_at(lat=lat, lng=lon)
        
        if not timezone_name:
            # Fall back to manual timezone detection
            if -1 <= lon <= 1 and 35 <= lat <= 37:  # Algeria (including Algiers) - more precise
                timezone_name = "Africa/Algiers"
            elif -10 <= lon <= 40 and 35 <= lat <= 70:  # Europe
                if 3 <= lon <= 15:  # Central Europe
                    timezone_name = "Europe/Paris"
                elif lon < 3:  # Western Europe
                    timezone_name = "Europe/London"
                else:  # Eastern Europe
                    timezone_name = "Europe/Berlin"
            elif -80 <= lon <= -60 and 25 <= lat <= 50:  # Eastern North America
                timezone_name = "America/New_York"
            elif -125 <= lon <= -115 and 30 <= lat <= 45:  # California
                timezone_name = "America/Los_Angeles"
            elif -120 <= lon <= -80 and 25 <= lat <= 50:  # Western North America
                timezone_name = "America/Los_Angeles"
            elif 70 <= lon <= 90 and 20 <= lat <= 40:  # India
                timezone_name = "Asia/Kolkata"
            elif 135 <= lon <= 145 and 35 <= lat <= 45:  # Japan
                timezone_name = "Asia/Tokyo"
            elif 110 <= lon <= 130 and 20 <= lat <= 40:  # China
                timezone_name = "Asia/Shanghai"
            elif -65 <= lon <= -60 and 15 <= lat <= 17:  # Guadeloupe
                timezone_name = "America/Guadeloupe"
            elif -75 <= lon <= -70 and 10 <= lat <= 20:  # Caribbean
                timezone_name = "America/Guadeloupe"
            else:
                raise ValueError(f"Could not determine timezone for coordinates ({lat}, {lon})")
        
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
        
        print(f"Timezone detected: {timezone_name}")
        print(f"Local time: {local_time} → Timezone: {timezone_name} → {dst_status} → UTC time: {utc_time}")
        print(f"DST offset: {dst_offset:.1f} hours")
        
        return utc_time
        
    except Exception as e:
        raise ValueError(f"Error converting local time to UTC: {e}")


class BirthChartAnalyzer:
    """Main class for analyzing birth charts and computing animal scores."""
    
    def __init__(self, scores_json_path: str, weights_csv_path: str, multipliers_csv_path: str):
        """Initialize with the animal scores JSON file and planet weights/multipliers."""
        self.scores_data = self._load_scores_json(scores_json_path)
        self.animals = [animal["ANIMAL"] for animal in self.scores_data["animals"]]
        self.planet_weights = self._load_planet_weights(weights_csv_path)
        self.planet_multipliers = self._load_planet_multipliers(multipliers_csv_path)
        self.supported_planets = list(self.planet_weights.keys())
        
    def _load_scores_json(self, scores_json_path: str) -> Dict:
        """Load and validate the animal scores JSON file."""
        try:
            with open(scores_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate structure
            if "animals" not in data:
                raise ValueError("JSON must contain 'animals' key")
            
            # Validate each animal entry
            for animal in data["animals"]:
                if "ANIMAL" not in animal:
                    raise ValueError("Each animal must have 'ANIMAL' key")
                
                # Check for all zodiac signs
                missing_signs = [sign for sign in ZODIAC_SIGNS if sign not in animal]
                if missing_signs:
                    raise ValueError(f"Animal {animal['ANIMAL']} missing scores for: {missing_signs}")
                
                # Validate score ranges
                for sign in ZODIAC_SIGNS:
                    score = animal[sign]
                    if not isinstance(score, (int, float)) or score < 0 or score > 100:
                        raise ValueError(f"Invalid score for {animal['ANIMAL']} - {sign}: {score}")
            
            return data
            
        except FileNotFoundError:
            raise FileNotFoundError(f"Scores JSON file not found: {scores_json_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
    
    def _load_planet_weights(self, weights_csv_path: str) -> Dict[str, float]:
        """Load planet weights from CSV file."""
        try:
            df = pd.read_csv(weights_csv_path)
            weights = {}
            for planet in df.columns[1:]:  # Skip first column (Planet)
                weights[planet] = float(df[df['Planet'] == 'PlanetWeight'][planet].iloc[0])
            return weights
        except Exception as e:
            raise ValueError(f"Error loading planet weights from {weights_csv_path}: {e}")
    
    def _load_planet_multipliers(self, multipliers_csv_path: str) -> Dict[str, Dict[str, float]]:
        """Load planet multipliers from CSV file."""
        try:
            df = pd.read_csv(multipliers_csv_path)
            multipliers = {}
            for _, row in df.iterrows():
                sign = row['Planet'].upper()
                multipliers[sign] = {}
                for planet in df.columns[1:]:  # Skip first column (Planet)
                    multipliers[sign][planet] = float(row[planet])
            return multipliers
        except Exception as e:
            raise ValueError(f"Error loading planet multipliers from {multipliers_csv_path}: {e}")
    
    def compute_birth_chart(self, date: str, time: str, lat: float, lon: float) -> Tuple[Dict[str, str], Dict[str, int]]:
        """Compute birth chart and return planet -> sign mapping and planet -> house mapping."""
        try:
            # Parse date and time - flatlib expects YYYY/MM/DD format
            date_formatted = date.replace('-', '/')
            dt = Datetime(date_formatted, time)
            
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
            chart = Chart(dt, pos, hsys=house_system, IDs=const.LIST_OBJECTS)
            
            # Debug: Print exact house cusps from Swiss Ephemeris
            print(f"\n=== DEBUG: Exact House Cusps ===")
            from flatlib.ephem import swe
            hlist, ascmc = swe.sweHousesLon(dt.jd, lat, lon, house_system)
            for i, cusp in enumerate(hlist):
                # Convert to degrees and minutes
                degrees = int(cusp)
                minutes = (cusp - degrees) * 60
                sign_num = int(cusp / 30)
                sign_names = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", 
                             "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
                sign_name = sign_names[sign_num]
                sign_degrees = degrees % 30
                print(f"House {i+1}: {cusp:.3f}° ({sign_degrees}°{minutes:02.0f}' {sign_name})")
            print(f"ASC: {ascmc[0]:.3f}°, MC: {ascmc[1]:.3f}°")
            
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
            
            return planet_signs, planet_houses
            
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
    
    def compute_raw_scores(self, planet_signs: Dict[str, str]) -> pd.DataFrame:
        """Compute raw animal scores for each planet."""
        raw_scores = []
        
        for animal_data in self.scores_data["animals"]:
            animal_name = animal_data["ANIMAL"]
            scores = {}
            
            for planet, sign in planet_signs.items():
                if sign in animal_data:
                    scores[planet] = animal_data[sign]
                else:
                    print(f"Warning: No score found for {animal_name} - {sign}")
                    scores[planet] = 0
            
            scores["ANIMAL"] = animal_name
            raw_scores.append(scores)
        
        df = pd.DataFrame(raw_scores)
        df.set_index("ANIMAL", inplace=True)
        return df
    
    def compute_weighted_scores(self, raw_scores: pd.DataFrame, dynamic_weights: Dict[str, float]) -> pd.DataFrame:
        """Apply dynamic planet weights to raw scores."""
        weighted_scores = raw_scores.copy()
        
        for planet in self.supported_planets:
            if planet in weighted_scores.columns:
                weighted_scores[planet] = weighted_scores[planet] * dynamic_weights[planet]
        
        return weighted_scores
    
    def compute_animal_totals(self, weighted_scores: pd.DataFrame) -> pd.DataFrame:
        """Compute total weighted scores for each animal."""
        totals = weighted_scores.sum(axis=1)
        totals_df = pd.DataFrame({
            'ANIMAL': totals.index,
            'TOTAL_SCORE': totals.values
        })
        totals_df = totals_df.sort_values('TOTAL_SCORE', ascending=False)
        return totals_df
    
    def compute_top3_percentage_strength(self, weighted_scores: pd.DataFrame, animal_totals: pd.DataFrame) -> pd.DataFrame:
        """Compute percentage strength of top 3 animals for each planet."""
        top3_animals = animal_totals.head(3)['ANIMAL'].tolist()
        
        # Get top 3 animals' weighted scores
        top3_scores = weighted_scores.loc[top3_animals]
        
        # Calculate percentage strength
        percentage_strength = pd.DataFrame(index=top3_animals, columns=self.supported_planets)
        
        for planet in self.supported_planets:
            if planet in weighted_scores.columns:
                max_score = weighted_scores[planet].max()
                if max_score > 0:
                    percentage_strength[planet] = (top3_scores[planet] / max_score) * 100
                else:
                    percentage_strength[planet] = 0
        
        return percentage_strength
    
    def compute_top3_true_false(self, weighted_scores: pd.DataFrame, animal_totals: pd.DataFrame) -> pd.DataFrame:
        """Compute TRUE/FALSE table for top 3 animals' top 6 planets."""
        top3_animals = animal_totals.head(3)['ANIMAL'].tolist()
        
        true_false_table = pd.DataFrame(index=top3_animals, columns=self.supported_planets)
        
        for animal in top3_animals:
            # Get this animal's weighted scores for all planets
            animal_scores = weighted_scores.loc[animal]
            
            # Sort planets by score (descending) and get top 6
            sorted_planets = animal_scores.sort_values(ascending=False).head(6).index.tolist()
            
            # Mark TRUE for top 6, FALSE for others
            for planet in self.supported_planets:
                true_false_table.loc[animal, planet] = planet in sorted_planets
        
        return true_false_table
    
    def generate_chatgpt_interpretation(self, planet_signs: Dict[str, str], 
                                      planet_houses: Dict[str, int],
                                      true_false_table: pd.DataFrame, 
                                      animal_totals: pd.DataFrame) -> Dict[str, str]:
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
            top1_animal = animal_totals.iloc[0]['ANIMAL']
            
            # Get the planets marked TRUE for the top1 animal
            top1_true_planets = []
            for planet in self.supported_planets:
                if true_false_table.loc[top1_animal, planet]:
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
            
            animal_translations = {
                "Deer": "Cerf", "Kangaroo": "Kangourou", "Swallow": "Hirondelle", "Whale": "Baleine",
                "Lynx": "Lynx", "Wolf": "Loup", "Eagle": "Aigle", "Bear": "Ours", "Fox": "Renard",
                "Owl": "Hibou", "Dolphin": "Dauphin", "Tiger": "Tigre", "Lion": "Lion", "Horse": "Cheval",
                "Butterfly": "Papillon", "Snake": "Serpent", "Rabbit": "Lapin", "Cat": "Chat", "Dog": "Chien",
                "Elephant": "Éléphant", "Giraffe": "Girafe", "Penguin": "Manchot", "Peacock": "Paon",
                "Swan": "Cygne", "Falcon": "Faucon", "Hawk": "Épervier", "Raven": "Corbeau", "Crow": "Corneille",
                "Sparrow": "Moineau", "Robin": "Rouge-gorge", "Cardinal": "Cardinal", "Hummingbird": "Colibri",
                "Parrot": "Perroquet", "Toucan": "Toucan", "Flamingo": "Flamant", "Pelican": "Pélican",
                "Seagull": "Mouette", "Albatross": "Albatros", "Ostrich": "Autruche", "Emu": "Émeu",
                "Kiwi": "Kiwi", "Panda": "Panda", "Koala": "Koala", "Sloth": "Paresseux", "Anteater": "Fourmilier",
                "Armadillo": "Tatou", "Platypus": "Ornithorynque", "Beaver": "Castor", "Squirrel": "Écureuil",
                "Chipmunk": "Tamia", "Hedgehog": "Hérisson", "Porcupine": "Porc-épic", "Skunk": "Mouffette",
                "Raccoon": "Ratons-laveurs", "Opossum": "Opossum", "Badger": "Blaireau", "Wolverine": "Carcajou",
                "Mink": "Vison", "Ferret": "Furet", "Weasel": "Belette", "Stoat": "Hermine", "Marten": "Martre",
                "Otter": "Loutre", "Seal": "Phoque", "Walrus": "Morse", "Polar Bear": "Ours polaire",
                "Grizzly Bear": "Grizzli", "Black Bear": "Ours noir", "Brown Bear": "Ours brun",
                "Panda Bear": "Panda", "Sun Bear": "Ours malais", "Spectacled Bear": "Ours à lunettes",
                "Asiatic Black Bear": "Ours noir d'Asie", "Sloth Bear": "Ours paresseux", "Giant Panda": "Panda géant",
                "Red Panda": "Panda roux", "Raccoon Dog": "Chien viverrin", "Civet": "Civette", "Genet": "Genette",
                "Mongoose": "Mangouste", "Meerkat": "Suricate", "Fossa": "Fossa", "Binturong": "Binturong",
                "Kinkajou": "Kinkajou", "Olingo": "Olingo", "Cacomistle": "Cacomistle", "Ringtail": "Chat à queue annelée",
                "Coatimundi": "Coati", "Nasua": "Nasua", "Potos": "Potos", "Olinguito": "Olinguito",
                "Bassariscus": "Bassariscus", "Bassaricyon": "Bassaricyon", "Nasuella": "Nasuella",
                "Potos flavus": "Potos flavus", "Bassariscus astutus": "Bassariscus astutus",
                "Bassaricyon gabbii": "Bassaricyon gabbii", "Nasuella olivacea": "Nasuella olivacea",
                "Potos flavus": "Potos flavus", "Bassariscus astutus": "Bassariscus astutus",
                "Bassaricyon gabbii": "Bassaricyon gabbii", "Nasuella olivacea": "Nasuella olivacea"
            }
            
            # Get French animal name
            animal_fr = animal_translations.get(top1_animal, top1_animal)
            
            # Build the prompt for ChatGPT
            prompt = f"""Tu es un astrologue expert spécialisé dans l'interprétation des thèmes de naissance et la compatibilité avec les animaux totems.

Basé sur le thème de naissance suivant et les planètes qui ont une forte corrélation avec l'animal totem, explique pourquoi l'animal "{animal_fr}" correspond à la personnalité de cette personne.

THÈME DE NAISSANCE:
{json.dumps(planet_signs, indent=2, ensure_ascii=False)}

PLANÈTES AVEC FORTE CORRÉLATION POUR L'ANIMAL "{animal_fr}":
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

Écris une interprétation courte (environ 800 caractères au total) en 3 points bullet points expliquant pourquoi l'animal "{animal_fr}" correspond à la personnalité de cette personne. Chaque point doit établir une corrélation directe entre des éléments spécifiques du thème natal (planètes dans signes et maisons) et l'archétype de l'animal.

                Format de réponse souhaité (3 points obligatoires):
                • [Titre du trait] : [planète(s) en signe(s) et maison(s)] donne/transmet [qualité]. Comme le {animal_fr}, tu [comportement/qualité], grâce à [aspect astrologique spécifique].
                • [Titre du trait] : [planète(s) en signe(s) et maison(s)] traduit [qualité]. Le {animal_fr} incarne [trait], [comportement spécifique], [qualité].
                • [Titre du trait] : [planète(s) en signe(s) et maison(s)] apporte [qualité]. Comme le {animal_fr} qui [comportement animal], ta personnalité associe [qualités], [comportements].

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
            
            # Get OpenAI API key from environment
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                print("⚠️  OPENAI_API_KEY environment variable not set, skipping ChatGPT interpretation")
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
                        dynamic_weights: Dict[str, float], raw_scores: pd.DataFrame, 
                        weighted_scores: pd.DataFrame, animal_totals: pd.DataFrame, 
                        percentage_strength: pd.DataFrame, true_false_table: pd.DataFrame):
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
        with open(output_files["birth_chart"], 'w', encoding='utf-8') as f:
            json.dump(birth_chart_data, f, indent=2)
        print(f"Birth chart data saved to: {output_files['birth_chart']}")
        
        # 2. Planet Weights (JSON)
        with open(output_files["planet_weights"], 'w', encoding='utf-8') as f:
            json.dump(dynamic_weights, f, indent=2)
        print(f"Planet weights saved to: {output_files['planet_weights']}")
        
        # 3. Raw Scores Table (CSV & JSON)
        raw_scores.to_csv(output_files["raw_scores_csv"])
        raw_scores.to_json(output_files["raw_scores_json"], orient='index', indent=2)
        print(f"Raw scores saved to: {output_files['raw_scores_csv']} and {output_files['raw_scores_json']}")
        
        # 4. Weighted Scores Table (CSV & JSON)
        weighted_scores.to_csv(output_files["weighted_scores_csv"])
        weighted_scores.to_json(output_files["weighted_scores_json"], orient='index', indent=2)
        print(f"Weighted scores saved to: {output_files['weighted_scores_csv']} and {output_files['weighted_scores_json']}")
        
        # 5. Animal Totals Table (CSV & JSON)
        animal_totals.to_csv(output_files["animal_totals_csv"], index=False)
        animal_totals.to_json(output_files["animal_totals_json"], orient='records', indent=2)
        print(f"Animal totals saved to: {output_files['animal_totals_csv']} and {output_files['animal_totals_json']}")
        
        # 6. Top 3 % Strength Table (CSV & JSON)
        percentage_strength.to_csv(output_files["top3_percentage_strength_csv"])
        percentage_strength.to_json(output_files["top3_percentage_strength_json"], orient='index', indent=2)
        print(f"Top 3 percentage strength saved to: {output_files['top3_percentage_strength_csv']} and {output_files['top3_percentage_strength_json']}")
        
        # 7. Top 3 TRUE/FALSE Table (CSV & JSON)
        true_false_table.to_csv(output_files["top3_true_false_csv"])
        true_false_table.to_json(output_files["top3_true_false_json"], orient='index', indent=2)
        print(f"Top 3 TRUE/FALSE table saved to: {output_files['top3_true_false_csv']} and {output_files['top3_true_false_json']}")
        
        # 8. Combined Results JSON
        combined_results = {
            "birth_chart": {
                "planet_signs": planet_signs,
                "planet_houses": planet_houses
            },
            "planet_weights": dynamic_weights,
            "raw_scores": raw_scores.to_dict('index'),
            "weighted_scores": weighted_scores.to_dict('index'),
            "animal_totals": animal_totals.to_dict('records'),
            "top3_percentage_strength": percentage_strength.to_dict('index'),
            "top3_true_false": true_false_table.to_dict('index')
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
                print(f"📊 Radar chart saved: {radar_result['top_animal_chart']}")
            else:
                print("⚠️  Radar chart generation failed")
        except ImportError:
            print("⚠️  Radar chart module not available")
        except Exception as e:
            print(f"⚠️  Radar chart generation failed: {e}")
        
        # 10. Generate ChatGPT interpretation
        try:
            interpretation = self.generate_chatgpt_interpretation(
                planet_signs, planet_houses, true_false_table, animal_totals
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
        
        # Print summary
        print(f"\n=== ANALYSIS SUMMARY ===")
        print(f"Top 3 animals:")
        for i, (_, row) in enumerate(animal_totals.head(3).iterrows(), 1):
            print(f"{i}. {row['ANIMAL']}: {row['TOTAL_SCORE']:.1f}")
    
    def run_analysis(self, date: str, time: str, lat: float, lon: float):
        """Run the complete analysis pipeline."""
        # Format coordinates with proper signs
        lat_sign = "N" if lat >= 0 else "S"
        lon_sign = "E" if lon >= 0 else "W"
        lat_abs = abs(lat)
        lon_abs = abs(lon)
        
        print(f"Starting analysis for birth data: {date} {time}")
        print(f"Coordinates: {lat_abs:.5f}°{lat_sign}, {lon_abs:.5f}°{lon_sign}")
        print(f"Raw coordinates: ({lat:.5f}, {lon:.5f})")
        
        # 1. Compute birth chart
        planet_signs, planet_houses = self.compute_birth_chart(date, time, lat, lon)
        print(f"\nBirth chart computed: {planet_signs}")
        print(f"Planet houses: {planet_houses}")
        
        # 2. Compute dynamic planet weights
        dynamic_weights = self.compute_dynamic_planet_weights(planet_signs)
        print(f"\nDynamic planet weights calculated")
        
        # 3. Compute raw scores
        raw_scores = self.compute_raw_scores(planet_signs)
        
        # 4. Apply dynamic weights
        weighted_scores = self.compute_weighted_scores(raw_scores, dynamic_weights)
        
        # 5. Compute animal totals
        animal_totals = self.compute_animal_totals(weighted_scores)
        
        # 6. Compute top 3 percentage strength
        percentage_strength = self.compute_top3_percentage_strength(weighted_scores, animal_totals)
        
        # 7. Compute top 3 TRUE/FALSE table
        true_false_table = self.compute_top3_true_false(weighted_scores, animal_totals)
        
        # 8. Generate outputs
        self.generate_outputs(planet_signs, planet_houses, dynamic_weights, raw_scores, 
                            weighted_scores, animal_totals, percentage_strength, true_false_table)


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="PLUMATOTM Animal × Planet Scoring System (Final Working Version)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # For Suzanna (September 1, 1991, 22:45 local time, Basse-Terre, Guadeloupe):
  python plumatotm_core.py \\
    --scores_json "plumatotm_raw_scores.json" \\
    --weights_csv "plumatotm_planets_weights.csv" \\
    --multipliers_csv "plumatotm_planets_multiplier.csv" \\
    --date 1991-09-01 --time 22:45 \\
    --lat 16.0167 --lon -61.7500

  # For Cindy (April 13, 1995, 11:30 local time, Suresnes, France):
  python plumatotm_core.py \\
    --scores_json "plumatotm_raw_scores.json" \\
    --weights_csv "plumatotm_planets_weights.csv" \\
    --multipliers_csv "plumatotm_planets_multiplier.csv" \\
    --date 1995-04-13 --time 11:30 \\
    --lat 48.8667 --lon 2.2333

  # For new person (August 31, 1990, 18:35 local time, France):
  python plumatotm_core.py \\
    --scores_json "plumatotm_raw_scores.json" \\
    --weights_csv "plumatotm_planets_weights.csv" \\
    --multipliers_csv "plumatotm_planets_multiplier.csv" \\
    --date 1990-08-31 --time 18:35 \\
    --lat 47.4000 --lon 0.7000

Note: This version automatically converts local time to UTC based on coordinates.
        """
    )
    
    parser.add_argument("--scores_json", required=True,
                       help="Path to the animal scores JSON file")
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
        utc_time = convert_local_to_utc(args.date, args.time, args.lat, args.lon)
        
        # Initialize analyzer
        analyzer = BirthChartAnalyzer(args.scores_json, args.weights_csv, args.multipliers_csv)
        
        # Run analysis with UTC time (includes radar chart generation)
        analyzer.run_analysis(args.date, utc_time, args.lat, args.lon)
        
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
