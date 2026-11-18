# Accès pour les IA

Le bot peut être piloté par une IA (Claude, ChatGPT, Gemini…) : lister les tâches, en ajouter, les modifier, envoyer un message au nom du bot, changer les réglages.

## Avant tout : la clé

1. Génère une clé longue : `openssl rand -hex 32`
2. Mets-la en secret : `npx wrangler secret put CLE_API` (colle la clé)
3. Garde-la pour toi : elle donne les mêmes droits que le portail. Jamais dans le code, sur GitHub ou sur Discord.
   Pour la changer (fuite), relance la commande avec une nouvelle clé : l'ancienne ne marche plus.

Adresse du bot : `https://bot-deadlines.bot-deadlines.workers.dev` (notée `<adresse>` ci-dessous).

## Option 1 : MCP (le plus simple pour discuter avec l'IA)

MCP est un standard pour brancher des outils dans une IA. L'IA voit directement les outils :
`tableau_de_bord`, `lister_taches`, `voir_tache`, `ajouter_tache`, `modifier_tache`, `supprimer_tache`,
`lister_membres`, `lister_salons`, `envoyer_message`, `lire_reglages`, `modifier_reglage`.

Deux façons de donner la clé :
- en-tête `Authorization: Bearer <clé>` sur l'adresse `<adresse>/mcp` (préférable) ;
- ou dans l'adresse elle-même : `<adresse>/mcp/<clé>`, pour les applis qui ne permettent pas d'ajouter un en-tête. Dans ce cas, l'adresse complète est aussi secrète que la clé.

Exemples (les menus des applis changent souvent, vérifie dans leur aide si un nom ne correspond plus) :
- **Claude Code** : `claude mcp add --transport http bot-deadlines <adresse>/mcp --header "Authorization: Bearer <clé>"`
- **Claude (appli / claude.ai)** : Réglages > Connecteurs > Ajouter un connecteur personnalisé, URL `<adresse>/mcp/<clé>`
- **ChatGPT** : mode développeur > Connecteurs > créer, URL `<adresse>/mcp/<clé>`, sans authentification
- **Gemini CLI** : dans `~/.gemini/settings.json`
  ```json
  { "mcpServers": { "bot-deadlines": { "httpUrl": "<adresse>/mcp", "headers": { "Authorization": "Bearer <clé>" } } } }
  ```

Ensuite il suffit de demander : « ajoute une tâche "Préparer la démo" pour Hocine, fin le 20/11 », « qu'est-ce qui est en retard ? », « passe la tâche 13 en terminée ».
Les outils `supprimer_tache` et `envoyer_message` sont marqués comme sensibles : l'IA doit demander confirmation avant.

## Option 2 : API REST + OpenAPI (GPT personnalisés, scripts)

La description complète est sur `<adresse>/openapi.json`.
- **GPT personnalisé** : Configurer > Actions > Importer depuis une URL : `<adresse>/openapi.json`. Authentification : Clé d'API, type Bearer, colle la clé.
- **Script ou curl** :
  ```bash
  curl -H "Authorization: Bearer $CLE" <adresse>/api/donnees
  curl -X POST -H "Authorization: Bearer $CLE" -H "Content-Type: application/json" \
       -d '{"titre":"Préparer la démo","fin":"2026-11-20","responsable":"Hocine"}' <adresse>/api/taches
  ```

| Méthode | Route | Rôle |
|---|---|---|
| GET | `/api/donnees` | tâches, membres, réglages |
| POST | `/api/taches` | ajouter (titre et fin obligatoires) |
| PATCH | `/api/taches/{id}` | modifier (seuls les champs envoyés changent) |
| DELETE | `/api/taches/{id}` | supprimer |
| GET | `/api/salons` | salons Discord |
| POST | `/api/message` | message au nom du bot (`contenu`, `salon` facultatif) |
| PUT | `/api/config` | réglage (`cle`, `valeur`) |

Dates au format `AAAA-MM-JJ`. Statuts : `a_faire`, `en_cours`, `termine`. Types : `tache`, `jalon`, `rendu`.
