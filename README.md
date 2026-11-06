# Règles GitHub de l'équipe

## Branches
- Une branche par fonctionnalité, créée depuis `main`.
- Noms de fichiers, dossiers et branches en français, sans accents, en minuscules avec des tirets (exemple : `feat/heuristique-scores`).
- `main` est protégée : pas de push direct, une Pull Request avec au moins une validation est obligatoire.

## Commits
Préfixes obligatoires :
- `feat:` nouvelle fonctionnalité
- `fix:` correction
- `docs:` documentation

Exemple : `feat: ajoute le service de calcul des scores`

## Travail en binôme
Chaque tâche a un responsable et un partenaire. Le partenaire peut laisser des commentaires dans la PR, et le responsable y répond avant la fusion.

## Pull Requests
Chaque PR utilise le modèle suivant :

**Tâche :**
**Responsable :**
**Partenaire :**

**Livrable du partenaire (obligatoire) :**
- [ ] Relecture écrite
- [ ] Test écrit
- [ ] Note d'explication
- [ ] Refait seul une partie
- [ ] Questions d'oral

**Terminé quand :**
- [ ] Le travail est fini et testé
- [ ] Le livrable du partenaire est dans la PR ou dans `docs/`
- [ ] Le partenaire a expliqué la tâche en 3 minutes sans aide

## Versions
Versionnement sémantique : `v0.1.0` pour la première version, `v1.0.0` pour la version finale.

## Données
Aucune donnée brute dans git (le fichier NHTSA fait des centaines de Mo). Les données brutes sont ignorées via le `.gitignore`.

## Suivi des tâches
GitHub Projects, relié aux issues.
