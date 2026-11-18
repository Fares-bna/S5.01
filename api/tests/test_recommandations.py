
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app) # création client test à partir de FastAPI


def test_recommandation_valide():
    """Une requête valide doit retourner une réponse 200."""
    response = client.post( # envoi requete POST
        "/api/recommandations",
        json={
            "id_vehicule": 1,
            "description": "Le voyant moteur est allumé",
            "carburant": "essence",
            "boite": "manuelle",
            "symptomes": [2],
        },
    )

    assert response.status_code == 200


def test_recommandation_vehicule_inconnu():
    """Un véhicule inexistant doit retourner une erreur 404."""
    response = client.post(
        "/api/recommandations",
        json={
            "id_vehicule": 999999,
            "description": "Le voyant moteur est allumé",
            "carburant": "essence",
            "boite": "manuelle",
            "symptomes": [2],
        },
    )

    assert response.status_code == 404
    assert response.json()["erreur"]["code"] == "VEHICULE_INCONNU"


def test_recommandation_requete_invalide():
    """Une requête qui ne respecte pas le contrat doit retourner 422."""
    response = client.post(
        "/api/recommandations",
        json={
            "id_vehicule": 1,
            "description": "",
            "carburant": "essence",
            "boite": "manuelle",
            "symptomes": [2],
        },
    )

    assert response.status_code == 422
    assert response.json()["erreur"]["code"] == "REQUETE_INVALIDE"


def test_structure_reponse():
    """La réponse doit contenir les deux approches prévues par le contrat."""
    response = client.post(
        "/api/recommandations",
        json={
            "id_vehicule": 1,
            "description": "Le voyant moteur est allumé",
            "carburant": "essence",
            "boite": "manuelle",
            "symptomes": [2],
        },
    )

    data = response.json() # reponse sous format dico

    assert "id_requete" in data
    assert "heuristique" in data
    assert "embeddings" in data

    assert "temps_calcul_ms" in data["heuristique"]
    assert "nb_resultats" in data["heuristique"]
    assert "resultats" in data["heuristique"]
