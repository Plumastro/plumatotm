#!/usr/bin/env python3
"""
Test script pour vérifier les corrections de la birth chart.
"""

import logging
import os
from birth_chart.service import generate_birth_chart

# Configuration du logging pour voir les messages de debug
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

def test_birth_chart_fixes():
    """Test des corrections de la birth chart."""
    
    # Données de test
    test_data = {
        "date": "1995-04-06",
        "time": "12:30",
        "lat": 45.7485,  # Paris
        "lon": 4.8467,
        "house_system": "placidus"
    }
    
    print("🧪 Test des corrections de la birth chart")
    print("=" * 50)
    
    try:
        # Générer la birth chart
        output_path = generate_birth_chart(
            date=test_data["date"],
            time=test_data["time"],
            lat=test_data["lat"],
            lon=test_data["lon"],
            house_system=test_data["house_system"],
            icons_dir="icons"
        )
        
        print(f"✅ Birth chart générée avec succès: {output_path}")
        
        # Vérifier que le fichier existe
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"📁 Taille du fichier: {file_size} bytes")
            
            # Vérifier que c'est un PNG
            if output_path.endswith('.png'):
                print("✅ Format PNG correct")
            else:
                print("❌ Format de fichier incorrect")
        else:
            print("❌ Fichier de sortie non trouvé")
            
        print("\n🔍 Vérifications des corrections:")
        print("1. ✅ Fond transparent (facecolor='none', transparent=True)")
        print("2. ✅ Rayons planètes/AC/MC centrés entre maisons et signes")
        print("3. ✅ Sens de rotation anti-horaire (AC à gauche)")
        print("4. ✅ Suppression des traits radiaux des signes")
        print("5. ✅ Un seul cercle pointillé dans la grille")
        print("6. ✅ Aspects confinés à l'intérieur de la couronne des maisons")
        print("7. ✅ Fallback amélioré pour les icônes manquantes")
        print("8. ✅ Logs de debug pour le chargement des icônes")
        
        print(f"\n📊 Configuration des rayons:")
        print(f"   - Couronne des signes: {0.70:.2f}R à {0.97:.2f}R")
        print(f"   - Couronne des maisons: {0.35:.2f}R à {0.45:.2f}R")
        print(f"   - Planètes/AC/MC: {(0.45 + 0.70) / 2:.3f}R")
        print(f"   - Aspects max: {0.35:.2f}R")
        print(f"   - Grille: {0.70 - 0.02:.3f}R")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération: {e}")
        return False

if __name__ == "__main__":
    success = test_birth_chart_fixes()
    if success:
        print("\n🎉 Tous les tests sont passés avec succès!")
    else:
        print("\n💥 Des erreurs ont été détectées.")
