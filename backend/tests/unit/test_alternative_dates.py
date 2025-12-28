"""Unit tests for alternative date suggestions (T076, T077).

Tests the suggest_alternative_dates functionality that helps guests
find available dates when their requested dates are unavailable.
"""

import datetime as dt
from unittest.mock import MagicMock

import pytest

from src.models import Availability, AvailabilityStatus
from src.services.availability import AvailabilityService


@pytest.fixture
def mock_db() -> MagicMock:
    """Create a mock DynamoDB service."""
    return MagicMock()


@pytest.fixture
def mock_pricing() -> MagicMock:
    """Create a mock Pricing service."""
    return MagicMock()


@pytest.fixture
def availability_service(mock_db: MagicMock, mock_pricing: MagicMock) -> AvailabilityService:
    """Create AvailabilityService with mock dependencies."""
    return AvailabilityService(mock_db, mock_pricing)


def mock_availability_data(
    mock_db: MagicMock,
    unavailable_dates: list[str],
) -> None:
    """Configure mock to return specific unavailable dates.

    Args:
        mock_db: Mock DynamoDB service
        unavailable_dates: List of date strings (YYYY-MM-DD) that are unavailable
    """
    def batch_get_side_effect(table: str, keys: list[dict]) -> list[dict]:
        """Return booked status for specified dates."""
        items = []
        for key in keys:
            date_str = key["date"]
            if date_str in unavailable_dates:
                items.append({
                    "date": date_str,
                    "status": AvailabilityStatus.BOOKED.value,
                })
        return items

    mock_db.batch_get.side_effect = batch_get_side_effect


class TestSuggestAlternativeDates:
    """Tests for suggest_alternative_dates method."""

    def test_suggests_earlier_dates_when_available(
        self,
        availability_service: AvailabilityService,
        mock_db: MagicMock,
    ) -> None:
        """Should suggest dates a few days earlier when available."""
        # Use dates far enough in the future for earlier suggestions to work
        # (earlier dates must be >= today)
        today = dt.date.today()
        start = today + dt.timedelta(days=20)  # 20 days from now
        end = start + dt.timedelta(days=5)  # 5-night stay

        # Block the requested dates
        blocked = [(start + dt.timedelta(days=i)).isoformat() for i in range(5)]
        mock_availability_data(mock_db, blocked)

        # When: Requesting alternatives
        suggestions = availability_service.suggest_alternative_dates(
            requested_start=start,
            requested_end=end,
            search_window_days=10,
            max_suggestions=5,
        )

        # Then: Should suggest earlier dates (since we're 20 days out)
        assert len(suggestions) > 0
        # At least one suggestion should be for earlier dates
        earlier_suggestions = [s for s in suggestions if s["offset_days"] < 0]
        assert len(earlier_suggestions) > 0

    def test_suggests_later_dates_when_available(
        self,
        availability_service: AvailabilityService,
        mock_db: MagicMock,
    ) -> None:
        """Should suggest dates a few days later when available."""
        # Given: July 15-20 is booked
        mock_availability_data(mock_db, ["2025-07-15", "2025-07-16", "2025-07-17", "2025-07-18", "2025-07-19"])

        # When: Requesting alternatives
        suggestions = availability_service.suggest_alternative_dates(
            requested_start=dt.date(2025, 7, 15),
            requested_end=dt.date(2025, 7, 20),
            search_window_days=7,
            max_suggestions=3,
        )

        # Then: Should include some later date suggestions
        assert len(suggestions) > 0
        later_suggestions = [s for s in suggestions if s["offset_days"] > 0]
        assert len(later_suggestions) > 0

    def test_returns_empty_list_when_no_alternatives(
        self,
        availability_service: AvailabilityService,
        mock_db: MagicMock,
    ) -> None:
        """Should return empty list when entire search window is booked."""
        # Use future dates
        today = dt.date.today()
        start = today + dt.timedelta(days=30)

        # Block the entire search window (30 days before and after)
        # to ensure no alternatives can be found
        blocked = []
        for i in range(-30, 50):  # Wide range to cover search window
            d = start + dt.timedelta(days=i)
            if d >= today:  # Can't block past dates anyway
                blocked.append(d.isoformat())
        mock_availability_data(mock_db, blocked)

        # When: Requesting alternatives with small search window
        suggestions = availability_service.suggest_alternative_dates(
            requested_start=start,
            requested_end=start + dt.timedelta(days=5),
            search_window_days=7,  # Only look 7 days in each direction
            max_suggestions=3,
        )

        # Then: Should return empty list (no alternatives found within window)
        assert suggestions == []

    def test_respects_max_suggestions_limit(
        self,
        availability_service: AvailabilityService,
        mock_db: MagicMock,
    ) -> None:
        """Should not return more than max_suggestions alternatives."""
        # Given: Many dates are available
        mock_availability_data(mock_db, [])  # All dates available

        # When: Requesting with limit of 2
        suggestions = availability_service.suggest_alternative_dates(
            requested_start=dt.date(2025, 7, 15),
            requested_end=dt.date(2025, 7, 18),
            search_window_days=14,
            max_suggestions=2,
        )

        # Then: Should return at most 2 suggestions
        assert len(suggestions) <= 2

    def test_suggestions_preserve_stay_duration(
        self,
        availability_service: AvailabilityService,
        mock_db: MagicMock,
    ) -> None:
        """Suggestions should have same number of nights as original request."""
        # Given: Some dates unavailable
        mock_availability_data(mock_db, ["2025-07-15", "2025-07-16"])

        # When: Requesting 5-night stay alternatives
        requested_nights = 5
        suggestions = availability_service.suggest_alternative_dates(
            requested_start=dt.date(2025, 7, 15),
            requested_end=dt.date(2025, 7, 20),
            search_window_days=7,
            max_suggestions=3,
        )

        # Then: All suggestions should be for 5 nights
        for suggestion in suggestions:
            assert suggestion["nights"] == requested_nights

    def test_sorts_suggestions_by_proximity(
        self,
        availability_service: AvailabilityService,
        mock_db: MagicMock,
    ) -> None:
        """Suggestions should be sorted by closeness to original dates."""
        # Given: Various dates available
        mock_availability_data(mock_db, ["2025-07-15"])  # Only requested start blocked

        # When: Requesting alternatives
        suggestions = availability_service.suggest_alternative_dates(
            requested_start=dt.date(2025, 7, 15),
            requested_end=dt.date(2025, 7, 18),
            search_window_days=7,
            max_suggestions=5,
        )

        # Then: Suggestions should be sorted by absolute offset
        offsets = [abs(s["offset_days"]) for s in suggestions]
        assert offsets == sorted(offsets)


class TestSuggestAlternativeDatesEdgeCases:
    """Edge case tests for alternative date suggestions."""

    def test_does_not_suggest_past_dates(
        self,
        availability_service: AvailabilityService,
        mock_db: MagicMock,
    ) -> None:
        """Should not suggest dates in the past."""
        # Given: All dates available but request is for near-term dates
        mock_availability_data(mock_db, [])
        today = dt.date.today()

        # When: Requesting alternatives for tomorrow
        start = today + dt.timedelta(days=1)
        end = start + dt.timedelta(days=3)
        suggestions = availability_service.suggest_alternative_dates(
            requested_start=start,
            requested_end=end,
            search_window_days=7,
            max_suggestions=3,
        )

        # Then: No suggestions should have dates before today
        for suggestion in suggestions:
            check_in = dt.date.fromisoformat(suggestion["check_in"])
            assert check_in >= today

    def test_handles_single_night_stay(
        self,
        availability_service: AvailabilityService,
        mock_db: MagicMock,
    ) -> None:
        """Should handle single night stay requests."""
        # Given: Requested single night is booked
        mock_availability_data(mock_db, ["2025-07-15"])

        # When: Requesting 1-night alternatives
        suggestions = availability_service.suggest_alternative_dates(
            requested_start=dt.date(2025, 7, 15),
            requested_end=dt.date(2025, 7, 16),
            search_window_days=7,
            max_suggestions=3,
        )

        # Then: Should return valid 1-night suggestions
        assert len(suggestions) > 0
        for suggestion in suggestions:
            assert suggestion["nights"] == 1

    def test_includes_direction_in_response(
        self,
        availability_service: AvailabilityService,
        mock_db: MagicMock,
    ) -> None:
        """Suggestions should include direction indicator."""
        # Given: Some dates unavailable
        mock_availability_data(mock_db, ["2025-07-15"])

        # When: Requesting alternatives
        suggestions = availability_service.suggest_alternative_dates(
            requested_start=dt.date(2025, 7, 15),
            requested_end=dt.date(2025, 7, 18),
            search_window_days=7,
            max_suggestions=5,
        )

        # Then: Each suggestion should have direction field
        for suggestion in suggestions:
            assert "direction" in suggestion
            assert suggestion["direction"] in ["earlier", "later"]
            # Direction should match offset sign
            if suggestion["offset_days"] < 0:
                assert suggestion["direction"] == "earlier"
            else:
                assert suggestion["direction"] == "later"


class TestSuggestAlternativeDatesIntegration:
    """Integration-style tests for the complete flow."""

    def test_multiple_blocked_ranges(
        self,
        availability_service: AvailabilityService,
        mock_db: MagicMock,
    ) -> None:
        """Should find gaps between multiple blocked periods."""
        # Given: Two separate blocked periods
        blocked = (
            # Block 1: July 10-14
            ["2025-07-10", "2025-07-11", "2025-07-12", "2025-07-13", "2025-07-14"]
            +
            # Block 2: July 20-24
            ["2025-07-20", "2025-07-21", "2025-07-22", "2025-07-23", "2025-07-24"]
        )
        mock_availability_data(mock_db, blocked)

        # When: Requesting alternatives for dates in middle (July 15-19)
        # which is actually available
        suggestions = availability_service.suggest_alternative_dates(
            requested_start=dt.date(2025, 7, 12),  # Falls in block 1
            requested_end=dt.date(2025, 7, 17),  # 5 nights
            search_window_days=10,
            max_suggestions=3,
        )

        # Then: Should find the gap (July 15-19 area)
        # There should be suggestions outside blocked periods
        assert len(suggestions) > 0
