#!/usr/bin/env python3
"""
Supabase Batch Processor for PLUMATOTM

This script processes multiple birth profiles in batch and updates Supabase database.
It integrates with the PLUMATOTM core engine and Supabase manager.
"""

import json
import os
import sys
from typing import Dict, List, Optional
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from plumatotm_core import BirthChartAnalyzer
    from supabase_manager import SupabaseManager
    print("✅ Successfully imported PLUMATOTM core and Supabase manager")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure all required modules are available")
    sys.exit(1)

class SupabaseBatchProcessor:
    """Processes multiple birth profiles and updates Supabase database."""
    
    def __init__(self, supabase_config_file: str = "supabase_config.py"):
        """Initialize the batch processor with Supabase configuration."""
        self.supabase_config_file = supabase_config_file
        self.supabase_manager = None
        self.analyzer = None
        
        # Statistics
        self.total_profiles = 0
        self.successful_analyses = 0
        self.failed_analyses = 0
        self.unique_animals = set()
        self.animal_counts = {}
        
    def _initialize_supabase(self) -> bool:
        """Initialize Supabase connection."""
        try:
            print("🔗 Initializing Supabase connection...")
            self.supabase_manager = SupabaseManager(self.supabase_config_file)
            
            # Test connection
            if self.supabase_manager.test_connection():
                print("✅ Supabase connection successful")
                return True
            else:
                print("❌ Supabase connection failed")
                return False
                
        except Exception as e:
            print(f"❌ Failed to initialize Supabase: {e}")
            return False
    
    def _initialize_analyzer(self) -> bool:
        """Initialize the PLUMATOTM analyzer."""
        try:
            print("🔧 Initializing PLUMATOTM analyzer...")
            self.analyzer = BirthChartAnalyzer(
                scores_csv_path="plumatotm_raw_scores_trad.csv",
                weights_csv_path="plumatotm_planets_weights.csv",
                multipliers_csv_path="plumatotm_planets_multiplier.csv"
            )
            print("✅ PLUMATOTM analyzer initialized")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize analyzer: {e}")
            return False
    
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
    
    def _process_single_profile(self, profile: Dict, profile_num: int) -> Dict:
        """Process a single birth profile."""
        print(f"\n📊 Processing profile {profile_num}/{self.total_profiles}")
        print(f"   📅 Date: {profile['date']}")
        print(f"   🕐 Time: {profile['time']}")
        print(f"   📍 Location: {profile['lat']:.4f}, {profile['lon']:.4f}")
        
        try:
            # Run PLUMATOTM analysis
            self.analyzer.run_analysis(
                date=profile['date'],
                time=profile['time'],
                lat=profile['lat'],
                lon=profile['lon']
            )
            
            # Load the result from generated files
            result_file = "outputs/result.json"
            if os.path.exists(result_file):
                with open(result_file, 'r', encoding='utf-8') as f:
                    result = json.load(f)
                
                # Extract top animal information
                animal_totals = result.get('animal_totals', [])
                if animal_totals:
                    top_animal = animal_totals[0]  # First animal is the top one
                    
                    # Get translations
                    animal_en = top_animal.get('ANIMAL', '')
                    animal_translations = self.analyzer.animal_translations.get(animal_en, {})
                    animal_fr = animal_translations.get('AnimalFR', animal_en)
                    
                    return {
                        'analysis_successful': True,
                        'plumid': result.get('plumid', ''),
                        'top1_animal_en': animal_en,
                        'top1_animal_fr': animal_fr,
                        'top1_score': top_animal.get('TOTAL_SCORE', 0.0),
                        'profile_data': profile
                    }
                else:
                    return {
                        'analysis_successful': False,
                        'error': 'No top animals found in result'
                    }
            else:
                return {
                    'analysis_successful': False,
                    'error': 'Result file not generated'
                }
                
        except Exception as e:
            print(f"   ❌ Analysis failed: {e}")
            return {
                'analysis_successful': False,
                'error': str(e)
            }
    
    def _update_supabase(self, result: Dict) -> bool:
        """Update Supabase with analysis result."""
        if not self.supabase_manager:
            print("   ⚠️  No Supabase connection, skipping database update")
            return False
        
        try:
            # Insert into Supabase - use the correct method name
            success = self.supabase_manager.update_animal_statistics(
                plumid=result['plumid'],
                animal_en=result['top1_animal_en'],
                animal_fr=result['top1_animal_fr'],
                score=result['top1_score']
            )
            
            if success:
                print(f"   ✅ Supabase updated successfully")
                return True
            else:
                print(f"   ❌ Supabase update failed")
                return False
                
        except Exception as e:
            print(f"   ❌ Supabase error: {e}")
            return False
    
    def _update_statistics(self, result: Dict):
        """Update processing statistics."""
        if result['analysis_successful']:
            self.successful_analyses += 1
            
            animal_en = result['top1_animal_en']
            if animal_en:
                self.unique_animals.add(animal_en)
                self.animal_counts[animal_en] = self.animal_counts.get(animal_en, 0) + 1
        else:
            self.failed_analyses += 1
    
    def process_batch(self, profiles_json: str) -> Dict:
        """Process a batch of profiles."""
        print("🚀 Starting batch processing...")
        
        # Parse profiles
        profiles = self._parse_profiles_json(profiles_json)
        self.total_profiles = len(profiles)
        
        if self.total_profiles == 0:
            print("❌ No valid profiles found")
            return {
                'success': False,
                'error': 'No valid profiles found'
            }
        
        print(f"📋 Found {self.total_profiles} valid profiles")
        
        # Initialize components
        if not self._initialize_analyzer():
            return {
                'success': False,
                'error': 'Failed to initialize analyzer'
            }
        
        if not self._initialize_supabase():
            print("⚠️  Continuing without Supabase updates...")
        
        # Process each profile
        results = []
        
        for i, profile in enumerate(profiles, 1):
            # Process the profile
            result = self._process_single_profile(profile, i)
            
            # Update Supabase if analysis was successful
            if result['analysis_successful']:
                self._update_supabase(result)
                print(f"   ✅ SUCCESS: {result['top1_animal_en']} (Score: {result['top1_score']:.1f})")
            else:
                print(f"   ❌ FAILED: {result.get('error', 'Unknown error')}")
            
            # Update statistics
            self._update_statistics(result)
            
            results.append(result)
        
        # Print final statistics
        self._print_final_statistics()
        
        return {
            'success': True,
            'total_profiles': self.total_profiles,
            'successful_analyses': self.successful_analyses,
            'failed_analyses': self.failed_analyses,
            'unique_animals': len(self.unique_animals),
            'results': results
        }
    
    def _print_final_statistics(self):
        """Print final processing statistics."""
        print("\n" + "="*60)
        print("📊 BATCH PROCESSING COMPLETE")
        print("="*60)
        print(f"📋 Total profiles processed: {self.total_profiles}")
        print(f"✅ Successful analyses: {self.successful_analyses}")
        print(f"❌ Failed analyses: {self.failed_analyses}")
        print(f"🎯 Unique animals found: {len(self.unique_animals)}")
        
        if self.animal_counts:
            print(f"\n🏆 Top 10 animals:")
            sorted_animals = sorted(self.animal_counts.items(), key=lambda x: x[1], reverse=True)
            for i, (animal, count) in enumerate(sorted_animals[:10], 1):
                print(f"   {i:2d}. {animal}: {count} occurrences")
        
        print("="*60)

def main():
    """Main function to run the batch processor."""
    print("🚀 PLUMATOTM SUPABASE BATCH PROCESSOR")
    print("=" * 60)
    print("🌐 This will update your Supabase database!")
    print("=" * 60)
    
    # Load profiles from JSON file
    try:
        with open('plumastro_1000_profiles.json', 'r', encoding='utf-8') as f:
            profiles_data = json.load(f)
        
        # Convert to the format expected by the processor
        profiles_input = '\n'.join([json.dumps(profile) for profile in profiles_data])
        print(f"📊 Loaded {len(profiles_data)} profiles from plumastro_1000_profiles.json")
        
    except FileNotFoundError:
        print("❌ Error: plumastro_1000_profiles.json not found!")
        return
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON: {e}")
        return
    except Exception as e:
        print(f"❌ Error loading profiles: {e}")
        return
    
    # Configuration
    supabase_config = "supabase_config.py"
    
    # Check if Supabase config exists
    if not os.path.exists(supabase_config):
        print(f"❌ Supabase config file not found: {supabase_config}")
        print("Please create the config file or update the path")
        return
    
    # Create processor
    processor = SupabaseBatchProcessor(supabase_config)
    
    # Process the batch
    try:
        result = processor.process_batch(profiles_input)
        
        if result['success']:
            print(f"\n🎉 Batch processing completed successfully!")
            print(f"📊 Processed {result['total_profiles']} profiles")
            print(f"✅ {result['successful_analyses']} successful analyses")
            print(f"❌ {result['failed_analyses']} failed analyses")
            print(f"🎯 Found {result['unique_animals']} unique animals")
        else:
            print(f"\n❌ Batch processing failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"\n❌ Error during batch processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
  "lon": 28.835051,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1961-01-28",
  "time": "03:38",
  "lat": 10.312158,
  "lon": -67.14608,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2017-01-12",
  "time": "18:29",
  "lat": 37.916909,
  "lon": 58.523677,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1944-09-30",
  "time": "16:09",
  "lat": 18.886433,
  "lon": 72.706825,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1985-02-09",
  "time": "15:13",
  "lat": 33.951769,
  "lon": -6.934071,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1942-01-27",
  "time": "20:25",
  "lat": 4.737503,
  "lon": -74.026195,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1933-10-04",
  "time": "16:00",
  "lat": 39.820328,
  "lon": 116.20019,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1942-06-13",
  "time": "17:04",
  "lat": 18.053015,
  "lon": 102.444481,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2000-04-10",
  "time": "15:35",
  "lat": 10.921899,
  "lon": 106.59964,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1945-04-09",
  "time": "19:44",
  "lat": 8.743196,
  "lon": -79.686295,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2000-07-30",
  "time": "05:05",
  "lat": -8.804879,
  "lon": 13.534518,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1975-03-29",
  "time": "16:20",
  "lat": -1.283738,
  "lon": 36.817646,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1978-05-09",
  "time": "04:40",
  "lat": -11.94258,
  "lon": -77.23309,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1970-10-21",
  "time": "12:48",
  "lat": 24.304754,
  "lon": 54.490371,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1937-12-22",
  "time": "18:28",
  "lat": 28.45514,
  "lon": 77.14639,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2020-05-11",
  "time": "10:21",
  "lat": -37.990922,
  "lon": 144.969841,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1934-10-06",
  "time": "01:49",
  "lat": 41.764081,
  "lon": 44.819479,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2012-04-07",
  "time": "19:32",
  "lat": -6.162712,
  "lon": 107.069094,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1960-11-26",
  "time": "08:06",
  "lat": 60.408379,
  "lon": 25.077763,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1996-02-25",
  "time": "05:48",
  "lat": -13.511162,
  "lon": -71.861006,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1931-05-25",
  "time": "06:04",
  "lat": -17.78444,
  "lon": 31.163272,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1966-11-29",
  "time": "07:32",
  "lat": 36.625023,
  "lon": 10.108011,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1981-12-30",
  "time": "03:26",
  "lat": 55.901165,
  "lon": 37.598975,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1955-01-23",
  "time": "06:57",
  "lat": 11.047928,
  "lon": 106.54657,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1977-05-21",
  "time": "20:17",
  "lat": 41.822594,
  "lon": 44.716605,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1948-06-20",
  "time": "19:18",
  "lat": 13.906062,
  "lon": -89.106064,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2015-05-24",
  "time": "09:10",
  "lat": -22.967513,
  "lon": -43.069137,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1969-05-28",
  "time": "07:23",
  "lat": -41.353222,
  "lon": 174.696846,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1978-06-27",
  "time": "19:06",
  "lat": 28.85563,
  "lon": 77.044778,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1975-10-17",
  "time": "02:30",
  "lat": 41.216271,
  "lon": 29.020197,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2024-01-31",
  "time": "20:10",
  "lat": -20.150582,
  "lon": -44.108052,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1964-01-26",
  "time": "00:13",
  "lat": 22.655512,
  "lon": 120.286214,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2011-05-06",
  "time": "02:20",
  "lat": 33.835969,
  "lon": -118.030403,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1943-02-26",
  "time": "06:20",
  "lat": 49.453559,
  "lon": -123.262445,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2002-01-24",
  "time": "17:00",
  "lat": 50.140559,
  "lon": 14.59641,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1955-07-11",
  "time": "13:02",
  "lat": 22.277746,
  "lon": 113.921401,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1938-08-24",
  "time": "08:34",
  "lat": 9.212807,
  "lon": -79.31496,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1976-01-08",
  "time": "18:01",
  "lat": 22.675137,
  "lon": 120.274492,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2018-10-26",
  "time": "07:39",
  "lat": 12.121092,
  "lon": -86.045446,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1990-08-17",
  "time": "03:34",
  "lat": 59.121216,
  "lon": 18.287023,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1966-08-08",
  "time": "18:10",
  "lat": 12.309229,
  "lon": -86.458107,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1973-11-24",
  "time": "03:29",
  "lat": 50.4206,
  "lon": 30.542388,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1933-01-27",
  "time": "16:37",
  "lat": -36.646754,
  "lon": 174.807386,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1993-05-18",
  "time": "20:14",
  "lat": 35.558269,
  "lon": 51.578318,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1933-10-28",
  "time": "20:57",
  "lat": 53.588262,
  "lon": -7.900617,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1961-05-15",
  "time": "14:17",
  "lat": -25.765924,
  "lon": 32.572571,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1944-04-03",
  "time": "16:47",
  "lat": 43.155736,
  "lon": 141.388272,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1953-12-06",
  "time": "11:26",
  "lat": -34.038744,
  "lon": 18.27037,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1965-01-20",
  "time": "08:56",
  "lat": 35.643898,
  "lon": 51.298178,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1986-03-16",
  "time": "03:15",
  "lat": -7.303493,
  "lon": 112.830421,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1931-07-04",
  "time": "16:37",
  "lat": 41.892932,
  "lon": -87.767551,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1930-11-03",
  "time": "01:33",
  "lat": 14.487892,
  "lon": -17.47973,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1952-02-06",
  "time": "18:55",
  "lat": -34.851086,
  "lon": 138.831333,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1937-01-24",
  "time": "08:51",
  "lat": -33.836988,
  "lon": 151.331227,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2008-08-12",
  "time": "01:07",
  "lat": 29.990795,
  "lon": 31.027457,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2018-08-11",
  "time": "15:34",
  "lat": 6.717819,
  "lon": 79.970807,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1958-05-30",
  "time": "03:57",
  "lat": -34.732323,
  "lon": -56.240884,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1930-10-07",
  "time": "22:34",
  "lat": 45.401744,
  "lon": 9.287235,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1943-04-09",
  "time": "20:06",
  "lat": 33.855768,
  "lon": -118.011042,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1994-06-29",
  "time": "19:02",
  "lat": 18.447315,
  "lon": -69.947013,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1989-02-12",
  "time": "00:38",
  "lat": 34.097303,
  "lon": -6.629354,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1942-04-10",
  "time": "09:52",
  "lat": 41.267751,
  "lon": -8.408482,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2012-10-08",
  "time": "03:07",
  "lat": 43.771659,
  "lon": -79.330031,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1998-08-18",
  "time": "17:51",
  "lat": 11.932237,
  "lon": -86.024111,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1939-11-12",
  "time": "09:03",
  "lat": 15.467916,
  "lon": 32.741659,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1963-07-11",
  "time": "17:35",
  "lat": 14.436412,
  "lon": 120.831984,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2021-01-06",
  "time": "13:45",
  "lat": -22.992904,
  "lon": -43.000713,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2023-10-16",
  "time": "16:19",
  "lat": -6.340042,
  "lon": 106.992806,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1967-09-02",
  "time": "17:16",
  "lat": -22.979212,
  "lon": -43.356044,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1952-12-22",
  "time": "03:02",
  "lat": -13.745211,
  "lon": -71.744507,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1977-12-14",
  "time": "14:25",
  "lat": 30.523015,
  "lon": 114.336315,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2016-10-18",
  "time": "08:12",
  "lat": 50.989817,
  "lon": 4.124901,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1952-08-05",
  "time": "03:03",
  "lat": 12.888139,
  "lon": 77.419528,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2000-11-18",
  "time": "20:58",
  "lat": 12.886417,
  "lon": 77.428274,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1981-03-12",
  "time": "23:37",
  "lat": 44.645652,
  "lon": 25.976228,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1960-02-06",
  "time": "08:26",
  "lat": 13.68811,
  "lon": 100.257288,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1981-12-19",
  "time": "05:29",
  "lat": 40.982363,
  "lon": 28.772095,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1953-09-25",
  "time": "19:46",
  "lat": 25.04729,
  "lon": 55.364002,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1937-04-25",
  "time": "08:34",
  "lat": 45.713639,
  "lon": -73.691212,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1984-09-23",
  "time": "13:55",
  "lat": 30.387948,
  "lon": 114.416734,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1939-08-14",
  "time": "11:25",
  "lat": 41.892613,
  "lon": 45.047761,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1946-01-06",
  "time": "08:59",
  "lat": -33.872008,
  "lon": 18.625268,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1988-07-10",
  "time": "03:42",
  "lat": 13.226927,
  "lon": 80.322953,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2008-08-05",
  "time": "21:37",
  "lat": -9.041507,
  "lon": 13.478138,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1973-08-07",
  "time": "15:00",
  "lat": 14.723229,
  "lon": -90.435711,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1993-03-23",
  "time": "03:15",
  "lat": 23.297736,
  "lon": -82.195996,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1980-02-19",
  "time": "04:10",
  "lat": 36.805685,
  "lon": 10.127444,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1936-04-14",
  "time": "07:29",
  "lat": -33.623839,
  "lon": -70.677501,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1946-06-15",
  "time": "06:46",
  "lat": 33.123078,
  "lon": 44.166437,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2020-01-09",
  "time": "13:13",
  "lat": -19.841144,
  "lon": -43.865225,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2015-03-19",
  "time": "23:25",
  "lat": 22.124738,
  "lon": 114.179467,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2018-12-26",
  "time": "12:13",
  "lat": 12.055173,
  "lon": -86.274871,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2016-08-23",
  "time": "17:40",
  "lat": 5.504233,
  "lon": -0.183095,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1963-03-02",
  "time": "04:21",
  "lat": 27.776926,
  "lon": 85.436984,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1950-01-14",
  "time": "07:31",
  "lat": 51.294946,
  "lon": 0.009123,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1965-11-17",
  "time": "14:25",
  "lat": -41.32279,
  "lon": 174.951704,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2011-09-09",
  "time": "05:06",
  "lat": 37.816778,
  "lon": 23.67794,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1989-01-09",
  "time": "02:26",
  "lat": -32.050285,
  "lon": 115.914485,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1958-12-20",
  "time": "14:09",
  "lat": 60.329895,
  "lon": 24.999294,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1945-06-27",
  "time": "15:39",
  "lat": -25.273417,
  "lon": -57.572861,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1992-09-22",
  "time": "23:04",
  "lat": 39.855813,
  "lon": 116.583672,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1994-09-19",
  "time": "06:30",
  "lat": 21.714856,
  "lon": 39.332105,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1966-11-02",
  "time": "09:49",
  "lat": 41.545817,
  "lon": 69.300202,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1946-10-27",
  "time": "06:17",
  "lat": 33.511154,
  "lon": 44.574137,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1980-03-02",
  "time": "16:28",
  "lat": 37.733483,
  "lon": 126.965357,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1982-02-16",
  "time": "21:36",
  "lat": 63.916037,
  "lon": -21.95089,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1971-08-21",
  "time": "01:38",
  "lat": 6.012659,
  "lon": -75.726321,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1991-10-05",
  "time": "20:16",
  "lat": 49.9847,
  "lon": 14.301768,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1931-05-06",
  "time": "03:49",
  "lat": 31.833596,
  "lon": 35.988369,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1978-09-19",
  "time": "23:38",
  "lat": 11.543112,
  "lon": 104.927,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1963-02-16",
  "time": "19:29",
  "lat": 42.669408,
  "lon": 23.323757,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2008-10-14",
  "time": "18:40",
  "lat": 24.460244,
  "lon": 54.167409,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1939-03-17",
  "time": "17:43",
  "lat": 14.477596,
  "lon": 121.057675,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1939-10-13",
  "time": "22:47",
  "lat": 44.672767,
  "lon": 20.640102,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1935-02-01",
  "time": "09:34",
  "lat": 24.266545,
  "lon": 54.205587,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1962-09-27",
  "time": "03:57",
  "lat": 40.780494,
  "lon": 29.256231,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2011-09-07",
  "time": "23:45",
  "lat": 8.769915,
  "lon": -79.314319,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1937-04-08",
  "time": "10:04",
  "lat": -16.417521,
  "lon": -67.878539,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1934-10-05",
  "time": "15:35",
  "lat": -3.344489,
  "lon": -60.179701,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1935-03-28",
  "time": "09:09",
  "lat": 24.866729,
  "lon": 46.469865,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2013-11-26",
  "time": "07:18",
  "lat": 28.399489,
  "lon": 77.279935,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2005-01-12",
  "time": "11:10",
  "lat": 28.722601,
  "lon": 77.174214,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2015-03-25",
  "time": "02:36",
  "lat": 22.515953,
  "lon": 114.097624,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1967-05-02",
  "time": "21:10",
  "lat": -27.434284,
  "lon": 152.940322,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2015-05-05",
  "time": "01:10",
  "lat": 50.278633,
  "lon": 30.764606,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1971-03-13",
  "time": "16:53",
  "lat": 29.214374,
  "lon": 47.778867,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1999-02-21",
  "time": "00:16",
  "lat": 13.088672,
  "lon": 80.400548,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1947-01-15",
  "time": "22:48",
  "lat": -17.60237,
  "lon": 31.223925,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1960-12-17",
  "time": "13:48",
  "lat": -1.06708,
  "lon": 36.654258,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1949-10-18",
  "time": "00:00",
  "lat": 41.121312,
  "lon": 69.377558,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1940-12-27",
  "time": "17:27",
  "lat": -8.79155,
  "lon": 13.372989,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1979-01-16",
  "time": "22:10",
  "lat": 31.938295,
  "lon": 35.341895,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1978-03-10",
  "time": "15:21",
  "lat": 8.842901,
  "lon": -79.381891,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1988-02-07",
  "time": "07:56",
  "lat": 20.822709,
  "lon": 106.082847,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1962-01-28",
  "time": "11:31",
  "lat": -13.393013,
  "lon": -72.136575,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1992-11-09",
  "time": "10:19",
  "lat": 41.479847,
  "lon": 69.114867,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2001-02-22",
  "time": "16:01",
  "lat": 38.104785,
  "lon": 23.926251,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1939-04-22",
  "time": "04:47",
  "lat": 42.61122,
  "lon": 23.184549,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2001-05-07",
  "time": "21:06",
  "lat": 14.526226,
  "lon": -17.241501,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2019-12-01",
  "time": "09:57",
  "lat": 17.98421,
  "lon": 102.716625,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1957-05-08",
  "time": "18:27",
  "lat": 14.754083,
  "lon": 120.737419,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2011-02-13",
  "time": "08:15",
  "lat": -4.281697,
  "lon": 15.346928,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2017-11-04",
  "time": "19:15",
  "lat": 18.010056,
  "lon": -76.752095,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1983-07-04",
  "time": "05:01",
  "lat": 24.282681,
  "lon": 54.475459,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1960-03-03",
  "time": "00:14",
  "lat": 25.029366,
  "lon": 55.538368,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2007-03-21",
  "time": "20:31",
  "lat": 22.908964,
  "lon": 113.465328,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1949-11-21",
  "time": "11:15",
  "lat": 12.737375,
  "lon": 77.380226,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2025-02-05",
  "time": "08:14",
  "lat": 28.55626,
  "lon": 77.213127,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1975-10-29",
  "time": "22:42",
  "lat": 40.109442,
  "lon": 116.43797,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1965-06-16",
  "time": "09:32",
  "lat": 59.823409,
  "lon": 30.26745,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1998-05-15",
  "time": "01:20",
  "lat": 10.636995,
  "lon": -66.88112,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1999-12-26",
  "time": "21:13",
  "lat": 8.748766,
  "lon": 38.974477,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1962-02-01",
  "time": "22:05",
  "lat": 9.70465,
  "lon": -83.948846,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2007-12-22",
  "time": "01:04",
  "lat": 25.466221,
  "lon": 55.06281,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1960-04-10",
  "time": "02:47",
  "lat": 5.401445,
  "lon": -0.387976,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1980-02-20",
  "time": "18:46",
  "lat": 10.233385,
  "lon": -67.051704,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1953-12-20",
  "time": "22:59",
  "lat": -1.059485,
  "lon": 36.89135,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2013-09-09",
  "time": "02:20",
  "lat": -32.789841,
  "lon": -60.635951,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2021-05-10",
  "time": "14:51",
  "lat": -4.585475,
  "lon": 15.108045,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1943-03-27",
  "time": "03:52",
  "lat": 19.640988,
  "lon": -99.219326,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1942-06-11",
  "time": "18:46",
  "lat": -37.067357,
  "lon": 174.582204,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1957-09-17",
  "time": "03:20",
  "lat": 44.557132,
  "lon": 20.274733,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2004-06-04",
  "time": "14:34",
  "lat": 12.083778,
  "lon": -86.270652,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2011-07-02",
  "time": "17:04",
  "lat": -36.825038,
  "lon": 174.749503,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1956-05-08",
  "time": "01:35",
  "lat": -41.333207,
  "lon": 174.914952,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1932-05-16",
  "time": "17:52",
  "lat": 37.537681,
  "lon": 127.079956,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1930-08-21",
  "time": "03:26",
  "lat": 38.757903,
  "lon": -8.940169,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1962-10-12",
  "time": "15:25",
  "lat": -17.802493,
  "lon": 31.090738,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1950-02-18",
  "time": "16:16",
  "lat": 45.64358,
  "lon": -73.786478,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1942-06-28",
  "time": "12:05",
  "lat": 51.638635,
  "lon": -0.074619,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1958-05-25",
  "time": "04:09",
  "lat": -29.664638,
  "lon": 30.959739,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1953-04-22",
  "time": "22:28",
  "lat": 40.991848,
  "lon": 28.856408,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1956-04-11",
  "time": "07:09",
  "lat": 38.181154,
  "lon": 58.444902,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1939-07-05",
  "time": "03:04",
  "lat": 42.001442,
  "lon": 12.461376,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1976-08-03",
  "time": "16:57",
  "lat": 9.686507,
  "lon": -84.086583,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2011-09-08",
  "time": "00:10",
  "lat": 23.343862,
  "lon": 58.547039,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2009-04-23",
  "time": "00:57",
  "lat": -19.720251,
  "lon": -44.029036,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1997-01-04",
  "time": "10:54",
  "lat": 15.579508,
  "lon": 32.662151,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1976-03-04",
  "time": "22:15",
  "lat": 35.696541,
  "lon": 51.567865,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1974-07-16",
  "time": "06:02",
  "lat": -25.205246,
  "lon": -49.061402,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2012-07-19",
  "time": "09:33",
  "lat": 44.692797,
  "lon": 20.627558,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2007-12-30",
  "time": "20:26",
  "lat": 40.623784,
  "lon": -3.831698,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1979-09-07",
  "time": "21:12",
  "lat": 39.976015,
  "lon": 116.453872,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1973-11-30",
  "time": "00:47",
  "lat": -33.770437,
  "lon": 18.439926,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1940-06-08",
  "time": "14:07",
  "lat": -27.59614,
  "lon": 152.902279,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1947-05-09",
  "time": "20:15",
  "lat": 18.00028,
  "lon": 102.81141,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1936-02-21",
  "time": "14:38",
  "lat": 24.9208,
  "lon": 121.619643,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1981-01-21",
  "time": "13:57",
  "lat": 41.918768,
  "lon": -87.408638,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2025-07-21",
  "time": "04:43",
  "lat": 40.36395,
  "lon": -3.795829,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1941-12-24",
  "time": "04:16",
  "lat": 45.712145,
  "lon": -73.488424,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1962-11-01",
  "time": "18:36",
  "lat": 4.510716,
  "lon": -74.056818,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1959-05-06",
  "time": "15:39",
  "lat": 47.433945,
  "lon": 8.30191,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1967-11-22",
  "time": "02:42",
  "lat": 12.865643,
  "lon": 80.195712,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1969-12-19",
  "time": "04:50",
  "lat": 35.545897,
  "lon": 51.266618,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1939-03-26",
  "time": "06:24",
  "lat": -37.975251,
  "lon": 145.181357,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1942-06-06",
  "time": "22:54",
  "lat": 35.399894,
  "lon": 136.734306,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1957-07-10",
  "time": "21:22",
  "lat": 18.730303,
  "lon": -69.855007,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1942-11-23",
  "time": "17:09",
  "lat": 40.559642,
  "lon": 50.078411,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2007-09-30",
  "time": "07:14",
  "lat": 37.698487,
  "lon": 127.118257,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1953-12-07",
  "time": "02:06",
  "lat": 24.945592,
  "lon": 46.478858,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1960-03-15",
  "time": "19:55",
  "lat": 37.750253,
  "lon": 58.487515,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2014-04-09",
  "time": "22:22",
  "lat": 25.387201,
  "lon": 55.283854,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1956-12-11",
  "time": "15:09",
  "lat": 5.382254,
  "lon": -0.024175,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2003-02-20",
  "time": "22:30",
  "lat": -26.01133,
  "lon": 28.007339,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2008-03-29",
  "time": "08:43",
  "lat": 30.674249,
  "lon": 103.921865,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2014-10-25",
  "time": "16:03",
  "lat": 27.941354,
  "lon": 85.094049,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2009-02-26",
  "time": "14:50",
  "lat": 46.297226,
  "lon": 6.246343,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2014-09-09",
  "time": "11:14",
  "lat": 40.072457,
  "lon": 44.530791,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1957-04-28",
  "time": "04:46",
  "lat": 50.411504,
  "lon": 30.692249,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1960-05-16",
  "time": "23:32",
  "lat": -29.989184,
  "lon": 30.910098,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1935-07-30",
  "time": "12:57",
  "lat": 53.650568,
  "lon": -7.765269,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2021-03-14",
  "time": "02:21",
  "lat": 19.435265,
  "lon": -99.182509,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1931-04-10",
  "time": "20:14",
  "lat": -23.757416,
  "lon": -46.717499,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1998-12-20",
  "time": "12:12",
  "lat": -1.33789,
  "lon": 37.016678,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1947-08-21",
  "time": "00:43",
  "lat": 39.957194,
  "lon": 44.443951,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1966-05-05",
  "time": "02:58",
  "lat": 40.843799,
  "lon": -74.06593,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1985-03-20",
  "time": "03:18",
  "lat": 25.073019,
  "lon": 67.049143,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1957-08-05",
  "time": "22:13",
  "lat": -4.662308,
  "lon": 15.198263,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1969-10-31",
  "time": "02:10",
  "lat": 48.989096,
  "lon": 2.438902,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1949-07-29",
  "time": "16:52",
  "lat": -34.896429,
  "lon": 138.746256,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2011-01-24",
  "time": "00:13",
  "lat": 30.388696,
  "lon": 114.295619,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1994-12-14",
  "time": "22:48",
  "lat": 3.531434,
  "lon": -76.76836,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1980-07-19",
  "time": "21:01",
  "lat": -33.524057,
  "lon": -70.686152,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1982-10-05",
  "time": "07:56",
  "lat": 52.576199,
  "lon": 13.219562,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2015-02-12",
  "time": "01:34",
  "lat": 4.709626,
  "lon": -74.161823,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1985-04-01",
  "time": "12:11",
  "lat": 31.581933,
  "lon": 35.034876,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1948-04-24",
  "time": "03:31",
  "lat": 46.207911,
  "lon": 5.995879,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2003-06-17",
  "time": "10:12",
  "lat": 43.155192,
  "lon": 141.108415,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1996-03-11",
  "time": "23:26",
  "lat": 30.116988,
  "lon": 31.078616,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1942-08-08",
  "time": "02:55",
  "lat": -3.694761,
  "lon": -38.627018,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1982-09-03",
  "time": "15:07",
  "lat": 25.077462,
  "lon": 51.63534,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2025-04-01",
  "time": "22:16",
  "lat": 48.376166,
  "lon": 16.139417,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2008-10-07",
  "time": "23:39",
  "lat": 5.602132,
  "lon": -4.185401,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1950-11-16",
  "time": "11:24",
  "lat": -36.909323,
  "lon": 174.970555,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1935-08-05",
  "time": "07:16",
  "lat": -1.125241,
  "lon": 36.606911,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1987-03-30",
  "time": "17:30",
  "lat": 55.877333,
  "lon": 37.572852,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2025-08-20",
  "time": "03:35",
  "lat": 14.751626,
  "lon": -90.478402,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2009-08-26",
  "time": "21:31",
  "lat": 11.338713,
  "lon": 105.169977,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1974-02-25",
  "time": "20:47",
  "lat": -29.962326,
  "lon": 31.233103,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1951-08-04",
  "time": "03:51",
  "lat": 7.032189,
  "lon": 79.686338,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1944-08-12",
  "time": "10:13",
  "lat": 31.903341,
  "lon": 35.726142,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2014-04-13",
  "time": "16:57",
  "lat": 34.040219,
  "lon": -118.005575,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1931-10-22",
  "time": "20:40",
  "lat": 35.468439,
  "lon": 139.731042,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1940-06-19",
  "time": "06:51",
  "lat": 9.004354,
  "lon": 38.891272,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2004-02-20",
  "time": "04:40",
  "lat": 53.268234,
  "lon": -6.239292,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1988-05-09",
  "time": "22:24",
  "lat": 30.562376,
  "lon": 114.484522,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1947-04-09",
  "time": "14:33",
  "lat": 53.41185,
  "lon": -8.177043,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1959-05-02",
  "time": "16:00",
  "lat": 49.062653,
  "lon": 2.559869,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1952-02-08",
  "time": "06:05",
  "lat": 53.326605,
  "lon": -6.108385,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1960-09-05",
  "time": "09:31",
  "lat": 18.352144,
  "lon": -72.198016,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2021-06-19",
  "time": "06:21",
  "lat": 13.730883,
  "lon": -89.274391,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1961-06-28",
  "time": "00:41",
  "lat": 24.653514,
  "lon": 67.200186,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2001-10-22",
  "time": "23:46",
  "lat": 41.137581,
  "lon": 28.805004,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1967-12-01",
  "time": "21:06",
  "lat": 39.860154,
  "lon": 116.449821,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2000-02-12",
  "time": "19:25",
  "lat": 41.284151,
  "lon": 69.086879,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2020-11-26",
  "time": "06:55",
  "lat": 15.444273,
  "lon": 32.766646,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2017-01-25",
  "time": "14:27",
  "lat": -31.760672,
  "lon": 115.697783,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1957-05-04",
  "time": "16:45",
  "lat": 30.485521,
  "lon": 114.371277,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1947-12-01",
  "time": "16:17",
  "lat": 55.850944,
  "lon": -4.122749,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1933-08-04",
  "time": "15:13",
  "lat": 12.190824,
  "lon": -86.461951,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1947-07-12",
  "time": "10:48",
  "lat": 35.685749,
  "lon": 139.645229,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1997-12-09",
  "time": "09:39",
  "lat": 31.948481,
  "lon": 35.741252,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1965-05-25",
  "time": "04:11",
  "lat": 28.689113,
  "lon": 77.01572,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1969-09-22",
  "time": "11:12",
  "lat": -36.810187,
  "lon": 174.780022,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1995-01-27",
  "time": "04:32",
  "lat": 36.894732,
  "lon": 3.016819,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1949-07-16",
  "time": "02:27",
  "lat": 14.777841,
  "lon": -17.357311,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1935-04-14",
  "time": "00:37",
  "lat": 20.954355,
  "lon": 105.875864,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1983-08-02",
  "time": "08:02",
  "lat": 48.70062,
  "lon": 2.585325,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1997-03-13",
  "time": "23:28",
  "lat": 41.361956,
  "lon": 69.366485,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1948-03-21",
  "time": "09:56",
  "lat": 38.068293,
  "lon": 23.81953,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1982-06-19",
  "time": "22:30",
  "lat": 19.522506,
  "lon": -98.996789,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1983-12-27",
  "time": "05:00",
  "lat": 52.290106,
  "lon": 21.004729,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2012-03-03",
  "time": "02:29",
  "lat": 41.796762,
  "lon": 12.460391,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2005-02-16",
  "time": "11:40",
  "lat": -32.706819,
  "lon": -60.720733,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2014-03-02",
  "time": "10:08",
  "lat": 34.155318,
  "lon": 109.16598,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1953-07-20",
  "time": "01:21",
  "lat": 43.595423,
  "lon": -79.183593,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2008-10-02",
  "time": "01:47",
  "lat": 18.463764,
  "lon": -72.327013,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2010-02-05",
  "time": "22:55",
  "lat": -0.10627,
  "lon": -78.326591,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1992-09-18",
  "time": "20:41",
  "lat": 41.800278,
  "lon": -87.47392,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1997-07-22",
  "time": "20:15",
  "lat": 3.313348,
  "lon": -76.62313,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1932-12-06",
  "time": "10:26",
  "lat": 0.231497,
  "lon": 32.760114,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2019-05-22",
  "time": "07:34",
  "lat": 49.134526,
  "lon": -122.919559,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2024-10-16",
  "time": "15:40",
  "lat": 5.618942,
  "lon": -0.23759,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1949-03-01",
  "time": "18:47",
  "lat": 55.768784,
  "lon": 12.702476,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2011-04-16",
  "time": "16:33",
  "lat": 11.549862,
  "lon": 104.736199,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1958-03-04",
  "time": "12:08",
  "lat": -32.782914,
  "lon": -60.69364,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2016-02-09",
  "time": "03:51",
  "lat": -8.86644,
  "lon": 13.090324,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2005-03-10",
  "time": "01:22",
  "lat": 52.37317,
  "lon": 20.858462,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1951-05-27",
  "time": "05:59",
  "lat": 22.772672,
  "lon": 88.193911,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2011-08-28",
  "time": "18:56",
  "lat": 55.741881,
  "lon": -3.367845,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2024-05-01",
  "time": "16:40",
  "lat": 31.754634,
  "lon": 74.578368,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1944-08-15",
  "time": "18:21",
  "lat": -34.443461,
  "lon": -58.382513,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2008-11-29",
  "time": "19:01",
  "lat": -31.401726,
  "lon": -64.323773,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1959-05-07",
  "time": "10:02",
  "lat": -11.940554,
  "lon": -77.114471,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1954-07-09",
  "time": "10:24",
  "lat": 34.596053,
  "lon": 135.331259,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2013-04-13",
  "time": "19:36",
  "lat": 30.226116,
  "lon": 31.141988,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2006-10-02",
  "time": "01:19",
  "lat": 23.073398,
  "lon": -82.538119,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1938-01-01",
  "time": "06:07",
  "lat": -41.380612,
  "lon": 174.587122,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1971-01-27",
  "time": "10:16",
  "lat": 23.906639,
  "lon": 90.630945,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1964-01-18",
  "time": "21:22",
  "lat": 24.998434,
  "lon": 121.494974,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1969-05-11",
  "time": "16:26",
  "lat": 22.548175,
  "lon": 88.490045,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1942-03-23",
  "time": "09:55",
  "lat": 10.862462,
  "lon": 106.51411,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2024-05-23",
  "time": "12:21",
  "lat": -25.852603,
  "lon": 32.477932,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1937-06-17",
  "time": "11:11",
  "lat": 13.865433,
  "lon": -89.001677,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1944-09-04",
  "time": "21:42",
  "lat": 45.977399,
  "lon": 6.001608,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1987-10-03",
  "time": "19:33",
  "lat": 40.19223,
  "lon": -3.647013,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2019-02-11",
  "time": "01:08",
  "lat": 41.899288,
  "lon": 12.744139,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1985-09-05",
  "time": "09:57",
  "lat": 23.697865,
  "lon": 90.649155,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2002-05-06",
  "time": "23:33",
  "lat": -1.469937,
  "lon": 36.639932,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1953-02-25",
  "time": "00:14",
  "lat": 31.140154,
  "lon": 121.497444,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2001-09-11",
  "time": "12:30",
  "lat": 23.650415,
  "lon": 58.270787,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2003-05-09",
  "time": "08:27",
  "lat": 1.154044,
  "lon": 104.010837,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1983-09-30",
  "time": "12:26",
  "lat": 12.830997,
  "lon": 77.755114,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2001-09-16",
  "time": "01:47",
  "lat": 43.054712,
  "lon": 141.426391,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1961-01-03",
  "time": "16:33",
  "lat": -33.730749,
  "lon": 18.532829,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1957-02-11",
  "time": "04:36",
  "lat": 34.721518,
  "lon": 135.616713,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1936-07-22",
  "time": "01:02",
  "lat": 45.558757,
  "lon": 9.276858,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1971-07-28",
  "time": "09:23",
  "lat": -27.626144,
  "lon": 153.24478,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1948-07-02",
  "time": "08:19",
  "lat": -8.733446,
  "lon": 13.51323,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2005-02-21",
  "time": "21:54",
  "lat": -34.733841,
  "lon": -56.206143,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1944-08-07",
  "time": "13:31",
  "lat": 4.864174,
  "lon": -74.071428,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1980-09-19",
  "time": "22:49",
  "lat": 40.419163,
  "lon": 44.345438,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1947-03-16",
  "time": "06:55",
  "lat": 60.37351,
  "lon": 24.948753,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1991-12-08",
  "time": "14:29",
  "lat": -33.480105,
  "lon": -70.491072,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1969-07-19",
  "time": "02:59",
  "lat": -23.326377,
  "lon": -46.78506,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1978-05-17",
  "time": "03:18",
  "lat": -26.243895,
  "lon": 28.288721,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1995-11-27",
  "time": "11:55",
  "lat": -0.391184,
  "lon": -78.691072,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1931-01-03",
  "time": "19:48",
  "lat": 35.70033,
  "lon": 139.846923,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1943-10-06",
  "time": "18:49",
  "lat": -13.564124,
  "lon": -72.022901,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1957-04-07",
  "time": "18:39",
  "lat": 37.838322,
  "lon": 23.915395,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1959-08-13",
  "time": "10:47",
  "lat": -26.004515,
  "lon": 27.81928,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1962-05-01",
  "time": "17:14",
  "lat": 52.376308,
  "lon": 13.210227,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2012-07-14",
  "time": "22:25",
  "lat": 33.950168,
  "lon": -7.059786,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1992-09-20",
  "time": "06:57",
  "lat": -33.965904,
  "lon": 151.320463,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1963-03-12",
  "time": "23:57",
  "lat": 38.49448,
  "lon": -9.35298,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1971-09-09",
  "time": "01:22",
  "lat": 43.077285,
  "lon": 141.184327,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1943-06-05",
  "time": "05:49",
  "lat": 55.670777,
  "lon": 37.820593,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2000-10-01",
  "time": "07:32",
  "lat": 39.684487,
  "lon": 116.380253,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1931-02-17",
  "time": "23:49",
  "lat": 31.835267,
  "lon": 35.911918,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1964-06-14",
  "time": "07:55",
  "lat": 22.426948,
  "lon": 114.222988,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1930-09-17",
  "time": "04:13",
  "lat": 34.960705,
  "lon": 129.093747,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2018-10-29",
  "time": "16:41",
  "lat": 35.650326,
  "lon": 51.425904,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1976-02-24",
  "time": "06:44",
  "lat": 40.288719,
  "lon": 49.672948,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1932-07-08",
  "time": "00:23",
  "lat": 24.967181,
  "lon": 121.771612,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1996-01-17",
  "time": "21:55",
  "lat": 43.664901,
  "lon": -79.293137,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2001-10-13",
  "time": "18:30",
  "lat": 6.360887,
  "lon": 3.14327,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1960-03-12",
  "time": "11:21",
  "lat": 30.093752,
  "lon": 31.347808,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1970-03-27",
  "time": "02:20",
  "lat": 48.322793,
  "lon": 16.359366,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1942-03-17",
  "time": "18:30",
  "lat": 6.316541,
  "lon": 3.607089,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1933-11-14",
  "time": "05:44",
  "lat": 12.362999,
  "lon": -86.340848,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1949-07-16",
  "time": "01:56",
  "lat": 16.619832,
  "lon": 95.955334,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1960-04-04",
  "time": "23:43",
  "lat": -3.598255,
  "lon": -38.321553,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1985-04-14",
  "time": "12:57",
  "lat": 50.937577,
  "lon": 4.409042,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2021-08-22",
  "time": "14:48",
  "lat": 30.671478,
  "lon": 104.288802,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1997-04-12",
  "time": "11:22",
  "lat": 37.398209,
  "lon": 127.218738,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1977-10-20",
  "time": "21:35",
  "lat": 40.198661,
  "lon": -3.696644,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2007-12-03",
  "time": "14:37",
  "lat": 59.340168,
  "lon": 18.303792,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1969-12-07",
  "time": "07:45",
  "lat": 22.591836,
  "lon": 88.472549,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1973-04-28",
  "time": "13:36",
  "lat": -12.818456,
  "lon": -38.62537,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2016-07-05",
  "time": "01:25",
  "lat": 11.021409,
  "lon": 106.597448,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1969-06-08",
  "time": "08:47",
  "lat": -3.099005,
  "lon": -60.000153,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1981-10-03",
  "time": "03:24",
  "lat": -6.034063,
  "lon": 106.724147,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1980-04-15",
  "time": "07:02",
  "lat": 52.48891,
  "lon": 4.702598,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1980-05-26",
  "time": "18:29",
  "lat": -3.062399,
  "lon": -60.007066,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1966-10-20",
  "time": "08:12",
  "lat": 29.532074,
  "lon": 48.147255,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1943-11-13",
  "time": "02:28",
  "lat": 40.583778,
  "lon": 49.65351,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2006-01-31",
  "time": "22:53",
  "lat": 17.150754,
  "lon": 78.499871,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1994-05-04",
  "time": "03:09",
  "lat": 28.757127,
  "lon": 77.447201,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1997-02-25",
  "time": "11:34",
  "lat": -8.712056,
  "lon": 13.352755,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1995-09-08",
  "time": "00:54",
  "lat": 59.770834,
  "lon": 30.438439,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2007-08-01",
  "time": "02:21",
  "lat": -29.688676,
  "lon": 31.051511,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2007-07-05",
  "time": "17:51",
  "lat": 30.395256,
  "lon": 104.180499,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1981-07-27",
  "time": "12:38",
  "lat": -25.620692,
  "lon": -49.275695,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1966-01-09",
  "time": "18:29",
  "lat": -26.302457,
  "lon": 28.213414,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2025-04-16",
  "time": "09:43",
  "lat": 48.305714,
  "lon": 16.166744,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1932-09-15",
  "time": "02:55",
  "lat": 5.413799,
  "lon": -4.168725,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1987-05-15",
  "time": "21:25",
  "lat": 55.76242,
  "lon": 37.78511,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2002-05-06",
  "time": "20:56",
  "lat": -34.9053,
  "lon": -56.32884,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1986-10-24",
  "time": "00:58",
  "lat": 55.534759,
  "lon": 37.465612,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1986-08-20",
  "time": "07:33",
  "lat": 51.016873,
  "lon": 4.573637,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1964-10-18",
  "time": "03:55",
  "lat": 17.775854,
  "lon": 102.569499,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2018-01-29",
  "time": "21:42",
  "lat": 37.700597,
  "lon": 127.164622,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1978-09-13",
  "time": "03:33",
  "lat": 41.50092,
  "lon": 44.945323,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1987-08-19",
  "time": "10:15",
  "lat": 36.57655,
  "lon": 3.004472,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1956-03-12",
  "time": "23:36",
  "lat": 43.099975,
  "lon": 76.845173,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1972-08-22",
  "time": "23:58",
  "lat": 30.660658,
  "lon": 114.199355,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2021-12-07",
  "time": "22:07",
  "lat": 32.040721,
  "lon": 35.845748,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1949-01-08",
  "time": "06:08",
  "lat": -25.267638,
  "lon": -57.349413,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1968-06-29",
  "time": "08:14",
  "lat": -0.311155,
  "lon": -78.488985,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1956-02-05",
  "time": "02:29",
  "lat": 27.963923,
  "lon": 85.301288,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2008-07-22",
  "time": "20:54",
  "lat": 35.900558,
  "lon": 139.935744,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2021-04-26",
  "time": "13:04",
  "lat": 60.162594,
  "lon": 25.012967,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2023-02-02",
  "time": "23:02",
  "lat": 40.422726,
  "lon": 49.969091,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1955-06-23",
  "time": "20:32",
  "lat": 33.811362,
  "lon": -7.626621,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1942-06-26",
  "time": "17:19",
  "lat": -35.005034,
  "lon": 138.736202,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1974-11-08",
  "time": "09:51",
  "lat": 52.169969,
  "lon": 21.004036,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1976-08-05",
  "time": "15:26",
  "lat": 11.403488,
  "lon": 105.000639,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1961-05-30",
  "time": "21:52",
  "lat": -25.153664,
  "lon": -57.797421,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2007-07-27",
  "time": "03:20",
  "lat": 45.381901,
  "lon": -73.722167,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1979-01-11",
  "time": "04:14",
  "lat": 25.229977,
  "lon": 51.738735,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1985-04-06",
  "time": "04:17",
  "lat": 30.42743,
  "lon": 104.054441,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1960-09-04",
  "time": "21:27",
  "lat": 23.164066,
  "lon": 113.311681,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1937-07-01",
  "time": "07:43",
  "lat": 18.577479,
  "lon": -70.039141,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2014-07-06",
  "time": "09:42",
  "lat": 34.98656,
  "lon": 129.106591,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2012-12-11",
  "time": "05:09",
  "lat": 13.620356,
  "lon": 100.376466,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1961-04-29",
  "time": "20:06",
  "lat": 31.81963,
  "lon": 35.975256,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2019-06-25",
  "time": "02:35",
  "lat": 19.550048,
  "lon": -99.279809,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1943-03-12",
  "time": "10:32",
  "lat": 19.109134,
  "lon": 72.744967,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1950-01-20",
  "time": "19:59",
  "lat": 19.261815,
  "lon": -99.120064,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2014-06-02",
  "time": "07:09",
  "lat": 10.285065,
  "lon": -66.704113,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1950-06-03",
  "time": "04:33",
  "lat": -12.797641,
  "lon": -38.65628,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1958-08-05",
  "time": "22:42",
  "lat": 22.814473,
  "lon": 120.356834,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1958-01-18",
  "time": "20:49",
  "lat": 23.105793,
  "lon": 113.330757,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1953-06-25",
  "time": "18:15",
  "lat": -22.705234,
  "lon": -43.009008,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1998-10-04",
  "time": "05:31",
  "lat": -7.3236,
  "lon": 112.991015,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1965-07-15",
  "time": "21:31",
  "lat": -8.116839,
  "lon": -34.775995,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1940-06-25",
  "time": "19:47",
  "lat": 60.13119,
  "lon": 30.184474,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1944-07-10",
  "time": "06:46",
  "lat": 55.712539,
  "lon": 12.59076,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1946-07-06",
  "time": "18:20",
  "lat": 13.060957,
  "lon": 80.210781,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1953-04-25",
  "time": "13:05",
  "lat": 14.60715,
  "lon": -17.567715,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1989-07-03",
  "time": "05:45",
  "lat": 13.855151,
  "lon": 100.290721,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1939-02-17",
  "time": "08:31",
  "lat": 22.33341,
  "lon": 113.954043,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1996-04-19",
  "time": "19:08",
  "lat": 59.337347,
  "lon": 17.90944,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1954-05-30",
  "time": "03:20",
  "lat": 52.248654,
  "lon": 20.960741,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2013-05-26",
  "time": "04:17",
  "lat": 29.424737,
  "lon": 47.964636,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2006-10-01",
  "time": "17:56",
  "lat": 35.393963,
  "lon": 128.950387,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2012-08-21",
  "time": "07:15",
  "lat": 43.054237,
  "lon": 141.363567,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2004-10-26",
  "time": "11:33",
  "lat": 55.76782,
  "lon": 37.402967,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1987-10-21",
  "time": "09:37",
  "lat": 51.622285,
  "lon": -0.369088,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1953-02-18",
  "time": "17:43",
  "lat": 10.710654,
  "lon": -67.119917,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1994-07-19",
  "time": "06:11",
  "lat": 53.348666,
  "lon": -7.859937,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2017-11-16",
  "time": "20:52",
  "lat": -37.957306,
  "lon": 145.031433,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1958-01-25",
  "time": "02:17",
  "lat": -30.003881,
  "lon": 30.877663,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2025-08-24",
  "time": "09:30",
  "lat": 49.00184,
  "lon": 2.319931,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1986-12-08",
  "time": "14:07",
  "lat": 40.431691,
  "lon": 50.075762,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1997-03-07",
  "time": "13:07",
  "lat": -35.124792,
  "lon": -56.029529,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1970-08-12",
  "time": "14:56",
  "lat": 10.494622,
  "lon": 123.979304,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1993-10-26",
  "time": "05:30",
  "lat": -34.014119,
  "lon": 151.317652,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1977-08-05",
  "time": "16:24",
  "lat": 8.930817,
  "lon": 38.610669,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2000-08-09",
  "time": "17:29",
  "lat": 50.676193,
  "lon": 4.120095,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1981-02-07",
  "time": "15:51",
  "lat": 44.248153,
  "lon": 26.137716,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1969-02-22",
  "time": "16:40",
  "lat": 24.486967,
  "lon": 46.645651,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1972-01-19",
  "time": "17:38",
  "lat": 38.140718,
  "lon": 58.120848,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1946-01-05",
  "time": "22:50",
  "lat": 13.676546,
  "lon": 100.647469,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2016-08-16",
  "time": "08:43",
  "lat": 55.868075,
  "lon": 12.467478,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2016-12-05",
  "time": "14:31",
  "lat": 18.15324,
  "lon": 102.42238,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2020-04-14",
  "time": "12:54",
  "lat": -11.980402,
  "lon": -76.991324,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1970-07-30",
  "time": "18:34",
  "lat": 19.229098,
  "lon": 72.918996,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2006-11-25",
  "time": "22:27",
  "lat": 52.038044,
  "lon": 21.05494,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1959-03-14",
  "time": "12:16",
  "lat": -6.004984,
  "lon": 106.923494,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2014-09-08",
  "time": "18:34",
  "lat": 60.187887,
  "lon": 24.715098,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1938-12-28",
  "time": "14:40",
  "lat": 17.312188,
  "lon": 78.455766,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1988-12-07",
  "time": "20:18",
  "lat": 22.535508,
  "lon": 114.353965,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1943-11-04",
  "time": "04:22",
  "lat": 13.029983,
  "lon": 77.842466,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1987-02-01",
  "time": "09:11",
  "lat": 41.059858,
  "lon": 28.860387,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1959-07-06",
  "time": "22:09",
  "lat": 19.419385,
  "lon": -99.209922,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1984-09-12",
  "time": "16:21",
  "lat": 36.942948,
  "lon": 3.242488,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1963-12-31",
  "time": "19:10",
  "lat": 23.103456,
  "lon": 113.416929,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1993-11-10",
  "time": "04:21",
  "lat": 3.505203,
  "lon": -76.775797,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2024-11-17",
  "time": "23:18",
  "lat": 44.759834,
  "lon": 20.604465,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1988-01-23",
  "time": "19:24",
  "lat": -4.454105,
  "lon": 15.098835,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1954-12-03",
  "time": "10:04",
  "lat": -13.178104,
  "lon": -38.499266,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2022-10-25",
  "time": "21:29",
  "lat": 17.384799,
  "lon": 78.467635,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1973-01-19",
  "time": "21:50",
  "lat": 31.534012,
  "lon": 74.285422,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2020-05-26",
  "time": "03:08",
  "lat": 35.829943,
  "lon": 139.865088,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1954-07-15",
  "time": "01:43",
  "lat": 17.811609,
  "lon": 102.835163,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1955-11-04",
  "time": "17:56",
  "lat": 18.802309,
  "lon": -72.554018,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1934-06-16",
  "time": "19:28",
  "lat": 22.517593,
  "lon": 114.183079,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1943-08-09",
  "time": "22:18",
  "lat": -12.862222,
  "lon": -38.439568,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1948-04-05",
  "time": "01:21",
  "lat": 47.55434,
  "lon": 18.994636,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2007-12-19",
  "time": "01:12",
  "lat": 31.268369,
  "lon": 121.537522,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1938-02-16",
  "time": "17:11",
  "lat": 24.749032,
  "lon": 67.237721,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1995-03-12",
  "time": "06:44",
  "lat": 40.508481,
  "lon": -3.686392,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1984-10-04",
  "time": "00:17",
  "lat": 43.24989,
  "lon": 141.188985,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2010-11-12",
  "time": "13:28",
  "lat": 23.930122,
  "lon": 90.545644,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1956-04-07",
  "time": "17:29",
  "lat": 31.783693,
  "lon": 35.300581,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2005-11-16",
  "time": "00:10",
  "lat": 40.982864,
  "lon": 29.249995,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1988-04-29",
  "time": "19:29",
  "lat": 18.362595,
  "lon": -72.134129,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1963-01-26",
  "time": "09:38",
  "lat": 5.711616,
  "lon": -0.288209,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1960-05-27",
  "time": "18:23",
  "lat": -25.106688,
  "lon": -57.364746,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2012-12-03",
  "time": "08:40",
  "lat": 60.355198,
  "lon": 24.710511,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1950-03-17",
  "time": "11:43",
  "lat": 23.15394,
  "lon": -82.45639,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2019-01-25",
  "time": "00:41",
  "lat": 6.551343,
  "lon": 3.187119,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1974-02-06",
  "time": "07:39",
  "lat": 45.358561,
  "lon": -73.343169,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1964-05-23",
  "time": "12:53",
  "lat": 48.081062,
  "lon": 16.465693,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1991-04-06",
  "time": "11:03",
  "lat": 55.861793,
  "lon": -4.254214,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1987-12-23",
  "time": "05:20",
  "lat": 10.787876,
  "lon": 106.698615,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1952-05-27",
  "time": "00:08",
  "lat": 55.560438,
  "lon": 12.373531,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1999-05-04",
  "time": "16:54",
  "lat": 41.685424,
  "lon": -87.876781,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1939-05-18",
  "time": "12:36",
  "lat": 32.168124,
  "lon": 35.696166,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1931-12-18",
  "time": "20:15",
  "lat": 16.780744,
  "lon": 96.383864,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1956-11-07",
  "time": "00:12",
  "lat": 27.934861,
  "lon": 85.107122,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2023-07-25",
  "time": "20:56",
  "lat": -33.836698,
  "lon": 151.024032,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2016-04-30",
  "time": "11:03",
  "lat": -26.242937,
  "lon": 27.939293,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1966-03-24",
  "time": "23:40",
  "lat": 59.158256,
  "lon": 17.975058,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1935-05-24",
  "time": "04:54",
  "lat": 6.96883,
  "lon": 80.033357,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1971-07-04",
  "time": "06:28",
  "lat": 23.345376,
  "lon": 113.129057,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1982-07-27",
  "time": "02:48",
  "lat": 30.664155,
  "lon": 104.233146,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1950-12-22",
  "time": "05:38",
  "lat": 22.20565,
  "lon": 114.089735,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1969-12-04",
  "time": "16:54",
  "lat": 52.33207,
  "lon": 4.848411,
  "country": "",
  "state": ""
}
'''
    
    # Configuration
    supabase_config = "supabase_config.py"
    
    # Check if Supabase config exists
    if not os.path.exists(supabase_config):
        print(f"❌ Supabase config file not found: {supabase_config}")
        print("Please create the config file or update the path")
        sys.exit(1)
    
    # Create processor
    processor = SupabaseBatchProcessor(supabase_config)
    
    # Process the batch
    try:
        result = processor.process_batch(profiles_input)
        
        if result['success']:
            print(f"\n🎉 Batch processing completed successfully!")
            print(f"📊 Processed {result['total_profiles']} profiles")
            print(f"✅ {result['successful_analyses']} successful analyses")
            print(f"❌ {result['failed_analyses']} failed analyses")
            print(f"🎯 Found {result['unique_animals']} unique animals")
        else:
            print(f"\n❌ Batch processing failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Batch processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error during batch processing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()