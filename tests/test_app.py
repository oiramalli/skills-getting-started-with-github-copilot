import copy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities_state():
    # Keep tests isolated because endpoints mutate in-memory global state.
    original_state = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(copy.deepcopy(original_state))


def test_root_redirects_to_static_index():
    # Arrange
    url = "/"

    # Act
    response = client.get(url, follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_expected_shape():
    # Arrange
    url = "/activities"

    # Act
    response = client.get(url)
    payload = response.json()

    # Assert
    assert response.status_code == 200
    assert "Chess Club" in payload
    assert "description" in payload["Chess Club"]
    assert "schedule" in payload["Chess Club"]
    assert "max_participants" in payload["Chess Club"]
    assert "participants" in payload["Chess Club"]


def test_signup_adds_participant_successfully():
    # Arrange
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"
    before_count = len(activities[activity_name]["participants"])

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})
    after_count = len(activities[activity_name]["participants"])

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for {activity_name}"
    assert email in activities[activity_name]["participants"]
    assert after_count == before_count + 1


def test_signup_rejects_unknown_activity():
    # Arrange
    activity_name = "Unknown Activity"
    email = "student@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_rejects_duplicate_email():
    # Arrange
    activity_name = "Programming Class"
    email = "emma@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_rejects_when_activity_is_full():
    # Arrange
    activity_name = "Full Activity"
    activities[activity_name] = {
        "description": "Already full",
        "schedule": "Fridays, 1:00 PM - 2:00 PM",
        "max_participants": 1,
        "participants": ["existing@mergington.edu"],
    }
    email = "another@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"


def test_unregister_removes_participant_successfully():
    # Arrange
    activity_name = "Art Club"
    email = "mia@mergington.edu"
    before_count = len(activities[activity_name]["participants"])

    # Act
    response = client.delete(f"/activities/{activity_name}/signup", params={"email": email})
    after_count = len(activities[activity_name]["participants"])

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Unregistered {email} from {activity_name}"
    assert email not in activities[activity_name]["participants"]
    assert after_count == before_count - 1


def test_unregister_rejects_unknown_activity():
    # Arrange
    activity_name = "Unknown Activity"
    email = "student@mergington.edu"

    # Act
    response = client.delete(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_rejects_email_not_enrolled():
    # Arrange
    activity_name = "Debate Team"
    email = "notenrolled@mergington.edu"

    # Act
    response = client.delete(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student not signed up for this activity"