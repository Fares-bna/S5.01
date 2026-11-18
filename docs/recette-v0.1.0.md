# Recette sur machine propre

* **Tâche :** Recette sur machine propre 

* **Responsable :** Ciffedinne (@Ciffedinne) · **Partenaire :** Fares (@Fares-bna)

* **Livrable du partenaire :** test écrit

* **Branche ou version testée :** `main` · **Tag visé :** v0.1.0

* **Date de la recette :** 18/11/2026

Principe : on installe et on lance le projet comme le ferait quelqu'un qui ne le connaît pas, en suivant seulement le README. Chaque étape qui n'y est pas écrite est notée comme un défaut.

## 1. La machine

| Élément | Valeur | 
| ----- | ----- | 
| Système d'exploitation | Microsoft Windows 11 Professionnel | 
| Dossier de travail | `C:\Users\maison\S5.01` (nouveau clone, sans `node_modules` ni ancien réglage) | 
| Git (`git --version`) | `git version 2.54.0.windows.1` | 
| Node.js (`node -v`) | `v24.16.0` | 
| npm (`npm -v`) | `11.13.0` | 
| Docker (`docker --version`) | `Docker version 29.9.3, build 5457199` | 

## 2. Installation et lancement

| N° | Étape | Attendu | Obtenu | OK | 
| ----- | ----- | ----- | ----- | ----- | 
| 1 | `git clone https://github.com/Fares-bna/S5.01.git`, puis `cd S5.01` | Le dépôt se clone sans erreur | Cloné sans erreur (412 objets) | ☑ | 
| 2 | Passer sur la branche ou la version testée | La branche est trouvée | Branche `main` trouvée (`Already on 'main'`) | ☑ | 
| 3 | Créer le fichier de configuration à partir de `.env.example` | Le fichier existe, sans mot de passe réel dans le dépôt | `.env` créé via `Copy-Item` (installation Python bloquée par `uvloop` sous Windows, contournée) | ☑ | 
| 4 | Lancer la partie serveur et base de données (`docker-compose` si le README le demande) | Les conteneurs démarrent sans erreur | PostgreSQL 16 démarré, schéma créé, 1000 plaintes ingérées (996 problèmes), `COPY 15` et `COPY 25`, API lancée sur `http://127.0.0.1:8000` (avec adaptation des redirections PowerShell) | ☑ | 
| 5 | Vérifier la route `/health` | Elle répond que le serveur fonctionne | Répond `status: ok` sur `http://localhost:8000/health` | ☑ | 
| 6 | `cd front`, puis `npm install` | Installation sans erreur bloquante | 141 paquets installés en 6 s (warnings de dépréciation non bloquants) | ☑ | 
| 7 | `npm run lint` | 0 error, 0 warning | `0 error, 0 warning` (`--max-warnings 0` validé) | ☑ | 
| 8 | `npm run build` | Le dossier `dist/` est généré sans erreur | `dist/` généré en 817 ms (`index.html`, CSS, JS et logo) | ☑ | 
| 9 | `npm run dev` | Le site s'ouvre sur `localhost:5173` | Vite prêt en 499 ms sur `http://localhost:5173/` | ☑ | 

Si une étape n'est pas décrite dans le README, je l'écris ici :

* Les équivalents Windows PowerShell (`.\.venv\Scripts\Activate.ps1`, `Copy-Item`, remplacement des redirections `<` par `Get-Content ... |` et `@('\copy ...') + ...`).

* Le contournement pour installer `api/requirements.txt` sans `uvloop==0.23.0` sous Windows.

* Les commandes front `npm run lint` et `npm run build` ne sont pas mentionnées dans le README.

## 3. Propreté du dépôt

| N° | Vérification | Attendu | Obtenu | OK | 
| ----- | ----- | ----- | ----- | ----- | 
| 15 | Aucun mot de passe, `.env` ni liste de VIN dans le dépôt cloné | Rien de tel | Seul `.env.example` (avec `POSTGRES_PASSWORD=changeme`) est suivi ; aucun `.env` réel, secret ou VIN dans Git | ☑ | 
| 16 | Aucune donnée brute NHTSA dans git | Seulement l'échantillon de 1000 lignes, s'il existe | Uniquement `data/echantillon/echantillon_nhtsa.csv`, les références `bdd/donnees/*.csv` et `api/mock/fausses_donnees.json` | ☑ | 
| 17 | Le README suffit pour tout installer | Aucune étape manquante | Non : commandes uniquement Linux/macOS, `uvloop` bloquant sous Windows, `lint`/`build` absents | ☐ | 

## 4. Temps total

Temps entre le clonage et le site affiché : **4 min 55 s** (installation back + base + démarrage API) + **\~8 s** (installation et lancement front) ≈ **5 min 05 s**.

## 5. Défauts trouvés

| N° | Défaut | Étape | Gravité (bloquant ou non) |
|---|---|---|---|
| 1 | `api/requirements.txt` impose `uvloop==0.23.0` sans condition de plateforme (`; sys_platform != "win32"`), ce qui fait échouer `pip install` sous Windows (`RuntimeError: uvloop does not support Windows at the moment`) | Étape 3 | Bloquant (sur Windows) |
| 2 | Le README ne fournit que les commandes Bash (Linux/macOS) : activation `.venv`, redirections `< bdd/schema.sql` et `< bdd/donnees/*.csv` échouent dans PowerShell | Étapes 3 & 4 | Non bloquant (si on adapte les commandes) |
| 3 | Le README ne mentionne pas les commandes front `npm run lint` et `npm run build` | Étapes 7 & 8 | Non bloquant |

## 6. Bilan

* **Verdict :** *À choisir après validation des scénarios navigateur 10 à 14 (prêt pour le tag v0.1.0 sous réserve de corriger `uvloop` dans `api/requirements.txt`).*

* **Correction fait avant le tag :** Ajouter `; sys_platform != "win32"` sur `uvloop` dans `api/requirements.txt` et documenter les commandes Windows + `npm run lint` / `npm run build` dans le `README.md`.

* **Points à améliorer après :** *À compléter selon les observations sur l'interface.*

## 8. Terminé quand

* [x] Toutes les étapes ont été faites sur une machine propre.

* [x] Les défauts sont notés et les responsables prévenus.

* [x] Ce fichier est dans la PR ou dans `docs/`.

* [ ] Fares a expliqué la tâche en 3 minutes sans aide.

* [ ] Fares a validé la PR (Approve), puis je fusionne.
