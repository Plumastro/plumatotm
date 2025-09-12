#!/usr/bin/env python3
"""
Script de monitoring pour suivre l'avancement du batch processing
"""

import os
import time
import json
from datetime import datetime

def monitor_batch_progress():
    """Monitorer l'avancement du batch processing"""
    print("🔍 MONITORING DU BATCH PROCESSING - 1000 PROFILS")
    print("=" * 60)
    
    # Fichiers à surveiller
    summary_file = "outputs/supabase_batch_summary.csv"
    results_file = "outputs/supabase_batch_results.json"
    animal_totals_file = "outputs/animal_totals.json"
    
    last_count = 0
    start_time = datetime.now()
    
    while True:
        try:
            # Vérifier si les fichiers existent
            if os.path.exists(summary_file):
                with open(summary_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    current_count = len(lines) - 1  # -1 pour l'en-tête
            else:
                current_count = 0
            
            # Vérifier le fichier JSON des résultats
            if os.path.exists(results_file):
                with open(results_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    json_count = len(data)
            else:
                json_count = 0
            
            # Vérifier les totaux d'animaux
            if os.path.exists(animal_totals_file):
                with open(animal_totals_file, 'r', encoding='utf-8') as f:
                    animal_data = json.load(f)
                    unique_animals = len([a for a in animal_data if a['TOTAL_SCORE'] > 0])
            else:
                unique_animals = 0
            
            # Calculer le progrès
            progress_percent = (current_count / 1000) * 100
            elapsed_time = datetime.now() - start_time
            
            # Afficher le statut
            print(f"\r📊 Progrès: {current_count}/1000 profils ({progress_percent:.1f}%) | "
                  f"JSON: {json_count} | Animaux uniques: {unique_animals} | "
                  f"Temps écoulé: {elapsed_time}", end="", flush=True)
            
            # Vérifier si le processus est terminé
            if current_count >= 1000:
                print(f"\n\n🎉 BATCH PROCESSING TERMINÉ !")
                print(f"✅ {current_count} profils traités avec succès")
                break
            
            # Vérifier si le processus est bloqué
            if current_count == last_count and current_count > 0:
                print(f"\n⚠️  Aucun nouveau profil traité depuis 30 secondes...")
                print(f"   Dernier profil: {current_count}")
            
            last_count = current_count
            time.sleep(5)  # Vérifier toutes les 5 secondes
            
        except KeyboardInterrupt:
            print(f"\n\n⏹️  Monitoring arrêté par l'utilisateur")
            break
        except Exception as e:
            print(f"\n❌ Erreur de monitoring: {e}")
            time.sleep(5)

if __name__ == "__main__":
    monitor_batch_progress()

