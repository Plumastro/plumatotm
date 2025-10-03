#!/usr/bin/env python3
"""
Générateur PlumID pour PLUMATOTM
Génère un ID unique basé sur les données de naissance et localisation.
"""

import re
from datetime import datetime
from typing import Tuple

class PlumIDGenerator:
    """Générateur d'ID unique pour chaque individu."""
    
    @staticmethod
    def generate_plumid(date: str, time: str, lat: float, lon: float) -> str:
        """
        Génère un PlumID unique basé sur les données d'entrée.
        
        Format: YYYY_MM_DD_HH_MM_LATDIR_LAT_LONDIR_LON
        Exemple: 1989_09_28_20_15_N_48D30442_W_0D61799
        
        Args:
            date: Date de naissance (format: YYYY-MM-DD)
            time: Heure de naissance locale (format: HH:MM en 24h)
            lat: Latitude (positive pour Nord, négative pour Sud)
            lon: Longitude (positive pour Est, négative pour Ouest)
            
        Returns:
            PlumID unique avec directions N/S et E/W
        """
        # Parse la date
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        
        # Parse l'heure (format 24h uniquement)
        time_clean = time.strip()
        time_obj = datetime.strptime(time_clean, '%H:%M')
        
        # Formater les coordonnées avec direction N/S et E/W
        lat_dir = 'N' if lat >= 0 else 'S'
        lon_dir = 'E' if lon >= 0 else 'W'
        lat_formatted = f"{abs(lat):.5f}".replace('.', 'D')
        lon_formatted = f"{abs(lon):.5f}".replace('.', 'D')
        
        # Générer le PlumID avec directions
        plumid = f"{date_obj.year:04d}_{date_obj.month:02d}_{date_obj.day:02d}_{time_obj.hour:02d}_{time_obj.minute:02d}_{lat_dir}_{lat_formatted}_{lon_dir}_{lon_formatted}"
        
        return plumid
    
    @staticmethod
    def parse_plumid(plumid: str) -> Tuple[str, str, float, float]:
        """
        Parse un PlumID pour extraire les données originales.
        
        Args:
            plumid: PlumID à parser
            
        Returns:
            Tuple (date, time, lat, lon)
        """
        parts = plumid.split('_')
        
        # Vérifier si c'est le nouveau format (avec directions) ou l'ancien format
        if len(parts) == 9:
            # Nouveau format: YYYY_MM_DD_HH_MM_LATDIR_LAT_LONDIR_LON
            year, month, day, hour, minute, lat_dir, lat_str, lon_dir, lon_str = parts
        elif len(parts) == 7:
            # Ancien format: YYYY_MM_DD_HH_MM_LAT_LON (longitude forcée négative)
            year, month, day, hour, minute, lat_str, lon_str = parts
            lat_dir = 'N'  # Par défaut Nord pour l'ancien format
            lon_dir = 'W'  # Longitude forcée Ouest dans l'ancien format
        else:
            raise ValueError(f"PlumID invalide: {plumid}")
        
        # Reconstruire la date et l'heure
        date = f"{year}-{month}-{day}"
        time = f"{hour}:{minute}"
        
        # Reconstruire les coordonnées avec les directions
        lat = float(lat_str.replace('D', '.')) * (1 if lat_dir == 'N' else -1)
        lon = float(lon_str.replace('D', '.')) * (1 if lon_dir == 'E' else -1)
        
        return date, time, lat, lon
    
    @staticmethod
    def validate_plumid(plumid: str) -> bool:
        """
        Valide le format d'un PlumID.
        
        Args:
            plumid: PlumID à valider
            
        Returns:
            True si valide, False sinon
        """
        try:
            PlumIDGenerator.parse_plumid(plumid)
            return True
        except (ValueError, IndexError):
            return False

# Test du générateur
if __name__ == "__main__":
    # Test avec les données de l'exemple
    test_plumid = PlumIDGenerator.generate_plumid(
        date="1998-12-22",
        time="10:13", 
        lat=42.35843,
        lon=-71.05977
    )
    
    print(f"PlumID généré: {test_plumid}")
    
    # Test de parsing
    parsed = PlumIDGenerator.parse_plumid(test_plumid)
    print(f"Données parsées: {parsed}")
    
    # Test de validation
    print(f"PlumID valide: {PlumIDGenerator.validate_plumid(test_plumid)}")
