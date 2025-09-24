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

# Import the core engine
import plumatotm_core

app = Flask(__name__)

# Configure CORS to allow requests from plumastro.com
CORS(app, resources={r"/analyze": {"origins": "https://plumastro.com"}})

# Global analyzer instance
analyzer = None

def initialize_analyzer():
    """Initialize the analyzer with required files"""
    global analyzer
    try:
        print("🔍 Testing flatlib import...")
        import flatlib
        print(f"✅ flatlib imported successfully (version: {getattr(flatlib, '__version__', 'unknown')})")
        
        print("🔍 Importing BirthChartAnalyzer...")
        from plumatotm_core import BirthChartAnalyzer
        print("✅ BirthChartAnalyzer imported successfully")
        
        print("🔍 Initializing analyzer...")
        analyzer = BirthChartAnalyzer(
            scores_csv_path="plumatotm_raw_scores_trad.csv",
            weights_csv_path="plumatotm_planets_weights.csv", 
            multipliers_csv_path="plumatotm_planets_multiplier.csv",
            translations_csv_path="plumatotm_raw_scores_trad.csv"
        )
        print("✅ PLUMATOTM Analyzer initialized successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 This might be a flatlib installation issue on Render")
        return False
    except Exception as e:
        print(f"❌ Failed to initialize analyzer: {e}")
        import traceback
        traceback.print_exc()
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
        "analyzer_ready": analyzer is not None
    })

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
        
    except Exception as e:
        print(f"⚠️  Warning: Could not load some analysis results: {e}")
    
    return results

def cleanup_memory():
    """Clean up memory after each API run to minimize memory usage in Render."""
    try:
        import gc
        import sys
        
        # Force garbage collection
        gc.collect()
        
        # Clear any cached data in the analyzer if it exists
        global analyzer
        if analyzer is not None:
            # Clear any cached data that might be stored in the analyzer
            if hasattr(analyzer, 'loaded_icons'):
                analyzer.loaded_icons.clear()
            if hasattr(analyzer, 'animal_translations'):
                # Don't clear translations as they're needed for next run
                pass
        
        # Clear any matplotlib cache
        try:
            import matplotlib.pyplot as plt
            plt.close('all')
        except:
            pass
        
        # Force another garbage collection
        gc.collect()
        
        print("🧹 Memory cleanup completed")
        
    except Exception as e:
        print(f"⚠️  Warning: Memory cleanup failed: {e}")

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
            
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
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
            ]
        }
        
        # Add the additional data requested by the user
        response_data.update(analysis_results)
        
        # Use json.dumps to preserve order (especially for french_birth_chart)
        from flask import Response
        json_response = json.dumps(response_data, ensure_ascii=False, indent=None)
        
        # Explicit memory cleanup after analysis
        cleanup_memory()
        
        return Response(json_response, mimetype='application/json')
        
    except Exception as e:
        print(f"❌ Analysis error: {e}")
        print(traceback.format_exc())
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/files/<filename>')
def get_file(filename):
    """Serve output files"""
    try:
        file_path = os.path.join("outputs", filename)
        if os.path.exists(file_path):
            return send_file(file_path)
        else:
            return jsonify({"error": "File not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/files')
def list_files():
    """List available output files"""
    try:
        outputs_dir = "outputs"
        if os.path.exists(outputs_dir):
            files = os.listdir(outputs_dir)
            return jsonify({
                "files": files,
                "count": len(files)
            })
        else:
            return jsonify({"files": [], "count": 0})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Initialize analyzer at module level (after function definition)
print("🚀 Starting PLUMATOTM API...")
if initialize_analyzer():
    print("✅ API ready to serve requests")
else:
    print("❌ Failed to start API - analyzer initialization failed")
    exit(1)

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
