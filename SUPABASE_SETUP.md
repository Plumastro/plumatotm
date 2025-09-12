# Configuration Supabase pour PLUMATOTM

## 1. Créer un projet Supabase

1. Allez sur [supabase.com](https://supabase.com)
2. Créez un compte ou connectez-vous
3. Créez un nouveau projet
4. Notez l'URL et la clé anonyme

## 2. Créer la table de base de données

Dans l'interface Supabase, allez dans l'éditeur SQL et exécutez :

```sql
-- Créer la table pour stocker les statistiques d'utilisation
CREATE TABLE IF NOT EXISTS plumastat_usage (
    plumid TEXT PRIMARY KEY,
    top1_animal TEXT NOT NULL,
    user_name TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Créer un index pour améliorer les performances
CREATE INDEX IF NOT EXISTS idx_plumastat_usage_top1_animal 
ON plumastat_usage(top1_animal);

-- Activer Row Level Security (RLS) pour la sécurité
ALTER TABLE plumastat_usage ENABLE ROW LEVEL SECURITY;

-- Créer une politique pour permettre la lecture et l'écriture
CREATE POLICY "Allow all operations on plumastat_usage" ON plumastat_usage
FOR ALL USING (true);
```

## 3. Configuration des variables d'environnement

Créez un fichier `.env` dans le répertoire racine avec :

```bash
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
```

## 4. Installation des dépendances

```bash
pip install supabase
```

## 5. Test de la configuration

Exécutez le test :

```bash
python supabase_manager.py
```

## 6. Structure de la table

| Colonne | Type | Description |
|---------|------|-------------|
| plumid | TEXT PRIMARY KEY | ID unique basé sur date/heure/location |
| top1_animal | TEXT | Animal totem principal de l'utilisateur |
| user_name | TEXT | Nom de l'utilisateur (optionnel) |
| created_at | TIMESTAMP | Date de création de l'enregistrement |
| updated_at | TIMESTAMP | Date de dernière mise à jour |

## 7. Exemple de données

```json
{
  "plumid": "1998_12_22_10_13_42D35843_71D05977",
  "top1_animal": "Penguin",
  "user_name": "Jean Dupont",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

## 8. Sécurité

- La table utilise Row Level Security (RLS)
- Les politiques permettent toutes les opérations (lecture/écriture)
- Pour la production, ajustez les politiques selon vos besoins

## 9. Monitoring

Vous pouvez surveiller l'utilisation dans l'interface Supabase :
- Onglet "Table Editor" pour voir les données
- Onglet "SQL Editor" pour des requêtes personnalisées
- Onglet "Logs" pour surveiller l'activité
