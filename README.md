# Règles GitHub de l'équipe

## Branches
- Une branche par fonctionnalité, créée depuis `main`.
- Noms de fichiers, dossiers et branches en français, sans accents, en minuscules avec des tirets (exemple : `feat/heuristique-scores`). Exception : les fichiers Python (.py) utilisent des underscores (ex. creer_echantillon.py), car un tiret empêche de les importer.
- `main` est protégée : pas de push direct, une Pull Request avec au moins une validation est obligatoire.

## Commits
Préfixes obligatoires :
- `feat:` nouvelle fonctionnalité
- `fix:` correction
- `docs:` documentation

Exemple : `feat: ajoute le service de calcul des scores`

## Travail en binôme
Chaque tâche a un responsable et un partenaire. Le partenaire relit la PR, rend son livrable (obligatoire) et la valide (Approve). La validation doit venir du partenaire de la tâche. Le responsable fusionne ensuite.

## Pull Requests
Chaque PR utilise le modèle suivant (fichier `.github/pull_request_template.md`) :

**Tâche :**
**Responsable :**
**Partenaire :**

**Livrable du partenaire (obligatoire : cocher au moins 1 case) :**
- [ ] Relecture écrite
- [ ] Test écrit
- [ ] Note d'explication
- [ ] Refait seul une partie
- [ ] Questions d'oral

**Avant de fusionner (responsable) :**
- [ ] Aucune donnée brute, liste de VIN, mot de passe ou `.env` dans la PR
- [ ] Je sais expliquer chaque ligne ajoutée

**Terminé quand (toutes les cases doivent être cochées avant de fusionner) :**
- [ ] Le travail est fini et testé
- [ ] Le livrable du partenaire est dans la PR ou dans `docs/` (dossier du dépôt ≠ Google Doc ) 
- [ ] Le partenaire a expliqué la tâche en 3 minutes sans aide
- [ ] Le partenaire a validé la PR (Approve), puis le responsable fusionne

## Versions
Versionnement sémantique : `v0.1.0` pour la première version, `v1.0.0` pour la version finale.

## Données
Aucune donnée brute dans git (le fichier NHTSA fait des centaines de Mo). Les données brutes sont ignorées via le `.gitignore`.
Exception : l'échantillon de 1000 lignes dans `data/echantillon/` (sans colonnes personnelles) est versionné.
Secrets : `.env` est ignoré, `.env.example` est versionné. Aucune liste de VIN ni mot de passe dans git.



## Installation (Ubuntu / WSL)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r pipeline/requirements.txt
```

Sous Ubuntu, `pip install` seul échoue (environnement géré par le système) : activer le `.venv` puis utiliser `python -m pip`.
