<script setup>
import { computed, ref } from 'vue'
import iconeVehicule from '../assets/icone-vehicule.svg'
import iconeOutil from '../assets/icone-outil.svg'
import iconeRappel from '../assets/icone-rappel.svg'
import iconeGravite from '../assets/icone-gravite.svg'
import { traduireListeComposants, formaterGravite } from '../outils/traductions'

const props = defineProps({
  diagnostic: {
    type: Object,
    required: true
  },
  saisieInitiale: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['nouveau-diagnostic', 'aller-performances'])

const afficherExplications = ref(true)

const donneesVehiculeIncompletes = computed(() => {
  const v = props.diagnostic?.vehicule
  return !v || v.annee === null || v.annee === undefined || v.carburant === null || v.carburant === undefined
})

const listeHeuristique = computed(() => {
  return props.diagnostic?.heuristique?.resultats || []
})

const listeEmbeddings = computed(() => {
  return props.diagnostic?.embeddings?.resultats || []
})

const tempsHeuristique = computed(() => props.diagnostic?.heuristique?.temps_calcul_ms ?? null)
const tempsEmbeddings = computed(() => props.diagnostic?.embeddings?.temps_calcul_ms ?? null)

const pisteHeuristique = computed(() => listeHeuristique.value[0] || null)
const pisteEmbeddings = computed(() => listeEmbeddings.value[0] || null)

function scoreEnPourcent(score) {
  if (score === null || score === undefined) return 'N/A'
  return `${Math.round(Number(score) * 100)}%`
}

function formaterCapitalize(texte, defaut = 'Non renseigné') {
  if (!texte) return defaut
  const str = String(texte)
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase()
}

</script>

<template>
  <div class="diag-page-wrapper">
    <div class="diag-top-heading">
      <h1 class="diag-main-title">
        Résultats du diagnostic – {{ formaterCapitalize(diagnostic.vehicule?.marque) }} {{ diagnostic.vehicule?.modele }} ({{ diagnostic.vehicule?.annee || 'Année N/A' }})
      </h1>
      <p class="diag-main-subtitle">
        <p class="diag-main-subtitle">
        Comparaison des causes, solutions recommandées et niveaux de gravité. Les pourcentages représentent un indice de correspondance indépendant pour chaque piste.
      </p>
      </p>
    </div>

    <div class="diag-vehicle-bar">
      <div class="diag-vehicle-info">
        <img
          :src="iconeVehicule"
          alt=""
          class="diag-icon-svg"
        >
        <span>
          <strong>{{ formaterCapitalize(diagnostic.vehicule?.marque) }} {{ diagnostic.vehicule?.modele }} ({{ diagnostic.vehicule?.annee || 'Non renseigné' }})</strong>
          · {{ formaterCapitalize(diagnostic.vehicule?.carburant, 'Motorisation non renseignée') }}
          <template v-if="diagnostic.vehicule?.boite">
            · Boîte {{ diagnostic.vehicule.boite }}
          </template>
          <template v-if="saisieInitiale?.codeObd">
            · Code OBD-II : <span class="font-mono">{{ saisieInitiale.codeObd }}</span>
          </template>
        </span>
      </div>

      <button
        type="button"
        class="diag-modify-link"
        @click="emit('nouveau-diagnostic')"
      >
        Modifier la saisie ↗
      </button>
    </div>
    <div
      v-if="donneesVehiculeIncompletes"
      class="diag-alert-box diag-alert-box--danger"
      style="margin-bottom: 1rem;"
      role="alert"
    >
      <img
        :src="iconeGravite"
        alt=""
        class="diag-icon-svg"
      >
      <span>Données incomplètes pour ce véhicule (année ou motorisation absente en base). Les résultats affichés sont indicatifs.</span>
    </div>

    <div class="diag-cards-grid">
      <article class="diag-card diag-card--heuristique">
        <div class="diag-method-banner diag-method-banner--heuristique font-mono">
          <span>[Approche A - Heuristique]</span>
          <span v-if="tempsHeuristique !== null">{{ tempsHeuristique }} ms</span>
        </div>

        <template v-if="pisteHeuristique">
          <span class="diag-cause-kicker font-mono">
            CAUSE #{{ pisteHeuristique.rang || 1 }} · PISTE PRIORITAIRE
            <template v-if="pisteHeuristique.explication?.composants_correspondants?.length">
              ({{ traduireListeComposants(pisteHeuristique.explication.composants_correspondants) }})
            </template>
          </span>

          <div class="diag-title-score-row">
            <h2 class="diag-cause-title">
              {{ pisteHeuristique.titre }}
            </h2>
            <span class="diag-big-score diag-big-score--heuristique font-mono">
              {{ scoreEnPourcent(pisteHeuristique.score) }}
            </span>
          </div>

          <p class="diag-score-caption">
            Score calculé sur les règles actives
            <template v-if="pisteHeuristique.explication?.nb_signalements">
              ({{ pisteHeuristique.explication.nb_signalements }} signalements correspondants)
            </template>
          </p>

          <hr class="diag-divider">

          <div
            v-if="pisteHeuristique.solutions?.length"
            class="diag-control-block"
          >
            <span class="diag-control-kicker">PREMIER CONTRÔLE RECOMMANDÉ</span>
            <p class="diag-control-action">
              <img
                :src="iconeOutil"
                alt=""
                class="diag-icon-svg"
              >
              <span>{{ pisteHeuristique.solutions[0].libelle }}</span>
            </p>
            <span class="diag-control-level">
              {{ pisteHeuristique.solutions[0].description }}
            </span>
          </div>

          <div
            v-if="pisteHeuristique.type_probleme === 'rappel'"
            class="diag-alert-box diag-alert-box--danger"
          >
            <img
              :src="iconeRappel"
              alt=""
              class="diag-icon-svg"
            >
            <span>RAPPEL CONSTRUCTEUR OFFICIEL (Gravité : {{ formaterGravite(pisteHeuristique.gravite) }})</span>
          </div>

          <div
            v-else-if="pisteHeuristique.gravite"
            class="diag-alert-box"
          >
            <img
              :src="iconeGravite"
              alt=""
              class="diag-icon-svg"
            >
            <span>Gravité : {{ formaterGravite(pisteHeuristique.gravite) }} (Type : {{ pisteHeuristique.type_probleme }})</span>
          </div>

          <div
            v-if="listeHeuristique.length > 1"
            class="diag-secondary-list"
          >
            <span class="diag-control-kicker">AUTRES PISTES HEURISTIQUES ({{ listeHeuristique.length - 1 }})</span>
            <div
              v-for="item in listeHeuristique.slice(1)"
              :key="item.id_probleme"
              class="diag-secondary-item"
            >
              <span>
                #{{ item.rang }} · {{ item.titre }}
                <strong
                  v-if="item.type_probleme === 'rappel'"
                  class="badge-rappel-inline font-mono"
                >[RAPPEL]</strong>
              </span>
              <strong class="font-mono">{{ scoreEnPourcent(item.score) }}</strong>
            </div>
          </div>
        </template>

        <div
          v-else
          class="diag-empty-card"
        >
          Aucune piste retournée par le moteur heuristique.
        </div>
      </article>

      <article class="diag-card diag-card--embeddings">
        <div class="diag-method-banner diag-method-banner--embeddings font-mono">
          <span>[Approche B - Embeddings]</span>
          <span v-if="tempsEmbeddings !== null">{{ tempsEmbeddings }} ms</span>
        </div>

        <template v-if="pisteEmbeddings">
          <span class="diag-cause-kicker font-mono">
            CAUSE #{{ pisteEmbeddings.rang || 1 }} · PISTE PRIORITAIRE
          </span>

          <div class="diag-title-score-row">
            <h2 class="diag-cause-title">
              {{ pisteEmbeddings.titre }}
            </h2>
            <span class="diag-big-score diag-big-score--embeddings font-mono">
              {{ scoreEnPourcent(pisteEmbeddings.score) }}
            </span>
          </div>

          <p class="diag-score-caption">
            Correspondance avec les pannes similaires signalées ({{ scoreEnPourcent(pisteEmbeddings.explication?.similarite ?? pisteEmbeddings.score) }})
          </p>

          <hr class="diag-divider">

          <div
            v-if="pisteEmbeddings.solutions?.length"
            class="diag-control-block"
          >
            <span class="diag-control-kicker">PREMIER CONTRÔLE RECOMMANDÉ</span>
            <p class="diag-control-action">
              <img
                :src="iconeOutil"
                alt=""
                class="diag-icon-svg"
              >
              <span>{{ pisteEmbeddings.solutions[0].libelle }}</span>
            </p>
            <span class="diag-control-level">
              {{ pisteEmbeddings.solutions[0].description }}
            </span>
          </div>

          <div
            v-if="pisteEmbeddings.type_probleme === 'rappel'"
            class="diag-alert-box diag-alert-box--danger"
          >
            <img
              :src="iconeRappel"
              alt=""
              class="diag-icon-svg"
            >
            <span>RAPPEL CONSTRUCTEUR OFFICIEL EXISTANT (Gravité : {{ formaterGravite(pisteEmbeddings.gravite) }})</span>
          </div>

          <div
            v-else-if="pisteEmbeddings.gravite"
            class="diag-alert-box"
          >
            <img
              :src="iconeGravite"
              alt=""
              class="diag-icon-svg"
            >
            <span>Gravité : {{ formaterGravite(pisteEmbeddings.gravite) }} (Type : {{ pisteEmbeddings.type_probleme }})</span>
          </div>

          <div
            v-if="listeEmbeddings.length > 1"
            class="diag-secondary-list"
          >
            <span class="diag-control-kicker">AUTRES PISTES EMBEDDINGS ({{ listeEmbeddings.length - 1 }})</span>
            <div
              v-for="item in listeEmbeddings.slice(1)"
              :key="item.id_probleme"
              class="diag-secondary-item"
            >
              <span>
                #{{ item.rang }} · {{ item.titre }}
                <strong
                  v-if="item.type_probleme === 'rappel'"
                  class="badge-rappel-inline font-mono"
                >[RAPPEL]</strong>
              </span>
              <strong class="font-mono">{{ scoreEnPourcent(item.score) }}</strong>
            </div>
          </div>
        </template>

        <div
          v-else
          class="diag-empty-card"
        >
          Aucune piste retournée par le moteur embeddings.
        </div>
      </article>
    </div>

    <div
      v-if="pisteHeuristique || pisteEmbeddings"
      class="diag-why-panel"
    >
      <button
        type="button"
        class="diag-why-toggle"
        @click="afficherExplications = !afficherExplications"
      >
        <span>{{ afficherExplications ? '▾' : '▸' }} Pourquoi ce diagnostic ?</span>
      </button>

      <div
        v-if="afficherExplications"
        class="diag-why-grid"
      >
        <div class="diag-why-col">
          <span class="diag-why-header diag-why-header--heuristique font-mono">
            A / EXPLICATION HEURISTIQUE (VOTRE DIAGNOSTIC)
          </span>
          <ul
            v-if="pisteHeuristique?.explication"
            class="diag-why-list font-mono"
          >
            <li v-if="pisteHeuristique.explication.composants_correspondants?.length">
              Composants : {{ traduireListeComposants(pisteHeuristique.explication.composants_correspondants) }}
            </li>
            <li v-if="pisteHeuristique.explication.nb_signalements !== undefined">
              Signalements NHTSA recensés : {{ pisteHeuristique.explication.nb_signalements }} cas
            </li>
            <li v-if="pisteHeuristique.explication.extrait">
              Extrait : "{{ pisteHeuristique.explication.extrait }}"
            </li>
          </ul>
          <p
            v-if="pisteHeuristique"
            class="diag-why-total font-mono"
          >
            Score retenu : {{ scoreEnPourcent(pisteHeuristique.score) }}
          </p>
        </div>

        <div class="diag-why-col">
          <span class="diag-why-header diag-why-header--embeddings font-mono">
            B / SIGNALEMENTS PROCHES DE VOTRE DESCRIPTION
          </span>
          <div
            v-for="(item, index) in listeEmbeddings.slice(0, 2)"
            :key="item.id_probleme"
            class="diag-neighbor-item font-mono"
          >
            <strong>
              Cause possible n°{{ item.rang || index + 1 }} ({{ item.titre }}) · Similarité {{ scoreEnPourcent(item.explication?.similarite ?? item.score) }}
            </strong>
            <p v-if="item.explication?.extrait">
              "{{ item.explication.extrait }}"
            </p>
          </div>
          <span class="diag-why-footnote">
            Données sources NHTSA vectorisées par sentence-transformers.
          </span>
        </div>
      </div>
    </div>

    <div
      v-if="pisteHeuristique && pisteEmbeddings"
      class="diag-conclusion-box"
    >
      <strong>Conclusion commune</strong>
      <p v-if="pisteHeuristique.id_probleme === pisteEmbeddings.id_probleme">
        Convergence : Les deux approches identifient la même cause prioritaire (<strong>{{ pisteHeuristique.titre }}</strong> — {{ pisteHeuristique.solutions?.[0]?.libelle }}).
      </p>
      <p v-else>
        Pistes complémentaires : L'approche heuristique priorise <strong>{{ pisteHeuristique.titre }}</strong> ({{ scoreEnPourcent(pisteHeuristique.score) }}) tandis que l'approche vectorielle met en avant <strong>{{ pisteEmbeddings.titre }}</strong> ({{ scoreEnPourcent(pisteEmbeddings.score) }}).
      </p>
    </div>

    <div class="diag-bottom-bar">
      <span class="diag-disclaimer">
        Résultats indicatifs · Faites confirmer la panne par un professionnel.
      </span>

      <button
        type="button"
        class="btn-primary"
        @click="emit('aller-performances')"
      >
        Voir le benchmark complet →
      </button>
    </div>
  </div>
</template>