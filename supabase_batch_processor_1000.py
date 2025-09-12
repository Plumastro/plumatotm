#!/usr/bin/env python3
"""
Supabase Batch Processor for PLUMATOTM - 1000 Profiles

This script processes 1000 birth profiles in batch and updates Supabase database.
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
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure all required modules are installed")
    sys.exit(1)

class SupabaseBatchProcessor:
    """Batch processor for handling multiple birth profiles with Supabase integration."""
    
    def __init__(self):
        """Initialize the batch processor with Supabase configuration."""
        self.supabase_manager = SupabaseManager()
        self.analyzer = BirthChartAnalyzer(
            scores_csv_path="plumatotm_raw_scores_trad.csv",
            weights_csv_path="plumatotm_planets_weights.csv",
            multipliers_csv_path="plumatotm_planets_multiplier.csv"
        )
        self.results = {
            'total_profiles': 0,
            'successful_analyses': 0,
            'failed_analyses': 0,
            'unique_animals': set(),
            'animal_counts': {},
            'errors': []
        }
    
    def _parse_profiles_json(self, profiles_json: str) -> List[Dict]:
        """Parse the profiles JSON string into a list of profile dictionaries."""
        profiles = []
        lines = profiles_json.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if line:
                try:
                    profile = json.loads(line)
                    profiles.append(profile)
                except json.JSONDecodeError as e:
                    print(f"⚠️  Skipping invalid JSON line: {line[:50]}...")
                    continue
        
        return profiles
    
    def _process_single_profile(self, profile: Dict, profile_index: int) -> Optional[Dict]:
        """Process a single birth profile and return the result."""
        try:
            # Extract profile data
            name = profile.get('name', '').strip()
            date = profile.get('date', '')
            time = profile.get('time', '')
            lat = float(profile.get('lat', 0))
            lon = float(profile.get('lon', 0))
            
            print(f"\n📊 Processing profile {profile_index + 1}/1000")
            print(f"   📅 Date: {date}")
            print(f"   🕐 Time: {time}")
            print(f"   📍 Location: {lat}, {lon}")
            if name:
                print(f"   👤 Name: {name}")
            
            # Run analysis
            result = self.analyzer.run_analysis(
                date=date,
                time=time,
                lat=lat,
                lon=lon,
                user_name=name if name else None
            )
            
            if result and result.get('success'):
                top1_animal = result.get('top1_animal', 'Unknown')
                score = result.get('top1_score', 0)
                
                # Update statistics
                self.results['unique_animals'].add(top1_animal)
                self.results['animal_counts'][top1_animal] = self.results['animal_counts'].get(top1_animal, 0) + 1
                
                print(f"   ✅ SUCCESS: {top1_animal} (Score: {score})")
                return result
            else:
                error_msg = result.get('error', 'Unknown error') if result else 'No result returned'
                print(f"   ❌ FAILED: {error_msg}")
                self.results['errors'].append(f"Profile {profile_index + 1}: {error_msg}")
                return None
                
        except Exception as e:
            error_msg = f"Exception: {str(e)}"
            print(f"   ❌ ERROR: {error_msg}")
            self.results['errors'].append(f"Profile {profile_index + 1}: {error_msg}")
            return None
    
    def process_batch(self, profiles_json: str) -> Dict:
        """Process all profiles in the batch."""
        print("🚀 Starting batch processing...")
        print("=" * 60)
        
        # Parse profiles
        profiles = self._parse_profiles_json(profiles_json)
        self.results['total_profiles'] = len(profiles)
        
        print(f"📋 Total profiles to process: {len(profiles)}")
        print("=" * 60)
        
        # Process each profile
        for i, profile in enumerate(profiles):
            result = self._process_single_profile(profile, i)
            
            if result:
                self.results['successful_analyses'] += 1
            else:
                self.results['failed_analyses'] += 1
        
        # Print summary
        self._print_summary()
        
        return {
            'success': self.results['failed_analyses'] == 0,
            'total_profiles': self.results['total_profiles'],
            'successful_analyses': self.results['successful_analyses'],
            'failed_analyses': self.results['failed_analyses'],
            'unique_animals': len(self.results['unique_animals']),
            'animal_counts': self.results['animal_counts'],
            'errors': self.results['errors']
        }
    
    def _print_summary(self):
        """Print a summary of the batch processing results."""
        print("\n" + "="*60)
        print("📊 BATCH PROCESSING COMPLETE")
        print("="*60)
        print(f"📋 Total profiles processed: {self.results['total_profiles']}")
        print(f"✅ Successful analyses: {self.results['successful_analyses']}")
        print(f"❌ Failed analyses: {self.results['failed_analyses']}")
        print(f"🎯 Unique animals found: {len(self.results['unique_animals'])}")
        
        # Top 10 animals
        if self.results['animal_counts']:
            print(f"\n🏆 Top 10 animals:")
            sorted_animals = sorted(self.results['animal_counts'].items(), 
                                  key=lambda x: x[1], reverse=True)
            for i, (animal, count) in enumerate(sorted_animals[:10], 1):
                print(f"   {i:2d}. {animal}: {count} occurrences")
        
        print("="*60)

def main():
    """Main function to run the batch processor."""
    print("🚀 PLUMATOTM SUPABASE BATCH PROCESSOR - 1000 PROFILES")
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
    
    # Create processor
    processor = SupabaseBatchProcessor()
    
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
