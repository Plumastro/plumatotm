#!/usr/bin/env python3
"""
Custom Batch Processor for PLUMATOTM Engine
Processes a specific list of birth profiles without impacting the live API
"""

import json
import time
import csv
from datetime import datetime
from typing import List, Dict
from plumatotm_core import BirthChartAnalyzer
import os

class CustomBatchProcessor:
    """Custom batch processor for specific profile lists."""
    
    def __init__(self, 
                 scores_csv_path: str = "plumatotm_raw_scores_trad.csv",
                 weights_csv_path: str = "plumatotm_planets_weights.csv", 
                 multipliers_csv_path: str = "plumatotm_planets_multiplier.csv",
                 translations_csv_path: str = "plumatotm_raw_scores_trad.csv"):
        """Initialize the custom batch processor."""
        print("🚀 Initializing Custom Batch Processor...")
        
        self.analyzer = BirthChartAnalyzer(
            scores_csv_path=scores_csv_path,
            weights_csv_path=weights_csv_path,
            multipliers_csv_path=multipliers_csv_path,
            translations_csv_path=translations_csv_path
        )
        
        # Load animal data
        self.analyzer._ensure_scores_data_loaded()
        self.analyzer._ensure_animal_translations_loaded()
        
        print(f"✅ Batch processor ready with {len(self.analyzer.animals)} animals")
    
    def process_profiles_from_json(self, profiles_json: str, delay: float = 0.5) -> List[Dict]:
        """
        Process profiles from a JSON string.
        
        Args:
            profiles_json: JSON string containing the profile data
            delay: Delay between analyses (seconds)
            
        Returns:
            List of analysis results
        """
        print("📋 Parsing profiles from JSON input...")
        
        # Parse the JSON input
        profiles = self._parse_profiles_json(profiles_json)
        print(f"✅ Parsed {len(profiles)} profiles")
        
        return self.process_profiles(profiles, delay=delay)
    
    def _parse_profiles_json(self, profiles_json: str) -> List[Dict]:
        """Parse the JSON input into a list of profiles."""
        profiles = []
        
        # Split by lines and look for JSON objects
        lines = profiles_json.strip().split('\n')
        
        current_json = ""
        brace_count = 0
        json_objects = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            current_json += line + "\n"
            
            # Count braces to detect complete JSON objects
            brace_count += line.count('{') - line.count('}')
            
            # If brace count is 0, we have a complete JSON object
            if brace_count == 0 and current_json.strip():
                json_objects.append(current_json.strip())
                current_json = ""
        
        # Process any remaining JSON object
        if current_json.strip():
            json_objects.append(current_json.strip())
        
        for i, json_str in enumerate(json_objects, 1):
            if not json_str:
                continue
                
            try:
                profile = json.loads(json_str)
                
                # Validate required fields
                required_fields = ['date', 'time', 'lat', 'lon']
                missing_fields = [field for field in required_fields if field not in profile]
                
                if missing_fields:
                    print(f"⚠️  Profile {i}: Missing fields {missing_fields}")
                    continue
                
                # Add profile ID
                profile['profile_id'] = i
                
                profiles.append(profile)
                
            except json.JSONDecodeError as e:
                print(f"❌ Profile {i}: JSON decode error - {e}")
                print(f"   JSON string: {json_str[:100]}...")
                continue
        
        return profiles
    
    def process_profiles(self, profiles: List[Dict], delay: float = 0.5) -> List[Dict]:
        """
        Process a list of birth profiles.
        
        Args:
            profiles: List of birth profile dictionaries
            delay: Delay between analyses (seconds)
            
        Returns:
            List of analysis results
        """
        print(f"🔬 Processing {len(profiles)} profiles...")
        print(f"⏱️  Delay between analyses: {delay}s")
        
        results = []
        successful = 0
        failed = 0
        unique_animals = set()
        
        for i, profile in enumerate(profiles, 1):
            print(f"\n📊 Profile {i}/{len(profiles)}: {profile.get('name', 'Unnamed')}")
            print(f"   📅 {profile['date']} {profile['time']}")
            print(f"   📍 {profile['lat']}, {profile['lon']}")
            
            result = self._analyze_profile(profile)
            results.append(result)
            
            if result['analysis_successful']:
                successful += 1
                if result['top1_animal_en']:
                    unique_animals.add(result['top1_animal_en'])
                print(f"   ✅ SUCCESS: {result['top1_animal_en']} (Score: {result['top1_score']:.1f})")
            else:
                failed += 1
                print(f"   ❌ FAILED: {result['error']}")
            
            # Progress summary every 10 profiles
            if i % 10 == 0:
                print(f"\n📈 Progress: {i}/{len(profiles)} | ✅ {successful} | ❌ {failed} | 🎯 {len(unique_animals)} unique animals")
            
            # Delay between analyses
            if delay > 0 and i < len(profiles):
                time.sleep(delay)
        
        print(f"\n🎉 Batch processing completed!")
        print(f"📊 Total: {len(results)} | ✅ Successful: {successful} | ❌ Failed: {failed}")
        print(f"🎯 Unique animals found: {len(unique_animals)}")
        
        return results
    
    def _analyze_profile(self, profile: Dict) -> Dict:
        """Analyze a single birth profile."""
        try:
            # Run the analysis
            self.analyzer.run_analysis(
                date=profile['date'],
                time=profile['time'],
                lat=profile['lat'],
                lon=profile['lon']
            )
            
            # Read the results
            result_path = "outputs/result.json"
            if os.path.exists(result_path):
                with open(result_path, 'r', encoding='utf-8') as f:
                    result_data = json.load(f)
                
                # Extract top1 animal and score
                animal_totals = result_data.get('animal_totals', [])
                if animal_totals:
                    top1_animal = animal_totals[0]['ANIMAL']
                    top1_score = animal_totals[0]['TOTAL_SCORE']
                    
                    # Get animal translation
                    animal_translation = self.analyzer.animal_translations.get(top1_animal, {})
                    animal_fr = animal_translation.get('AnimalFR', top1_animal)
                    
                    return {
                        'profile_id': profile['profile_id'],
                        'name': profile.get('name', ''),
                        'date': profile['date'],
                        'time': profile['time'],
                        'lat': profile['lat'],
                        'lon': profile['lon'],
                        'country': profile.get('country', ''),
                        'state': profile.get('state', ''),
                        'top1_animal_en': top1_animal,
                        'top1_animal_fr': animal_fr,
                        'top1_score': top1_score,
                        'analysis_successful': True,
                        'error': None,
                        'timestamp': datetime.now().isoformat()
                    }
            
            return {
                'profile_id': profile['profile_id'],
                'name': profile.get('name', ''),
                'date': profile['date'],
                'time': profile['time'],
                'lat': profile['lat'],
                'lon': profile['lon'],
                'country': profile.get('country', ''),
                'state': profile.get('state', ''),
                'top1_animal_en': None,
                'top1_animal_fr': None,
                'top1_score': None,
                'analysis_successful': False,
                'error': 'No results found',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'profile_id': profile['profile_id'],
                'name': profile.get('name', ''),
                'date': profile['date'],
                'time': profile['time'],
                'lat': profile['lat'],
                'lon': profile['lon'],
                'country': profile.get('country', ''),
                'state': profile.get('state', ''),
                'top1_animal_en': None,
                'top1_animal_fr': None,
                'top1_score': None,
                'analysis_successful': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def save_results(self, results: List[Dict], filename: str = "custom_batch_results.json"):
        """Save results to JSON file."""
        try:
            os.makedirs("outputs", exist_ok=True)
            output_path = f"outputs/{filename}"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Results saved to: {output_path}")
            return True
        except Exception as e:
            print(f"❌ Error saving results: {e}")
            return False
    
    def save_csv_summary(self, results: List[Dict], filename: str = "custom_batch_summary.csv"):
        """Save a CSV summary of the results."""
        try:
            os.makedirs("outputs", exist_ok=True)
            output_path = f"outputs/{filename}"
            
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                if results:
                    writer = csv.DictWriter(f, fieldnames=results[0].keys())
                    writer.writeheader()
                    writer.writerows(results)
            
            print(f"📊 CSV summary saved to: {output_path}")
            return True
        except Exception as e:
            print(f"❌ Error saving CSV: {e}")
            return False
    
    def print_summary(self, results: List[Dict]):
        """Print a summary of the batch processing results."""
        successful = [r for r in results if r['analysis_successful']]
        failed = [r for r in results if not r['analysis_successful']]
        
        if successful:
            # Animal distribution
            animal_counts = {}
            for result in successful:
                animal = result['top1_animal_en']
                if animal:
                    animal_counts[animal] = animal_counts.get(animal, 0) + 1
            
            sorted_animals = sorted(animal_counts.items(), key=lambda x: x[1], reverse=True)
            
            print(f"\n📊 BATCH PROCESSING SUMMARY")
            print(f"=" * 50)
            print(f"📈 Total profiles: {len(results)}")
            print(f"✅ Successful: {len(successful)}")
            print(f"❌ Failed: {len(failed)}")
            print(f"🎯 Unique animals: {len(animal_counts)}")
            
            print(f"\n🏆 TOP ANIMALS:")
            for i, (animal, count) in enumerate(sorted_animals[:10], 1):
                percentage = count / len(successful) * 100
                print(f"   {i:2d}. {animal:<25} {count:2d} times ({percentage:5.1f}%)")
            
            if failed:
                print(f"\n❌ FAILED PROFILES:")
                for result in failed[:5]:  # Show first 5 failures
                    print(f"   Profile {result['profile_id']}: {result['date']} {result['time']} - {result['error']}")
                if len(failed) > 5:
                    print(f"   ... and {len(failed) - 5} more failures")

def main():
    """Main function for custom batch processing."""
    print("🚀 PLUMATOTM CUSTOM BATCH PROCESSOR")
    print("=" * 60)
    print("⚠️  This is for local testing only - does NOT impact Render API")
    print("=" * 60)
    
    # Your input data
    profiles_input = '''
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
{
  "name": "",
  "date": "2017-06-08",
  "time": "01:19",
  "lat": -33.8688,
  "lon": 151.2093,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1944-01-29",
  "time": "22:40",
  "lat": 55.7558,
  "lon": 37.6173,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1971-05-25",
  "time": "13:57",
  "lat": -23.5505,
  "lon": -46.6333,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1990-09-18",
  "time": "04:12",
  "lat": 19.4326,
  "lon": -99.1332,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2009-12-30",
  "time": "15:23",
  "lat": 34.0522,
  "lon": -118.2437,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1938-07-16",
  "time": "09:44",
  "lat": 41.9028,
  "lon": 12.4964,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1966-02-04",
  "time": "20:59",
  "lat": 48.8566,
  "lon": 2.3522,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1985-04-27",
  "time": "06:31",
  "lat": -1.2921,
  "lon": 36.8219,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2013-08-15",
  "time": "11:08",
  "lat": -26.2041,
  "lon": 28.0473,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1958-10-23",
  "time": "02:54",
  "lat": 31.2304,
  "lon": 121.4737,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1998-01-19",
  "time": "21:47",
  "lat": -34.6037,
  "lon": -58.3816,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2016-05-03",
  "time": "17:39",
  "lat": 52.5200,
  "lon": 13.4050,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1949-11-06",
  "time": "05:22",
  "lat": 43.6532,
  "lon": -79.3832,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1974-09-12",
  "time": "14:01",
  "lat": 13.7563,
  "lon": 100.5018,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2001-03-04",
  "time": "09:14",
  "lat": 25.2769,
  "lon": 55.2962,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1931-12-28",
  "time": "19:37",
  "lat": 59.9139,
  "lon": 10.7522,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1969-06-17",
  "time": "08:25",
  "lat": 30.0444,
  "lon": 31.2357,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1981-03-10",
  "time": "00:53",
  "lat": 39.9042,
  "lon": 116.4074,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2018-02-14",
  "time": "12:18",
  "lat": -36.8485,
  "lon": 174.7633,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1953-07-05",
  "time": "23:46",
  "lat": 19.0760,
  "lon": 72.8777,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1993-10-29",
  "time": "03:42",
  "lat": 14.5995,
  "lon": 120.9842,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2007-04-08",
  "time": "18:36",
  "lat": 35.1796,
  "lon": 129.0756,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1937-08-11",
  "time": "16:59",
  "lat": -22.9068,
  "lon": -43.1729,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1977-01-02",
  "time": "07:55",
  "lat": 12.9716,
  "lon": 77.5946,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1942-05-24",
  "time": "20:16",
  "lat": 60.1699,
  "lon": 24.9384,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1965-11-17",
  "time": "10:12",
  "lat": -41.2865,
  "lon": 174.7762,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2002-08-23",
  "time": "01:58",
  "lat": 41.7151,
  "lon": 44.8271,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2015-01-27",
  "time": "06:44",
  "lat": -15.7975,
  "lon": -47.8919,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1956-09-21",
  "time": "22:30",
  "lat": 50.1109,
  "lon": 8.6821,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1989-06-04",
  "time": "04:55",
  "lat": 28.6139,
  "lon": 77.2090,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1934-10-19",
  "time": "11:21",
  "lat": -4.4419,
  "lon": 15.2663,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1960-12-06",
  "time": "14:47",
  "lat": 43.6532,
  "lon": -79.3832,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1982-02-28",
  "time": "09:31",
  "lat": 25.2769,
  "lon": 55.2962,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2006-03-15",
  "time": "21:14",
  "lat": -12.0464,
  "lon": -77.0428,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2019-09-01",
  "time": "16:29",
  "lat": 45.4642,
  "lon": 9.1900,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1947-06-09",
  "time": "12:36",
  "lat": 64.1355,
  "lon": -21.8954,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1972-03-28",
  "time": "19:49",
  "lat": 35.9078,
  "lon": 127.7669,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1996-12-14",
  "time": "02:20",
  "lat": -17.7134,
  "lon": 178.0650,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2012-07-07",
  "time": "08:59",
  "lat": 19.0760,
  "lon": 72.8777,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1954-05-05",
  "time": "23:15",
  "lat": -25.7461,
  "lon": 28.1881,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1988-11-30",
  "time": "06:41",
  "lat": 14.5995,
  "lon": 120.9842,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1939-02-08",
  "time": "03:56",
  "lat": 37.5665,
  "lon": 126.9780,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1979-08-02",
  "time": "17:38",
  "lat": 34.0522,
  "lon": -118.2437,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2004-04-22",
  "time": "05:27",
  "lat": 60.1699,
  "lon": 24.9384,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2011-10-18",
  "time": "13:02",
  "lat": 64.9631,
  "lon": -19.0208,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1943-09-27",
  "time": "22:41",
  "lat": -15.7975,
  "lon": -47.8919,
  "country": "",
  "state": ""
}
'''
    
    # Initialize processor
    processor = CustomBatchProcessor()
    
    # Configuration
    delay_between_analyses = 0.5  # seconds - adjust as needed
    
    print(f"⚙️  Configuration:")
    print(f"   Delay between analyses: {delay_between_analyses}s")
    print(f"   Profiles to process: {len(profiles_input.strip().split('{')) - 1}")  # Rough count
    
    # Process the profiles
    results = processor.process_profiles_from_json(profiles_input, delay=delay_between_analyses)
    
    # Save results
    processor.save_results(results, "custom_batch_results.json")
    processor.save_csv_summary(results, "custom_batch_summary.csv")
    
    # Print summary
    processor.print_summary(results)
    
    print(f"\n🎉 Custom batch processing completed!")
    print(f"💾 Results saved to outputs/")
    print(f"⚠️  This was local testing only - Render API was NOT affected")

if __name__ == "__main__":
    main()
