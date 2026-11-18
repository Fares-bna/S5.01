# Fiche de compréhension – Bot deadlines

## Quoi
Un bot Discord qui garde la liste des tâches du projet (responsable, partenaire, dates, statut) et envoie un récap quotidien qui mentionne les personnes concernées. Tout se règle depuis Discord avec des commandes slash.

## Pourquoi ces choix
- **Commandes slash par "interactions HTTP"** : Discord envoie chaque commande en requête HTTP au bot. Pas besoin d'une connexion permanente, donc le bot peut tourner sur un hébergement qui "dort" entre deux appels.
- **Cloudflare Workers** : gratuit, toujours joignable, réveil planifié inclus (cron toutes les 15 min) et base de données D1 (SQLite) incluse. Google Apps Script ne marche pas ici (réponse signée en moins de 3 s impossible), et les offres gratuites de Render/Railway s'endorment.
- **Prénoms dans la base, comptes Discord à part** (table `membres`) : le planning se pré-remplit avec des prénoms, et `/membre lier` fait le lien avec les comptes pour les mentions.
- **Un seul message par jour, rien si rien à dire** : pour éviter le spam. `dernier_envoi` empêche d'envoyer deux fois le même jour.

## Comment ça marche
1. On tape `/tache ajouter`. Discord envoie une requête POST signée au Worker.
2. `index.js` vérifie la signature Ed25519 avec la clé publique (sinon n'importe qui pourrait se faire passer pour Discord), puis passe la commande à `commandes.js`.
3. `commandes.js` lit les options, appelle `taches.js` qui écrit dans D1, et renvoie la réponse en moins de 3 s.
4. Toutes les 15 min, Cloudflare appelle `scheduled`. Si un salon est choisi, que l'heure du récap est passée et que rien n'a été envoyé aujourd'hui, `rappels.js` construit le récap et l'envoie avec le token du bot.

## Qui peut terminer une tâche
Discord envoie avec chaque commande l'id du compte qui l'a tapée (`interaction.member.user.id`) et ses permissions. Le bot cherche le prénom lié à cet id dans `membres` et le compare au responsable de la tâche. Les admins (permission « Gérer le serveur ») peuvent toujours corriger. On compare des id et pas des pseudos, car un pseudo peut changer ou être copié, alors que l'id est unique et fixe.

## Pièges
- Le **token** est secret : uniquement dans `wrangler secret`, jamais dans le code. La clé publique et l'Application ID ne sont pas secrets.
- Après une modif de `definitions.js`, il faut relancer `npm run commandes`, sinon Discord affiche les anciennes commandes.
- Les dates sont stockées en `AAAA-MM-JJ` et calculées à l'heure de Paris (`Intl.DateTimeFormat`), sinon le récap changerait de jour à 23h ou 1h.
- Une date saisie sans année et passée depuis plus de 2 mois est mise à l'année suivante (ex : 15/01 tapé en novembre).
- Les mentions sont limitées aux personnes citées (`allowed_mentions`) : un texte avec @everyone ne notifie personne.
- `/message` répond en éphémère et poste le texte via l'API, sinon Discord afficherait "X a utilisé /message".

## Portail web et accès des IA
- Le portail est servi par le même Worker : `GET /` renvoie la page, `/api/...` lit et écrit dans la même base D1. Le bot et le site voient donc toujours les mêmes données.
- **Connexion** : mot de passe commun (secret `PORTAIL_MOT_DE_PASSE`). Si c'est le bon, le Worker pose un cookie `session = expiration.signature`. La signature est un HMAC-SHA256 de la date d'expiration avec le mot de passe comme clé : impossible à fabriquer sans le mot de passe, et changer le mot de passe coupe toutes les sessions. Le cookie est `HttpOnly` (illisible par le JavaScript de la page), `Secure` (HTTPS seulement) et `SameSite=Strict` (pas envoyé depuis un autre site).
- Limite assumée : avec un mot de passe commun, le site ne sait pas **qui** est connecté. La règle « seul le responsable termine » ne s'applique donc que sur Discord.
- **IA** : une clé d'API (secret `CLE_API`) envoyée dans `Authorization: Bearer <clé>`. `/mcp` parle le protocole MCP (JSON-RPC) : l'IA demande la liste des outils (`tools/list`) puis les appelle (`tools/call`). `/openapi.json` décrit l'API REST pour les GPT personnalisés. Les deux réutilisent les fonctions de `api.js`, donc les mêmes vérifications que le portail.
- Les textes venant des utilisateurs sont échappés (`esc`) avant d'être affichés dans la page, sinon un titre de tâche contenant du HTML pourrait exécuter du code chez les autres.
