"""Tests du chargement : ils ont besoin de la base (docker compose up -d), sinon ils sont ignorés.

Chaque test travaille dans un schéma temporaire : la vraie base n'est pas touchée.
"""
from pathlib import Path

import psycopg
import pytest
from dotenv import load_dotenv

from pipeline.ingestion.chargement_nhtsa import charger, se_connecter
from pipeline.ingestion.lecture_nhtsa import lire_plaintes
from pipeline.ingestion.transformation_nhtsa import transformer

RACINE = Path(__file__).resolve().parents[2]
load_dotenv(RACINE / ".env")


@pytest.fixture()
def connexion():
    try:
        conn = se_connecter()
    except (psycopg.OperationalError, KeyError) as erreur:  # base absente ou variables .env manquantes
        pytest.skip(f"Base indisponible : {erreur}")
    conn.execute("DROP SCHEMA IF EXISTS test_ingestion CASCADE")
    conn.execute("CREATE SCHEMA test_ingestion")
    conn.execute("SET search_path TO test_ingestion")
    conn.execute((RACINE / "bdd" / "schema.sql").read_text(encoding="utf-8"))
    conn.commit()
    yield conn
    conn.rollback()
    conn.execute("DROP SCHEMA test_ingestion CASCADE")
    conn.commit()
    conn.close()


@pytest.fixture(scope="module")
def tables():
    return transformer(lire_plaintes(RACINE / "data" / "echantillon" / "echantillon_nhtsa.csv"))


def compter(conn, table):
    return conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]


def test_chargement_echantillon(connexion, tables):
    charger(tables, connexion)
    assert compter(connexion, "probleme") == 996
    assert compter(connexion, "composant") == 67
    assert compter(connexion, "source_donnees") == 1
    assert compter(connexion, "vehicule_probleme") == 996


def test_chargement_rejouable(connexion, tables):
    charger(tables, connexion)
    avant = {t: compter(connexion, t) for t in ("probleme", "composant", "vehicule", "probleme_composant", "vehicule_probleme")}
    charger(tables, connexion)
    apres = {t: compter(connexion, t) for t in avant}
    assert avant == apres


def test_annee_inconnue_en_null(connexion, tables):
    charger(tables, connexion)
    assert connexion.execute("SELECT count(*) FROM vehicule WHERE annee IS NULL").fetchone()[0] > 0
    assert connexion.execute("SELECT count(*) FROM vehicule WHERE annee = 9999").fetchone()[0] == 0


def test_chargement_avec_carburant_rempli(connexion, tables):
    """Quand le décodage du VIN remplira le carburant, le chargement ne doit pas changer."""
    avec_carburant = {nom: table.copy() for nom, table in tables.items()}
    for nom in ("vehicule", "vehicule_probleme"):
        avec_carburant[nom]["carburant"] = "diesel"
    charger(avec_carburant, connexion)
    assert compter(connexion, "vehicule_probleme") == 996
    assert connexion.execute("SELECT count(*) FROM vehicule WHERE carburant = 'diesel'").fetchone()[0] == len(tables["vehicule"])