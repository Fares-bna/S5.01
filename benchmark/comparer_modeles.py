"""Compare plusieurs modèles d'embeddings pour l'approche B, sur l'échantillon NHTSA.

Exemple :
    python -m benchmark.comparer_modeles
    python -m benchmark.comparer_modeles --modeles paraphrase-multilingual-MiniLM-L12-v2

Pour chaque modèle :
1. on encode les plaintes de l'échantillon (une fois, comme le précalcul prévu dans l'approche B) ;
2. pour chaque description française du jeu `data/evaluation/descriptions_modeles.csv`,
   on cherche les plaintes les plus proches (similarité cosinus) ;
3. une plainte est « bonne » si l'une de ses catégories de composant fait partie des catégories attendues.

Mesures affichées par modèle :
- top-1 / top-3 : part des descriptions dont une bonne plainte est en 1re place / dans les 3 premières ;
- MRR : moyenne de 1/rang de la première bonne plainte (0 si elle n'est pas dans les 10 premières) ;
- temps de chargement du modèle, temps d'encodage des plaintes, temps moyen par requête ;
- mémoire prise par le chargement du modèle (RAM, en Mo, approximative).

Les modèles sont téléchargés depuis Hugging Face au premier lancement (quelques centaines de Mo chacun).
Aucune base n'est nécessaire : les plaintes sont lues et transformées comme dans le pipeline d'ingestion.
"""

import argparse
import csv
import gc
import sys
import time
from pathlib import Path

import numpy as np
import psutil
from sentence_transformers import SentenceTransformer

from pipeline.ingestion.lecture_nhtsa import lire_plaintes
from pipeline.ingestion.transformation_nhtsa import categorie_composant, transformer

ECHANTILLON_PAR_DEFAUT = "data/echantillon/echantillon_nhtsa.csv"
JEU_PAR_DEFAUT = "data/evaluation/descriptions_modeles.csv"

# Les 4 candidats retenus (multilingues, licence compatible MIT).
MODELES_PAR_DEFAUT = [
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "intfloat/multilingual-e5-small",
    "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
    "intfloat/multilingual-e5-base",
]

RANG_MAX = 10  # au-delà, on considère que la bonne plainte n'est pas trouvée (MRR = 0)


def lire_jeu(chemin):
    """Descriptions de test : id_cas, symptome, description, categories_attendues (séparées par « | »)."""
    with open(chemin, newline="", encoding="utf-8") as fichier:
        cas = list(csv.DictReader(fichier))
    for ligne in cas:
        ligne["categories_attendues"] = {c.strip() for c in ligne["categories_attendues"].split("|") if c.strip()}
    return cas


def lire_plaintes_avec_categories(chemin):
    """Renvoie deux listes alignées : le texte de chaque plainte et l'ensemble de ses catégories."""
    tables = transformer(lire_plaintes(Path(chemin)))
    liens = tables["probleme_composant"]
    categories = (
        liens.assign(categorie=liens["composant"].map(categorie_composant))
        .groupby("reference_externe")["categorie"]
        .agg(set)
        .to_dict()
    )
    problemes = tables["probleme"]
    textes = problemes["description"].tolist()
    categories_par_plainte = [categories.get(ref, set()) for ref in problemes["reference_externe"]]
    return textes, categories_par_plainte


def prefixes(nom_modele):
    """Les modèles E5 attendent « query: » devant la question et « passage: » devant les documents."""
    if "e5" in nom_modele.lower():
        return "query: ", "passage: "
    return "", ""


def rang_premiere_bonne(classement, categories_par_plainte, attendues):
    """Rang (1, 2, ...) de la première plainte dont une catégorie est attendue, ou None."""
    for rang, indice in enumerate(classement, start=1):
        if categories_par_plainte[indice] & attendues:
            return rang
    return None


def evaluer_modele(nom_modele, textes, categories_par_plainte, jeu):
    processus = psutil.Process()
    prefixe_requete, prefixe_document = prefixes(nom_modele)

    ram_avant = processus.memory_info().rss
    debut = time.perf_counter()
    modele = SentenceTransformer(nom_modele, device="cpu")
    temps_chargement = time.perf_counter() - debut
    ram_mo = (processus.memory_info().rss - ram_avant) / 1024 / 1024  # mémoire prise par le modèle

    # Précalcul : toutes les plaintes encodées une fois. Vecteurs normalisés => cosinus = produit scalaire.
    debut = time.perf_counter()
    vecteurs = modele.encode(
        [prefixe_document + t for t in textes], batch_size=32, normalize_embeddings=True
    )
    temps_encodage = time.perf_counter() - debut

    rangs, temps_requetes = [], []
    for cas in jeu:
        debut = time.perf_counter()
        requete = modele.encode(prefixe_requete + cas["description"], normalize_embeddings=True)
        similarites = vecteurs @ requete
        classement = np.argsort(-similarites)[:RANG_MAX]
        temps_requetes.append(time.perf_counter() - debut)
        rangs.append(rang_premiere_bonne(classement, categories_par_plainte, cas["categories_attendues"]))

    n = len(jeu)
    resultat = {
        "modele": nom_modele.split("/")[-1],
        "dimension": vecteurs.shape[1],
        "top1": sum(1 for r in rangs if r == 1) / n,
        "top3": sum(1 for r in rangs if r is not None and r <= 3) / n,
        "mrr": sum(1 / r for r in rangs if r is not None) / n,
        "chargement_s": temps_chargement,
        "encodage_s": temps_encodage,
        "requete_ms": 1000 * sum(temps_requetes) / n,
        "ram_mo": ram_mo,
        "rangs": rangs,
    }

    del modele, vecteurs  # libère la mémoire avant le modèle suivant
    gc.collect()
    return resultat


def afficher(resultats, nb_plaintes, nb_cas):
    print(f"\n{nb_plaintes} plaintes, {nb_cas} descriptions de test\n")
    print("| Modèle | Dim. | Top-1 | Top-3 | MRR | Chargement (s) | Encodage plaintes (s) | Requête (ms) | RAM (Mo) |")
    print("|---|---|---|---|---|---|---|---|---|")
    for r in resultats:
        print(
            f"| {r['modele']} | {r['dimension']} | {r['top1']:.0%} | {r['top3']:.0%} | {r['mrr']:.2f} "
            f"| {r['chargement_s']:.1f} | {r['encodage_s']:.1f} | {r['requete_ms']:.1f} | {r['ram_mo']:.0f} |"
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--echantillon", default=ECHANTILLON_PAR_DEFAUT)
    parser.add_argument("--jeu", default=JEU_PAR_DEFAUT)
    parser.add_argument("--modeles", nargs="+", default=MODELES_PAR_DEFAUT)
    parser.add_argument("--details", action="store_true", help="affiche le rang obtenu pour chaque description")
    args = parser.parse_args()

    jeu = lire_jeu(args.jeu)
    textes, categories_par_plainte = lire_plaintes_avec_categories(args.echantillon)

    resultats = []
    for nom in args.modeles:
        print(f"Modèle {nom}...", file=sys.stderr)
        resultats.append(evaluer_modele(nom, textes, categories_par_plainte, jeu))

    afficher(resultats, len(textes), len(jeu))

    if args.details:
        print("\n| Cas | " + " | ".join(r["modele"] for r in resultats) + " |")
        print("|---|" + "---|" * len(resultats))
        for i, cas in enumerate(jeu):
            rangs = [str(r["rangs"][i] or "-") for r in resultats]
            print(f"| {cas['id_cas']} | " + " | ".join(rangs) + " |")


if __name__ == "__main__":
    main()
