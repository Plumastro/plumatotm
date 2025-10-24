-- Script SQL pour corriger les problèmes RLS sur Supabase
-- À exécuter dans l'éditeur SQL de Supabase
-- ATTENTION: La table plumastat_usage existe déjà avec des données (3,093 enregistrements)

-- 1. Désactiver temporairement RLS sur la table plumastat_usage
-- (Solution recommandée pour permettre les insertions)
ALTER TABLE plumastat_usage DISABLE ROW LEVEL SECURITY;

-- 2. Alternative: Créer une politique RLS permissive (si vous préférez garder RLS)
-- Décommentez les lignes suivantes si vous voulez garder RLS activé :
-- DROP POLICY IF EXISTS "Allow all operations on plumastat_usage" ON plumastat_usage;
-- CREATE POLICY "Allow all operations on plumastat_usage" 
-- ON plumastat_usage FOR ALL 
-- USING (true) 
-- WITH CHECK (true);

-- 3. Créer des index pour améliorer les performances (si pas déjà existants)
CREATE INDEX IF NOT EXISTS idx_plumastat_usage_plumid ON plumastat_usage(plumid);
CREATE INDEX IF NOT EXISTS idx_plumastat_usage_animal ON plumastat_usage(top1_animal);
CREATE INDEX IF NOT EXISTS idx_plumastat_usage_created_at ON plumastat_usage(created_at);

-- 4. Vérifier que les colonnes nécessaires existent
-- (Ces colonnes semblent déjà exister d'après l'interface)
-- ALTER TABLE plumastat_usage ADD COLUMN IF NOT EXISTS user_name TEXT;
-- ALTER TABLE plumastat_usage ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
-- ALTER TABLE plumastat_usage ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
