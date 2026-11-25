from pathlib import Path

import pandas as pd
import pytest

from pipeline.ingestion.lecture_nhtsa import lire_plaintes
from pipeline.ingestion.validation_nhtsa import valider_plaintes

ECHANTILLON = Path(__file__).resolve().parents[2] / "data" / "echantillon" / "echantillon_nhtsa.csv"


@pytest.fixture()
def brut() -> pd.DataFrame:
    return lire_plaintes(ECHANTILLON)


def test_echantillon_valide(brut):
    valider_plaintes(brut)   # ne doit rien lever


def test_colonne_manquante(brut):
    with pytest.raises(ValueError, match="LDATE"):
        valider_plaintes(brut.drop(columns=["LDATE"]))


def test_date_invalide(brut):
    brut.loc[brut.index[0], "LDATE"] = "20261342"
    with pytest.raises(ValueError, match="LDATE"):
        valider_plaintes(brut)


def test_cmplid_en_double(brut):
    brut.loc[brut.index[1], "CMPLID"] = brut.loc[brut.index[0], "CMPLID"]
    with pytest.raises(ValueError, match="CMPLID"):
        valider_plaintes(brut)


def test_valeur_oui_non_inattendue(brut):
    brut.loc[brut.index[0], "FIRE"] = "X"
    with pytest.raises(ValueError, match="FIRE"):
        valider_plaintes(brut)


def test_annee_mal_formee(brut):
    brut.loc[brut.index[0], "YEARTXT"] = "20X4"
    with pytest.raises(ValueError, match="YEARTXT"):
        valider_plaintes(brut)


def test_fichier_vide(brut):
    with pytest.raises(ValueError, match="vide"):
        valider_plaintes(brut.iloc[0:0])
