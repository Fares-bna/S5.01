// Ce que fait chaque commande slash. Chaque fonction reçoit l'interaction et renvoie une réponse.

import { repondre, envoyerMessage } from './discord.js';
import { lireConfig, ecrireConfig, RAPPELS } from './config.js';
import { aujourdhui, lireDate, afficherDate, ecartJours } from './dates.js';
import {
  ajouterTache, lireTache, modifierTache, supprimerTache, listerTaches, ligneTache, legende,
  listerMembres, lierMembre, prenomDe, mention, STATUTS, TYPES
} from './taches.js';
import { envoyerRecap } from './rappels.js';

// Point d'entrée : choisit la bonne fonction selon la commande tapée
export async function traiterCommande(interaction, env, ctx) {
  const nom = interaction.data.name;
  const sous = interaction.data.options?.[0];
  const estSousCommande = sous?.type === 1;
  const options = lireOptions(estSousCommande ? sous.options : interaction.data.options);
  const outils = { interaction, env, ctx, options, db: env.DB, utilisateurs: interaction.data.resolved?.users ?? {} };

  const fonction = ACTIONS[estSousCommande ? `${nom} ${sous.name}` : nom];
  if (!fonction) return repondre('Commande inconnue. Tape `/aide`.', true);
  try {
    return await fonction(outils);
  } catch (e) {
    return repondre(`❌ Erreur : ${e.message}`, true);
  }
}

// [{name, value}] -> { name: value }
function lireOptions(liste = []) {
  return Object.fromEntries(liste.map(o => [o.name, o.value]));
}

// Prénom d'un utilisateur choisi dans une option @ (null si vide)
async function prenomOption(o, nomOption) {
  const id = o.options[nomOption];
  if (!id) return undefined;
  const u = o.utilisateurs[id];
  return prenomDe(o.db, id, u?.global_name || u?.username || id);
}

function dateOption(o, nomOption) {
  const texte = o.options[nomOption];
  if (texte === undefined) return undefined;
  const iso = lireDate(texte);
  if (!iso) throw new Error(`date "${texte}" invalide, utilise JJ/MM ou JJ/MM/AAAA`);
  return iso;
}

const ACTIONS = {
  // ---------- /tache ----------
  async 'tache ajouter'(o) {
    const t = {
      titre: o.options.titre,
      description: o.options.description,
      type: o.options.type ?? 'tache',
      responsable: await prenomOption(o, 'responsable'),
      partenaire: await prenomOption(o, 'partenaire'),
      debut: dateOption(o, 'debut'),
      fin: dateOption(o, 'fin'),
      etape: o.options.etape
    };
    if (t.debut && t.debut > t.fin) throw new Error('la date de début est après la date de fin');
    const id = await ajouterTache(o.db, t);
    const membres = await listerMembres(o.db);
    const nouvelle = { ...t, id, statut: 'a_faire' };
    return repondre(`✅ Tâche ajoutée\n${ligneTache(nouvelle, membres)}\n${legende([nouvelle])}`);
  },

  async 'tache liste'(o) {
    const prenom = o.options.membre ? await prenomOption(o, 'membre') : undefined;
    const taches = await listerTaches(o.db, {
      prenom, statut: o.options.statut, etape: o.options.etape, nonTerminees: !o.options.tout && !o.options.statut
    });
    if (taches.length === 0) return repondre('Aucune tâche trouvée.', true);
    const membres = await listerMembres(o.db);
    const titre = prenom ? `📋 Tâches de ${prenom}` : '📋 Tâches';
    return repondre([titre, ...taches.map(t => ligneTache(t, membres)), legende(taches)].join('\n'), true);
  },

  async 'tache voir'(o) {
    const t = await lireTache(o.db, o.options.id);
    if (!t) return repondre(`Pas de tâche #${o.options.id}.`, true);
    const membres = await listerMembres(o.db);
    return repondre([
      `**#${t.id} · ${t.titre}**`,
      `${TYPES[t.type]} · ${STATUTS[t.statut]}${t.etape ? ` · étape ${t.etape}` : ''}`,
      `📅 ${t.debut ? `${afficherDate(t.debut)} → ` : ''}${afficherDate(t.fin)}`,
      `👤 Responsable : ${mention(membres, t.responsable)} · Partenaire : ${mention(membres, t.partenaire)}`,
      t.description ? `📝 ${t.description}` : null
    ].filter(Boolean).join('\n'), true);
  },

  async 'tache modifier'(o) {
    const avant = await lireTache(o.db, o.options.id);
    if (!avant) return repondre(`Pas de tâche #${o.options.id}.`, true);
    const champs = {
      titre: o.options.titre, description: o.options.description, type: o.options.type, etape: o.options.etape,
      responsable: await prenomOption(o, 'responsable'), partenaire: await prenomOption(o, 'partenaire'),
      debut: dateOption(o, 'debut'), fin: dateOption(o, 'fin')
    };
    await modifierTache(o.db, avant.id, champs);
    const apres = await lireTache(o.db, avant.id);
    return repondre(`✏️ Tâche modifiée\n${ligneTache(apres, await listerMembres(o.db))}\n${legende([apres])}`);
  },

  async 'tache statut'(o) {
    return changerStatut(o, o.options.id, o.options.statut);
  },

  async 'tache terminer'(o) {
    return changerStatut(o, o.options.id, 'termine');
  },

  async 'tache supprimer'(o) {
    const ok = await supprimerTache(o.db, o.options.id);
    return repondre(ok ? `🗑️ Tâche #${o.options.id} supprimée.` : `Pas de tâche #${o.options.id}.`, !ok);
  },

  // ---------- /membre ----------
  async 'membre lier'(o) {
    await lierMembre(o.db, o.options.prenom, o.options.compte);
    return repondre(`🔗 ${o.options.prenom} = <@${o.options.compte}>`, true);
  },

  async 'membre liste'(o) {
    const membres = await listerMembres(o.db);
    if (membres.length === 0) return repondre('Aucun membre. Utilise `/membre lier`.', true);
    return repondre(['👥 Membres', ...membres.map(m => `${m.prenom} : ${m.discord_id ? `<@${m.discord_id}>` : 'pas lié'}`)].join('\n'), true);
  },

  // ---------- /config ----------
  async 'config voir'(o) {
    const c = await lireConfig(o.db);
    return repondre([
      '⚙️ **Réglages**',
      `Heure du récap : ${c.heure}`,
      `Salon : ${c.salon ? `<#${c.salon}>` : 'pas choisi (utilise /config salon)'}`,
      ...Object.entries(RAPPELS).map(([cle, nom]) => `${c[cle] === 'oui' ? '✅' : '❌'} ${nom}`)
    ].join('\n'), true);
  },

  async 'config heure'(o) {
    const m = String(o.options.heure).trim().match(/^(\d{1,2})[:hH](\d{2})?$/);
    if (!m || Number(m[1]) > 23 || Number(m[2] ?? 0) > 59) return repondre('Heure invalide, exemple : 08:00', true);
    const heure = `${m[1].padStart(2, '0')}:${m[2] ?? '00'}`;
    await ecrireConfig(o.db, 'heure', heure);
    return repondre(`⏰ Le récap sera envoyé chaque jour vers ${heure} (à 15 min près).`, true);
  },

  async 'config salon'(o) {
    await ecrireConfig(o.db, 'salon', o.options.salon);
    return repondre(`📢 Le récap sera posté dans <#${o.options.salon}>.`, true);
  },

  async 'config rappel'(o) {
    await ecrireConfig(o.db, o.options.type, o.options.actif ? 'oui' : 'non');
    return repondre(`${o.options.actif ? '✅ Activé' : '❌ Coupé'} : ${RAPPELS[o.options.type]}`, true);
  },

  // ---------- /recap ----------
  // Tâches pas terminées alors qu'elles ont commencé (ou sont en retard), regroupées par responsable
  async recap(o) {
    const jour = aujourdhui();
    const prenom = o.options.membre ? await prenomOption(o, 'membre') : undefined;
    const taches = (await listerTaches(o.db, { prenom, nonTerminees: true }))
      .filter(t => t.type === 'tache' && (t.debut ?? t.fin) <= jour);
    const prive = Boolean(o.options.prive);
    if (taches.length === 0) return repondre('🎉 Aucune tâche en attente, tout est à jour.', prive);
    const membres = await listerMembres(o.db);
    const parResponsable = {};
    for (const t of taches) (parResponsable[t.responsable ?? 'Sans responsable'] ??= []).push(t);
    const lignes = [`📋 **Tâches pas encore terminées** (${taches.length})`];
    for (const [resp, liste] of Object.entries(parResponsable).sort(([a], [b]) => a.localeCompare(b))) {
      lignes.push('', resp === 'Sans responsable' ? `**${resp}**` : mention(membres, resp));
      for (const t of liste) {
        const retard = ecartJours(jour, t.fin);
        const etat = retard < 0 ? `🚨 en retard de ${-retard} j` : retard === 0 ? '📌 à rendre aujourd\'hui' : `fin le ${afficherDate(t.fin)}`;
        lignes.push(`${STATUTS[t.statut].split(' ')[0]} \`#${t.id}\` ${t.titre} · ${etat}${t.partenaire ? ` · avec ${t.partenaire}` : ''}`);
      }
    }
    lignes.push('', 'Tâche finie ? Le responsable la confirme avec `/tache terminer id`.', legende(taches));
    const texte = lignes.join('\n');
    // Version privée : visible par l'auteur seulement, sans notifier personne
    if (prive) return repondre(texte, true);
    return repondre(texte, false, [...new Set([...texte.matchAll(/<@(\d+)>/g)].map(m => m[1]))]);
  },

  // ---------- /rappel ----------
  async rappel(o) {
    const config = await lireConfig(o.db);
    const salon = config.salon || o.interaction.channel_id;
    // Envoi en arrière-plan : Discord attend une réponse en moins de 3 s
    o.ctx.waitUntil(envoyerRecap(o.env, aujourdhui(), config, salon).then(envoye => {
      if (!envoye) return envoyerMessage(o.env, o.interaction.channel_id, '😴 Rien à signaler aujourd\'hui.');
    }));
    return repondre(`📨 Récap envoyé dans <#${salon}>.`, true);
  },

  // ---------- /message ----------
  async message(o) {
    // Le texte est posté par le bot lui-même ; seule la personne voit la confirmation
    o.ctx.waitUntil(envoyerMessage(o.env, o.interaction.channel_id, o.options.texte));
    return repondre('🤫 Message envoyé.', true);
  },

  // ---------- /aide ----------
  async aide() {
    return repondre([
      '📖 **Aide du bot**',
      '',
      '**Tâches**',
      '`/tache ajouter` titre, fin, responsable, partenaire, début, description, type, étape',
      '`/tache liste` tâches pas terminées (filtres : membre, statut, étape, tout)',
      '`/tache voir id` · `/tache modifier id …` · `/tache statut id` · `/tache supprimer id`',
      '`/tache terminer id` : le responsable (ou un admin) confirme que la tâche est finie',
      '`/recap` : tâches commencées ou en retard pas encore terminées, par responsable, visible par tous (options : membre, prive:True pour toi seul)',
      'Types : 📝 tâche, 🟡 jalon interne, 🔴 rendu prof. Dates en JJ/MM.',
      '',
      '**Membres** : `/membre lier prénom @compte` pour que les rappels mentionnent la bonne personne · `/membre liste`',
      '',
      '**Rappels** : un seul récap par jour à l\'heure choisie, rien si rien à signaler. Il mentionne responsable et partenaire pour : en retard, à rendre aujourd\'hui, demain, dans 3 jours (règle J-3), début de tâche ; jalons et rendus à J-7 et J-1 ; récap de la semaine le lundi.',
      '',
      '**Admins** : `/config voir` · `/config heure 08:00` · `/config salon #salon` · `/config rappel type oui/non` · `/rappel` (envoie le récap maintenant) · `/message texte` (fait parler le bot)'
    ].join('\n'), true);
  }
};

async function changerStatut(o, id, statut) {
  const t = await lireTache(o.db, id);
  if (!t) return repondre(`Pas de tâche #${id}.`, true);
  if (statut === 'termine' && !(await peutTerminer(o, t))) {
    return repondre(`Seul le responsable (${t.responsable ?? 'aucun'}) ou un admin peut confirmer que \`#${id}\` est terminée.`, true);
  }
  await modifierTache(o.db, id, { statut });
  return repondre(`${STATUTS[statut]} : \`#${id}\` ${t.titre}`);
}

// Le responsable de la tâche, ou un admin (permission "Gérer le serveur"), peut la marquer terminée
async function peutTerminer(o, tache) {
  const membre = o.interaction.member;
  if (membre && (BigInt(membre.permissions ?? 0) & 0x20n) !== 0n) return true;
  const ligne = await o.db.prepare('SELECT prenom FROM membres WHERE discord_id = ?').bind(membre?.user?.id ?? '').first();
  return Boolean(ligne && tache.responsable && ligne.prenom === tache.responsable);
}
