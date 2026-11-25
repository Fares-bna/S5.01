// Envoie la liste des commandes à Discord (à relancer après chaque changement de definitions.js).
// Usage : DISCORD_TOKEN=... DISCORD_APPLICATION_ID=... DISCORD_GUILD_ID=... npm run commandes
import { COMMANDES } from '../src/definitions.js';

const { DISCORD_TOKEN, DISCORD_APPLICATION_ID, DISCORD_GUILD_ID } = process.env;
if (!DISCORD_TOKEN || !DISCORD_APPLICATION_ID || !DISCORD_GUILD_ID) {
  console.error('Il manque DISCORD_TOKEN, DISCORD_APPLICATION_ID ou DISCORD_GUILD_ID');
  process.exit(1);
}

// Commandes du serveur (visibles tout de suite, contrairement aux commandes globales)
const url = `https://discord.com/api/v10/applications/${DISCORD_APPLICATION_ID}/guilds/${DISCORD_GUILD_ID}/commands`;
const rep = await fetch(url, {
  method: 'PUT',
  headers: { Authorization: `Bot ${DISCORD_TOKEN}`, 'Content-Type': 'application/json' },
  body: JSON.stringify(COMMANDES)
});
console.log(rep.ok ? `✅ ${COMMANDES.length} commandes enregistrées` : `❌ ${rep.status} ${await rep.text()}`);
