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
  return !v || v.annee == null || v.carburant == null
})

const listeHeuristique = computed(() => props.diagnostic?.heuristique?.resultats || [])
const listeEmbeddings = computed(() => props.diagnostic?.embeddings?.resultats || [])

const pisteHeuristique = computed(() => listeHeuristique.value[0] || null)
const pisteEmbeddings = computed(() => listeEmbeddings.value[0] || null)

function scoreEnPourcent(score) {
  if (score == null) return 'N/A'
  return `${Math.round(Number(score) * 100)}%`
}

function formaterCapitalize(texte, defaut = 'Non renseigné') {
  if (!texte) return defaut
  const str = String(texte)
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase()
}

// les plaintes NHTSA n'ont pas de titre (l'api renvoie le début du texte en anglais)
// donc on affiche le nom de la cause en français comme sur la maquette
function titrePiste(piste) {
  return piste?.explication?.libelle_cause || piste?.titre || ''
}

function determinerMessageVide(blocMoteur, nomMoteur) {
  if (!blocMoteur || blocMoteur.temps_calcul_ms === null) {
    return `Le moteur ${nomMoteur} est temporairement indisponible.`
  }
  return `Aucune piste retournée par le moteur ${nomMoteur}.`
}

const cartesMoteurs = computed(() => [
  {
    cle: 'heuristique',
    banniere: '[Approche A - Heuristique]',
    temps: props.diagnostic?.heuristique?.temps_calcul_ms ?? null,
    estIndisponible: props.diagnostic?.heuristique?.temps_calcul_ms === null,
    piste: pisteHeuristique.value,
    autresPistes: listeHeuristique.value.slice(1),
    titreAutres: 'AUTRES PISTES HEURISTIQUES',
    composants: pisteHeuristique.value?.explication?.composants_correspondants?.length
      ? traduireListeComposants(pisteHeuristique.value.explication.composants_correspondants)
      : '',
    legendeScore: pisteHeuristique.value?.explication?.nb_signalements
      ? `Score calculé sur les règles actives (${pisteHeuristique.value.explication.nb_signalements} signalements correspondants)`
      : 'Score calculé sur les règles actives',
    // on garde quand même l'extrait de la plainte sous le score
    signalement: pisteHeuristique.value?.explication?.libelle_cause ? pisteHeuristique.value.titre : '',
    libelleRappel: 'RAPPEL CONSTRUCTEUR OFFICIEL',
    messageVide: determinerMessageVide(props.diagnostic?.heuristique, 'heuristique')
  },
  {
    cle: 'embeddings',
    banniere: '[Approche B - Embeddings]',
    temps: props.diagnostic?.embeddings?.temps_calcul_ms ?? null,
    estIndisponible: props.diagnostic?.embeddings?.temps_calcul_ms === null,
    piste: pisteEmbeddings.value,
    autresPistes: listeEmbeddings.value.slice(1),
    titreAutres: 'AUTRES PISTES EMBEDDINGS',
    composants: '',
    legendeScore: pisteEmbeddings.value
      ? `Correspondance avec les pannes similaires signalées (${scoreEnPourcent(pisteEmbeddings.value.explication?.similarite ?? pisteEmbeddings.value.score)})`
      : '',
    signalement: '',
    libelleRappel: 'RAPPEL CONSTRUCTEUR OFFICIEL EXISTANT',
    messageVide: determinerMessageVide(props.diagnostic?.embeddings, 'embeddings')
  }
])
</script>

<template>
  <div class="diag-page-wrapper">
    <div class="diag-top-heading">
      <h1 class="diag-main-title">
        Résultats du diagnostic – {{ formaterCapitalize(diagnostic.vehicule?.marque) }} {{ diagnostic.vehicule?.modele }} ({{ diagnostic.vehicule?.annee || 'Année N/A' }})
      </h1>
      <p class="diag-main-subtitle">
        Comparaison des causes, solutions recommandées et niveaux de gravité. Les pourcentages représentent un indice de correspondance indépendant pour chaque piste.
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
      <article
        v-for="moteur in cartesMoteurs"
        :key="moteur.cle"
        class="diag-card"
        :class="`diag-card--${moteur.cle}`"
      >
        <div
          class="diag-method-banner font-mono"
          :class="`diag-method-banner--${moteur.cle}`"
        >
          <span>{{ moteur.banniere }}</span>
          <span v-if="moteur.temps !== null">{{ moteur.temps }} ms</span>
        </div>

        <template v-if="moteur.piste">
          <span class="diag-cause-kicker font-mono">
            CAUSE #{{ moteur.piste.rang || 1 }} · PISTE PRIORITAIRE
            <template v-if="moteur.composants">
              ({{ moteur.composants }})
            </template>
          </span>

          <div class="diag-title-score-row">
            <h2 class="diag-cause-title">
              {{ titrePiste(moteur.piste) }}
            </h2>
            <span
              class="diag-big-score font-mono"
              :class="`diag-big-score--${moteur.cle}`"
            >
              {{ scoreEnPourcent(moteur.piste.score) }}
            </span>
          </div>

          <p class="diag-score-caption">
            {{ moteur.legendeScore }}
          </p>

          <p
            v-if="moteur.signalement"
            class="diag-score-caption"
          >
            Plainte NHTSA : « {{ moteur.signalement }} »
          </p>

          <hr class="diag-divider">

          <div
            v-if="moteur.piste.solutions?.length"
            class="diag-control-block"
          >
            <span class="diag-control-kicker">PREMIER CONTRÔLE RECOMMANDÉ</span>
            <p class="diag-control-action">
              <img
                :src="iconeOutil"
                alt=""
                class="diag-icon-svg"
              >
              <span>{{ moteur.piste.solutions[0].libelle }}</span>
            </p>
            <span class="diag-control-level">
              {{ moteur.piste.solutions[0].description }}
            </span>
          </div>

          <div
            v-if="moteur.piste.type_probleme === 'rappel'"
            class="diag-alert-box diag-alert-box--danger"
          >
            <img
              :src="iconeRappel"
              alt=""
              class="diag-icon-svg"
            >
            <span>{{ moteur.libelleRappel }} (Gravité : {{ formaterGravite(moteur.piste.gravite) }})</span>
          </div>

          <div
            v-else-if="moteur.piste.gravite"
            class="diag-alert-box"
          >
            <img
              :src="iconeGravite"
              alt=""
              class="diag-icon-svg"
            >
            <span>Gravité : {{ formaterGravite(moteur.piste.gravite) }} (Type : {{ moteur.piste.type_probleme }})</span>
          </div>

          <div
            v-if="moteur.autresPistes.length"
            class="diag-secondary-list"
          >
            <span class="diag-control-kicker">{{ moteur.titreAutres }} ({{ moteur.autresPistes.length }})</span>
            <div
              v-for="item in moteur.autresPistes"
              :key="item.id_probleme"
              class="diag-secondary-item"
            >
              <span>
                #{{ item.rang }} · {{ titrePiste(item) }}
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
          :class="{ 'diag-alert-box--danger': moteur.estIndisponible }"
        >
          {{ moteur.messageVide }}
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
              Cause possible n°{{ item.rang || index + 1 }} ({{ titrePiste(item) }}) · Similarité {{ scoreEnPourcent(item.explication?.similarite ?? item.score) }}
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
        Convergence : Les deux approches identifient la même cause prioritaire (<strong>{{ titrePiste(pisteHeuristique) }}</strong> — {{ pisteHeuristique.solutions?.[0]?.libelle }}).
      </p>
      <p v-else>
        Pistes complémentaires : L'approche heuristique priorise <strong>{{ titrePiste(pisteHeuristique) }}</strong> ({{ scoreEnPourcent(pisteHeuristique.score) }}) tandis que l'approche vectorielle met en avant <strong>{{ titrePiste(pisteEmbeddings) }}</strong> ({{ scoreEnPourcent(pisteEmbeddings.score) }}).
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