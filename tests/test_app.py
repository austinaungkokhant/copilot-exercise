import pytest
from fastapi.testclient import TestClient

from src import app as application


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(
        application,
        "activities",
        {
            "Test Activity": {
                "description": "A test activity",
                "schedule": "Mondays",
                "max_participants": 10,
                "participants": ["existing@mergington.edu"],
            }
        },
    )
    return TestClient(application.app)


def test_get_activities_returns_activities_without_caching(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json()["Test Activity"]["participants"] == [
        "existing@mergington.edu"
    ]
    assert response.headers["cache-control"] == "no-store"


def test_signup_adds_participant(client):
    response = client.post(
        "/activities/Test Activity/signup",
        params={"email": "new@mergington.edu"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Signed up new@mergington.edu for Test Activity"
    }
    assert "new@mergington.edu" in client.get("/activities").json()[
        "Test Activity"
    ]["participants"]


def test_signup_rejects_duplicate_participant(client):
    response = client.post(
        "/activities/Test Activity/signup",
        params={"email": "existing@mergington.edu"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_rejects_unknown_activity(client):
    response = client.post(
        "/activities/Unknown Activity/signup",
        params={"email": "new@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_participant(client):
    response = client.delete(
        "/activities/Test Activity/signup",
        params={"email": "existing@mergington.edu"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Removed existing@mergington.edu from Test Activity"
    }
    assert client.get("/activities").json()["Test Activity"]["participants"] == []


def test_remove_participant_rejects_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown Activity/signup",
        params={"email": "existing@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_participant_rejects_unregistered_student(client):
    response = client.delete(
        "/activities/Test Activity/signup",
        params={"email": "not-registered@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
