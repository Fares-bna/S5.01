# DiagDuo

DiagDuo aide un particulier sans connaissances en mécanique à comprendre une panne de voiture. Il choisit son véhicule, coche ses symptômes et décrit le problème en quelques mots. L'application propose des causes probables, leur niveau d'urgence et des solutions.

Deux approches de recommandation sont comparées sur les mêmes données (plaintes NHTSA) :

- **Approche A, heuristique** : des règles à poids, calculés à partir de la fréquence des plaintes (voir `docs/regles_heuristique.md`).
- **Approche B, embeddings** : comparaison du texte saisi avec le texte des plaintes.

Projet réalisé dans le cadre de la SAÉ S5.01 (BUT Informatique). Licence MIT.

## Structure du dépôt

| Dossier | Contenu |
|---|---|
| `api/` | Backend FastAPI (contrôleurs, services, dépôts, schémas) et fausses données (`api/mock/`) |
| `bdd/` | Schéma PostgreSQL (`schema.sql`) et données de référence (`donnees/`) |
| `pipeline/` | Ingestion des plaintes NHTSA (lecture, transformation, chargement) et ses tests |
| `data/echantillon/` | Échantillon de 1000 lignes NHTSA, sans données personnelles |
| `scripts/` | Scripts utilitaires (création de l'échantillon, liste des composants) |
| `benchmark/` | Comparaison des deux approches |
| `front/` | Application web frontend (Vite / Vue) |
| `docs/` | Documentation : contrat d'API, règles de l'heuristique, règles GitHub, fiches |

## Prérequis

- Python 3.12 ou plus récent
- Docker et Docker Compose (Docker Desktop sous Windows et macOS)
- Node.js 18 ou plus récent (pour le front)

## Installation

**Linux / macOS (Bash) :**

```bash
git clone https://github.com/Fares-bna/S5.01.git
cd S5.01
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r pipeline/requirements.txt -r api/requirements.txt
cp .env.example .env
```

**Windows (PowerShell) :**

```powershell
git clone https://github.com/Fares-bna/S5.01.git
cd S5.01
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install -r pipeline/requirements.txt -r api/requirements.txt
Copy-Item .env.example .env
```

Sous Ubuntu, `pip install` seul échoue (environnement géré par le système) : activer le `.venv` puis utiliser `python -m pip`.

Le fichier `.env` contient les identifiants de la base. Il n'est jamais versionné.

## Lancer la base de données

**Linux / macOS (Bash) :**

```bash
docker compose up -d
docker compose exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < bdd/schema.sql
```

**Windows (PowerShell) :**

```powershell
docker compose up -d
Get-Content bdd/schema.sql | docker compose exec -T db sh -c 'psql -U $POSTGRES_USER -d $POSTGRES_DB'
```

La première commande lance PostgreSQL 16 dans un conteneur. La seconde crée les tables (à faire une seule fois, la base est conservée dans un volume Docker).

**Mac avec Postgres.app (ou tout Postgres déjà installé)** : le port 5432 est déjà pris, et la connexion arrive sur ce Postgres local au lieu du conteneur. Mettre `POSTGRES_PORT=5433` dans `.env`, puis relancer `docker compose up -d`.

## Charger les plaintes NHTSA

```bash
python -m pipeline.ingestion.ingerer_nhtsa data/echantillon/echantillon_nhtsa.csv
```

L'ingestion lit le fichier, le transforme puis charge les tables. Elle peut être relancée sans créer de doublons. Pour le fichier complet, le télécharger sur le site de la NHTSA et le placer dans `data/nhtsa/` (dossier ignoré par git) :

```bash
python -m pipeline.ingestion.ingerer_nhtsa data/nhtsa/COMPLAINTS_RECEIVED_2025-2026.txt
```

## Charger les causes

L'heuristique a besoin des 15 causes et de leurs catégories de composants NHTSA. À faire une seule fois, après la création des tables :

**Linux / macOS (Bash) :**

```bash
docker compose exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "\copy cause FROM STDIN CSV HEADER"' < bdd/donnees/cause.csv
docker compose exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "\copy cause_composant FROM STDIN CSV HEADER"' < bdd/donnees/cause_composant.csv
```

**Windows (PowerShell) :**

```powershell
@('\copy cause FROM STDIN CSV HEADER') + (Get-Content bdd/donnees/cause.csv) | docker compose exec -T db sh -c 'psql -U $POSTGRES_USER -d $POSTGRES_DB'
@('\copy cause_composant FROM STDIN CSV HEADER') + (Get-Content bdd/donnees/cause_composant.csv) | docker compose exec -T db sh -c 'psql -U $POSTGRES_USER -d $POSTGRES_DB'
```

Résultat attendu : `COPY 15` puis `COPY 25`.

## Lancer l'API

```bash
cd api
uvicorn app.main:app --reload
```

L'API répond sur http://localhost:8000. La page http://localhost:8000/docs permet d'essayer les routes depuis le navigateur, et http://localhost:8000/health vérifie que l'API fonctionne.

## Lancer le front

Dans un second terminal :

```bash
cd front
npm install
npm run dev
```

Le front s'ouvre sur http://localhost:5173.

Pour vérifier la qualité du code et générer le build de production :

```bash
npm run lint
npm run build
```

## Lancer les tests

```bash
python -m pytest -v
```

Les tests de chargement utilisent la base Docker. Si elle n'est pas lancée, ils sont ignorés (`skipped`) au lieu d'échouer.

Les tests de l'API se lancent depuis le dossier `api/`. Ils ont besoin de la base lancée, avec les plaintes et les causes chargées :

```bash
cd api
python -m pytest -v
```

## Documentation

- [Contrat d'API](docs/contrat_api.md) : routes, données échangées entre le front et le back
- [Schéma entité-association](docs/schema_er.md) : les tables de la base et leurs liens
- [Pipeline d'ingestion](docs/pipeline.md) : lancer l'ingestion des plaintes NHTSA de bout en bout
- [Fiche des sources](docs/fiche-sources.md) : origine des données, vérifications et chiffres chargés
- [Règles de l'heuristique](docs/regles_heuristique.md) : calcul des poids et algorithme de l'approche A
- [Table causes ↔ composants](docs/fiche-table-causes-composants.md) : lien entre nos causes et les composants NHTSA
- [Règles GitHub de l'équipe](docs/regles_github.md) : branches, commits, modèle de PR, versions
