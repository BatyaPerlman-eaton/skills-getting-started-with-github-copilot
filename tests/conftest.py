import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def app_fixture():
    """Provide the FastAPI app instance for testing."""
    return app


@pytest.fixture
def client(app_fixture):
    """Create a TestClient for making HTTP requests to the app."""
    return TestClient(app_fixture)


@pytest.fixture(autouse=True)
def reset_activities():
    """
    Reset activities to their initial state before each test.
    This fixture runs automatically ('autouse=True') to ensure test isolation.
    """
    # Capture the initial state (deep copy of each activity)
    initial_activities = {}
    for activity_name, activity_data in activities.items():
        initial_activities[activity_name] = {
            "description": activity_data["description"],
            "schedule": activity_data["schedule"],
            "max_participants": activity_data["max_participants"],
            "participants": activity_data["participants"].copy(),
        }

    yield  # Test runs here

    # Restore activities to initial state after the test
    for activity_name in activities:
        activities[activity_name]["participants"] = initial_activities[
            activity_name
        ]["participants"].copy()
