#!/usr/bin/env python3
"""
Test de connexion Supabase pour PLUMATOTM
"""

from supabase_manager import supabase_manager
from supabase_config import supabase_config

def test_supabase_connection():
    """Test la connexion Supabase"""
    print("🧪 Test de connexion Supabase...")
    
    # Vérifier la configuration
    print(f"✅ URL configurée: {bool(supabase_config.url)}")
    print(f"✅ Clé configurée: {bool(supabase_config.key)}")
    print(f"✅ Table: {supabase_config.table_name}")
    
    if not supabase_config.is_configured():
        print("❌ Supabase non configuré")
        print("   Configurez SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY")
        return False
    
    # Tester la connexion
    if not supabase_manager.is_available():
        print("❌ Gestionnaire Supabase non disponible")
        return False
    
    print("✅ Gestionnaire Supabase disponible")
    
    # Test d'insertion
    test_plumid = "TEST_12345"
    test_animal = "TestAnimal"
    
    print(f"🧪 Test d'insertion: {test_plumid} -> {test_animal}")
    
    try:
        # Essayer d'ajouter un utilisateur de test
        success = supabase_manager.add_user(test_plumid, test_animal, "Test User")
        
        if success:
            print("✅ Insertion réussie")
            
            # Tester la récupération
            print("🧪 Test de récupération...")
            retrieved_animal = supabase_manager.get_user_animal(test_plumid)
            
            if retrieved_animal == test_animal:
                print("✅ Récupération réussie")
                
                # Nettoyer le test
                print("🧹 Nettoyage du test...")
                # Note: Pas de méthode de suppression dans le code actuel
                print("ℹ️  L'utilisateur de test reste dans la base (normal)")
                
                return True
            else:
                print(f"❌ Récupération échouée: {retrieved_animal} != {test_animal}")
                return False
        else:
            print("❌ Insertion échouée")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

if __name__ == "__main__":
    success = test_supabase_connection()
    
    if success:
        print("\n🎉 Test Supabase réussi ! Votre API devrait maintenant fonctionner.")
    else:
        print("\n💥 Test Supabase échoué. Vérifiez votre configuration.")
