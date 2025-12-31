"""Contract tests for OAuth2 auth API endpoints.

Tests the HTTP contract for session status endpoint.
OAuth2 callback completion is handled by frontend via SDK (not backend API).

Tests cover:
- GET /api/auth/session/{session_id} returns session status JSON
- GET /api/auth/session/{session_id} with unknown ID returns 404
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from shared.models.oauth2_session import OAuth2Session, OAuth2SessionStatus


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    from api.main import app

    return TestClient(app)


@pytest.fixture
def mock_dynamodb_service() -> MagicMock:
    """Mock DynamoDBService for auth API tests."""
    mock_service = MagicMock()
    return mock_service


class TestGetSessionEndpoint:
    """Tests for GET /api/auth/session/{session_id} endpoint."""

    def test_get_session_returns_status_json(
        self,
        client: TestClient,
        mock_dynamodb_service: MagicMock,
    ) -> None:
        """Should return session status as JSON."""
        # Given: Session exists
        session_id = "session-status-check"
        mock_dynamodb_service.get_oauth2_session.return_value = OAuth2Session(
            session_id=session_id,
            conversation_id="conv-status",
            guest_email="status@example.com",
            status=OAuth2SessionStatus.COMPLETED,
            created_at=datetime.now(timezone.utc),
            expires_at=int(datetime.now(timezone.utc).timestamp()) + 600,
        )

        # When: Getting session status
        with patch(
            "api.routes.auth.get_dynamodb_service", return_value=mock_dynamodb_service
        ):
            response = client.get(f"/api/auth/session/{session_id}")

        # Then: Should return JSON with status
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert data["status"] == "completed"

    def test_get_session_unknown_id_returns_404(
        self,
        client: TestClient,
        mock_dynamodb_service: MagicMock,
    ) -> None:
        """Should return 404 when session_id doesn't exist."""
        # Given: Session doesn't exist
        mock_dynamodb_service.get_oauth2_session.return_value = None

        # When: Getting unknown session
        with patch(
            "api.routes.auth.get_dynamodb_service", return_value=mock_dynamodb_service
        ):
            response = client.get("/api/auth/session/session-unknown")

        # Then: Should return 404 Not Found
        assert response.status_code == 404
        data = response.json()
        assert "error" in data or "detail" in data

    def test_get_session_returns_pending_status(
        self,
        client: TestClient,
        mock_dynamodb_service: MagicMock,
    ) -> None:
        """Should return PENDING status when auth in progress."""
        # Given: Session is pending
        session_id = "session-pending"
        mock_dynamodb_service.get_oauth2_session.return_value = OAuth2Session(
            session_id=session_id,
            conversation_id="conv-pending",
            guest_email="pending@example.com",
            status=OAuth2SessionStatus.PENDING,
            created_at=datetime.now(timezone.utc),
            expires_at=int(datetime.now(timezone.utc).timestamp()) + 600,
        )

        # When: Getting session status
        with patch(
            "api.routes.auth.get_dynamodb_service", return_value=mock_dynamodb_service
        ):
            response = client.get(f"/api/auth/session/{session_id}")

        # Then: Should return pending status
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"

    def test_get_session_returns_failed_status(
        self,
        client: TestClient,
        mock_dynamodb_service: MagicMock,
    ) -> None:
        """Should return FAILED status when auth failed."""
        # Given: Session failed
        session_id = "session-failed"
        mock_dynamodb_service.get_oauth2_session.return_value = OAuth2Session(
            session_id=session_id,
            conversation_id="conv-failed",
            guest_email="failed@example.com",
            status=OAuth2SessionStatus.FAILED,
            created_at=datetime.now(timezone.utc),
            expires_at=int(datetime.now(timezone.utc).timestamp()) + 600,
        )

        # When: Getting session status
        with patch(
            "api.routes.auth.get_dynamodb_service", return_value=mock_dynamodb_service
        ):
            response = client.get(f"/api/auth/session/{session_id}")

        # Then: Should return failed status
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
