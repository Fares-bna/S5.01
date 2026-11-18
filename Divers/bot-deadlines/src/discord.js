// Échanges avec Discord : vérification de signature, réponses, envoi de messages.

const API = 'https://discord.com/api/v10';

// Types de réponse aux interactions (doc Discord)
export const REPONSE = { PONG: 1, MESSAGE: 4 };
export const EPHEMERE = 64; // message visible seulement par la personne qui a tapé la commande

// Discord signe chaque requête : on vérifie qu'elle vient bien de lui (clé publique Ed25519)
export async function signatureValide(requete, corps, clePublique) {
  const signature = requete.headers.get('X-Signature-Ed25519');
  const horodatage = requete.headers.get('X-Signature-Timestamp');
  if (!signature || !horodatage) return false;
  const cle = await crypto.subtle.importKey('raw', hexEnOctets(clePublique), { name: 'Ed25519' }, false, ['verify']);
  return crypto.subtle.verify('Ed25519', cle, hexEnOctets(signature), new TextEncoder().encode(horodatage + corps));
}

function hexEnOctets(hex) {
  return new Uint8Array(hex.match(/.{1,2}/g).map(o => parseInt(o, 16)));
}

export function repondreJson(donnees) {
  return new Response(JSON.stringify(donnees), { headers: { 'Content-Type': 'application/json' } });
}

// Réponse à une commande. ephemere = true : seul l'auteur la voit.
// mentions : ids des personnes à notifier (par défaut personne)
export function repondre(contenu, ephemere = false, mentions = []) {
  return repondreJson({
    type: REPONSE.MESSAGE,
    data: { content: tronquer(contenu), flags: ephemere ? EPHEMERE : 0, allowed_mentions: { parse: [], users: mentions.slice(0, 100) } }
  });
}

// Envoie un message dans un salon au nom du bot. Les @everyone/@here sont toujours bloqués.
export async function envoyerMessage(env, salonId, contenu, mentionsAutorisees = []) {
  for (const morceau of decouper(contenu)) {
    const rep = await fetch(`${API}/channels/${salonId}/messages`, {
      method: 'POST',
      headers: { Authorization: `Bot ${env.DISCORD_TOKEN}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: morceau, allowed_mentions: { parse: [], users: mentionsAutorisees.slice(0, 100) } })
    });
    if (!rep.ok) throw new Error(`Discord a refusé le message (${rep.status}) : ${await rep.text()}`);
  }
}

// Discord limite un message à 2000 caractères : on coupe proprement aux retours à la ligne
export function decouper(texte, max = 1900) {
  const morceaux = [];
  let courant = '';
  for (const ligne of texte.split('\n')) {
    if ((courant + '\n' + ligne).length > max && courant) { morceaux.push(courant); courant = ''; }
    courant = courant ? courant + '\n' + ligne : ligne;
  }
  if (courant) morceaux.push(courant);
  return morceaux;
}

function tronquer(texte) {
  return texte.length > 1990 ? texte.slice(0, 1980) + '\n…' : texte;
}
