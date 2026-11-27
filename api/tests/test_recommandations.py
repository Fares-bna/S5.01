
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


def test_recommandation_s3_s10_essence_manuelle():
    """S3 + S10 doivent utiliser les poids de C5 pour une essence manuelle."""
    response = client.post(
        "/api/recommandations",
        json={
            "id_vehicule": 1,
            "description": "La voiture perd de la puissance et les vitesses passent mal",
            "carburant": "essence",
            "boite": "manuelle",
            "symptomes": [3, 10],
        },
    )

    assert response.status_code == 200

    resultats = response.json()["heuristique"]["resultats"]

    assert len(resultats) == 5

    for resultat in resultats:
        assert resultat["explication"]["cause"] == "C5"
        assert resultat["score"] == 0.45

        contributions = resultat["explication"]["contributions"] # verifie nouveaux poids bien utilisés par API

        assert contributions == [
            {"id_symptome": 3, "points": 32.2},
            {"id_symptome": 10, "points": 65.2},
        ]


def test_recommandation_s7_c2_et_c11():
    """S7 doit proposer C2 et C11, avec C2 avant C11."""
    response = client.post(
        "/api/recommandations",
        json={
            "id_vehicule": 1,
            "description": "La voiture vibre dans le volant",
            "carburant": "essence",
            "boite": "manuelle",
            "symptomes": [7],
        },
    )

    assert response.status_code == 200

    resultats = response.json()["heuristique"]["resultats"]

    causes = [resultat["explication"]["cause"] for resultat in resultats]

    assert "C2" in causes
    assert "C11" in causes
    assert causes.index("C2") < causes.index("C11")
    data = response.json() # reponse sous format dico

    assert "id_requete" in data
    assert "heuristique" in data
    assert "embeddings" in data

    assert "temps_calcul_ms" in data["heuristique"]
    assert "nb_resultats" in data["heuristique"]
    assert "resultats" in data["heuristique"]
