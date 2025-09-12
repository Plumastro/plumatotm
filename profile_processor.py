#!/usr/bin/env python3
"""
Simple Profile Processor for PLUMATOTM Engine
Easy-to-use processor for custom profile lists
"""

from custom_batch_processor import CustomBatchProcessor

def process_custom_profiles(profiles_json: str, delay: float = 0.5):
    """
    Process custom profiles from JSON string.
    
    Args:
        profiles_json: JSON string with profile data
        delay: Delay between analyses (seconds)
    """
    print("🚀 Processing custom profiles...")
    print("⚠️  Local testing only - does NOT impact Render API")
    
    # Initialize processor
    processor = CustomBatchProcessor()
    
    # Process profiles
    results = processor.process_profiles_from_json(profiles_json, delay=delay)
    
    # Save results
    processor.save_results(results, "profile_results.json")
    processor.save_csv_summary(results, "profile_summary.csv")
    
    # Print summary
    processor.print_summary(results)
    
    return results

# Example usage
if __name__ == "__main__":
    # Your profiles here - just paste your JSON data
    profiles = '''
{
  "name": "",
  "date": "1962-03-14",
  "time": "07:33",
  "lat": 40.4168,
  "lon": -3.7038,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1995-11-21",
  "time": "18:02",
  "lat": 35.6895,
  "lon": 139.6917,
  "country": "",
  "state": ""
}
'''
    
    # Process with 0.5 second delay between analyses
    results = process_custom_profiles(profiles, delay=0.5)
