"""Validation du format des plaintes NHTSA, avant toute transformation.

Le but n'est pas de juger la qualité des textes (la transformation s'en charge), mais de
détecter un changement de format du fichier : colonne manquante, date mal écrite, valeur
Y/N inattendue, identifiant en double. Dans ce cas, on s'arrête avant de charger quoi que ce soit.
"""
import pandas as pd
import pandera.pandas as pa

OUI_NON = ["Y", "N"]


def _dates_valides(serie: pd.Series) -> pd.Series:
    """Vrai pour les dates AAAAMMJJ qui existent vraiment (pas 20261342)."""
    return pd.to_datetime(serie, format="%Y%m%d", errors="coerce").notna()


SCHEMA_PLAINTES = pa.DataFrameSchema(
    {
        "CMPLID": pa.Column(str, pa.Check.str_matches(r"^\d+$"), unique=True),   # une ligne = un CMPLID
        "ODINO": pa.Column(str, pa.Check.str_matches(r"^\d+$")),                 # une plainte = un ODINO
        "MAKETXT": pa.Column(str),
        "MODELTXT": pa.Column(str),
        "YEARTXT": pa.Column(str, pa.Check.str_matches(r"^\d{4}$")),             # 9999 = inconnue
        "CRASH": pa.Column(str, pa.Check.isin(OUI_NON)),
        "FIRE": pa.Column(str, pa.Check.isin(OUI_NON)),
        "MEDICAL_ATTN": pa.Column(str, pa.Check.isin(OUI_NON)),
        "VEHICLES_TOWED_YN": pa.Column(str, pa.Check.isin([*OUI_NON, ""])),      # parfois vide
        "INJURED": pa.Column(str, pa.Check.str_matches(r"^\d+$")),
        "DEATHS": pa.Column(str, pa.Check.str_matches(r"^\d+$")),
        "COMPDESC": pa.Column(str),
        "LDATE": pa.Column(str, pa.Check(_dates_valides, element_wise=False, error="date AAAAMMJJ invalide")),
        "CDESCR": pa.Column(str),
        "PROD_TYPE": pa.Column(str, pa.Check.str_matches(r"^[A-Z]$")),
    },
    checks=pa.Check(lambda donnees: len(donnees) > 0, error="le fichier est vide"),
    strict=False,   # des colonnes en plus ne gênent pas
)

NB_EXEMPLES = 3


def valider_plaintes(brut: pd.DataFrame) -> None:
    """Lève une ValueError lisible si le format n'est pas celui attendu. Ne modifie rien."""
    try:
        SCHEMA_PLAINTES.validate(brut, lazy=True)
    except pa.errors.SchemaErrors as erreurs:
        cas = erreurs.failure_cases
        lignes = []
        for (colonne, controle), groupe in cas.groupby(["column", "check"], dropna=False):
            exemples = ", ".join(repr(v) for v in groupe["failure_case"].head(NB_EXEMPLES))
            lignes.append(f"- {colonne} : {controle} ({len(groupe)} cas, ex. {exemples})")
        raise ValueError("Format NHTSA inattendu, rien n'a été chargé :\n" + "\n".join(lignes)) from erreurs
