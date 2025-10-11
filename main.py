#!/usr/bin/env python3
"""
PLUMATOTM API Web Service
Expose the astrological animal compatibility engine via HTTP API
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import json
import tempfile
from datetime import datetime
import traceback
import csv
import re

# Import the core engine
import plumatotm_core

# Import Supabase manager
try:
    from supabase_manager import SupabaseManager
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("WARNING: Supabase not available. Install with: pip install supabase")

app = Flask(__name__)

# Configure CORS to allow requests from plumastro.com
CORS(app, resources={r"/analyze": {"origins": "https://plumastro.com"}})

# Global analyzer instance
analyzer = None

# Global Supabase manager instance
supabase_manager = None

def initialize_analyzer():
    """Initialize the analyzer with required files"""
    global analyzer
    try:
        print("Testing flatlib import...")
        import flatlib
        print(f"SUCCESS: flatlib imported successfully (version: {getattr(flatlib, '__version__', 'unknown')})")
        
        print("Importing BirthChartAnalyzer...")
        from plumatotm_core import BirthChartAnalyzer
        print("SUCCESS: BirthChartAnalyzer imported successfully")
        
        print("Initializing analyzer...")
        analyzer = BirthChartAnalyzer(
            scores_csv_path="plumatotm_raw_scores_trad.csv",
            weights_csv_path="plumatotm_planets_weights.csv", 
            multipliers_csv_path="plumatotm_planets_multiplier.csv",
            translations_csv_path="plumatotm_raw_scores_trad.csv"
        )
        print("SUCCESS: PLUMATOTM Analyzer initialized successfully")
        return True
    except ImportError as e:
        print(f"ERROR: Import error: {e}")
        print("INFO: This might be a flatlib installation issue on Render")
        return False
    except Exception as e:
        print(f"ERROR: Failed to initialize analyzer: {e}")
        import traceback
        traceback.print_exc()
        return False

def initialize_supabase():
    """Initialize the Supabase manager"""
    global supabase_manager
    if SUPABASE_AVAILABLE:
        try:
            supabase_manager = SupabaseManager()
            if supabase_manager.is_available():
                print("SUCCESS: Supabase manager initialized successfully")
                return True
            else:
                print("WARNING: Supabase manager not available (check configuration)")
                return False
        except Exception as e:
            print(f"ERROR: Failed to initialize Supabase manager: {e}")
            return False
    else:
        print("WARNING: Supabase not available")
        return False

@app.route('/')
def home():
    """API home endpoint"""
    return jsonify({
        "service": "PLUMATOTM Astrological Animal Compatibility Engine",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "POST /analyze": "Run full astrological analysis",
            "POST /order": "Process order with customAttributes and generate prompts",
            "GET /health": "Health check",
            "GET /": "This information"
        }
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "analyzer_ready": analyzer is not None,
        "supabase_ready": supabase_manager is not None and supabase_manager.is_available()
    })

# Dictionnaires pour les descriptions des planètes et explications des maisons
PLANET_DESCRIPTIONS = {
    "AC": "Ta motivation pour vivre",
    "Ascendant": "Ton impulsion de vie",
    "Sun": "Ton identité et là où tu brilles",
    "Moon": "Ton corps et tes émotions",
    "Mercury": "Comment et dans quel domaine tu communiques",
    "Venus": "Comment et dans quel domaine tu crées du lien",
    "Mars": "Comment et dans quel domaine tu passes à l'action",
    "Jupiter": "Comment et dans quel domaine tu crées l'abondance",
    "Saturn": "Comment et dans quel domaine tu poses des limites",
    "Uranus": "Comment et dans quel domaine tu innoves et bouscules",
    "Neptune": "Comment et dans quel domaine tu utilises ton imagination",
    "Pluto": "Comment et dans quel domaine tu détiens un pouvoir secret",
    "MC": "Ton image publique et ta vocation",
    "North Node": "Comment et dans quel domaine tu es insatiable"
}

HOUSE_EXPLANATIONS = {
    1: "Maison 1, celle de l’identité et de la vitalité",
    2: "Maison 2, celle des biens et des talents",
    3: "Maison 3, celle de la communication et de la fratrie",
    4: "Maison 4, celle du foyer et des racines",
    5: "Maison 5, celle de la créativité et du plaisir",
    6: "Maison 6, celle du travail et de la santé",
    7: "Maison 7, celle des partenariats et de l’union",
    8: "Maison 8, celle de la transformation et de l’héritage",
    9: "Maison 9, celle des voyages et de la spiritualité",
    10: "Maison 10, celle de la carrière et de la réputation",
    11: "Maison 11, celle des amis et de la communauté",
    12: "Maison 12, celle de l’inconscient et de l’isolement"
}

# Mapping des noms anglais vers français pour les planètes
PLANET_NAME_MAPPING = {
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

# Mapping des signes anglais vers français
SIGN_NAME_MAPPING = {
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

# Mapping des numéros de maisons vers chiffres arabes (plus utilisé, conservé pour compatibilité)
# Les maisons sont maintenant affichées directement avec des chiffres arabes

def generate_top_aspects(date, time, lat, lon):
    """Generate the TOP 10 ASPECTS for the birth chart."""
    try:
        # Import the aspects generator
        from aspects_patterns_generator import AspectsPatternsGenerator
        
        # Generate aspects and patterns
        generator = AspectsPatternsGenerator()
        aspects_patterns_data = generator.generate_aspects_patterns(date, time, lat, lon)
        
        # Traductions des aspects
        aspect_translations = {
            "Conjunction": "Conjonction",
            "Opposition": "Opposition",
            "Square": "Carré",
            "Trine": "Trigone",
            "Sextile": "Sextile",
            "Quincunx": "Quinconce",
            "Semisextile": "Semi-sextile",
            "Semisquare": "Semi-carré",
            "Quintile": "Quintile",
            "Sesquiquintile": "Sesqui-quintile",
            "Biquintile": "Bi-quintile",
            "Semiquintile": "Semi-quintile"
        }
        
        # Traductions des planètes
        planet_translations = {
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
        
        # Trier les aspects par orbe croissant (plus l'orbe est petit, plus l'aspect est puissant)
        sorted_aspects = sorted(aspects_patterns_data['aspects'], key=lambda x: x['orb'])[:10]
        
        # Créer le dictionnaire des TOP 10 aspects
        top_aspects = {}
        for i in range(1, 11):  # ASPECT1 à ASPECT10
            if i <= len(sorted_aspects):
                aspect = sorted_aspects[i-1]
                planet1_fr = planet_translations.get(aspect['planet1'], aspect['planet1'])
                planet2_fr = planet_translations.get(aspect['planet2'], aspect['planet2'])
                aspect_fr = aspect_translations.get(aspect['aspect'], aspect['aspect'])
                top_aspects[f"ASPECT{i}"] = f"{planet1_fr} {aspect_fr} {planet2_fr} (orb: {aspect['orb']}°)"
            else:
                # Si moins de 10 aspects, laisser vide
                top_aspects[f"ASPECT{i}"] = ""
        
        return top_aspects
        
    except Exception as e:
        print(f"WARNING: Error generating top aspects: {e}")
        import traceback
        traceback.print_exc()
        # Return empty aspects if error
        return {f"ASPECT{i}": "" for i in range(1, 11)}

def parse_custom_attributes(custom_attributes_value):
    """Parse the customAttributes_item.value format"""
    parts = custom_attributes_value.split('¬¬ ')
    if len(parts) != 11:
        raise ValueError(f"Invalid customAttributes format. Expected 11 parts, got {len(parts)}")
    
    return {
        'genre': parts[0].strip(),
        'nom': parts[1].strip(),
        'prenom': parts[2].strip(),
        'lieu_naissance': parts[3].strip(),
        'pays': parts[4].strip(),
        'region': parts[5].strip(),
        'lat': float(parts[6].strip()),
        'lon': float(parts[7].strip()),
        'date_naissance': parts[8].strip(),
        'heure_naissance': parts[9].strip(),
        'validation': parts[10].strip()
    }

def get_sun_ascendant_sign(birth_chart_data):
    """Extract Sun and Ascendant signs from birth chart data"""
    try:
        planet_signs = birth_chart_data.get('planet_signs', {})
        sun_sign = planet_signs.get('Sun', '')
        ascendant_sign = planet_signs.get('Ascendant', '')
        
        # Translate to French - NO ACCENTS (to match CSV format)
        sign_translations = {
            "ARIES": "Belier", "TAURUS": "Taureau", "GEMINI": "Gemeaux",
            "CANCER": "Cancer", "LEO": "Lion", "VIRGO": "Vierge",
            "LIBRA": "Balance", "SCORPIO": "Scorpion", "SAGITTARIUS": "Sagittaire",
            "CAPRICORN": "Capricorne", "AQUARIUS": "Verseau", "PISCES": "Poissons"
        }
        
        sun_fr = sign_translations.get(sun_sign, sun_sign)
        ascendant_fr = sign_translations.get(ascendant_sign, ascendant_sign)
        
        return f"{sun_fr}-{ascendant_fr}"
    except Exception as e:
        print(f"ERROR: Could not extract sun-ascendant signs: {e}")
        return "Unknown-Unknown"

def get_animal_pose_colour(sun_ascendant_sign):
    """Get animal pose and colours from plumatotm_animalposecolour.csv"""
    try:
        csv_path = "plumatotm_animalposecolour.csv"
        if not os.path.exists(csv_path):
            print(f"WARNING: {csv_path} not found")
            return "Pose inconnue", "Ton 1 : inconnu et Ton 2 : inconnu"
        
        # Try different encodings - start with utf-8-sig to handle BOM
        encodings = ['utf-8-sig', 'utf-8', 'latin1', 'cp1252']
        working_encoding = None
        
        for encoding in encodings:
            try:
                with open(csv_path, 'r', encoding=encoding) as f:
                    reader = csv.DictReader(f)
                    # Test if we can read the first row
                    first_row = next(reader, None)
                    if first_row and ('Signe Soleil-Ascendant' in first_row or '\ufeffSigne Soleil-Ascendant' in first_row):
                        working_encoding = encoding
                        print(f"SUCCESS: CSV loaded with encoding {encoding}")
                        break
            except Exception as enc_error:
                continue
        
        if not working_encoding:
            print("ERROR: Could not read CSV with any encoding")
            return "Pose inconnue", "Ton 1 : inconnu et Ton 2 : inconnu"
        
        # Search for the sign combination - handle BOM in CSV
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Handle both with and without BOM
                sign_key = row.get('Signe Soleil-Ascendant', '') or row.get('\ufeffSigne Soleil-Ascendant', '')
                if sign_key.strip() == sun_ascendant_sign.strip():
                    action = row.get('Action/Attitude illustrable', 'Pose inconnue')
                    bicolore = row.get('Bicolore', 'Ton 1 : inconnu et Ton 2 : inconnu')
                    print(f"FOUND: {sun_ascendant_sign} -> {action}")
                    return action, bicolore
        
        print(f"WARNING: No match found for '{sun_ascendant_sign}' in CSV")
        print(f"DEBUG: Available signs (first 5): {list(csv.DictReader(open(csv_path, 'r', encoding='utf-8-sig')))[:5]}")
        return "Pose inconnue", "Ton 1 : inconnu et Ton 2 : inconnu"
        
    except Exception as e:
        print(f"ERROR: Could not read animal pose colour CSV: {e}")
        import traceback
        traceback.print_exc()
        return "Pose inconnue", "Ton 1 : inconnu et Ton 2 : inconnu"

def generate_animal_summary(order_name_nb, animal_totem, genre, sun_ascendant_sign):
    """Generate the Animal Summary string"""
    try:
        # Extract order number (remove the -1, -2, etc.)
        order_number = order_name_nb.split('-')[0]
        
        # Get pose and colours
        action, bicolore = get_animal_pose_colour(sun_ascendant_sign)
        
        # Capitalize animal name properly
        animal_capitalized = animal_totem.title()
        
        # Format: "1048-1 - Léopard des neiges (Femme) ///// Foulee equilibree ///// Ton 1 : rouge et Ton 2 : vert emeraude ou rose"
        return f"{order_number}-1 - {animal_capitalized} ({genre.capitalize()}) ///// {action} ///// {bicolore}"
        
    except Exception as e:
        print(f"ERROR: Could not generate animal summary: {e}")
        return f"{order_name_nb} - {animal_totem} ({genre}) ///// Pose inconnue ///// Couleurs inconnues"

def generate_planetary_positions_summary():
    """Generate the PLANETARY POSITIONS SUMMARY from birth chart data."""
    try:
        # Load birth chart data
        birth_chart_path = "outputs/birth_chart.json"
        if not os.path.exists(birth_chart_path):
            print("WARNING: Birth chart file not found")
            return []
        
        with open(birth_chart_path, 'r', encoding='utf-8') as f:
            birth_chart_data = json.load(f)
        
        planet_signs = birth_chart_data.get('planet_signs', {})
        planet_houses = birth_chart_data.get('planet_houses', {})
        
        # Load detailed positions if available
        planet_positions = {}
        if 'planet_positions' in birth_chart_data:
            planet_positions = birth_chart_data['planet_positions']
        
        planetary_summary = []
        
        # Define the order of planets/points to process
        planet_order = [
            "Sun", "Ascendant", "Moon", "Mercury", "Venus", "Mars", 
            "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", 
            "North Node", "MC"
        ]
        
        for planet_key in planet_order:
            if planet_key not in planet_signs:
                continue
                
            # Get planet name in French
            planet_fr = PLANET_NAME_MAPPING.get(planet_key, planet_key)
            
            # Get description
            description = PLANET_DESCRIPTIONS.get(planet_key, "")
            
            # Get sign in French
            sign_en = planet_signs[planet_key]
            sign_fr = SIGN_NAME_MAPPING.get(sign_en, sign_en)
            
            # Get angle (degrees and minutes) - must match french_birth_chart exactly
            angle = "0°00'"  # Default
            if planet_key in planet_positions:
                pos_data = planet_positions[planet_key]
                degrees = int(pos_data.get("degrees", 0))
                minutes = int(pos_data.get("minutes", 0))
                angle = f"{degrees}°{minutes:02d}'"
            
            # Get house number and explanation
            house_num = planet_houses.get(planet_key, 1)
            house_explanation = HOUSE_EXPLANATIONS.get(house_num, "")
            
            planetary_entry = {
                "PLANETE": planet_fr,
                "DESCRIPTION": description,
                "SIGNE": sign_fr,
                "ANGLE": angle,
                "MAISON": f"Maison {house_num}",
                "MAISON EXPLICATION": house_explanation
            }
            
            planetary_summary.append(planetary_entry)
        
        return planetary_summary
        
    except Exception as e:
        print(f"WARNING: Error generating planetary positions summary: {e}")
        return []

def load_analysis_results():
    """Load and format analysis results for API response."""
    results = {}
    
    try:
        # 1. Load French birth chart (preserve exact order from JSON file)
        birth_chart_path = "outputs/birth_chart.json"
        if os.path.exists(birth_chart_path):
            with open(birth_chart_path, 'r', encoding='utf-8') as f:
                birth_chart_data = json.load(f)
                french_chart = birth_chart_data.get('french_birth_chart', {})
                
                # Define the exact order we want (matching the JSON file order)
                planet_order = [
                    "Soleil", "Ascendant", "Lune", "Mercure", "Vénus", "Mars", 
                    "Jupiter", "Saturne", "Uranus", "Neptune", "Pluton", 
                    "Nœud Nord", "MC"
                ]
                
                # Create ordered dictionary with the exact order
                # Use a regular dict with Python 3.7+ order preservation
                ordered_french_chart = {}
                for planet in planet_order:
                    if planet in french_chart:
                        ordered_french_chart[planet] = french_chart[planet]
                
                results['french_birth_chart'] = ordered_french_chart
        
        # 2. Load animal proportion with French translations
        animal_proportion_path = "outputs/animal_proportion.json"
        if os.path.exists(animal_proportion_path):
            with open(animal_proportion_path, 'r', encoding='utf-8') as f:
                animal_proportion_data = json.load(f)
                
                # Translate animal names in all_animals_percentages
                analyzer._ensure_animal_translations_loaded()
                translated_percentages = {}
                for animal_en, percentage in animal_proportion_data.get('all_animals_percentages', {}).items():
                    animal_translation = analyzer.animal_translations.get(animal_en, {})
                    animal_fr = animal_translation.get('AnimalFR', animal_en)
                    translated_percentages[animal_fr] = percentage
                
                # Get user current animal translations
                user_current_animal_en = animal_proportion_data.get('user_current_animal', '')
                user_animal_translation = analyzer.animal_translations.get(user_current_animal_en, {})
                
                results['animal_proportion'] = {
                    'user_plumid': animal_proportion_data.get('user_plumid', ''),
                    'user_current_animal': user_animal_translation.get('AnimalFR', user_current_animal_en),
                    'user_animal_percentage': animal_proportion_data.get('user_animal_percentage', 0),
                    'all_animals_percentages': translated_percentages
                }
        
        # 3. Load top 3 animals with French translations and strength
        top3_strength_path = "outputs/top3_percentage_strength.json"
        if os.path.exists(top3_strength_path):
            with open(top3_strength_path, 'r', encoding='utf-8') as f:
                top3_data = json.load(f)
                
                # Sort animals by OVERALL_STRENGTH_ADJUST to get top 3
                animals_with_strength = []
                for animal_en, data in top3_data.items():
                    if 'OVERALL_STRENGTH_ADJUST' in data:
                        animals_with_strength.append((animal_en, data['OVERALL_STRENGTH_ADJUST']))
                
                # Sort by strength (descending) and take top 3
                animals_with_strength.sort(key=lambda x: x[1], reverse=True)
                top3_animals = animals_with_strength[:3]
                
                # Create top3_summary
                top3_summary = {}
                analyzer._ensure_animal_translations_loaded()
                for i, (animal_en, strength) in enumerate(top3_animals, 1):
                    animal_translation = analyzer.animal_translations.get(animal_en, {})
                    animal_fr = animal_translation.get('AnimalFR', animal_en)
                    determinant_fr = animal_translation.get('DeterminantAnimalFR', animal_fr)
                    article_fr = animal_translation.get('ArticleAnimalFR', animal_fr)
                    
                    top3_summary[f"Top{i}"] = {
                        "animal": animal_fr,
                        "animal_english": animal_en,
                        "determinant_animal": determinant_fr,
                        "article_animal": article_fr,
                        "overall_strength_adjust": strength
                    }
                
                results['top3_summary'] = top3_summary
        
        # 4. Load ChatGPT interpretation
        interpretation_path = "outputs/chatgpt_interpretation.json"
        if os.path.exists(interpretation_path):
            with open(interpretation_path, 'r', encoding='utf-8') as f:
                interpretation_data = json.load(f)
                results['interpretation'] = interpretation_data.get('interpretation', '')
        
        # 5. Generate PLANETARY POSITIONS SUMMARY
        planetary_summary = generate_planetary_positions_summary()
        if planetary_summary:
            results['PLANETARY POSITIONS SUMMARY'] = planetary_summary
        
    except Exception as e:
        print(f"WARNING: Could not load some analysis results: {e}")
    
    return results

def cleanup_memory():
    """Clean up memory after each API run to minimize memory usage in Render."""
    try:
        import gc
        import sys
        
        # Clear analyzer cache
        global analyzer
        if analyzer is not None:
            # Clear scores data (safe after load_analysis_results)
            if hasattr(analyzer, 'scores_data'):
                analyzer.scores_data = None
            if hasattr(analyzer, 'animals'):
                analyzer.animals = None
            if hasattr(analyzer, '_scores_data_loaded'):
                analyzer._scores_data_loaded = False
            
            # Clear animal translations (safe after load_analysis_results)
            if hasattr(analyzer, 'animal_translations'):
                analyzer.animal_translations.clear()
            if hasattr(analyzer, '_animal_translations_loaded'):
                analyzer._animal_translations_loaded = False
            
            # Clear any other cached data
            if hasattr(analyzer, 'loaded_icons'):
                analyzer.loaded_icons.clear()
        
        # Clear matplotlib cache
        try:
            import matplotlib.pyplot as plt
            plt.close('all')
        except:
            pass
        
        # Force garbage collection
        gc.collect()
        
        print("Memory cleanup completed")
        
    except Exception as e:
        print(f"WARNING: Memory cleanup failed: {e}")

def cleanup_output_files():
    """Remove output files after processing, but keep PNG files for display."""
    import os
    import glob
    
    # Only clean JSON and TXT files, keep PNG files for display
    output_patterns = [
        "outputs/*.json",
        "outputs/*.txt"
        # "outputs/*.png" - KEEP PNG files for display
    ]
    
    files_removed = 0
    for pattern in output_patterns:
        for file_path in glob.glob(pattern):
            try:
                os.remove(file_path)
                files_removed += 1
            except Exception as e:
                print(f"WARNING: Could not remove {file_path}: {e}")
    
    if files_removed > 0:
        print(f"Cleaned {files_removed} output files (PNG files kept for display)")

@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Main analysis endpoint
    Expected JSON payload:
    {
        "name": "Jean",
        "date": "1995-11-17",
        "time": "12:12",
        "lat": 45.7578137,
        "lon": 4.8320114,
        "country": "France",
        "state": "Auvergne-Rhône-Alpes",
        "city": "Lyon",
        "openai_api_key": "sk-..." (optional)
    }
    """
    try:
        # Validate request
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['date', 'time', 'lat', 'lon']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Extract parameters
        name = data.get('name', 'Anonymous')
        date = data['date']
        time = data['time']
        lat = float(data['lat'])
        lon = float(data['lon'])
        country = data.get('country', 'Unknown')
        state = data.get('state', 'Unknown')
        city = data.get('city', 'Unknown')
        openai_api_key = data.get('openai_api_key')
        
        # Validate date format
        try:
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
        
        # Validate time format
        try:
            datetime.strptime(time, '%H:%M')
        except ValueError:
            return jsonify({"error": "Invalid time format. Use HH:MM (24h)"}), 400
        
        # Validate coordinates
        if not (-90 <= lat <= 90):
            return jsonify({"error": "Latitude must be between -90 and 90"}), 400
        if not (-180 <= lon <= 180):
            return jsonify({"error": "Longitude must be between -180 and 180"}), 400
        
        # Check if analyzer is ready
        if analyzer is None:
            return jsonify({"error": "Analyzer not initialized"}), 500
        
        print(f"🔮 Starting analysis for {name} ({date} {time} at {lat}°N, {lon}°W, {city}, {state}, {country})")
        
        try:
            # Run analysis using the analyzer's run_analysis method
            result = analyzer.run_analysis(
                date=date,
                time=time, 
                lat=lat,
                lon=lon,
                openai_api_key=openai_api_key,
                user_name=name
            )
            
            # Load additional results for frontend
            analysis_results = load_analysis_results()
            
            # Generate TOP 10 ASPECTS
            print("🌟 Generating TOP 10 ASPECTS...")
            top_aspects = generate_top_aspects(date, time, lat, lon)
            analysis_results['TOP ASPECTS'] = top_aspects
            print(f"✅ TOP 10 ASPECTS generated successfully")
            
            # Update Supabase with user data
            supabase_updated = False
            if supabase_manager and supabase_manager.is_available():
                try:
                    # Get the top1 animal from the results
                    top3_summary = analysis_results.get('top3_summary', {})
                    top1_data = top3_summary.get('Top1', {})
                    top1_animal = top1_data.get('animal_english', '')
                    
                    if top1_animal:
                        # Generate a unique PlumID for this user using the correct format
                        from plumid_generator import PlumIDGenerator
                        plumid = PlumIDGenerator.generate_plumid(date, time, lat, lon)
                        
                        # Check if user already exists in Supabase
                        existing_animal = supabase_manager.get_user_animal(plumid)
                        
                        if existing_animal:
                            # User exists, update the record
                            supabase_success = supabase_manager.update_user_animal(plumid, top1_animal, name)
                            if supabase_success:
                                supabase_updated = True
                                print(f"SUCCESS: Supabase updated existing user: {name} -> {top1_animal} (PlumID: {plumid})")
                            else:
                                print(f"WARNING: Supabase update failed for existing user {name}")
                        else:
                            # User doesn't exist, add new record
                            supabase_success = supabase_manager.add_user(plumid, top1_animal, name)
                            if supabase_success:
                                supabase_updated = True
                                print(f"SUCCESS: Supabase added new user: {name} -> {top1_animal} (PlumID: {plumid})")
                            else:
                                print(f"WARNING: Supabase add failed for new user {name}")
                    else:
                        print("WARNING: No top1 animal found for Supabase update")
                        
                except Exception as supabase_error:
                    print(f"WARNING: Supabase error: {supabase_error}")
            
        except Exception as e:
            print(f"ERROR: Analysis failed: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                "error": "Analysis failed",
                "details": str(e),
                "timestamp": datetime.now().isoformat()
            }), 500
        
        # Return success response with additional data
        response_data = {
            "status": "success",
            "message": "Analysis completed successfully",
            "timestamp": datetime.now().isoformat(),
            "client_info": {
                "name": name,
                "location": {
                    "country": country,
                    "state": state,
                    "city": city,
                    "coordinates": {
                        "lat": lat,
                        "lon": lon
                    }
                }
            },
            "input": {
                "date": date,
                "time": time,
                "lat": lat,
                "lon": lon
            },
            "output_files": [
                "birth_chart.json",
                "birth_chart.png",
                "animal_totals.json", 
                "top3_percentage_strength.json",
                "animal_proportion.json",
                "chatgpt_interpretation.json",
                "top1_animal_radar.png",
                "top2_animal_radar.png", 
                "top3_animal_radar.png"
            ],
            "supabase_updated": supabase_updated
        }
        
        # Add the additional data requested by the user
        response_data.update(analysis_results)
        
        # Use json.dumps to preserve order (especially for french_birth_chart)
        from flask import Response
        json_response = json.dumps(response_data, ensure_ascii=False, indent=None)
        
        # Explicit memory cleanup after analysis
        cleanup_memory()
        cleanup_output_files()
        
        return Response(json_response, mimetype='application/json')
        
    except Exception as e:
        print(f"ERROR: Analysis error: {e}")
        print(traceback.format_exc())
        
        # Cleanup even on error
        cleanup_memory()
        cleanup_output_files()
        
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/files/<filename>')
def get_file(filename):
    """Serve output files"""
    try:
        # Get absolute path to outputs directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        outputs_dir = os.path.join(current_dir, "outputs")
        file_path = os.path.join(outputs_dir, filename)
        
        # Debug logging
        print(f"Looking for file: {file_path}")
        print(f"Outputs directory exists: {os.path.exists(outputs_dir)}")
        print(f"File exists: {os.path.exists(file_path)}")
        
        if os.path.exists(file_path):
            return send_file(file_path)
        else:
            # List available files for debugging
            if os.path.exists(outputs_dir):
                available_files = os.listdir(outputs_dir)
                print(f"📋 Available files: {available_files}")
                return jsonify({
                    "error": "File not found", 
                    "requested_file": filename,
                    "available_files": available_files
                }), 404
            else:
                return jsonify({
                    "error": "Outputs directory not found",
                    "outputs_dir": outputs_dir
                }), 404
    except Exception as e:
        print(f"ERROR: Error serving file {filename}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/files')
def list_files():
    """List available output files"""
    try:
        # Get absolute path to outputs directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        outputs_dir = os.path.join(current_dir, "outputs")
        
        print(f"Looking for outputs directory: {outputs_dir}")
        print(f"Directory exists: {os.path.exists(outputs_dir)}")
        
        if os.path.exists(outputs_dir):
            files = os.listdir(outputs_dir)
            print(f"Found {len(files)} files: {files}")
            return jsonify({
                "files": files,
                "count": len(files),
                "outputs_dir": outputs_dir
            })
        else:
            print(f"ERROR: Outputs directory not found: {outputs_dir}")
            return jsonify({
                "files": [], 
                "count": 0,
                "error": "Outputs directory not found",
                "outputs_dir": outputs_dir
            })
    except Exception as e:
        print(f"ERROR: Error listing files: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/order', methods=['POST'])
def process_order():
    """
    Order processing endpoint
    Expected JSON payload:
    {
        "order_name_nb": "#1050-1",
        "customAttributes_item_value": "Homme¬¬ LUCIEN¬¬ JEREMIE¬¬ Villecresnes — Île-de-France¬¬ France¬¬ Île-de-France¬¬ 48.7208822¬¬ 2.5327265¬¬ 1988-11-11¬¬ 12:25¬¬ Oui"
    }
    """
    try:
        # Validate request
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['order_name_nb', 'customAttributes_item_value']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Extract parameters
        order_name_nb = data['order_name_nb']
        custom_attributes_value = data['customAttributes_item_value']
        
        print(f"📦 Processing order: {order_name_nb}")
        
        # Parse custom attributes
        try:
            parsed_data = parse_custom_attributes(custom_attributes_value)
            print(f"✅ Parsed data for {parsed_data['prenom']} {parsed_data['nom']}")
        except ValueError as e:
            return jsonify({"error": f"Invalid customAttributes format: {e}"}), 400
        
        # Check if analyzer is ready
        if analyzer is None:
            return jsonify({"error": "Analyzer not initialized"}), 500
        
        # Run astrological analysis (reuse existing logic)
        print("🔮 Running astrological analysis...")
        try:
            result = analyzer.run_analysis(
                date=parsed_data['date_naissance'],
                time=parsed_data['heure_naissance'], 
                lat=parsed_data['lat'],
                lon=parsed_data['lon'],
                user_name=parsed_data['prenom']
            )
            
            # Load analysis results
            analysis_results = load_analysis_results()
            
            # Generate TOP 10 ASPECTS
            top_aspects = generate_top_aspects(
                parsed_data['date_naissance'],
                parsed_data['heure_naissance'],
                parsed_data['lat'],
                parsed_data['lon']
            )
            analysis_results['TOP ASPECTS'] = top_aspects
            
        except Exception as e:
            print(f"ERROR: Analysis failed: {e}")
            return jsonify({
                "error": "Astrological analysis failed",
                "details": str(e)
            }), 500
        
        # Extract data for animal summary
        birth_chart_data = analysis_results.get('birth_chart', {})
        top3_summary = analysis_results.get('top3_summary', {})
        top1_data = top3_summary.get('Top1', {})
        animal_totem = top1_data.get('animal', 'Animal inconnu')
        
        print(f"DEBUG: analysis_results keys: {list(analysis_results.keys())}")
        print(f"DEBUG: birth_chart_data: {birth_chart_data}")
        print(f"DEBUG: top3_summary keys: {list(top3_summary.keys()) if top3_summary else 'None'}")
        print(f"DEBUG: animal_totem: {animal_totem}")
        
        # Try to load birth chart data directly from file if not in analysis_results
        if not birth_chart_data:
            try:
                with open("outputs/birth_chart.json", 'r', encoding='utf-8') as f:
                    birth_chart_data = json.load(f)
                print(f"DEBUG: Loaded birth_chart directly from file: {list(birth_chart_data.keys())}")
            except Exception as e:
                print(f"WARNING: Could not load birth_chart.json: {e}")
                birth_chart_data = {}
        
        # Get Sun-Ascendant sign for pose lookup
        sun_ascendant_sign = get_sun_ascendant_sign(birth_chart_data)
        print(f"DEBUG: sun_ascendant_sign: {sun_ascendant_sign}")
        print(f"DEBUG: birth_chart_data planet_signs: {birth_chart_data.get('planet_signs', {}) if birth_chart_data else 'None'}")
        
        # Generate Animal Summary
        animal_summary = generate_animal_summary(
            order_name_nb, animal_totem, parsed_data['genre'], sun_ascendant_sign
        )
        
        # Generate prompts
        prenom_capitalized = parsed_data['prenom'].capitalize()
        nom_capitalized = parsed_data['nom'].capitalize()
        
        # Prompt1reCouv
        prompt1re_couv = f"""Texte que Victor utilise pour la 1re couv
{animal_summary}"""
        
        # Generate aspects and patterns for Prompt4emeCouv
        from aspects_patterns_generator import AspectsPatternsGenerator
        generator = AspectsPatternsGenerator()
        aspects_patterns_data = generator.generate_aspects_patterns(
            parsed_data['date_naissance'],
            parsed_data['heure_naissance'],
            parsed_data['lat'],
            parsed_data['lon']
        )
        
        # Format aspects and patterns text
        aspects_text = ""
        if aspects_patterns_data['aspects']:
            aspects_text = "\nAspects:\n"
            for aspect in aspects_patterns_data['aspects'][:10]:  # Top 10 only
                aspects_text += f"{aspect['planet1']} {aspect['aspect']} {aspect['planet2']} (orb: {aspect['orb']}°)\n"
        
        patterns_text = ""
        if aspects_patterns_data['patterns']:
            patterns_text = "\nConfigurations:\n"
            for pattern in aspects_patterns_data['patterns']:
                patterns_text += f"{pattern['type']}\n"
        
        # Get the determinant animal (just the French name, not the full summary)
        animal_determinant = top1_data.get('determinant_animal', animal_totem)
        
        # Generate french_chart_text (reuse from generate_book.py)
        french_chart_text = ""
        try:
            if birth_chart_data:
                french_birth_chart = birth_chart_data.get('french_birth_chart', {})
                
                # Format the French birth chart exactly like in generate_book.py
                french_chart_text = "{\n"
                for planet, position in french_birth_chart.items():
                    french_chart_text += f'    "{planet}": "{position}",\n'
                french_chart_text = french_chart_text.rstrip(",\n") + "\n}"
                
                print(f"DEBUG: Generated french_chart_text ({len(french_chart_text)} chars)")
        except Exception as e:
            print(f"WARNING: Could not generate french_chart_text: {e}")
            french_chart_text = "French chart data not available"
        
        # Prompt4emeCouv
        prompt4eme_couv = f"""This illustration attached is the cover you made of a Plumastro book about my client's astrological personality. Animal symbolising astrologically the client on the illustration : {animal_determinant} ({parsed_data['genre']}) here is the client birth chart data : {french_chart_text}
 Explique en Francais en approximativement 500 (entre 440 et 560) caracteres pourquoi tu as fait cette illustration avec cette animal, cette position, ces couleurs pour decrire le client ? Tu es un expert astrologue, et explique le de maniere poetique. Tout le texte doit etre en français, pas d'anglais. N'utilise pas de tiret pour ponctuer tes phrases. Parles des positions des planètes marquantes qui ont une forte influence sur la personnalite. Voici une reference de description que tu as faite pour un autre client : "Abeille de velours, elle traverse les ronces avec une grâce instinctive. Sa force est calme, enracinée, mais toujours en mouvement — elle sait où cueillir, où guérir. Chaque battement d'aile parle d'un monde intérieur dense, patient, infiniment loyal. Elle avance sans bruit, portée par une sagesse ancienne, tissant entre les roses un chemin secret. Autour d'elle, tout respire l'équilibre et la douceur farouche d'un être qui ne cède rien, sauf à l'amour." et une autre reference pour un autre client : "Lama d'améthyste, il avance avec une paix fière, porteur d'un feu intérieur maîtrisé. Il cherche du sens, des sommets, une vérité à incarner. Sa nature profonde l'enracine : il aime la lenteur, la sensualité, la constance des choses simples. Il observe le monde avec patience, ajuste chaque geste, affine chaque pensée. Derrière sa douceur calme, brûle une quête sincère : celle d'un être digne, lucide, attentif à ce qui compte, guidé par un éclat que rien ne peut éteindre." Garde ce ton poetique, pour decrire l'image d'un point de vue astrologique"""
        
        # Generate prompt_chatgpt by running generate_book.py and reading the output file
        prompt_chatgpt = ""
        try:
            # First, run generate_book.py to create the prompt file
            from generate_book import generate_book
            
            # Prepare input data in the format expected by generate_book.py
            input_data = {
                'genre': parsed_data['genre'],
                'nom': parsed_data['nom'],
                'prenom': parsed_data['prenom'],
                'lieu_naissance': parsed_data['lieu_naissance'],
                'pays': parsed_data['pays'],
                'region': parsed_data['region'],
                'lat': parsed_data['lat'],
                'lon': parsed_data['lon'],
                'date_naissance': parsed_data['date_naissance'],
                'heure_naissance': parsed_data['heure_naissance']
            }
            
            # Run generate_book.py
            print("Running generate_book.py to create prompt_chatgpt.txt...")
            success = generate_book(input_data)
            
            if success:
                # Read the generated prompt file
                prompt_file = "livre/prompt_chatgpt.txt"
                if os.path.exists(prompt_file):
                    with open(prompt_file, 'r', encoding='utf-8') as f:
                        prompt_chatgpt = f.read()
                    print(f"SUCCESS: Read prompt_chatgpt.txt ({len(prompt_chatgpt)} chars)")
                else:
                    print(f"WARNING: prompt_chatgpt.txt not found after generate_book.py")
                    prompt_chatgpt = "Prompt file not generated"
            else:
                print("WARNING: generate_book.py failed")
                prompt_chatgpt = "Generate book failed"
                
        except Exception as e:
            print(f"WARNING: Could not generate chatgpt prompt: {e}")
            import traceback
            traceback.print_exc()
            prompt_chatgpt = "ChatGPT prompt generation failed"
        
        # Upload files to Google Drive
        drive_upload_result = None
        try:
            print("\n📤 Uploading files to Google Drive...")
            from google_drive_uploader import upload_order_to_drive
            
            # Define file paths (from livre/ folder after generate_book.py runs)
            birth_chart_path = "livre/birth_chart.png"
            radar1_path = "livre/top1_animal_radar.png"
            radar2_path = "livre/top2_animal_radar.png"
            radar3_path = "livre/top3_animal_radar.png"
            
            # Upload to Google Drive
            drive_upload_result = upload_order_to_drive(
                order_name_nb,
                birth_chart_path,
                radar1_path,
                radar2_path,
                radar3_path
            )
            
            if drive_upload_result:
                print(f"✅ Google Drive upload successful!")
                print(f"📁 Folder URL: https://drive.google.com/drive/folders/{drive_upload_result['order_folder_id']}")
            else:
                print("⚠️ Google Drive upload failed (continuing anyway)")
                
        except Exception as e:
            print(f"⚠️ Google Drive upload error (non-critical): {e}")
            import traceback
            traceback.print_exc()
        
        # Prepare response
        response_data = {
            "status": "success",
            "message": "Order processed successfully",
            "timestamp": datetime.now().isoformat(),
            "order_info": {
                "order_name_nb": order_name_nb,
                "prenom": prenom_capitalized,
                "nom": nom_capitalized,
                "animal_summary": animal_summary
            },
            "prompts": {
                "Prompt1reCouv": prompt1re_couv,
                "Prompt4emeCouv": prompt4eme_couv,
                "prompt_chatgpt": prompt_chatgpt
            },
            "google_drive": {
                "uploaded": drive_upload_result is not None,
                "folder_url": f"https://drive.google.com/drive/folders/{drive_upload_result['order_folder_id']}" if drive_upload_result else None,
                "files_uploaded": drive_upload_result['uploaded_files'] if drive_upload_result else {}
            }
        }
        
        # Cleanup memory
        cleanup_memory()
        cleanup_output_files()
        
        from flask import Response
        return Response(json.dumps(response_data, ensure_ascii=False, indent=2), mimetype='application/json')
        
    except Exception as e:
        print(f"ERROR: Order processing error: {e}")
        print(traceback.format_exc())
        
        # Cleanup even on error
        cleanup_memory()
        cleanup_output_files()
        
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

# Initialize analyzer and Supabase at module level (after function definition)
print("Starting PLUMATOTM API...")
if initialize_analyzer():
    print("SUCCESS: Analyzer ready")
else:
    print("ERROR: Failed to start API - analyzer initialization failed")
    exit(1)

# Initialize Supabase (optional - API will work without it)
initialize_supabase()

if __name__ == '__main__':
    # Analyzer is already initialized at module level
    # Get port from environment (Render sets PORT)
    port = int(os.environ.get('PORT', 5000))
    
    # Check if running in production (Render sets RENDER=true)
    if os.environ.get('RENDER'):
        print("🌐 Running in production mode - use Gunicorn via Procfile")
        # In production, Gunicorn will handle the server
        # This block is only for local development
        app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
    else:
        print("🔧 Running in development mode")
        app.run(host='0.0.0.0', port=port, debug=True, threaded=True)
