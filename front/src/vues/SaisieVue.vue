<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { getSymptomes } from '../services/api'

const emit = defineEmits(['lancer-diagnostic'])

const catalogueVehicules = {
  Chevrolet: ['Equinox', 'Malibu', 'Silverado', 'Tahoe'],
  Ford: ['Explorer', 'F-150', 'Focus', 'Mustang'],
  Honda: ['Accord', 'Civic', 'CR-V', 'Pilot'],
  Hyundai: ['Elantra', 'Santa Fe', 'Sonata', 'Tucson'],
  Jeep: ['Cherokee', 'Compass', 'Grand Cherokee', 'Wrangler'],
  'Land Rover': ['Range Rover', 'Evoque', 'Discovery'],
  Nissan: ['Altima', 'Rogue', 'Sentra', 'Pathfinder'],
  Opel: ['Corsa', 'Astra', 'Mokka'],
  Peugeot: ['208', '308', '3008'],
  Renault: ['Clio', 'Captur', 'Mégane IV', 'Austral'],
  Subaru: ['Forester', 'Impreza', 'Outback', 'Crosstrek'],
  Tesla: ['Model 3', 'Model S', 'Model X', 'Model Y'],
  Toyota: ['Camry', 'Corolla', 'RAV4', 'Yaris']
}

const listeMarques = Object.keys(catalogueVehicules)
const listeSymptomesDisponibles = ref([])
const messageErreur = ref('')

const formulaire = reactive({
  marque: '',
  modele: '',
  annee: null,
  carburant: '',
  boite: '',
  kilometrage: null,
  codeObd: '',
  description: '',
  symptomesSelectionnes: []
})

onMounted(async () => {
  try {
    listeSymptomesDisponibles.value = await getSymptomes()
  } catch {
    listeSymptomesDisponibles.value = []
  }
})

const modelesDisponibles = computed(() => {
  if (!formulaire.marque) return []
  return catalogueVehicules[formulaire.marque] || []
})

function changerMarque() {
  formulaire.modele = ''
}

function basculerSymptome(idSymptome) {
  const index = formulaire.symptomesSelectionnes.indexOf(idSymptome)
  if (index > -1) {
    formulaire.symptomesSelectionnes.splice(index, 1)
  } else if (formulaire.symptomesSelectionnes.length < 20) {
    formulaire.symptomesSelectionnes.push(idSymptome)
  }
}

function soumettreSaisie() {
  const texteSansEspaces = formulaire.description.replace(/\s+/g, '')

  if (!formulaire.marque || !formulaire.modele || !formulaire.annee) {
    messageErreur.value = "Veuillez sélectionner une marque, un modèle et l'année du véhicule."
    return
  }

  if (texteSansEspaces.length < 3) {
    messageErreur.value = 'Veuillez décrire les symptômes (au moins 3 caractères hors espaces).'
    return
  }

  messageErreur.value = ''

  emit('lancer-diagnostic', {
    marque: formulaire.marque,
    modele: formulaire.modele,
    annee: formulaire.annee,
    carburant: formulaire.carburant || null,
    boite: formulaire.boite || null,
    kilometrage: formulaire.kilometrage,
    codeObd: formulaire.codeObd.trim(),
    description: formulaire.description.trim(),
    symptomes: [...formulaire.symptomesSelectionnes]
  })
}

function reinitialiserFormulaire() {
  formulaire.marque = ''
  formulaire.modele = ''
  formulaire.annee = null
  formulaire.carburant = ''
  formulaire.boite = ''
  formulaire.kilometrage = null
  formulaire.codeObd = ''
  formulaire.description = ''
  formulaire.symptomesSelectionnes = []
  messageErreur.value = ''
}
</script>

<template>
  <section class="card-atelier">
    <div class="card-header">
      <div>
        <span class="step-badge">ÉTAPE 01 — COLLECTE D'ATELIER</span>
        <h1 class="page-title">
          Fiche de saisie du véhicule et des symptômes
        </h1>
        <p class="page-subtitle">
          Renseignez les caractéristiques du véhicule et décrivez la panne observée pour interroger nos deux moteurs de diagnostic.
        </p>
      </div>
    </div>

    <form
      class="form-atelier"
      @submit.prevent="soumettreSaisie"
    >
      <div class="form-section">
        <h2 class="section-title">
          1. Identification du véhicule
        </h2>

        <div class="form-grid-3">
          <div class="form-group">
            <label
              class="form-label"
              for="marque"
            >Marque *</label>
            <select
              id="marque"
              v-model="formulaire.marque"
              class="form-select"
              @change="changerMarque"
            >
              <option value="">
                Sélectionner une marque...
              </option>
              <option
                v-for="marque in listeMarques"
                :key="marque"
                :value="marque"
              >
                {{ marque }}
              </option>
            </select>
          </div>

          <div class="form-group">
            <label
              class="form-label"
              for="modele"
            >Modèle *</label>
            <select
              id="modele"
              v-model="formulaire.modele"
              class="form-select"
              :disabled="!formulaire.marque"
            >
              <option value="">
                {{ formulaire.marque ? 'Sélectionner un modèle...' : "Choisissez d'abord une marque" }}
              </option>
              <option
                v-for="modele in modelesDisponibles"
                :key="modele"
                :value="modele"
              >
                {{ modele }}
              </option>
            </select>
          </div>

          <div class="form-group">
            <label
              class="form-label"
              for="annee"
            >Année de mise en circulation *</label>
            <input
              id="annee"
              v-model.number="formulaire.annee"
              type="number"
              min="1980"
              max="2026"
              class="form-input font-mono"
              placeholder="Ex : 2019"
            >
          </div>
        </div>

        <div class="form-grid-3">
          <div class="form-group">
            <label
              class="form-label"
              for="carburant"
            >Motorisation / Carburant</label>
            <select
              id="carburant"
              v-model="formulaire.carburant"
              class="form-select"
            >
              <option value="">
                Non renseigné
              </option>
              <option value="diesel">
                Diesel
              </option>
              <option value="essence">
                Essence
              </option>
              <option value="hybride">
                Hybride
              </option>
              <option value="electrique">
                Électrique
              </option>
            </select>
          </div>

          <div class="form-group">
            <label
              class="form-label"
              for="boite"
            >Transmission</label>
            <select
              id="boite"
              v-model="formulaire.boite"
              class="form-select"
            >
              <option value="">
                Non renseignée
              </option>
              <option value="manuelle">
                Manuelle
              </option>
              <option value="automatique">
                Automatique
              </option>
            </select>
          </div>

          <div class="form-group">
            <label
              class="form-label"
              for="kilometrage"
            >Kilométrage (km)</label>
            <input
              id="kilometrage"
              v-model.number="formulaire.kilometrage"
              type="number"
              min="0"
              step="1000"
              class="form-input font-mono"
              placeholder="Ex : 118000"
            >
          </div>
        </div>
      </div>

      <div class="form-section">
        <h2 class="section-title">
          2. Relevé OBD-II & Symptômes constatés
        </h2>

        <div class="form-group">
          <label class="form-label">
            Symptômes observés <span class="badge-obd">OPTIONNEL</span>
          </label>
          <div class="tags-container">
            <button
              v-for="item in listeSymptomesDisponibles"
              :key="item.id_symptome"
              type="button"
              class="tag-badge"
              :class="{ active: formulaire.symptomesSelectionnes.includes(item.id_symptome) }"
              @click="basculerSymptome(item.id_symptome)"
            >
              {{ item.libelle }}
            </button>
          </div>
        </div>

        <div class="form-group">
          <label
            class="form-label"
            for="codeObd"
          >
            Code défaut OBD-II <span class="badge-obd">OPTIONNEL</span>
          </label>
          <input
            id="codeObd"
            v-model="formulaire.codeObd"
            type="text"
            class="form-input input-obd font-mono"
            placeholder="Ex : P0300, P0420, U0100..."
          >
        </div>

        <div class="form-group">
          <label
            class="form-label"
            for="description"
          >Description détaillée des symptômes *</label>
          <textarea
            id="description"
            v-model="formulaire.description"
            rows="4"
            maxlength="2000"
            class="form-textarea"
            placeholder="Décrivez le comportement du véhicule (bruits, pertes de puissance, voyants allumés, conditions d'apparition à froid ou à chaud...)"
          />
          <span class="char-counter font-mono">
            {{ formulaire.description.length }} / 2000
          </span>
        </div>
      </div>

      <p
        v-if="messageErreur"
        class="alert-error"
      >
        {{ messageErreur }}
      </p>

      <div class="form-actions">
        <button
          type="button"
          class="btn-secondary"
          @click="reinitialiserFormulaire"
        >
          Réinitialiser
        </button>
        <button
          type="submit"
          class="btn-primary"
        >
          Lancer le double diagnostic →
        </button>
      </div>
    </form>
  </section>
</template>