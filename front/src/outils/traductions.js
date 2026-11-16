// src/outils/traductions.js

const COMPOSANTS_NHTSA = {
  'SERVICE BRAKES': 'Freins',
  'SERVICE BRAKES, HYDRAULIC': 'Freins hydrauliques',
  'SERVICE BRAKES, AIR': 'Freins pneumatiques',
  'PARKING BRAKE': 'Frein de stationnement',
  'SUSPENSION': 'Suspension',
  'STEERING': 'Direction',
  'ENGINE': 'Moteur',
  'ENGINE AND ENGINE COOLING': 'Moteur et refroidissement',
  'POWER TRAIN': 'Transmission',
  'ELECTRICAL SYSTEM': 'Système électrique',
  'FUEL SYSTEM, GASOLINE': 'Système de carburant (Essence)',
  'FUEL SYSTEM, DIESEL': 'Système de carburant (Diesel)',
  'EXTERIOR LIGHTING': 'Éclairage extérieur',
  'AIR BAGS': 'Airbags',
  'TIRES': 'Pneumatiques',
  'WHEELS': 'Roues',
  'STRUCTURE': 'Carrosserie / Châssis',
  'VISIBILITY': 'Visibilité / Pare-brise'
}

const ACCENTS_GRAVITE = {
  moderee: 'Modérée',
  elevee: 'Élevée'
}

export function traduireComposant(nomAnglais) {
  if (!nomAnglais) return ''
  const cle = String(nomAnglais).trim().toUpperCase()
  return COMPOSANTS_NHTSA[cle] || nomAnglais
}

export function traduireListeComposants(liste = []) {
  if (!Array.isArray(liste)) return ''
  return liste.map(traduireComposant).join(', ')
}

export function formaterGravite(gravite) {
  if (!gravite) return ''
  if (ACCENTS_GRAVITE[gravite]) return ACCENTS_GRAVITE[gravite]
  const str = String(gravite)
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase()
}