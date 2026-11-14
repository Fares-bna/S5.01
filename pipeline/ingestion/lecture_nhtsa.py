"""Lecture des plaintes NHTSA : fichier brut (tabulations) ou échantillon CSV de l'équipe."""
from pathlib import Path

import pandas as pd

# Les 51 colonnes, dans l'ordre de CMPL.txt (le fichier brut n'a pas de ligne d'en-tête).
COLONNES_BRUT = [
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

# Seules colonnes dont on a besoin. On ne lit jamais le VIN, la ville, le concessionnaire, etc.
COLONNES_UTILES = [
    "CMPLID", "ODINO", "MAKETXT", "MODELTXT", "YEARTXT", "CRASH", "FIRE",
    "INJURED", "DEATHS", "COMPDESC", "LDATE", "CDESCR", "PROD_TYPE",
    "MEDICAL_ATTN", "VEHICLES_TOWED_YN",
]


def lire_plaintes(chemin: Path) -> pd.DataFrame:
    """Lit un fichier .csv (échantillon) ou .txt (fichier brut NHTSA), tout en texte."""
    if not chemin.exists():
        raise FileNotFoundError(f"Fichier introuvable : {chemin}")
    if chemin.suffix.lower() == ".csv":
        brut = pd.read_csv(chemin, dtype=str, keep_default_na=False, usecols=COLONNES_UTILES)
    else:
        brut = pd.read_csv(
            chemin,
            sep="\t",
            header=None,
            names=COLONNES_BRUT,
            usecols=COLONNES_UTILES,
            dtype=str,
            encoding="latin-1",
            quoting=3,
            keep_default_na=False,
        )
    return brut