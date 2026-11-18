// front/src/services/api.js
// tous les appels vers l'api passent par ce fichier, les vues ne savent pas d'où viennent les données
import faussesDonnees from '../../../api/mock/fausses_donnees.json'

// "/api" est redirigé vers FastAPI par vite (voir vite.config.js)
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

// mettre VITE_USE_MOCK=true dans front/.env.local pour repasser sur les fausses données
export const UTILISER_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

// messages affichés selon le code d'erreur (le front se base sur le code, pas sur le message de l'api)
const MESSAGES_ERREUR = {
  VEHICULE_INCONNU: "Ce véhicule n'existe pas dans la base de données.",
  REQUETE_INVALIDE: 'Certaines informations saisies ne sont pas valides.',
  NON_TROUVE: "Cette fonctionnalité n'est pas encore disponible côté API.",
  ERREUR_INTERNE: 'Le serveur a rencontré une erreur, réessayez plus tard.',
  API_INJOIGNABLE: "Impossible de joindre l'API, vérifiez qu'elle est bien lancée (uvicorn)."
}

function creerErreur(code, message, details = null) {
  const erreur = new Error(message)
  erreur.code = code
  erreur.details = details
  return erreur
}

export function messagePourUtilisateur(erreur) {
  let message = MESSAGES_ERREUR[erreur.code] || 'Une erreur inattendue est survenue.'

  // pour une requête invalide on précise quels champs sont en cause
  if (erreur.code === 'REQUETE_INVALIDE' && erreur.details) {
    const champs = erreur.details.map((detail) => detail.champ)
    message += ' Champ(s) à corriger : ' + champs.join(', ') + '.'
  }

  return message
}

async function requeteHttp(endpoint, options = {}) {
  let reponse

  try {
    reponse = await fetch(API_BASE_URL + endpoint, {
      headers: { 'Content-Type': 'application/json' },
      ...options
    })
  } catch {
    // fetch plante seulement si le serveur ne répond pas du tout
    throw creerErreur('API_INJOIGNABLE', MESSAGES_ERREUR.API_INJOIGNABLE)
  }

  const donnees = await reponse.json().catch(() => null)

  if (!reponse.ok) {
    // si uvicorn est éteint, le proxy de vite renvoie une erreur 500 sans json
    if (!donnees?.erreur) {
      throw creerErreur('API_INJOIGNABLE', MESSAGES_ERREUR.API_INJOIGNABLE)
    }
    const { code, message, details } = donnees.erreur
    throw creerErreur(code, message, details)
  }

  return donnees
}

// pas encore de route /symptomes dans l'api : on prend la liste S1 à S10 des fausses données
// (les id sont les mêmes que dans les règles de l'heuristique, donc ça marche aussi avec la vraie api)
export async function getSymptomes() {
  return faussesDonnees.symptomes
}

export async function rechercherVehicules({ marque, modele, annee }) {
  // les données NHTSA sont en majuscules
  const marqueMaj = marque.trim().toUpperCase()
  const modeleMaj = modele.trim().toUpperCase()

  if (UTILISER_MOCK) {
    return faussesDonnees.vehicules.filter(
      (v) =>
        v.marque.toUpperCase() === marqueMaj &&
        v.modele.toUpperCase() === modeleMaj &&
        (v.annee === Number(annee) || v.annee === null)
    )
  }

  const params = new URLSearchParams({ marque: marqueMaj, modele: modeleMaj, annee: annee })
  return requeteHttp('/vehicules?' + params.toString())
}

// scenarioMock : 'recommandation' | 'recommandation_b_indisponible' | 'recommandation_aucun_resultat'
export async function obtenirRecommandations(saisie, scenarioMock = 'recommandation') {
  // on envoie seulement les champs du contrat d'api (pas le code OBD ni le kilométrage)
  const corps = {
    id_vehicule: Number(saisie.id_vehicule),
    description: saisie.description,
    carburant: saisie.carburant || null,
    boite: saisie.boite || null,
    symptomes: saisie.symptomes || []
  }

  if (UTILISER_MOCK) {
    const vehicule = faussesDonnees.vehicules.find((v) => v.id_vehicule === corps.id_vehicule)
    if (!vehicule) {
      const { code, message } = faussesDonnees.erreurs.VEHICULE_INCONNU.erreur
      throw creerErreur(code, message)
    }
    return faussesDonnees[scenarioMock] || faussesDonnees.recommandation
  }

  return requeteHttp('/recommandations', {
    method: 'POST',
    body: JSON.stringify(corps)
  })
}

export async function getMetriques() {
  if (UTILISER_MOCK) {
    return faussesDonnees.metriques
  }
  return requeteHttp('/metriques')
}
