
# Contrat API et fausses données

## Pourquoi un contrat

Le contrat définit comment le frontend et le backend communiquent : les routes, ce que le front envoie, ce que le back répond et les règles à respecter des deux côtés. Il permet à chacun d'avancer en parallèle. Pour les simulations, nous utilisons des fausses données créées par nous.

## Objectif

L'utilisateur fait sa requête, l'API l'envoie aux deux approches de recommandation (heuristique et embeddings), et il obtient deux résultats à comparer.

## Règles générales

- Les noms de champs reprennent ceux de la base : `id_vehicule`, `id_probleme`, `id_solution`, `id_symptome`.
- Une valeur `null` est normale : `annee`, `carburant`, `boite` et `cylindres` sont souvent inconnus dans les données NHTSA.
- `gravite` vaut `faible`, `moderee`, `elevee` ou `critique`.
- Les textes des plaintes (`description`, `extrait`) viennent de NHTSA : ils sont en anglais et parfois longs. Les titres, les libellés de solutions et de symptômes sont en français.
- Les scores sont propres à chaque approche : on ne les compare pas entre eux (0,85 de l'heuristique et 0,91 des embeddings ne veulent pas dire que les embeddings sont meilleurs).
- Une recherche sans résultat n'est pas une erreur : réponse `200` avec `"resultats": []`.

## Routes

- `POST /api/recommandations` : lance les deux approches
- `GET /api/vehicules` : liste filtrée de véhicules
- `GET /api/symptomes` : symptômes à cocher dans le formulaire
- `GET /api/problemes/{id_probleme}` : consulter un problème
- `GET /api/metriques` : temps min, max, moyen par approche (dashboard)

## POST /api/recommandations

Requête :

```json
{
  "id_vehicule": 1,
  "description": "Ma voiture fait un bruit lorsque je freine",
  "carburant": "diesel",
  "boite": "manuelle",
  "symptomes": [4]
}
```

**Explications :**

- `id_vehicule` : entier, renvoyé par `GET /vehicules`, obligatoire
- `description` : texte libre de 3 à 2000 caractères (espaces retirés), obligatoire
- `carburant` : `essence`, `diesel`, `hybride` ou `electrique`
- `boite` : `manuelle` ou `automatique`
- `symptomes` : liste de `id_symptome` (20 maximum), renvoyés par `GET /symptomes`

Réponse (un seul résultat par approche pour la lisibilité) :

```json
{
  "id_requete": 42,
  "heuristique": {
    "temps_calcul_ms": 12.4,
    "nb_resultats": 1,
    "resultats": [
      {
        "rang": 1,
        "score": 0.85,
        "id_probleme": 12,
        "titre": "Usure des plaquettes de frein",
        "gravite": "elevee",
        "type_probleme": "signalement",
        "solutions": [
          {
            "id_solution": 3,
            "libelle": "Remplacer les plaquettes de frein",
            "description": "Faire contrôler et remplacer les plaquettes de frein usées."
          }
        ],
        "explication": {
          "composants_correspondants": ["SERVICE BRAKES"],
          "nb_signalements": 34,
          "extrait": "Loud grinding noise when braking..."
        }
      }
    ]
  },
  "embeddings": {
    "temps_calcul_ms": 48.7,
    "nb_resultats": 1,
    "resultats": [
      {
        "rang": 1,
        "score": 0.91,
        "id_probleme": 12,
        "titre": "Usure des plaquettes de frein",
        "gravite": "elevee",
        "type_probleme": "signalement",
        "solutions": [
          {
            "id_solution": 3,
            "libelle": "Remplacer les plaquettes de frein",
            "description": "Faire contrôler et remplacer les plaquettes de frein usées."
          }
        ],
        "explication": {
          "similarite": 0.91,
          "extrait": "Loud grinding noise when braking..."
        }
      }
    ]
  }
}
```

**Explications :**

- `id_requete` permet de retrouver la requête dans la base (`requete_utilisateur`).
- `explication` répond à « Pourquoi cette recommandation ? » : l'heuristique donne les composants correspondants et le nombre de signalements, les embeddings donnent la similarité. Les deux donnent un `extrait`.
- Pour notre première version : seule l'heuristique existe. L'approche `embeddings` garde la même forme, avec `"temps_calcul_ms": null`, `"nb_resultats": 0` et `"resultats": []`. Le front garde ainsi ses deux colonnes dès la première version.
- L'API renvoie au maximum 5 résultats par approche (valeur fixe, non modifiable par le front).

## GET /api/vehicules

Paramètres, tous facultatifs sauf : `marque`, `modele`, `annee`.

```json
[
  {
    "id_vehicule": 1,
    "marque": "VOLKSWAGEN",
    "modele": "TAOS",
    "annee": 2023,
    "carburant": null,
    "boite": null,
    "cylindres": null
  }
]
```

**Explications :**

- `annee`, `carburant`, `boite` et `cylindres` peuvent être `null` : le front doit l'afficher sans planter.

## GET /api/symptomes

```json
[
  { "id_symptome": 4, "libelle": "Bruit au freinage" }
]
```

## GET /api/problemes/{id_probleme}

```json
{
  "id_probleme": 12,
  "titre": "Usure des plaquettes de frein",
  "description": "Loud grinding noise when braking. The dealer found the brake pads worn.",
  "gravite": "elevee",
  "type_probleme": "signalement",
  "source": "NHTSA complaints",
  "solutions": [
    {
      "id_solution": 3,
      "libelle": "Remplacer les plaquettes de frein",
      "description": "Faire contrôler et remplacer les plaquettes de frein usées."
    }
  ]
}
```

## GET /api/metriques

```json
{
  "approches": [
    {
      "approche": "heuristique",
      "min_ms": 4.1,
      "max_ms": 38.2,
      "moyen_ms": 12.6,
      "energie_kwh_moyen": null,
      "complexite": null
    },
    {
      "approche": "embeddings",
      "min_ms": 61.0,
      "max_ms": 310.5,
      "moyen_ms": 88.7,
      "energie_kwh_moyen": null,
      "complexite": null
    }
  ]
}
```

**Explications :**

- `energie_kwh_moyen` et `complexite` restent `null` tant que les benchmarks ne sont pas faits.

## Erreurs

- `404` `VEHICULE_INCONNU` : `id_vehicule` absent de la base
- `404` `PROBLEME_INCONNU` : `id_probleme` absent de la base
- `422` `REQUETE_INVALIDE` : données incorrectes (champ manquant, valeur hors limites)

Toutes les erreurs ont le même format. Le front se base sur `code`, jamais sur `message` :

```json
{
  "erreur": {
    "code": "VEHICULE_INCONNU",
    "message": "Aucun véhicule avec l'id 999.",
    "details": null
  }
}
```

Pour `REQUETE_INVALIDE`, `details` liste les champs en erreur : `[{ "champ": "description", "message": "..." }]`.