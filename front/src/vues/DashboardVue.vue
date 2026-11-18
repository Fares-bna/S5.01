<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import Chart from 'chart.js/auto'
import '../styles/dashboard.css'
import { getMetriques, messagePourUtilisateur, UTILISER_MOCK } from '../services/api'

import iconeCible from '../assets/icone-cible.svg'
import iconeHorloge from '../assets/icone-horloge.svg'
import iconeFeuille from '../assets/icone-feuille.svg'
import iconeEclair from '../assets/icone-eclair.svg'

// résultat du dernier diagnostic envoyé par App.vue (null si aucun diagnostic lancé)
const props = defineProps({
  dernierDiagnostic: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['retour-diagnostic'])

const donneesMetriques = ref(null)
const chargementMetriques = ref(true)
const erreurMetriques = ref('')

const listeApproches = computed(() => donneesMetriques.value?.approches ?? [])

const approcheA = computed(() =>
  listeApproches.value.find((item) => item.approche === 'heuristique') ?? null
)

const approcheB = computed(() =>
  listeApproches.value.find((item) => item.approche === 'embeddings') ?? null
)

const casEvalues = computed(() => donneesMetriques.value?.cas_evalues ?? null)

const donneesScalabiliteDisponibles = computed(() =>
  Array.isArray(approcheA.value?.scalabilite_ms) &&
  Array.isArray(approcheB.value?.scalabilite_ms)
)

// le graphique s'affiche dès qu'une des deux approches a des temps
const latenceDisponible = computed(() =>
  approcheA.value?.moyen_ms != null || approcheB.value?.moyen_ms != null
)

function formaterMesure(valeur, unite = '') {
  return valeur != null ? `${valeur}${unite}` : null
}

const cartesComparatives = computed(() => [
  {
    titre: 'Précision Top-3',
    icone: iconeCible,
    valeurA: formaterMesure(approcheA.value?.precision_top3, '%'),
    valeurB: formaterMesure(approcheB.value?.precision_top3, '%'),
    note: 'Présence de la cause dans le Top-3'
  },
  {
    titre: 'Temps moyen',
    icone: iconeHorloge,
    valeurA: formaterMesure(approcheA.value?.moyen_ms, ' ms'),
    valeurB: formaterMesure(approcheB.value?.moyen_ms, ' ms'),
    note: 'Latence moyenne par requête'
  },
  {
    titre: 'Énergie / requête',
    icone: iconeFeuille,
    valeurA: formaterMesure(approcheA.value?.energie_kwh_moyen, ' kWh'),
    valeurB: formaterMesure(approcheB.value?.energie_kwh_moyen, ' kWh'),
    note: '(Mesuré via CodeCarbon)'
  }
])

const lignesTableau = computed(() => [
  {
    nom: 'Approche A (Heuristique)',
    classeTexte: 'texte-marine',
    cellules: [
      formaterMesure(approcheA.value?.precision_top3, '%'),
      formaterMesure(approcheA.value?.moyen_ms, ' ms'),
      formaterMesure(approcheA.value?.energie_kwh_moyen, ' kWh'),
      approcheA.value?.memoire_ram ?? null
    ]
  },
  {
    nom: 'Approche B (Embeddings)',
    classeTexte: 'texte-emeraude',
    cellules: [
      formaterMesure(approcheB.value?.precision_top3, '%'),
      formaterMesure(approcheB.value?.moyen_ms, ' ms'),
      formaterMesure(approcheB.value?.energie_kwh_moyen, ' kWh'),
      approcheB.value?.memoire_ram ?? null
    ]
  }
])

// phrase sous le graphique, calculée avec les vraies valeurs
const conclusionLatence = computed(() => {
  const tempsA = approcheA.value?.moyen_ms
  const tempsB = approcheB.value?.moyen_ms

  if (tempsA == null && tempsB == null) return null
  if (tempsB == null) return `Heuristique : ${tempsA} ms en moyenne, l'approche embeddings n'est pas encore mesurée.`
  if (tempsA == null) return `Embeddings : ${tempsB} ms en moyenne, l'approche heuristique n'est pas encore mesurée.`
  if (tempsA < tempsB) return `${tempsA} ms vs ${tempsB} ms : l'heuristique privilégie la rapidité.`
  return `${tempsA} ms vs ${tempsB} ms : les embeddings sont plus rapides.`
})

// infos d'une approche pour le panneau "Votre dernier diagnostic"
function resumerApproche(bloc) {
  const premierResultat = bloc?.resultats?.[0]
  return {
    temps: formaterMesure(bloc?.temps_calcul_ms, ' ms'),
    nbResultats: bloc?.nb_resultats ?? 0,
    // nom de la cause en français plutôt que l'extrait de plainte en anglais
    piste: premierResultat?.explication?.libelle_cause || premierResultat?.titre || null
  }
}

const resumeDernierDiagnostic = computed(() => {
  if (!props.dernierDiagnostic) return null

  return [
    { nom: 'A · Heuristique', classe: 'texte-marine', ...resumerApproche(props.dernierDiagnostic.heuristique) },
    { nom: 'B · Embeddings', classe: 'texte-emeraude', ...resumerApproche(props.dernierDiagnostic.embeddings) }
  ]
})

const vehiculeDernierDiagnostic = computed(() => {
  const v = props.dernierDiagnostic?.vehicule
  if (!v) return null
  return `${v.marque} ${v.modele} (${v.annee || 'année inconnue'})`
})

const canvasLatence = ref(null)
const canvasScalabilite = ref(null)

let instanceChartLatence = null
let instanceChartScalabilite = null

// chart.js a besoin des couleurs en js, on les récupère dans tokens.css
function couleurCss(nomVariable) {
  return getComputedStyle(document.documentElement).getPropertyValue(nomVariable).trim()
}

const pluginValeursDessusBarres = {
  id: 'valeursDessusBarres',
  afterDatasetsDraw(chart) {
    const { ctx } = chart
    ctx.save()
    ctx.font = "500 11px 'JetBrains Mono', monospace"
    ctx.textAlign = 'center'
    ctx.textBaseline = 'bottom'

    chart.data.datasets.forEach((dataset, indexDataset) => {
      const meta = chart.getDatasetMeta(indexDataset)
      ctx.fillStyle = dataset.backgroundColor

      meta.data.forEach((barre, index) => {
        const valeur = dataset.data[index]
        if (valeur != null) {
          ctx.fillText(`${valeur}ms`, barre.x, barre.y - 4)
        }
      })
    })
    ctx.restore()
  }
}

function creerOptionsGraphique(paddingTop = 0) {
  return {
    responsive: true,
    maintainAspectRatio: false,
    layout: { padding: { top: paddingTop } },
    plugins: {
      legend: { display: false },
      tooltip: {
        titleFont: { family: "'Inter', sans-serif", size: 12 },
        bodyFont: { family: "'JetBrains Mono', monospace", size: 12 },
        callbacks: {
          label: (contexte) => `${contexte.dataset.label} : ${contexte.parsed.y} ms`
        }
      }
    },
    scales: {
      x: {
        grid: { display: false },
        border: { color: couleurCss('--border-filet-calibre') },
        ticks: {
          color: couleurCss('--text-ardoise'),
          font: { family: "'Inter', sans-serif", size: 12 }
        }
      },
      y: {
        beginAtZero: true,
        border: { display: false },
        grid: { color: couleurCss('--border-filet-calibre') },
        ticks: {
          color: couleurCss('--text-gris-jauge'),
          font: { family: "'JetBrains Mono', monospace", size: 11 },
          callback: (valeur) => `${valeur}ms`
        }
      }
    }
  }
}

function initialiserGraphiques() {
  const couleurA = couleurCss('--color-marine-heuristique')
  const couleurB = couleurCss('--color-emeraude')

  if (canvasLatence.value && latenceDisponible.value) {
    instanceChartLatence = new Chart(canvasLatence.value, {
      type: 'bar',
      data: {
        labels: ['Min', 'Max', 'Moyenne'],
        datasets: [
          {
            label: 'A · Heuristique',
            data: [approcheA.value?.min_ms, approcheA.value?.max_ms, approcheA.value?.moyen_ms],
            backgroundColor: couleurA,
            borderRadius: 4,
            barPercentage: 0.65,
            categoryPercentage: 0.45
          },
          {
            label: 'B · Embeddings',
            data: [approcheB.value?.min_ms, approcheB.value?.max_ms, approcheB.value?.moyen_ms],
            backgroundColor: couleurB,
            borderRadius: 4,
            barPercentage: 0.65,
            categoryPercentage: 0.45
          }
        ]
      },
      options: creerOptionsGraphique(22),
      plugins: [pluginValeursDessusBarres]
    })
  }

  if (canvasScalabilite.value && donneesScalabiliteDisponibles.value) {
    instanceChartScalabilite = new Chart(canvasScalabilite.value, {
      type: 'line',
      data: {
        labels: donneesMetriques.value?.paliers_documents ?? [],
        datasets: [
          {
            label: 'A · Heuristique',
            data: approcheA.value.scalabilite_ms,
            borderColor: couleurA,
            backgroundColor: couleurA,
            borderWidth: 2,
            pointRadius: 3.5,
            tension: 0.1
          },
          {
            label: 'B · Embeddings',
            data: approcheB.value.scalabilite_ms,
            borderColor: couleurB,
            backgroundColor: couleurB,
            borderWidth: 2,
            pointRadius: 3.5,
            tension: 0.1
          }
        ]
      },
      options: creerOptionsGraphique(0)
    })
  }
}

function detruireGraphiques() {
  if (instanceChartLatence) instanceChartLatence.destroy()
  if (instanceChartScalabilite) instanceChartScalabilite.destroy()
  instanceChartLatence = null
  instanceChartScalabilite = null
}

// appelée au chargement de la page et quand on clique sur "Réessayer"
async function chargerMetriques() {
  chargementMetriques.value = true
  erreurMetriques.value = ''
  detruireGraphiques()

  try {
    donneesMetriques.value = await getMetriques()
  } catch (erreur) {
    donneesMetriques.value = null
    erreurMetriques.value = messagePourUtilisateur(erreur)
  } finally {
    chargementMetriques.value = false
  }

  // on attend que les canvas soient affichés avant de créer les graphiques
  await nextTick()
  initialiserGraphiques()
}

onMounted(chargerMetriques)

onBeforeUnmount(detruireGraphiques)
</script>

<template>
  <div class="conteneur-page-benchmark">
    <header class="en-tete-benchmark">
      <h1 class="titre-principal-benchmark">
        Benchmark comparatif des deux approches
      </h1>
      <p class="sous-titre-principal-benchmark">
        Mesure de la rapidité, de l'empreinte environnementale et des ressources matérielles.
      </p>
    </header>

    <div
      v-if="erreurMetriques"
      class="alert-error bandeau-erreur-metriques"
      role="alert"
    >
      <span>Métriques indisponibles : {{ erreurMetriques }}</span>
      <button
        type="button"
        class="btn-secondary"
        :disabled="chargementMetriques"
        @click="chargerMetriques"
      >
        Réessayer
      </button>
    </div>

    <p
      v-else-if="chargementMetriques"
      class="sous-titre-principal-benchmark font-mono"
    >
      Chargement des métriques...
    </p>

    <section class="panneau-dernier-diagnostic">
      <div class="en-tete-tableau-recap">
        <h2 class="titre-panneau">
          Votre dernier diagnostic
        </h2>
        <span
          v-if="vehiculeDernierDiagnostic"
          class="badge-meta-tableau"
        >{{ vehiculeDernierDiagnostic }}</span>
      </div>

      <div
        v-if="resumeDernierDiagnostic"
        class="grille-dernier-diagnostic"
      >
        <div
          v-for="ligne in resumeDernierDiagnostic"
          :key="ligne.nom"
          class="bloc-dernier-diagnostic"
        >
          <span
            class="sous-etiquette-approche"
            :class="ligne.classe"
          >{{ ligne.nom }}</span>
          <strong
            v-if="ligne.temps"
            class="valeur-approche"
            :class="ligne.classe"
          >{{ ligne.temps }}</strong>
          <span
            v-else
            class="badge-donnee-manquante"
          >Non disponible</span>
          <span class="note-bas-indicateur">
            {{ ligne.nbResultats }} piste(s)<template v-if="ligne.piste"> · n°1 : {{ ligne.piste }}</template>
          </span>
        </div>
        <button
          type="button"
          class="btn-secondary"
          @click="emit('retour-diagnostic')"
        >
          ← Revoir le diagnostic
        </button>
      </div>

      <p
        v-else
        class="sous-titre-panneau"
      >
        Lancez un diagnostic à l'étape 01 pour comparer ici les temps de réponse de votre requête.
      </p>
    </section>

    <section class="grille-indicateurs">
      <article class="carte-indicateur">
        <div class="en-tete-carte-indicateur">
          <span class="titre-indicateur">Cas évalués</span>
        </div>
        <div
          v-if="casEvalues !== null"
          class="chiffre-cle-principal"
        >
          {{ casEvalues }}
        </div>
        <div
          v-else
          class="badge-donnee-manquante"
        >
          Donnée manquante
        </div>
        <span class="note-bas-indicateur">(Jeu de test NHTSA)</span>
      </article>

      <article
        v-for="carte in cartesComparatives"
        :key="carte.titre"
        class="carte-indicateur"
      >
        <div class="en-tete-carte-indicateur">
          <span class="titre-indicateur">{{ carte.titre }}</span>
          <img
            :src="carte.icone"
            :alt="carte.titre"
            class="icone-indicateur"
          >
        </div>
        <div
          v-if="carte.valeurA !== null || carte.valeurB !== null"
          class="duel-valeurs-indicateur"
        >
          <div class="bloc-valeur-approche">
            <strong
              v-if="carte.valeurA !== null"
              class="valeur-approche texte-marine"
            >{{ carte.valeurA }}</strong>
            <span
              v-else
              class="badge-donnee-manquante"
            >Non mesuré</span>
            <span class="sous-etiquette-approche texte-marine">Approche A</span>
          </div>
          <span class="separateur-vs">vs</span>
          <div class="bloc-valeur-approche">
            <strong
              v-if="carte.valeurB !== null"
              class="valeur-approche texte-emeraude"
            >{{ carte.valeurB }}</strong>
            <span
              v-else
              class="badge-donnee-manquante"
            >Non mesuré</span>
            <span class="sous-etiquette-approche">Approche B</span>
          </div>
        </div>
        <div
          v-else
          class="badge-donnee-manquante"
        >
          Donnée manquante
        </div>
        <span class="note-bas-indicateur">{{ carte.note }}</span>
      </article>
    </section>

    <section class="grille-graphiques">
      <article class="panneau-accent-vert">
        <h2 class="titre-panneau">
          Temps de réponse
        </h2>
        <p class="sous-titre-panneau">
          Distribution de la latence · millisecondes
        </p>

        <div class="legende-graphique">
          <div class="element-legende">
            <span class="pastille-legende fond-marine" />
            <span>A · Heuristique</span>
          </div>
          <div class="element-legende">
            <span class="pastille-legende fond-emeraude" />
            <span>B · Embeddings</span>
          </div>
        </div>

        <div
          v-if="latenceDisponible"
          class="conteneur-canvas-graphique"
        >
          <canvas ref="canvasLatence" />
        </div>
        <div
          v-else
          class="badge-donnee-manquante"
        >
          Donnée manquante
        </div>

        <div class="pied-note-latence">
          <img
            :src="iconeEclair"
            alt="Rapidité"
            class="icone-eclair-latence"
          >
          <span v-if="conclusionLatence">
            {{ conclusionLatence }}
          </span>
          <span
            v-else
            class="badge-donnee-manquante"
          >Donnée manquante</span>
        </div>
      </article>

      <article class="panneau-accent-vert">
        <h2 class="titre-panneau">
          Complexité algorithmique &amp; Empreinte mémoire
        </h2>

        <div class="bloc-formules-complexite">
          <div class="ligne-formule-complexite">
            <strong class="texte-marine">A</strong>
            <span v-if="approcheA?.complexite">{{ approcheA.complexite }}</span>
            <span
              v-else
              class="badge-donnee-manquante"
            >Donnée manquante</span>
          </div>
          <div class="ligne-formule-complexite">
            <strong class="texte-emeraude">B</strong>
            <span v-if="approcheB?.complexite">{{ approcheB.complexite }}</span>
            <span
              v-else
              class="badge-donnee-manquante"
            >Donnée manquante</span>
          </div>
        </div>

        <div class="legende-graphique">
          <div class="element-legende">
            <span class="pastille-legende fond-marine" />
            <span>A · Heuristique</span>
          </div>
          <div class="element-legende">
            <span class="pastille-legende fond-emeraude" />
            <span>B · Embeddings</span>
          </div>
        </div>

        <div
          v-if="donneesScalabiliteDisponibles"
          class="conteneur-canvas-scalabilite"
        >
          <canvas ref="canvasScalabilite" />
        </div>
        <div
          v-else
          class="badge-donnee-manquante"
        >
          Donnée manquante
        </div>

        <p class="note-scalabilite">
          Scalabilité indicative · Temps de traitement selon le nombre de documents
        </p>
      </article>
    </section>

    <section class="panneau-tableau-recap">
      <div class="en-tete-tableau-recap">
        <h2 class="titre-panneau">
          Les performances, en un regard
        </h2>
        <span
          v-if="casEvalues !== null"
          class="badge-meta-tableau"
        >
          {{ casEvalues }} CAS · DEUX MÉTHODES
        </span>
        <span
          v-else
          class="badge-donnee-manquante"
        >Donnée manquante</span>
      </div>

      <div class="conteneur-scroll-tableau">
        <table class="tableau-performances">
          <thead>
            <tr>
              <th>Méthode</th>
              <th>Précision Top-3</th>
              <th>Temps moyen</th>
              <th>Énergie (CodeCarbon)</th>
              <th>Mémoire RAM</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="ligne in lignesTableau"
              :key="ligne.nom"
            >
              <td
                class="nom-methode"
                :class="ligne.classeTexte"
              >
                {{ ligne.nom }}
              </td>
              <td
                v-for="(valeur, index) in ligne.cellules"
                :key="index"
              >
                <span
                  v-if="valeur !== null"
                  class="cellule-valeur"
                  :class="ligne.classeTexte"
                >
                  {{ valeur }}
                </span>
                <span
                  v-else
                  class="badge-donnee-manquante"
                >Donnée manquante</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <footer class="mentions-bas-benchmark">
      <span>NHTSA · Jeu de test commun aux deux approches</span>
      <span v-if="UTILISER_MOCK">Valeurs fictives (mode démo)</span>
      <span v-else>Temps mesurés par l'API à chaque diagnostic</span>
    </footer>
  </div>
</template>