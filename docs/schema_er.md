# Schéma entité-association

Diagramme tiré de `bdd/schema.sql` (16 tables et une vue). GitHub l'affiche directement en image.

```mermaid
erDiagram
    source_donnees ||--o{ probleme : "fournit"
    vehicule ||--o{ vehicule_probleme : ""
    probleme ||--o{ vehicule_probleme : ""
    probleme ||--o{ probleme_composant : ""
    composant ||--o{ probleme_composant : ""
    probleme ||--o{ probleme_solution : ""
    solution ||--o{ probleme_solution : ""
    probleme ||--o{ probleme_symptome : ""
    symptome ||--o{ probleme_symptome : ""
    symptome ||--o{ symptome_composant : ""
    composant ||--o{ symptome_composant : ""
    cause ||--o{ cause_composant : ""
    composant }o..o{ cause_composant : "même catégorie"
    vehicule ||--o{ requete_utilisateur : "choisi dans"
    requete_utilisateur ||--o{ execution_recommandation : "lance"
    execution_recommandation ||--o{ resultat_recommandation : "renvoie"
    probleme ||--o{ resultat_recommandation : "proposé dans"

    source_donnees {
        int id_source PK
        varchar nom
        text url
        varchar licence
        timestamptz date_import
    }
    vehicule {
        int id_vehicule PK
        varchar marque
        varchar modele
        int annee
        text carburant
        text boite
        smallint cylindres
    }
    composant {
        int id_composant PK
        text nom
        varchar categorie
    }
    probleme {
        int id_probleme PK
        int id_source FK
        varchar reference_externe
        varchar type_probleme
        varchar titre
        text description
        varchar gravite
        date date_signalement
    }
    cause {
        varchar id_cause PK
        varchar libelle
        varchar carburant
        varchar boite
        varchar urgence
    }
    cause_composant {
        varchar id_cause PK, FK
        varchar categorie PK
    }
    solution {
        int id_solution PK
        varchar libelle
        text description
        varchar origine
    }
    symptome {
        int id_symptome PK
        varchar libelle
    }
    probleme_composant {
        int id_probleme PK, FK
        int id_composant PK, FK
        varchar cmplid
    }
    probleme_solution {
        int id_probleme PK, FK
        int id_solution PK, FK
    }
    probleme_symptome {
        int id_probleme PK, FK
        int id_symptome PK, FK
    }
    symptome_composant {
        int id_symptome PK, FK
        int id_composant PK, FK
    }
    vehicule_probleme {
        int id_vehicule PK, FK
        int id_probleme PK, FK
    }
    requete_utilisateur {
        int id_requete PK
        int id_vehicule FK
        text carburant
        text boite
        jsonb symptomes_saisis
        text description_saisie
        timestamptz date_requete
    }
    execution_recommandation {
        int id_execution PK
        int id_requete FK
        varchar approche
        numeric temps_calcul_ms
        int nb_resultats
        timestamptz date_execution
    }
    resultat_recommandation {
        int id_resultat PK
        int id_execution FK
        int id_probleme FK
        int rang
        float score
        jsonb explication
    }
```

## Les tables en une phrase

**Données NHTSA**
- `source_donnees` : d'où viennent les données (nom, adresse, licence, date d'import).
- `probleme` : une plainte NHTSA (une par ODINO), avec son texte et sa gravité.
- `vehicule` : un véhicule, identifié par marque, modèle, année, carburant, boîte et cylindres.
- `composant` : un composant NHTSA (`COMPDESC`) et sa catégorie (partie avant le premier « : »).
- `vehicule_probleme` et `probleme_composant` : relient une plainte à son véhicule et à ses composants.

**Contenu métier**
- `cause` : les 15 causes proposées à l'utilisateur (C1 à C15), avec carburant, boîte et urgence.
- `cause_composant` : relie une cause aux catégories de composants. Le lien avec `composant` passe par la valeur de `categorie`, pas par une clé étrangère (une catégorie regroupe plusieurs composants).
- `solution`, `symptome` et leurs tables de liaison (`probleme_solution`, `probleme_symptome`, `symptome_composant`).

**Utilisation de l'application**
- `requete_utilisateur` : ce que l'utilisateur a saisi (véhicule, carburant, boîte, symptômes, description).
- `execution_recommandation` : une exécution d'une approche (heuristique ou embeddings) pour une requête, avec son temps de calcul.
- `resultat_recommandation` : le classement renvoyé par une exécution, avec le score et l'explication du « Pourquoi ».
- La vue `v_metriques_approche` calcule les temps min, max, moyen, médian et p95 par approche (dashboard).
