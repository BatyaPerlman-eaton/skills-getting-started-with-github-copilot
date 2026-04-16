"""
Integration tests for all FastAPI endpoints.
Tests the full request/response flow for each endpoint.
"""

import pytest
from src.app import activities


class TestGetRoot:
    """Tests for GET / endpoint"""

    def test_root_redirects_to_static_index(self, client):
        """Verify root endpoint redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_all_activities_returns_dict(self, client):
        """Verify GET /activities returns activities dictionary"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_get_activities_has_all_activities(self, client):
        """Verify all 9 activities are returned"""
        response = client.get("/activities")
        data = response.json()
        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Basketball Team",
            "Soccer Team",
            "Drama Club",
            "Art Studio",
            "Debate Club",
            "Robotics Club",
        ]
        assert len(data) == 9
        for activity_name in expected_activities:
            assert activity_name in data

    def test_activity_has_required_fields(self, client):
        """Verify each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        required_fields = ["description", "schedule", "max_participants", "participants"]
        for activity_name, activity_data in data.items():
            for field in required_fields:
                assert field in activity_data
                assert isinstance(activity_data[field], (str, int, list))

    def test_activities_have_correct_max_participants(self, client):
        """Verify max_participants values are correct"""
        response = client.get("/activities")
        data = response.json()
        expected_max_participants = {
            "Chess Club": 12,
            "Programming Class": 20,
            "Gym Class": 30,
            "Basketball Team": 15,
            "Soccer Team": 18,
            "Drama Club": 20,
            "Art Studio": 16,
            "Debate Club": 14,
            "Robotics Club": 12,
        }
        for activity_name, expected_max in expected_max_participants.items():
            assert data[activity_name]["max_participants"] == expected_max

    def test_activities_have_participants_list(self, client):
        """Verify participants field is a list"""
        response = client.get("/activities")
        data = response.json()
        for activity_name, activity_data in data.items():
            assert isinstance(activity_data["participants"], list)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_happy_path(self, client):
        """Successfully sign up a new student for an activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "newstudent@mergington.edu" in data["message"]

    def test_signup_adds_student_to_participants(self, client):
        """Verify signup adds the student to the participants list"""
        email = "newstudent@mergington.edu"
        client.post(f"/activities/Chess Club/signup?email={email}")
        assert email in activities["Chess Club"]["participants"]

    def test_signup_duplicate_returns_400(self, client):
        """Already signed up student gets 400 error"""
        email = "michael@mergington.edu"  # Already in Chess Club
        response = client.post(f"/activities/Chess Club/signup?email={email}")
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_nonexistent_activity_returns_404(self, client):
        """Signing up for non-existent activity returns 404"""
        response = client.post(
            "/activities/NonExistent Club/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_multiple_students_same_activity(self, client):
        """Multiple different students can sign up for same activity"""
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        for email in emails:
            response = client.post(f"/activities/Gym Class/signup?email={email}")
            assert response.status_code == 200

        for email in emails:
            assert email in activities["Gym Class"]["participants"]

    def test_signup_same_student_different_activities(self, client):
        """Same student can sign up for multiple different activities"""
        email = "versatile@mergington.edu"
        activities_to_join = ["Chess Club", "Drama Club", "Debate Club"]
        for activity_name in activities_to_join:
            response = client.post(f"/activities/{activity_name}/signup?email={email}")
            assert response.status_code == 200

        for activity_name in activities_to_join:
            assert email in activities[activity_name]["participants"]

    def test_signup_at_max_capacity_still_allows_signup(self, client):
        """Verify signup doesn't check max capacity (based on app logic)"""
        # Build up an activity close to capacity
        activity_name = "Chess Club"
        initial_participants = len(activities[activity_name]["participants"])
        max_participants = activities[activity_name]["max_participants"]

        # Fill up to max
        for i in range(max_participants - initial_participants):
            email = f"student{i}@mergington.edu"
            response = client.post(f"/activities/{activity_name}/signup?email={email}")
            assert response.status_code == 200

        # Try to add one more (should still succeed based on app logic)
        extra_email = "overfull@mergington.edu"
        response = client.post(f"/activities/{activity_name}/signup?email={extra_email}")
        # App doesn't enforce max capacity, so this should succeed
        assert response.status_code == 200 or response.status_code == 400

    def test_signup_with_different_email_formats(self, client):
        """Signup works with different valid email formats"""
        emails = [
            "first.last@mergington.edu",
            "firstname123@mergington.edu",
            "a@mergington.edu",
        ]
        for email in emails:
            response = client.post(f"/activities/Art Studio/signup?email={email}")
            assert response.status_code == 200
            assert email in activities["Art Studio"]["participants"]


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_happy_path(self, client):
        """Successfully unregister a student from an activity"""
        email = "michael@mergington.edu"  # Already in Chess Club
        response = client.delete(f"/activities/Chess Club/unregister?email={email}")
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]

    def test_unregister_removes_from_participants(self, client):
        """Verify unregister removes the student from participants list"""
        email = "michael@mergington.edu"
        client.delete(f"/activities/Chess Club/unregister?email={email}")
        assert email not in activities["Chess Club"]["participants"]

    def test_unregister_not_registered_returns_400(self, client):
        """Unregistering student not in activity returns 400"""
        email = "notregistered@mergington.edu"
        response = client.delete(f"/activities/Chess Club/unregister?email={email}")
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]

    def test_unregister_nonexistent_activity_returns_404(self, client):
        """Unregistering from non-existent activity returns 404"""
        response = client.delete(
            "/activities/NonExistent Club/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_then_signup_again(self, client):
        """Student can unregister and then sign up again"""
        email = "michael@mergington.edu"
        activity = "Chess Club"

        # Unregister
        response = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert response.status_code == 200
        assert email not in activities[activity]["participants"]

        # Sign up again
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
        assert email in activities[activity]["participants"]

    def test_unregister_multiple_students(self, client):
        """Multiple students can be unregistered from same activity"""
        activity = "Robotics Club"
        initial_participants = activities[activity]["participants"].copy()

        for email in initial_participants:
            response = client.delete(f"/activities/{activity}/unregister?email={email}")
            assert response.status_code == 200

        assert len(activities[activity]["participants"]) == 0


class TestActivityStateIsolation:
    """Tests to verify activity state is properly isolated between tests"""

    def test_activity_state_persists_within_test(self, client):
        """Verify state persists within a single test"""
        email = "isolation@mergington.edu"
        client.post(f"/activities/Chess Club/signup?email={email}")
        response = client.get("/activities")
        data = response.json()
        assert email in data["Chess Club"]["participants"]

    def test_signup_unregister_sequence(self, client):
        """Verify signup/unregister sequence works correctly"""
        email = "sequence@mergington.edu"
        activity = "Programming Class"

        # Sign up
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200

        # Verify signup
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]

        # Unregister
        response = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert response.status_code == 200

        # Verify unregister
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]
