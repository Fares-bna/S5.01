"""Gestion des erreurs : toutes les erreurs de l'API ont le même format (voir docs/contrat_api.md).

    {"erreur": {"code": "VEHICULE_INCONNU", "message": "...", "details": null}}
"""
import logging # module python permettant d'ecrire des infos dans les logs du serveur

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException # recupere les erreurs classqiues

# Le journal sert à écrire les détails d'une erreur inattendue dans le terminal du serveur.
journal = logging.getLogger("diagduo")


class ErreurApi(Exception):
    """Erreur prévue par le contrat : par exemple 404 VEHICULE_INCONNU."""

    def __init__(self, statut, code, message, details=None):
        self.statut = statut      # code HTTP : 404, 422...
        self.code = code          # code lu par le front : "VEHICULE_INCONNU"
        self.message = message    
        self.details = details    # liste des champs en erreur, ou None


def reponse_erreur(statut, code, message, details=None):
    """Fabrique la réponse JSON d'une erreur, toujours au même format."""
    corps = {"erreur": {"code": code, "message": message, "details": details}}
    return JSONResponse(status_code=statut, content=corps)


def installer_gestionnaires(app):
    """Dit à l'application quelle réponse renvoyer pour chaque type d'erreur."""

    @app.exception_handler(ErreurApi)
    async def gerer_erreur_api(request: Request, exc: ErreurApi):
        return reponse_erreur(exc.statut, exc.code, exc.message, exc.details)

    @app.exception_handler(RequestValidationError) # utiliser si données ne respectent pas le modèle prévu
    async def gerer_validation(request: Request, exc: RequestValidationError):
        # exc.errors() est la liste des champs invalides. "loc" ressemble à ("body", "description"),
        # on enlève le premier élément (("body")= indique que cela vient des données envoyées par l'utilisateur) pour ne garder que le nom du champ.
        details = []
        for erreur in exc.errors():
            morceaux = [str(m) for m in erreur["loc"][1:]] # 
            details.append({"champ": ".".join(morceaux), "message": erreur["msg"]})
        return reponse_erreur(422, "REQUETE_INVALIDE", "La requête ne respecte pas le contrat d'API.", details)

    @app.exception_handler(StarletteHTTPException)
    async def gerer_erreur_http(request: Request, exc: StarletteHTTPException):
        # Erreurs de FastAPI lui-même : route inexistante (404), mauvaise méthode (405)...
        if exc.status_code == 404:
            code = "NON_TROUVE"
        elif exc.status_code == 405:
            code = "METHODE_NON_AUTORISEE"
        else:
            code = "ERREUR_HTTP"
        return reponse_erreur(exc.status_code, code, str(exc.detail))

    @app.exception_handler(Exception)
    async def gerer_erreur_inattendue(request: Request, exc: Exception):
        # Bug du code ou base inaccessible. La trace va dans le terminal du serveur, jamais dans la réponse.
        journal.exception("Erreur inattendue")
        return reponse_erreur(500, "ERREUR_INTERNE", "Une erreur interne est survenue.")