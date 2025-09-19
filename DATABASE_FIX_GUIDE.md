# 🚨 Guide de Correction - Problème de Base de Données Supabase

## Problème Identifié
Votre API PLUMATOTM ne peut pas se connecter à la base de données Supabase `plumastat_usage` à cause de problèmes de configuration.

## Solutions Immédiates

### 1. 🔑 Configuration des Clés Supabase

**Problème**: Votre code cherche `SUPABASE_SERVICE_ROLE_KEY` mais vous n'avez peut-être que `SUPABASE_ANON_KEY`.

**Solution**: Ajoutez la **Service Role Key** à vos variables d'environnement sur Render :

1. Allez dans votre projet Supabase
2. Settings → API → Copiez la **service_role** key (pas l'anon key)
3. Sur Render, ajoutez cette variable d'environnement :
   ```
   SUPABASE_SERVICE_ROLE_KEY=votre-service-role-key-ici
   ```

### 2. 🛡️ Correction des Politiques RLS

**Problème**: Vos politiques RLS ne correspondent pas à ce que le code attend.

**Solution**: Exécutez ce SQL dans l'éditeur SQL de Supabase :

```sql
-- Supprimer les anciennes politiques
DROP POLICY IF EXISTS "Allow Insert on plumastat_usage" ON plumastat_usage;
DROP POLICY IF EXISTS "Allow Select for API operations on plumastat_usage" ON plumastat_usage;

-- Créer les nouvelles politiques
CREATE POLICY "Allow Insert on plumastat_usage" ON plumastat_usage
FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow Select for API operations on plumastat_usage" ON plumastat_usage
FOR SELECT USING (true);

CREATE POLICY "Allow Update on plumastat_usage" ON plumastat_usage
FOR UPDATE USING (true);
```

### 3. 🧪 Test de la Configuration

Exécutez le script de test pour vérifier que tout fonctionne :

```bash
python test_database_connection.py
```

### 4. 🔄 Redéploiement

Après avoir ajouté la `SUPABASE_SERVICE_ROLE_KEY` sur Render :

1. Redéployez votre application
2. Testez avec une requête API

## Variables d'Environnement Requises sur Render

```
SUPABASE_URL=https://votre-projet-id.supabase.co
SUPABASE_SERVICE_ROLE_KEY=votre-service-role-key
SUPABASE_ANON_KEY=votre-anon-key (optionnel, fallback)
```

## Vérification Rapide

1. **Testez la connexion** :
   ```bash
   python test_database_connection.py
   ```

2. **Testez l'API** :
   ```bash
   curl -X POST https://votre-api-render.com/analyze \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Test",
       "date": "1990-01-01",
       "time": "12:00",
       "lat": 48.8566,
       "lon": 2.3522
     }'
   ```

## Messages d'Erreur Courants

- **"Supabase non configuré"** → Ajoutez `SUPABASE_SERVICE_ROLE_KEY`
- **"Erreur d'insertion"** → Vérifiez les politiques RLS
- **"Client Supabase non disponible"** → Vérifiez l'URL et la clé

## Support

Si le problème persiste, vérifiez :
1. Les logs de Render pour les erreurs détaillées
2. Les logs Supabase dans l'onglet "Logs"
3. Que la table `plumastat_usage` existe bien
