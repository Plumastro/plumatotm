# 🎬 PLUMATOTM Animation Module (Optional)

Ce module **optionnel** permet de créer des animations GIF des graphiques radar. Il est séparé du moteur principal pour garder le projet léger.

## 📋 Prérequis

```bash
pip install matplotlib pillow numpy
```

## 🚀 Utilisation

### 1. Générer l'animation d'exemple
```bash
# Crée une animation d'exemple avec des données fictives
python plumatotm_animation.py
```

### 2. Utilisation programmatique
```python
from plumatotm_animation import AnimatedRadarGenerator

# Créer un générateur avec icônes personnalisées
generator = AnimatedRadarGenerator(icons_folder="icons")

# Créer une animation personnalisée
final_values = [85, 78, 92, 67, 45, 89, 34, 56, 23, 12, 78, 45, 67]
generator.create_animated_radar(
    final_values=final_values,
    animal_name="Fox",
    output_path="my_animation.gif",
    duration=5.0
)
```

## 📁 Fichiers générés

- `example_radar_animation.gif` - Animation d'exemple avec données fictives

## ⚙️ Paramètres

- **Durée** : 10 secondes par défaut (animation encore plus lente)
- **FPS** : 25 images par seconde
- **Résolution** : 1000x1000px
- **Format** : GIF optimisé avec loop parfait

## 🎯 Fonctionnalités

- ✅ **Séquence séquentielle** : Chaque planète monte une par une dans l'ordre (Soleil → Ascendant → Lune → Mercure → Vénus → Mars → Jupiter → Saturne → Uranus → Neptune → Pluton → Nœud Nord → MC)
- ✅ **Position initiale** : Tous les points commencent à 35%
- ✅ **Loop parfait** : Retour à 35% à la fin pour une boucle infinie
- ✅ **Contraintes respectées** : Soleil, Ascendant > 95%, Lune > 90%, Jupiter, Uranus, Neptune > 40%, tous les autres > 30%
- ✅ **Score dynamique** qui s'actualise en temps réel
- ✅ **Taille des points** basée sur l'importance astrologique
- ✅ **Icônes PNG** des planètes autour du graphique
- ✅ **Design identique** au radar chart statique
- ❌ Pas de révélation progressive
- ❌ Pas de pulsation
- ❌ Pas de traînée
- ❌ Pas de couleurs (noir et blanc uniquement)

## 📦 Intégration

Ce module est **complètement optionnel** :
- Le moteur principal fonctionne sans ce module
- Aucune dépendance supplémentaire pour le core
- Peut être installé séparément selon les besoins
- Parfait pour les démonstrations et présentations

## 🔧 Personnalisation

Pour modifier l'animation, éditez les paramètres dans `plumatotm_animation.py` :

```python
# Changer la durée
duration = 4.0  # secondes

# Changer le nombre de frames
frames = 80

# Changer la fonction d'easing
eased_progress = progress * progress * (3 - 2 * progress)  # Smooth step
```

## 📊 Exemple de sortie

L'animation montre une séquence séquentielle avec loop parfait :
1. **Position initiale** : Tous les points commencent à 35%
2. **Soleil monte** : Premier à atteindre sa position finale (96%)
3. **Ascendant monte** : Deuxième à atteindre sa position finale (97%)
4. **Lune monte** : Troisième à atteindre sa position finale (92%)
5. **Mercure monte** : Quatrième à atteindre sa position finale (67%)
6. **Vénus monte** : Cinquième à atteindre sa position finale (45%)
7. **Mars monte** : Sixième à atteindre sa position finale (89%)
8. **Jupiter monte** : Septième à atteindre sa position finale (45%)
9. **Saturne monte** : Huitième à atteindre sa position finale (56%)
10. **Uranus monte** : Neuvième à atteindre sa position finale (42%)
11. **Neptune monte** : Dixième à atteindre sa position finale (41%)
12. **Pluton monte** : Onzième à atteindre sa position finale (78%)
13. **Nœud Nord monte** : Douzième à atteindre sa position finale (45%)
14. **MC monte** : Dernier à atteindre sa position finale (67%)
15. **Retour à 35%** : Tous les points redescendent à 35% pour la boucle
16. **Score dynamique** : Le score total s'actualise en temps réel
17. **Icônes des planètes** : Affichées autour du graphique (sans cercle)

Parfait pour expliquer visuellement l'ordre d'importance des planètes en astrologie avec une boucle infinie !
