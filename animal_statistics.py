#!/usr/bin/env python3
"""
Générateur de statistiques d'animaux pour PLUMATOTM
Génère l'output animal_proportion.json avec les pourcentages d'occurrence.
"""

import json
import os
import pandas as pd
from typing import Dict, List, Optional
from plumid_generator import PlumIDGenerator
from supabase_manager import supabase_manager

class AnimalStatisticsGenerator:
    """Générateur de statistiques d'animaux."""
    
    def __init__(self, raw_scores_file: str = "plumatotm_raw_scores.csv"):
        self.raw_scores_file = raw_scores_file
        self.all_animals = self._load_all_animals()
    
    def _load_all_animals(self) -> List[str]:
        """Charge la liste de tous les animaux disponibles."""
        try:
            if os.path.exists(self.raw_scores_file):
                df = pd.read_csv(self.raw_scores_file)
                if 'ANIMAL' in df.columns:
                    return sorted(df['ANIMAL'].unique().tolist())
            
            # Fallback: liste des animaux les plus communs
            return [
                "Penguin", "Mountain Goat", "Donkey", "Owl", "Raven", "Dog (siberian husky)",
                "Falcon", "Snow Leopard", "Dog (dalmatian)", "Bat", "Bee", "Lizard",
                "Shark", "Dog (border collie)", "Hare", "Parrot", "Squirrel", "Lemur",
                "Gazelle", "Monkey", "Raccoon", "Horse", "Seahorse", "Cobra", "Macaw",
                "Fox", "Crane", "Tiger", "Octopus", "Pelican", "Jaguar", "Eagle", "Cat",
                "Butterfly", "Giraffe", "Dolphin", "Lynx", "Chameleon", "Swallow",
                "Caribou", "Peacock", "Dog (great dane)", "Jellyfish", "Cheetah", "Otter",
                "Boa Constrictor", "Hedgehog", "Polar Bear", "Turtle", "Dog (rottweiler)",
                "Koala", "Llama", "Panther", "Whale", "Stag", "Elk", "Camel", "Beaver",
                "Crocodile", "Elephant", "Wolf", "Cow", "Dog (belgian malinois)", "Pig",
                "Capybara", "Sheep", "Gorillas", "Kangaroo", "Frog", "Swan", "Hippopotamus",
                "Bear", "Deer", "Panda", "Goose", "Dog (bulldog)", "Dog (golden retriever)",
                "Snake", "Rabbit"
            ]
        except Exception as e:
            print(f"⚠️  Erreur chargement animaux: {e}")
            return []
    
    def generate_plumid(self, date: str, time: str, lat: float, lon: float) -> str:
        """Génère le PlumID pour l'utilisateur actuel."""
        return PlumIDGenerator.generate_plumid(date, time, lat, lon)
    
    def process_user(self, plumid: str, current_top1_animal: str) -> Dict:
        """
        Traite un utilisateur: vérifie s'il existe, l'ajoute ou le met à jour.
        
        Args:
            plumid: ID unique de l'utilisateur
            current_top1_animal: Animal top1 actuel
            
        Returns:
            Dictionnaire avec les informations de traitement
        """
        result = {
            'plumid': plumid,
            'current_animal': current_top1_animal,
            'is_new_user': False,
            'previous_animal': None,
            'animal_changed': False
        }
        
        if not supabase_manager.is_available():
            print("⚠️  Supabase non disponible, simulation du traitement")
            result['is_new_user'] = True
            return result
        
        # Vérifier si l'utilisateur existe
        existing_animal = supabase_manager.get_user_animal(plumid)
        
        if existing_animal is None:
            # Nouvel utilisateur
            success = supabase_manager.add_user(plumid, current_top1_animal)
            if success:
                result['is_new_user'] = True
                print(f"✅ Nouvel utilisateur ajouté: {plumid}")
            else:
                print(f"❌ Échec ajout utilisateur: {plumid}")
        else:
            # Utilisateur existant
            result['previous_animal'] = existing_animal
            if existing_animal != current_top1_animal:
                # L'animal a changé
                success = supabase_manager.update_user_animal(plumid, current_top1_animal)
                if success:
                    result['animal_changed'] = True
                    print(f"🔄 Animal mis à jour: {existing_animal} -> {current_top1_animal}")
                else:
                    print(f"❌ Échec mise à jour: {plumid}")
            else:
                print(f"ℹ️  Animal inchangé: {current_top1_animal}")
        
        return result
    
    def generate_animal_proportion(self, plumid: str, current_top1_animal: str) -> Dict:
        """
        Génère les statistiques d'animaux pour l'output animal_proportion.json.
        
        Args:
            plumid: ID unique de l'utilisateur
            current_top1_animal: Animal top1 de l'utilisateur actuel
            
        Returns:
            Dictionnaire avec les statistiques
        """
        result = {
            'user_plumid': plumid,
            'user_current_animal': current_top1_animal,
            'user_animal_percentage': 0.0,
            'all_animals_percentages': {}
        }
        
        if not supabase_manager.is_available():
            print("⚠️  Supabase non disponible, génération de statistiques simulées")
            # Statistiques simulées pour le développement
            result['user_animal_percentage'] = 15.5  # Exemple
            result['all_animals_percentages'] = {
                animal: round(100 / len(self.all_animals), 2) 
                for animal in self.all_animals[:10]  # Limiter pour l'exemple
            }
            return result
        
        # Calculer le pourcentage de l'utilisateur actuel
        user_percentage = supabase_manager.get_user_percentage(plumid, current_top1_animal)
        result['user_animal_percentage'] = user_percentage
        
        # Récupérer les statistiques globales
        global_stats = supabase_manager.get_animal_statistics()
        
        # Compléter avec tous les animaux (même ceux avec 0%)
        for animal in self.all_animals:
            result['all_animals_percentages'][animal] = global_stats.get(animal, 0.0)
        
        return result
    
    def save_animal_proportion(self, statistics: Dict, output_path: str = "outputs/animal_proportion.json") -> bool:
        """
        Sauvegarde les statistiques dans le fichier animal_proportion.json.
        
        Args:
            statistics: Dictionnaire des statistiques
            output_path: Chemin de sortie
            
        Returns:
            True si succès, False sinon
        """
        try:
            # Créer le dossier outputs s'il n'existe pas
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Sauvegarder le fichier
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(statistics, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Statistiques sauvegardées: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur sauvegarde statistiques: {e}")
            return False
    
    def run_full_analysis(self, date: str, time: str, lat: float, lon: float, top1_animal: str) -> Dict:
        """
        Exécute l'analyse complète des statistiques.
        
        Args:
            date: Date de naissance
            time: Heure de naissance
            lat: Latitude
            lon: Longitude
            top1_animal: Animal top1 de l'utilisateur
            
        Returns:
            Dictionnaire avec toutes les statistiques
        """
        print("📊 Génération des statistiques d'animaux...")
        
        # Générer le PlumID
        plumid = self.generate_plumid(date, time, lat, lon)
        print(f"🆔 PlumID généré: {plumid}")
        
        # Traiter l'utilisateur
        user_result = self.process_user(plumid, top1_animal)
        
        # Générer les statistiques
        statistics = self.generate_animal_proportion(plumid, top1_animal)
        
        # Ajouter les informations de traitement
        statistics['user_processing'] = user_result
        
        # Sauvegarder
        self.save_animal_proportion(statistics)
        
        return statistics

# Test du générateur
if __name__ == "__main__":
    print("🧪 Test du générateur de statistiques")
    
    generator = AnimalStatisticsGenerator()
    
    # Test avec des données d'exemple
    test_stats = generator.run_full_analysis(
        date="1998-12-22",
        time="10:13",
        lat=42.35843,
        lon=-71.05977,
        top1_animal="Penguin"
    )
    
    print("📊 Statistiques générées:")
    print(f"   PlumID: {test_stats['user_plumid']}")
    print(f"   Animal actuel: {test_stats['user_current_animal']}")
    print(f"   Pourcentage utilisateur: {test_stats['user_animal_percentage']}%")
    print(f"   Nombre d'animaux: {len(test_stats['all_animals_percentages'])}")
