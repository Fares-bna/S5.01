-- Membres du groupe : prénom -> compte Discord (pour les mentions)
CREATE TABLE IF NOT EXISTS membres (
  prenom     TEXT PRIMARY KEY,
  discord_id TEXT UNIQUE
);

-- Tâches, jalons internes et rendus prof
CREATE TABLE IF NOT EXISTS taches (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  titre       TEXT NOT NULL,
  description TEXT,
  type        TEXT NOT NULL DEFAULT 'tache',   -- tache | jalon | rendu
  responsable TEXT,                            -- prénom (table membres)
  partenaire  TEXT,                            -- prénom (table membres)
  debut       TEXT,                            -- AAAA-MM-JJ
  fin         TEXT NOT NULL,                   -- AAAA-MM-JJ
  statut      TEXT NOT NULL DEFAULT 'a_faire', -- a_faire | en_cours | termine
  etape       INTEGER
);

-- Réglages modifiables depuis Discord (/config)
CREATE TABLE IF NOT EXISTS config (
  cle    TEXT PRIMARY KEY,
  valeur TEXT
);
