#!/usr/bin/env python3
"""
Configuration Supabase pour PLUMATOTM
"""

import os
from typing import Optional

# Charger les variables d'environnement depuis .env
try:
    from dotenv import load_dotenv
    load_dotenv()  # Charge le fichier .env
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    print("⚠️  python-dotenv non installé. Installez avec: pip install python-dotenv")

class SupabaseConfig:
    """Configuration pour la connexion Supabase."""
    
    def __init__(self):
        # Ces valeurs doivent être configurées dans les variables d'environnement
        # ou dans un fichier .env
        self.url = os.getenv('SUPABASE_URL')
        self.key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        self.table_name = 'plumastat_usage'
        
    def is_configured(self) -> bool:
        """Vérifie si Supabase est configuré."""
        return bool(self.url and self.key)
    
    def get_connection_info(self) -> dict:
        """Retourne les informations de connexion."""
        return {
            'url': self.url,
            'key': self.key,
            'table_name': self.table_name
        }

# Instance globale
supabase_config = SupabaseConfig()
