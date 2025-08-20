#!/usr/bin/env python3
"""
PLUMATOTM Animal × Planet Scoring System - HTTP API Server

This FastAPI server exposes the astrological analysis engine as a REST API
for integration with Shopify and other web applications.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import Dict, Any, Optional
import uvicorn
import json
import os
from datetime import datetime

# Import our existing analysis engine
from compute_scores_final import BirthChartAnalyzer, convert_local_to_utc

# Import radar chart generator
from radar_chart_generator import RadarChartGenerator

# Initialize FastAPI app
app = FastAPI(
    title="PLUMATOTM Astrological Analysis API",
    description="API for computing animal scores based on birth chart data",
    version="1.0.0"
)

# Add CORS middleware for web integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the analyzer with our data files
try:
    analyzer = BirthChartAnalyzer(
        "plumatotm_raw_scores.json",
        "plumatotm_planets_weights.csv", 
        "plumatotm_planets_multiplier.csv"
    )
    print("✅ Analysis engine initialized successfully")
except Exception as e:
    print(f"❌ Error initializing analysis engine: {e}")
    analyzer = None

# Initialize radar chart generator
try:
    radar_generator = RadarChartGenerator()
    print("✅ Radar chart generator initialized successfully")
except Exception as e:
    print(f"❌ Error initializing radar chart generator: {e}")
    radar_generator = None

# Pydantic models for request/response validation
class BirthDataRequest(BaseModel):
    date: str  # YYYY-MM-DD
    time: str  # HH:MM (24h format)
    lat: float
    lon: float
    name: Optional[str] = None  # Optional name for reference
    
    @validator('date')
    def validate_date(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')
    
    @validator('time')
    def validate_time(cls, v):
        try:
            datetime.strptime(v, "%H:%M")
            return v
        except ValueError:
            raise ValueError('Time must be in HH:MM format (24h)')
    
    @validator('lat')
    def validate_lat(cls, v):
        if not -90 <= v <= 90:
            raise ValueError('Latitude must be between -90 and 90')
        return v
    
    @validator('lon')
    def validate_lon(cls, v):
        if not -180 <= v <= 180:
            raise ValueError('Longitude must be between -180 and 180')
        return v

class AnalysisResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "PLUMATOTM Astrological Analysis API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "analyzer_ready": analyzer is not None,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_birth_data(request: BirthDataRequest):
    """
    Analyze birth data and return animal scores
    
    This endpoint takes birth date, time, and coordinates,
    computes the astrological chart, and returns the top animal matches.
    """
    
    if analyzer is None:
        raise HTTPException(status_code=500, detail="Analysis engine not available")
    
    try:
        # Convert local time to UTC
        utc_time = convert_local_to_utc(request.date, request.time, request.lat, request.lon)
        
        # Run the analysis
        analyzer.run_analysis(request.date, utc_time, request.lat, request.lon)
        
        # Read the results from the outputs directory
        with open("outputs/result.json", 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        # Extract top 3 animals for easy access
        animal_totals = results.get("animal_totals", [])
        top_3_animals = animal_totals[:3] if animal_totals else []
        
        # Generate radar charts if generator is available
        radar_charts = {}
        if radar_generator is not None:
            try:
                # Create a temporary result structure for the radar generator
                temp_result_data = {
                    "data": {
                        "top_3_animals": top_3_animals,
                        "top3_percentage_strength": results.get("top3_percentage_strength", {})
                    }
                }
                
                            # Generate top animal radar chart
            top_chart_path = radar_generator.generate_top_animal_radar(temp_result_data)
            radar_charts["top_animal_chart"] = top_chart_path
                
            except Exception as e:
                print(f"Warning: Could not generate radar charts: {e}")
                radar_charts = {}
        
        # Create a simplified response for web integration
        response_data = {
            "birth_data": {
                "date": request.date,
                "time": request.time,
                "utc_time": utc_time,
                "lat": request.lat,
                "lon": request.lon,
                "name": request.name
            },
            "birth_chart": results.get("birth_chart", {}),
            "planet_weights": results.get("planet_weights", {}),
            "top_3_animals": top_3_animals,
            "all_animals": animal_totals,
            "analysis_summary": {
                "total_animals_analyzed": len(animal_totals),
                "top_score": top_3_animals[0]["TOTAL_SCORE"] if top_3_animals else 0
            },
            "radar_charts": radar_charts
        }
        
        return AnalysisResponse(
            success=True,
            message="Analysis completed successfully",
            data=response_data
        )
        
    except Exception as e:
        return AnalysisResponse(
            success=False,
            message="Analysis failed",
            error=str(e)
        )

@app.get("/animals")
async def get_available_animals():
    """Get list of all available animals in the system"""
    if analyzer is None:
        raise HTTPException(status_code=500, detail="Analysis engine not available")
    
    return {
        "animals": analyzer.animals,
        "total_count": len(analyzer.animals)
    }

@app.get("/planets")
async def get_supported_planets():
    """Get list of all supported planets/points"""
    if analyzer is None:
        raise HTTPException(status_code=500, detail="Analysis engine not available")
    
    return {
        "planets": analyzer.supported_planets,
        "total_count": len(analyzer.supported_planets)
    }

@app.post("/generate-radar-charts")
async def generate_radar_charts(request: BirthDataRequest):
    """
    Generate radar charts for the given birth data
    
    This endpoint generates radar charts showing the correlation strength
    between the top animal and all planets.
    """
    
    if analyzer is None:
        raise HTTPException(status_code=500, detail="Analysis engine not available")
    
    if radar_generator is None:
        raise HTTPException(status_code=500, detail="Radar chart generator not available")
    
    try:
        # Convert local time to UTC
        utc_time = convert_local_to_utc(request.date, request.time, request.lat, request.lon)
        
        # Run the analysis
        analyzer.run_analysis(request.date, utc_time, request.lat, request.lon)
        
        # Read the results from the outputs directory
        with open("outputs/result.json", 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        # Extract top 3 animals
        animal_totals = results.get("animal_totals", [])
        top_3_animals = animal_totals[:3] if animal_totals else []
        
        # Create result structure for radar generator
        result_data = {
            "data": {
                "top_3_animals": top_3_animals,
                "top3_percentage_strength": results.get("top3_percentage_strength", {})
            }
        }
        
        # Generate radar charts
        top_chart_path = radar_generator.generate_top_animal_radar(result_data)
        
        return {
            "success": True,
            "message": "Radar charts generated successfully",
            "data": {
                "top_animal": top_3_animals[0] if top_3_animals else None,
                            "radar_charts": {
                "top_animal_chart": top_chart_path
            }
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": "Failed to generate radar charts",
            "error": str(e)
        }

if __name__ == "__main__":
    # Run the server
    print("🚀 Starting PLUMATOTM API Server...")
    print("📖 API Documentation available at: http://localhost:8000/docs")
    print("🔗 Health check at: http://localhost:8000/health")
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
