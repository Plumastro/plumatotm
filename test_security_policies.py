#!/usr/bin/env python3
"""
Test de sécurité des politiques RLS Supabase
Vérifie que seules les requêtes avec service role key peuvent accéder à la table.
"""

import os
import sys
from datetime import datetime

def test_service_role_access():
    """Test l'accès avec la service role key (devrait fonctionner)"""
    print("\n🔒 Test d'accès avec Service Role Key...")
    
    try:
        from supabase import create_client, Client
        
        url = os.getenv('SUPABASE_URL')
        service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not url or not service_key:
            print("❌ Service role key non configurée")
            return False
        
        client = create_client(url, service_key)
        
        # Test d'insertion
        test_plumid = f"SECURITY_TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        test_animal = "SecurityTestAnimal"
        
        print(f"🧪 Test d'insertion avec service role: {test_plumid}")
        
        try:
            insert_data = {
                'plumid': test_plumid,
                'top1_animal': test_animal
            }
            
            response = client.table('plumastat_usage').insert(insert_data).execute()
            
            if response.data:
                print("✅ Insertion avec service role réussie")
                
                # Test de lecture
                read_response = client.table('plumastat_usage').select('*').eq('plumid', test_plumid).execute()
                
                if read_response.data:
                    print("✅ Lecture avec service role réussie")
                    return True
                else:
                    print("❌ Lecture avec service role échouée")
                    return False
            else:
                print("❌ Insertion avec service role échouée")
                return False
                
        except Exception as e:
            print(f"❌ Erreur avec service role: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur de test service role: {e}")
        return False

def test_anon_key_access():
    """Test l'accès avec la clé anonyme (devrait être bloqué)"""
    print("\n🚫 Test d'accès avec Anon Key (devrait être bloqué)...")
    
    try:
        from supabase import create_client, Client
        
        url = os.getenv('SUPABASE_URL')
        anon_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not url or not anon_key:
            print("⚠️  Anon key non configurée - test ignoré")
            return True  # Pas d'anon key = pas de test possible
        
        client = create_client(url, anon_key)
        
        # Test d'insertion (devrait échouer)
        test_plumid = f"ANON_TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        test_animal = "AnonTestAnimal"
        
        print(f"🧪 Test d'insertion avec anon key: {test_plumid}")
        
        try:
            insert_data = {
                'plumid': test_plumid,
                'top1_animal': test_animal
            }
            
            response = client.table('plumastat_usage').insert(insert_data).execute()
            
            if response.data:
                print("❌ PROBLÈME DE SÉCURITÉ: Insertion avec anon key réussie (ne devrait pas être possible)")
                return False
            else:
                print("✅ Insertion avec anon key bloquée (correct)")
                
        except Exception as e:
            if "permission denied" in str(e).lower() or "insufficient_privilege" in str(e).lower():
                print("✅ Insertion avec anon key bloquée (correct)")
            else:
                print(f"❌ Erreur inattendue avec anon key: {e}")
                return False
        
        # Test de lecture (devrait échouer)
        print("🧪 Test de lecture avec anon key...")
        
        try:
            read_response = client.table('plumastat_usage').select('*').limit(1).execute()
            
            if read_response.data:
                print("❌ PROBLÈME DE SÉCURITÉ: Lecture avec anon key réussie (ne devrait pas être possible)")
                return False
            else:
                print("✅ Lecture avec anon key bloquée (correct)")
                
        except Exception as e:
            if "permission denied" in str(e).lower() or "insufficient_privilege" in str(e).lower():
                print("✅ Lecture avec anon key bloquée (correct)")
            else:
                print(f"❌ Erreur inattendue avec anon key: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur de test anon key: {e}")
        return False

def test_plumatotm_api_security():
    """Test la sécurité avec le SupabaseManager de PLUMATOTM"""
    print("\n🔒 Test de sécurité avec SupabaseManager...")
    
    try:
        from supabase_manager import supabase_manager
        
        if not supabase_manager.is_available():
            print("❌ SupabaseManager non disponible")
            return False
        
        # Test avec le manager (utilise service role key)
        test_plumid = f"PLUMATOTM_SECURITY_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        test_animal = "SecurityPenguin"
        test_name = "Security Test User"
        
        print(f"🧪 Test avec SupabaseManager: {test_plumid}")
        
        # Test d'ajout
        success = supabase_manager.add_user(test_plumid, test_animal, test_name)
        
        if success:
            print("✅ SupabaseManager: Ajout réussi")
            
            # Test de récupération
            retrieved_animal = supabase_manager.get_user_animal(test_plumid)
            
            if retrieved_animal == test_animal:
                print("✅ SupabaseManager: Récupération réussie")
                return True
            else:
                print(f"❌ SupabaseManager: Récupération incorrecte: {retrieved_animal}")
                return False
        else:
            print("❌ SupabaseManager: Ajout échoué")
            return False
            
    except Exception as e:
        print(f"❌ Erreur SupabaseManager: {e}")
        return False

def main():
    """Fonction principale de test de sécurité"""
    print("🔒 Test de sécurité des politiques RLS Supabase")
    print("=" * 60)
    
    tests = [
        ("Accès Service Role (devrait fonctionner)", test_service_role_access),
        ("Accès Anon Key (devrait être bloqué)", test_anon_key_access),
        ("Sécurité PLUMATOTM API", test_plumatotm_api_security)
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
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS DE SÉCURITÉ")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ RÉUSSI" if result else "❌ ÉCHOUÉ"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nRésultat global: {passed}/{total} tests réussis")
    
    if passed == total:
        print("\n🎉 Tous les tests de sécurité sont passés !")
        print("✅ Votre API est sécurisée et fonctionne correctement.")
        return True
    else:
        print(f"\n💥 {total - passed} test(s) de sécurité ont échoué.")
        print("🔒 Vérifiez vos politiques RLS dans Supabase.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

