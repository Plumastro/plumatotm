#!/usr/bin/env python3
"""
Test de connexion à la base de données Supabase pour PLUMATOTM
Ce script teste spécifiquement les opérations d'insertion et de lecture.
"""

import os
import sys
from datetime import datetime

# Charger les variables d'environnement
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Variables d'environnement chargées depuis .env")
except ImportError:
    print("⚠️  python-dotenv non installé, utilisation des variables système")

def test_environment_variables():
    """Test des variables d'environnement"""
    print("\n🔍 Test des variables d'environnement...")
    
    url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    anon_key = os.getenv('SUPABASE_ANON_KEY')
    
    print(f"SUPABASE_URL: {'✅ Configuré' if url else '❌ Manquant'}")
    print(f"SUPABASE_SERVICE_ROLE_KEY: {'✅ Configuré' if service_key else '❌ Manquant'}")
    print(f"SUPABASE_ANON_KEY: {'✅ Configuré' if anon_key else '❌ Manquant'}")
    
    if not url:
        print("❌ SUPABASE_URL est requis")
        return False
    
    if not service_key and not anon_key:
        print("❌ Au moins une clé Supabase est requise (SUPABASE_SERVICE_ROLE_KEY ou SUPABASE_ANON_KEY)")
        return False
    
    print("✅ Variables d'environnement OK")
    return True

def test_supabase_import():
    """Test de l'import Supabase"""
    print("\n🔍 Test de l'import Supabase...")
    
    try:
        from supabase import create_client, Client
        print("✅ Module supabase importé avec succès")
        return True
    except ImportError as e:
        print(f"❌ Erreur d'import supabase: {e}")
        print("💡 Installez avec: pip install supabase")
        return False

def test_supabase_connection():
    """Test de la connexion Supabase"""
    print("\n🔍 Test de la connexion Supabase...")
    
    try:
        from supabase import create_client, Client
        
        url = os.getenv('SUPABASE_URL')
        service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        anon_key = os.getenv('SUPABASE_ANON_KEY')
        
        # Utiliser service role key en priorité
        key = service_key or anon_key
        
        if not url or not key:
            print("❌ URL ou clé manquante")
            return False
        
        # Créer le client
        client = create_client(url, key)
        print("✅ Client Supabase créé")
        
        # Test de connexion simple
        try:
            # Essayer une requête simple
            response = client.table('plumastat_usage').select('*').limit(1).execute()
            print("✅ Connexion à la base de données réussie")
            return True
        except Exception as e:
            print(f"❌ Erreur de connexion à la base: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur de création du client: {e}")
        return False

def test_database_operations():
    """Test des opérations de base de données"""
    print("\n🔍 Test des opérations de base de données...")
    
    try:
        from supabase import create_client, Client
        
        url = os.getenv('SUPABASE_URL')
        service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        anon_key = os.getenv('SUPABASE_ANON_KEY')
        key = service_key or anon_key
        
        client = create_client(url, key)
        
        # Test d'insertion
        test_plumid = f"TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        test_animal = "TestAnimal"
        test_name = "Test User"
        
        print(f"🧪 Test d'insertion: {test_plumid} -> {test_animal}")
        
        try:
            # Insérer un enregistrement de test
            insert_data = {
                'plumid': test_plumid,
                'top1_animal': test_animal,
                'user_name': test_name
            }
            
            response = client.table('plumastat_usage').insert(insert_data).execute()
            
            if response.data:
                print("✅ Insertion réussie")
                
                # Test de lecture
                print("🧪 Test de lecture...")
                read_response = client.table('plumastat_usage').select('*').eq('plumid', test_plumid).execute()
                
                if read_response.data and len(read_response.data) > 0:
                    retrieved_data = read_response.data[0]
                    if retrieved_data['top1_animal'] == test_animal:
                        print("✅ Lecture réussie")
                        
                        # Test de mise à jour
                        print("🧪 Test de mise à jour...")
                        update_data = {
                            'top1_animal': 'UpdatedTestAnimal',
                            'updated_at': 'NOW()'
                        }
                        
                        update_response = client.table('plumastat_usage').update(update_data).eq('plumid', test_plumid).execute()
                        
                        if update_response.data:
                            print("✅ Mise à jour réussie")
                            
                            # Vérifier la mise à jour
                            verify_response = client.table('plumastat_usage').select('top1_animal').eq('plumid', test_plumid).execute()
                            if verify_response.data and verify_response.data[0]['top1_animal'] == 'UpdatedTestAnimal':
                                print("✅ Vérification de mise à jour réussie")
                                return True
                            else:
                                print("❌ Vérification de mise à jour échouée")
                                return False
                        else:
                            print("❌ Mise à jour échouée")
                            return False
                    else:
                        print(f"❌ Données lues incorrectes: {retrieved_data['top1_animal']} != {test_animal}")
                        return False
                else:
                    print("❌ Lecture échouée - aucune donnée retournée")
                    return False
            else:
                print("❌ Insertion échouée - aucune donnée retournée")
                return False
                
        except Exception as e:
            print(f"❌ Erreur lors des opérations de base: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test des opérations: {e}")
        return False

def test_plumatotm_integration():
    """Test de l'intégration avec PLUMATOTM"""
    print("\n🔍 Test de l'intégration PLUMATOTM...")
    
    try:
        from supabase_manager import supabase_manager
        
        if not supabase_manager.is_available():
            print("❌ Supabase manager non disponible")
            return False
        
        print("✅ Supabase manager disponible")
        
        # Test avec le manager PLUMATOTM
        test_plumid = f"PLUMATOTM_TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        test_animal = "Penguin"
        test_name = "PLUMATOTM Test User"
        
        print(f"🧪 Test avec SupabaseManager: {test_plumid} -> {test_animal}")
        
        # Test d'ajout d'utilisateur
        success = supabase_manager.add_user(test_plumid, test_animal, test_name)
        
        if success:
            print("✅ Ajout d'utilisateur réussi")
            
            # Test de récupération
            retrieved_animal = supabase_manager.get_user_animal(test_plumid)
            
            if retrieved_animal == test_animal:
                print("✅ Récupération d'utilisateur réussie")
                
                # Test de mise à jour
                update_success = supabase_manager.update_user_animal(test_plumid, "UpdatedPenguin", test_name)
                
                if update_success:
                    print("✅ Mise à jour d'utilisateur réussie")
                    return True
                else:
                    print("❌ Mise à jour d'utilisateur échouée")
                    return False
            else:
                print(f"❌ Récupération incorrecte: {retrieved_animal} != {test_animal}")
                return False
        else:
            print("❌ Ajout d'utilisateur échoué")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test d'intégration: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🧪 Test de connexion à la base de données Supabase pour PLUMATOTM")
    print("=" * 70)
    
    tests = [
        ("Variables d'environnement", test_environment_variables),
        ("Import Supabase", test_supabase_import),
        ("Connexion Supabase", test_supabase_connection),
        ("Opérations de base de données", test_database_operations),
        ("Intégration PLUMATOTM", test_plumatotm_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erreur inattendue dans {test_name}: {e}")
            results.append((test_name, False))
    
    # Résumé des résultats
    print("\n" + "=" * 70)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 70)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ RÉUSSI" if result else "❌ ÉCHOUÉ"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nRésultat global: {passed}/{total} tests réussis")
    
    if passed == total:
        print("\n🎉 Tous les tests sont passés ! Votre API PLUMATOTM devrait maintenant fonctionner correctement.")
        return True
    else:
        print(f"\n💥 {total - passed} test(s) ont échoué. Vérifiez votre configuration Supabase.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
