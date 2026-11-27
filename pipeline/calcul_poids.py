"""Calcul des poids des règles heuristiques : fréquence et gravité NHTSA.

Lancer depuis la racine du dépôt :  python -m pipeline.calcul_poids

Pour chaque couple (symptôme, cause) :
    fréquence = plaintes du symptôme qui concernent la cause / plaintes du symptôme
    gravité   = gravité moyenne de ces plaintes (faible = 0 ... critique = 1)
    poids     = fréquence x (1 + gravité), en pourcentage
"""

import re
from pathlib import Path

import pandas as pd

from pipeline.ingestion.lecture_nhtsa import lire_plaintes
from pipeline.ingestion.transformation_nhtsa import calculer_gravite


# Fichier NHTSA utilisé pour le calcul.
FICHIER_NHTSA = Path("data/nhtsa/COMPLAINTS_RECEIVED_2025-2026.txt")

# Seuils du document regles_heuristique.md
SEUIL_SYMPTOME = 20   # un symptôme repéré dans moins de 20 plaintes n'a pas de règle
SEUIL_REGLE = 3       # une règle qui repose sur moins de 3 plaintes n'est pas conservée

# Valeur numérique de chaque niveau de gravité (définie avec Yasmine).
VALEUR_GRAVITE = {
    "faible": 0,
    "moderee": 1 / 3,
    "elevee": 2 / 3,
    "critique": 1,
}

# Causes liées à chaque symptôme.
# Valeurs de départ déduites de l'ancien tableau de règles (liens ayant au moins 3 plaintes dans l'échantillon).
# Un symptôme dont la liste est vide est ignoré par le script.
LIENS_SYMPTOME_CAUSES = {
    "S1": ["C1","C3","C7","C13","C14"],    
    "S2": ["C15", "C3", "C12", "C7", "C8", "C9", "C1", "C13"],
    "S3": ["C15", "C3", "C8", "C9", "C5", "C6"],
    "S4": ["C2"],   
    "S5": ["C2"],    
    "S6": ["C10"],
    "S7": ["C2","C11"],
    "S8": ["C4", "C12", "C8", "C9", "C5"],
    "S9": ["C4"],
    "S10": ["C5", "C6"],
}

# Mots-clés utilisés pour reconnaître chaque symptôme (document regles_heuristique.md).
# "*" en fin de mot = début de mot : "vibrat*" repère "vibration" et "vibrating".
# permet de déterminer quel symptome est present dans une description nhtsa
REGLES_SYMPTOMES = {
    "S1": ["fail* to start", "not start", "no start", "hard start", "slow crank", "no crank"],
    "S2": ["check engine", "engine light", "malfunction indicator", "dtc"],
    "S3": ["stall*", "loss of power", "lost power", "hesitat*", "lag in",
           "loss of acceleration", "reduced power"],
    "S4": ["grind*", "squeal*", "squeak*", "screech*", "noise"],
    "S5": ["spongy", "soft pedal", "pedal to the floor", "brake fluid", "brakes failed",
           "not brake", "loss of brak*"],
    "S6": ["power steering", "hard to steer", "difficult to steer", "steering wheel locked",
           "steering became stiff", "stiff steering", "heavy steering"],
    "S7": ["vibrat*", "shak*", "shudder*", "wobbl*"],
    "S8": ["smoke", "smoking", "burning smell", "burnt smell", "smell of burning",
           "burning odor", "burning oil"],
    "S9": ["coolant", "head gasket", "engine overheat*", "overheating engine",
           "temperature gauge", "overheat*"],
    "S10": ["hard shift*", "harsh shift*", "shifting", "jerk*", "slipping",
            "transmission slip*", "clutch"],
}

# Le symptôme S4 (bruit au freinage) demande aussi le mot « brake » dans le texte.
MOT_DE_CONTEXTE = {"S4": "brake"}


def construire_motif(mot_cle: str) -> str:
    """Transforme un mot-clé en expression régulière.
    """

    base = re.escape(mot_cle.replace("*", "")).replace(r"\ ", r"\s+") # supprime *

    if mot_cle.endswith("*"): # si le mot finit par
        return r"\b" + base + r"\w*"     # début de mot, la fin peut varier

    return r"\b" + base + r"\b"          # mot (ou groupe de mots) exact


# On prépare une seule fois, pour chaque symptôme, l'expression qui contient tous ses mots-clés.
MOTIFS_SYMPTOMES = {
    id_symptome: re.compile("|".join(construire_motif(mot) for mot in mots_cles)) # transforme les mots cles en regex, et compile ensuite en un motif reutilisable
    for id_symptome, mots_cles in REGLES_SYMPTOMES.items() # pour chaque symptome on recupere son id et mot cles 
}


def trouver_symptomes(description: str) -> list[str]:
    """Retourne les symptômes détectés dans une description."""

    texte = description.lower() # tt en minuscule
    symptomes = []

    for id_symptome, motif in MOTIFS_SYMPTOMES.items(): #parcourt des symptomes

        if not motif.search(texte): # recherche d'elements similaires
            continue

        # Pour S4, le mot « brake » doit aussi être présent.
        mot_contexte = MOT_DE_CONTEXTE.get(id_symptome)
        if mot_contexte and not re.search(r"\b" + re.escape(mot_contexte),texte,): # symptome rejete si mot de descriptionest necessaire et non trouvé    
            continue

        symptomes.append(id_symptome)

    return symptomes


def charger_categories_par_cause() -> dict[str, set]:
    """Lit cause_composant.csv et renvoie {"C2": {"SERVICE BRAKES", ...}, ...}."""

    liens = pd.read_csv("bdd/donnees/cause_composant.csv", dtype=str) # lecture en chaine de caractere

    categories_par_cause = {}
    for id_cause in liens["id_cause"].unique():
        categories = liens[liens["id_cause"] == id_cause]["categorie"] # categorie correspondant à la cause
        categories_par_cause[id_cause] = set(categories) # transformation en set

    return categories_par_cause


def preparer_plaintes(df: pd.DataFrame) -> dict:
    """Une plainte = un ODINO. On garde sa description, sa gravité et toutes ses catégories."""

    df = df[df["PROD_TYPE"] == "V"] # on garde les plaintes concernant les vehicules
    plaintes = {}

    for odino, groupe in df.groupby("ODINO"): # regroupe les lignes ayant le même ODINO
        ligne = groupe.iloc[0]
        categories = set()

        for composant in groupe["COMPDESC"].fillna(""): # fillna transforme les chaines manquantes en vide
            composant = composant.strip() # suppression espace inutile

            if composant == "" or composant == "UNKNOWN OR OTHER":
                continue

            # La catégorie est la partie avant le premier « : », comme dans l'ingestion.
            categories.add(composant.split(":", 1)[0].strip())

        plaintes[odino] = {
            "description": ligne["CDESCR"],
            "gravite": calculer_gravite(ligne),
            "categories": categories,
        }

    return plaintes


def calculer_poids(plaintes: dict, categories_par_cause: dict) -> list[dict]:
    """Compte, pour chaque symptôme et chaque cause liée, les plaintes et leur gravité."""

    statistiques = {}

    for plainte in plaintes.values():
        valeur_gravite = VALEUR_GRAVITE[plainte["gravite"]] # convertit la gravité en valeur

        for id_symptome in trouver_symptomes(plainte["description"]): # recherche symptomes

            if id_symptome not in statistiques:
                statistiques[id_symptome] = {"total": 0, "causes": {}}

            # Une plainte compte une seule fois pour le symptôme.
            statistiques[id_symptome]["total"] += 1

            # Seules les causes liées au symptôme sont examinées.
            for id_cause in LIENS_SYMPTOME_CAUSES.get(id_symptome, []):

                # La plainte concerne la cause si une de ses catégories est une catégorie de la cause.
                if not plainte["categories"] & categories_par_cause[id_cause]:#important
                    continue

                causes = statistiques[id_symptome]["causes"]
                if id_cause not in causes:
                    causes[id_cause] = {"plaintes": 0, "gravites": []}

                causes[id_cause]["plaintes"] += 1 # compte les plaintes d'une cause
                causes[id_cause]["gravites"].append(valeur_gravite)

    resultats = []

    for id_symptome, donnees in statistiques.items():
        total_symptome = donnees["total"]

        if total_symptome < SEUIL_SYMPTOME: # application du seuil si pas assez pas de règles
            continue

        for id_cause, donnees_cause in donnees["causes"].items():
            nombre_plaintes = donnees_cause["plaintes"]

            if nombre_plaintes < SEUIL_REGLE:
                continue

            frequence = nombre_plaintes / total_symptome # calcul frequence
            gravite_moyenne = sum(donnees_cause["gravites"]) / nombre_plaintes
            poids = frequence * (1 + gravite_moyenne) * 100

            resultats.append({
                "symptome": id_symptome,
                "cause": id_cause,
                "plaintes": nombre_plaintes,
                "total_symptome": total_symptome,
                "frequence": frequence,
                "gravite_moyenne": gravite_moyenne,
                "poids": poids,
            })

    # Tri : symptôme S1, S2, ... puis poids décroissant.
    resultats.sort(key=lambda r: (int(r["symptome"][1:]), -r["poids"]))
    return resultats


def afficher_resultats(resultats: list[dict]) -> None:
    """Affiche le détail du calcul."""

    for r in resultats:
        print(
            f"{r['symptome']} -> {r['cause']} | {r['plaintes']} / {r['total_symptome']} | "
            f"frequence={r['frequence']:.3f} | gravite={r['gravite_moyenne']:.3f} | poids={r['poids']:.1f}"
        )


def afficher_regles(resultats: list[dict]) -> None:
    """Affiche le dictionnaire REGLES, prêt à copier dans app/services/heuristique.py."""

    regles = {}
    for r in resultats:
        numero = int(r["symptome"][1:])
        regles.setdefault(numero, []).append((r["cause"], round(r["poids"], 1), r["plaintes"]))
    print("\nREGLES = {")
    for numero in sorted(regles):
        print(f'    "S{numero}": [')
        for cause, poids, plaintes in regles[numero]:
            print(f'        ("{cause}", {poids}, {plaintes}),')
        print("    ],")
    print("}")


def main() -> None:
    """Point d'entrée du script."""

    print("Lecture du fichier NHTSA...")
    df = lire_plaintes(FICHIER_NHTSA)
    print(f"{len(df)} lignes lues (tous les produits, une ligne par composant).")

    plaintes = preparer_plaintes(df)
    print(f"{len(plaintes)} plaintes de véhicules (un ODINO = une plainte).")

    for id_symptome, causes in LIENS_SYMPTOME_CAUSES.items():
        if not causes:
            print(f"ATTENTION : {id_symptome} n'a aucune cause dans LIENS_SYMPTOME_CAUSES, il est ignoré.")

    print("Calcul des poids...\n")
    resultats = calculer_poids(plaintes, charger_categories_par_cause())

    afficher_resultats(resultats)
    afficher_regles(resultats)


if __name__ == "__main__":
    main()