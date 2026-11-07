"""Crée un échantillon de 1000 lignes NHTSA (véhicules uniquement, sans données personnelles).

Utilisation :
    python scripts/creer_echantillon.py FICHIER_BRUT.txt data/echantillon/echantillon_nhtsa.csv
"""
import argparse
from pathlib import Path

import pandas as pd

# Les 51 colonnes, dans l'ordre de CMPL.txt (le fichier n'a pas de ligne d'en-tête).
COLONNES = [
    "CMPLID", "ODINO", "MFR_NAME", "MAKETXT", "MODELTXT", "YEARTXT", "CRASH",
    "FAILDATE", "FIRE", "INJURED", "DEATHS", "COMPDESC", "CITY", "STATE", "VIN",
    "DATEA", "LDATE", "MILES", "OCCURENCES", "CDESCR", "CMPL_TYPE",
    "POLICE_RPT_YN", "PURCH_DT", "ORIG_OWNER_YN", "ANTI_BRAKES_YN",
    "CRUISE_CONT_YN", "NUM_CYLS", "DRIVE_TRAIN", "FUEL_SYS", "FUEL_TYPE",
    "TRANS_TYPE", "VEH_SPEED", "DOT", "TIRE_SIZE", "LOC_OF_TIRE",
    "TIRE_FAIL_TYPE", "ORIG_EQUIP_YN", "MANUF_DT", "SEAT_TYPE",
    "RESTRAINT_TYPE", "DEALER_NAME", "DEALER_TEL", "DEALER_CITY",
    "DEALER_STATE", "DEALER_ZIP", "PROD_TYPE", "REPAIRED_YN", "MEDICAL_ATTN",
    "VEHICLES_TOWED_YN", "STATE_OF_INCIDENT", "VEHICLE_OPERATOR",
]

# Colonnes qui identifient quelqu'un : on ne les garde pas.
COLONNES_EXCLUES = [
    "VIN", "CITY", "DEALER_NAME", "DEALER_TEL", "DEALER_CITY",
    "DEALER_STATE", "DEALER_ZIP", "VEHICLE_OPERATOR",
]

NB_LIGNES_ATTENDUES = 210_698  # fichier COMPLAINTS_RECEIVED_2025-2026 du 4 nov 2026
TAILLE_ECHANTILLON = 1000
GRAINE = 42  # graine fixe : toute l'équipe obtient le même échantillon


def lire_fichier_brut(chemin: Path) -> pd.DataFrame:
    """Lit le fichier NHTSA (tabulations, sans en-tête, tout en texte)."""
    return pd.read_csv(
        chemin,
        sep="\t",
        header=None,
        names=COLONNES,
        dtype=str,            # tout en texte : on ne perd ni zéros ni dates
        encoding="latin-1",
        quoting=3,            # pas de gestion des guillemets (ils sont dans les textes)
    )


def main() -> None:
    parseur = argparse.ArgumentParser(description=__doc__)
    parseur.add_argument("fichier_brut", type=Path)
    parseur.add_argument("sortie", type=Path)
    args = parseur.parse_args()

    if not args.fichier_brut.exists():
        parseur.error(
            f"Fichier introuvable : {args.fichier_brut}. "
            "Télécharge-le sur nhtsa.gov (page Complaints) et place-le dans data/nhtsa/."
        )

    donnees = lire_fichier_brut(args.fichier_brut)
    print(f"Lignes lues : {len(donnees)} (attendu pour ce fichier : {NB_LIGNES_ATTENDUES})")
    assert donnees.shape[1] == 51, "Le fichier doit avoir 51 colonnes"

    vehicules = donnees[donnees["PROD_TYPE"] == "V"]
    print(f"Lignes véhicules : {len(vehicules)}")

    vehicules = vehicules.drop(columns=COLONNES_EXCLUES)

    echantillon = vehicules.sample(n=TAILLE_ECHANTILLON, random_state=GRAINE)

    args.sortie.parent.mkdir(parents=True, exist_ok=True)
    echantillon.to_csv(args.sortie, index=False, encoding="utf-8")
    print(f"Échantillon écrit : {args.sortie} ({len(echantillon)} lignes, {echantillon.shape[1]} colonnes)")


if __name__ == "__main__":
    main()