<script setup>
import { ref } from 'vue'
import SaisieVue from './vues/SaisieVue.vue'
import ResultatsVue from './vues/ResultatsVue.vue'
import { rechercherVehicules, obtenirRecommandations } from './services/api'
import logoUrl from './assets/logo.svg'


// Variables pour gérer la navigation et stocker les résultats

const etapes = ['01 Saisie', '02 Diagnostic', '03 Performances']
const etapeActive = ref(0)
const derniereSaisie = ref(null)
const donneesDiagnostic = ref(null)
const chargementEnCours = ref(false)
const erreurApi = ref('')

async function gererDiagnostic(donnees) {
  derniereSaisie.value = donnees
  chargementEnCours.value = true
  erreurApi.value = ''

  try {
    // On cherche le véhicule dans fausses_donnees.json (via api.js) pour récupérer l'id_vehicule.
    const vehiculesTrouves = await rechercherVehicules({
      marque: donnees.marque,
      modele: donnees.modele,
      annee: donnees.annee,
      carburant: donnees.carburant,
      boite: donnees.boite
    })

    // Là, si le véhicule n'est pas dans les données (en base), on affiche une erreur
    if (!vehiculesTrouves || vehiculesTrouves.length === 0) {
      erreurApi.value = `Aucun véhicule trouvé en base pour ${donnees.marque} ${donnees.modele} (${donnees.annee}). Veuillez vérifier les informations saisies.`
      return
    }

    const vehiculeRetenu = vehiculesTrouves[0]

    // Ici, on récupère  les résultats des deux approches (heuristique et embeddings)
    const resultat = await obtenirRecommandations({
      id_vehicule: vehiculeRetenu.id_vehicule,
      description: donnees.description,
      carburant: donnees.carburant,
      boite: donnees.boite,
      symptomes: donnees.symptomes
    })

    // On stocke le résultat et on bascule sur la vue des résultats
    donneesDiagnostic.value = resultat
    etapeActive.value = 1
  } catch (err) {
    erreurApi.value = err.message || 'Une erreur est survenue lors du diagnostic.'
  } finally {
    chargementEnCours.value = false
  }
}

// C'est ici juste ce qui permet de revenir au formulaire quand on clique sur "Modifier la saisie" on repasse à l'étape 0 et on vide l'erreur éventuelle
function retourSaisie() {
  etapeActive.value = 0
  erreurApi.value = ''
}
</script>
 <!-- A partir d'ici, c'est  le layout de l'application (la navigation, le logo, le titre, etc.) -->
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
    </div>

    <nav class="stepper-nav">
      <button
        v-for="(etape, index) in etapes"
        :key="etape"
        type="button"
        class="stepper-btn"
        :class="{ active: etapeActive === index }"
        @click="etapeActive = index"
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

    <!-- Etape 3 (Dashboard / Benchmark / Performances) -->
    <section
      v-else
      class="card-atelier"
    >
      <span class="step-badge">ÉTAPE 03 — BENCHMARK</span>
      <h1 class="page-title">
        Performances des moteurs
      </h1>
      <p class="page-subtitle">
        Synthèse comparative des deux approches sur le dernier diagnostic exécuté.
      </p>

      <div
        v-if="donneesDiagnostic"
        class="vehicule-summary-banner"
      >
        <div class="summary-item">
          <span class="summary-label">Pistes Heuristiques</span>
          <strong class="summary-value font-mono">
            {{ donneesDiagnostic.heuristique?.nb_resultats || 0 }} résultat(s)
          </strong>
        </div>
        <div class="summary-item">
          <span class="summary-label">Temps Heuristique</span>
          <strong class="summary-value font-mono">
            {{ donneesDiagnostic.heuristique?.temps_calcul_ms || 'N/A' }} ms
          </strong>
        </div>
        <div class="summary-item">
          <span class="summary-label">Pistes Embeddings (IA)</span>
          <strong class="summary-value font-mono">
            {{ donneesDiagnostic.embeddings?.nb_resultats || 0 }} résultat(s)
          </strong>
        </div>
        <div class="summary-item">
          <span class="summary-label">Temps Embeddings</span>
          <strong class="summary-value font-mono">
            {{ donneesDiagnostic.embeddings?.temps_calcul_ms || 'N/A' }} ms
          </strong>
        </div>
      </div>

      <p
        v-else
        class="page-subtitle"
      >
        Lancez un diagnostic à l'étape 01 pour afficher les métriques comparatives.
      </p>
    </section>
  </main>
</template>