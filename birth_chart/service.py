"""
Birth Chart Service

Main orchestration service that coordinates calculator and renderer
to generate complete birth charts.
"""

import os
import logging
from typing import Optional
from datetime import datetime

from .calculator import BirthChartCalculator
from .renderer import BirthChartRenderer

logger = logging.getLogger(__name__)

def generate_birth_chart(
    date: str,
    time: str,
    lat: float,
    lon: float,
    icons_dir: str = "icons",
    house_system: str = "placidus",
    zodiac: str = "tropical",
    output_path: Optional[str] = None
) -> str:
    """
    Generate a complete birth chart.
    
    Args:
        date: Date in YYYY-MM-DD format
        time: Local time in HH:MM format (24h)
        lat: Latitude of birth place
        lon: Longitude of birth place
        icons_dir: Directory containing PNG icons
        house_system: House system ("placidus" or "porphyry")
        zodiac: Zodiac system ("tropical" only supported)
        output_path: Custom output path (optional)
    
    Returns:
        Path to the generated PNG file
    
    Raises:
        ValueError: If inputs are invalid
        ImportError: If required dependencies are missing
    """
    try:
        # Validate inputs
        _validate_inputs(date, time, lat, lon, house_system, zodiac)
        
        # Generate output path if not provided
        if output_path is None:
            output_path = _generate_output_path(date, time, lat, lon)
        
        logger.info(f"Generating birth chart for {date} {time} at ({lat}, {lon})")
        
        # Initialize calculator and renderer
        calculator = BirthChartCalculator()
        renderer = BirthChartRenderer(icons_dir)
        
        # Calculate birth chart data
        logger.info("Calculating astrological positions...")
        chart_data = calculator.calculate_birth_chart(
            date=date,
            time=time,
            lat=lat,
            lon=lon,
            house_system=house_system
        )
        
        # Render the chart
        logger.info("Rendering birth chart...")
        image_path = renderer.render_birth_chart(chart_data, output_path)
        
        logger.info(f"Birth chart generated successfully: {image_path}")
        return image_path
        
    except Exception as e:
        logger.error(f"Error generating birth chart: {e}")
        raise

def _validate_inputs(date: str, time: str, lat: float, lon: float, 
                    house_system: str, zodiac: str) -> None:
    """Validate input parameters."""
    # Validate date format
    try:
        datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        raise ValueError("Invalid date format. Use YYYY-MM-DD")
    
    # Validate time format
    try:
        datetime.strptime(time, '%H:%M')
    except ValueError:
        raise ValueError("Invalid time format. Use HH:MM (24h)")
    
    # Validate coordinates
    if not (-90 <= lat <= 90):
        raise ValueError("Latitude must be between -90 and 90")
    if not (-180 <= lon <= 180):
        raise ValueError("Longitude must be between -180 and 180")
    
    # Validate house system
    if house_system.lower() not in ["placidus", "porphyry"]:
        raise ValueError("House system must be 'placidus' or 'porphyry'")
    
    # Validate zodiac
    if zodiac.lower() != "tropical":
        raise ValueError("Only tropical zodiac is supported")

def _generate_output_path(date: str, time: str, lat: float, lon: float) -> str:
    """Generate output path based on birth data."""
    # Ensure outputs directory exists
    os.makedirs("outputs", exist_ok=True)
    
    # Format date and time for filename
    date_formatted = date.replace('-', '')
    time_formatted = time.replace(':', '')
    
    # Format coordinates (remove decimal points for filename)
    lat_str = f"{abs(lat):.4f}".replace('.', '')
    lon_str = f"{abs(lon):.4f}".replace('.', '')
    lat_sign = 'N' if lat >= 0 else 'S'
    lon_sign = 'E' if lon >= 0 else 'W'
    
    filename = f"birth_chart_{date_formatted}_{time_formatted}_{lat_str}{lat_sign}_{lon_str}{lon_sign}.png"
    return os.path.join("outputs", filename)

def integrate_with_engine(result_json_path: str, icons_dir: str = "icons") -> str:
    """
    Integration hook for PLUMATOTM engine.
    
    Reads birth data from existing engine results and generates a birth chart.
    
    Args:
        result_json_path: Path to result.json from PLUMATOTM engine
        icons_dir: Directory containing PNG icons
    
    Returns:
        Path to the generated birth chart image
    
    Raises:
        FileNotFoundError: If result.json doesn't exist
        ValueError: If birth data is missing or invalid
    """
    import json
    
    try:
        # Load engine results
        with open(result_json_path, 'r', encoding='utf-8') as f:
            result_data = json.load(f)
        
        # Extract birth chart data
        birth_chart_data = result_data.get("birth_chart", {})
        if not birth_chart_data:
            raise ValueError("No birth chart data found in result.json")
        
        # For now, we need to get the original birth data
        # This would typically be stored in the engine results
        # For this integration, we'll require the user to provide it
        raise NotImplementedError(
            "Integration with engine requires original birth data. "
            "Please use generate_birth_chart() directly with birth parameters."
        )
        
    except FileNotFoundError:
        raise FileNotFoundError(f"Result file not found: {result_json_path}")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON in result file: {result_json_path}")
    except Exception as e:
        raise ValueError(f"Error reading engine results: {e}")
