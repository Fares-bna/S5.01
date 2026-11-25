// Réglages du bot : valeurs par défaut + lecture/écriture dans la table config.

export const REGLAGES_PAR_DEFAUT = {
  heure: '08:00',          // heure du récap quotidien (heure de Paris)
  salon: '',               // id du salon où poster le récap
  // Types de rappels (activables avec /config rappel)
  rappel_debut: 'oui',     // la tâche commence aujourd'hui
  rappel_j3: 'oui',        // fin dans 3 jours (règle J-3)
  rappel_veille: 'oui',    // à rendre demain
  rappel_jour: 'oui',      // à rendre aujourd'hui
  rappel_retard: 'oui',    // date dépassée et pas terminée
  rappel_jalon_j7: 'oui',  // jalon ou rendu prof dans 7 jours
  rappel_jalon_j1: 'oui',  // jalon ou rendu prof demain
  recap_hebdo: 'oui',      // le lundi : tâches de la semaine par personne
  dernier_envoi: ''        // date du dernier récap (évite les doublons)
};

// Description lisible de chaque rappel (utilisée par /config et /aide)
export const RAPPELS = {
  rappel_debut: 'Tâche qui commence aujourd\'hui',
  rappel_j3: 'Fin dans 3 jours (règle J-3)',
  rappel_veille: 'À rendre demain',
  rappel_jour: 'À rendre aujourd\'hui',
  rappel_retard: 'En retard',
  rappel_jalon_j7: 'Jalon / rendu prof dans 7 jours',
  rappel_jalon_j1: 'Jalon / rendu prof demain',
  recap_hebdo: 'Récap de la semaine le lundi'
};

export async function lireConfig(db) {
  const { results } = await db.prepare('SELECT cle, valeur FROM config').all();
  const config = { ...REGLAGES_PAR_DEFAUT };
  for (const ligne of results) config[ligne.cle] = ligne.valeur;
  return config;
}

export async function ecrireConfig(db, cle, valeur) {
  await db.prepare('INSERT INTO config (cle, valeur) VALUES (?, ?) ON CONFLICT(cle) DO UPDATE SET valeur = excluded.valeur')
    .bind(cle, valeur).run();
}
