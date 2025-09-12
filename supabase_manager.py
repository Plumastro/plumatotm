#!/usr/bin/env python3
"""
Gestionnaire Supabase pour PLUMATOTM
Gère les opérations de base de données pour les statistiques d'utilisation.
"""

import json
import os
from typing import Dict, List, Optional, Tuple
from supabase_config import supabase_config

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("⚠️  Supabase non installé. Installez avec: pip install supabase")

class SupabaseManager:
    """Gestionnaire des opérations Supabase pour PLUMATOTM."""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self.table_name = 'plumastat_usage'
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialise le client Supabase."""
        if not SUPABASE_AVAILABLE:
            print("❌ Supabase non disponible")
            return
        
        if not supabase_config.is_configured():
            print("⚠️  Supabase non configuré. Définissez SUPABASE_URL et SUPABASE_ANON_KEY")
            return
        
        try:
            self.client = create_client(supabase_config.url, supabase_config.key)
            print("✅ Client Supabase initialisé")
        except Exception as e:
            print(f"❌ Erreur d'initialisation Supabase: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """Vérifie si Supabase est disponible et configuré."""
        return self.client is not None
    
    def create_table_if_not_exists(self) -> bool:
        """
        Crée la table si elle n'existe pas.
        Note: Cette fonction nécessite des privilèges d'administration.
        """
        if not self.is_available():
            return False
        
        # SQL pour créer la table
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            plumid TEXT PRIMARY KEY,
            top1_animal TEXT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- Index pour améliorer les performances
        CREATE INDEX IF NOT EXISTS idx_{self.table_name}_top1_animal 
        ON {self.table_name}(top1_animal);
        """
        
        try:
            # Note: Cette opération nécessite des privilèges d'administration
            # En production, créez la table manuellement dans l'interface Supabase
            print("ℹ️  Créez manuellement la table dans l'interface Supabase:")
            print(f"   Table: {self.table_name}")
            print("   Colonnes: plumid (TEXT PRIMARY KEY), top1_animal (TEXT), created_at (TIMESTAMP), updated_at (TIMESTAMP)")
            return True
        except Exception as e:
            print(f"❌ Erreur création table: {e}")
            return False
    
    def get_user_animal(self, plumid: str) -> Optional[str]:
        """
        Récupère l'animal top1 d'un utilisateur existant.
        
        Args:
            plumid: ID unique de l'utilisateur
            
        Returns:
            Nom de l'animal top1 ou None si non trouvé
        """
        if not self.is_available():
            return None
        
        try:
            response = self.client.table(self.table_name).select("top1_animal").eq("plumid", plumid).execute()
            
            if response.data:
                return response.data[0]['top1_animal']
            return None
            
        except Exception as e:
            print(f"❌ Erreur récupération utilisateur: {e}")
            return None
    
    def add_user(self, plumid: str, top1_animal: str, user_name: str = None) -> bool:
        """
        Ajoute un nouvel utilisateur à la base de données.
        
        Args:
            plumid: ID unique de l'utilisateur
            top1_animal: Animal top1 de l'utilisateur
            user_name: Nom de l'utilisateur (optionnel)
            
        Returns:
            True si succès, False sinon
        """
        if not self.is_available():
            return False
        
        try:
            data = {
                'plumid': plumid,
                'top1_animal': top1_animal
            }
            
            # Add user_name if provided
            if user_name:
                data['user_name'] = user_name
            
            response = self.client.table(self.table_name).insert(data).execute()
            
            if response.data:
                name_display = f" ({user_name})" if user_name else ""
                print(f"✅ Utilisateur ajouté: {plumid} -> {top1_animal}{name_display}")
                return True
            return False
            
        except Exception as e:
            print(f"❌ Erreur ajout utilisateur: {e}")
            return False
    
    def update_user_animal(self, plumid: str, top1_animal: str, user_name: str = None) -> bool:
        """
        Met à jour l'animal top1 d'un utilisateur existant.
        
        Args:
            plumid: ID unique de l'utilisateur
            top1_animal: Nouvel animal top1
            user_name: Nom de l'utilisateur (optionnel)
            
        Returns:
            True si succès, False sinon
        """
        if not self.is_available():
            return False
        
        try:
            data = {
                'top1_animal': top1_animal,
                'updated_at': 'NOW()'
            }
            
            # Add user_name if provided
            if user_name:
                data['user_name'] = user_name
            
            response = self.client.table(self.table_name).update(data).eq('plumid', plumid).execute()
            
            if response.data:
                name_display = f" ({user_name})" if user_name else ""
                print(f"✅ Utilisateur mis à jour: {plumid} -> {top1_animal}{name_display}")
                return True
            return False
            
        except Exception as e:
            print(f"❌ Erreur mise à jour utilisateur: {e}")
            return False
    
    def get_animal_statistics(self) -> Dict[str, float]:
        """
        Récupère les statistiques d'occurrence de chaque animal.
        
        Returns:
            Dictionnaire {animal: pourcentage}
        """
        if not self.is_available():
            return {}
        
        try:
            # Récupérer tous les animaux
            response = self.client.table(self.table_name).select("top1_animal").execute()
            
            if not response.data:
                return {}
            
            # Compter les occurrences
            animal_counts = {}
            total_users = len(response.data)
            
            for record in response.data:
                animal = record['top1_animal']
                animal_counts[animal] = animal_counts.get(animal, 0) + 1
            
            # Calculer les pourcentages
            animal_percentages = {}
            for animal, count in animal_counts.items():
                percentage = (count / total_users) * 100
                animal_percentages[animal] = round(percentage, 2)
            
            return animal_percentages
            
        except Exception as e:
            print(f"❌ Erreur récupération statistiques: {e}")
            return {}
    
    def get_user_percentage(self, plumid: str, top1_animal: str) -> float:
        """
        Calcule le pourcentage d'utilisateurs ayant le même animal top1.
        
        Args:
            plumid: ID unique de l'utilisateur
            top1_animal: Animal top1 de l'utilisateur
            
        Returns:
            Pourcentage d'utilisateurs avec le même animal
        """
        if not self.is_available():
            return 0.0
        
        try:
            # Compter les utilisateurs avec le même animal
            response = self.client.table(self.table_name).select("plumid").eq("top1_animal", top1_animal).execute()
            
            if not response.data:
                return 0.0
            
            same_animal_count = len(response.data)
            
            # Compter le total d'utilisateurs
            total_response = self.client.table(self.table_name).select("plumid").execute()
            total_users = len(total_response.data) if total_response.data else 1
            
            percentage = (same_animal_count / total_users) * 100
            return round(percentage, 2)
            
        except Exception as e:
            print(f"❌ Erreur calcul pourcentage utilisateur: {e}")
            return 0.0

# Instance globale
supabase_manager = SupabaseManager()

# Test du gestionnaire
if __name__ == "__main__":
    print("🧪 Test du gestionnaire Supabase")
    print(f"Supabase disponible: {supabase_manager.is_available()}")
    
    if supabase_manager.is_available():
        print("✅ Gestionnaire Supabase opérationnel")
    else:
        print("❌ Gestionnaire Supabase non disponible")
        print("Configurez SUPABASE_URL et SUPABASE_ANON_KEY dans vos variables d'environnement")
