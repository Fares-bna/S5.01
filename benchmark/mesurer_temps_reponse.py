"""Mesure le temps de réponse de POST /api/recommandations.

Exemple :
    python -m benchmark.mesurer_temps_reponse --url http://localhost:8000 --n 100

Deux temps sont mesurés :
- le temps total vu par le client (réseau + API + base) ;
- le temps de calcul de chaque approche, lu dans `temps_calcul_ms` de la réponse.
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request

APPROCHES = ("heuristique", "embeddings")

CORPS_PAR_DEFAUT = {
    "id_vehicule": 1,
    "description": "Ma voiture fait un bruit lorsque je freine",
    "carburant": "diesel",
    "boite": "manuelle",
    "symptomes": [4],
}


def percentile(valeurs, p):
    """Percentile par interpolation linéaire (comme percentile_cont de PostgreSQL). p entre 0 et 1."""
    if not valeurs:
        raise ValueError("Aucune valeur à résumer")
    triees = sorted(valeurs)
    position = p * (len(triees) - 1)
    bas = int(position)
    haut = min(bas + 1, len(triees) - 1)
    return triees[bas] + (triees[haut] - triees[bas]) * (position - bas)


def resumer(valeurs):
    """Statistiques d'une liste de temps en millisecondes."""
    return {
        "n": len(valeurs),
        "min_ms": min(valeurs),
        "max_ms": max(valeurs),
        "moyen_ms": sum(valeurs) / len(valeurs),
        "mediane_ms": percentile(valeurs, 0.5),
        "p95_ms": percentile(valeurs, 0.95),
    }


def envoyer(url, corps, delai=30):
    """Envoie une requête de recommandation. Renvoie (durée en ms, réponse JSON)."""
    requete = urllib.request.Request(
        url.rstrip("/") + "/api/recommandations",
        data=json.dumps(corps).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    debut = time.perf_counter()
    with urllib.request.urlopen(requete, timeout=delai) as reponse:
        contenu = reponse.read()
    duree_ms = (time.perf_counter() - debut) * 1000
    return duree_ms, json.loads(contenu)


def mesurer(url, corps, n, echauffement):
    """Lance `echauffement` requêtes jetées, puis `n` requêtes mesurées."""
    for _ in range(echauffement):
        envoyer(url, corps)

    temps_total = []
    temps_serveur = {approche: [] for approche in APPROCHES}
    for _ in range(n):
        duree_ms, reponse = envoyer(url, corps)
        temps_total.append(duree_ms)
        for approche in APPROCHES:
            temps = (reponse.get(approche) or {}).get("temps_calcul_ms")
            if temps is not None:
                temps_serveur[approche].append(temps)
    return temps_total, temps_serveur


def construire_rapport(temps_total, temps_serveur):
    rapport = {"total_client": resumer(temps_total)}
    for approche, valeurs in temps_serveur.items():
        if valeurs:
            rapport[approche] = resumer(valeurs)
    return rapport


def afficher(rapport):
    print(f"{'mesure':<16}{'n':>5}{'min':>10}{'moyen':>10}{'médiane':>10}{'p95':>10}{'max':>10}   (ms)")
    for nom, r in rapport.items():
        print(
            f"{nom:<16}{r['n']:>5}{r['min_ms']:>10.1f}{r['moyen_ms']:>10.1f}"
            f"{r['mediane_ms']:>10.1f}{r['p95_ms']:>10.1f}{r['max_ms']:>10.1f}"
        )


def main():
    parseur = argparse.ArgumentParser(description="Mesure le temps de réponse de l'API de recommandation.")
    parseur.add_argument("--url", default="http://localhost:8000", help="adresse de l'API (défaut : %(default)s)")
    parseur.add_argument("--n", type=int, default=100, help="nombre de requêtes mesurées (défaut : %(default)s)")
    parseur.add_argument("--echauffement", type=int, default=5, help="requêtes jetées avant la mesure")
    parseur.add_argument("--corps", help="fichier JSON avec le corps de la requête (sinon un exemple fixe)")
    parseur.add_argument("--sortie", help="écrit le rapport en JSON dans ce fichier")
    args = parseur.parse_args()

    if args.n < 1:
        parseur.error("--n doit être au moins 1")

    corps = CORPS_PAR_DEFAUT
    if args.corps:
        with open(args.corps, encoding="utf-8") as fichier:
            corps = json.load(fichier)

    try:
        temps_total, temps_serveur = mesurer(args.url, corps, args.n, args.echauffement)
    except urllib.error.HTTPError as erreur:
        print(f"L'API a répondu {erreur.code} : {erreur.read().decode('utf-8', 'replace')}", file=sys.stderr)
        return 1
    except urllib.error.URLError as erreur:
        print(f"Impossible de joindre l'API ({args.url}) : {erreur.reason}", file=sys.stderr)
        return 1

    rapport = construire_rapport(temps_total, temps_serveur)
    afficher(rapport)

    if args.sortie:
        with open(args.sortie, "w", encoding="utf-8") as fichier:
            json.dump(rapport, fichier, indent=2, ensure_ascii=False)
        print(f"Rapport écrit dans {args.sortie}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
