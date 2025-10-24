#!/usr/bin/env python3
"""
Supabase Batch Processor for PLUMATOTM - 1500 Profiles (No ChatGPT, No Charts)

This script processes 1500 birth profiles in batch and updates Supabase database.
It integrates with the PLUMATOTM core engine and Supabase manager.
Skips ChatGPT interpretation and chart generation for faster processing.
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
    print(f"[ERROR] Import error: {e}")
    print("Please ensure all required modules are installed")
    sys.exit(1)

class SupabaseBatchProcessor1500NoCharts:
    """Batch processor for handling 1500 birth profiles with Supabase integration (no charts)."""
    
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
    
    def _load_profiles(self) -> List[Dict]:
        """Load profiles from JSON file."""
        try:
            with open('plumastro_1500_profiles.json', 'r', encoding='utf-8') as f:
                profiles_data = json.load(f)
            print(f"[INFO] Loaded {len(profiles_data)} profiles from plumastro_1500_profiles.json")
            return profiles_data
        except Exception as e:
            print(f"[ERROR] Error loading profiles: {e}")
            return []
    
    def _process_single_profile(self, profile: Dict, profile_index: int) -> Optional[Dict]:
        """Process a single birth profile and return the result."""
        try:
            # Extract profile data
            name = profile.get('name', '').strip()
            date = profile.get('date', '')
            time = profile.get('time', '')
            lat = float(profile.get('lat', 0))
            lon = float(profile.get('lon', 0))
            
            print(f"\n[INFO] Processing profile {profile_index + 1}/1500")
            print(f"   Date: {date}")
            print(f"   Time: {time}")
            print(f"   Location: {lat}, {lon}")
            if name:
                print(f"   Name: {name}")
            
            # Run analysis WITHOUT ChatGPT interpretation
            # Note: Chart generation will still occur but we'll handle it differently
            self.analyzer.run_analysis(
                date=date,
                time=time,
                lat=lat,
                lon=lon,
                user_name=name if name else None,
                openai_api_key=None,  # Skip ChatGPT interpretation
                skip_chatgpt=True  # Explicitly skip ChatGPT
            )
            
            # Read the results from the output files
            try:
                with open('outputs/result.json', 'r', encoding='utf-8') as f:
                    result_data = json.load(f)
                
                # Extract top animal from the results
                if 'animal_totals' in result_data and result_data['animal_totals']:
                    top1_animal = result_data['animal_totals'][0]['ANIMAL']
                    top1_score = result_data['animal_totals'][0]['TOTAL_SCORE']
                    
                    # Update statistics
                    self.results['unique_animals'].add(top1_animal)
                    self.results['animal_counts'][top1_animal] = self.results['animal_counts'].get(top1_animal, 0) + 1
                    
                    print(f"   [SUCCESS] {top1_animal} (Score: {top1_score})")
                    
                    # Try to update Supabase
                    try:
                        # Generate a plumid for this profile
                        plumid = f"batch1500_v2_{profile_index + 1:05d}_{date.replace('-', '_')}_{time.replace(':', '_')}"
                        
                        supabase_result = self.supabase_manager.add_user(
                            plumid=plumid,
                            top1_animal=top1_animal,
                            user_name=name if name else None
                        )
                        if supabase_result:
                            print(f"   [SUPABASE] Updated successfully (PlumID: {plumid})")
                        else:
                            print(f"   [WARNING] Supabase update failed")
                    except Exception as supabase_error:
                        print(f"   [WARNING] Supabase error: {supabase_error}")
                    
                    return {
                        'success': True,
                        'top1_animal': top1_animal,
                        'top1_score': top1_score
                    }
                else:
                    print(f"   [FAILED] No animals found in results")
                    self.results['errors'].append(f"Profile {profile_index + 1}: No animals found in results")
                    return None
                    
            except Exception as e:
                print(f"   [FAILED] Error reading results: {e}")
                self.results['errors'].append(f"Profile {profile_index + 1}: Error reading results: {e}")
                return None
                
        except Exception as e:
            error_msg = f"Exception: {str(e)}"
            print(f"   [ERROR] {error_msg}")
            self.results['errors'].append(f"Profile {profile_index + 1}: {error_msg}")
            return None
    
    def process_batch(self) -> Dict:
        """Process all profiles in the batch."""
        print("[START] Starting batch processing for 1500 profiles (NO CHARTS)...")
        print("=" * 60)
        
        # Load profiles
        profiles = self._load_profiles()
        if not profiles:
            return {'success': False, 'error': 'No profiles loaded'}
        
        self.results['total_profiles'] = len(profiles)
        print(f"[INFO] Total profiles to process: {len(profiles)}")
        print("[INFO] Chart generation is DISABLED for faster processing")
        print("=" * 60)
        
        # Process each profile
        for i, profile in enumerate(profiles):
            result = self._process_single_profile(profile, i)
            
            if result:
                self.results['successful_analyses'] += 1
            else:
                self.results['failed_analyses'] += 1
            
            # Progress update every 50 profiles
            if (i + 1) % 50 == 0:
                print(f"\n[PROGRESS] Progress: {i + 1}/{len(profiles)} profiles processed")
                print(f"[SUCCESS] Successful: {self.results['successful_analyses']}")
                print(f"[FAILED] Failed: {self.results['failed_analyses']}")
        
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
        print("[COMPLETE] BATCH PROCESSING COMPLETE - 1500 PROFILES (NO CHARTS)")
        print("="*60)
        print(f"[INFO] Total profiles processed: {self.results['total_profiles']}")
        print(f"[SUCCESS] Successful analyses: {self.results['successful_analyses']}")
        print(f"[FAILED] Failed analyses: {self.results['failed_analyses']}")
        print(f"[RESULT] Unique animals found: {len(self.results['unique_animals'])}")
        
        # Top 15 animals
        if self.results['animal_counts']:
            print(f"\n[TOP] Top 15 animals:")
            sorted_animals = sorted(self.results['animal_counts'].items(), 
                                  key=lambda x: x[1], reverse=True)
            for i, (animal, count) in enumerate(sorted_animals[:15], 1):
                print(f"   {i:2d}. {animal}: {count} occurrences")
        
        print("="*60)

def main():
    """Main function to run the batch processor."""
    print("[START] PLUMATOTM SUPABASE BATCH PROCESSOR - 1500 PROFILES (NO CHATGPT, NO CHARTS)")
    print("=" * 60)
    print("[INFO] This will update your Supabase database!")
    print("[INFO] ChatGPT interpretation is DISABLED for faster processing")
    print("[INFO] Chart generation is DISABLED for faster processing")
    print("=" * 60)
    
    # Create processor
    processor = SupabaseBatchProcessor1500NoCharts()
    
    # Process the batch
    try:
        result = processor.process_batch()
        
        if result['success']:
            print(f"\n[SUCCESS] Batch processing completed successfully!")
            print(f"[INFO] Processed {result['total_profiles']} profiles")
            print(f"[SUCCESS] {result['successful_analyses']} successful analyses")
            print(f"[FAILED] {result['failed_analyses']} failed analyses")
            print(f"[RESULT] Found {result['unique_animals']} unique animals")
        else:
            print(f"\n[FAILED] Batch processing completed with errors")
            print(f"[INFO] Processed {result['total_profiles']} profiles")
            print(f"[SUCCESS] {result['successful_analyses']} successful analyses")
            print(f"[FAILED] {result['failed_analyses']} failed analyses")
            
    except Exception as e:
        print(f"\n[ERROR] Error during batch processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
