from fastapi import FastAPI
 
from app.controleurs import recommandations, referentiel
from app.erreurs import installer_gestionnaires
 
app = FastAPI(title="DiagDuo API", version="0.1.0")
installer_gestionnaires(app)
app.include_router(recommandations.router)
app.include_router(referentiel.router)
 
 
@app.get("/health")
def health():
    return {"status": "ok"} # permet de vérifier que l'api est ok 
 