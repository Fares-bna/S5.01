"""POST /api/recommandations.

Le contrôleur reçoit la requête HTTP, appelle les approches
et renvoie la réponse correspondant au contrat d'API.
"""

import time
from typing import Annotated, Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field, StringConstraints

from app.depots import recommandation as depot
from app.services import heuristique


router = APIRouter( prefix="/api", tags=["recommandations"],) # création routeur(ensemble de route) FastAPI


class RecommandationRequete(BaseModel):
    id_vehicule: int = Field(gt=0) # l'id doit être supérieur à 0

    description: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            min_length=3,
            max_length=2000,
        ),
    ]

    carburant: Literal[
        "essence",
        "diesel",
        "hybride",
        "electrique",
    ] | None = None

    boite: Literal[
        "manuelle",
        "automatique",
    ] | None = None

    symptomes: list[int] = Field(
        default_factory=list,
        max_length=20,
    )


class Solution(BaseModel):
    id_solution: int
    libelle: str
    description: str | None = None


class Explication(BaseModel):
    composants_correspondants: list[str] = Field(
        default_factory=list
    )

    nb_signalements: int | None = None

    similarite: float | None = None

    extrait: str | None = None

    cause: str | None = None

    libelle_cause: str | None = None

    urgence: str | None = None

    contributions: list[dict] = Field(
        default_factory=list
    )


class Resultat(BaseModel):
    rang: int
    score: float
    id_probleme: int
    titre: str

    gravite: Literal[
        "faible",
        "moderee",
        "elevee",
        "critique",
    ] | None = None

    type_probleme: Literal[
        "rappel",
        "signalement",
    ]

    solutions: list[Solution]

    explication: Explication


class BlocApproche(BaseModel):
    temps_calcul_ms: float | None = None
    nb_resultats: int
    resultats: list[Resultat]


class RecommandationReponse(BaseModel):
    id_requete: int
    heuristique: BlocApproche
    embeddings: BlocApproche


EMBEDDINGS_INDISPONIBLE = { # pas encore dispo
    "temps_calcul_ms": None,
    "nb_resultats": 0,
    "resultats": [],
}


@router.post(
    "/recommandations",
    response_model=RecommandationReponse,
    response_model_exclude_unset=True,
)
def recommander(requete: RecommandationRequete):
    """Lance l'approche heuristique et prépare la réponse API."""

    debut = time.perf_counter() # temps que cela prendra

    resultats = heuristique.recommander(
        id_vehicule=requete.id_vehicule,
        symptomes=requete.symptomes,
        carburant=requete.carburant,
        boite=requete.boite,
    )

    temps_ms = round( # temps convertit en ms
        (time.perf_counter() - debut) * 1000,
        1,
    )

    id_requete = depot.enregistrer_requete(
        requete.id_vehicule,
        requete.description,
        requete.carburant,
        requete.boite,
        requete.symptomes,
    )

    return {
        "id_requete": id_requete,

        "heuristique": {
            "temps_calcul_ms": temps_ms,
            "nb_resultats": len(resultats),
            "resultats": resultats,
        },

        "embeddings": EMBEDDINGS_INDISPONIBLE,
    }