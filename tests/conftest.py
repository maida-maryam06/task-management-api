"""
tests/conftest.py — Shared pytest fixtures.

All fixtures use the "testing" config (in-memory SQLite) so they are
isolated, fast, and leave no files on disk.
"""

import pytest
from app import create_app, db as _db


@pytest.fixture(scope="function")
def app():
    """Create a fresh app + in-memory database for each test."""
    app = create_app("testing")
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture
def registered_user(client):
    """Register and return a test user's credentials."""
    payload = {"username": "testuser", "email": "test@example.com", "password": "password123"}
    client.post("/auth/register", json=payload)
    return payload


@pytest.fixture
def auth_headers(client, registered_user):
    """Return Authorization headers for the registered test user."""
    resp = client.post("/auth/login", json={
        "email": registered_user["email"],
        "password": registered_user["password"],
    })
    token = resp.get_json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def project(client, auth_headers):
    """Create and return a test project."""
    resp = client.post("/projects", json={"name": "Test Project", "description": "A test"},
                       headers=auth_headers)
    return resp.get_json()["data"]


@pytest.fixture
def task(client, auth_headers, project):
    """Create and return a test task inside the test project."""
    resp = client.post(
        f"/projects/{project['id']}/tasks",
        json={"title": "Test Task", "description": "Do something", "priority": "high"},
        headers=auth_headers,
    )
    return resp.get_json()["data"]
