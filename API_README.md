# PLUMATOTM API Documentation

## 🚀 API Web Service

Cette API expose le moteur d'analyse astrologique PLUMATOTM via HTTP.

## 📡 Endpoints

### `GET /`
**Description :** Informations sur l'API  
**Réponse :**
```json
{
  "service": "PLUMATOTM Astrological Animal Compatibility Engine",
  "version": "1.0.0",
  "status": "running",
  "endpoints": {
    "POST /analyze": "Run full astrological analysis",
    "GET /health": "Health check",
    "GET /": "This information"
  }
}
```

### `GET /health`
**Description :** Vérification de l'état de l'API  
**Réponse :**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00",
  "analyzer_ready": true
}
```

### `POST /analyze`
**Description :** Lance une analyse astrologique complète  
**Body (JSON) :**
```json
{
  "date": "1998-12-22",
  "time": "10:13",
  "lat": 42.35843,
  "lon": -71.05977,
  "openai_api_key": "sk-..." // optionnel
}
```

**Paramètres :**
- `date` (requis) : Date de naissance au format YYYY-MM-DD
- `time` (requis) : Heure de naissance au format HH:MM (24h)
- `lat` (requis) : Latitude (-90 à 90)
- `lon` (requis) : Longitude (-180 à 180)
- `openai_api_key` (optionnel) : Clé API OpenAI pour l'interprétation ChatGPT

**Réponse de succès :**
```json
{
  "status": "success",
  "message": "Analysis completed successfully",
  "timestamp": "2024-01-15T10:30:00",
  "input": {
    "date": "1998-12-22",
    "time": "10:13",
    "lat": 42.35843,
    "lon": -71.05977
  },
  "output_files": [
    "birth_chart.json",
    "animal_totals.json",
    "top3_percentage_strength.json",
    "animal_proportion.json",
    "chatgpt_interpretation.json",
    "top1_animal_radar.png",
    "top2_animal_radar.png",
    "top3_animal_radar.png"
  ]
}
```

### `GET /files`
**Description :** Liste les fichiers de sortie disponibles  
**Réponse :**
```json
{
  "files": ["birth_chart.json", "animal_totals.json", ...],
  "count": 8
}
```

### `GET /files/<filename>`
**Description :** Télécharge un fichier de sortie spécifique  
**Paramètres :**
- `filename` : Nom du fichier (ex: `birth_chart.json`, `top1_animal_radar.png`)

## 🔧 Configuration Render

### Build Command
```bash
pip install -r requirements.txt
```

### Start Command
```bash
python app.py
```

### Variables d'environnement
```
OPENAI_API_KEY=sk-proj-...
SUPABASE_URL=https://...
SUPABASE_ANON_KEY=eyJ...
```

## 🧪 Test local

```bash
# Démarrer l'API
python app.py

# Tester l'API
python test_api.py
```

## 📊 Exemple d'utilisation

```python
import requests

# Analyser un thème astral
response = requests.post("https://your-app.onrender.com/analyze", json={
    "date": "1998-12-22",
    "time": "10:13", 
    "lat": 42.35843,
    "lon": -71.05977
})

result = response.json()
print(f"Status: {result['status']}")

# Télécharger un fichier de sortie
if result['status'] == 'success':
    birth_chart = requests.get("https://your-app.onrender.com/files/birth_chart.json")
    print(birth_chart.json())
```

## 🎯 Fonctionnalités

- ✅ Analyse astrologique complète
- ✅ Génération de graphiques radar (PNG)
- ✅ Interprétation ChatGPT (optionnelle)
- ✅ Statistiques d'animaux avec Supabase
- ✅ Thème astral en français
- ✅ Métriques de force globale
- ✅ API RESTful simple
