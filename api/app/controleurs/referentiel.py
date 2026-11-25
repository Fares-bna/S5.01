"""GET /api/vehicules : recherche du véhicule saisi dans le formulaire du front."""

from typing import Annotated

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.depots import referentiel as depot


router = APIRouter(prefix="/api", tags=["vehicules"])


class Vehicule(BaseModel):
    id_vehicule: int
    marque: str
    modele: str
    annee: int | None = None # souvent inconnus dans les données NHTSA
    carburant: str | None = None
    boite: str | None = None
    cylindres: int | None = None


@router.get("/vehicules", response_model=list[Vehicule])
def lister_vehicules(
    marque: Annotated[str | None, Query(max_length=100)] = None,
    modele: Annotated[str | None, Query(max_length=100)] = None,
    annee: Annotated[int | None, Query(ge=1900, le=2100)] = None,
):
    """Liste des véhicules filtrée par marque, modèle et année.

    Le front s'en sert pour récupérer l'id_vehicule avant POST /api/recommandations.
    Aucun véhicule trouvé n'est pas une erreur : on renvoie une liste vide.
    """

    return depot.chercher_vehicules(marque, modele, annee)
