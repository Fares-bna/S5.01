"""Ingestion des plaintes NHTSA : lecture -> transformation -> chargement en base.

Utilisation (depuis la racine du dépôt, base lancée avec `docker compose up -d`) :
    python -m pipeline.ingestion.ingerer_nhtsa data/echantillon/echantillon_nhtsa.csv
    python -m pipeline.ingestion.ingerer_nhtsa data/nhtsa/COMPLAINTS_RECEIVED_2025-2026.txt
"""
import argparse
from pathlib import Path

from dotenv import load_dotenv

from pipeline.ingestion.chargement_nhtsa import charger, se_connecter
from pipeline.ingestion.lecture_nhtsa import lire_plaintes
from pipeline.ingestion.transformation_nhtsa import transformer
from pipeline.ingestion.validation_nhtsa import valider_plaintes


def main() -> None:
    parseur = argparse.ArgumentParser(description=__doc__)
    parseur.add_argument("fichier", type=Path, help="échantillon .csv ou fichier brut NHTSA .txt")
    parseur.add_argument("--url", default=None, help="adresse de la source, enregistrée dans source_donnees")
    args = parseur.parse_args()

    load_dotenv()
    brut = lire_plaintes(args.fichier)
    print(f"Lignes lues : {len(brut)}")
    valider_plaintes(brut)
    print("Format validé.")
    tables = transformer(brut)
    print({nom: len(table) for nom, table in tables.items()})
    with se_connecter() as connexion:
        resultat = charger(tables, connexion, url=args.url)
    print("Chargement terminé :", resultat)


if __name__ == "__main__":
    main()
