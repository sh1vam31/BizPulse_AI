import pytest
from app.models.auth import UserRole


def test_register_new_user_and_organization(client):
    payload = {
        "name": "Jane Doe",
        "email": "jane@techcorp.io",
        "password": "SecurePassword123!",
        "role": UserRole.BUSINESS_OWNER.value,
        "organization_name": "TechCorp Global",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "jane@techcorp.io"
    assert data["user"]["role"] == UserRole.BUSINESS_OWNER.value
    assert data["user"]["organization_id"] is not None


def test_register_duplicate_email_fails(client, test_admin_user):
    payload = {
        "name": "Another Admin",
        "email": test_admin_user.email,
        "password": "AnotherPassword123!",
        "role": UserRole.ADMIN.value,
        "organization_name": "New Org",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_login_success(client, test_admin_user):
    payload = {
        "email": "admin@acme.com",
        "password": "AdminSecret123!",
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "admin@acme.com"


def test_login_invalid_password(client, test_admin_user):
    payload = {
        "email": "admin@acme.com",
        "password": "IncorrectPassword123!",
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_refresh_token_endpoint(client, test_admin_user):
    # First login to obtain tokens
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@acme.com", "password": "AdminSecret123!"},
    )
    refresh_token = login_res.json()["refresh_token"]

    # Refresh
    refresh_res = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_res.status_code == 200
    data = refresh_res.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_get_me_unauthenticated(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_get_me_authenticated(client, admin_auth_headers, test_admin_user):
    response = client.get("/api/v1/auth/me", headers=admin_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_admin_user.email
    assert data["role"] == UserRole.ADMIN.value


def test_rbac_role_restriction(client, admin_auth_headers, viewer_auth_headers):
    from fastapi import Depends
    from app.api.deps import require_roles
    from app.main import app

    @app.get("/api/v1/test-admin-only", dependencies=[Depends(require_roles([UserRole.ADMIN]))])
    def admin_only_endpoint():
        return {"status": "success", "access": "admin"}

    # Admin access should succeed (200)
    admin_res = client.get("/api/v1/test-admin-only", headers=admin_auth_headers)
    assert admin_res.status_code == 200
    assert admin_res.json()["access"] == "admin"

    # Viewer access should fail with 403 Forbidden
    viewer_res = client.get("/api/v1/test-admin-only", headers=viewer_auth_headers)
    assert viewer_res.status_code == 403
    assert "Access forbidden" in viewer_res.json()["detail"]
