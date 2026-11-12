"""Transforme les plaintes NHTSA (lues telles quelles) en tables prêtes pour la base.

Entrée : un DataFrame avec les colonnes du fichier NHTSA, tout en texte.
Sortie : un dict de DataFrames (un par table), sans accès à la base.
"""
import re

import pandas as pd

NOM_SOURCE = "NHTSA complaints"

# Valeurs autorisées par la contrainte chk_gravite du schéma (sans accents).
GRAVITE_FAIBLE = "faible"
GRAVITE_MODEREE = "moderee"
GRAVITE_ELEVEE = "elevee"
GRAVITE_CRITIQUE = "critique"

ANNEE_INCONNUE = "9999"  # valeur NHTSA pour « année inconnue » : devient NULL

# Numéros de téléphone américains (ex. 360-555-0123, (360) 555 0123).
MOTIF_TELEPHONE = re.compile(r"(?<!\d)(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}(?!\d)")
TELEPHONE_MASQUE = "[numéro masqué]"

# Textes qui ne décrivent rien : la plainte est écartée, comme un texte vide.
TEXTES_SANS_INFORMATION = {"unknown", "n/a", "na", "none", "desconocido", "."}


def est_texte_utile(texte: str) -> bool:
    return texte.strip().lower() not in TEXTES_SANS_INFORMATION


def calculer_gravite(ligne: pd.Series) -> str:
    """Gravité d'une plainte (règle validée avec Fares)."""
    if int(ligne["DEATHS"] or 0) > 0:
        return GRAVITE_CRITIQUE
    if (
        int(ligne["INJURED"] or 0) > 0
        or ligne["MEDICAL_ATTN"] == "Y"
        or ligne["FIRE"] == "Y"
        or ligne["CRASH"] == "Y"
    ):
        return GRAVITE_ELEVEE
    if ligne["VEHICLES_TOWED_YN"] == "Y":
        return GRAVITE_MODEREE
    return GRAVITE_FAIBLE


def masquer_telephones(texte: str) -> str:
    return MOTIF_TELEPHONE.sub(TELEPHONE_MASQUE, texte)


def categorie_composant(nom: str) -> str:
    """Catégorie = partie avant le premier « : » ; le reste du nom n'est pas fusionné."""
    return nom.split(":", 1)[0].strip()


def transformer(brut: pd.DataFrame) -> dict[str, pd.DataFrame]:
    donnees = brut[brut["PROD_TYPE"] == "V"].copy()

    donnees["CDESCR"] = donnees["CDESCR"].fillna("").str.strip()
    donnees = donnees[donnees["CDESCR"].map(est_texte_utile) & (donnees["CDESCR"] != "")]  # pas de texte : pas de plainte
    donnees["CDESCR"] = donnees["CDESCR"].map(masquer_telephones)

    for colonne in ("MAKETXT", "MODELTXT", "COMPDESC"):
        donnees[colonne] = donnees[colonne].fillna("").str.strip()
    donnees = donnees[(donnees["MAKETXT"] != "") & (donnees["MODELTXT"] != "")]

    donnees["annee"] = pd.to_numeric(
        donnees["YEARTXT"].where(donnees["YEARTXT"] != ANNEE_INCONNUE), errors="coerce"
    ).astype("Int64")
    donnees["date_signalement"] = pd.to_datetime(
        donnees["LDATE"], format="%Y%m%d", errors="coerce"
    ).dt.date

    # Carburant, boîte et cylindres ne sont pas dans le fichier NHTSA : NULL pour l'instant.
    # Les colonnes existent déjà, pour que le chargement n'ait pas à changer quand le
    # décodage du VIN les remplira.
    vehicules = (
        donnees[["MAKETXT", "MODELTXT", "annee"]]
        .rename(columns={"MAKETXT": "marque", "MODELTXT": "modele"})
        .drop_duplicates()
        .assign(carburant=None, boite=None, cylindres=None)
        .reset_index(drop=True)
    )

    # « UNKNOWN OR OTHER » reste dans la table composant (sans plainte reliée, il ne sort dans aucun résultat).
    sans_inconnu = donnees["COMPDESC"] != ""
    composants = (
        donnees.loc[sans_inconnu, ["COMPDESC"]]
        .drop_duplicates()
        .rename(columns={"COMPDESC": "nom"})
        .assign(categorie=lambda t: t["nom"].map(categorie_composant))
        .reset_index(drop=True)
    )

    # Une ligne par plainte (ODINO) ; les lignes d'une même plainte ont le même texte et le même véhicule.
    une_par_plainte = donnees.drop_duplicates("ODINO")
    problemes = pd.DataFrame(
        {
            "reference_externe": une_par_plainte["ODINO"],
            "type_probleme": "signalement",
            "description": une_par_plainte["CDESCR"],
            "gravite": une_par_plainte.apply(calculer_gravite, axis=1),
            "date_signalement": une_par_plainte["date_signalement"],
        }
    ).reset_index(drop=True)

    # « UNKNOWN OR OTHER » : la plainte est gardée, sans lien vers un composant (décision n°9).
    liens = donnees[donnees["COMPDESC"].ne("UNKNOWN OR OTHER") & sans_inconnu]
    probleme_composant = (
        liens[["ODINO", "COMPDESC", "CMPLID"]]
        .rename(columns={"ODINO": "reference_externe", "COMPDESC": "composant", "CMPLID": "cmplid"})
        .drop_duplicates(["reference_externe", "composant"])
        .reset_index(drop=True)
    )

    vehicule_probleme = (
        une_par_plainte[["ODINO", "MAKETXT", "MODELTXT", "annee"]]
        .rename(columns={"ODINO": "reference_externe", "MAKETXT": "marque", "MODELTXT": "modele"})
        .assign(carburant=None, boite=None, cylindres=None)
        .reset_index(drop=True)
    )

    return {
        "vehicule": vehicules,
        "composant": composants,
        "probleme": problemes,
        "probleme_composant": probleme_composant,
        "vehicule_probleme": vehicule_probleme,
    }