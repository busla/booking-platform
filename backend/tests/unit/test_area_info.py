"""Unit tests for area information tools (T078).

Tests the get_area_info functionality that provides local area
knowledge about golf courses, beaches, restaurants, and activities.
"""

import pytest

from shared.models import AreaCategory, AreaInfo
from shared.tools.area_info import (
    get_area_info,
    load_area_data_from_dicts,
    set_area_data_store,
)


@pytest.fixture(autouse=True)
def reset_area_data() -> None:
    """Reset area data before each test."""
    set_area_data_store([])


# Sample test data fixtures
@pytest.fixture
def sample_area_data() -> list[dict]:
    """Create sample area information data."""
    return [
        {
            "id": "golf-1",
            "name": "La Marquesa Golf",
            "category": "golf",
            "description": "18-hole course with stunning views",
            "distance_km": 3.0,
            "features": ["18 holes", "clubhouse", "restaurant"],
            "family_friendly": True,
            "tags": ["golf", "sport", "outdoor"],
        },
        {
            "id": "golf-2",
            "name": "Vistabella Golf",
            "category": "golf",
            "description": "Championship course",
            "distance_km": 8.0,
            "features": ["27 holes", "pro shop"],
            "family_friendly": True,
            "tags": ["golf", "sport", "championship"],
        },
        {
            "id": "beach-1",
            "name": "Guardamar Beach",
            "category": "beach",
            "description": "Long sandy beach with dunes",
            "distance_km": 15.0,
            "features": ["sandy", "dunes", "lifeguard"],
            "family_friendly": True,
            "tags": ["beach", "swimming", "family"],
        },
        {
            "id": "beach-2",
            "name": "La Mata Beach",
            "category": "beach",
            "description": "Blue flag beach",
            "distance_km": 12.0,
            "features": ["blue flag", "promenade"],
            "family_friendly": True,
            "tags": ["beach", "swimming", "clean"],
        },
        {
            "id": "restaurant-1",
            "name": "La Taberna",
            "category": "restaurant",
            "description": "Traditional Spanish tapas",
            "distance_km": 1.0,
            "cuisine": "Spanish tapas",
            "price_range": "€€",
            "family_friendly": True,
            "tags": ["restaurant", "tapas", "spanish"],
        },
        {
            "id": "restaurant-2",
            "name": "El Pescador",
            "category": "restaurant",
            "description": "Fresh seafood restaurant",
            "distance_km": 5.0,
            "cuisine": "Seafood",
            "price_range": "€€€",
            "family_friendly": True,
            "tags": ["restaurant", "seafood", "fine dining"],
        },
        {
            "id": "attraction-1",
            "name": "Torrevieja Salt Lakes",
            "category": "attraction",
            "description": "Pink salt lakes, great for photos",
            "distance_km": 10.0,
            "features": ["photography", "nature", "free entry"],
            "family_friendly": True,
            "tags": ["attraction", "nature", "photography"],
        },
        {
            "id": "activity-1",
            "name": "Aquopolis Torrevieja",
            "category": "activity",
            "description": "Water park",
            "distance_km": 12.0,
            "features": ["slides", "pools", "kids area"],
            "family_friendly": True,
            "tags": ["activity", "water park", "family", "kids"],
        },
        {
            "id": "activity-2",
            "name": "Club Nautico",
            "category": "activity",
            "description": "Sailing and water sports club",
            "distance_km": 15.0,
            "features": ["sailing", "kayaking", "lessons"],
            "family_friendly": False,
            "tags": ["activity", "sailing", "sport", "adults"],
        },
    ]


class TestAreaInfoModel:
    """Tests for AreaInfo model validation."""

    def test_creates_valid_area_info(self) -> None:
        """Should create a valid AreaInfo instance."""
        info = AreaInfo(
            id="golf-1",
            name="La Marquesa Golf",
            category=AreaCategory.GOLF,
            description="18-hole course",
            distance_km=3.0,
        )
        assert info.name == "La Marquesa Golf"
        assert info.category == AreaCategory.GOLF
        assert info.distance_km == 3.0

    def test_creates_restaurant_with_optional_fields(self) -> None:
        """Should create restaurant with cuisine and price_range."""
        info = AreaInfo(
            id="rest-1",
            name="La Taberna",
            category=AreaCategory.RESTAURANT,
            description="Spanish tapas",
            distance_km=1.0,
            cuisine="Spanish tapas",
            price_range="€€",
        )
        assert info.cuisine == "Spanish tapas"
        assert info.price_range == "€€"

    def test_requires_positive_distance(self) -> None:
        """Should reject negative distance."""
        with pytest.raises(ValueError):
            AreaInfo(
                id="test-1",
                name="Test Place",
                category=AreaCategory.BEACH,
                description="Test",
                distance_km=-5.0,
            )

    def test_default_values(self) -> None:
        """Should have sensible defaults for optional fields."""
        info = AreaInfo(
            id="test-1",
            name="Test Place",
            category=AreaCategory.ATTRACTION,
            description="Test attraction",
            distance_km=5.0,
        )
        assert info.cuisine is None
        assert info.price_range is None
        assert info.features == []
        assert info.family_friendly is True
        assert info.tags == []


class TestGetAreaInfo:
    """Tests for get_area_info tool functionality."""

    def test_returns_all_places_when_no_category_filter(
        self, sample_area_data: list[dict]
    ) -> None:
        """Should return all places when no category specified."""
        load_area_data_from_dicts(sample_area_data)

        result = get_area_info()

        assert result["status"] == "success"
        assert result["total_count"] == 9  # All 9 sample places
        assert len(result["places"]) == 9
        assert result["category"] is None

    def test_filters_by_golf_category(
        self, sample_area_data: list[dict]
    ) -> None:
        """Should return only golf courses when category is golf."""
        load_area_data_from_dicts(sample_area_data)

        result = get_area_info(category="golf")

        assert result["status"] == "success"
        assert result["total_count"] == 2
        assert all(p["category"] == "golf" for p in result["places"])

    def test_filters_by_beach_category(
        self, sample_area_data: list[dict]
    ) -> None:
        """Should return only beaches when category is beach."""
        load_area_data_from_dicts(sample_area_data)

        result = get_area_info(category="beach")

        assert result["status"] == "success"
        assert result["total_count"] == 2
        assert all(p["category"] == "beach" for p in result["places"])

    def test_filters_by_restaurant_category(
        self, sample_area_data: list[dict]
    ) -> None:
        """Should return only restaurants when category is restaurant."""
        load_area_data_from_dicts(sample_area_data)

        result = get_area_info(category="restaurant")

        assert result["status"] == "success"
        assert result["total_count"] == 2
        assert all(p["category"] == "restaurant" for p in result["places"])

    def test_filters_by_attraction_category(
        self, sample_area_data: list[dict]
    ) -> None:
        """Should return only attractions when category is attraction."""
        load_area_data_from_dicts(sample_area_data)

        result = get_area_info(category="attraction")

        assert result["status"] == "success"
        assert result["total_count"] == 1
        assert all(p["category"] == "attraction" for p in result["places"])

    def test_filters_by_activity_category(
        self, sample_area_data: list[dict]
    ) -> None:
        """Should return only activities when category is activity."""
        load_area_data_from_dicts(sample_area_data)

        result = get_area_info(category="activity")

        assert result["status"] == "success"
        assert result["total_count"] == 2
        assert all(p["category"] == "activity" for p in result["places"])

    def test_returns_sorted_by_distance(
        self, sample_area_data: list[dict]
    ) -> None:
        """Should return places sorted by distance (closest first)."""
        load_area_data_from_dicts(sample_area_data)

        result = get_area_info()

        assert result["status"] == "success"
        places = result["places"]
        distances = [p["distance_km"] for p in places]
        assert distances == sorted(distances), "Places should be sorted by distance"

    def test_includes_all_required_fields(
        self, sample_area_data: list[dict]
    ) -> None:
        """Should include all required fields in response."""
        load_area_data_from_dicts(sample_area_data)

        result = get_area_info(category="golf")

        assert "status" in result
        assert "places" in result
        assert "total_count" in result
        assert "message" in result

        # Check place fields
        place = result["places"][0]
        assert "id" in place
        assert "name" in place
        assert "category" in place
        assert "description" in place
        assert "distance_km" in place

    def test_returns_error_for_unknown_category(self) -> None:
        """Should handle invalid category gracefully."""
        result = get_area_info(category="invalid_category")

        assert result["status"] == "error"
        assert "Unknown category" in result["message"]
        assert "golf" in result["message"]  # Should list valid categories

    def test_response_includes_total_count(
        self, sample_area_data: list[dict]
    ) -> None:
        """Should include total count in response."""
        load_area_data_from_dicts(sample_area_data)

        result = get_area_info(category="golf")

        assert result["total_count"] == 2
        assert len(result["places"]) == result["total_count"]
