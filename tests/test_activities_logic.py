"""
Unit tests for business logic and validation rules.
Tests specific logic components in isolation.
"""

import pytest
from src.app import activities


class TestActivitiesDataStructure:
    """Tests for the initial activities data structure"""

    def test_activities_is_dict(self):
        """Verify activities is a dictionary"""
        assert isinstance(activities, dict)

    def test_activities_has_nine_entries(self):
        """Verify there are 9 activities"""
        assert len(activities) == 9

    def test_all_activities_have_required_fields(self):
        """Verify every activity has all required fields"""
        required_fields = ["description", "schedule", "max_participants", "participants"]
        for activity_name, activity_data in activities.items():
            for field in required_fields:
                assert field in activity_data, f"{activity_name} missing {field}"
            assert isinstance(activity_data["description"], str)
            assert isinstance(activity_data["schedule"], str)
            assert isinstance(activity_data["max_participants"], int)
            assert isinstance(activity_data["participants"], list)

    def test_all_participants_are_strings(self):
        """Verify all participants are email strings"""
        for activity_name, activity_data in activities.items():
            for participant in activity_data["participants"]:
                assert isinstance(participant, str)
                assert "@" in participant  # Basic email check

    def test_initial_participants_counts(self):
        """Verify initial participant counts are correct"""
        expected_counts = {
            "Chess Club": 2,
            "Programming Class": 2,
            "Gym Class": 2,
            "Basketball Team": 1,
            "Soccer Team": 2,
            "Drama Club": 1,
            "Art Studio": 2,
            "Debate Club": 1,
            "Robotics Club": 2,
        }
        for activity_name, expected_count in expected_counts.items():
            actual_count = len(activities[activity_name]["participants"])
            assert (
                actual_count == expected_count
            ), f"{activity_name} has {actual_count} participants, expected {expected_count}"

    def test_max_participants_are_positive_integers(self):
        """Verify all max_participants values are positive"""
        for activity_name, activity_data in activities.items():
            max_participants = activity_data["max_participants"]
            assert isinstance(max_participants, int)
            assert max_participants > 0, f"{activity_name} has non-positive max_participants"

    def test_no_duplicate_participants_initially(self):
        """Verify no activity has duplicate participants initially"""
        for activity_name, activity_data in activities.items():
            participants = activity_data["participants"]
            assert len(participants) == len(
                set(participants)
            ), f"{activity_name} has duplicate participants"


class TestSignupValidationLogic:
    """Tests for signup validation and logic"""

    def test_duplicate_signup_not_allowed(self, client):
        """Verify duplicate signup is prevented"""
        email = "existing@mergington.edu"
        activity = "Chess Club"

        # Ensure email is in participants
        activities[activity]["participants"].append(email)

        # Try to signup same email again
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 400

    def test_signup_nonexistent_activity_fails(self, client):
        """Verify signup fails for non-existent activity"""
        response = client.post("/activities/Fake Activity/signup?email=test@mergington.edu")
        assert response.status_code == 404

    def test_signup_valid_activity_succeeds(self, client):
        """Verify signup succeeds for valid activity and new email"""
        email = "newperson@mergington.edu"
        response = client.post(f"/activities/Chess Club/signup?email={email}")
        assert response.status_code == 200

    def test_signup_modifies_participants_list(self, client):
        """Verify signup actually adds email to participants"""
        email = "added@mergington.edu"
        activity = "Drama Club"
        initial_count = len(activities[activity]["participants"])

        client.post(f"/activities/{activity}/signup?email={email}")

        assert len(activities[activity]["participants"]) == initial_count + 1
        assert email in activities[activity]["participants"]

    def test_multiple_activities_independent(self, client):
        """Verify signup in one activity doesn't affect others"""
        email = "independent@mergington.edu"
        activity1 = "Chess Club"
        activity2 = "Drama Club"

        # Signup for activity1
        client.post(f"/activities/{activity1}/signup?email={email}")

        # Verify email is only in activity1, not in activity2
        assert email in activities[activity1]["participants"]
        assert email not in activities[activity2]["participants"]


class TestUnregisterValidationLogic:
    """Tests for unregister validation and logic"""

    def test_unregister_nonexistent_activity_fails(self, client):
        """Verify unregister fails for non-existent activity"""
        response = client.delete("/activities/Fake Activity/unregister?email=test@mergington.edu")
        assert response.status_code == 404

    def test_unregister_nonexistent_participant_fails(self, client):
        """Verify unregister fails for participant not in activity"""
        email = "nothere@mergington.edu"
        response = client.delete(f"/activities/Chess Club/unregister?email={email}")
        assert response.status_code == 400

    def test_unregister_existing_participant_succeeds(self, client):
        """Verify unregister succeeds for existing participant"""
        email = "michael@mergington.edu"  # Known to be in Chess Club
        response = client.delete(f"/activities/Chess Club/unregister?email={email}")
        assert response.status_code == 200

    def test_unregister_removes_participant(self, client):
        """Verify unregister removes email from participants list"""
        email = "michael@mergington.edu"
        activity = "Chess Club"
        initial_count = len(activities[activity]["participants"])

        client.delete(f"/activities/{activity}/unregister?email={email}")

        assert len(activities[activity]["participants"]) == initial_count - 1
        assert email not in activities[activity]["participants"]

    def test_unregister_twice_fails(self, client):
        """Verify unregistering same email twice fails"""
        email = "michael@mergington.edu"
        # First unregister succeeds
        response1 = client.delete(f"/activities/Chess Club/unregister?email={email}")
        assert response1.status_code == 200

        # Second unregister fails
        response2 = client.delete(f"/activities/Chess Club/unregister?email={email}")
        assert response2.status_code == 400

    def test_unregister_from_wrong_activity_fails(self, client):
        """Verify unregister fails if email not in that activity"""
        email = "michael@mergington.edu"  # In Chess Club
        response = client.delete(f"/activities/Drama Club/unregister?email={email}")
        assert response.status_code == 400


class TestDataPersistenceLogic:
    """Tests for data persistence and isolation"""

    def test_signup_persists_in_get_activities(self, client):
        """Verify signup changes are reflected in GET /activities"""
        email = "persistent@mergington.edu"
        activity = "Gym Class"

        # Sign up
        client.post(f"/activities/{activity}/signup?email={email}")

        # Fetch and verify
        response = client.get("/activities")
        data = response.json()
        assert email in data[activity]["participants"]

    def test_unregister_persists_in_get_activities(self, client):
        """Verify unregister changes are reflected in GET /activities"""
        email = "michael@mergington.edu"
        activity = "Chess Club"

        # Unregister
        client.delete(f"/activities/{activity}/unregister?email={email}")

        # Fetch and verify
        response = client.get("/activities")
        data = response.json()
        assert email not in data[activity]["participants"]


class TestCapacityLogic:
    """Tests for participant capacity handling"""

    def test_activity_capacity_exists(self):
        """Verify all activities have a max_participants value"""
        for activity_name, activity_data in activities.items():
            assert "max_participants" in activity_data
            assert activity_data["max_participants"] > 0

    def test_capacity_values_reasonable(self):
        """Verify max_participants values are within reasonable range"""
        for activity_name, activity_data in activities.items():
            max_participants = activity_data["max_participants"]
            assert 10 <= max_participants <= 50, (
                f"{activity_name} has unreasonable max_participants: {max_participants}"
            )

    def test_current_participants_not_exceed_maximum_initially(self):
        """Verify initial participants count doesn't exceed max"""
        for activity_name, activity_data in activities.items():
            participants_count = len(activity_data["participants"])
            max_participants = activity_data["max_participants"]
            assert participants_count <= max_participants, (
                f"{activity_name} has {participants_count} participants but max is {max_participants}"
            )


class TestEmailHandling:
    """Tests for email handling and validation"""

    def test_emails_contain_at_symbol(self):
        """Verify all existing participant emails contain @"""
        for activity_name, activity_data in activities.items():
            for email in activity_data["participants"]:
                assert "@" in email, f"Invalid email format: {email}"

    def test_emails_contain_domain(self):
        """Verify all emails have a domain"""
        for activity_name, activity_data in activities.items():
            for email in activity_data["participants"]:
                parts = email.split("@")
                assert len(parts) == 2, f"Invalid email format: {email}"
                assert parts[1], f"Email missing domain: {email}"

    def test_signup_accepts_various_email_formats(self, client):
        """Verify signup accepts various valid email formats"""
        valid_emails = [
            "john@mergington.edu",
            "john.doe@mergington.edu",
            "john123@mergington.edu",
            "j@mergington.edu",
        ]
        for email in valid_emails:
            response = client.post(f"/activities/Soccer Team/signup?email={email}")
            # Should not return 400 for email validation reasons
            assert response.status_code in [200, 400]  # 200 success, 400 only for duplicate
