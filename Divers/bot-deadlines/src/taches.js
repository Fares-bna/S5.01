// Accès à la base : tâches et membres.

export const STATUTS = { a_faire: '⬜ À faire', en_cours: '🟦 En cours', termine: '✅ Terminé' };
export const TYPES = { tache: '📝 Tâche', jalon: '🟡 Jalon interne', rendu: '🔴 Rendu prof' };

// ---------- Membres ----------

export async function listerMembres(db) {
  const { results } = await db.prepare('SELECT prenom, discord_id FROM membres ORDER BY prenom').all();
  return results;
}

// Associe un prénom à un compte Discord (crée ou met à jour)
export async function lierMembre(db, prenom, discordId) {
  await db.batch([
    db.prepare('UPDATE membres SET discord_id = NULL WHERE discord_id = ?').bind(discordId),
    db.prepare('INSERT INTO membres (prenom, discord_id) VALUES (?, ?) ON CONFLICT(prenom) DO UPDATE SET discord_id = excluded.discord_id')
      .bind(prenom, discordId)
  ]);
}

// Retrouve le prénom d'un compte Discord. S'il est inconnu, on l'ajoute avec son nom Discord.
export async function prenomDe(db, discordId, nomDiscord) {
  const ligne = await db.prepare('SELECT prenom FROM membres WHERE discord_id = ?').bind(discordId).first();
  if (ligne) return ligne.prenom;
  await db.prepare('INSERT OR IGNORE INTO membres (prenom, discord_id) VALUES (?, ?)').bind(nomDiscord, discordId).run();
  return nomDiscord;
}

// "Fares" -> "<@123>" si le compte est lié, sinon "**Fares**"
export function mention(membres, prenom) {
  if (!prenom) return '—';
  const m = membres.find(x => x.prenom === prenom);
  return m && m.discord_id ? `<@${m.discord_id}>` : `**${prenom}**`;
}

// ---------- Tâches ----------

export async function ajouterTache(db, t) {
  const res = await db.prepare(
    'INSERT INTO taches (titre, description, type, responsable, partenaire, debut, fin, statut, etape) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)'
  ).bind(t.titre, t.description ?? null, t.type ?? 'tache', t.responsable ?? null, t.partenaire ?? null,
    t.debut ?? null, t.fin, t.statut ?? 'a_faire', t.etape ?? null).run();
  return res.meta.last_row_id;
}

export async function lireTache(db, id) {
  return db.prepare('SELECT * FROM taches WHERE id = ?').bind(id).first();
}

// Modifie seulement les champs fournis
export async function modifierTache(db, id, champs) {
  const cles = Object.keys(champs).filter(c => champs[c] !== undefined);
  if (cles.length === 0) return;
  const sql = `UPDATE taches SET ${cles.map(c => `${c} = ?`).join(', ')} WHERE id = ?`;
  await db.prepare(sql).bind(...cles.map(c => champs[c]), id).run();
}

export async function supprimerTache(db, id) {
  const res = await db.prepare('DELETE FROM taches WHERE id = ?').bind(id).run();
  return res.meta.changes > 0;
}

// Filtres possibles : prenom (responsable ou partenaire), statut, etape
export async function listerTaches(db, filtres = {}) {
  const conditions = [];
  const valeurs = [];
  if (filtres.prenom) { conditions.push('(responsable = ? OR partenaire = ?)'); valeurs.push(filtres.prenom, filtres.prenom); }
  if (filtres.statut) { conditions.push('statut = ?'); valeurs.push(filtres.statut); }
  if (filtres.nonTerminees) conditions.push("statut != 'termine'");
  if (filtres.etape) { conditions.push('etape = ?'); valeurs.push(filtres.etape); }
  const where = conditions.length ? 'WHERE ' + conditions.join(' AND ') : '';
  const { results } = await db.prepare(`SELECT * FROM taches ${where} ORDER BY fin, id`).bind(...valeurs).all();
  return results;
}

// Une ligne lisible pour une tâche
export function ligneTache(t, membres, avecMentions = false) {
  const qui = avecMentions
    ? [t.responsable, t.partenaire].filter(Boolean).map(p => mention(membres, p)).join(' + ') || 'tout le monde'
    : [t.responsable, t.partenaire].filter(Boolean).join(' / ') || 'tout le monde';
  const dates = t.debut ? `${fr(t.debut)} → ${fr(t.fin)}` : fr(t.fin);
  return `${iconeTache(t)} \`#${t.id}\` **${t.titre}** · ${dates} · ${qui}`;
}

// Icône d'une ligne : le statut pour une tâche, le type pour un jalon ou un rendu
export function iconeTache(t) {
  return t.type === 'tache' ? STATUTS[t.statut].split(' ')[0] : TYPES[t.type].split(' ')[0];
}

// Légende en petit texte : les 3 statuts toujours, jalon et rendu seulement s'il y en a dans la liste
// ex : "-# ⬜ À faire · 🟦 En cours · ✅ Terminé · 🔴 Rendu prof"
export function legende(taches) {
  const types = [TYPES.jalon, TYPES.rendu].filter(l => taches.some(t => iconeTache(t) === l.split(' ')[0]));
  return `-# ${[...Object.values(STATUTS), ...types].join(' · ')}`;
}

function fr(iso) {
  return `${iso.slice(8, 10)}/${iso.slice(5, 7)}`;
}
