#!/usr/bin/env python3
"""
Simple batch processor that continues from profile 320 without file generation
"""

import json
import os
import sys
import time
from typing import Dict, List
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from plumatotm_core import BirthChartAnalyzer
    from supabase_manager import SupabaseManager
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

class SimpleBatchProcessor:
    """Simple batch processor without file generation."""
    
    def __init__(self, start_index: int = 319):
        """Initialize starting from profile 320 (index 319)."""
        self.start_index = start_index
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
            'animal_counts': {},
            'errors': []
        }
        self.processed_profiles = []
    
    def _load_profiles(self) -> List[Dict]:
        """Load profiles from JSON file."""
        try:
            with open('plumastro_1000_profiles.json', 'r', encoding='utf-8') as f:
                profiles_data = json.load(f)
            print(f"📊 Loaded {len(profiles_data)} profiles from plumastro_1000_profiles.json")
            return profiles_data
        except Exception as e:
            print(f"❌ Error loading profiles: {e}")
            return []
    
    def _analyze_profile(self, profile: Dict, profile_index: int) -> Dict:
        """Analyze a single profile and return results."""
        try:
            # Extract profile data
            name = profile.get('name', '').strip()
            date = profile.get('date', '')
            time_str = profile.get('time', '')
            lat = float(profile.get('lat', 0))
            lon = float(profile.get('lon', 0))
            
            print(f"\n📊 Processing profile {profile_index + 1}/1000")
            print(f"   📅 Date: {date}")
            print(f"   🕐 Time: {time_str}")
            print(f"   📍 Location: {lat}, {lon}")
            if name:
                print(f"   👤 Name: {name}")
            
            # Calculate birth chart directly
            birth_chart_data = self.analyzer.compute_birth_chart(
                date=date,
                time=time_str,
                lat=lat,
                lon=lon
            )
            
            if not birth_chart_data:
                raise Exception("Failed to compute birth chart")
            
            birth_chart, planet_houses, animal_scores = birth_chart_data
            
            # Calculate dynamic weights
            dynamic_weights = self.analyzer.compute_dynamic_planet_weights(birth_chart)
            
            # Calculate raw scores
            raw_scores_data = self.analyzer.compute_raw_scores(birth_chart)
            
            # Calculate weighted scores
            weighted_scores_data = self.analyzer.compute_weighted_scores(raw_scores_data, dynamic_weights)
            
            # Calculate animal totals
            animal_totals = self.analyzer.compute_animal_totals(weighted_scores_data)
            
            if not animal_totals:
                raise Exception("No animal totals calculated")
            
            # Get top animal
            top_animal = animal_totals[0][0]
            top_score = animal_totals[0][1]
            
            # Create result
            result = {
                'profile_index': profile_index + 1,
                'name': name,
                'date': date,
                'time': time_str,
                'lat': lat,
                'lon': lon,
                'top1_animal': top_animal,
                'top1_score': top_score,
                'success': True,
                'processed_at': datetime.now().isoformat()
            }
            
            print(f"   🎯 Result: {top_animal} (Score: {top_score:.2f})")
            
            return result
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return {
                'profile_index': profile_index + 1,
                'name': profile.get('name', ''),
                'date': profile.get('date', ''),
                'time': profile.get('time', ''),
                'lat': float(profile.get('lat', 0)),
                'lon': float(profile.get('lon', 0)),
                'top1_animal': 'Unknown',
                'top1_score': 0,
                'success': False,
                'error': str(e),
                'processed_at': datetime.now().isoformat()
            }
    
    def run_batch(self):
        """Run the batch processing from the specified start index."""
        print(f"🚀 Starting simple batch processing from profile {self.start_index + 1}")
        print("=" * 60)
        
        # Load profiles
        profiles = self._load_profiles()
        if not profiles:
            print("❌ No profiles loaded. Exiting.")
            return
        
        remaining_profiles = profiles[self.start_index:]
        self.results['total_profiles'] = len(remaining_profiles)
        
        print(f"📊 Processing {len(remaining_profiles)} profiles (from {self.start_index + 1} to {len(profiles)})")
        
        start_time = time.time()
        
        # Process profiles one by one
        for i, profile in enumerate(remaining_profiles):
            profile_index = self.start_index + i
            
            # Analyze profile
            result = self._analyze_profile(profile, profile_index)
            self.processed_profiles.append(result)
            
            if result['success']:
                self.results['successful_analyses'] += 1
                animal = result['top1_animal']
                self.results['animal_counts'][animal] = self.results['animal_counts'].get(animal, 0) + 1
                
                # Try to update Supabase
                try:
                    # Generate a plumid for this profile
                    plumid = f"batch_{result['profile_index']:04d}_{result['date'].replace('-', '_')}_{result['time'].replace(':', '_')}"
                    
                    supabase_result = self.supabase_manager.add_user(
                        plumid=plumid,
                        top1_animal=result['top1_animal'],
                        user_name=result['name'] if result['name'] else None
                    )
                    if supabase_result:
                        print(f"   ✅ Supabase updated successfully (PlumID: {plumid})")
                    else:
                        print(f"   ⚠️  Supabase update failed")
                except Exception as supabase_error:
                    print(f"   ⚠️  Supabase error: {supabase_error}")
            else:
                self.results['failed_analyses'] += 1
                self.results['errors'].append(f"Profile {profile_index + 1}: {result.get('error', 'Unknown error')}")
            
            # Progress update every 10 profiles
            if (i + 1) % 10 == 0:
                elapsed_time = time.time() - start_time
                processed_count = len(self.processed_profiles)
                remaining_count = len(remaining_profiles) - processed_count
                
                print(f"\n📈 Progress: {processed_count}/{len(remaining_profiles)} profiles processed")
                print(f"⏱️  Elapsed time: {elapsed_time/60:.1f} minutes")
                if remaining_count > 0 and processed_count > 0:
                    avg_time_per_profile = elapsed_time / processed_count
                    estimated_remaining = avg_time_per_profile * remaining_count
                    print(f"⏳ Estimated remaining time: {estimated_remaining/60:.1f} minutes")
                
                # Save intermediate results
                self._save_results()
        
        # Final results
        self._print_final_results()
        self._save_results()
    
    def _save_results(self):
        """Save results to JSON file."""
        try:
            results_data = {
                'processed_profiles': self.processed_profiles,
                'statistics': {
                    'total_profiles': self.results['total_profiles'],
                    'successful_analyses': self.results['successful_analyses'],
                    'failed_analyses': self.results['failed_analyses'],
                    'animal_counts': dict(self.results['animal_counts'])
                },
                'errors': self.results['errors'][-20:],  # Last 20 errors
                'last_updated': datetime.now().isoformat()
            }
            
            with open('outputs/supabase_batch_results_simple.json', 'w', encoding='utf-8') as f:
                json.dump(results_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"⚠️  Error saving results: {e}")
    
    def _print_final_results(self):
        """Print final processing results."""
        print("\n" + "=" * 60)
        print("🏁 BATCH PROCESSING COMPLETED")
        print("=" * 60)
        print(f"📊 Total profiles processed: {self.results['total_profiles']}")
        print(f"✅ Successful analyses: {self.results['successful_analyses']}")
        print(f"❌ Failed analyses: {self.results['failed_analyses']}")
        
        if self.results['animal_counts']:
            print(f"\n🐾 Top 10 most common animals:")
            sorted_animals = sorted(self.results['animal_counts'].items(), key=lambda x: x[1], reverse=True)
            for i, (animal, count) in enumerate(sorted_animals[:10]):
                print(f"  {i+1:2d}. {animal:20s}: {count:3d} profiles")

def main():
    """Main function."""
    processor = SimpleBatchProcessor(start_index=319)
    processor.run_batch()

if __name__ == "__main__":
    main()
