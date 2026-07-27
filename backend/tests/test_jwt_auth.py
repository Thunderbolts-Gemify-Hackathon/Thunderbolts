"""JWT login / refresh + Bearer auth."""

from backend.tests.test_patch_onboarding import _creer_utilisateur


def test_login_jwt_and_refresh(client):
    user = _creer_utilisateur(client, "jwt-user@example.com")

    # login classique toujours OK
    classic = client.post(
        "/utilisateurs/login",
        json={"email": "jwt-user@example.com", "mot_de_passe": "Passw0rd!"},
    )
    assert classic.status_code == 200
    assert classic.json()["api_token"] == user["api_token"]

    jwt_login = client.post(
        "/utilisateurs/login-jwt",
        json={"email": "jwt-user@example.com", "mot_de_passe": "Passw0rd!"},
    )
    assert jwt_login.status_code == 200
    body = jwt_login.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["api_token"] == user["api_token"]
    assert body["token_type"] == "bearer"

    me = client.get(
        f"/utilisateurs/{user['id']}",
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["id"] == user["id"]

    refreshed = client.post(
        "/utilisateurs/refresh",
        json={"refresh_token": body["refresh_token"]},
    )
    assert refreshed.status_code == 200
    assert refreshed.json()["access_token"]
    assert refreshed.json()["api_token"] == user["api_token"]


def test_refresh_rejects_access_token(client):
    user = _creer_utilisateur(client, "jwt-bad@example.com")
    jwt_login = client.post(
        "/utilisateurs/login-jwt",
        json={"email": "jwt-bad@example.com", "mot_de_passe": "Passw0rd!"},
    )
    access = jwt_login.json()["access_token"]
    r = client.post("/utilisateurs/refresh", json={"refresh_token": access})
    assert r.status_code == 401
