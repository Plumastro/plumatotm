#!/usr/bin/env python3
"""
Birth Chart Integration Hook

Integration module to connect the birth chart generator with the PLUMATOTM engine.
"""

import json
import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path

from birth_chart import generate_birth_chart

logger = logging.getLogger(__name__)

def integrate_with_plumatotm_engine(
    result_json_path: str,
    icons_dir: str = "icons",
    output_dir: str = "outputs"
) -> str:
    """
    Integration hook for PLUMATOTM engine.
    
    Reads birth data from existing engine results and generates a birth chart.
    
    Args:
        result_json_path: Path to result.json from PLUMATOTM engine
        icons_dir: Directory containing PNG icons
        output_dir: Directory to save the birth chart
    
    Returns:
        Path to the generated birth chart image
    
    Raises:
        FileNotFoundError: If result.json doesn't exist
        ValueError: If birth data is missing or invalid
    """
    try:
        # Load engine results
        with open(result_json_path, 'r', encoding='utf-8') as f:
            result_data = json.load(f)
        
        # Extract birth chart data
        birth_chart_data = result_data.get("birth_chart", {})
        if not birth_chart_data:
            raise ValueError("No birth chart data found in result.json")
        
        # Try to extract original birth data from various possible locations
        birth_data = _extract_birth_data_from_results(result_data)
        
        if not birth_data:
            raise ValueError(
                "Could not extract original birth data from engine results. "
                "Please provide birth data manually or ensure the engine stores it."
            )
        
        # Generate output path
        date = birth_data["date"]
        time = birth_data["time"]
        lat = birth_data["lat"]
        lon = birth_data["lon"]
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename based on birth data
        date_formatted = date.replace('-', '')
        time_formatted = time.replace(':', '')
        lat_str = f"{abs(lat):.4f}".replace('.', '')
        lon_str = f"{abs(lon):.4f}".replace('.', '')
        lat_sign = 'N' if lat >= 0 else 'S'
        lon_sign = 'E' if lon >= 0 else 'W'
        
        filename = f"birth_chart_{date_formatted}_{time_formatted}_{lat_str}{lat_sign}_{lon_str}{lon_sign}.png"
        output_path = os.path.join(output_dir, filename)
        
        # Generate birth chart
        logger.info(f"Generating birth chart from PLUMATOTM results...")
        result_path = generate_birth_chart(
            date=date,
            time=time,
            lat=lat,
            lon=lon,
            icons_dir=icons_dir,
            output_path=output_path
        )
        
        logger.info(f"Birth chart generated from engine results: {result_path}")
        return result_path
        
    except FileNotFoundError:
        raise FileNotFoundError(f"Result file not found: {result_json_path}")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON in result file: {result_json_path}")
    except Exception as e:
        raise ValueError(f"Error processing engine results: {e}")

def _extract_birth_data_from_results(result_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract original birth data from PLUMATOTM engine results.
    
    This function tries to find birth data in various possible locations
    within the engine results structure.
    """
    birth_data = None
    
    # Try different possible locations for birth data
    possible_locations = [
        # Direct birth data
        result_data.get("birth_data"),
        result_data.get("input_data"),
        result_data.get("client_info"),
        
        # From birth chart metadata
        result_data.get("birth_chart", {}).get("birth_data"),
        result_data.get("birth_chart", {}).get("input_data"),
        
        # From analysis metadata
        result_data.get("analysis_metadata", {}).get("birth_data"),
        result_data.get("metadata", {}).get("birth_data"),
    ]
    
    for location in possible_locations:
        if location and isinstance(location, dict):
            # Check if this location has the required fields
            required_fields = ["date", "time", "lat", "lon"]
            if all(field in location for field in required_fields):
                birth_data = {
                    "date": location["date"],
                    "time": location["time"],
                    "lat": float(location["lat"]),
                    "lon": float(location["lon"])
                }
                break
    
    # If still not found, try to extract from file path or other metadata
    if not birth_data:
        birth_data = _extract_from_metadata(result_data)
    
    return birth_data

def _extract_from_metadata(result_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Try to extract birth data from metadata or other sources.
    """
    # Check if there's any metadata that might contain birth info
    metadata = result_data.get("metadata", {})
    
    # Look for common patterns
    if "birth_date" in metadata and "birth_time" in metadata:
        try:
            return {
                "date": metadata["birth_date"],
                "time": metadata["birth_time"],
                "lat": float(metadata.get("latitude", 0)),
                "lon": float(metadata.get("longitude", 0))
            }
        except (ValueError, KeyError):
            pass
    
    return None

def generate_birth_chart_from_engine_cli():
    """
    CLI function for generating birth chart from engine results.
    """
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(
        description="Generate birth chart from PLUMATOTM engine results"
    )
    parser.add_argument("result_json", help="Path to result.json from PLUMATOTM engine")
    parser.add_argument("--icons", default="icons", help="Icons directory")
    parser.add_argument("--output", default="outputs", help="Output directory")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    
    try:
        result_path = integrate_with_plumatotm_engine(
            args.result_json,
            args.icons,
            args.output
        )
        print(f"✅ Birth chart generated: {result_path}")
        return 0
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(generate_birth_chart_from_engine_cli())
