"""Accès à la base pour la recherche de véhicules (GET /api/vehicules)."""

from app.depots.recommandation import connexion


LIMITE_VEHICULES = 50 # évite de renvoyer toute la table si aucun filtre n'est donné


def chercher_vehicules(
    marque: str | None,
    modele: str | None,
    annee: int | None,
) -> list[dict]:
    """Cherche les véhicules correspondant aux filtres donnés."""

    conditions = []
    parametres = []

    # les données NHTSA sont en majuscules donc on compare sans tenir compte de la casse
    if marque:
        conditions.append("UPPER(marque) = UPPER(%s)")
        parametres.append(marque.strip())

    if modele:
        conditions.append("UPPER(modele) = UPPER(%s)")
        parametres.append(modele.strip())

    # un véhicule sans année (fréquent dans la NHTSA) reste proposé
    if annee is not None:
        conditions.append("(annee = %s OR annee IS NULL)")
        parametres.append(annee)

    # les conditions sont écrites ici en dur, les valeurs passent toujours par %s
    filtre = ""
    if conditions:
        filtre = "WHERE " + " AND ".join(conditions)

    requete = f"""
        SELECT
            id_vehicule,
            marque,
            modele,
            annee,
            carburant,
            boite,
            cylindres
        FROM vehicule
        {filtre}
        ORDER BY marque, modele, annee NULLS LAST, id_vehicule
        LIMIT %s
    """

    with connexion() as conn:
        lignes = conn.execute(requete, (*parametres, LIMITE_VEHICULES)).fetchall()

    return lignes
