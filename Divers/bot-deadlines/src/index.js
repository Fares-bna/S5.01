// Point d'entrée du Worker Cloudflare.
// - fetch : Discord envoie ici chaque commande tapée (POST /), le portail web est servi sur GET / et /api/,
//   les IA passent par /mcp et /openapi.json
// - scheduled : Cloudflare l'appelle toutes les 15 min pour le récap

import { signatureValide, repondreJson, REPONSE } from './discord.js';
import { traiterCommande } from './commandes.js';
import { verifierHeureRecap } from './rappels.js';
import { traiterApi } from './api.js';
import { traiterMcp, openapi } from './mcp.js';
import PORTAIL from './portail.html';

export default {
  async fetch(requete, env, ctx) {
    const url = new URL(requete.url);
    if (url.pathname.startsWith('/api/')) return traiterApi(requete, env, ctx);
    if (url.pathname === '/mcp' || url.pathname.startsWith('/mcp/')) return traiterMcp(requete, env); // accès des IA
    if (url.pathname === '/openapi.json') return openapi(requete);
    if (requete.method === 'GET') {
      if (url.pathname !== '/') return new Response('Page introuvable', { status: 404 });
      return new Response(PORTAIL, { headers: ENTETES_PORTAIL });
    }
    if (requete.method !== 'POST') return new Response('Méthode non gérée', { status: 405 });

    const corps = await requete.text();
    if (!(await signatureValide(requete, corps, env.DISCORD_PUBLIC_KEY))) {
      return new Response('Signature invalide', { status: 401 });
    }

    const interaction = JSON.parse(corps);
    if (interaction.type === 1) return repondreJson({ type: REPONSE.PONG }); // test de Discord
    if (interaction.type === 2) return traiterCommande(interaction, env, ctx); // commande slash
    return new Response('Type non géré', { status: 400 });
  },

  async scheduled(evenement, env, ctx) {
    ctx.waitUntil(verifierHeureRecap(env));
  }
};

// Le portail ne charge rien d'extérieur : on l'interdit, et on empêche de l'afficher dans un autre site
const ENTETES_PORTAIL = {
  'Content-Type': 'text/html; charset=utf-8',
  'Content-Security-Policy': "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; img-src 'self' data:; frame-ancestors 'none'",
  'X-Frame-Options': 'DENY',
  'Referrer-Policy': 'no-referrer'
};
