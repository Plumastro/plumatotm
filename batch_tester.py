#!/usr/bin/env python3
"""
Batch Tester for PLUMATOTM Engine
Generates many different birth profiles to populate Supabase database with diverse top1 animals
"""

import random
import json
import time
import csv
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from plumatotm_core import BirthChartAnalyzer
import os

class BatchTester:
    """Batch tester for generating diverse birth profiles."""
    
    def __init__(self, 
                 scores_csv_path: str = "plumatotm_raw_scores_trad.csv",
                 weights_csv_path: str = "plumatotm_planets_weights.csv", 
                 multipliers_csv_path: str = "plumatotm_planets_multiplier.csv",
                 translations_csv_path: str = "plumatotm_raw_scores_trad.csv"):
        """Initialize the batch tester with the PLUMATOTM engine."""
        self.analyzer = BirthChartAnalyzer(
            scores_csv_path=scores_csv_path,
            weights_csv_path=weights_csv_path,
            multipliers_csv_path=multipliers_csv_path,
            translations_csv_path=translations_csv_path
        )
        
        # Load all available animals for analysis
        self.analyzer._ensure_scores_data_loaded()
        self.analyzer._ensure_animal_translations_loaded()
        self.all_animals = self.analyzer.animals
        
        print(f"🎯 Batch Tester initialized with {len(self.all_animals)} animals")
        print(f"📊 Available animals: {', '.join(self.all_animals[:10])}{'...' if len(self.all_animals) > 10 else ''}")
    
    def generate_random_birth_data(self, count: int = 1000) -> List[Dict]:
        """
        Generate random birth data for testing.
        
        Args:
            count: Number of profiles to generate
            
        Returns:
            List of birth data dictionaries
        """
        print(f"🎲 Generating {count} random birth profiles...")
        
        profiles = []
        
        # Define realistic ranges
        start_date = datetime(1950, 1, 1)
        end_date = datetime(2010, 12, 31)
        date_range = (end_date - start_date).days
        
        # Major cities with diverse locations
        cities = [
            # North America
            (40.7128, -74.0060, "New York"),      # NYC
            (34.0522, -118.2437, "Los Angeles"),  # LA
            (41.8781, -87.6298, "Chicago"),       # Chicago
            (29.7604, -95.3698, "Houston"),       # Houston
            (25.7617, -80.1918, "Miami"),         # Miami
            
            # Europe
            (51.5074, -0.1278, "London"),         # London
            (48.8566, 2.3522, "Paris"),           # Paris
            (52.5200, 13.4050, "Berlin"),         # Berlin
            (41.9028, 12.4964, "Rome"),           # Rome
            (55.7558, 37.6176, "Moscow"),         # Moscow
            
            # Asia
            (35.6762, 139.6503, "Tokyo"),         # Tokyo
            (22.3193, 114.1694, "Hong Kong"),     # Hong Kong
            (1.3521, 103.8198, "Singapore"),      # Singapore
            (19.0760, 72.8777, "Mumbai"),         # Mumbai
            (37.5665, 126.9780, "Seoul"),         # Seoul
            
            # South America
            (-23.5505, -46.6333, "São Paulo"),    # São Paulo
            (-34.6118, -58.3960, "Buenos Aires"), # Buenos Aires
            (-12.0464, -77.0428, "Lima"),         # Lima
            (4.7110, -74.0721, "Bogotá"),         # Bogotá
            
            # Africa
            (-26.2041, 28.0473, "Johannesburg"),  # Johannesburg
            (30.0444, 31.2357, "Cairo"),          # Cairo
            (6.5244, 3.3792, "Lagos"),            # Lagos
            (-1.2921, 36.8219, "Nairobi"),        # Nairobi
            
            # Oceania
            (-33.8688, 151.2093, "Sydney"),       # Sydney
            (-37.8136, 144.9631, "Melbourne"),    # Melbourne
            (-36.8485, 174.7633, "Auckland"),     # Auckland
        ]
        
        for i in range(count):
            # Random date
            random_days = random.randint(0, date_range)
            birth_date = start_date + timedelta(days=random_days)
            
            # Random time (24-hour format)
            hour = random.randint(0, 23)
            minute = random.randint(0, 59)
            
            # Random city
            lat, lon, city_name = random.choice(cities)
            
            # Add some random variation to coordinates (±0.5 degrees)
            lat += random.uniform(-0.5, 0.5)
            lon += random.uniform(-0.5, 0.5)
            
            profile = {
                'date': birth_date.strftime('%Y-%m-%d'),
                'time': f"{hour:02d}:{minute:02d}",
                'lat': round(lat, 6),
                'lon': round(lon, 6),
                'city': city_name,
                'profile_id': i + 1
            }
            
            profiles.append(profile)
        
        print(f"✅ Generated {len(profiles)} birth profiles")
        return profiles
    
    def analyze_profile(self, profile: Dict) -> Dict:
        """
        Analyze a single birth profile.
        
        Args:
            profile: Birth data dictionary
            
        Returns:
            Analysis result with top1 animal
        """
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
                
                # Extract top1 animal from animal_totals
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
                'top1_animal': None,
                'top1_score': None,
                'analysis_successful': False,
                'error': str(e)
            }
    
    def batch_analyze(self, profiles: List[Dict], batch_size: int = 50, delay: float = 0.1) -> List[Dict]:
        """
        Analyze multiple profiles in batches.
        
        Args:
            profiles: List of birth profiles
            batch_size: Number of profiles to process before reporting
            delay: Delay between analyses (seconds)
            
        Returns:
            List of analysis results
        """
        print(f"🔬 Starting batch analysis of {len(profiles)} profiles...")
        print(f"📦 Batch size: {batch_size}, Delay: {delay}s between analyses")
        
        results = []
        successful = 0
        failed = 0
        
        for i, profile in enumerate(profiles, 1):
            print(f"📊 Analyzing profile {i}/{len(profiles)}: {profile['city']} ({profile['date']} {profile['time']})", end=" ... ")
            
            result = self.analyze_profile(profile)
            results.append(result)
            
            if result['analysis_successful']:
                successful += 1
                print(f"✅ {result['top1_animal']}")
            else:
                failed += 1
                print(f"❌ {result['error']}")
            
            # Batch reporting
            if i % batch_size == 0:
                print(f"\n📈 Progress: {i}/{len(profiles)} | ✅ {successful} successful | ❌ {failed} failed")
                print(f"🎯 Current animal diversity: {len(set(r['top1_animal'] for r in results if r['top1_animal']))} unique animals")
            
            # Delay between analyses
            if delay > 0:
                time.sleep(delay)
        
        print(f"\n🎉 Batch analysis completed!")
        print(f"📊 Total: {len(results)} | ✅ Successful: {successful} | ❌ Failed: {failed}")
        
        return results
    
    def save_results(self, results: List[Dict], output_file: str = "batch_test_results.json"):
        """Save batch test results to file."""
        try:
            os.makedirs("outputs", exist_ok=True)
            output_path = f"outputs/{output_file}"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Results saved to: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving results: {e}")
            return False
    
    def save_csv_summary(self, results: List[Dict], output_file: str = "batch_test_summary.csv"):
        """Save a CSV summary of the results."""
        try:
            os.makedirs("outputs", exist_ok=True)
            output_path = f"outputs/{output_file}"
            
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
    
    def generate_animal_statistics(self, results: List[Dict]) -> Dict:
        """Generate statistics about the animal distribution."""
        successful_results = [r for r in results if r['analysis_successful'] and r['top1_animal']]
        
        if not successful_results:
            return {'error': 'No successful analyses'}
        
        animal_counts = {}
        city_animals = {}
        date_animals = {}
        
        for result in successful_results:
            animal = result['top1_animal']
            city = result['city']
            date = result['date'][:7]  # YYYY-MM
            
            # Count animals
            animal_counts[animal] = animal_counts.get(animal, 0) + 1
            
            # Animals by city
            if city not in city_animals:
                city_animals[city] = {}
            city_animals[city][animal] = city_animals[city].get(animal, 0) + 1
            
            # Animals by month
            if date not in date_animals:
                date_animals[date] = {}
            date_animals[date][animal] = date_animals[date].get(animal, 0) + 1
        
        # Sort animals by frequency
        sorted_animals = sorted(animal_counts.items(), key=lambda x: x[1], reverse=True)
        
        stats = {
            'total_profiles': len(results),
            'successful_analyses': len(successful_results),
            'failed_analyses': len(results) - len(successful_results),
            'unique_animals': len(animal_counts),
            'animal_distribution': dict(sorted_animals),
            'top_10_animals': dict(sorted_animals[:10]),
            'rare_animals': dict([(k, v) for k, v in sorted_animals if v == 1]),
            'city_diversity': {city: len(animals) for city, animals in city_animals.items()},
            'month_diversity': {month: len(animals) for month, animals in date_animals.items()}
        }
        
        return stats
    
    def print_statistics(self, results: List[Dict]):
        """Print detailed statistics about the batch test results."""
        stats = self.generate_animal_statistics(results)
        
        if 'error' in stats:
            print(f"❌ {stats['error']}")
            return
        
        print(f"\n📊 BATCH TEST STATISTICS")
        print(f"=" * 50)
        print(f"📈 Total Profiles: {stats['total_profiles']}")
        print(f"✅ Successful: {stats['successful_analyses']}")
        print(f"❌ Failed: {stats['failed_analyses']}")
        print(f"🎯 Unique Animals: {stats['unique_animals']}/{len(self.all_animals)} ({stats['unique_animals']/len(self.all_animals)*100:.1f}%)")
        
        print(f"\n🏆 TOP 10 ANIMALS:")
        for i, (animal, count) in enumerate(stats['top_10_animals'].items(), 1):
            percentage = count / stats['successful_analyses'] * 100
            print(f"   {i:2d}. {animal:<20} {count:3d} times ({percentage:5.1f}%)")
        
        if stats['rare_animals']:
            print(f"\n🦄 RARE ANIMALS (appeared only once):")
            for animal in list(stats['rare_animals'].keys())[:10]:
                print(f"   • {animal}")
            if len(stats['rare_animals']) > 10:
                print(f"   ... and {len(stats['rare_animals']) - 10} more")
        
        print(f"\n🌍 CITY DIVERSITY:")
        sorted_cities = sorted(stats['city_diversity'].items(), key=lambda x: x[1], reverse=True)
        for city, diversity in sorted_cities[:5]:
            print(f"   {city:<15} {diversity} unique animals")
        
        print(f"\n📅 MONTHLY DIVERSITY:")
        sorted_months = sorted(stats['month_diversity'].items(), key=lambda x: x[1], reverse=True)
        for month, diversity in sorted_months[:5]:
            print(f"   {month:<10} {diversity} unique animals")

def main():
    """Main function to run batch testing."""
    print("🚀 PLUMATOTM BATCH TESTER")
    print("=" * 50)
    
    # Initialize batch tester
    tester = BatchTester()
    
    # Configuration
    num_profiles = 1000  # Adjust this number
    batch_size = 50      # Report progress every N profiles
    delay = 0.1          # Delay between analyses (seconds)
    
    print(f"⚙️  Configuration:")
    print(f"   Profiles to generate: {num_profiles}")
    print(f"   Batch size: {batch_size}")
    print(f"   Delay between analyses: {delay}s")
    
    # Generate random birth profiles
    profiles = tester.generate_random_birth_data(num_profiles)
    
    # Run batch analysis
    results = tester.batch_analyze(profiles, batch_size=batch_size, delay=delay)
    
    # Save results
    tester.save_results(results, "batch_test_results.json")
    tester.save_csv_summary(results, "batch_test_summary.csv")
    
    # Print statistics
    tester.print_statistics(results)
    
    print(f"\n🎉 Batch testing completed!")
    print(f"💾 Results saved to outputs/")
    print(f"🌐 Your Supabase database should now have {len([r for r in results if r['analysis_successful']])} new profiles!")

if __name__ == "__main__":
    main()
