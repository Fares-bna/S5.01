<script setup>
import { ref } from 'vue'
import SaisieVue from './vues/SaisieVue.vue'
import ResultatsVue from './vues/ResultatsVue.vue'
import DashboardVue from './vues/DashboardVue.vue'
import { rechercherVehicules, obtenirRecommandations, messagePourUtilisateur, UTILISER_MOCK } from './services/api'
import logoUrl from './assets/logo.svg'

// Variables pour gérer la navigation et stocker les résultats
const etapes = ['01 Saisie', '02 Diagnostic', '03 Performances']
const etapeActive = ref(0)
const derniereSaisie = ref(null)
const donneesDiagnostic = ref(null)
const chargementEnCours = ref(false)
const erreurApi = ref('')

// l'api peut renvoyer plusieurs véhicules pour un même modèle (motorisations différentes)
// on prend celui qui a la bonne année et le bon carburant, sinon la bonne année, sinon le premier
function choisirVehicule(vehicules, saisie) {
  const memeAnneeEtCarburant = vehicules.find(
    (v) => v.annee === saisie.annee && v.carburant === saisie.carburant
  )
  const memeAnnee = vehicules.find((v) => v.annee === saisie.annee)

  return memeAnneeEtCarburant || memeAnnee || vehicules[0]
}

async function gererDiagnostic(donnees) {
  derniereSaisie.value = donnees
  chargementEnCours.value = true
  erreurApi.value = ''

  try {
    // On cherche le véhicule en base pour récupérer son id_vehicule
    const vehiculesTrouves = await rechercherVehicules({
      marque: donnees.marque,
      modele: donnees.modele,
      annee: donnees.annee
    })

    // Là, si le véhicule n'est pas en base, on affiche une erreur
    if (vehiculesTrouves.length === 0) {
      erreurApi.value = `Aucun véhicule trouvé en base pour ${donnees.marque} ${donnees.modele} (${donnees.annee}). Veuillez vérifier les informations saisies.`
      return
    }

    const vehiculeRetenu = choisirVehicule(vehiculesTrouves, donnees)

    // Ici, on récupère les résultats des deux approches (heuristique et embeddings)
    const resultat = await obtenirRecommandations({
      id_vehicule: vehiculeRetenu.id_vehicule,
      description: donnees.description,
      carburant: donnees.carburant,
      boite: donnees.boite,
      symptomes: donnees.symptomes
    })

    // la réponse de l'api ne contient pas le véhicule donc on le rajoute pour l'affichage
    // (le carburant et la boîte saisis remplacent les valeurs souvent vides de la NHTSA)
    donneesDiagnostic.value = {
      ...resultat,
      vehicule: {
        ...vehiculeRetenu,
        carburant: donnees.carburant || vehiculeRetenu.carburant,
        boite: donnees.boite || vehiculeRetenu.boite
      }
    }
    etapeActive.value = 1
  } catch (err) {
    console.error(err)
    erreurApi.value = messagePourUtilisateur(err)
  } finally {
    chargementEnCours.value = false
  }
}

// Permet de revenir au formulaire quand on clique sur "Modifier la saisie"
function retourSaisie() {
  etapeActive.value = 0
  erreurApi.value = ''
}

// changement d'étape avec le menu, on enlève l'erreur affichée
function changerEtape(index) {
  etapeActive.value = index
  erreurApi.value = ''
}
</script>

<template>
  <header class="app-header">
    <div class="brand-container">
      <img
        :src="logoUrl"
        alt="Logo DiagDuo"
        class="brand-logo-icon"
      >
      <div class="brand-text-group">
        <p class="brand-logo">
          DiagDuo<span>.</span>
        </p>
        <span class="brand-slogan">Deux diagnostics valent mieux qu'un</span>
      </div>
      <span
        v-if="UTILISER_MOCK"
        class="badge-mode-demo font-mono"
        title="Fausses données (VITE_USE_MOCK=true)"
      >DONNÉES FICTIVES</span>
    </div>

    <nav class="stepper-nav">
      <button
        v-for="(etape, index) in etapes"
        :key="etape"
        type="button"
        class="stepper-btn"
        :class="{ active: etapeActive === index }"
        :disabled="chargementEnCours"
        @click="changerEtape(index)"
      >
        {{ etape }}
      </button>
    </nav>
  </header>

  <main class="page-container">
    <p
      v-if="erreurApi"
      class="alert-error banner-error"
    >
      {{ erreurApi }}
    </p>

    <div
      v-if="chargementEnCours"
      class="loading-state card-atelier"
    >
      <p class="font-mono">
        Interrogation des moteurs Heuristique et Embeddings en cours...
      </p>
    </div>

    <!-- Etape 1 : Saisie du véhicule et symptomes -->
    <SaisieVue
      v-else-if="etapeActive === 0"
      @lancer-diagnostic="gererDiagnostic"
    />

    <!-- Etape 2 : Resultats du formulaire -->
    <template v-else-if="etapeActive === 1">
      <ResultatsVue
        v-if="donneesDiagnostic"
        :diagnostic="donneesDiagnostic"
        :saisie-initiale="derniereSaisie"
        @nouveau-diagnostic="retourSaisie"
        @aller-performances="etapeActive = 2"
      />

      <section
        v-else
        class="card-atelier"
      >
        <span class="step-badge">ÉTAPE 02 — DOUBLE DIAGNOSTIC</span>
        <h1 class="page-title">
          Comparaison Algorithmique en attente
        </h1>
        <p class="page-subtitle">
          Veuillez d'abord renseigner un véhicule et ses symptômes à l'étape 01 pour lancer l'analyse.
        </p>
        <div class="form-actions">
          <button
            type="button"
            class="btn-primary"
            @click="etapeActive = 0"
          >
            Aller à la saisie →
          </button>
        </div>
      </section>
    </template>

    <!-- Etape 3 : Dashboard / Benchmark / Performances -->
    <DashboardVue
      v-else
      :dernier-diagnostic="donneesDiagnostic"
      @retour-diagnostic="changerEtape(1)"
    />
  </main>
</template>