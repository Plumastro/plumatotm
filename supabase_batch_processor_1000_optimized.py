#!/usr/bin/env python3
"""
Supabase Batch Processor for PLUMATOTM - 1000 Profiles (Optimized)

This script processes 1000 birth profiles in batch and updates Supabase database.
It processes profiles in smaller chunks to avoid memory issues and provides better progress tracking.
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

class OptimizedSupabaseBatchProcessor:
    """Optimized batch processor for handling multiple birth profiles with Supabase integration."""
    
    def __init__(self, chunk_size: int = 50):
        """Initialize the batch processor with chunk size for processing."""
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
                        'profile_id': profile_index + 1,
                        'name': name,
                        'date': date,
                        'time': time_str,
                        'lat': lat,
                        'lon': lon,
                        'country': profile.get('country', ''),
                        'state': profile.get('state', ''),
                        'top1_animal_en': top1_animal,
                        'top1_animal_fr': result.get('top1_animal_fr', top1_animal),
                        'top1_score': score,
                        'analysis_successful': True,
                        'error': None,
                        'timestamp': datetime.now().isoformat(),
                        'plumid': result.get('plumid', f"{date}_{time_str}_{lat}_{lon}")
                    }
                    
                    chunk_results.append(profile_result)
                    self.results['successful_analyses'] += 1
                    
                    print(f"   ✅ SUCCESS: {top1_animal} (Score: {score})")
                else:
                    error_msg = result.get('error', 'Unknown error') if result else 'No result returned'
                    profile_result = {
                        'profile_id': profile_index + 1,
                        'name': name,
                        'date': date,
                        'time': time_str,
                        'lat': lat,
                        'lon': lon,
                        'country': profile.get('country', ''),
                        'state': profile.get('state', ''),
                        'top1_animal_en': 'Unknown',
                        'top1_animal_fr': 'Inconnu',
                        'top1_score': 0,
                        'analysis_successful': False,
                        'error': error_msg,
                        'timestamp': datetime.now().isoformat(),
                        'plumid': f"{date}_{time_str}_{lat}_{lon}"
                    }
                    
                    chunk_results.append(profile_result)
                    self.results['failed_analyses'] += 1
                    self.results['errors'].append(f"Profile {profile_index + 1}: {error_msg}")
                    
                    print(f"   ❌ FAILED: {error_msg}")
                    
            except Exception as e:
                error_msg = f"Exception: {str(e)}"
                profile_result = {
                    'profile_id': profile_index + 1,
                    'name': profile.get('name', ''),
                    'date': profile.get('date', ''),
                    'time': profile.get('time', ''),
                    'lat': profile.get('lat', 0),
                    'lon': profile.get('lon', 0),
                    'country': profile.get('country', ''),
                    'state': profile.get('state', ''),
                    'top1_animal_en': 'Unknown',
                    'top1_animal_fr': 'Inconnu',
                    'top1_score': 0,
                    'analysis_successful': False,
                    'error': error_msg,
                    'timestamp': datetime.now().isoformat(),
                    'plumid': f"{profile.get('date', '')}_{profile.get('time', '')}_{profile.get('lat', 0)}_{profile.get('lon', 0)}"
                }
                
                chunk_results.append(profile_result)
                self.results['failed_analyses'] += 1
                self.results['errors'].append(f"Profile {profile_index + 1}: {error_msg}")
                
                print(f"   ❌ ERROR: {error_msg}")
        
        return chunk_results
    
    def _save_results(self, results: List[Dict]):
        """Save results to files."""
        # Save JSON results
        with open('outputs/supabase_batch_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Save CSV summary
        if results:
            import csv
            with open('outputs/supabase_batch_summary.csv', 'w', newline='', encoding='utf-8') as f:
                if results:
                    writer = csv.DictWriter(f, fieldnames=results[0].keys())
                    writer.writeheader()
                    writer.writerows(results)
        
        print(f"💾 Results saved: {len(results)} profiles")
    
    def process_batch(self) -> Dict:
        """Process all profiles in the batch using chunks."""
        print("🚀 Starting optimized batch processing...")
        print("=" * 60)
        
        # Load profiles
        profiles = self._load_profiles()
        if not profiles:
            return {'success': False, 'error': 'No profiles loaded'}
        
        self.results['total_profiles'] = len(profiles)
        print(f"📋 Total profiles to process: {len(profiles)}")
        print(f"📦 Processing in chunks of {self.chunk_size} profiles")
        print("=" * 60)
        
        all_results = []
        start_time = datetime.now()
        
        # Process profiles in chunks
        for i in range(0, len(profiles), self.chunk_size):
            chunk = profiles[i:i + self.chunk_size]
            chunk_number = (i // self.chunk_size) + 1
            total_chunks = (len(profiles) + self.chunk_size - 1) // self.chunk_size
            
            print(f"\n🔄 Processing chunk {chunk_number}/{total_chunks} (profiles {i+1}-{min(i+self.chunk_size, len(profiles))})")
            
            # Process chunk
            chunk_results = self._process_chunk(chunk, i)
            all_results.extend(chunk_results)
            
            # Save intermediate results
            self._save_results(all_results)
            
            # Print progress
            progress_percent = (len(all_results) / len(profiles)) * 100
            elapsed_time = datetime.now() - start_time
            print(f"📊 Progress: {len(all_results)}/{len(profiles)} ({progress_percent:.1f}%) | Elapsed: {elapsed_time}")
            
            # Small delay between chunks to avoid overwhelming the system
            if i + self.chunk_size < len(profiles):
                print("⏳ Waiting 2 seconds before next chunk...")
                time.sleep(2)
        
        # Final save
        self._save_results(all_results)
        
        # Print final summary
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
    """Main function to run the optimized batch processor."""
    print("🚀 PLUMATOTM SUPABASE BATCH PROCESSOR - 1000 PROFILES (OPTIMIZED)")
    print("=" * 60)
    print("🌐 This will update your Supabase database!")
    print("⚠️  ChatGPT interpretation is DISABLED for faster processing")
    print("📦 Processing in chunks of 50 profiles for better stability")
    print("=" * 60)
    
    # Create processor
    processor = OptimizedSupabaseBatchProcessor(chunk_size=50)
    
    # Process the batch
    try:
        result = processor.process_batch()
        
        if result['success']:
            print(f"\n🎉 Batch processing completed successfully!")
            print(f"📊 Processed {result['total_profiles']} profiles")
            print(f"✅ {result['successful_analyses']} successful analyses")
            print(f"❌ {result['failed_analyses']} failed analyses")
            print(f"🎯 Found {result['unique_animals']} unique animals")
        else:
            print(f"\n❌ Batch processing completed with errors")
            print(f"📊 Processed {result['total_profiles']} profiles")
            print(f"✅ {result['successful_analyses']} successful analyses")
            print(f"❌ {result['failed_analyses']} failed analyses")
            
    except Exception as e:
        print(f"\n❌ Error during batch processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
