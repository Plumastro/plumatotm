# 🌞 Single Axis Animation Generator (Optional Module)

Ce module **complètement séparé** permet de créer des animations simples d'une seule planète sur son axe.

## ⚠️ IMPORTANT - SÉPARATION TOTALE

- **AUCUN IMPACT** sur le moteur principal
- **AUCUN IMPACT** sur l'API
- **AUCUN IMPACT** sur les calculs astrologiques
- Module **complètement indépendant**

## 📋 Prérequis

```bash
pip install matplotlib pillow numpy
```

## 🚀 Utilisation

```bash
python single_axis_animation.py
```

## 📁 Fichiers générés

- `sun_axis_animation.gif` - Animation simple du Soleil sur son axe

## ⚙️ Paramètres

- **Durée** : 5 secondes
- **FPS** : 30 images par seconde
- **Résolution** : 800x800px
- **Format** : GIF optimisé avec loop parfait

## 🎯 Fonctionnalités

- ✅ **Animation simple** : Une seule planète (Soleil) sur son axe
- ✅ **Mouvement fluide** : 20% → 92% → 20%
- ✅ **Loop parfait** : Boucle infinie
- ✅ **Icône PNG** du Soleil au-dessus de la ligne
- ✅ **Pas de score** affiché
- ✅ **Animation très lisse** avec courbe sinusoïdale (plus lent aux extrémités, plus rapide au milieu)
- ✅ **Pas de cercle** autour du graphique

## 📊 Exemple de sortie

L'animation montre :
1. **Position initiale** : Soleil à 20%
2. **Montée** : Soleil monte doucement jusqu'à 92% (plus lent au début et à la fin)
3. **Descente** : Soleil redescend doucement à 20% (plus lent au début et à la fin)
4. **Loop** : L'animation recommence

## 📦 Intégration

Ce module est **complètement optionnel** :
- Le moteur principal fonctionne sans ce module
- Aucune dépendance supplémentaire pour le core
- Peut être installé séparément selon les besoins
- Parfait pour des démonstrations simples

## 🔧 Personnalisation

Pour modifier l'animation, éditez les paramètres dans `single_axis_animation.py` :

```python
# Changer la durée
duration = 6.0  # secondes

# Changer les valeurs
current_value = 20.0 + (92.0 - 20.0) * eased_progress  # 20% à 92%

# Changer la planète (modifier sun_angle et l'icône)
sun_angle = 0  # 0° = haut, 90° = droite, 180° = bas, 270° = gauche
```

## 🎨 Utilisation des icônes

Le module utilise automatiquement les icônes PNG du dossier `icons/` si disponible :
- `sun.png` pour le Soleil
- Sinon utilise le symbole Unicode ☉

Parfait pour des animations simples et élégantes !
