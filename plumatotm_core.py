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
            if -10 <= lon <= 40 and 35 <= lat <= 70:  # Europe
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
        
        print(f"Timezone detected: {timezone_name}")
        print(f"Local time: {local_time} → UTC time: {utc_time}")
        
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
    
    def compute_birth_chart(self, date: str, time: str, lat: float, lon: float) -> Dict[str, str]:
        """Compute birth chart and return planet -> sign mapping."""
        try:
            # Parse date and time - flatlib expects YYYY/MM/DD format
            date_formatted = date.replace('-', '/')
            dt = Datetime(date_formatted, time)
            
            # Create chart with coordinates and explicit object list
            pos = GeoPos(lat, lon)
            chart = Chart(dt, pos, IDs=const.LIST_OBJECTS)
            
            # Extract planet -> sign mapping
            planet_signs = {}
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
                    
                    # Print detailed information for debugging
                    print(f"{planet_name}: {obj.sign} {obj.signlon:.1f}°")
                    
                except Exception as e:
                    print(f"Warning: Could not get {planet_name}: {e}")
                    continue
            
            return planet_signs
            
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
    
    def generate_outputs(self, planet_signs: Dict[str, str], dynamic_weights: Dict[str, float],
                        raw_scores: pd.DataFrame, weighted_scores: pd.DataFrame, 
                        animal_totals: pd.DataFrame, percentage_strength: pd.DataFrame, 
                        true_false_table: pd.DataFrame):
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
        
        # 1. Birth Chart Data (JSON)
        with open(output_files["birth_chart"], 'w', encoding='utf-8') as f:
            json.dump(planet_signs, f, indent=2)
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
            "birth_chart": planet_signs,
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
            radar_result = generate_radar_charts_from_results(output_files["result"])
            if radar_result:
                print(f"📊 Radar chart saved: {radar_result['top_animal_chart']}")
            else:
                print("⚠️  Radar chart generation failed")
        except ImportError:
            print("⚠️  Radar chart module not available")
        except Exception as e:
            print(f"⚠️  Radar chart generation failed: {e}")
        
        # Print summary
        print(f"\n=== ANALYSIS SUMMARY ===")
        print(f"Top 3 animals:")
        for i, (_, row) in enumerate(animal_totals.head(3).iterrows(), 1):
            print(f"{i}. {row['ANIMAL']}: {row['TOTAL_SCORE']:.1f}")
    
    def run_analysis(self, date: str, time: str, lat: float, lon: float):
        """Run the complete analysis pipeline."""
        print(f"Starting analysis for birth data: {date} {time} at coordinates ({lat}, {lon})")
        
        # 1. Compute birth chart
        planet_signs = self.compute_birth_chart(date, time, lat, lon)
        print(f"\nBirth chart computed: {planet_signs}")
        
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
        self.generate_outputs(planet_signs, dynamic_weights, raw_scores, weighted_scores, 
                            animal_totals, percentage_strength, true_false_table)


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
