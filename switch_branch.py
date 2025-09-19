#!/usr/bin/env python3
"""
Script de basculement entre les branches PLUMATOTM
Facilite le passage entre production et développement
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Exécute une commande Git et affiche le résultat"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} réussi")
            if result.stdout.strip():
                print(f"   {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description} échoué")
            if result.stderr.strip():
                print(f"   Erreur: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ Erreur lors de {description}: {e}")
        return False

def get_current_branch():
    """Récupère la branche actuelle"""
    try:
        result = subprocess.run("git branch --show-current", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except:
        return None

def show_status():
    """Affiche le statut actuel"""
    print("\n📊 STATUT ACTUEL")
    print("=" * 50)
    
    current_branch = get_current_branch()
    print(f"Branche actuelle: {current_branch}")
    
    # Afficher les branches disponibles
    run_command("git branch -a", "Liste des branches")
    
    # Afficher le statut Git
    run_command("git status --porcelain", "Modifications en cours")

def switch_to_development():
    """Bascule vers la branche de développement"""
    print("\n🔧 BASCULEMENT VERS DÉVELOPPEMENT")
    print("=" * 50)
    
    # Vérifier s'il y a des modifications non commitées
    result = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True)
    if result.stdout.strip():
        print("⚠️  Modifications non commitées détectées")
        choice = input("Voulez-vous les commiter avant de basculer ? (y/n): ").lower()
        if choice == 'y':
            message = input("Message de commit: ") or "🔧 Modifications avant basculement"
            if not run_command(f'git add . && git commit -m "{message}"', "Commit des modifications"):
                return False
    
    # Basculer vers development
    if run_command("git checkout development", "Basculement vers development"):
        print("✅ Vous êtes maintenant sur la branche de développement")
        print("💡 Vous pouvez maintenant faire vos modifications en toute sécurité")
        return True
    return False

def switch_to_production():
    """Bascule vers la branche de production"""
    print("\n🏭 BASCULEMENT VERS PRODUCTION")
    print("=" * 50)
    
    # Vérifier s'il y a des modifications non commitées
    result = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True)
    if result.stdout.strip():
        print("⚠️  Modifications non commitées détectées")
        choice = input("Voulez-vous les commiter avant de basculer ? (y/n): ").lower()
        if choice == 'y':
            message = input("Message de commit: ") or "🔧 Modifications avant basculement"
            if not run_command(f'git add . && git commit -m "{message}"', "Commit des modifications"):
                return False
    
    # Basculer vers main
    if run_command("git checkout main", "Basculement vers main"):
        print("✅ Vous êtes maintenant sur la branche de production")
        print("⚠️  ATTENTION: Ne modifiez pas directement cette branche !")
        return True
    return False

def switch_to_backup():
    """Bascule vers la branche de sauvegarde"""
    print("\n🛡️ BASCULEMENT VERS SAUVEGARDE")
    print("=" * 50)
    
    if run_command("git checkout production-backup", "Basculement vers production-backup"):
        print("✅ Vous êtes maintenant sur la branche de sauvegarde")
        print("🛡️ Cette branche contient une sauvegarde de la version stable")
        return True
    return False

def create_new_development_branch():
    """Crée une nouvelle branche de développement"""
    print("\n🆕 CRÉATION D'UNE NOUVELLE BRANCHE DE DÉVELOPPEMENT")
    print("=" * 50)
    
    branch_name = input("Nom de la nouvelle branche (ex: feature-nouvelle-fonctionnalite): ")
    if not branch_name:
        print("❌ Nom de branche requis")
        return False
    
    if run_command(f"git checkout -b {branch_name}", f"Création de la branche {branch_name}"):
        print(f"✅ Nouvelle branche '{branch_name}' créée et activée")
        return True
    return False

def show_help():
    """Affiche l'aide"""
    print("\n📖 AIDE - SCRIPT DE BASCULEMENT DE BRANCHES")
    print("=" * 60)
    print("Ce script vous aide à basculer entre les branches PLUMATOTM en toute sécurité.")
    print()
    print("Branches disponibles:")
    print("  🏭 main (production) - Version stable déployée")
    print("  🔧 development - Branche de travail pour les modifications")
    print("  🛡️ production-backup - Sauvegarde de la version stable")
    print()
    print("Commandes:")
    print("  1 - Basculer vers développement")
    print("  2 - Basculer vers production")
    print("  3 - Basculer vers sauvegarde")
    print("  4 - Créer une nouvelle branche")
    print("  5 - Afficher le statut")
    print("  6 - Aide")
    print("  0 - Quitter")
    print()
    print("💡 Conseil: Travaillez toujours sur 'development' pour éviter d'endommager la production")

def main():
    """Fonction principale"""
    print("🔄 SCRIPT DE BASCULEMENT DE BRANCHES PLUMATOTM")
    print("=" * 60)
    
    while True:
        print("\nQue voulez-vous faire ?")
        print("1 - Basculer vers développement")
        print("2 - Basculer vers production")
        print("3 - Basculer vers sauvegarde")
        print("4 - Créer une nouvelle branche")
        print("5 - Afficher le statut")
        print("6 - Aide")
        print("0 - Quitter")
        
        choice = input("\nVotre choix (0-6): ").strip()
        
        if choice == '1':
            switch_to_development()
        elif choice == '2':
            switch_to_production()
        elif choice == '3':
            switch_to_backup()
        elif choice == '4':
            create_new_development_branch()
        elif choice == '5':
            show_status()
        elif choice == '6':
            show_help()
        elif choice == '0':
            print("👋 Au revoir !")
            break
        else:
            print("❌ Choix invalide. Veuillez choisir entre 0 et 6.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Script interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        sys.exit(1)
