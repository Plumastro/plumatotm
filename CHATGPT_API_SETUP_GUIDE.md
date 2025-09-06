# Guide de Configuration de l'API ChatGPT pour PLUMATOTM

## Vue d'ensemble

Ce guide vous explique comment configurer l'API ChatGPT pour obtenir des interprétations automatiques des animaux totems basées sur l'analyse astrologique.

## Fonctionnalités

✅ **Interprétation automatique** : Le système génère automatiquement une interprétation expliquant pourquoi l'animal totem numéro 1 correspond à la personnalité du sujet

✅ **Informations complètes** : Inclut les positions des planètes dans les signes ET les maisons astrologiques

✅ **Format optimisé** : Prompt spécialement conçu pour obtenir des interprétations de qualité en français

✅ **Intégration transparente** : Fonctionne automatiquement lors de l'exécution de l'analyse principale

## Configuration requise

### 1. Obtenir une clé API OpenAI

1. **Créer un compte OpenAI** :
   - Allez sur [https://platform.openai.com/](https://platform.openai.com/)
   - Créez un compte ou connectez-vous

2. **Générer une clé API** :
   - Allez dans la section "API Keys" de votre dashboard
   - Cliquez sur "Create new secret key"
   - Copiez la clé générée (elle commence par `sk-`)

3. **Ajouter des crédits** :
   - Allez dans la section "Billing" 
   - Ajoutez des crédits à votre compte (minimum $5 recommandé)
   - Les interprétations coûtent environ $0.001-0.002 par analyse

### 2. Configuration de la variable d'environnement

#### Windows PowerShell
```powershell
$env:OPENAI_API_KEY='sk-votre-cle-api-ici'
```

#### Windows Command Prompt
```cmd
set OPENAI_API_KEY=sk-votre-cle-api-ici
```

#### Linux/Mac
```bash
export OPENAI_API_KEY='sk-votre-cle-api-ici'
```

### 3. Configuration permanente (optionnel)

#### Windows
1. Ouvrez "Paramètres système avancés"
2. Cliquez sur "Variables d'environnement"
3. Ajoutez une nouvelle variable système :
   - Nom : `OPENAI_API_KEY`
   - Valeur : `sk-votre-cle-api-ici`

#### Linux/Mac
Ajoutez à votre fichier `~/.bashrc` ou `~/.zshrc` :
```bash
export OPENAI_API_KEY='sk-votre-cle-api-ici'
```

## Utilisation

### Exécution automatique

L'interprétation ChatGPT est générée automatiquement lors de l'exécution de l'analyse principale :

```bash
python plumatotm_core.py --scores_json "plumatotm_raw_scores.json" --weights_csv "plumatotm_planets_weights.csv" --multipliers_csv "plumatotm_planets_multiplier.csv" --date 1991-09-01 --time 22:45 --lat 16.0167 --lon -61.7500
```

### Test de la fonctionnalité

Pour tester uniquement la génération de l'interprétation :

```bash
python test_chatgpt_interpretation.py
```

## Format de sortie

L'interprétation est sauvegardée dans `outputs/chatgpt_interpretation.json` :

```json
{
  "top1_animal": "Beaver",
  "true_planets": ["Sun", "Ascendant", "Moon", "Mars", "Uranus", "Neptune"],
  "interpretation": "• Vision perçante et lucidité intérieure : la Lune en Vierge, en lien avec Neptune et Uranus, donne une sensibilité fine et une capacité d'observer les détails invisibles aux autres. Comme le lynx, tu vois au-delà des apparences, tu débusques ce qui est caché, grâce à ton intuition alliée à une rigueur mentale.\n• Indépendance et force intérieure : le Soleil et Mercure en Bélier, soutenus par Mars en Lion et Jupiter en Sagittaire (Grand Trine de Feu), traduisent un tempérament audacieux, autonome et puissant. Le lynx incarne cette force solitaire, agile et confiante, avançant avec courage sans dépendre du groupe.\n• Discrétion stratégique et mystère : l'Ascendant Cancer allié à de fortes influences en Poissons (Vénus et Saturne sur le Milieu du Ciel) apporte une dimension plus subtile, parfois secrète, mais très magnétique. Comme le lynx qui apparaît soudain après une longue attente silencieuse, ta personnalité associe patience, mystère et capacité à frapper au moment juste.",
  "character_count": 798
}
```

## Exemple de prompt généré

Le système génère automatiquement un prompt détaillé incluant :

- **Thème de naissance complet** : Positions de toutes les planètes dans les signes
- **Planètes avec forte corrélation** : Les 6 planètes les plus importantes pour l'animal totem
- **Informations de maisons** : Position de chaque planète dans sa maison astrologique
- **Instructions spécifiques** : Format de réponse et style d'écriture

Exemple :
```
Tu es un astrologue expert spécialisé dans l'interprétation des thèmes de naissance et la compatibilité avec les animaux totems.

Basé sur le thème de naissance suivant et les planètes qui ont une forte corrélation avec l'animal totem, explique pourquoi l'animal "Beaver" correspond à la personnalité de cette personne.

THÈME DE NAISSANCE:
{
  "Sun": "VIRGO",
  "Ascendant": "TAURUS",
  "Moon": "TAURUS",
  ...
}

PLANÈTES AVEC FORTE CORRÉLATION POUR L'ANIMAL "Beaver":
Sun, Ascendant, Moon, Mars, Uranus, Neptune

Pour chaque planète marquée TRUE, voici son signe et sa maison dans le thème de naissance:
- Sun: VIRGO (Maison 4)
- Ascendant: TAURUS (Maison 1)
- Moon: TAURUS (Maison 1)
- Mars: VIRGO (Maison 5)
- Uranus: CAPRICORN (Maison 8)
- Neptune: CAPRICORN (Maison 8)

Écris une interprétation courte (environ 800 caractères au total) en 3 points bullet points expliquant pourquoi l'animal "Beaver" correspond à la personnalité de cette personne, en te basant sur les planètes, signes et maisons mentionnés ci-dessus.

Format de réponse souhaité:
• [explication basée sur une corrélation entre un élément du thème natal et l'archétype de l'animal]
• [explication basée sur une corrélation entre un autre élément du thème natal et l'archétype de l'animal]  
• [explication basée sur les traits caractéristiques de l'animal]

Sois précis, concis, tutoie l'interlocuteur comme si tu t'adressais directement à lui et utilise le vocabulaire astrologique approprié.
```

## Dépannage

### Erreur : "OPENAI_API_KEY environment variable not set"
- Vérifiez que la variable d'environnement est correctement définie
- Redémarrez votre terminal après avoir défini la variable
- Testez avec : `echo $env:OPENAI_API_KEY` (Windows) ou `echo $OPENAI_API_KEY` (Linux/Mac)

### Erreur : "Insufficient quota"
- Vérifiez que votre compte OpenAI a des crédits suffisants
- Allez sur [https://platform.openai.com/usage](https://platform.openai.com/usage) pour voir votre utilisation

### Erreur : "Invalid API key"
- Vérifiez que votre clé API est correcte
- Assurez-vous qu'elle commence par `sk-`
- Régénérez une nouvelle clé si nécessaire

### L'interprétation n'est pas générée
- Vérifiez les logs pour voir les messages d'erreur
- Assurez-vous que la bibliothèque `openai` est installée : `pip install openai>=1.0.0`
- Testez avec `python test_chatgpt_interpretation.py`

## Coûts estimés

- **Coût par interprétation** : ~$0.001-0.002
- **Modèle utilisé** : GPT-3.5-turbo
- **Tokens par requête** : ~500 tokens
- **Exemple de coût** : 1000 analyses = ~$1-2

## Sécurité

⚠️ **Important** : Ne partagez jamais votre clé API publiquement
- Ne l'incluez pas dans le code source
- Ne la commitez pas dans Git
- Utilisez toujours les variables d'environnement
- Régénérez la clé si elle est compromise

## Support

Pour toute question ou problème :
1. Vérifiez ce guide de dépannage
2. Consultez la documentation OpenAI : [https://platform.openai.com/docs](https://platform.openai.com/docs)
3. Testez avec `python test_chatgpt_interpretation.py` pour diagnostiquer les problèmes
