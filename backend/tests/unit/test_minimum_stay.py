"""Unit tests for minimum stay validation.

Tests the PricingService's validate_minimum_stay functionality,
which enforces different minimum night requirements per season.
"""

import datetime as dt
from unittest.mock import MagicMock

import pytest

from src.models import Pricing
from src.services.pricing import PricingService


@pytest.fixture
def mock_db() -> MagicMock:
    """Create a mock DynamoDB service."""
    return MagicMock()


@pytest.fixture
def pricing_service(mock_db: MagicMock) -> PricingService:
    """Create PricingService with mock DB."""
    return PricingService(mock_db)


@pytest.fixture
def seasons_with_varying_minimums() -> list[Pricing]:
    """Seasons with different minimum stay requirements.

    - Low season: 3 nights minimum
    - High season: 7 nights minimum
    - Peak season: 10 nights minimum
    """
    return [
        Pricing(
            season_id="low-2025",
            season_name="Low Season",
            start_date=dt.date(2025, 1, 1),
            end_date=dt.date(2025, 6, 30),
            nightly_rate=8000,
            minimum_nights=3,
            cleaning_fee=5000,
            is_active=True,
        ),
        Pricing(
            season_id="high-2025",
            season_name="High Season",
            start_date=dt.date(2025, 7, 1),
            end_date=dt.date(2025, 8, 31),
            nightly_rate=15000,
            minimum_nights=7,
            cleaning_fee=6000,
            is_active=True,
        ),
        Pricing(
            season_id="peak-2025",
            season_name="Peak Season (Christmas)",
            start_date=dt.date(2025, 12, 1),
            end_date=dt.date(2025, 12, 31),
            nightly_rate=18000,
            minimum_nights=10,
            cleaning_fee=6000,
            is_active=True,
        ),
    ]


def mock_table_scan(seasons: list[Pricing]) -> MagicMock:
    """Create mock table with scan response."""
    mock_table = MagicMock()
    mock_table.scan.return_value = {
        "Items": [
            {
                "season_id": s.season_id,
                "season_name": s.season_name,
                "start_date": s.start_date.isoformat(),
                "end_date": s.end_date.isoformat(),
                "nightly_rate": s.nightly_rate,
                "minimum_nights": s.minimum_nights,
                "cleaning_fee": s.cleaning_fee,
                "is_active": s.is_active,
            }
            for s in seasons
        ]
    }
    return mock_table


class TestValidateMinimumStay:
    """Tests for PricingService.validate_minimum_stay."""

    def test_accepts_stay_meeting_low_season_minimum(
        self,
        pricing_service: PricingService,
        mock_db: MagicMock,
        seasons_with_varying_minimums: list[Pricing],
    ) -> None:
        """Test that 3+ night stay in low season passes validation."""
        mock_db._get_table.return_value = mock_table_scan(seasons_with_varying_minimums)

        is_valid, error = pricing_service.validate_minimum_stay(
            check_in=dt.date(2025, 2, 10),
            check_out=dt.date(2025, 2, 13),  # 3 nights
        )

        assert is_valid is True
        assert error == ""

    def test_rejects_stay_below_low_season_minimum(
        self,
        pricing_service: PricingService,
        mock_db: MagicMock,
        seasons_with_varying_minimums: list[Pricing],
    ) -> None:
        """Test that <3 night stay in low season fails validation."""
        mock_db._get_table.return_value = mock_table_scan(seasons_with_varying_minimums)

        is_valid, error = pricing_service.validate_minimum_stay(
            check_in=dt.date(2025, 2, 10),
            check_out=dt.date(2025, 2, 12),  # 2 nights
        )

        assert is_valid is False
        assert "Minimum stay is 3 nights" in error
        assert "Low Season" in error
        assert "2 nights" in error

    def test_accepts_stay_meeting_high_season_minimum(
        self,
        pricing_service: PricingService,
        mock_db: MagicMock,
        seasons_with_varying_minimums: list[Pricing],
    ) -> None:
        """Test that 7+ night stay in high season passes validation."""
        mock_db._get_table.return_value = mock_table_scan(seasons_with_varying_minimums)

        is_valid, error = pricing_service.validate_minimum_stay(
            check_in=dt.date(2025, 7, 10),
            check_out=dt.date(2025, 7, 17),  # 7 nights
        )

        assert is_valid is True
        assert error == ""

    def test_rejects_stay_below_high_season_minimum(
        self,
        pricing_service: PricingService,
        mock_db: MagicMock,
        seasons_with_varying_minimums: list[Pricing],
    ) -> None:
        """Test that <7 night stay in high season fails validation."""
        mock_db._get_table.return_value = mock_table_scan(seasons_with_varying_minimums)

        is_valid, error = pricing_service.validate_minimum_stay(
            check_in=dt.date(2025, 7, 10),
            check_out=dt.date(2025, 7, 15),  # 5 nights
        )

        assert is_valid is False
        assert "Minimum stay is 7 nights" in error
        assert "High Season" in error
        assert "5 nights" in error

    def test_accepts_stay_meeting_peak_season_minimum(
        self,
        pricing_service: PricingService,
        mock_db: MagicMock,
        seasons_with_varying_minimums: list[Pricing],
    ) -> None:
        """Test that 10+ night stay in peak season passes validation."""
        mock_db._get_table.return_value = mock_table_scan(seasons_with_varying_minimums)

        is_valid, error = pricing_service.validate_minimum_stay(
            check_in=dt.date(2025, 12, 15),
            check_out=dt.date(2025, 12, 25),  # 10 nights
        )

        assert is_valid is True
        assert error == ""

    def test_rejects_stay_below_peak_season_minimum(
        self,
        pricing_service: PricingService,
        mock_db: MagicMock,
        seasons_with_varying_minimums: list[Pricing],
    ) -> None:
        """Test that <10 night stay in peak season fails validation."""
        mock_db._get_table.return_value = mock_table_scan(seasons_with_varying_minimums)

        is_valid, error = pricing_service.validate_minimum_stay(
            check_in=dt.date(2025, 12, 15),
            check_out=dt.date(2025, 12, 22),  # 7 nights
        )

        assert is_valid is False
        assert "Minimum stay is 10 nights" in error
        assert "Peak Season" in error
        assert "7 nights" in error


class TestMinimumStayEdgeCases:
    """Edge case tests for minimum stay validation."""

    def test_accepts_stay_exactly_at_minimum(
        self,
        pricing_service: PricingService,
        mock_db: MagicMock,
        seasons_with_varying_minimums: list[Pricing],
    ) -> None:
        """Test that stay exactly matching minimum passes."""
        mock_db._get_table.return_value = mock_table_scan(seasons_with_varying_minimums)

        # Exactly 3 nights in low season
        is_valid, error = pricing_service.validate_minimum_stay(
            check_in=dt.date(2025, 2, 10),
            check_out=dt.date(2025, 2, 13),
        )

        assert is_valid is True

    def test_accepts_stay_exceeding_minimum(
        self,
        pricing_service: PricingService,
        mock_db: MagicMock,
        seasons_with_varying_minimums: list[Pricing],
    ) -> None:
        """Test that stay exceeding minimum passes."""
        mock_db._get_table.return_value = mock_table_scan(seasons_with_varying_minimums)

        # 14 nights in high season (minimum is 7)
        is_valid, error = pricing_service.validate_minimum_stay(
            check_in=dt.date(2025, 7, 1),
            check_out=dt.date(2025, 7, 15),
        )

        assert is_valid is True

    def test_returns_error_for_missing_season(
        self,
        pricing_service: PricingService,
        mock_db: MagicMock,
    ) -> None:
        """Test validation when no season is configured for dates."""
        mock_db._get_table.return_value = mock_table_scan([])

        is_valid, error = pricing_service.validate_minimum_stay(
            check_in=dt.date(2025, 5, 10),
            check_out=dt.date(2025, 5, 15),
        )

        assert is_valid is False
        assert "No pricing available" in error

    def test_rejects_single_night_stay_when_minimum_is_higher(
        self,
        pricing_service: PricingService,
        mock_db: MagicMock,
        seasons_with_varying_minimums: list[Pricing],
    ) -> None:
        """Test that 1-night stay fails in all seasons (min is 3)."""
        mock_db._get_table.return_value = mock_table_scan(seasons_with_varying_minimums)

        is_valid, error = pricing_service.validate_minimum_stay(
            check_in=dt.date(2025, 2, 10),
            check_out=dt.date(2025, 2, 11),  # 1 night
        )

        assert is_valid is False
        assert "1 nights" in error


class TestMinimumStayErrorMessages:
    """Tests for minimum stay error message formatting."""

    def test_error_includes_required_nights(
        self,
        pricing_service: PricingService,
        mock_db: MagicMock,
        seasons_with_varying_minimums: list[Pricing],
    ) -> None:
        """Test that error message includes required minimum nights."""
        mock_db._get_table.return_value = mock_table_scan(seasons_with_varying_minimums)

        _, error = pricing_service.validate_minimum_stay(
            check_in=dt.date(2025, 7, 10),
            check_out=dt.date(2025, 7, 13),  # 3 nights, min is 7
        )

        assert "7 nights" in error

    def test_error_includes_selected_nights(
        self,
        pricing_service: PricingService,
        mock_db: MagicMock,
        seasons_with_varying_minimums: list[Pricing],
    ) -> None:
        """Test that error message includes actual selected nights."""
        mock_db._get_table.return_value = mock_table_scan(seasons_with_varying_minimums)

        _, error = pricing_service.validate_minimum_stay(
            check_in=dt.date(2025, 7, 10),
            check_out=dt.date(2025, 7, 13),  # 3 nights
        )

        assert "3 nights" in error

    def test_error_includes_season_name(
        self,
        pricing_service: PricingService,
        mock_db: MagicMock,
        seasons_with_varying_minimums: list[Pricing],
    ) -> None:
        """Test that error message includes season name for context."""
        mock_db._get_table.return_value = mock_table_scan(seasons_with_varying_minimums)

        _, error = pricing_service.validate_minimum_stay(
            check_in=dt.date(2025, 7, 10),
            check_out=dt.date(2025, 7, 13),
        )

        assert "High Season" in error


class TestMinimumStayWithVariousSeasons:
    """Tests for minimum stay across different season types."""

    def test_low_season_allows_shorter_stays(
        self,
        pricing_service: PricingService,
        mock_db: MagicMock,
        seasons_with_varying_minimums: list[Pricing],
    ) -> None:
        """Test that low season (3 night min) allows shorter stays than high season."""
        mock_db._get_table.return_value = mock_table_scan(seasons_with_varying_minimums)

        # 4 nights - passes in low season
        is_valid_low, _ = pricing_service.validate_minimum_stay(
            check_in=dt.date(2025, 2, 10),
            check_out=dt.date(2025, 2, 14),
        )

        # Same duration fails in high season
        is_valid_high, _ = pricing_service.validate_minimum_stay(
            check_in=dt.date(2025, 7, 10),
            check_out=dt.date(2025, 7, 14),
        )

        assert is_valid_low is True
        assert is_valid_high is False

    def test_validation_uses_checkin_date_season(
        self,
        pricing_service: PricingService,
        mock_db: MagicMock,
        seasons_with_varying_minimums: list[Pricing],
    ) -> None:
        """Test that minimum stay uses check-in date's season.

        If stay starts in low season and extends into high season,
        the low season minimum should apply.
        """
        mock_db._get_table.return_value = mock_table_scan(seasons_with_varying_minimums)

        # Start June 28 (low season), checkout July 2 (high season)
        # Low season minimum of 3 nights should apply
        is_valid, error = pricing_service.validate_minimum_stay(
            check_in=dt.date(2025, 6, 28),
            check_out=dt.date(2025, 7, 2),  # 4 nights
        )

        assert is_valid is True
