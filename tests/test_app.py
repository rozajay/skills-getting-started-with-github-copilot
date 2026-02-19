from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture(autouse=True)
def reset_activities_state():
    original_activities = deepcopy(app_module.activities)
    yield
    app_module.activities = original_activities


@pytest.fixture
def client():
    return TestClient(app_module.app)


def test_root_redirects_to_static_index(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code in (302, 307)
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_data(client):
    response = client.get("/activities")

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, dict)
    assert "Basketball Team" in payload
    assert isinstance(payload["Basketball Team"]["participants"], list)


def test_signup_success_adds_participant(client):
    email = "new.student@mergington.edu"

    response = client.post(f"/activities/Basketball%20Team/signup?email={email}")

    assert response.status_code == 200
    assert email in app_module.activities["Basketball Team"]["participants"]


def test_signup_fails_for_duplicate_participant(client):
    email = app_module.activities["Basketball Team"]["participants"][0]

    response = client.post(f"/activities/Basketball%20Team/signup?email={email}")

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_fails_when_activity_is_full(client):
    app_module.activities["Tiny Club"] = {
        "description": "Small group",
        "schedule": "Mondays",
        "max_participants": 1,
        "participants": ["already@mergington.edu"],
    }

    response = client.post("/activities/Tiny%20Club/signup?email=another@mergington.edu")

    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"


def test_unreg_success_removes_participant(client):
    email = app_module.activities["Soccer Club"]["participants"][0]

    response = client.delete(f"/activities/Soccer%20Club/signup?email={email}")

    assert response.status_code == 200
    assert email not in app_module.activities["Soccer Club"]["participants"]


def test_unreg_fails_for_missing_activity(client):
    response = client.delete("/activities/NotARealClub/signup?email=user@mergington.edu")

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unreg_fails_when_participant_not_registered(client):
    response = client.delete("/activities/Drama%20Club/signup?email=not.registered@mergington.edu")

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
