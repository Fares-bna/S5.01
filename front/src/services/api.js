import faussesDonnees from '../../../api/mock/fausses_donnees.json'

export async function getSymptomes() {
  return faussesDonnees.symptomes
}

export async function rechercherVehicules({ marque, modele, annee }) {
  return faussesDonnees.vehicules.filter(
    v =>
      v.marque.toUpperCase() === marque.trim().toUpperCase() &&
      v.modele.toUpperCase() === modele.trim().toUpperCase() &&
      (v.annee === Number(annee) || v.annee === null)
  )
}

export async function obtenirRecommandations({ id_vehicule, carburant, boite }) {
  const vehicule = faussesDonnees.vehicules.find(v => v.id_vehicule === Number(id_vehicule))

  if (!vehicule) {
    throw new Error(faussesDonnees.erreurs.VEHICULE_INCONNU.erreur.message)
  }

  return {
    vehicule: {
      ...vehicule,
      carburant: carburant || vehicule.carburant,
      boite: boite || vehicule.boite
    },
    ...faussesDonnees.recommandation
  }
}

export async function getMetriques() {
  return faussesDonnees.metriques
}