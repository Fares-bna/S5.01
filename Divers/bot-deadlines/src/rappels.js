// Récap quotidien : construit le message du jour et l'envoie si c'est l'heure.

import { lireConfig, ecrireConfig } from './config.js';
import { aujourdhui, heureParis, ecartJours, jourSemaine, ajouterJours } from './dates.js';
import { listerTaches, listerMembres, ligneTache, legende, mention } from './taches.js';
import { envoyerMessage } from './discord.js';

// Appelé toutes les 15 min par Cloudflare
export async function verifierHeureRecap(env, maintenant = new Date()) {
  const config = await lireConfig(env.DB);
  const jour = aujourdhui(maintenant);
  if (!config.salon) return;                       // pas de salon choisi
  if (config.dernier_envoi === jour) return;       // déjà envoyé aujourd'hui
  if (heureParis(maintenant) < config.heure) return; // pas encore l'heure
  await envoyerRecap(env, jour, config);
  await ecrireConfig(env.DB, 'dernier_envoi', jour);
}

// Construit et envoie le récap (aussi utilisé par /rappel maintenant)
export async function envoyerRecap(env, jour, config, salonId = config.salon) {
  const { texte, mentions } = await construireRecap(env.DB, jour, config);
  if (!texte) return false; // rien à dire : pas de message (anti-spam)
  await envoyerMessage(env, salonId, texte, mentions);
  return true;
}

export async function construireRecap(db, jour, config) {
  const taches = await listerTaches(db, { nonTerminees: true });
  const membres = await listerMembres(db);
  const actif = cle => config[cle] === 'oui';

  // Chaque section : titre + liste de tâches
  const sections = [
    { cle: 'rappel_retard', titre: '🚨 **En retard**', filtre: t => t.type === 'tache' && ecartJours(jour, t.fin) < 0 },
    { cle: 'rappel_jour', titre: '📌 **À rendre aujourd\'hui**', filtre: t => t.type === 'tache' && t.fin === jour },
    { cle: 'rappel_veille', titre: '⏰ **À rendre demain**', filtre: t => t.type === 'tache' && ecartJours(jour, t.fin) === 1 },
    { cle: 'rappel_j3', titre: '⚠️ **Fin dans 3 jours** (pas commencée = réattribuée, règle J-3)', filtre: t => t.type === 'tache' && ecartJours(jour, t.fin) === 3 },
    { cle: 'rappel_debut', titre: '🚀 **Commence aujourd\'hui**', filtre: t => t.type === 'tache' && t.debut === jour },
    { cle: 'rappel_jalon_j1', titre: '📣 **Jalon / rendu demain**', filtre: t => t.type !== 'tache' && ecartJours(jour, t.fin) === 1 },
    { cle: 'rappel_jalon_j7', titre: '🗓️ **Jalon / rendu dans 7 jours**', filtre: t => t.type !== 'tache' && ecartJours(jour, t.fin) === 7 }
  ];

  const lignes = [];
  const dejaCites = new Set();
  const affichees = []; // tâches affichées avec une icône, pour la légende
  for (const s of sections) {
    if (!actif(s.cle)) continue;
    const liste = taches.filter(t => s.filtre(t) && !dejaCites.has(t.id));
    if (liste.length === 0) continue;
    lignes.push('', s.titre);
    for (const t of liste) {
      dejaCites.add(t.id);
      affichees.push(t);
      const retard = s.cle === 'rappel_retard' ? ` (depuis ${-ecartJours(jour, t.fin)} j)` : '';
      lignes.push(ligneTache(t, membres, true) + retard);
    }
  }

  // Le lundi : ce que chacun a en cours cette semaine
  if (actif('recap_hebdo') && jourSemaine(jour) === 1) {
    const finSemaine = ajouterJours(jour, 6);
    const semaine = taches.filter(t => t.type === 'tache' && (t.debut ?? t.fin) <= finSemaine && t.fin >= jour);
    if (semaine.length) {
      lignes.push('', '📅 **Cette semaine**');
      const parPersonne = {};
      for (const t of semaine) {
        for (const p of [t.responsable, t.partenaire].filter(Boolean)) (parPersonne[p] ??= []).push(`\`#${t.id}\` ${t.titre}`);
      }
      for (const [p, liste] of Object.entries(parPersonne).sort(([a], [b]) => a.localeCompare(b))) lignes.push(`${mention(membres, p)} : ${liste.join(', ')}`);
    }
  }

  if (lignes.length === 0) return { texte: '', mentions: [] };
  if (affichees.length) lignes.push('', legende(affichees));
  const texte = `**☀️ Récap du ${jour.slice(8, 10)}/${jour.slice(5, 7)}**` + lignes.join('\n');
  // Seules les personnes citées dans le message sont notifiées
  const mentions = [...texte.matchAll(/<@(\d+)>/g)].map(m => m[1]);
  return { texte, mentions: [...new Set(mentions)] };
}
