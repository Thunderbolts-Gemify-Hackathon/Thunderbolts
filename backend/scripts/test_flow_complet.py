from __future__ import annotations

import asyncio

import httpx

from backend.data.seed import seed
from backend.database import init_db
from backend.main import app
from backend.scripts.flow_setup import prepare_demo_repas
from backend.scripts.flow_steps import assert_market_rules, assert_planning_empty, complete_onboarding


async def run_flow() -> dict:
    init_db()
    seed()
    results: dict = {}

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        profil_id, headers = await complete_onboarding(client)
        results["profil_id"] = profil_id
        await assert_planning_empty(client, profil_id, headers)

        ids = prepare_demo_repas(profil_id)
        results.update(ids)

        r = await client.get(f"/stock/{profil_id}", headers=headers)
        r.raise_for_status()
        avant = {x["ingredient_id"]: x["quantite_disponible"] for x in r.json()}

        r = await client.post(f"/planning/{ids['repas_id']}/valider", headers=headers)
        r.raise_for_status()
        assert r.json()["statut"] == "consomme"

        r = await client.get(f"/stock/{profil_id}", headers=headers)
        r.raise_for_status()
        apres = {x["ingredient_id"]: x["quantite_disponible"] for x in r.json()}
        assert apres[ids["riz_id"]] < avant[ids["riz_id"]]

        r = await client.get(f"/planning/{ids['planning_id']}/courses", headers=headers)
        r.raise_for_status()
        results["courses_statuts"] = {i["ingredient"]["nom"]: i["statut"] for i in r.json()}
        assert "bredes mafana" in results["courses_statuts"]

        results["market_premier"] = await assert_market_rules(client, ids["bredes_id"])
        results["stock_avant"] = avant
        results["stock_apres"] = apres

    print("Flow complet OK")
    return results


def main() -> None:
    asyncio.run(run_flow())


if __name__ == "__main__":
    main()
