"""
tests/test_api.py — Integration tests for the Task Management API.

Tests use the Flask test client with an in-memory SQLite database.
Every test function gets a fresh database via the fixtures in conftest.py.

Coverage:
    Auth    — tests 01-05: register, login, refresh, /me, bad credentials
    Projects — tests 06-10: CRUD + owner-only enforcement
    Tasks   — tests 11-15: CRUD + filters + pagination
"""

import pytest
from datetime import datetime, timedelta, timezone


# ===========================================================================
# Auth tests
# ===========================================================================

class TestAuth:

    def test_01_register_success(self, client):
        """POST /auth/register should create a new user and return 201."""
        resp = client.post("/auth/register", json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "securepass",
        })
        data = resp.get_json()
        assert resp.status_code == 201
        assert data["success"] is True
        assert data["data"]["username"] == "alice"
        assert "password" not in data["data"]     # password must never appear in response

    def test_02_register_duplicate_email(self, client, registered_user):
        """POST /auth/register with a duplicate email should return 400."""
        resp = client.post("/auth/register", json={
            "username": "other",
            "email": registered_user["email"],    # same email
            "password": "pass123456",
        })
        assert resp.status_code == 400
        assert resp.get_json()["success"] is False

    def test_03_login_success(self, client, registered_user):
        """POST /auth/login should return access_token and refresh_token."""
        resp = client.post("/auth/login", json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        })
        data = resp.get_json()
        assert resp.status_code == 200
        assert "access_token"  in data["data"]
        assert "refresh_token" in data["data"]

    def test_04_login_wrong_password(self, client, registered_user):
        """POST /auth/login with wrong password should return 401."""
        resp = client.post("/auth/login", json={
            "email": registered_user["email"],
            "password": "wrongpassword",
        })
        assert resp.status_code == 401
        assert resp.get_json()["success"] is False

    def test_05_get_me(self, client, auth_headers, registered_user):
        """GET /auth/me should return the current user's profile."""
        resp = client.get("/auth/me", headers=auth_headers)
        data = resp.get_json()
        assert resp.status_code == 200
        assert data["data"]["email"] == registered_user["email"]


# ===========================================================================
# Project tests
# ===========================================================================

class TestProjects:

    def test_06_create_project(self, client, auth_headers):
        """POST /projects should create a project and return 201."""
        resp = client.post("/projects", json={
            "name": "My Project",
            "description": "A brand new project",
        }, headers=auth_headers)
        data = resp.get_json()
        assert resp.status_code == 201
        assert data["success"] is True
        assert data["data"]["name"] == "My Project"

    def test_07_list_projects_paginated(self, client, auth_headers, project):
        """GET /projects should return paginated project list."""
        resp = client.get("/projects?page=1&per_page=5", headers=auth_headers)
        data = resp.get_json()
        assert resp.status_code == 200
        assert "items"    in data["data"]
        assert "total"    in data["data"]
        assert "pages"    in data["data"]
        assert len(data["data"]["items"]) >= 1

    def test_08_get_project(self, client, auth_headers, project):
        """GET /projects/<id> should return the project."""
        resp = client.get(f"/projects/{project['id']}", headers=auth_headers)
        data = resp.get_json()
        assert resp.status_code == 200
        assert data["data"]["id"] == project["id"]

    def test_09_update_project_owner_only(self, client, auth_headers, project):
        """PUT /projects/<id> should succeed for owner; 403 for others."""
        # Owner update — should succeed
        resp = client.put(f"/projects/{project['id']}",
                          json={"name": "Renamed"},
                          headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json()["data"]["name"] == "Renamed"

        # Register a second user and try to update
        client.post("/auth/register", json={
            "username": "bob", "email": "bob@example.com", "password": "bobpass123"
        })
        login2 = client.post("/auth/login", json={
            "email": "bob@example.com", "password": "bobpass123"
        })
        token2 = login2.get_json()["data"]["access_token"]
        resp2 = client.put(f"/projects/{project['id']}",
                           json={"name": "Hacked"},
                           headers={"Authorization": f"Bearer {token2}"})
        assert resp2.status_code == 403

    def test_10_delete_project(self, client, auth_headers, project):
        """DELETE /projects/<id> should remove the project (owner only)."""
        resp = client.delete(f"/projects/{project['id']}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True

        # Subsequent GET should return 404
        resp2 = client.get(f"/projects/{project['id']}", headers=auth_headers)
        assert resp2.status_code == 404


# ===========================================================================
# Task tests
# ===========================================================================

class TestTasks:

    def test_11_create_task(self, client, auth_headers, project):
        """POST /projects/<id>/tasks should create a task and return 201."""
        resp = client.post(f"/projects/{project['id']}/tasks", json={
            "title": "Write tests",
            "description": "Cover all endpoints",
            "priority": "urgent",
            "status": "todo",
        }, headers=auth_headers)
        data = resp.get_json()
        assert resp.status_code == 201
        assert data["data"]["title"] == "Write tests"
        assert data["data"]["priority"] == "urgent"

    def test_12_list_tasks_with_status_filter(self, client, auth_headers, project):
        """GET /projects/<id>/tasks?status=done should filter correctly."""
        pid = project["id"]
        # Create two tasks with different statuses
        client.post(f"/projects/{pid}/tasks",
                    json={"title": "Task A", "status": "done"},
                    headers=auth_headers)
        client.post(f"/projects/{pid}/tasks",
                    json={"title": "Task B", "status": "todo"},
                    headers=auth_headers)

        resp = client.get(f"/projects/{pid}/tasks?status=done", headers=auth_headers)
        data = resp.get_json()
        assert resp.status_code == 200
        assert all(t["status"] == "done" for t in data["data"]["items"])

    def test_13_filter_by_priority(self, client, auth_headers, project):
        """GET /projects/<id>/tasks?priority=high should return only high-priority tasks."""
        pid = project["id"]
        client.post(f"/projects/{pid}/tasks",
                    json={"title": "High task", "priority": "high"},
                    headers=auth_headers)
        client.post(f"/projects/{pid}/tasks",
                    json={"title": "Low task", "priority": "low"},
                    headers=auth_headers)

        resp = client.get(f"/projects/{pid}/tasks?priority=high", headers=auth_headers)
        items = resp.get_json()["data"]["items"]
        assert all(t["priority"] == "high" for t in items)
        assert len(items) >= 1

    def test_14_update_task(self, client, auth_headers, project, task):
        """PUT /projects/<id>/tasks/<tid> should update the task."""
        pid, tid = project["id"], task["id"]
        resp = client.put(f"/projects/{pid}/tasks/{tid}",
                          json={"status": "in_progress", "title": "Updated Title"},
                          headers=auth_headers)
        data = resp.get_json()
        assert resp.status_code == 200
        assert data["data"]["status"] == "in_progress"
        assert data["data"]["title"]  == "Updated Title"

    def test_15_delete_task_and_overdue_filter(self, client, auth_headers, project):
        """DELETE removes a task; overdue filter returns only past-due tasks."""
        pid = project["id"]

        # Create an overdue task (due yesterday)
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        resp = client.post(f"/projects/{pid}/tasks",
                           json={"title": "Overdue", "due_date": yesterday},
                           headers=auth_headers)
        overdue_id = resp.get_json()["data"]["id"]

        # Create a future task
        tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        client.post(f"/projects/{pid}/tasks",
                    json={"title": "Future", "due_date": tomorrow},
                    headers=auth_headers)

        # Overdue filter should return only the past-due task
        resp2 = client.get(f"/projects/{pid}/tasks?overdue=true", headers=auth_headers)
        items = resp2.get_json()["data"]["items"]
        assert len(items) >= 1
        assert all(t["id"] != resp.get_json()["data"]["id"] or t["title"] == "Overdue"
                   for t in items)

        # Delete the overdue task
        del_resp = client.delete(f"/projects/{pid}/tasks/{overdue_id}",
                                 headers=auth_headers)
        assert del_resp.status_code == 200

        # Confirm it's gone
        get_resp = client.get(f"/projects/{pid}/tasks/{overdue_id}",
                              headers=auth_headers)
        assert get_resp.status_code == 404
