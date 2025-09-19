# 🛡️ Workflow de Développement Sécurisé - PLUMATOTM

## 📋 Vue d'Ensemble

Ce guide vous explique comment travailler en toute sécurité sur PLUMATOTM sans risquer d'endommager la version de production déployée.

## 🌳 Structure des Branches

```
main (production) ← Version stable déployée
├── production-backup ← Sauvegarde de la version actuelle
└── development ← Branche de travail pour les modifications
```

## 🔄 Workflow de Développement

### 1. **Branche de Production (`main`)**
- ✅ **Version stable** déployée sur Render
- ✅ **Ne jamais modifier directement**
- ✅ **Seulement pour les merges validés**

### 2. **Branche de Sauvegarde (`production-backup`)**
- 🛡️ **Sauvegarde** de l'état actuel de production
- 🛡️ **Point de retour** en cas de problème
- 🛡️ **Ne jamais modifier**

### 3. **Branche de Développement (`development`)**
- 🔧 **Branche de travail** pour toutes les modifications
- 🔧 **Tests et expérimentations**
- 🔧 **Développement de nouvelles fonctionnalités**

## 🚀 Commandes de Base

### **Basculer sur la branche de développement**
```bash
git checkout development
```

### **Basculer sur la branche de production**
```bash
git checkout main
```

### **Voir toutes les branches**
```bash
git branch -a
```

### **Voir l'état actuel**
```bash
git status
```

## 📝 Workflow de Modification

### **Étape 1: Basculer sur development**
```bash
git checkout development
```

### **Étape 2: Faire vos modifications**
- Modifiez les fichiers nécessaires
- Testez vos changements localement

### **Étape 3: Commiter vos changements**
```bash
git add .
git commit -m "🔧 Description de vos modifications"
```

### **Étape 4: Pousser vers GitHub**
```bash
git push origin development
```

### **Étape 5: Tester sur la branche development**
- Créez un déploiement de test sur Render (optionnel)
- Testez toutes les fonctionnalités

### **Étape 6: Merger vers production (quand prêt)**
```bash
# Basculer sur main
git checkout main

# Merger development dans main
git merge development

# Pousser vers production
git push origin main
```

## 🛡️ Règles de Sécurité

### ✅ **À FAIRE**
- Toujours travailler sur la branche `development`
- Tester toutes les modifications avant de merger
- Commiter régulièrement avec des messages clairs
- Garder la branche `production-backup` intacte

### ❌ **À ÉVITER**
- Ne jamais modifier directement la branche `main`
- Ne jamais supprimer la branche `production-backup`
- Ne jamais merger sans avoir testé
- Ne jamais pousser du code non testé

## 🔧 Configuration de l'Environnement de Développement

### **Variables d'Environnement de Test**
Créez un fichier `.env.development` pour vos tests :

```bash
# Configuration de développement
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key

# Base de données de test (optionnel)
SUPABASE_TEST_TABLE=plumastat_usage_test
```

### **Scripts de Test**
```bash
# Test de la base de données
python test_database_connection.py

# Test de sécurité
python test_security_policies.py

# Test de l'API complète
python test_api.py
```

## 🚨 En Cas de Problème

### **Retour à la version stable**
```bash
# Basculer sur la sauvegarde
git checkout production-backup

# Créer une nouvelle branche de développement
git checkout -b development-fix

# Travailler sur les corrections
```

### **Annuler des modifications**
```bash
# Annuler les modifications non commitées
git checkout -- .

# Annuler le dernier commit (garder les modifications)
git reset --soft HEAD~1

# Annuler le dernier commit (supprimer les modifications)
git reset --hard HEAD~1
```

## 📊 Monitoring et Tests

### **Tests Automatiques**
- Exécutez `test_database_connection.py` avant chaque commit
- Exécutez `test_security_policies.py` après chaque modification de sécurité
- Testez l'API complète avec des données réelles

### **Vérifications Avant Merge**
- [ ] Tous les tests passent
- [ ] Aucune erreur de linting
- [ ] Documentation mise à jour
- [ ] Variables d'environnement vérifiées

## 🔄 Cycle de Développement Recommandé

1. **Développement** sur `development`
2. **Tests** locaux complets
3. **Commit** avec message descriptif
4. **Push** vers GitHub
5. **Tests** supplémentaires (optionnel)
6. **Merge** vers `main` quand prêt
7. **Déploiement** automatique sur Render

## 📞 Support

En cas de problème :
1. Vérifiez que vous êtes sur la bonne branche
2. Consultez les logs Git : `git log --oneline`
3. Utilisez la branche `production-backup` comme point de retour
4. Testez toujours avant de merger

---

**🎯 Objectif : Développer en toute sécurité sans risquer la version de production !**
