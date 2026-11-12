"""Charge en base les tables produites par transformation_nhtsa.

Rejouable : on peut relancer le chargement sans créer de doublons (NHTSA met son fichier à jour,
donc une plainte déjà présente est mise à jour au lieu d'être recréée).
Tout se fait dans une seule transaction : en cas d'erreur, rien n'est écrit.
"""
import os

import pandas as pd
import psycopg

from pipeline.ingestion.transformation_nhtsa import NOM_SOURCE

TAILLE_LOT = 5000


def se_connecter() -> psycopg.Connection:
    """Connexion PostgreSQL, avec les variables du fichier .env (voir .env.example)."""
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        dbname=os.environ["POSTGRES_DB"],
    )


def _valeur(v):
    """pandas -> Python : <NA> et NaN deviennent None (NULL en base)."""
    return None if pd.isna(v) else (int(v) if hasattr(v, "item") and isinstance(v.item(), int) else v)


def _lignes(table: pd.DataFrame, colonnes: list[str]) -> list[tuple]:
    return [tuple(_valeur(v) for v in ligne) for ligne in table[colonnes].itertuples(index=False, name=None)]


def _par_lots(lignes: list[tuple]):
    for debut in range(0, len(lignes), TAILLE_LOT):
        yield lignes[debut : debut + TAILLE_LOT]


def charger(tables: dict[str, pd.DataFrame], connexion: psycopg.Connection,
            url: str | None = None, licence: str = "à vérifier") -> dict[str, int]:
    """Charge les tables dans l'ordre imposé par les clés étrangères. Retourne les nombres de lignes."""
    with connexion.transaction(), connexion.cursor() as curseur:
        # 1. Source (une ligne, mise à jour à chaque import)
        curseur.execute(
            """INSERT INTO source_donnees (nom, url, licence, date_import)
               VALUES (%s, %s, %s, now())
               ON CONFLICT (nom) DO UPDATE SET date_import = now()
               RETURNING id_source""",
            (NOM_SOURCE, url, licence),
        )
        id_source = curseur.fetchone()[0]

        # 2. Composants
        for lot in _par_lots(_lignes(tables["composant"], ["nom", "categorie"])):
            curseur.executemany(
                "INSERT INTO composant (nom, categorie) VALUES (%s, %s) ON CONFLICT (nom) DO NOTHING", lot
            )
        curseur.execute("SELECT nom, id_composant FROM composant")
        id_composant = dict(curseur.fetchall())

        # 3. Véhicules (carburant, boîte, cylindres inconnus : NULL)
        for lot in _par_lots(_lignes(tables["vehicule"], ["marque", "modele", "annee"])):
            curseur.executemany(
                """INSERT INTO vehicule (marque, modele, annee) VALUES (%s, %s, %s)
                   ON CONFLICT ON CONSTRAINT uq_vehicule DO NOTHING""",
                lot,
            )
        curseur.execute(
            """SELECT marque, modele, annee, id_vehicule FROM vehicule
               WHERE carburant IS NULL AND boite IS NULL AND cylindres IS NULL"""
        )
        id_vehicule = {(m, mo, a): i for m, mo, a, i in curseur.fetchall()}

        # 4. Problèmes (une plainte = un ODINO) ; relancer met à jour le texte, la gravité, la date
        lignes = [(id_source, *ligne) for ligne in _lignes(
            tables["probleme"], ["reference_externe", "type_probleme", "description", "gravite", "date_signalement"])]
        for lot in _par_lots(lignes):
            curseur.executemany(
                """INSERT INTO probleme (id_source, reference_externe, type_probleme, description, gravite, date_signalement)
                   VALUES (%s, %s, %s, %s, %s, %s)
                   ON CONFLICT ON CONSTRAINT uq_probleme_source DO UPDATE
                   SET description = EXCLUDED.description, gravite = EXCLUDED.gravite,
                       date_signalement = EXCLUDED.date_signalement""",
                lot,
            )
        curseur.execute("SELECT reference_externe, id_probleme FROM probleme WHERE id_source = %s", (id_source,))
        id_probleme = dict(curseur.fetchall())

        # 5. Liens plainte <-> composant (cmplid = identifiant de la ligne NHTSA)
        liens = [
            (id_probleme[ref], id_composant[comp], cmplid)
            for ref, comp, cmplid in _lignes(tables["probleme_composant"], ["reference_externe", "composant", "cmplid"])
        ]
        for lot in _par_lots(liens):
            curseur.executemany(
                """INSERT INTO probleme_composant (id_probleme, id_composant, cmplid) VALUES (%s, %s, %s)
                   ON CONFLICT (id_probleme, id_composant) DO UPDATE SET cmplid = EXCLUDED.cmplid""",
                lot,
            )

        # 6. Liens véhicule <-> plainte
        liens_vehicule = []
        for ref, marque, modele, annee in _lignes(
                tables["vehicule_probleme"], ["reference_externe", "marque", "modele", "annee"]):
            liens_vehicule.append((id_vehicule[(marque, modele, annee)], id_probleme[ref]))
        for lot in _par_lots(liens_vehicule):
            curseur.executemany(
                """INSERT INTO vehicule_probleme (id_vehicule, id_probleme) VALUES (%s, %s)
                   ON CONFLICT DO NOTHING""",
                lot,
            )

    return {nom: len(table) for nom, table in tables.items()}