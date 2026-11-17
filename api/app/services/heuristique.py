"""Approche A : recommandation par règles heuristiques.

Les symptômes sélectionnés donnent des points aux causes C1 à C15.
Les causes sont ensuite filtrées selon le carburant et la boîte de vitesses,
puis classées par score.
"""

from app.depots import recommandation as depot
from app.erreurs import ErreurApi


# Pour chaque symptôme :
# (id_cause, poids, nombre_de_plaintes)
#
# Les poids viennent du calcul effectué sur l'échantillon NHTSA.
REGLES = { # dictionnaire contenant les regles heuristiques
    # S2 : voyant moteur allumé
    2: [
        ("C15", 63, 61),
        ("C3", 56, 54),
        ("C12", 56, 54),
        ("C7", 51, 49),
        ("C8", 51, 49),
        ("C9", 51, 49),
        ("C1", 5, 5),
        ("C13", 5, 5),
    ],

    # S3 : perte de puissance
    3: [
        ("C15", 48, 52),
        ("C3", 41, 44),
        ("C8", 34, 37),
        ("C9", 34, 37),
        ("C5", 15, 16),
        ("C6", 15, 16),
    ],

    # S6 : direction dure ou bruyante
    6: [
        ("C10", 51, 20),
    ],

    # S7 : vibrations
    7: [
        ("C2", 11, 5),
    ],

    # S8 : fumée ou odeur de brûlé
    8: [
        ("C4", 38, 9),
        ("C12", 38, 9),
        ("C8", 29, 7),
        ("C9", 29, 7),
        ("C5", 21, 5),
    ],

    # S9 : moteur qui chauffe
    9: [
        ("C4", 54, 27),
    ],

    # S10 : vitesses qui passent mal
    10: [
        ("C5", 45, 27),
        ("C6", 45, 27),
    ],
}

# la fonction permet de garder seulement les causes compatibles avec le carburant, la boite 
def filtrer_causes(
    causes: list[dict],
    carburant: str | None,
    boite: str | None,
) -> list[dict]:
    """Retire les causes incompatibles avec le véhicule."""

    causes_filtrees = []

    for cause in causes:
        id_cause = cause["id_cause"]

        # Une voiture diesel n'utilise pas les bougies/bobines d'allumage prévues ici pour les moteurs essence.
        if carburant == "diesel" and id_cause == "C3":
            continue

        # Les causes C7, C8 et C9 sont spécifiques au diesel.
        if carburant == "essence" and id_cause in {"C7", "C8", "C9"}:
            continue

        # C5 concerne l'embrayage d'une boîte manuelle.
        if boite == "automatique" and id_cause == "C5":
            continue

        # C6 concerne une boîte automatique.
        if boite == "manuelle" and id_cause == "C6":
            continue

        causes_filtrees.append(cause)

    return causes_filtrees


def classer_causes(
    symptomes: list[int],
    carburant: str | None = None,
    boite: str | None = None,
) -> list[dict]:
    """Calcule et classe les causes à partir des symptômes."""

    # Récupération des causes C1 à C15 depuis le depot postgresql
    causes = depot.toutes_les_causes()

    # On élimine les causes incompatibles
    causes = filtrer_causes(causes, carburant, boite)

    ids_autorises = {cause["id_cause"] for cause in causes} # set( comme liste mais evite doublon) contenant les identifiants autorisés

    scores: dict[str, int] = {}
    plaintes: dict[str, int] = {} # nb plaintes 
    contributions: dict[str, list[dict]] = {} # symptomes qui ont contribués au score

    # On évite de compter deux fois le même symptôme.
    for symptome in dict.fromkeys(symptomes): # fromkeys permet de supprimer les doublons en conservant l'ordre

        for id_cause, poids, nb_plaintes in REGLES.get(symptome, []): # .get pour les cas où il n'y a pas de regles renvoi []

            if id_cause not in ids_autorises:
                continue

            scores[id_cause] = scores.get(id_cause, 0) + poids # ajoute le score 
            plaintes[id_cause] = plaintes.get(id_cause, 0) + nb_plaintes # ajoute  le nb de plaintes

            contributions.setdefault(id_cause, []).append({ # permet de conserver l'explication du score 
                "id_symptome": symptome,
                "points": poids,
            })

    if not scores:
        return []

    total = sum(scores.values()) # addition de tt les points

    causes_par_id = { # transformation de la liste des causes en dictionnaire 
        cause["id_cause"]: cause
        for cause in causes
    }

    # Classement selon 3 critères  :
    # 1. score décroissant
    # 2. nombre de plaintes décroissant
    # 3. identifiant de cause croissant
    ordre = sorted(
        scores,
        key=lambda id_cause: (
            -scores[id_cause], # - permet d'avoir le + grand score en 1
            -plaintes[id_cause], # si 2 causes ont le mm score celles qui a le + de plaintes passe avant
            int(id_cause[1:]), # si tt est egale on utilise l'id 
        ),
    )

    resultats = []

    for id_cause in ordre:
        cause = causes_par_id[id_cause] # récupération des infos de la cause

        resultats.append({
            "id_cause": id_cause,
            "libelle": cause["libelle"],
            "urgence": cause["urgence"],
            "score": scores[id_cause],
            "pourcentage": int(100 * scores[id_cause] / total + 0.5),
            "nb_plaintes": plaintes[id_cause],
            "contributions": contributions[id_cause],
        })

    return resultats


def _extrait(texte: str, longueur: int) -> str:
    """Réduit un texte trop long pour l'affichage."""

    texte = " ".join((texte or "").split()) # supp les espaces inutiles, ceux de trop entre le smots et rend none en " "

    if len(texte) <= longueur: # si texte deja court on laisse
        return texte

    return texte[:longueur].rstrip() + "..." # sinon seulement une partie 


def recommander(
    id_vehicule: int,
    symptomes: list[int],
    carburant: str | None = None,
    boite: str | None = None,
    limite: int = 5,
) -> list[dict]:
    """Retourne les problèmes correspondant aux causes classées."""

    if not depot.vehicule_existe(id_vehicule): # vérifie l'existence du vehicule
        raise ErreurApi(
            404,
            "VEHICULE_INCONNU",
            f"Aucun véhicule avec l'id {id_vehicule}.",
        )

    causes = classer_causes(
        symptomes,
        carburant,
        boite,
    )

    if not causes:
        return []

    ids_causes = [ # récupere les causes 
        cause["id_cause"]
        for cause in causes
    ]

    lignes = depot.problemes_par_causes( # récupere les problemes connus liés aux causes 
        id_vehicule,
        ids_causes,
        limite,
    )
    ordre_causes = {id_cause: position for position, id_cause in enumerate(ids_causes)} # dictionnaire gardant les positions
    lignes.sort(key=lambda ligne: ordre_causes[ligne["id_cause"]])

    solutions = depot.solutions_des_problemes( # réupere les solutions
        [ligne["id_probleme"] for ligne in lignes]
    )

    causes_par_id = {
        cause["id_cause"]: cause
        for cause in causes
    }

    resultats = []
    deja_vus: set[int] = set() # permet d'éviter les doublons

    for ligne in lignes:

        id_probleme = ligne["id_probleme"]

        if id_probleme in deja_vus:
            continue

        deja_vus.add(id_probleme)

        cause = causes_par_id[ligne["id_cause"]]

        resultats.append({
            "rang": len(resultats) + 1,
            "score": round(cause["pourcentage"] / 100, 2),
            "id_probleme": id_probleme,
            "titre": (
                ligne["titre"]
                or _extrait(ligne["description"], 80)
            ),
            "gravite": ligne["gravite"],
            "type_probleme": ligne["type_probleme"],
            "solutions": solutions.get(id_probleme, []),
            "explication": { # permet d'expliquer le resultat, de le justifier
                "composants_correspondants": [
                    ligne["categorie"]
                ],
                "nb_signalements": ligne["nb_signalements"],
                "extrait": _extrait(
                    ligne["description"],
                    200,
                ),
                "cause": cause["id_cause"],
                "libelle_cause": cause["libelle"],
                "urgence": cause["urgence"],
                "contributions": cause["contributions"],
            },
        })

        if len(resultats) == limite:
            break

    return resultats