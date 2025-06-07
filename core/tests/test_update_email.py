import pytest
from django.urls import reverse
from knox.models import AuthToken
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import User
from core.tests.factories import UserFactory


class UpdateEmailAPIViewTest(APITestCase):
    """
    Test cases for the UpdateEmailAPIView endpoint.
    """

    def setUp(self):
        """Set up test data."""
        self.user = UserFactory()
        self.url = reverse("update-email")

        self.token = AuthToken.objects.create(self.user)[1]
        self.auth_header = f"Token {self.token}"

    def test_successful_email_update(self):
        """Test successful email update for authenticated user."""
        new_email = "newemail@example.com"
        data = {"email": new_email}

        self.client.credentials(HTTP_AUTHORIZATION=self.auth_header)
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Email updated successfully")
        self.assertEqual(response.data["email"], new_email)

        # Verify email was updated in database
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, new_email)

    def test_invalid_email_format(self):
        """Test validation failure for invalid email format."""
        invalid_emails = [
            "invalid-email",
            "invalid@",
            "@example.com",
            "invalid..email@example.com",
            "",
        ]

        self.client.credentials(HTTP_AUTHORIZATION=self.auth_header)

        for invalid_email in invalid_emails:
            data = {"email": invalid_email}
            response = self.client.post(self.url, data, format="json")

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn("email", response.data)

    def test_unauthorized_access(self):
        """Test that unauthenticated requests return 401."""
        data = {"email": "test@example.com"}

        # Make request without authentication
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_missing_email_field(self):
        """Test validation failure when email field is missing."""
        data = {}  # No email field

        self.client.credentials(HTTP_AUTHORIZATION=self.auth_header)
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_email_normalization(self):
        """Test that email is normalized to lowercase."""
        mixed_case_email = "Test.Email@EXAMPLE.COM"
        expected_email = "test.email@example.com"
        data = {"email": mixed_case_email}

        self.client.credentials(HTTP_AUTHORIZATION=self.auth_header)
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], expected_email)

        # Verify email was normalized in database
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, expected_email)

    def test_invalid_token(self):
        """Test that invalid tokens return 401."""
        data = {"email": "test@example.com"}

        # Use invalid token
        self.client.credentials(HTTP_AUTHORIZATION="Token invalid-token")
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
