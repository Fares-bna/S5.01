from pathlib import Path

import pandas as pd
import pytest

from pipeline.ingestion.transformation_nhtsa import (
    calculer_gravite,
    categorie_composant,
    est_texte_utile,
    masquer_telephones,
    transformer,
)

ECHANTILLON = Path(__file__).resolve().parents[2] / "data" / "echantillon" / "echantillon_nhtsa.csv"


@pytest.fixture(scope="module")
def tables():
    brut = pd.read_csv(ECHANTILLON, dtype=str, keep_default_na=False)
    return transformer(brut)


def ligne(**valeurs):
    base = {"DEATHS": "0", "INJURED": "0", "MEDICAL_ATTN": "N", "FIRE": "N", "CRASH": "N", "VEHICLES_TOWED_YN": "N"}
    return pd.Series({**base, **valeurs})


def test_gravite():
    assert calculer_gravite(ligne(DEATHS="1")) == "critique"
    assert calculer_gravite(ligne(INJURED="2")) == "elevee"
    assert calculer_gravite(ligne(FIRE="Y")) == "elevee"
    assert calculer_gravite(ligne(VEHICLES_TOWED_YN="Y")) == "moderee"
    assert calculer_gravite(ligne()) == "faible"


def test_categorie_composant():
    assert categorie_composant("VISIBILITY:SUN/MOON ROOF ASSEMBLY") == "VISIBILITY"
    assert categorie_composant("SERVICE BRAKES, HYDRAULIC") == "SERVICE BRAKES, HYDRAULIC"
    assert categorie_composant("ENGINE") == "ENGINE"


def test_telephone_masque():
    assert "360-555-0123" not in masquer_telephones("Appelez le 360-555-0123 demain")


def test_nombres_echantillon(tables):
    assert len(tables["probleme"]) == 996
    assert tables["probleme"]["reference_externe"].is_unique
    assert len(tables["composant"]) == 67
    assert tables["vehicule"]["annee"].isna().sum() > 0


def test_valeurs_autorisees(tables):
    assert set(tables["probleme"]["gravite"]) <= {"faible", "moderee", "elevee", "critique"}
    assert (tables["probleme"]["description"].str.strip() != "").all()
    assert not tables["vehicule"]["annee"].eq(9999).any()


def test_unknown_or_other_sans_lien(tables):
    assert "UNKNOWN OR OTHER" not in set(tables["probleme_composant"]["composant"])
    assert tables["probleme_composant"].duplicated(["reference_externe", "composant"]).sum() == 0


def test_textes_sans_information():
    assert not est_texte_utile("N/A")
    assert not est_texte_utile(" Unknown ")
    assert est_texte_utile("Low coolant warning in red triangle")


def test_colonnes_vehicule(tables):
    assert list(tables["vehicule"].columns) == ["marque", "modele", "annee", "carburant", "boite", "cylindres"]
    assert tables["vehicule"][["carburant", "boite", "cylindres"]].isna().all().all()