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
            scores_json_path="plumatotm_raw_scores.json",
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
        # 1. Load French birth chart
        birth_chart_path = "outputs/birth_chart.json"
        if os.path.exists(birth_chart_path):
            with open(birth_chart_path, 'r', encoding='utf-8') as f:
                birth_chart_data = json.load(f)
                results['french_birth_chart'] = birth_chart_data.get('french_birth_chart', {})
        
        # 2. Load animal proportion with French translations
        animal_proportion_path = "outputs/animal_proportion.json"
        if os.path.exists(animal_proportion_path):
            with open(animal_proportion_path, 'r', encoding='utf-8') as f:
                animal_proportion_data = json.load(f)
                
                # Translate animal names in all_animals_percentages
                translated_percentages = {}
                for animal_en, percentage in animal_proportion_data.get('all_animals_percentages', {}).items():
                    animal_fr = analyzer.animal_translations.get(animal_en, animal_en)
                    translated_percentages[animal_fr] = percentage
                
                results['animal_proportion'] = {
                    'user_plumid': animal_proportion_data.get('user_plumid', ''),
                    'user_current_animal': analyzer.animal_translations.get(
                        animal_proportion_data.get('user_current_animal', ''), 
                        animal_proportion_data.get('user_current_animal', '')
                    ),
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
                for i, (animal_en, strength) in enumerate(top3_animals, 1):
                    animal_fr = analyzer.animal_translations.get(animal_en, animal_en)
                    top3_summary[f"Top{i}"] = {
                        "animal": animal_fr,
                        "overall_strength_adjust": strength
                    }
                
                results['top3_summary'] = top3_summary
        
        # 4. Load ChatGPT interpretation
        interpretation_path = "outputs/chatgpt_interpretation.json"
        if os.path.exists(interpretation_path):
            with open(interpretation_path, 'r', encoding='utf-8') as f:
                interpretation_data = json.load(f)
                results['chatgpt_interpretation'] = interpretation_data.get('interpretation', '')
        
    except Exception as e:
        print(f"⚠️  Warning: Could not load some analysis results: {e}")
    
    return results

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
        
        print(f"🔮 Starting analysis for {name} ({date} {time} at {lat}°N, {lon}°W, {country}, {state})")
        
        # Run analysis using the analyzer's run_analysis method
        result = analyzer.run_analysis(
            date=date,
            time=time, 
            lat=lat,
            lon=lon,
            openai_api_key=openai_api_key
        )
        
        # Load additional results for frontend
        analysis_results = load_analysis_results()
        
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
        
        return jsonify(response_data)
        
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

if __name__ == '__main__':
    print("🚀 Starting PLUMATOTM API...")
    
    # Initialize analyzer
    if initialize_analyzer():
        print("✅ API ready to serve requests")
        # Get port from environment (Render sets PORT)
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port, debug=False)
    else:
        print("❌ Failed to start API - analyzer initialization failed")
        exit(1)
