// Accès pour les IA (Claude, ChatGPT, Gemini…).
// - /mcp : serveur MCP (Model Context Protocol), le standard pour brancher des outils dans une IA.
//   Clé dans l'en-tête "Authorization: Bearer <clé>", ou dans l'adresse /mcp/<clé> pour les applis
//   qui ne permettent pas d'ajouter un en-tête.
// - /openapi.json : description de l'API REST, pour les GPT personnalisés (Actions) et les autres outils.
// Les deux réutilisent les mêmes fonctions que le portail (ACTIONS dans api.js).

import { ACTIONS, cleValide } from './api.js';
import { lireTache, listerTaches } from './taches.js';
import { lireConfig, RAPPELS } from './config.js';
import { aujourdhui, ecartJours, ajouterJours } from './dates.js';

const VERSIONS = ['2025-06-18', '2025-03-26', '2024-11-05'];

// ---------- Les outils proposés à l'IA ----------

const STATUT = { type: 'string', enum: ['a_faire', 'en_cours', 'termine'], description: 'a_faire, en_cours ou termine' };
const CHAMPS_TACHE = {
  titre: { type: 'string', description: 'Titre court de la tâche' },
  description: { type: 'string' },
  responsable: { type: 'string', description: 'Prénom d\'un membre (voir lister_membres), vide pour personne' },
  partenaire: { type: 'string', description: 'Prénom d\'un membre, vide pour personne' },
  debut: { type: 'string', description: 'Date de début AAAA-MM-JJ (facultatif)' },
  fin: { type: 'string', description: 'Date de fin AAAA-MM-JJ' },
  type: { type: 'string', enum: ['tache', 'jalon', 'rendu'], description: 'tache, jalon (jalon interne) ou rendu (rendu prof)' },
  etape: { type: 'integer', description: 'Étape du projet (1 à 4)' },
  statut: STATUT
};

const OUTILS = [
  {
    name: 'tableau_de_bord',
    description: 'Résumé du projet : date du jour, tâches en retard, à rendre cette semaine, prochains jalons et rendus, avancement par étape.',
    inputSchema: { type: 'object', properties: {} },
    lecture: true,
    run: env => tableauDeBord(env)
  },
  {
    name: 'lister_taches',
    description: 'Liste les tâches. Par défaut seulement celles qui ne sont pas terminées.',
    inputSchema: {
      type: 'object',
      properties: {
        personne: { type: 'string', description: 'Prénom : tâches où la personne est responsable ou partenaire' },
        statut: STATUT,
        etape: { type: 'integer' },
        inclure_terminees: { type: 'boolean', description: 'true pour avoir aussi les tâches terminées' }
      }
    },
    lecture: true,
    run: (env, a) => listerTaches(env.DB, {
      prenom: a.personne, statut: a.statut, etape: a.etape, nonTerminees: !a.inclure_terminees && !a.statut
    })
  },
  {
    name: 'voir_tache',
    description: 'Détail d\'une tâche par son numéro.',
    inputSchema: { type: 'object', properties: { id: { type: 'integer' } }, required: ['id'] },
    lecture: true,
    run: async (env, a) => (await lireTache(env.DB, a.id)) ?? erreur(`Pas de tâche #${a.id}`)
  },
  {
    name: 'ajouter_tache',
    description: 'Ajoute une tâche (titre et date de fin obligatoires).',
    inputSchema: { type: 'object', properties: CHAMPS_TACHE, required: ['titre', 'fin'] },
    run: (env, a) => ACTIONS.creerTache(env, a)
  },
  {
    name: 'modifier_tache',
    description: 'Modifie une tâche : seuls les champs donnés changent. Pour marquer une tâche finie : statut = termine.',
    inputSchema: { type: 'object', properties: { id: { type: 'integer' }, ...CHAMPS_TACHE }, required: ['id'] },
    run: (env, { id, ...champs }) => ACTIONS.changerTache(env, id, champs)
  },
  {
    name: 'supprimer_tache',
    description: 'Supprime définitivement une tâche. Demande confirmation à l\'utilisateur avant.',
    inputSchema: { type: 'object', properties: { id: { type: 'integer' } }, required: ['id'] },
    destructif: true,
    run: (env, a) => ACTIONS.effacerTache(env, a.id)
  },
  {
    name: 'lister_membres',
    description: 'Membres du groupe (prénom et identifiant Discord). Pour mentionner quelqu\'un dans un message : <@identifiant>.',
    inputSchema: { type: 'object', properties: {} },
    lecture: true,
    run: async env => (await ACTIONS.donnees(env)).membres
  },
  {
    name: 'lister_salons',
    description: 'Salons texte du serveur Discord (id et nom).',
    inputSchema: { type: 'object', properties: {} },
    lecture: true,
    run: env => ACTIONS.listerSalons(env)
  },
  {
    name: 'envoyer_message',
    description: 'Poste un message sur Discord au nom du bot. Les @everyone et @here sont bloqués. Montre le texte à l\'utilisateur avant d\'envoyer.',
    inputSchema: {
      type: 'object',
      properties: {
        contenu: { type: 'string', description: 'Texte du message (Markdown Discord)' },
        salon: { type: 'string', description: 'Id du salon (voir lister_salons). Vide : le salon du récap' }
      },
      required: ['contenu']
    },
    destructif: true,
    run: (env, a) => ACTIONS.message(env, a)
  },
  {
    name: 'lire_reglages',
    description: 'Réglages du récap quotidien : heure, salon, rappels activés.',
    inputSchema: { type: 'object', properties: {} },
    lecture: true,
    run: async env => {
      const c = await lireConfig(env.DB);
      return { heure: c.heure, salon: c.salon, rappels: Object.fromEntries(Object.entries(RAPPELS).map(([k, nom]) => [k, { nom, actif: c[k] === 'oui' }])) };
    }
  },
  {
    name: 'modifier_reglage',
    description: 'Change un réglage : heure (HH:MM), salon (id) ou un rappel (' + Object.keys(RAPPELS).join(', ') + ') avec oui/non.',
    inputSchema: {
      type: 'object',
      properties: { cle: { type: 'string', enum: ['heure', 'salon', ...Object.keys(RAPPELS)] }, valeur: { type: 'string' } },
      required: ['cle', 'valeur']
    },
    run: (env, a) => ACTIONS.changerConfig(env, a)
  }
];

async function tableauDeBord(env) {
  const j = aujourdhui();
  const toutes = await listerTaches(env.DB);
  const taches = toutes.filter(t => t.type === 'tache');
  const court = t => ({ id: t.id, titre: t.titre, responsable: t.responsable, partenaire: t.partenaire, fin: t.fin, statut: t.statut });
  const etapes = {};
  for (const t of taches) if (t.etape) { (etapes[t.etape] ??= { terminees: 0, total: 0 }).total++; if (t.statut === 'termine') etapes[t.etape].terminees++; }
  return {
    aujourdhui: j,
    en_retard: taches.filter(t => t.statut !== 'termine' && t.fin < j).map(t => ({ ...court(t), jours_de_retard: -ecartJours(j, t.fin) })),
    cette_semaine: taches.filter(t => t.statut !== 'termine' && t.fin >= j && t.fin <= ajouterJours(j, 6)).map(court),
    prochains_jalons_et_rendus: toutes.filter(t => t.type !== 'tache' && t.fin >= j).slice(0, 5).map(t => ({ id: t.id, titre: t.titre, type: t.type, fin: t.fin })),
    avancement_par_etape: etapes
  };
}

// ---------- Protocole MCP (JSON-RPC sur HTTP) ----------

export async function traiterMcp(requete, env) {
  const url = new URL(requete.url);
  const cleUrl = url.pathname.startsWith('/mcp/') ? decodeURIComponent(url.pathname.slice(5)) : null;
  if (!(await cleValide(requete, env, cleUrl))) {
    return new Response(JSON.stringify({ erreur: 'Clé d\'API manquante ou incorrecte' }), {
      status: 401, headers: { 'Content-Type': 'application/json', 'WWW-Authenticate': 'Bearer' }
    });
  }
  if (requete.method === 'DELETE') return new Response(null, { status: 204 }); // fin de session : rien à faire
  if (requete.method !== 'POST') return new Response('Méthode non gérée', { status: 405, headers: { Allow: 'POST' } });

  let message;
  try { message = await requete.json(); } catch { return rpc(null, null, { code: -32700, message: 'JSON invalide' }); }

  // Un lot de messages ou un seul
  const liste = Array.isArray(message) ? message : [message];
  const reponses = [];
  for (const m of liste) {
    const r = await traiterMessage(m, env);
    if (r) reponses.push(r);
  }
  if (reponses.length === 0) return new Response(null, { status: 202 }); // seulement des notifications
  return new Response(JSON.stringify(Array.isArray(message) ? reponses : reponses[0]), { headers: { 'Content-Type': 'application/json' } });
}

async function traiterMessage(m, env) {
  if (!m || m.jsonrpc !== '2.0' || typeof m.method !== 'string') return { jsonrpc: '2.0', id: m?.id ?? null, error: { code: -32600, message: 'Requête invalide' } };
  if (m.id === undefined) return null; // notification (ex : notifications/initialized) : pas de réponse
  const ok = result => ({ jsonrpc: '2.0', id: m.id, result });

  switch (m.method) {
    case 'initialize': {
      const demandee = m.params?.protocolVersion;
      return ok({
        protocolVersion: VERSIONS.includes(demandee) ? demandee : VERSIONS[0],
        capabilities: { tools: {} },
        serverInfo: { name: 'bot-deadlines', version: '1.0.0' },
        instructions: 'Outils de suivi des tâches de la SAÉ S5.01 (projet DiagDuo, 6 membres). Les dates sont au format AAAA-MM-JJ, heure de Paris. ' +
          'Utilise lister_membres pour les prénoms exacts. Avant de supprimer une tâche ou d\'envoyer un message Discord, demande confirmation à l\'utilisateur.'
      });
    }
    case 'ping':
      return ok({});
    case 'tools/list':
      return ok({
        tools: OUTILS.map(o => ({
          name: o.name, description: o.description, inputSchema: o.inputSchema,
          annotations: { readOnlyHint: Boolean(o.lecture), destructiveHint: Boolean(o.destructif) }
        }))
      });
    case 'tools/call': {
      const outil = OUTILS.find(o => o.name === m.params?.name);
      if (!outil) return { jsonrpc: '2.0', id: m.id, error: { code: -32602, message: `Outil inconnu : ${m.params?.name}` } };
      try {
        const resultat = await outil.run(env, m.params.arguments ?? {});
        return ok({ content: [{ type: 'text', text: JSON.stringify(resultat, null, 2) }] });
      } catch (e) {
        // Erreur métier (date invalide, tâche introuvable…) : on la renvoie à l'IA pour qu'elle corrige
        return ok({ content: [{ type: 'text', text: `Erreur : ${e.message}` }], isError: true });
      }
    }
    default:
      return { jsonrpc: '2.0', id: m.id, error: { code: -32601, message: `Méthode inconnue : ${m.method}` } };
  }
}

function rpc(id, result, error) {
  return new Response(JSON.stringify({ jsonrpc: '2.0', id, ...(error ? { error } : { result }) }), { headers: { 'Content-Type': 'application/json' } });
}

function erreur(texte) {
  throw new Error(texte);
}

// ---------- Description OpenAPI de l'API REST ----------

export function openapi(requete) {
  const tache = { type: 'object', properties: CHAMPS_TACHE };
  const corps = schema => ({ required: true, content: { 'application/json': { schema } } });
  const reponse = { 200: { description: 'OK', content: { 'application/json': { schema: { type: 'object' } } } } };
  const id = { name: 'id', in: 'path', required: true, schema: { type: 'integer' } };
  const doc = {
    openapi: '3.1.0',
    info: {
      title: 'Bot deadlines SAÉ S5.01',
      version: '1.0.0',
      description: 'Tâches et deadlines du groupe. Dates au format AAAA-MM-JJ. Authentification : en-tête Authorization: Bearer <clé>.'
    },
    servers: [{ url: new URL(requete.url).origin }],
    components: { securitySchemes: { cle: { type: 'http', scheme: 'bearer' } } },
    security: [{ cle: [] }],
    paths: {
      '/api/donnees': { get: { operationId: 'lireDonnees', summary: 'Toutes les tâches, les membres et les réglages', responses: reponse } },
      '/api/taches': { post: { operationId: 'ajouterTache', summary: 'Ajouter une tâche (titre et fin obligatoires)', requestBody: corps({ ...tache, required: ['titre', 'fin'] }), responses: reponse } },
      '/api/taches/{id}': {
        patch: { operationId: 'modifierTache', summary: 'Modifier une tâche (seuls les champs envoyés changent)', parameters: [id], requestBody: corps(tache), responses: reponse },
        delete: { operationId: 'supprimerTache', summary: 'Supprimer une tâche', parameters: [id], responses: reponse }
      },
      '/api/salons': { get: { operationId: 'listerSalons', summary: 'Salons texte du serveur Discord', responses: reponse } },
      '/api/message': {
        post: {
          operationId: 'envoyerMessage', summary: 'Poster un message sur Discord au nom du bot',
          requestBody: corps({ type: 'object', properties: { contenu: { type: 'string' }, salon: { type: 'string', description: 'Id du salon, vide = salon du récap' } }, required: ['contenu'] }),
          responses: reponse
        }
      },
      '/api/config': {
        put: {
          operationId: 'modifierReglage', summary: 'Changer un réglage (heure, salon, rappels oui/non)',
          requestBody: corps({ type: 'object', properties: { cle: { type: 'string' }, valeur: { type: 'string' } }, required: ['cle', 'valeur'] }),
          responses: reponse
        }
      }
    }
  };
  return new Response(JSON.stringify(doc, null, 2), { headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' } });
}
