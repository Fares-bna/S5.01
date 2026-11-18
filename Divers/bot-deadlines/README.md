# Bot deadlines – SAÉ S5.01

Bot Discord qui suit les tâches et deadlines du projet DiagDuo et mentionne chaque jour les personnes concernées.
Il tourne gratuitement sur Cloudflare Workers, avec une base de données Cloudflare D1.

## Ce qu'il fait

- Commandes `/tache` pour ajouter, lister, voir, modifier, changer le statut, terminer ou supprimer une tâche. Seul le responsable d'une tâche (ou un admin) peut confirmer qu'elle est terminée.
- `/recap` : toutes les tâches commencées ou en retard pas encore terminées, regroupées par responsable, avec mention. Option `prive:True` pour l'afficher seulement à soi, sans notifier personne.
- Un récap par jour à l'heure choisie (rien si rien à signaler) : en retard, à rendre aujourd'hui, demain, dans 3 jours (règle J-3), début de tâche, jalons et rendus prof à J-7 et J-1, et le lundi les tâches de la semaine par personne.
- `/config` pour changer l'heure, le salon et activer ou couper chaque type de rappel.
- `/message` pour faire parler le bot. `/aide` explique tout.
- **Portail web** (même adresse que le bot) : tableau de bord, tâches (ajouter, modifier, terminer, supprimer), message au nom du bot, réglages. Protégé par un mot de passe commun.
- **Accès pour les IA** (Claude, ChatGPT, Gemini…) : serveur MCP sur `/mcp` et description OpenAPI sur `/openapi.json`, protégés par une clé. Voir [docs/acces-ia.md](docs/acces-ia.md).

## Organisation du code

```
src/index.js        point d'entrée : reçoit les commandes (fetch) et le réveil toutes les 15 min (scheduled)
src/commandes.js    ce que fait chaque commande
src/definitions.js  liste des commandes envoyée à Discord
src/rappels.js      construction et envoi du récap quotidien
src/taches.js       accès à la base (tâches, membres)
src/config.js       réglages par défaut et lecture/écriture
src/dates.js        fonctions de dates (heure de Paris, JJ/MM)
src/discord.js      signature, réponses, envoi de messages
src/portail.html    le portail web (HTML, CSS et JS dans un seul fichier, sans bibliothèque)
src/api.js          API du portail (/api/...) : connexion, tâches, réglages, message
src/mcp.js          accès des IA : serveur MCP (/mcp) et description OpenAPI (/openapi.json)
schema.sql          tables de la base
donnees.sql         planning de départ du projet
scripts/enregistrer-commandes.js  enregistre les commandes sur le serveur Discord
```

Ajouter une commande : la déclarer dans `definitions.js`, écrire sa fonction dans `commandes.js` (objet `ACTIONS`), puis relancer `npm run commandes`.
Ajouter un type de rappel : une valeur dans `config.js`, une section dans `rappels.js`, un choix dans `definitions.js`.

## Installation (une seule fois)

Il faut Node.js 20 ou plus.

1. **Créer le bot sur Discord** : https://discord.com/developers/applications > New Application. Choisis le nom et la photo.
   - Dans *General Information*, note l'**Application ID** et la **Public Key**.
   - Dans *Bot*, clique *Reset Token* et garde le **token** pour toi (il est secret, ne le mets jamais dans le code ni sur GitHub).
   - Dans *Installation*, coche `applications.commands` et `bot`, avec les permissions *View Channels* et *Send Messages*, puis ouvre le lien pour ajouter le bot au serveur SAE S5.
2. **Installer les outils** : `npm install`, puis `npx wrangler login` (crée ou connecte ton compte Cloudflare).
3. **Créer la base** : `npx wrangler d1 create bot-deadlines`, puis copie le `database_id` affiché dans `wrangler.toml`.
4. **Remplir `wrangler.toml`** : `DISCORD_APPLICATION_ID` et `DISCORD_PUBLIC_KEY`.
5. **Créer les tables et le planning** : `npm run base` puis `npm run remplir`.
6. **Mettre le token en secret** : `npx wrangler secret put DISCORD_TOKEN` (colle le token quand c'est demandé).
7. **Mettre en ligne** : `npm run deployer`. Note l'adresse affichée (`https://bot-deadlines.xxx.workers.dev`).
8. **Relier Discord au bot** : dans *General Information*, colle cette adresse dans *Interactions Endpoint URL* et enregistre.
9. **Enregistrer les commandes** : `DISCORD_TOKEN=… DISCORD_APPLICATION_ID=… DISCORD_GUILD_ID=… npm run commandes`
   (l'id du serveur : clic droit sur le serveur > Copier l'identifiant, avec le mode développeur activé dans Discord).
10. **Portail web** : `npx wrangler secret put PORTAIL_MOT_DE_PASSE` (choisis le mot de passe commun du groupe), puis ouvre l'adresse du bot dans un navigateur.
11. **Accès IA (facultatif)** : `npx wrangler secret put CLE_API` avec une longue clé aléatoire (au moins 20 caractères, par exemple `openssl rand -hex 32`). Sans cette clé, `/mcp` et l'accès par clé sont coupés.

## Premiers réglages sur Discord

1. `/membre lier` pour chaque personne (prénom + compte Discord), pour que les rappels mentionnent les bons comptes.
2. `/tache liste tout:True` pour vérifier les statuts, puis `/tache terminer` sur ce qui est fini.
3. `/config salon` puis `/config heure`. Tant qu'aucun salon n'est choisi, le bot n'envoie aucun rappel.
4. `/rappel` pour voir le récap tout de suite.

## Licence

MIT
