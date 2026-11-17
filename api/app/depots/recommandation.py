"""Accès à la base de données pour l'approche heuristique, permet de faire le lien entre python et postgresql"""

import os

import psycopg # pilote python qui communique avec postgresql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from dotenv import load_dotenv


load_dotenv()

def connexion():
    """Ouvre une connexion à PostgreSQL."""

    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"), # récupération adresse postgresql
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        row_factory=dict_row, # les lignes seront retouner sous forme de dictionnaire
    )


def vehicule_existe(id_vehicule: int) -> bool:
    """Vérifie que le véhicule existe dans la base."""

    with connexion() as conn:
        ligne = conn.execute(
            """
            SELECT 1
            FROM vehicule
            WHERE id_vehicule = %s
            """,
            (id_vehicule,), # SELECT 1 car on souhaite seulemnt savoir s'il existe pas d'infos
        ).fetchone()

    return ligne is not None


def enregistrer_requete(
    id_vehicule,
    description,
    carburant,
    boite,
    symptomes,
) -> int:
    """Enregistre la requête de l'utilisateur."""

    with connexion() as conn:
        ligne = conn.execute(
            """
            INSERT INTO requete_utilisateur (
                id_vehicule,
                carburant,
                boite,
                symptomes_saisis,
                description_saisie
            )
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id_requete 
            """, # retourne l'identifiant créer et %s est une requete parametré evite de faire WHERE id_vehicule={id_vehicule} 
            # Returning retourne l'id de la requet ce qui permet un suivi de celle-ci et identifier de maniere unique
            (
                id_vehicule,
                carburant,
                boite,
                Jsonb(symptomes), # envoi la liste des symptomes dans la colonne jsonb
                description,
            ),
        ).fetchone()

    return ligne["id_requete"] # renvoi l'id au controleur


def toutes_les_causes() -> list[dict]:
    """Récupère toutes les causes C1 à C15."""

    with connexion() as conn:
        lignes = conn.execute(
            """
            SELECT
                id_cause,
                libelle,
                carburant,
                boite,
                urgence
            FROM cause
            ORDER BY id_cause
            """
        ).fetchall()

    return lignes

# Cette fonction utilise plusieurs jointures SQL pour retrouver, pour un véhicule donné, les problèmes associés aux catégories de composants des causes retenues, puis les classe par gravité et date.
def problemes_par_causes(
    id_vehicule: int,
    ids_causes: list[str],
    limite: int,
) -> list[dict]:
    """Cherche les problèmes du véhicule liés aux causes données.

    Une cause peut être liée à plusieurs catégories NHTSA
    grâce à la table cause_composant.
    """

    if not ids_causes:
        return []

    requete = """
        WITH liaisons AS (
            SELECT 
                cc.id_cause,
                MIN(c.categorie) AS categorie,
                p.id_probleme,
                p.titre,
                p.description,
                p.gravite,
                p.type_probleme,
                p.date_signalement
            FROM cause_composant cc

            JOIN composant c
                ON c.categorie = cc.categorie

            JOIN probleme_composant pc 
                ON pc.id_composant = c.id_composant

            JOIN probleme p
                ON p.id_probleme = pc.id_probleme

            JOIN vehicule_probleme vp
                ON vp.id_probleme = p.id_probleme

            WHERE vp.id_vehicule = %s
              AND cc.id_cause = ANY(%s)
            GROUP BY cc.id_cause, p.id_probleme

        ),

        classees AS (
            SELECT
                liaisons.*,

                COUNT(*) OVER (
                    PARTITION BY id_cause
                ) AS nb_signalements,

                ROW_NUMBER() OVER (
                    PARTITION BY id_cause
                    ORDER BY
                        CASE gravite
                            WHEN 'critique' THEN 4
                            WHEN 'elevee' THEN 3
                            WHEN 'moderee' THEN 2
                            WHEN 'faible' THEN 1
                            ELSE 0
                        END DESC,
                        date_signalement DESC NULLS LAST,
                        id_probleme
                ) AS rang_cause

            FROM liaisons
        )

        SELECT
            id_cause,
            categorie,
            id_probleme,
            titre,
            description,
            gravite,
            type_probleme,
            nb_signalements

        FROM classees

        WHERE rang_cause <= %s

        ORDER BY id_cause, rang_cause
    """

    with connexion() as conn:
        lignes = conn.execute(
            requete,
            (
                id_vehicule,
                ids_causes,
                limite,
            ),
        ).fetchall()

    return lignes


def solutions_des_problemes(
    ids_probleme: list[int],
) -> dict[int, list[dict]]:
    """Récupère les solutions associées aux problèmes."""

    if not ids_probleme:
        return {}

    with connexion() as conn:
        lignes = conn.execute(
            """
            SELECT
                ps.id_probleme,
                s.id_solution,
                s.libelle,
                s.description

            FROM probleme_solution ps

            JOIN solution s
                ON s.id_solution = ps.id_solution

            WHERE ps.id_probleme = ANY(%s)

            ORDER BY s.id_solution
            """,
            (ids_probleme,),
        ).fetchall()

    resultat: dict[int, list[dict]] = {}

    for ligne in lignes:
        resultat.setdefault( # si le pb n'existe pas liste vide
            ligne["id_probleme"],
            [],
        ).append({
            "id_solution": ligne["id_solution"],
            "libelle": ligne["libelle"],
            "description": ligne["description"],
        })

    return resultat