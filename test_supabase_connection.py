#!/usr/bin/env python3
"""
Test de connexion Supabase pour vérifier la configuration
"""

import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from supabase_manager import SupabaseManager
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def test_supabase_connection():
    """Test de connexion et d'insertion Supabase."""
    print("[TEST] Test de connexion Supabase...")
    print("=" * 50)
    
    # Créer le gestionnaire
    manager = SupabaseManager()
    
    # Vérifier la connexion
    if not manager.is_available():
        print("[FAILED] Supabase non disponible")
        return False
    
    print("[SUCCESS] Connexion Supabase OK")
    
    # Tester l'insertion d'un utilisateur de test
    test_plumid = "test_connection_123"
    test_animal = "Test Animal"
    test_name = "Test User"
    
    print(f"\n[TEST] Tentative d'insertion...")
    print(f"   PlumID: {test_plumid}")
    print(f"   Animal: {test_animal}")
    print(f"   Nom: {test_name}")
    
    # Essayer d'ajouter l'utilisateur
    success = manager.add_user(
        plumid=test_plumid,
        top1_animal=test_animal,
        user_name=test_name
    )
    
    if success:
        print("[SUCCESS] Insertion réussie !")
        
        # Nettoyer le test
        print("\n[TEST] Nettoyage du test...")
        try:
            manager.delete_user(test_plumid)
            print("[SUCCESS] Test nettoyé")
        except:
            print("[WARNING] Nettoyage échoué (normal)")
        
        return True
    else:
        print("[FAILED] Insertion échouée")
        print("\n[SOLUTION] Exécutez le script SQL dans Supabase :")
        print("   1. Allez dans l'éditeur SQL de Supabase")
        print("   2. Exécutez le contenu de fix_supabase_rls.sql")
        print("   3. Relancez ce test")
        return False

def main():
    """Fonction principale."""
    print("[TEST] TEST DE CONNEXION SUPABASE")
    print("=" * 50)
    
    success = test_supabase_connection()
    
    if success:
        print("\n[SUCCESS] Supabase est prêt pour les 1000 profils !")
    else:
        print("\n[FAILED] Problème de configuration Supabase")
        print("   Consultez fix_supabase_rls.sql pour la solution")

if __name__ == "__main__":
    main()