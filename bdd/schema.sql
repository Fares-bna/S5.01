
-- SOURCES DE DONNÉES (traçabilité + licences)
CREATE TABLE source_donnees (
    id_source   SERIAL PRIMARY KEY,
    nom         VARCHAR(100) NOT NULL UNIQUE,   -- 'NHTSA complaints', 'NHTSA recalls', 'RappelConso'
    url         TEXT,
    licence     VARCHAR(100),                   -- à vérifier avant usage
    date_import TIMESTAMPTZ
);
 
-- VEHICULE
CREATE TABLE vehicule (
    id_vehicule  SERIAL PRIMARY KEY,
    marque       VARCHAR(100) NOT NULL,
    modele       VARCHAR(100) NOT NULL,
    annee        INTEGER,
    carburant    TEXT,
    boite        TEXT,
    cylindres    SMALLINT,

    CONSTRAINT chk_annee CHECK (annee BETWEEN 1900 AND 2100),
    CONSTRAINT uq_vehicule UNIQUE NULLS NOT DISTINCT(marque, modele, annee, carburant, boite, cylindres)
);
 
--  COMPOSANT
CREATE TABLE composant (
    id_composant SERIAL PRIMARY KEY,
    nom          TEXT NOT NULL UNIQUE,
    categorie    VARCHAR(100)                   -- électricité, freinage
);
 
--  PROBLEME (une plainte ou un rappel)
CREATE TABLE probleme (
    id_probleme       SERIAL PRIMARY KEY,
    id_source         INTEGER NOT NULL REFERENCES source_donnees(id_source),
    reference_externe VARCHAR(150) NOT NULL,    -- identifiant dans la source d'origine
    type_probleme     VARCHAR(20) NOT NULL,     -- 'rappel' ou 'signalement'
    titre             VARCHAR(255),
    description       TEXT NOT NULL,
    gravite           VARCHAR(30),
    date_signalement  DATE, --optionnel

 
    CONSTRAINT uq_probleme_source UNIQUE (id_source, reference_externe),
    CONSTRAINT chk_type_probleme CHECK (type_probleme IN ('rappel', 'signalement')),
    CONSTRAINT chk_gravite CHECK (
        gravite IS NULL OR gravite IN ('faible', 'moderee', 'elevee', 'critique')
    )
);

-- CAUSE (une ligne par cause)
CREATE TABLE cause (
    id_cause  VARCHAR(10)  PRIMARY KEY,         -- 'C1' à 'C15'
    libelle   VARCHAR(255) NOT NULL UNIQUE,
    carburant VARCHAR(30),                      -- NULL = la cause concerne tous les carburants
    boite     VARCHAR(30),                      -- NULL = la cause concerne toutes les boîtes
    urgence   VARCHAR(30)  NOT NULL,
 
    CONSTRAINT chk_cause_carburant
        CHECK (carburant IS NULL OR carburant IN ('essence', 'diesel', 'hybride', 'electrique')),
    CONSTRAINT chk_cause_boite
        CHECK (boite IS NULL OR boite IN ('manuelle', 'automatique')),
    CONSTRAINT chk_cause_urgence
        CHECK (urgence IN ('peut_rouler', 'garage_rapidement', 'ne_pas_rouler'))
);
 
-- SOLUTION (ce que l'on recommande réellement)
CREATE TABLE solution (
    id_solution SERIAL PRIMARY KEY,
    libelle     VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    origine     VARCHAR(100)                    -- 'remede constructeur', 'redige par l''equipe'
);
 
-- SYMPTOME (optionnel)
CREATE TABLE symptome (
    id_symptome SERIAL PRIMARY KEY,
    libelle     VARCHAR(255) NOT NULL UNIQUE
);
 
-- LIAISONS
CREATE TABLE probleme_composant (
    id_probleme  INTEGER NOT NULL REFERENCES probleme(id_probleme)   ON DELETE CASCADE,
    id_composant INTEGER NOT NULL REFERENCES composant(id_composant) ON DELETE RESTRICT,
    cmplid       VARCHAR(50), -- numero de ligne NHTSA
    PRIMARY KEY (id_probleme, id_composant)
);
 
CREATE TABLE probleme_solution (
    id_probleme INTEGER NOT NULL REFERENCES probleme(id_probleme) ON DELETE CASCADE,
    id_solution INTEGER NOT NULL REFERENCES solution(id_solution) ON DELETE CASCADE,
    PRIMARY KEY (id_probleme, id_solution)
);
 
CREATE TABLE probleme_symptome (
    id_probleme INTEGER NOT NULL REFERENCES probleme(id_probleme) ON DELETE CASCADE,
    id_symptome INTEGER NOT NULL REFERENCES symptome(id_symptome) ON DELETE CASCADE,
    PRIMARY KEY (id_probleme, id_symptome)
);
 
CREATE TABLE symptome_composant (
    id_symptome  INTEGER NOT NULL REFERENCES symptome(id_symptome)   ON DELETE CASCADE,
    id_composant INTEGER NOT NULL REFERENCES composant(id_composant) ON DELETE CASCADE,
    PRIMARY KEY (id_symptome, id_composant)
);
 
CREATE TABLE vehicule_probleme (
    id_vehicule INTEGER NOT NULL REFERENCES vehicule(id_vehicule) ON DELETE CASCADE,
    id_probleme INTEGER NOT NULL REFERENCES probleme(id_probleme) ON DELETE CASCADE,
    PRIMARY KEY (id_vehicule, id_probleme)
);

CREATE TABLE cause_composant(
    id_cause  VARCHAR(10) NOT NULL REFERENCES cause(id_cause) ON DELETE CASCADE,
    categorie VARCHAR(100) NOT NULL,
    PRIMARY KEY (id_cause, categorie)
)
 
-- REQUETE UTILISATEUR
CREATE TABLE requete_utilisateur (
    id_requete         SERIAL PRIMARY KEY,
    id_vehicule        INTEGER NOT NULL REFERENCES vehicule(id_vehicule) ON DELETE RESTRICT,
    carburant          TEXT,
    boite              TEXT,
    symptomes_saisis   JSONB,
    description_saisie TEXT NOT NULL,
    date_requete       TIMESTAMPTZ NOT NULL DEFAULT now()
);
 
-- EXECUTION D'UNE APPROCHE POUR UNE REQUETE (le temps de réponse est ici, pas sur chaque résultat)
CREATE TABLE execution_recommandation (
    id_execution    SERIAL PRIMARY KEY,
    id_requete      INTEGER NOT NULL REFERENCES requete_utilisateur(id_requete) ON DELETE CASCADE,
    approche        VARCHAR(30) NOT NULL,
    temps_calcul_ms NUMERIC(12,4) NOT NULL,
    nb_resultats    INTEGER NOT NULL DEFAULT 0,
    date_execution  TIMESTAMPTZ NOT NULL DEFAULT now(),
 
    CONSTRAINT chk_approche CHECK (approche IN ('heuristique', 'embeddings'))
);
 
-- RESULTATS (classement renvoyé par une exécution)
CREATE TABLE resultat_recommandation (
    id_resultat  SERIAL PRIMARY KEY,
    id_execution INTEGER NOT NULL REFERENCES execution_recommandation(id_execution) ON DELETE CASCADE,
    id_probleme  INTEGER NOT NULL REFERENCES probleme(id_probleme) ON DELETE RESTRICT,
    rang         INTEGER NOT NULL,
    score        DOUBLE PRECISION,
    explication  JSONB,                         -- "Pourquoi ?" : composants matchés, poids, extrait
 
    CONSTRAINT chk_rang CHECK (rang > 0),
    CONSTRAINT uq_resultat_rang UNIQUE (id_execution, rang)   -- crée aussi l'index sur id_execution
);
 
-- INDEX 

CREATE INDEX idx_requete_vehicule        ON requete_utilisateur(id_vehicule);
CREATE INDEX idx_execution_requete       ON execution_recommandation(id_requete);
CREATE INDEX idx_probleme_composant_comp ON probleme_composant(id_composant);
CREATE INDEX idx_vehicule_probleme_prob  ON vehicule_probleme(id_probleme);
 
-- VUE DE METRIQUES
CREATE VIEW v_metriques_approche AS
SELECT approche,
       COUNT(*)                                                       AS nb_executions,
       MIN(temps_calcul_ms)                                           AS min_ms,
       MAX(temps_calcul_ms)                                           AS max_ms,
       AVG(temps_calcul_ms)                                           AS moyen_ms,
       percentile_cont(0.5)  WITHIN GROUP (ORDER BY temps_calcul_ms)  AS mediane_ms,
       percentile_cont(0.95) WITHIN GROUP (ORDER BY temps_calcul_ms)  AS p95_ms
FROM execution_recommandation
GROUP BY approche;