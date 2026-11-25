// Petites fonctions de dates. Toutes les dates sont stockées en AAAA-MM-JJ.

// Date du jour à Paris, au format AAAA-MM-JJ
export function aujourdhui(maintenant = new Date()) {
  return new Intl.DateTimeFormat('fr-CA', { timeZone: 'Europe/Paris' }).format(maintenant);
}

// Heure actuelle à Paris, au format HH:MM
export function heureParis(maintenant = new Date()) {
  return new Intl.DateTimeFormat('fr-FR', { timeZone: 'Europe/Paris', hour: '2-digit', minute: '2-digit' }).format(maintenant);
}

// Jour de la semaine à Paris (1 = lundi ... 7 = dimanche)
export function jourSemaine(iso) {
  const j = new Date(iso + 'T12:00:00Z').getUTCDay();
  return j === 0 ? 7 : j;
}

// Nombre de jours entre deux dates AAAA-MM-JJ (b - a)
export function ecartJours(a, b) {
  return Math.round((Date.parse(b + 'T12:00:00Z') - Date.parse(a + 'T12:00:00Z')) / 86400000);
}

export function ajouterJours(iso, n) {
  const d = new Date(iso + 'T12:00:00Z');
  d.setUTCDate(d.getUTCDate() + n);
  return d.toISOString().slice(0, 10);
}

// "18/11/2026" ou "18/11" -> "2026-11-18" (null si invalide)
export function lireDate(texte, reference = aujourdhui()) {
  const m = String(texte || '').trim().match(/^(\d{1,2})\/(\d{1,2})(?:\/(\d{2,4}))?$/);
  if (!m) return null;
  let annee = m[3] ? Number(m[3]) : Number(reference.slice(0, 4));
  if (annee < 100) annee += 2000;
  const iso = `${annee}-${m[2].padStart(2, '0')}-${m[1].padStart(2, '0')}`;
  const d = new Date(iso + 'T12:00:00Z');
  if (isNaN(d) || d.toISOString().slice(0, 10) !== iso) return null;
  // Sans année : si la date est passée depuis plus de 2 mois, on prend l'année suivante (ex : 15/01 saisi en novembre)
  if (!m[3] && ecartJours(reference, iso) < -60) return `${annee + 1}${iso.slice(4)}`;
  return iso;
}

// "2026-11-18" -> "18/11"
export function afficherDate(iso) {
  if (!iso) return '?';
  return `${iso.slice(8, 10)}/${iso.slice(5, 7)}`;
}
