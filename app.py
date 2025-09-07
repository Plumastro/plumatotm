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
            multipliers_csv_path="plumatotm_planets_multiplier.csv"
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
        
        # Return success response
        return jsonify({
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
        })
        
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
