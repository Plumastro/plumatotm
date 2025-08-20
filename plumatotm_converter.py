#!/usr/bin/env python3
"""
CSV to JSON Converter for PLUMATOTM Animal Scores

This script converts the CSV file with animal scores for astrological signs
into the JSON format required by the scoring system.
"""

import pandas as pd
import json
import sys
import os

def convert_csv_to_json(csv_file_path: str, output_json_path: str = None):
    """
    Convert CSV file with animal scores to JSON format.
    
    Args:
        csv_file_path: Path to the input CSV file
        output_json_path: Path for the output JSON file (optional)
    """
    
    # Read the CSV file
    try:
        df = pd.read_csv(csv_file_path)
        print(f"Successfully loaded CSV file: {csv_file_path}")
        print(f"Found {len(df)} animals")
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return
    
    # Clean the data - remove empty rows and rows with all zeros
    df = df.dropna(subset=['ANIMAL-SIGNE'])
    df = df[df['ANIMAL-SIGNE'].str.strip() != '']
    
    # Remove rows where all zodiac sign scores are 0
    zodiac_columns = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                     'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
    
    # Check if all required columns exist
    missing_columns = [col for col in zodiac_columns if col not in df.columns]
    if missing_columns:
        print(f"Warning: Missing columns in CSV: {missing_columns}")
        print(f"Available columns: {list(df.columns)}")
        return
    
    # Filter out rows where all zodiac scores are 0
    df = df[df[zodiac_columns].sum(axis=1) > 0]
    
    print(f"After cleaning: {len(df)} animals with valid scores")
    
    # Convert to the required JSON format
    animals_data = []
    
    for _, row in df.iterrows():
        animal_name = row['ANIMAL-SIGNE'].strip()
        
        # Skip if animal name is empty
        if not animal_name:
            continue
        
        animal_entry = {
            "ANIMAL": animal_name,
            "ARIES": int(row['Aries']) if pd.notna(row['Aries']) else 0,
            "TAURUS": int(row['Taurus']) if pd.notna(row['Taurus']) else 0,
            "GEMINI": int(row['Gemini']) if pd.notna(row['Gemini']) else 0,
            "CANCER": int(row['Cancer']) if pd.notna(row['Cancer']) else 0,
            "LEO": int(row['Leo']) if pd.notna(row['Leo']) else 0,
            "VIRGO": int(row['Virgo']) if pd.notna(row['Virgo']) else 0,
            "LIBRA": int(row['Libra']) if pd.notna(row['Libra']) else 0,
            "SCORPIO": int(row['Scorpio']) if pd.notna(row['Scorpio']) else 0,
            "SAGITTARIUS": int(row['Sagittarius']) if pd.notna(row['Sagittarius']) else 0,
            "CAPRICORN": int(row['Capricorn']) if pd.notna(row['Capricorn']) else 0,
            "AQUARIUS": int(row['Aquarius']) if pd.notna(row['Aquarius']) else 0,
            "PISCES": int(row['Pisces']) if pd.notna(row['Pisces']) else 0
        }
        
        animals_data.append(animal_entry)
    
    # Create the final JSON structure
    json_data = {
        "animals": animals_data
    }
    
    # Determine output file path
    if output_json_path is None:
        base_name = os.path.splitext(csv_file_path)[0]
        output_json_path = f"{base_name}_converted.json"
    
    # Save to JSON file
    try:
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        print(f"Successfully converted {len(animals_data)} animals to JSON")
        print(f"Output saved to: {output_json_path}")
        
        # Print some statistics
        print(f"\n=== CONVERSION STATISTICS ===")
        print(f"Total animals: {len(animals_data)}")
        
        # Show some examples
        print(f"\nFirst 5 animals:")
        for i, animal in enumerate(animals_data[:5], 1):
            print(f"{i}. {animal['ANIMAL']}")
        
        if len(animals_data) > 5:
            print(f"... and {len(animals_data) - 5} more animals")
        
        return output_json_path
        
    except Exception as e:
        print(f"Error saving JSON file: {e}")
        return None

def main():
    """Main function for command line usage."""
    if len(sys.argv) < 2:
        print("Usage: python csv_to_json_converter.py <csv_file> [output_json_file]")
        print("\nExample:")
        print("  python plumatotm_converter.py 'plumatotm_raw_scores.csv'")
        print("  python plumatotm_converter.py 'plumatotm_raw_scores.csv' scores_animaux.json")
        return
    
    csv_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(csv_file):
        print(f"Error: CSV file not found: {csv_file}")
        return
    
    convert_csv_to_json(csv_file, output_file)

if __name__ == "__main__":
    main()
