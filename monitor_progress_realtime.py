#!/usr/bin/env python3
"""
Script de monitoring en temps réel pour le batch processing optimisé
"""

import os
import time
import json
from datetime import datetime

def monitor_realtime_progress():
    """Monitorer l'avancement en temps réel"""
    print("🔍 MONITORING EN TEMPS RÉEL - BATCH PROCESSING OPTIMISÉ")
    print("=" * 60)
    
    summary_file = "outputs/supabase_batch_summary.csv"
    results_file = "outputs/supabase_batch_results.json"
    
    last_count = 0
    start_time = datetime.now()
    last_update_time = datetime.now()
    
    while True:
        try:
            current_count = 0
            current_time = datetime.now()
            
            # Vérifier le fichier CSV
            if os.path.exists(summary_file):
                with open(summary_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    current_count = len(lines) - 1  # -1 pour l'en-tête
                
                # Vérifier la dernière modification
                file_time = datetime.fromtimestamp(os.path.getmtime(summary_file))
                if file_time > last_update_time:
                    last_update_time = file_time
                    print(f"\n🔄 Mise à jour détectée à {file_time.strftime('%H:%M:%S')}")
            
            # Calculer le progrès
            progress_percent = (current_count / 1000) * 100
            elapsed_time = current_time - start_time
            
            # Calculer la vitesse de traitement
            if current_count > last_count:
                time_diff = (current_time - last_update_time).total_seconds()
                if time_diff > 0:
                    speed = (current_count - last_count) / time_diff
                    eta_seconds = (1000 - current_count) / speed if speed > 0 else 0
                    eta = datetime.now().timestamp() + eta_seconds
                    eta_str = datetime.fromtimestamp(eta).strftime('%H:%M:%S')
                else:
                    eta_str = "Calcul..."
            else:
                eta_str = "En attente..."
            
            # Afficher le statut
            status = "🟢 Actif" if current_count > last_count else "🟡 En pause"
            print(f"\r{status} | 📊 {current_count}/1000 ({progress_percent:.1f}%) | "
                  f"⏱️ {elapsed_time} | 🎯 ETA: {eta_str}", end="", flush=True)
            
            # Vérifier si terminé
            if current_count >= 1000:
                print(f"\n\n🎉 BATCH PROCESSING TERMINÉ !")
                print(f"✅ {current_count} profils traités avec succès")
                print(f"⏱️ Temps total: {elapsed_time}")
                break
            
            # Vérifier si bloqué
            if current_count == last_count and current_count > 0:
                time_since_update = (current_time - last_update_time).total_seconds()
                if time_since_update > 60:  # Plus d'1 minute sans mise à jour
                    print(f"\n⚠️  Aucune mise à jour depuis {time_since_update:.0f} secondes")
                    print(f"   Dernier profil: {current_count}")
            
            last_count = current_count
            time.sleep(2)  # Vérifier toutes les 2 secondes
            
        except KeyboardInterrupt:
            print(f"\n\n⏹️  Monitoring arrêté par l'utilisateur")
            print(f"📊 Progrès final: {current_count}/1000 profils")
            break
        except Exception as e:
            print(f"\n❌ Erreur de monitoring: {e}")
            time.sleep(5)

if __name__ == "__main__":
    monitor_realtime_progress()
