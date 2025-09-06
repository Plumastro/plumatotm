# ChatGPT Interpretation Feature

## Description

Cette fonctionnalité ajoute une interprétation automatique par ChatGPT expliquant pourquoi l'animal totem numéro 1 correspond à la personnalité du sujet, basée sur son thème de naissance astrologique.

## Fonctionnement

1. **Analyse des données** : Le système identifie l'animal totem numéro 1 et les 6 planètes qui ont une forte corrélation avec cet animal (marquées "TRUE" dans le fichier `top3_true_false.json`)

2. **Génération du prompt** : Un prompt détaillé est créé pour ChatGPT incluant :
   - Le thème de naissance complet (positions des planètes dans les signes)
   - Les planètes avec forte corrélation pour l'animal top1
   - Les combinaisons planète-signes spécifiques

3. **Interprétation ChatGPT** : ChatGPT génère une argumentation courte (environ 800 caractères) en 3 points bullet points expliquant la correspondance entre l'animal et la personnalité

4. **Sauvegarde** : Le résultat est sauvegardé dans `outputs/chatgpt_interpretation.json`

## Configuration requise

### 1. Installation des dépendances

```bash
pip install openai>=1.0.0
```

### 2. Configuration de l'API OpenAI

Définissez votre clé API OpenAI comme variable d'environnement :

```bash
# Linux/Mac
export OPENAI_API_KEY='your-openai-api-key-here'

# Windows PowerShell
$env:OPENAI_API_KEY='your-openai-api-key-here'

# Windows Command Prompt
set OPENAI_API_KEY=your-openai-api-key-here
```

## Utilisation

### Intégration automatique

La fonctionnalité est automatiquement intégrée dans le processus principal. Lorsque vous exécutez `plumatotm_core.py`, l'interprétation ChatGPT sera générée automatiquement si :
- La bibliothèque `openai` est installée
- La variable d'environnement `OPENAI_API_KEY` est définie

### Test manuel

Pour tester la fonctionnalité indépendamment :

```bash
python test_chatgpt_interpretation.py
```

## Format de sortie

Le fichier `outputs/chatgpt_interpretation.json` contient :

```json
{
  "top1_animal": "Nom de l'animal totem numéro 1",
  "true_planets": ["Planète1", "Planète2", "Planète3", "Planète4", "Planète5", "Planète6"],
  "interpretation": "• Point 1: [explication basée sur les planètes principales]\n• Point 2: [explication basée sur les aspects de personnalité]\n• Point 3: [explication basée sur les traits caractéristiques de l'animal]",
  "character_count": 800
}
```

## Gestion des erreurs

- Si la bibliothèque `openai` n'est pas installée : Avertissement affiché, fonctionnalité ignorée
- Si `OPENAI_API_KEY` n'est pas définie : Avertissement affiché, fonctionnalité ignorée
- Si l'API OpenAI échoue : Erreur capturée et affichée, processus principal continue

## Exemple de prompt généré

```
Tu es un astrologue expert spécialisé dans l'interprétation des thèmes de naissance et la compatibilité avec les animaux totems.

Basé sur le thème de naissance suivant et les planètes qui ont une forte corrélation avec l'animal totem, explique pourquoi l'animal "Bear" correspond à la personnalité de cette personne.

THÈME DE NAISSANCE:
{
  "Sun": "CANCER",
  "Ascendant": "CANCER",
  "Moon": "LEO",
  "Mercury": "CANCER",
  "Venus": "GEMINI",
  "Mars": "TAURUS",
  "Jupiter": "SCORPIO",
  "Saturn": "LEO",
  "Uranus": "GEMINI",
  "Neptune": "LIBRA",
  "Pluto": "LEO",
  "North Node": "GEMINI",
  "MC": "ARIES"
}

PLANÈTES AVEC FORTE CORRÉLATION POUR L'ANIMAL "Bear":
Sun, Ascendant, Moon, Mercury, Mars, Jupiter

Pour chaque planète marquée TRUE, voici son signe dans le thème de naissance:
- Sun: CANCER
- Ascendant: CANCER
- Moon: LEO
- Mercury: CANCER
- Mars: TAURUS
- Jupiter: SCORPIO

Écris une interprétation courte (environ 800 caractères au total) en 3 points bullet points expliquant pourquoi l'animal "Bear" correspond à la personnalité de cette personne, en te basant sur les planètes et signes mentionnés ci-dessus.

Format de réponse souhaité:
• Point 1: [explication basée sur les planètes principales]
• Point 2: [explication basée sur les aspects de personnalité]
• Point 3: [explication basée sur les traits caractéristiques de l'animal]

Sois précis, concis et utilise le vocabulaire astrologique approprié.
```

## Notes techniques

- **Modèle utilisé** : GPT-3.5-turbo
- **Tokens maximum** : 500
- **Température** : 0.7 (pour un bon équilibre créativité/précision)
- **Langue** : Français (prompt en français)
- **Format** : 3 points bullet points, environ 800 caractères total
