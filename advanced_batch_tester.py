#!/usr/bin/env python3
"""
Advanced Batch Tester for PLUMATOTM Engine
Strategically generates profiles to maximize animal diversity in Supabase database
"""

import random
import json
import time
import csv
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Set
from plumatotm_core import BirthChartAnalyzer
import os

class AdvancedBatchTester:
    """Advanced batch tester with strategic animal targeting."""
    
    def __init__(self, 
                 scores_csv_path: str = "plumatotm_raw_scores_trad.csv",
                 weights_csv_path: str = "plumatotm_planets_weights.csv", 
                 multipliers_csv_path: str = "plumatotm_planets_multiplier.csv",
                 translations_csv_path: str = "plumatotm_raw_scores_trad.csv"):
        """Initialize the advanced batch tester."""
        self.analyzer = BirthChartAnalyzer(
            scores_csv_path=scores_csv_path,
            weights_csv_path=weights_csv_path,
            multipliers_csv_path=multipliers_csv_path,
            translations_csv_path=translations_csv_path
        )
        
        # Load all available animals
        self.analyzer._ensure_scores_data_loaded()
        self.analyzer._ensure_animal_translations_loaded()
        self.all_animals = self.analyzer.animals
        
        # Track which animals we've found
        self.found_animals = set()
        self.animal_profiles = {}  # animal -> list of profiles that produced it
        
        print(f"🎯 Advanced Batch Tester initialized with {len(self.all_animals)} animals")
    
    def get_current_database_animals(self) -> Set[str]:
        """Get animals already in the database (if Supabase is available)."""
        try:
            from supabase_manager import supabase_manager
            if supabase_manager.is_available():
                # Get existing animals from database
                existing_animals = supabase_manager.get_all_animals()
                print(f"📊 Found {len(existing_animals)} animals already in database")
                return set(existing_animals)
        except:
            pass
        
        return set()
    
    def generate_targeted_profiles(self, 
                                 target_animals: List[str] = None,
                                 avoid_animals: List[str] = None,
                                 count: int = 500,
                                 max_attempts_per_animal: int = 100) -> List[Dict]:
        """
        Generate profiles specifically targeting certain animals.
        
        Args:
            target_animals: List of animals to specifically target (None = all animals)
            avoid_animals: List of animals to avoid
            count: Total number of profiles to generate
            max_attempts_per_animal: Maximum attempts per animal before giving up
            
        Returns:
            List of birth data dictionaries
        """
        if target_animals is None:
            target_animals = self.all_animals.copy()
        
        if avoid_animals is None:
            avoid_animals = []
        
        # Remove animals we want to avoid
        target_animals = [a for a in target_animals if a not in avoid_animals]
        
        print(f"🎯 Targeting {len(target_animals)} animals")
        print(f"🚫 Avoiding {len(avoid_animals)} animals")
        
        profiles = []
        animal_attempts = {animal: 0 for animal in target_animals}
        
        # Strategic date/time combinations that might favor certain animals
        strategic_combinations = self._generate_strategic_combinations()
        
        attempts = 0
        max_total_attempts = count * 3  # Allow some failures
        
        while len(profiles) < count and attempts < max_total_attempts:
            attempts += 1
            
            # Choose a target animal (prioritize rare ones)
            available_targets = [a for a in target_animals if animal_attempts[a] < max_attempts_per_animal]
            
            if not available_targets:
                print("⚠️  All target animals have reached max attempts")
                break
            
            # Weight selection towards animals we haven't found yet
            if self.found_animals:
                unfound_animals = [a for a in available_targets if a not in self.found_animals]
                if unfound_animals:
                    target_animal = random.choice(unfound_animals)
                else:
                    # Choose from least attempted animals
                    target_animal = min(available_targets, key=lambda x: animal_attempts[x])
            else:
                target_animal = random.choice(available_targets)
            
            animal_attempts[target_animal] += 1
            
            # Generate profile with strategic parameters
            profile = self._generate_strategic_profile(target_animal, strategic_combinations)
            profiles.append(profile)
            
            # Progress reporting
            if attempts % 100 == 0:
                found_count = len(self.found_animals)
                print(f"📊 Attempts: {attempts} | Profiles: {len(profiles)} | Animals found: {found_count}/{len(target_animals)}")
        
        print(f"✅ Generated {len(profiles)} targeted profiles")
        return profiles
    
    def _generate_strategic_combinations(self) -> List[Dict]:
        """Generate strategic date/time combinations that might favor different animals."""
        combinations = []
        
        # Different seasons and times that might favor different animal types
        seasons = [
            {"months": [3, 4, 5], "name": "Spring"},
            {"months": [6, 7, 8], "name": "Summer"}, 
            {"months": [9, 10, 11], "name": "Autumn"},
            {"months": [12, 1, 2], "name": "Winter"}
        ]
        
        times = [
            {"hour_range": (0, 6), "name": "Night"},
            {"hour_range": (6, 12), "name": "Morning"},
            {"hour_range": (12, 18), "name": "Afternoon"},
            {"hour_range": (18, 24), "name": "Evening"}
        ]
        
        for season in seasons:
            for time_period in times:
                combinations.append({
                    "season": season,
                    "time_period": time_period,
                    "description": f"{season['name']} {time_period['name']}"
                })
        
        return combinations
    
    def _generate_strategic_profile(self, target_animal: str, combinations: List[Dict]) -> Dict:
        """Generate a profile with strategic parameters."""
        # Choose a strategic combination
        combination = random.choice(combinations)
        
        # Generate date in the chosen season
        year = random.randint(1960, 2005)
        month = random.choice(combination["season"]["months"])
        
        # Handle December for winter
        if month == 12:
            day = random.randint(1, 31)
        elif month in [1, 3, 5, 7, 8, 10]:
            day = random.randint(1, 31)
        elif month == 2:
            day = random.randint(1, 28)  # Simplified leap year handling
        else:
            day = random.randint(1, 30)
        
        birth_date = datetime(year, month, day)
        
        # Generate time in the chosen period
        start_hour, end_hour = combination["time_period"]["hour_range"]
        hour = random.randint(start_hour, end_hour - 1)
        minute = random.randint(0, 59)
        
        # Diverse locations
        locations = [
            # Arctic/Subarctic (might favor cold-weather animals)
            (78.2186, 15.6406, "Svalbard"),        # Arctic
            (64.1466, -21.9426, "Reykjavik"),      # Iceland
            (61.2181, -149.9003, "Anchorage"),     # Alaska
            
            # Tropical (might favor tropical animals)
            (1.3521, 103.8198, "Singapore"),       # Singapore
            (-8.6500, 115.2167, "Bali"),           # Bali
            (14.5995, 120.9842, "Manila"),         # Philippines
            
            # Desert (might favor desert animals)
            (24.7136, 46.6753, "Riyadh"),          # Saudi Arabia
            (25.2048, 55.2708, "Dubai"),           # UAE
            (30.0444, 31.2357, "Cairo"),           # Egypt
            
            # Oceanic (might favor marine animals)
            (-33.8688, 151.2093, "Sydney"),        # Sydney
            (-37.8136, 144.9631, "Melbourne"),     # Melbourne
            (21.3099, -157.8581, "Honolulu"),      # Hawaii
            
            # Mountain (might favor mountain animals)
            (46.5197, 6.6323, "Lausanne"),         # Swiss Alps
            (40.0150, -105.2705, "Boulder"),       # Rocky Mountains
            (-16.2902, -63.5887, "La Paz"),        # Andes
            
            # Forest (might favor forest animals)
            (45.5017, -73.5673, "Montreal"),       # Boreal forest
            (55.7558, 37.6176, "Moscow"),          # Taiga
            (-22.9068, -43.1729, "Rio de Janeiro"), # Atlantic forest
        ]
        
        lat, lon, city = random.choice(locations)
        
        # Add some random variation
        lat += random.uniform(-0.3, 0.3)
        lon += random.uniform(-0.3, 0.3)
        
        return {
            'date': birth_date.strftime('%Y-%m-%d'),
            'time': f"{hour:02d}:{minute:02d}",
            'lat': round(lat, 6),
            'lon': round(lon, 6),
            'city': city,
            'strategy': combination['description'],
            'target_animal': target_animal,
            'profile_id': len(self.found_animals) + 1
        }
    
    def analyze_and_track(self, profiles: List[Dict], batch_size: int = 25) -> List[Dict]:
        """Analyze profiles and track which animals we find."""
        print(f"🔬 Analyzing {len(profiles)} profiles with animal tracking...")
        
        results = []
        successful = 0
        new_animals = 0
        
        for i, profile in enumerate(profiles, 1):
            print(f"📊 Profile {i}/{len(profiles)}: {profile['city']} ({profile['strategy']})", end=" ... ")
            
            result = self._analyze_profile(profile)
            results.append(result)
            
            if result['analysis_successful'] and result['top1_animal']:
                successful += 1
                animal = result['top1_animal']
                
                # Track new animals
                if animal not in self.found_animals:
                    new_animals += 1
                    self.found_animals.add(animal)
                    self.animal_profiles[animal] = []
                
                self.animal_profiles[animal].append(result)
                
                if animal == profile.get('target_animal'):
                    print(f"🎯 TARGET HIT: {animal}")
                else:
                    print(f"✅ {animal}")
            else:
                print(f"❌ Failed")
            
            # Progress reporting
            if i % batch_size == 0:
                print(f"\n📈 Progress: {i}/{len(profiles)} | ✅ {successful} | 🆕 {new_animals} new animals | 🎯 {len(self.found_animals)}/{len(self.all_animals)} total")
        
        print(f"\n🎉 Analysis completed!")
        print(f"📊 Total: {len(results)} | ✅ Successful: {successful} | 🆕 New animals: {new_animals}")
        print(f"🎯 Animal diversity: {len(self.found_animals)}/{len(self.all_animals)} ({len(self.found_animals)/len(self.all_animals)*100:.1f}%)")
        
        return results
    
    def _analyze_profile(self, profile: Dict) -> Dict:
        """Analyze a single profile."""
        try:
            self.analyzer.run_analysis(
                date=profile['date'],
                time=profile['time'],
                lat=profile['lat'],
                lon=profile['lon']
            )
            
            # Read results
            result_path = "outputs/result.json"
            if os.path.exists(result_path):
                with open(result_path, 'r', encoding='utf-8') as f:
                    result_data = json.load(f)
                
                animal_totals = result_data.get('animal_totals', [])
                if animal_totals:
                    top1_animal = animal_totals[0]['ANIMAL']
                    
                    return {
                        'profile_id': profile['profile_id'],
                        'date': profile['date'],
                        'time': profile['time'],
                        'lat': profile['lat'],
                        'lon': profile['lon'],
                        'city': profile['city'],
                        'strategy': profile.get('strategy', ''),
                        'target_animal': profile.get('target_animal', ''),
                        'top1_animal': top1_animal,
                        'top1_score': animal_totals[0]['TOTAL_SCORE'],
                        'analysis_successful': True,
                        'error': None
                    }
            
            return {
                'profile_id': profile['profile_id'],
                'date': profile['date'],
                'time': profile['time'],
                'lat': profile['lat'],
                'lon': profile['lon'],
                'city': profile['city'],
                'strategy': profile.get('strategy', ''),
                'target_animal': profile.get('target_animal', ''),
                'top1_animal': None,
                'top1_score': None,
                'analysis_successful': False,
                'error': 'No results found'
            }
            
        except Exception as e:
            return {
                'profile_id': profile['profile_id'],
                'date': profile['date'],
                'time': profile['time'],
                'lat': profile['lat'],
                'lon': profile['lon'],
                'city': profile['city'],
                'strategy': profile.get('strategy', ''),
                'target_animal': profile.get('target_animal', ''),
                'top1_animal': None,
                'top1_score': None,
                'analysis_successful': False,
                'error': str(e)
            }
    
    def print_animal_coverage(self):
        """Print detailed animal coverage statistics."""
        print(f"\n📊 ANIMAL COVERAGE REPORT")
        print(f"=" * 60)
        print(f"🎯 Total animals available: {len(self.all_animals)}")
        print(f"✅ Animals found: {len(self.found_animals)}")
        print(f"❌ Animals missing: {len(self.all_animals) - len(self.found_animals)}")
        print(f"📈 Coverage: {len(self.found_animals)/len(self.all_animals)*100:.1f}%")
        
        if self.found_animals:
            print(f"\n✅ FOUND ANIMALS:")
            for animal in sorted(self.found_animals):
                count = len(self.animal_profiles.get(animal, []))
                print(f"   {animal:<25} {count:3d} profiles")
        
        missing_animals = set(self.all_animals) - self.found_animals
        if missing_animals:
            print(f"\n❌ MISSING ANIMALS:")
            for animal in sorted(missing_animals):
                print(f"   {animal}")
    
    def save_results(self, results: List[Dict], filename: str = "advanced_batch_results.json"):
        """Save results to file."""
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

def main():
    """Main function for advanced batch testing."""
    print("🚀 PLUMATOTM ADVANCED BATCH TESTER")
    print("=" * 60)
    
    # Initialize tester
    tester = AdvancedBatchTester()
    
    # Get existing animals from database
    existing_animals = tester.get_current_database_animals()
    if existing_animals:
        tester.found_animals = existing_animals
        print(f"📊 Starting with {len(existing_animals)} animals already in database")
    
    # Configuration
    target_count = 1000  # Total profiles to generate
    batch_size = 25      # Progress reporting
    
    print(f"⚙️  Configuration:")
    print(f"   Target profiles: {target_count}")
    print(f"   Batch size: {batch_size}")
    
    # Generate targeted profiles
    profiles = tester.generate_targeted_profiles(count=target_count)
    
    # Analyze with tracking
    results = tester.analyze_and_track(profiles, batch_size=batch_size)
    
    # Save results
    tester.save_results(results, "advanced_batch_results.json")
    
    # Print coverage report
    tester.print_animal_coverage()
    
    print(f"\n🎉 Advanced batch testing completed!")
    print(f"💾 Results saved to outputs/")
    print(f"🌐 Your Supabase database should now have much more animal diversity!")

if __name__ == "__main__":
    main()
