# Pipeline d'ingestion NHTSA

Ce document explique comment lancer le pipeline qui lit les plaintes NHTSA, les valide, les transforme et les charge dans PostgreSQL. Les sources, les règles de nettoyage et les chiffres sont dans `docs/fiche-sources.md`.

## Ce que fait le pipeline

Le pipeline suit quatre étapes, chacune dans son fichier de `pipeline/ingestion/` :

| Étape | Fichier | Rôle |
|---|---|---|
| Lecture | `lecture_nhtsa.py` | lit le fichier (.txt brut ou .csv d'échantillon), seulement les 15 colonnes utiles : le VIN n'est jamais lu |
| Validation | `validation_nhtsa.py` | contrôle le format avec pandera ; s'arrête avec un message lisible si le format change |
| Transformation | `transformation_nhtsa.py` | nettoie et produit 5 tables : véhicule, composant, problème, problème-composant, véhicule-problème |
| Chargement | `chargement_nhtsa.py` | écrit dans PostgreSQL en une seule transaction ; peut être rejoué sans doublon |

Le point d'entrée est `ingerer_nhtsa.py`. Les tests sont dans `pipeline/tests/`.

## Prérequis

- Docker (pour PostgreSQL 16) ;
- Python avec un environnement virtuel, dans WSL ou Linux.

## 1. Installer

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r pipeline/requirements.txt
```

## 2. Lancer la base

```bash
cp .env.example .env
```

Dans `.env`, change `POSTGRES_PASSWORD`. Si le port 5432 est déjà pris sur ta machine (un PostgreSQL local, par exemple), mets `POSTGRES_PORT=5433`. Le fichier `.env` n'est jamais versionné.

```bash
docker compose up -d
docker compose ps
```

`db` doit être `healthy` (10 à 20 secondes).

## 3. Charger le schéma

```bash
docker compose exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < bdd/schema.sql
```

Le schéma crée les tables, les index et la vue. En cas de doute : `docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "\dt"'` liste les tables.

## 4. Lancer les tests

```bash
python -m pytest -v
```

Résultat attendu : tous les tests passent. Les tests de chargement utilisent un schéma temporaire dans la base ; si la base n'est pas joignable, ces tests sont ignorés (« skipped ») au lieu d'échouer.

## 5. Charger les données

Échantillon (environ 1 000 lignes, versionné dans `data/echantillon/`) :

```bash
python -m pipeline.ingestion.ingerer_nhtsa data/echantillon/echantillon_nhtsa.csv
```

Le script affiche « Format validé. », puis le nombre de lignes chargées.

Fichier complet 2025-2026 : le zip est sur le Drive de l'équipe et n'est jamais versionné. Dépose-le dans `data/nhtsa/`, vérifie son empreinte, décompresse-le, puis charge-le :

```bash
sha256sum data/nhtsa/COMPLAINTS_RECEIVED_2025-2026.zip
unzip data/nhtsa/COMPLAINTS_RECEIVED_2025-2026.zip -d data/nhtsa
python -m pipeline.ingestion.ingerer_nhtsa data/nhtsa/COMPLAINTS_RECEIVED_2025-2026.txt
```

L'empreinte attendue est `6a106e8509b917c557c7eef257c2c77edf3056b6271a585e6f1b9ce53211a7d0`. Résultat attendu sur le fichier complet : 140 271 plaintes, 503 composants, 7 360 véhicules, 186 665 liens plainte-composant (sur l'échantillon : 996, 67, 674 et 905).

Le chargement peut être relancé : les lignes existantes sont mises à jour, sans doublon.

## Pièges connus

- **`docker compose down -v` efface la base** (le `-v` supprime le volume). Sans `-v`, les données sont conservées.
- **Port 5432 occupé** : utilise `POSTGRES_PORT=5433` dans `.env`, sinon la connexion échoue ou vise un autre PostgreSQL, et les tests de chargement sont ignorés.
- **Si le format du fichier change**, la validation s'arrête avant d'écrire en base : lis le message, il indique la colonne, la règle et des exemples.
- **Carburant, boîte et cylindres** sont à NULL pour l'instant (décodage du VIN non fait) : voir la fiche des sources.
