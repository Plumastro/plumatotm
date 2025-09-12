#!/usr/bin/env python3
"""
Processeur de batch simple et fiable pour 1000 profils
"""

import json
import os
import sys
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from plumatotm_core import BirthChartAnalyzer
    from supabase_manager import SupabaseManager
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def process_single_profile(analyzer, profile, profile_index):
    """Traiter un seul profil"""
    try:
        name = profile.get('name', '').strip()
        date = profile.get('date', '')
        time_str = profile.get('time', '')
        lat = float(profile.get('lat', 0))
        lon = float(profile.get('lon', 0))
        
        print(f"\n📊 Profil {profile_index + 1}/1000")
        print(f"   📅 {date} {time_str}")
        print(f"   📍 {lat}, {lon}")
        
        # Analyse sans ChatGPT
        result = analyzer.run_analysis(
            date=date,
            time=time_str,
            lat=lat,
            lon=lon,
            user_name=name if name else None,
            openai_api_key=None
        )
        
        if result and result.get('success'):
            top1_animal = result.get('top1_animal', 'Unknown')
            score = result.get('top1_score', 0)
            print(f"   ✅ {top1_animal} (Score: {score})")
            
            return {
                'profile_id': profile_index + 1,
                'name': name,
                'date': date,
                'time': time_str,
                'lat': lat,
                'lon': lon,
                'top1_animal': top1_animal,
                'top1_score': score,
                'success': True,
                'plumid': result.get('plumid', ''),
                'timestamp': datetime.now().isoformat()
            }
        else:
            error = result.get('error', 'Unknown error') if result else 'No result'
            print(f"   ❌ Échec: {error}")
            return {
                'profile_id': profile_index + 1,
                'name': name,
                'date': date,
                'time': time_str,
                'lat': lat,
                'lon': lon,
                'top1_animal': 'Unknown',
                'top1_score': 0,
                'success': False,
                'error': error,
                'timestamp': datetime.now().isoformat()
            }
            
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return {
            'profile_id': profile_index + 1,
            'name': profile.get('name', ''),
            'date': profile.get('date', ''),
            'time': profile.get('time', ''),
            'lat': profile.get('lat', 0),
            'lon': profile.get('lon', 0),
            'top1_animal': 'Unknown',
            'top1_score': 0,
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def main():
    print("🚀 PROCESSEUR DE BATCH SIMPLE - 1000 PROFILS")
    print("=" * 50)
    
    # Charger les profils
    try:
        with open('plumastro_1000_profiles.json', 'r', encoding='utf-8') as f:
            profiles = json.load(f)
        print(f"📊 {len(profiles)} profils chargés")
    except Exception as e:
        print(f"❌ Erreur chargement: {e}")
        return
    
    # Initialiser l'analyseur
    try:
        analyzer = BirthChartAnalyzer(
            scores_csv_path="plumatotm_raw_scores_trad.csv",
            weights_csv_path="plumatotm_planets_weights.csv",
            multipliers_csv_path="plumatotm_planets_multiplier.csv"
        )
        print("✅ Analyseur initialisé")
    except Exception as e:
        print(f"❌ Erreur analyseur: {e}")
        return
    
    # Traiter les profils
    results = []
    successful = 0
    failed = 0
    
    for i, profile in enumerate(profiles):
        result = process_single_profile(analyzer, profile, i)
        results.append(result)
        
        if result['success']:
            successful += 1
        else:
            failed += 1
        
        # Sauvegarder tous les 10 profils
        if (i + 1) % 10 == 0:
            with open('outputs/batch_progress.json', 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"💾 Progrès sauvegardé: {i + 1}/1000")
        
        # Afficher le progrès tous les 50 profils
        if (i + 1) % 50 == 0:
            progress = (i + 1) / len(profiles) * 100
            print(f"\n📊 PROGRÈS: {i + 1}/{len(profiles)} ({progress:.1f}%)")
            print(f"✅ Succès: {successful} | ❌ Échecs: {failed}")
    
    # Sauvegarde finale
    with open('outputs/batch_final_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n🎉 TERMINÉ!")
    print(f"📊 Total: {len(results)} profils")
    print(f"✅ Succès: {successful}")
    print(f"❌ Échecs: {failed}")

if __name__ == "__main__":
    main()

