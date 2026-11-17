"""Évalue la précision des recommandations sur un jeu de test séparé.

Exemple :
    python -m benchmark.evaluer_precision --url http://localhost:8000

Pour chaque cas du fichier CSV, on interroge l'API et on regarde à quel rang apparaît
la première bonne réponse (un des `titres_attendus`). On calcule ensuite, par approche :
- top-k : part des cas où une bonne réponse est dans les k premiers résultats ;
- MRR : moyenne de 1/rang de la première bonne réponse (0 si elle est absente).

Colonnes du CSV : id_cas, marque, modele, annee, carburant, boite, symptomes, description, titres_attendus.
`symptomes` et `titres_attendus` contiennent plusieurs valeurs séparées par « | ».
Les véhicules et les symptômes sont retrouvés par leur nom, donc le fichier ne dépend pas des id de la base.
"""

import argparse
import csv
import json
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

APPROCHES = ("heuristique", "embeddings")
JEU_PAR_DEFAUT = "data/evaluation/jeu_test.csv"


def normaliser(texte):
    """Minuscules, sans accents, espaces nettoyés : « Étrier  de frein » == « etrier de frein »."""
    sans_accents = unicodedata.normalize("NFD", texte or "")
    sans_accents = "".join(c for c in sans_accents if unicodedata.category(c) != "Mn")
    return " ".join(sans_accents.lower().split())


def separer(valeur):
    return [partie.strip() for partie in (valeur or "").split("|") if partie.strip()]


def lire_jeu(chemin):
    with open(chemin, encoding="utf-8", newline="") as fichier:
        return list(csv.DictReader(fichier))


def rang_attendu(resultats, titres_attendus):
    """Rang (à partir de 1) de la première bonne réponse, ou None si absente."""
    attendus = {normaliser(titre) for titre in titres_attendus}
    for position, resultat in enumerate(resultats, start=1):
        if normaliser(resultat.get("titre")) in attendus:
            return resultat.get("rang", position)
    return None


def calculer_scores(rangs, ks=(1, 3, 5)):
    """`rangs` : un rang (ou None) par cas. Renvoie les top-k et le MRR."""
    n = len(rangs)
    scores = {"n": n}
    for k in ks:
        scores[f"top{k}"] = sum(1 for r in rangs if r is not None and r <= k) / n if n else 0.0
    scores["mrr"] = sum(1 / r for r in rangs if r is not None) / n if n else 0.0
    return scores


def appeler(url, chemin, corps=None, parametres=None, delai=30):
    adresse = url.rstrip("/") + chemin
    if parametres:
        adresse += "?" + urllib.parse.urlencode(parametres)
    donnees = json.dumps(corps).encode("utf-8") if corps is not None else None
    requete = urllib.request.Request(
        adresse,
        data=donnees,
        headers={"Content-Type": "application/json"},
        method="POST" if corps is not None else "GET",
    )
    with urllib.request.urlopen(requete, timeout=delai) as reponse:
        return json.loads(reponse.read())


def trouver_vehicule(url, cas):
    parametres = {"marque": cas["marque"], "modele": cas["modele"]}
    if cas.get("annee"):
        parametres["annee"] = cas["annee"]
    vehicules = appeler(url, "/api/vehicules", parametres=parametres)
    return vehicules[0]["id_vehicule"] if vehicules else None


def construire_requete(cas, id_vehicule, ids_symptomes):
    corps = {"id_vehicule": id_vehicule, "description": cas["description"]}
    if cas.get("carburant"):
        corps["carburant"] = cas["carburant"]
    if cas.get("boite"):
        corps["boite"] = cas["boite"]
    libelles = separer(cas.get("symptomes"))
    corps["symptomes"] = [ids_symptomes[normaliser(libelle)] for libelle in libelles]
    return corps


def evaluer(url, cas_de_test, ks=(1, 3, 5)):
    """Renvoie (scores par approche, liste des cas ignorés, liste des échecs)."""
    ids_symptomes = {normaliser(s["libelle"]): s["id_symptome"] for s in appeler(url, "/api/symptomes")}
    rangs = {approche: [] for approche in APPROCHES}
    ignores, echecs = [], []

    for cas in cas_de_test:
        id_vehicule = trouver_vehicule(url, cas)
        inconnus = [s for s in separer(cas.get("symptomes")) if normaliser(s) not in ids_symptomes]
        if id_vehicule is None or inconnus:
            raison = "véhicule introuvable" if id_vehicule is None else f"symptôme inconnu : {inconnus}"
            ignores.append((cas["id_cas"], raison))
            continue

        reponse = appeler(url, "/api/recommandations", corps=construire_requete(cas, id_vehicule, ids_symptomes))
        attendus = separer(cas["titres_attendus"])
        for approche in APPROCHES:
            resultats = (reponse.get(approche) or {}).get("resultats") or []
            if not resultats:
                continue  # approche indisponible ou sans résultat : on ne la compte pas
            rang = rang_attendu(resultats, attendus)
            rangs[approche].append(rang)
            if rang is None:
                echecs.append((cas["id_cas"], approche, attendus, resultats[0].get("titre")))

    scores = {approche: calculer_scores(r, ks) for approche, r in rangs.items() if r}
    return scores, ignores, echecs


def afficher(scores, ignores, echecs, ks=(1, 3, 5)):
    if not scores:
        print("Aucune approche n'a renvoyé de résultat : rien à évaluer.")
    else:
        colonnes = "".join(f"{'top-' + str(k):>9}" for k in ks)
        print(f"{'approche':<14}{'cas':>5}{colonnes}{'MRR':>9}")
        for approche, s in scores.items():
            valeurs = "".join(f"{s[f'top{k}']:>9.0%}" for k in ks)
            print(f"{approche:<14}{s['n']:>5}{valeurs}{s['mrr']:>9.2f}")
    if ignores:
        print("\nCas ignorés :")
        for id_cas, raison in ignores:
            print(f"  {id_cas} : {raison}")
    if echecs:
        print("\nCas où la bonne réponse n'est pas dans les résultats :")
        for id_cas, approche, attendus, obtenu in echecs:
            print(f"  {id_cas} [{approche}] attendu : {attendus} | 1er résultat : {obtenu}")


def main():
    parseur = argparse.ArgumentParser(description="Évalue la précision des recommandations.")
    parseur.add_argument("--url", default="http://localhost:8000", help="adresse de l'API (défaut : %(default)s)")
    parseur.add_argument("--jeu", default=JEU_PAR_DEFAUT, help="fichier CSV du jeu de test (défaut : %(default)s)")
    args = parseur.parse_args()

    cas_de_test = lire_jeu(args.jeu)
    try:
        scores, ignores, echecs = evaluer(args.url, cas_de_test)
    except urllib.error.HTTPError as erreur:
        print(f"L'API a répondu {erreur.code} : {erreur.read().decode('utf-8', 'replace')}", file=sys.stderr)
        return 1
    except urllib.error.URLError as erreur:
        print(f"Impossible de joindre l'API ({args.url}) : {erreur.reason}", file=sys.stderr)
        return 1

    afficher(scores, ignores, echecs)
    return 0


if __name__ == "__main__":
    sys.exit(main())
