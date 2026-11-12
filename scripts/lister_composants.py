"""Liste les composants (colonne COMPDESC) de l'échantillon NHTSA avec leur nombre de plaintes.

Sert à préparer la table causes ↔ composants : on relie nos causes (C1 à C15)
aux noms de composants qui existent vraiment dans les données.

Utilisation :
    python scripts/lister_composants.py data/echantillon/echantillon_nhtsa.csv
"""
import argparse
from pathlib import Path

import pandas as pd

# Dans COMPDESC, les niveaux sont séparés par ":".
# Exemple : "SERVICE BRAKES, HYDRAULIC:FOUNDATION COMPONENTS:MASTER CYLINDER"
#           -> niveau principal "SERVICE BRAKES, HYDRAULIC", puis deux sous-niveaux.
SEPARATEUR_NIVEAUX = ":"


def lire_echantillon(chemin: Path) -> pd.DataFrame:
    """Lit l'échantillon (CSV avec en-tête, tout en texte)."""
    # dtype=str : on garde les valeurs telles quelles, sans conversion en nombres.
    return pd.read_csv(chemin, dtype=str)


def niveau_principal(compdesc: str) -> str:
    """Garde seulement le premier niveau d'un COMPDESC.

    "ELECTRICAL SYSTEM:ALTERNATOR/GENERATOR/REGULATOR" -> "ELECTRICAL SYSTEM"
    "ENGINE" (un seul niveau)                         -> "ENGINE"
    """
    # split coupe le texte à chaque ":" et renvoie une liste ; [0] prend le premier morceau.
    # strip enlève les espaces autour (certaines valeurs ont un espace après le ":").
    return compdesc.split(SEPARATEUR_NIVEAUX)[0].strip()


def afficher_comptage(titre: str, comptage: pd.Series) -> None:
    """Affiche un comptage : une ligne par composant, du plus fréquent au moins fréquent."""
    print(f"\n{titre} ({len(comptage)} valeurs différentes)")
    # comptage.items() donne les paires (nom du composant, nombre de plaintes).
    for composant, nombre in comptage.items():
        # :>5 aligne le nombre à droite sur 5 caractères, pour que la liste soit lisible.
        print(f"{nombre:>5}  {composant}")


def main() -> None:
    parseur = argparse.ArgumentParser(description=__doc__)
    parseur.add_argument("echantillon", type=Path)
    args = parseur.parse_args()

    if not args.echantillon.exists():
        parseur.error(f"Fichier introuvable : {args.echantillon}")

    donnees = lire_echantillon(args.echantillon)
    print(f"Lignes lues : {len(donnees)}")

    # dropna retire les lignes sans composant ; str.strip enlève les espaces en trop.
    composants = donnees["COMPDESC"].dropna().str.strip()

    # 1. Les valeurs complètes, telles qu'elles sont écrites dans le fichier.
    #    value_counts compte chaque valeur et trie du plus fréquent au moins fréquent.
    afficher_comptage("Valeurs complètes de COMPDESC", composants.value_counts())

    # 2. Les mêmes valeurs ramenées à leur niveau principal.
    #    map applique niveau_principal à chaque ligne, puis on compte à nouveau.
    afficher_comptage("Niveau principal de COMPDESC", composants.map(niveau_principal).value_counts())


if __name__ == "__main__":
    main()
