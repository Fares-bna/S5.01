// API du portail web : connexion par mot de passe commun, puis lecture/écriture dans la même base que le bot.
// Le mot de passe est un secret Cloudflare : npx wrangler secret put PORTAIL_MOT_DE_PASSE
// Une IA (ou un script) peut aussi appeler l'API avec la clé : en-tête "Authorization: Bearer <clé>"
// (secret CLE_API). Les fonctions de ACTIONS sont partagées avec le serveur MCP (mcp.js).

import { envoyerMessage } from './discord.js';
import { lireConfig, ecrireConfig, REGLAGES_PAR_DEFAUT } from './config.js';
import { aujourdhui } from './dates.js';
import {
  ajouterTache, lireTache, modifierTache, supprimerTache, listerTaches, listerMembres, lierMembre, STATUTS, TYPES
} from './taches.js';

const API_DISCORD = 'https://discord.com/api/v10';
const DUREE_SESSION = 30 * 24 * 3600; // 30 jours, en secondes

// Point d'entrée : toutes les URL qui commencent par /api/
export async function traiterApi(requete, env, ctx) {
  const url = new URL(requete.url);
  const chemin = url.pathname.replace(/\/+$/, '');
  const methode = requete.method;

  try {
    if (chemin === '/api/connexion' && methode === 'POST') return connexion(requete, env);
    if (chemin === '/api/deconnexion' && methode === 'POST') return deconnexion();

    // Tout le reste demande d'être connecté (cookie du portail) ou d'envoyer la clé d'API
    if (!(await sessionValide(requete, env)) && !(await cleValide(requete, env))) return json({ erreur: 'Non connecté' }, 401);

    // Les écritures doivent être du JSON : un formulaire d'un autre site ne peut pas en envoyer sans être bloqué
    const corps = methode === 'GET' || methode === 'DELETE' ? {} : await lireJson(requete);

    if (chemin === '/api/donnees' && methode === 'GET') return json(await ACTIONS.donnees(env));
    if (chemin === '/api/salons' && methode === 'GET') return json(await ACTIONS.listerSalons(env));
    if (chemin === '/api/taches' && methode === 'POST') return json(await ACTIONS.creerTache(env, corps), 201);
    const m = chemin.match(/^\/api\/taches\/(\d+)$/);
    if (m && methode === 'PATCH') return json(await ACTIONS.changerTache(env, Number(m[1]), corps));
    if (m && methode === 'DELETE') return json(await ACTIONS.effacerTache(env, Number(m[1])));
    if (chemin === '/api/config' && methode === 'PUT') return json(await ACTIONS.changerConfig(env, corps));
    if (chemin === '/api/membres' && methode === 'PUT') return json(await ACTIONS.changerMembre(env, corps));
    if (chemin === '/api/message' && methode === 'POST') return json(await ACTIONS.message(env, corps));
    return json({ erreur: 'Route inconnue' }, 404);
  } catch (e) {
    return json({ erreur: e.message }, e.statut ?? 500);
  }
}

// ---------- Connexion ----------

async function connexion(requete, env) {
  if (!env.PORTAIL_MOT_DE_PASSE) return json({ erreur: 'Portail pas configuré (secret PORTAIL_MOT_DE_PASSE manquant).' }, 503);
  const { mot_de_passe } = await lireJson(requete);
  if (!(await egalSur(String(mot_de_passe ?? ''), env.PORTAIL_MOT_DE_PASSE))) {
    await new Promise(r => setTimeout(r, 1000)); // ralentit les essais au hasard
    return json({ erreur: 'Mot de passe incorrect' }, 401);
  }
  const expiration = Math.floor(Date.now() / 1000) + DUREE_SESSION;
  const jeton = `${expiration}.${await signer(String(expiration), env.PORTAIL_MOT_DE_PASSE)}`;
  return json({ ok: true }, 200, {
    'Set-Cookie': `session=${jeton}; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=${DUREE_SESSION}`
  });
}

function deconnexion() {
  return json({ ok: true }, 200, { 'Set-Cookie': 'session=; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=0' });
}

// Le cookie contient "expiration.signature". La signature est calculée avec le mot de passe :
// si on change le mot de passe, toutes les sessions sont coupées.
async function sessionValide(requete, env) {
  if (!env.PORTAIL_MOT_DE_PASSE) return false;
  const cookie = requete.headers.get('Cookie') ?? '';
  const jeton = cookie.split(/;\s*/).find(c => c.startsWith('session='))?.slice(8);
  if (!jeton) return false;
  const [expiration, signature] = jeton.split('.');
  if (!expiration || !signature || Number(expiration) < Date.now() / 1000) return false;
  return egalSur(signature, await signer(expiration, env.PORTAIL_MOT_DE_PASSE));
}

// Clé d'API envoyée par une IA ou un script : "Authorization: Bearer <clé>"
export async function cleValide(requete, env, cleRecue = null) {
  if (!env.CLE_API || env.CLE_API.length < 20) return false; // clé absente ou trop courte : accès IA coupé
  const cle = cleRecue ?? (requete.headers.get('Authorization') ?? '').replace(/^Bearer\s+/i, '');
  return Boolean(cle) && egalSur(cle, env.CLE_API);
}

async function signer(texte, secret) {
  const cle = await crypto.subtle.importKey('raw', new TextEncoder().encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const sig = await crypto.subtle.sign('HMAC', cle, new TextEncoder().encode(texte));
  return [...new Uint8Array(sig)].map(o => o.toString(16).padStart(2, '0')).join('');
}

// Compare deux textes sans s'arrêter au premier caractère différent (évite de deviner par le temps de réponse)
async function egalSur(a, b) {
  const [ha, hb] = await Promise.all([a, b].map(t => crypto.subtle.digest('SHA-256', new TextEncoder().encode(t))));
  const x = new Uint8Array(ha), y = new Uint8Array(hb);
  let diff = 0;
  for (let i = 0; i < x.length; i++) diff |= x[i] ^ y[i];
  return diff === 0;
}

// ---------- Actions (renvoient des données, lancent une erreur si quelque chose ne va pas) ----------

export const ACTIONS = { donnees, listerSalons, creerTache, changerTache, effacerTache, changerConfig, changerMembre, message };

async function donnees(env) {
  const [taches, membres, config] = await Promise.all([listerTaches(env.DB), listerMembres(env.DB), lireConfig(env.DB)]);
  return { aujourdhui: aujourdhui(), taches, membres, config, statuts: STATUTS, types: TYPES };
}

// Salons texte des serveurs où le bot est invité
async function listerSalons(env) {
  const serveurs = await discord(env, '/users/@me/guilds');
  const salons = [];
  for (const s of serveurs) {
    const liste = await discord(env, `/guilds/${s.id}/channels`);
    for (const c of liste) if (c.type === 0 || c.type === 5) salons.push({ id: c.id, nom: c.name, position: c.position, serveur: s.name });
  }
  return salons.sort((a, b) => a.position - b.position);
}

async function discord(env, chemin) {
  const rep = await fetch(API_DISCORD + chemin, { headers: { Authorization: `Bot ${env.DISCORD_TOKEN}` } });
  if (!rep.ok) throw new Error(`Discord a refusé (${rep.status})`);
  return rep.json();
}

// ---------- Tâches ----------

async function creerTache(env, c) {
  const t = await verifierTache(env, c, true);
  const id = await ajouterTache(env.DB, t);
  return lireTache(env.DB, id);
}

async function changerTache(env, id, c) {
  const avant = await lireTache(env.DB, id);
  if (!avant) throw erreur(`Pas de tâche #${id}`, 404);
  const champs = await verifierTache(env, c, false);
  const debut = champs.debut !== undefined ? champs.debut : avant.debut;
  const fin = champs.fin ?? avant.fin;
  if (debut && debut > fin) throw erreur('La date de début est après la date de fin');
  await modifierTache(env.DB, id, champs);
  return lireTache(env.DB, id);
}

async function effacerTache(env, id) {
  const avant = await lireTache(env.DB, id);
  if (!avant || !(await supprimerTache(env.DB, id))) throw erreur(`Pas de tâche #${id}`, 404);
  return { ok: true, supprimee: avant };
}

// Vérifie les champs envoyés par le site. complet = true pour une nouvelle tâche (titre et fin obligatoires).
async function verifierTache(env, c, complet) {
  const prenoms = (await listerMembres(env.DB)).map(m => m.prenom);
  const t = {};
  if (c.titre !== undefined || complet) {
    t.titre = String(c.titre ?? '').trim();
    if (!t.titre) throw erreur('Le titre est obligatoire');
    if (t.titre.length > 200) throw erreur('Titre trop long (200 caractères max)');
  }
  if (c.description !== undefined) t.description = String(c.description ?? '').trim().slice(0, 1000) || null;
  if (c.type !== undefined) { if (!TYPES[c.type]) throw erreur('Type inconnu'); t.type = c.type; }
  if (c.statut !== undefined) { if (!STATUTS[c.statut]) throw erreur('Statut inconnu'); t.statut = c.statut; }
  for (const role of ['responsable', 'partenaire']) {
    if (c[role] === undefined) continue;
    t[role] = c[role] || null;
    if (t[role] && !prenoms.includes(t[role])) throw erreur(`Membre inconnu : ${t[role]}`);
  }
  if (c.debut !== undefined) t.debut = c.debut ? dateValide(c.debut) : null;
  if (c.fin !== undefined || complet) t.fin = dateValide(c.fin);
  if (c.etape !== undefined) {
    t.etape = c.etape === '' || c.etape === null ? null : Number(c.etape);
    if (t.etape !== null && !(Number.isInteger(t.etape) && t.etape >= 1 && t.etape <= 9)) throw erreur('Étape invalide');
  }
  if (complet && t.debut && t.debut > t.fin) throw erreur('La date de début est après la date de fin');
  return t;
}

function dateValide(iso) {
  const d = new Date(String(iso) + 'T12:00:00Z');
  if (!/^\d{4}-\d{2}-\d{2}$/.test(String(iso)) || isNaN(d) || d.toISOString().slice(0, 10) !== iso) throw erreur('Date invalide');
  return iso;
}

// ---------- Réglages et membres ----------

async function changerConfig(env, { cle, valeur }) {
  if (!(cle in REGLAGES_PAR_DEFAUT) || cle === 'dernier_envoi') throw erreur('Réglage inconnu');
  let v = String(valeur ?? '').trim();
  if (cle === 'heure') {
    const m = v.match(/^(\d{1,2}):(\d{2})$/);
    if (!m || Number(m[1]) > 23 || Number(m[2]) > 59) throw erreur('Heure invalide, exemple : 08:00');
    v = `${m[1].padStart(2, '0')}:${m[2]}`;
  } else if (cle === 'salon') {
    if (v && !/^\d{5,25}$/.test(v)) throw erreur('Salon invalide');
  } else if (v !== 'oui' && v !== 'non') throw erreur('Valeur attendue : oui ou non');
  await ecrireConfig(env.DB, cle, v);
  return { ok: true, cle, valeur: v };
}

async function changerMembre(env, { prenom, discord_id }) {
  const p = String(prenom ?? '').trim();
  const id = String(discord_id ?? '').trim();
  if (!p || p.length > 50) throw erreur('Prénom invalide');
  if (id && !/^\d{5,25}$/.test(id)) throw erreur('Identifiant Discord invalide (que des chiffres)');
  if (id) await lierMembre(env.DB, p, id);
  else await env.DB.prepare('INSERT INTO membres (prenom) VALUES (?) ON CONFLICT(prenom) DO UPDATE SET discord_id = NULL').bind(p).run();
  return { ok: true, prenom: p, discord_id: id || null };
}

// ---------- Message au nom du bot ----------

async function message(env, { salon, contenu }) {
  const texte = String(contenu ?? '').trim();
  if (!salon) salon = (await lireConfig(env.DB)).salon; // par défaut : le salon du récap
  if (!/^\d{5,25}$/.test(String(salon ?? ''))) throw erreur('Choisis un salon');
  if (!texte) throw erreur('Le message est vide');
  if (texte.length > 4000) throw erreur('Message trop long (4000 caractères max)');
  // Comme /message : les @everyone et @here sont bloqués, et seules les personnes mentionnées avec <@id> sont notifiées
  const mentions = [...new Set([...texte.matchAll(/<@!?(\d+)>/g)].map(m => m[1]))];
  await envoyerMessage(env, salon, texte, mentions);
  return { ok: true, salon };
}

// ---------- Outils ----------

async function lireJson(requete) {
  if (!(requete.headers.get('Content-Type') ?? '').includes('application/json')) throw erreur('JSON attendu', 415);
  try { return await requete.json(); } catch { throw erreur('JSON invalide'); }
}

function erreur(texte, statut = 400) {
  return Object.assign(new Error(texte), { statut });
}

function json(donnees, statut = 200, entetes = {}) {
  return new Response(JSON.stringify(donnees), {
    status: statut,
    headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store', ...entetes }
  });
}
