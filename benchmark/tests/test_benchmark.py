import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

from benchmark.evaluer_precision import calculer_scores, evaluer, lire_jeu, normaliser, rang_attendu
from benchmark.mesurer_temps_reponse import mesurer, percentile, resumer

JEU = Path(__file__).resolve().parents[2] / "data" / "evaluation" / "jeu_test.csv"


class FausseApi(BaseHTTPRequestHandler):
    """Petite API qui respecte docs/contrat_api.md, pour tester sans la vraie API."""

    def _repondre(self, corps):
        donnees = json.dumps(corps).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(donnees)

    def do_GET(self):
        if self.path.startswith("/api/symptomes"):
            self._repondre([{"id_symptome": 4, "libelle": "Bruit au freinage"}])
        elif self.path.startswith("/api/vehicules"):
            self._repondre([{"id_vehicule": 1}] if "CORSA" in self.path else [])
        else:
            self.send_error(404)

    def do_POST(self):
        self.rfile.read(int(self.headers["Content-Length"]))
        resultat = {"rang": 1, "titre": "Usure des plaquettes de frein"}
        self._repondre(
            {
                "heuristique": {"temps_calcul_ms": 10.0, "nb_resultats": 1, "resultats": [resultat]},
                "embeddings": {"temps_calcul_ms": None, "nb_resultats": 0, "resultats": []},
            }
        )

    def log_message(self, *args):
        pass


@pytest.fixture(scope="module")
def url_api():
    serveur = HTTPServer(("127.0.0.1", 0), FausseApi)
    fil = threading.Thread(target=serveur.serve_forever, daemon=True)
    fil.start()
    yield f"http://127.0.0.1:{serveur.server_port}"
    serveur.shutdown()


def test_percentile():
    assert percentile([10], 0.95) == 10
    assert percentile([1, 2, 3, 4], 0.5) == 2.5
    assert percentile([0, 100], 0.95) == pytest.approx(95)


def test_resumer():
    r = resumer([10.0, 20.0, 30.0])
    assert (r["n"], r["min_ms"], r["max_ms"], r["moyen_ms"], r["mediane_ms"]) == (3, 10.0, 30.0, 20.0, 20.0)


def test_mesurer_lit_le_temps_serveur(url_api):
    total, serveur = mesurer(url_api, {"id_vehicule": 1, "description": "test"}, n=3, echauffement=1)
    assert len(total) == 3
    assert serveur["heuristique"] == [10.0, 10.0, 10.0]
    assert serveur["embeddings"] == []  # temps_calcul_ms est null en v0.1 : on l'ignore


def test_normaliser():
    assert normaliser("  Étrier  de FREIN ") == "etrier de frein"


def test_rang_attendu():
    resultats = [{"rang": 1, "titre": "Autre"}, {"rang": 2, "titre": "Étrier de frein grippé"}]
    assert rang_attendu(resultats, ["etrier de frein grippe"]) == 2
    assert rang_attendu(resultats, ["Inconnu"]) is None


def test_calculer_scores():
    s = calculer_scores([1, 3, None, 2])
    assert s["top1"] == 0.25
    assert s["top3"] == 0.75
    assert s["mrr"] == pytest.approx((1 + 1 / 3 + 1 / 2) / 4)


def test_jeu_de_test_est_bien_forme():
    cas = lire_jeu(JEU)
    assert len(cas) >= 1
    assert len({c["id_cas"] for c in cas}) == len(cas)  # pas d'identifiant en double
    assert all(c["description"].strip() and c["titres_attendus"].strip() for c in cas)


def test_evaluer_avec_fausse_api(url_api):
    base = {"annee": "", "carburant": "", "boite": "", "symptomes": "", "description": "test"}
    cas = [
        {**base, "id_cas": "A", "marque": "OPEL", "modele": "CORSA", "annee": "2019",
         "symptomes": "Bruit au freinage", "titres_attendus": "Usure des plaquettes de frein"},
        {**base, "id_cas": "B", "marque": "INCONNU", "modele": "X", "titres_attendus": "Peu importe"},
    ]
    scores, ignores, echecs = evaluer(url_api, cas)
    assert scores["heuristique"]["top1"] == 1.0
    assert "embeddings" not in scores  # aucun résultat : approche non évaluée
    assert [i[0] for i in ignores] == ["B"]
    assert echecs == []
