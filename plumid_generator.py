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
        
        Format: YYYY_MM_DD_HH_MM_LAT_LON
        
        Args:
            date: Date de naissance (format: YYYY-MM-DD)
            time: Heure de naissance locale (format: HH:MM en 24h)
            lat: Latitude
            lon: Longitude
            
        Returns:
            PlumID unique
        """
        # Parse la date
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        
        # Parse l'heure (format 24h uniquement)
        time_clean = time.strip()
        time_obj = datetime.strptime(time_clean, '%H:%M')
        
        # Formater les coordonnées (arrondir à 5 décimales pour éviter les variations mineures)
        # Utiliser un format plus simple pour éviter les problèmes de parsing
        lat_formatted = f"{lat:.5f}".replace('.', 'D')
        lon_formatted = f"{abs(lon):.5f}".replace('.', 'D')
        
        # Générer le PlumID
        plumid = f"{date_obj.year:04d}_{date_obj.month:02d}_{date_obj.day:02d}_{time_obj.hour:02d}_{time_obj.minute:02d}_{lat_formatted}_{lon_formatted}"
        
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
        
        if len(parts) < 7:
            raise ValueError(f"PlumID invalide: {plumid}")
        
        # Extraire les composants (les coordonnées peuvent avoir plusieurs parties)
        year, month, day, hour, minute = parts[:5]
        lat_str = parts[5]
        lon_str = parts[6]
        
        # Reconstruire la date et l'heure
        date = f"{year}-{month}-{day}"
        time = f"{hour}:{minute}"
        
        # Reconstruire les coordonnées
        lat = float(lat_str.replace('D', '.'))
        lon = -float(lon_str.replace('D', '.'))
        
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
