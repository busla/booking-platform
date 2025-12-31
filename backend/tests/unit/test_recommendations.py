"""Unit tests for recommendation tools (T079).

Tests the get_recommendations functionality that helps guests
discover activities and places based on their interests.
"""

import pytest

from shared.models import AreaCategory, AreaInfo
from shared.tools.area_info import (
    get_recommendations,
    load_area_data_from_dicts,
    set_area_data_store,
)


@pytest.fixture(autouse=True)
def reset_area_data() -> None:
    """Reset area data before each test."""
    set_area_data_store([])


# Sample test data fixtures (shared with test_area_info.py pattern)
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


class TestGetRecommendations:
    """Tests for get_recommendations tool functionality."""

    def test_returns_recommendations_matching_interests(
        self, sample_area_data: list[dict]
    ) -> None:
        """Should return places matching user interests."""
        load_area_data_from_dicts(sample_area_data)

        result = get_recommendations(interests=["golf"])

        assert result["status"] == "success"
        assert result["total_count"] == 2
        # Should return both golf courses
        names = [r["name"] for r in result["recommendations"]]
        assert "La Marquesa Golf" in names
        assert "Vistabella Golf" in names

    def test_matches_multiple_interests(
        self, sample_area_data: list[dict]
    ) -> None:
        """Should return places matching any of multiple interests."""
        load_area_data_from_dicts(sample_area_data)

        result = get_recommendations(interests=["golf", "beach"], limit=10)

        assert result["status"] == "success"
        # Should include golf courses and beaches
        categories = {r["category"] for r in result["recommendations"]}
        assert "golf" in categories
        assert "beach" in categories

    def test_filters_by_max_distance(
        self, sample_area_data: list[dict]
    ) -> None:
        """Should only return places within max_distance_km."""
        load_area_data_from_dicts(sample_area_data)

        result = get_recommendations(max_distance_km=5.0, limit=20)

        assert result["status"] == "success"
        for place in result["recommendations"]:
            assert place["distance_km"] <= 5.0

    def test_filters_family_friendly_only(
        self, sample_area_data: list[dict]
    ) -> None:
        """Should only return family-friendly places when requested."""
        load_area_data_from_dicts(sample_area_data)

        result = get_recommendations(
            interests=["sailing", "activity"],
            family_friendly_only=True,
            limit=10,
        )

        # Club Nautico has sailing tag but is not family-friendly
        for place in result["recommendations"]:
            assert place["family_friendly"] is True
        names = [r["name"] for r in result["recommendations"]]
        assert "Club Nautico" not in names

    def test_respects_limit(
        self, sample_area_data: list[dict]
    ) -> None:
        """Should not return more than limit recommendations."""
        load_area_data_from_dicts(sample_area_data)

        result = get_recommendations(limit=2)

        assert result["status"] == "success"
        assert len(result["recommendations"]) <= 2

    def test_returns_sorted_by_relevance_then_distance(
        self, sample_area_data: list[dict]
    ) -> None:
        """Should sort by relevance to interests, then by distance."""
        load_area_data_from_dicts(sample_area_data)

        # Golf has both tag and category matches for golf courses
        result = get_recommendations(interests=["golf"], limit=10)

        places = result["recommendations"]
        # Both golf courses should be returned, closest first among equal relevance
        golf_places = [p for p in places if p["category"] == "golf"]
        if len(golf_places) >= 2:
            distances = [p["distance_km"] for p in golf_places]
            assert distances == sorted(distances)

    def test_returns_empty_for_no_matching_interests(
        self, sample_area_data: list[dict]
    ) -> None:
        """Should return empty list when no places match interests."""
        load_area_data_from_dicts(sample_area_data)

        result = get_recommendations(interests=["skiing", "snowboarding"])

        assert result["status"] == "success"
        assert result["total_count"] == 0
        assert len(result["recommendations"]) == 0

    def test_returns_diverse_recommendations_when_no_interests(
        self, sample_area_data: list[dict]
    ) -> None:
        """Should return diverse category mix when no specific interests."""
        load_area_data_from_dicts(sample_area_data)

        result = get_recommendations(limit=10)

        assert result["status"] == "success"
        categories = {r["category"] for r in result["recommendations"]}
        # Should have multiple categories represented
        assert len(categories) >= 2

    def test_matches_tags_case_insensitive(
        self, sample_area_data: list[dict]
    ) -> None:
        """Should match interests to tags case-insensitively."""
        load_area_data_from_dicts(sample_area_data)

        result = get_recommendations(interests=["GOLF"])

        assert result["status"] == "success"
        assert result["total_count"] == 2
        # Should find golf courses despite uppercase interest

    def test_matches_category_names_as_interests(
        self, sample_area_data: list[dict]
    ) -> None:
        """Should match category names as valid interests."""
        load_area_data_from_dicts(sample_area_data)

        result = get_recommendations(interests=["beach"])

        assert result["status"] == "success"
        # Should find beaches because "beach" matches the category
        categories = [r["category"] for r in result["recommendations"]]
        assert "beach" in categories

    def test_includes_filters_applied_in_response(
        self, sample_area_data: list[dict]
    ) -> None:
        """Should include applied filters in response metadata."""
        load_area_data_from_dicts(sample_area_data)

        result = get_recommendations(
            interests=["golf"],
            max_distance_km=10.0,
            family_friendly_only=True,
            limit=3,
        )

        assert "filters_applied" in result
        filters = result["filters_applied"]
        assert filters["interests"] == ["golf"]
        assert filters["max_distance_km"] == 10.0
        assert filters["family_friendly_only"] is True
        assert filters["limit"] == 3


class TestRecommendationScenarios:
    """Scenario-based tests for common recommendation use cases."""

    def test_family_vacation_recommendations(
        self, sample_area_data: list[dict]
    ) -> None:
        """Should recommend family-friendly activities for families."""
        load_area_data_from_dicts(sample_area_data)

        result = get_recommendations(
            interests=["family", "kids"],
            family_friendly_only=True,
            limit=10,
        )

        assert result["status"] == "success"
        names = [r["name"] for r in result["recommendations"]]
        # Aquopolis has "family" and "kids" tags
        assert "Aquopolis Torrevieja" in names
        # Club Nautico should be excluded (not family-friendly)
        assert "Club Nautico" not in names

    def test_golf_trip_recommendations(
        self, sample_area_data: list[dict]
    ) -> None:
        """Should recommend golf courses for golf enthusiasts."""
        load_area_data_from_dicts(sample_area_data)

        result = get_recommendations(interests=["golf"])

        assert result["status"] == "success"
        names = [r["name"] for r in result["recommendations"]]
        assert "La Marquesa Golf" in names
        assert "Vistabella Golf" in names

    def test_food_lover_recommendations(
        self, sample_area_data: list[dict]
    ) -> None:
        """Should recommend restaurants for food lovers."""
        load_area_data_from_dicts(sample_area_data)

        result = get_recommendations(
            interests=["restaurant", "tapas", "seafood"],
            limit=10,
        )

        assert result["status"] == "success"
        names = [r["name"] for r in result["recommendations"]]
        assert "La Taberna" in names  # Has "tapas" tag
        assert "El Pescador" in names  # Has "seafood" tag

    def test_nature_photography_recommendations(
        self, sample_area_data: list[dict]
    ) -> None:
        """Should recommend scenic spots for photographers."""
        load_area_data_from_dicts(sample_area_data)

        result = get_recommendations(interests=["nature", "photography"])

        assert result["status"] == "success"
        names = [r["name"] for r in result["recommendations"]]
        # Salt Lakes has both "nature" and "photography" tags
        assert "Torrevieja Salt Lakes" in names

    def test_water_sports_recommendations(
        self, sample_area_data: list[dict]
    ) -> None:
        """Should recommend water activities for sports enthusiasts."""
        load_area_data_from_dicts(sample_area_data)

        result = get_recommendations(
            interests=["swimming", "sailing", "water park"],
            limit=10,
        )

        assert result["status"] == "success"
        names = [r["name"] for r in result["recommendations"]]
        # Multiple places should match these interests
        assert len(result["recommendations"]) >= 2
