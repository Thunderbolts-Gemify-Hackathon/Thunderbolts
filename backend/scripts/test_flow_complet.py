from __future__ import annotations

import asyncio
from datetime import date

import httpx
from sqlalchemy.orm import joinedload

from backend.data.seed import seed
from backend.database import SessionLocal, init_db
from backend.main import app
from backend.models.planning import Planning, RepasPlanifie
from backend.models.recette import Recette, RecetteIngredient
from backend.models.stock import IngredientStock, Stock


def _log(step: str, r: httpx.Response) -> None:
    print(f"[{r.status_code}] {step}")


def _prepare(profil_id: str) -> dict[str, str]:
    db = SessionLocal()
    try:
        recette = (
            db.query(Recette)
            .options(joinedload(Recette.ingredients).joinedload(RecetteIngredient.ingredient))
            .filter(Recette.nom == "romazava")
            .one()
        )
        by_nom = {l.ingredient.nom: l.ingredient for l in recette.ingredients}

        stock = Stock(profil_id=profil_id, lieu_stockage="cuisine")
        db.add(stock)
        db.flush()
        qty = {
            "riz": 500.0,
            "poulet": 250.0,
            "bredes mafana": 50.0,
            "tomate": 200.0,
            "oignon": 200.0,
            "gingembre": 50.0,
        }
        for ligne in recette.ingredients:
            db.add(
                IngredientStock(
                    stock_id=stock.id,
                    ingredient_id=ligne.ingredient_id,
                    quantite_disponible=qty.get(ligne.ingredient.nom, 200.0),
                    unite=ligne.unite,
                )
            )

        planning = Planning(profil_id=profil_id, periode="semaine", date_debut=date.today())
        db.add(planning)
        db.flush()
        repas = RepasPlanifie(
            planning_id=planning.id,
            recette_id=recette.id,
            jour=date.today(),
            type_repas="dejeuner",
        )
        db.add(repas)
        db.commit()
        return {
            "planning_id": planning.id,
            "repas_id": repas.id,
            "riz_id": by_nom["riz"].id,
            "poulet_id": by_nom["poulet"].id,
            "bredes_id": by_nom["bredes mafana"].id,
        }
    finally:
        db.close()


async def run_flow() -> dict:
    init_db()
    seed()
    results: dict = {}

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        r = await client.post(
            "/onboarding/profil",
            json={
                "age": 27,
                "sexe": "homme",
                "poids": 72.0,
                "taille": 175.0,
                "niveau_activite": "modere",
                "objectif": "maintien",
            },
        )
        _log("profil", r)
        r.raise_for_status()
        profil_id = r.json()["id"]
        results["profil_id"] = profil_id

        for path, body in [
            (f"/onboarding/profil/{profil_id}/foyer", {"nombre_personnes": 2, "membres": [{"age_approx": 25}]}),
            (f"/onboarding/profil/{profil_id}/preferences", {"tabous": ["porc"], "allergies": [], "aliments_detestes": [], "regime_specifique": "sans_porc"}),
            (f"/onboarding/profil/{profil_id}/budget", {"montant": 200000, "periode": "semaine"}),
            (f"/onboarding/profil/{profil_id}/localisation", {"latitude": -18.9102, "longitude": 47.5256, "quartier": "Analakely", "saison": "hiver_sec"}),
        ]:
            r = await client.post(path, json=body)
            _log(path.split("/")[-1], r)
            r.raise_for_status()

        r = await client.get(
            f"/planning/{profil_id}",
            params={"periode": "semaine", "date_debut": date.today().isoformat()},
        )
        _log("planning vide", r)
        assert r.status_code == 404

        ids = _prepare(profil_id)
        results.update(ids)

        r = await client.get(f"/stock/{profil_id}")
        r.raise_for_status()
        avant = {x["ingredient_id"]: x["quantite_disponible"] for x in r.json()}

        r = await client.post(f"/planning/{ids['repas_id']}/valider")
        _log("valider", r)
        r.raise_for_status()
        assert r.json()["statut"] == "consomme"

        r = await client.get(f"/stock/{profil_id}")
        r.raise_for_status()
        apres = {x["ingredient_id"]: x["quantite_disponible"] for x in r.json()}
        assert apres[ids["riz_id"]] < avant[ids["riz_id"]]
        results["stock_avant"] = avant
        results["stock_apres"] = apres

        r = await client.get(f"/planning/{ids['planning_id']}/courses")
        _log("courses", r)
        r.raise_for_status()
        results["courses_statuts"] = {i["ingredient"]["nom"]: i["statut"] for i in r.json()}
        assert "bredes mafana" in results["courses_statuts"]

        r = await client.get(
            "/market/nearby",
            params={"ingredient_id": ids["bredes_id"], "lat": -18.9102, "lon": 47.5256, "rayon_km": 15},
        )
        _log("market", r)
        r.raise_for_status()
        matches = r.json()
        assert matches
        for m in matches:
            if m.get("itineraire") and m["itineraire"]["niveau_securite"] == "a_eviter":
                assert m["deprioritise"] is True
        normal = [m for m in matches if not m["deprioritise"]]
        assert [m["prix"] for m in normal] == sorted(m["prix"] for m in normal)
        results["market_premier"] = {
            "nom": matches[0]["point_de_vente"]["nom"],
            "prix": matches[0]["prix"],
            "deprioritise": matches[0]["deprioritise"],
        }

    print("Flow complet OK")
    return results


def main() -> None:
    asyncio.run(run_flow())


if __name__ == "__main__":
    main()
