#!/usr/bin/env python3
"""
Continue batch processing from profile 320
"""

import json
import os
import sys
import time
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

class ContinueBatchProcessor:
    """Continue batch processing from a specific profile index."""
    
    def __init__(self, start_index: int = 320, chunk_size: int = 50):
        """Initialize the batch processor starting from a specific index."""
        self.start_index = start_index
        self.chunk_size = chunk_size
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
    
    def _process_chunk(self, profiles_chunk: List[Dict], start_index: int) -> List[Dict]:
        """Process a chunk of profiles."""
        chunk_results = []
        
        for i, profile in enumerate(profiles_chunk):
            profile_index = start_index + i
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
                
                # Run analysis WITHOUT ChatGPT interpretation
                result = self.analyzer.run_analysis(
                    date=date,
                    time=time_str,
                    lat=lat,
                    lon=lon,
                    user_name=name if name else None,
                    openai_api_key=None  # Skip ChatGPT interpretation
                )
                
                if result and result.get('success'):
                    top1_animal = result.get('top1_animal', 'Unknown')
                    score = result.get('top1_score', 0)
                    
                    # Update statistics
                    self.results['unique_animals'].add(top1_animal)
                    self.results['animal_counts'][top1_animal] = self.results['animal_counts'].get(top1_animal, 0) + 1
                    
                    # Create result record
                    profile_result = {
                        'profile_index': profile_index + 1,
                        'name': name,
                        'date': date,
                        'time': time_str,
                        'lat': lat,
                        'lon': lon,
                        'top1_animal': top1_animal,
                        'top1_score': score,
                        'success': True,
                        'processed_at': datetime.now().isoformat()
                    }
                    
                    # Try to update Supabase
                    try:
                        supabase_result = self.supabase_manager.insert_or_update_profile(
                            profile_result['profile_index'],
                            name,
                            date,
                            time_str,
                            lat,
                            lon,
                            top1_animal,
                            score
                        )
                        if supabase_result:
                            print(f"   ✅ Supabase updated successfully")
                        else:
                            print(f"   ⚠️  Supabase update failed, but analysis succeeded")
                    except Exception as supabase_error:
                        print(f"   ⚠️  Supabase error: {supabase_error}")
                    
                    chunk_results.append(profile_result)
                    self.results['successful_analyses'] += 1
                    
                    print(f"   🎯 Result: {top1_animal} (Score: {score:.2f})")
                    
                else:
                    print(f"   ❌ Analysis failed")
                    self.results['failed_analyses'] += 1
                    self.results['errors'].append(f"Profile {profile_index + 1}: Analysis failed")
                
            except Exception as e:
                print(f"   ❌ Error processing profile {profile_index + 1}: {e}")
                self.results['failed_analyses'] += 1
                self.results['errors'].append(f"Profile {profile_index + 1}: {str(e)}")
        
        return chunk_results
    
    def run_batch(self):
        """Run the batch processing from the specified start index."""
        print(f"🚀 Starting batch processing from profile {self.start_index + 1}")
        print(f"📦 Chunk size: {self.chunk_size}")
        print("=" * 60)
        
        # Load profiles
        profiles = self._load_profiles()
        if not profiles:
            print("❌ No profiles loaded. Exiting.")
            return
        
        total_profiles = len(profiles)
        remaining_profiles = profiles[self.start_index:]
        self.results['total_profiles'] = len(remaining_profiles)
        
        print(f"📊 Processing {len(remaining_profiles)} profiles (from {self.start_index + 1} to {total_profiles})")
        
        # Process in chunks
        start_time = time.time()
        
        for i in range(0, len(remaining_profiles), self.chunk_size):
            chunk = remaining_profiles[i:i + self.chunk_size]
            chunk_start_index = self.start_index + i
            
            print(f"\n🔄 Processing chunk {i//self.chunk_size + 1} (profiles {chunk_start_index + 1}-{chunk_start_index + len(chunk)})")
            
            chunk_results = self._process_chunk(chunk, chunk_start_index)
            self.processed_profiles.extend(chunk_results)
            
            # Save intermediate results
            self._save_intermediate_results()
            
            # Progress update
            processed_count = len(self.processed_profiles)
            remaining_count = len(remaining_profiles) - processed_count
            elapsed_time = time.time() - start_time
            
            print(f"\n📈 Progress: {processed_count}/{len(remaining_profiles)} profiles processed")
            print(f"⏱️  Elapsed time: {elapsed_time/60:.1f} minutes")
            if remaining_count > 0 and processed_count > 0:
                avg_time_per_profile = elapsed_time / processed_count
                estimated_remaining = avg_time_per_profile * remaining_count
                print(f"⏳ Estimated remaining time: {estimated_remaining/60:.1f} minutes")
        
        # Final results
        self._print_final_results()
        self._save_final_results()
    
    def _save_intermediate_results(self):
        """Save intermediate results to JSON file."""
        try:
            results_data = {
                'processed_profiles': self.processed_profiles,
                'statistics': {
                    'total_profiles': self.results['total_profiles'],
                    'successful_analyses': self.results['successful_analyses'],
                    'failed_analyses': self.results['failed_analyses'],
                    'unique_animals_count': len(self.results['unique_animals']),
                    'animal_counts': dict(self.results['animal_counts'])
                },
                'errors': self.results['errors'][-10:],  # Last 10 errors
                'last_updated': datetime.now().isoformat()
            }
            
            with open('outputs/supabase_batch_results_continued.json', 'w', encoding='utf-8') as f:
                json.dump(results_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"⚠️  Error saving intermediate results: {e}")
    
    def _save_final_results(self):
        """Save final results."""
        try:
            # Save detailed results
            with open('outputs/supabase_batch_results_continued.json', 'w', encoding='utf-8') as f:
                json.dump({
                    'processed_profiles': self.processed_profiles,
                    'statistics': {
                        'total_profiles': self.results['total_profiles'],
                        'successful_analyses': self.results['successful_analyses'],
                        'failed_analyses': self.results['failed_analyses'],
                        'unique_animals_count': len(self.results['unique_animals']),
                        'animal_counts': dict(self.results['animal_counts'])
                    },
                    'errors': self.results['errors'],
                    'completed_at': datetime.now().isoformat()
                }, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Final results saved to: outputs/supabase_batch_results_continued.json")
            
        except Exception as e:
            print(f"⚠️  Error saving final results: {e}")
    
    def _print_final_results(self):
        """Print final processing results."""
        print("\n" + "=" * 60)
        print("🏁 BATCH PROCESSING COMPLETED")
        print("=" * 60)
        print(f"📊 Total profiles processed: {self.results['total_profiles']}")
        print(f"✅ Successful analyses: {self.results['successful_analyses']}")
        print(f"❌ Failed analyses: {self.results['failed_analyses']}")
        print(f"🎯 Unique animals found: {len(self.results['unique_animals'])}")
        
        if self.results['animal_counts']:
            print(f"\n🐾 Top 10 most common animals:")
            sorted_animals = sorted(self.results['animal_counts'].items(), key=lambda x: x[1], reverse=True)
            for i, (animal, count) in enumerate(sorted_animals[:10]):
                print(f"  {i+1:2d}. {animal:20s}: {count:3d} profiles")

def main():
    """Main function."""
    # Start from profile 320 (index 319)
    processor = ContinueBatchProcessor(start_index=319, chunk_size=50)
    processor.run_batch()

if __name__ == "__main__":
    main()
