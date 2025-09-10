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

- `score_axis_animation.gif` - Animation du point qui monte et descend sur l'axe (Soleil)
- `weight_axis_animation.gif` - Animation du poids (diamètre) du point à position fixe (Jupiter)

## ⚙️ Paramètres

- **Durée** : 3.5 secondes
- **FPS** : 30 images par seconde
- **Résolution** : 1000x1000px (120 DPI)
- **Format** : GIF optimisé avec loop parfait

## 🎯 Fonctionnalités

### Score Axis Animation (Soleil)
- ✅ **Animation de score** : Point qui monte et descend sur l'axe
- ✅ **Mouvement fluide** : 20% → 92% → 20%
- ✅ **Icône PNG** du Soleil au-dessus de la ligne
- ✅ **Animation très lisse** avec courbe d'easing (plus lent aux extrémités, plus rapide au milieu)

### Weight Axis Animation (Jupiter)
- ✅ **Animation de poids** : Point à position fixe (80%) avec diamètre variable
- ✅ **Diamètre variable** : Petit → Très gros → Petit (plus gros que le Soleil)
- ✅ **Icône PNG** de Jupiter au-dessus de la ligne
- ✅ **Animation très lisse** avec courbe d'easing sur le diamètre
- ✅ **Loop parfait** : Retour au diamètre initial pour boucle infinie

### Caractéristiques communes
- ✅ **Loop parfait** : Boucle infinie
- ✅ **Pas de score** affiché
- ✅ **Pas de cercle** autour du graphique
- ✅ **Haute résolution** (120 DPI) pour des traits très propres

## 📊 Exemple de sortie

### Score Axis Animation
1. **Position initiale** : Soleil à 20%
2. **Montée** : Soleil monte jusqu'à 92% (plus lent au début et à la fin, plus rapide au milieu)
3. **Descente** : Soleil redescend à 20% (plus lent au début et à la fin, plus rapide au milieu)
4. **Loop** : L'animation recommence

### Weight Axis Animation
1. **Position fixe** : Jupiter à 80% sur l'axe
2. **Croissance** : Le diamètre du point grandit (plus lent au début et à la fin, plus rapide au milieu)
3. **Décroissance** : Le diamètre du point diminue (plus lent au début et à la fin, plus rapide au milieu)
4. **Loop** : L'animation recommence avec le diamètre initial

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
duration = 4.0  # secondes

# Changer les valeurs
current_value = 20.0 + (92.0 - 20.0) * eased_progress  # 20% à 92%

# Changer la résolution
anim.save(output_path, writer=writer, dpi=150)  # DPI plus élevé

# Changer la taille de la figure
fig, ax = plt.subplots(figsize=(12, 12), subplot_kw=dict(projection='polar'))

# Changer la planète (modifier sun_angle et l'icône)
sun_angle = 0  # 0° = haut, 90° = droite, 180° = bas, 270° = gauche
```

## 🎨 Utilisation des icônes

Le module utilise automatiquement les icônes PNG du dossier `icons/` si disponible :
- `sun.png` pour le Soleil
- Sinon utilise le symbole Unicode ☉

Parfait pour des animations simples et élégantes !
