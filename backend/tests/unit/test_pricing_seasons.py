"""Unit tests for seasonal pricing calculations.

Tests the PricingService's ability to:
- Look up seasonal rates for specific dates
- Calculate total prices across seasons
- Handle transitions between seasons
"""

import datetime as dt
from unittest.mock import MagicMock

import pytest

from src.models import PriceCalculation, Pricing
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
def sample_seasons() -> list[Pricing]:
    """Sample pricing seasons for testing.

    Creates a realistic seasonal pricing structure:
    - Low season: Jan-Mar (€80/night, min 3 nights)
    - Mid season: Apr-Jun, Sep-Nov (€100/night, min 5 nights)
    - High season: Jul-Aug (€150/night, min 7 nights)
    - Peak season: Christmas/NY (€180/night, min 7 nights)
    """
    return [
        Pricing(
            season_id="low-2025",
            season_name="Low Season",
            start_date=dt.date(2025, 1, 1),
            end_date=dt.date(2025, 3, 31),
            nightly_rate=8000,  # €80 in cents
            minimum_nights=3,
            cleaning_fee=5000,  # €50
            is_active=True,
        ),
        Pricing(
            season_id="mid-spring-2025",
            season_name="Mid Season (Spring)",
            start_date=dt.date(2025, 4, 1),
            end_date=dt.date(2025, 6, 30),
            nightly_rate=10000,  # €100
            minimum_nights=5,
            cleaning_fee=5000,
            is_active=True,
        ),
        Pricing(
            season_id="high-2025",
            season_name="High Season",
            start_date=dt.date(2025, 7, 1),
            end_date=dt.date(2025, 8, 31),
            nightly_rate=15000,  # €150
            minimum_nights=7,
            cleaning_fee=6000,  # €60
            is_active=True,
        ),
        Pricing(
            season_id="mid-fall-2025",
            season_name="Mid Season (Fall)",
            start_date=dt.date(2025, 9, 1),
            end_date=dt.date(2025, 11, 30),
            nightly_rate=10000,  # €100
            minimum_nights=5,
            cleaning_fee=5000,
            is_active=True,
        ),
        Pricing(
            season_id="peak-2025",
            season_name="Peak Season (Christmas)",
            start_date=dt.date(2025, 12, 1),
            end_date=dt.date(2025, 12, 31),
            nightly_rate=18000,  # €180
            minimum_nights=7,
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


class TestGetSeasonForDate:
    """Tests for PricingService.get_season_for_date."""

    def test_returns_correct_season_for_low_season(
        self, pricing_service: PricingService, mock_db: MagicMock, sample_seasons: list[Pricing]
    ) -> None:
        """Test that January dates return low season pricing."""
        mock_db._get_table.return_value = mock_table_scan(sample_seasons)

        season = pricing_service.get_season_for_date(dt.date(2025, 2, 15))

        assert season is not None
        assert season.season_name == "Low Season"
        assert season.nightly_rate == 8000

    def test_returns_correct_season_for_high_season(
        self, pricing_service: PricingService, mock_db: MagicMock, sample_seasons: list[Pricing]
    ) -> None:
        """Test that July dates return high season pricing."""
        mock_db._get_table.return_value = mock_table_scan(sample_seasons)

        season = pricing_service.get_season_for_date(dt.date(2025, 7, 20))

        assert season is not None
        assert season.season_name == "High Season"
        assert season.nightly_rate == 15000

    def test_returns_correct_season_for_peak_season(
        self, pricing_service: PricingService, mock_db: MagicMock, sample_seasons: list[Pricing]
    ) -> None:
        """Test that December dates return peak season pricing."""
        mock_db._get_table.return_value = mock_table_scan(sample_seasons)

        season = pricing_service.get_season_for_date(dt.date(2025, 12, 25))

        assert season is not None
        assert season.season_name == "Peak Season (Christmas)"
        assert season.nightly_rate == 18000

    def test_returns_season_on_boundary_dates(
        self, pricing_service: PricingService, mock_db: MagicMock, sample_seasons: list[Pricing]
    ) -> None:
        """Test season lookup on season boundary dates."""
        mock_db._get_table.return_value = mock_table_scan(sample_seasons)

        # First day of high season
        season_start = pricing_service.get_season_for_date(dt.date(2025, 7, 1))
        assert season_start is not None
        assert season_start.season_name == "High Season"

        # Last day of high season
        season_end = pricing_service.get_season_for_date(dt.date(2025, 8, 31))
        assert season_end is not None
        assert season_end.season_name == "High Season"

    def test_returns_none_for_date_without_season(
        self, pricing_service: PricingService, mock_db: MagicMock
    ) -> None:
        """Test that dates outside all seasons return None."""
        # Empty seasons list
        mock_db._get_table.return_value = mock_table_scan([])

        season = pricing_service.get_season_for_date(dt.date(2025, 5, 15))
        assert season is None


class TestCalculatePrice:
    """Tests for PricingService.calculate_price."""

    def test_calculates_low_season_price(
        self, pricing_service: PricingService, mock_db: MagicMock, sample_seasons: list[Pricing]
    ) -> None:
        """Test price calculation for low season stay."""
        mock_db._get_table.return_value = mock_table_scan(sample_seasons)

        # 5 nights in low season: 5 * €80 + €50 cleaning = €450
        result = pricing_service.calculate_price(
            check_in=dt.date(2025, 2, 10),
            check_out=dt.date(2025, 2, 15),
        )

        assert result is not None
        assert result.nights == 5
        assert result.nightly_rate == 8000  # €80 in cents
        assert result.subtotal == 40000  # €400
        assert result.cleaning_fee == 5000  # €50
        assert result.total_amount == 45000  # €450
        assert result.season_name == "Low Season"

    def test_calculates_high_season_price(
        self, pricing_service: PricingService, mock_db: MagicMock, sample_seasons: list[Pricing]
    ) -> None:
        """Test price calculation for high season stay."""
        mock_db._get_table.return_value = mock_table_scan(sample_seasons)

        # 7 nights in high season: 7 * €150 + €60 cleaning = €1110
        result = pricing_service.calculate_price(
            check_in=dt.date(2025, 7, 10),
            check_out=dt.date(2025, 7, 17),
        )

        assert result is not None
        assert result.nights == 7
        assert result.nightly_rate == 15000  # €150 in cents
        assert result.subtotal == 105000  # €1050
        assert result.cleaning_fee == 6000  # €60
        assert result.total_amount == 111000  # €1110
        assert result.season_name == "High Season"

    def test_calculates_price_for_single_night(
        self, pricing_service: PricingService, mock_db: MagicMock, sample_seasons: list[Pricing]
    ) -> None:
        """Test price calculation for minimum 1-night stay."""
        mock_db._get_table.return_value = mock_table_scan(sample_seasons)

        result = pricing_service.calculate_price(
            check_in=dt.date(2025, 2, 10),
            check_out=dt.date(2025, 2, 11),
        )

        assert result is not None
        assert result.nights == 1
        assert result.subtotal == 8000
        assert result.total_amount == 13000  # €80 + €50 cleaning

    def test_returns_none_for_zero_nights(
        self, pricing_service: PricingService, mock_db: MagicMock, sample_seasons: list[Pricing]
    ) -> None:
        """Test that same check-in/check-out returns None."""
        mock_db._get_table.return_value = mock_table_scan(sample_seasons)

        result = pricing_service.calculate_price(
            check_in=dt.date(2025, 2, 10),
            check_out=dt.date(2025, 2, 10),
        )

        assert result is None

    def test_returns_none_for_negative_nights(
        self, pricing_service: PricingService, mock_db: MagicMock, sample_seasons: list[Pricing]
    ) -> None:
        """Test that check-out before check-in returns None."""
        mock_db._get_table.return_value = mock_table_scan(sample_seasons)

        result = pricing_service.calculate_price(
            check_in=dt.date(2025, 2, 15),
            check_out=dt.date(2025, 2, 10),
        )

        assert result is None

    def test_returns_none_when_no_season_available(
        self, pricing_service: PricingService, mock_db: MagicMock
    ) -> None:
        """Test price calculation when no season is available."""
        mock_db._get_table.return_value = mock_table_scan([])

        result = pricing_service.calculate_price(
            check_in=dt.date(2025, 2, 10),
            check_out=dt.date(2025, 2, 15),
        )

        assert result is None

    def test_price_includes_minimum_nights_info(
        self, pricing_service: PricingService, mock_db: MagicMock, sample_seasons: list[Pricing]
    ) -> None:
        """Test that price calculation includes minimum nights requirement."""
        mock_db._get_table.return_value = mock_table_scan(sample_seasons)

        result = pricing_service.calculate_price(
            check_in=dt.date(2025, 7, 10),
            check_out=dt.date(2025, 7, 17),
        )

        assert result is not None
        assert result.minimum_nights == 7  # High season minimum


class TestGetAllSeasons:
    """Tests for PricingService.get_all_seasons."""

    def test_returns_all_active_seasons(
        self, pricing_service: PricingService, mock_db: MagicMock, sample_seasons: list[Pricing]
    ) -> None:
        """Test that all active seasons are returned."""
        mock_db._get_table.return_value = mock_table_scan(sample_seasons)

        seasons = pricing_service.get_all_seasons(active_only=True)

        assert len(seasons) == 5
        assert all(s.is_active for s in seasons)

    def test_returns_seasons_sorted_by_start_date(
        self, pricing_service: PricingService, mock_db: MagicMock, sample_seasons: list[Pricing]
    ) -> None:
        """Test that seasons are sorted chronologically."""
        mock_db._get_table.return_value = mock_table_scan(sample_seasons)

        seasons = pricing_service.get_all_seasons()

        start_dates = [s.start_date for s in seasons]
        assert start_dates == sorted(start_dates)

    def test_filters_inactive_seasons(
        self, pricing_service: PricingService, mock_db: MagicMock
    ) -> None:
        """Test that inactive seasons are filtered out when active_only=True."""
        seasons_with_inactive = [
            Pricing(
                season_id="active-season",
                season_name="Active",
                start_date=dt.date(2025, 1, 1),
                end_date=dt.date(2025, 3, 31),
                nightly_rate=8000,
                minimum_nights=3,
                cleaning_fee=5000,
                is_active=True,
            ),
            Pricing(
                season_id="inactive-season",
                season_name="Inactive",
                start_date=dt.date(2025, 4, 1),
                end_date=dt.date(2025, 6, 30),
                nightly_rate=10000,
                minimum_nights=5,
                cleaning_fee=5000,
                is_active=False,
            ),
        ]
        mock_db._get_table.return_value = mock_table_scan(seasons_with_inactive)

        active_seasons = pricing_service.get_all_seasons(active_only=True)
        all_seasons = pricing_service.get_all_seasons(active_only=False)

        assert len(active_seasons) == 1
        assert active_seasons[0].season_name == "Active"
        assert len(all_seasons) == 2


class TestSeasonTransitions:
    """Tests for handling stays that span season boundaries."""

    def test_uses_checkin_date_season_rate(
        self, pricing_service: PricingService, mock_db: MagicMock, sample_seasons: list[Pricing]
    ) -> None:
        """Test that the check-in date determines the rate.

        When a stay spans season boundaries, the rate from the
        check-in date's season is used for the entire stay.
        """
        mock_db._get_table.return_value = mock_table_scan(sample_seasons)

        # Stay starts March 28 (low season) ends April 5 (mid season)
        # Should use low season rate for entire stay
        result = pricing_service.calculate_price(
            check_in=dt.date(2025, 3, 28),
            check_out=dt.date(2025, 4, 5),
        )

        assert result is not None
        assert result.nights == 8
        # Low season rate: €80/night
        assert result.nightly_rate == 8000
        assert result.season_name == "Low Season"
        assert result.total_amount == 8 * 8000 + 5000  # 8 nights + cleaning
