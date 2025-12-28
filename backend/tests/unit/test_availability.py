"""Unit tests for availability tools (T044).

Tests the check_availability and get_calendar tools that allow
the agent to check if dates are available for booking.
"""

from datetime import date
from decimal import Decimal
from typing import Any

import pytest
from moto import mock_aws

# Import will work once tools are implemented
# from src.tools.availability import check_availability, get_calendar


class TestCheckAvailability:
    """Tests for the check_availability tool."""

    @pytest.mark.skip(reason="Tool not yet implemented")
    def test_check_availability_available_dates(
        self,
        dynamodb_client: Any,
        create_tables: None,
    ) -> None:
        """Should return available=True for open dates."""
        # Given: A date range with no existing bookings
        check_in = "2025-07-01"
        check_out = "2025-07-05"

        # When: Checking availability for those dates
        result = check_availability(check_in, check_out)

        # Then: Should indicate dates are available
        assert result["available"] is True
        assert result["check_in_date"] == check_in
        assert result["check_out_date"] == check_out
        assert result["num_nights"] == 4

    @pytest.mark.skip(reason="Tool not yet implemented")
    def test_check_availability_booked_dates(
        self,
        dynamodb_client: Any,
        create_tables: None,
        sample_reservation: dict[str, Any],
    ) -> None:
        """Should return available=False when dates overlap with existing booking."""
        # Given: An existing reservation for July 15-22
        # (fixture provides this data)

        # When: Checking availability that overlaps
        check_in = "2025-07-18"
        check_out = "2025-07-25"
        result = check_availability(check_in, check_out)

        # Then: Should indicate dates are NOT available
        assert result["available"] is False
        assert "conflict" in result or "reason" in result

    @pytest.mark.skip(reason="Tool not yet implemented")
    def test_check_availability_partial_overlap(
        self,
        dynamodb_client: Any,
        create_tables: None,
    ) -> None:
        """Should detect partial overlap with existing bookings."""
        # Given: A booking exists for July 10-14
        # When: Checking July 12-18 (overlaps by 2 days)
        result = check_availability("2025-07-12", "2025-07-18")

        # Then: Should indicate unavailable
        assert result["available"] is False

    @pytest.mark.skip(reason="Tool not yet implemented")
    def test_check_availability_adjacent_dates_allowed(
        self,
        dynamodb_client: Any,
        create_tables: None,
    ) -> None:
        """Adjacent bookings should be allowed (checkout day = new checkin)."""
        # Given: A booking exists for July 10-14 (checkout on 14th)
        # When: Checking July 14-18 (checkin on 14th - same day checkout/checkin)
        result = check_availability("2025-07-14", "2025-07-18")

        # Then: Should be available (turnover day)
        assert result["available"] is True

    @pytest.mark.skip(reason="Tool not yet implemented")
    def test_check_availability_minimum_stay_enforced(
        self,
        dynamodb_client: Any,
        create_tables: None,
        sample_pricing: dict[str, Any],
    ) -> None:
        """Should enforce minimum stay requirements by season."""
        # Given: Peak season (August) requires 7-night minimum
        check_in = "2025-08-01"
        check_out = "2025-08-04"  # Only 3 nights

        # When: Checking availability
        result = check_availability(check_in, check_out)

        # Then: Should indicate min stay not met
        assert result["available"] is False
        assert result.get("min_stay_required", 0) >= 7
        assert result.get("min_stay_met") is False

    @pytest.mark.skip(reason="Tool not yet implemented")
    def test_check_availability_invalid_date_range(self) -> None:
        """Should reject checkout before checkin."""
        # When: Checking with checkout before checkin
        result = check_availability("2025-07-10", "2025-07-05")

        # Then: Should indicate error
        assert result.get("error") is not None or result["available"] is False

    @pytest.mark.skip(reason="Tool not yet implemented")
    def test_check_availability_past_dates(self) -> None:
        """Should reject dates in the past."""
        # When: Checking dates in the past
        result = check_availability("2020-01-01", "2020-01-05")

        # Then: Should indicate error
        assert result.get("error") is not None or result["available"] is False


class TestGetCalendar:
    """Tests for the get_calendar tool."""

    @pytest.mark.skip(reason="Tool not yet implemented")
    def test_get_calendar_returns_month_data(
        self,
        dynamodb_client: Any,
        create_tables: None,
    ) -> None:
        """Should return availability for entire month."""
        # When: Getting calendar for July 2025
        result = get_calendar(2025, 7)

        # Then: Should return all days of the month
        assert result["year"] == 2025
        assert result["month"] == 7
        assert len(result["days"]) == 31  # July has 31 days

    @pytest.mark.skip(reason="Tool not yet implemented")
    def test_get_calendar_shows_booked_dates(
        self,
        dynamodb_client: Any,
        create_tables: None,
        sample_availability: list[dict[str, Any]],
    ) -> None:
        """Should mark booked dates in the calendar."""
        # Given: Some dates are booked (July 10-14 from fixture)

        # When: Getting calendar for July 2025
        result = get_calendar(2025, 7)

        # Then: Booked dates should be marked
        booked_days = [d for d in result["days"] if d["status"] == "booked"]
        assert len(booked_days) > 0

        # Specifically July 10-14 should be booked
        for day_num in [10, 11, 12, 13, 14]:
            day_str = f"2025-07-{day_num:02d}"
            day_entry = next((d for d in result["days"] if d["date"] == day_str), None)
            assert day_entry is not None
            assert day_entry["status"] == "booked"

    @pytest.mark.skip(reason="Tool not yet implemented")
    def test_get_calendar_includes_minimum_stay(
        self,
        dynamodb_client: Any,
        create_tables: None,
    ) -> None:
        """Should include minimum stay info for each day."""
        # When: Getting calendar for high season (July)
        result = get_calendar(2025, 7)

        # Then: Days should include min_stay
        for day in result["days"]:
            assert "min_stay" in day
            assert day["min_stay"] >= 1

    @pytest.mark.skip(reason="Tool not yet implemented")
    def test_get_calendar_handles_blocked_dates(
        self,
        dynamodb_client: Any,
        create_tables: None,
    ) -> None:
        """Should handle owner-blocked dates."""
        # Given: Some dates are blocked by owner (not available for booking)

        # When: Getting calendar
        result = get_calendar(2025, 7)

        # Then: Blocked dates should be marked as such
        # (implementation may vary - could be 'blocked' or 'unavailable')
        statuses = {d["status"] for d in result["days"]}
        assert "available" in statuses  # At least some should be available

    @pytest.mark.skip(reason="Tool not yet implemented")
    def test_get_calendar_invalid_month(self) -> None:
        """Should handle invalid month numbers."""
        # When: Getting calendar for invalid month
        result = get_calendar(2025, 13)

        # Then: Should return error
        assert "error" in result

    @pytest.mark.skip(reason="Tool not yet implemented")
    def test_get_calendar_multiple_months(
        self,
        dynamodb_client: Any,
        create_tables: None,
    ) -> None:
        """Should be able to get consecutive months."""
        # When: Getting calendar for July and August
        july = get_calendar(2025, 7)
        august = get_calendar(2025, 8)

        # Then: Both should return valid data
        assert july["month"] == 7
        assert august["month"] == 8
        assert len(july["days"]) == 31
        assert len(august["days"]) == 31


class TestAvailabilityEdgeCases:
    """Edge case tests for availability checking."""

    @pytest.mark.skip(reason="Tool not yet implemented")
    def test_same_day_checkin_checkout_rejected(self) -> None:
        """Should reject same-day checkin/checkout (0 nights)."""
        result = check_availability("2025-07-15", "2025-07-15")
        assert result["available"] is False

    @pytest.mark.skip(reason="Tool not yet implemented")
    def test_very_long_stay(
        self,
        dynamodb_client: Any,
        create_tables: None,
    ) -> None:
        """Should handle very long stay requests."""
        # When: Checking 90-day stay
        result = check_availability("2025-07-01", "2025-09-29")

        # Then: Should return valid result (available or not)
        assert "available" in result
        assert result["num_nights"] == 90

    @pytest.mark.skip(reason="Tool not yet implemented")
    def test_year_boundary_stay(
        self,
        dynamodb_client: Any,
        create_tables: None,
    ) -> None:
        """Should handle stays that span year boundary."""
        # When: Checking December 28 - January 4
        result = check_availability("2025-12-28", "2026-01-04")

        # Then: Should return valid result
        assert "available" in result
        assert result["num_nights"] == 7
