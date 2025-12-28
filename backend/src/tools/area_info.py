"""Area information tools for local attractions and amenities.

These tools allow the booking agent to provide information about
golf courses, beaches, restaurants, attractions, and activities
in the Quesada/Costa Blanca area.
"""

import json
import logging
from pathlib import Path
from typing import Any

from strands import tool

from src.models import (
    AreaCategory,
    AreaInfo,
    AreaInfoResponse,
    RecommendationResponse,
)

logger = logging.getLogger(__name__)


# In-memory data store for area information
# This can be loaded from JSON or DynamoDB in production
_AREA_DATA: list[AreaInfo] = []
_DATA_LOADED: bool = False


def get_area_data_store() -> list[AreaInfo]:
    """Get the current area data store."""
    return _AREA_DATA


def set_area_data_store(data: list[AreaInfo]) -> None:
    """Set the area data store (for testing or initialization)."""
    global _AREA_DATA
    _AREA_DATA = data


def load_area_data_from_dicts(data: list[dict[str, Any]]) -> None:
    """Load area data from a list of dictionaries.

    Useful for loading from JSON files or test fixtures.
    """
    global _AREA_DATA
    _AREA_DATA = []
    for item in data:
        # Convert category string to enum if needed
        if isinstance(item.get("category"), str):
            item = item.copy()
            item["category"] = AreaCategory(item["category"])
        _AREA_DATA.append(AreaInfo(**item))


def load_area_data_from_json(json_path: Path | str | None = None) -> int:
    """Load area data from JSON file.

    Args:
        json_path: Path to JSON file. If None, uses default location.

    Returns:
        Number of places loaded.

    Raises:
        FileNotFoundError: If JSON file doesn't exist.
        json.JSONDecodeError: If JSON is invalid.
    """
    global _DATA_LOADED

    if json_path is None:
        # Default to bundled data file
        json_path = Path(__file__).parent.parent / "data" / "area_info.json"

    json_path = Path(json_path)

    with open(json_path) as f:
        data = json.load(f)

    places = data.get("places", [])
    load_area_data_from_dicts(places)
    _DATA_LOADED = True

    logger.info(f"Loaded {len(places)} area info places from {json_path}")
    return len(places)


def ensure_area_data_loaded() -> None:
    """Ensure area data is loaded, loading from default source if needed."""
    global _DATA_LOADED
    if not _DATA_LOADED and len(_AREA_DATA) == 0:
        try:
            load_area_data_from_json()
        except FileNotFoundError:
            logger.warning("Area info data file not found, starting with empty data")
            _DATA_LOADED = True  # Mark as loaded (empty) to prevent repeated attempts


@tool
def get_area_info(category: str | None = None) -> dict[str, Any]:
    """Get information about local places and attractions.

    Use this tool when a guest asks about things to do, places to eat,
    golf courses, beaches, or attractions near the property.

    Args:
        category: Optional filter - one of: golf, beach, restaurant,
                  attraction, activity. If not provided, returns all places.

    Returns:
        Dictionary with list of places sorted by distance from the property
    """
    # Ensure data is loaded
    ensure_area_data_loaded()
    data = get_area_data_store()

    # Validate category if provided
    category_enum: AreaCategory | None = None
    if category:
        category_lower = category.lower().strip()
        try:
            category_enum = AreaCategory(category_lower)
        except ValueError:
            valid_categories = [c.value for c in AreaCategory]
            return {
                "status": "error",
                "message": f"Unknown category '{category}'. Valid categories are: {', '.join(valid_categories)}",
            }

    # Filter by category if specified
    if category_enum:
        filtered = [place for place in data if place.category == category_enum]
    else:
        filtered = list(data)

    # Sort by distance (closest first)
    filtered.sort(key=lambda p: p.distance_km)

    # Build response
    response = AreaInfoResponse(
        places=filtered,
        category=category_enum,
        total_count=len(filtered),
    )

    # Create helpful message
    if category_enum:
        category_name = category_enum.value.replace("_", " ")
        if filtered:
            message = f"Found {len(filtered)} {category_name}(s) near the property."
        else:
            message = f"No {category_name}s found in our database."
    else:
        if filtered:
            message = f"Found {len(filtered)} places of interest near the property."
        else:
            message = "No places found in our database."

    return {
        "status": "success",
        "places": [place.model_dump() for place in response.places],
        "category": response.category.value if response.category else None,
        "total_count": response.total_count,
        "message": message,
    }


@tool
def get_recommendations(
    interests: list[str] | None = None,
    max_distance_km: float | None = None,
    family_friendly_only: bool = False,
    limit: int = 5,
) -> dict[str, Any]:
    """Get personalized recommendations based on guest interests.

    Use this tool when a guest asks for suggestions or recommendations,
    or when they mention their interests (golf, beaches, family activities, etc.).

    Args:
        interests: List of interests to match (e.g., ['golf', 'beach', 'family']).
                  Matches against place tags and categories.
        max_distance_km: Optional maximum distance filter in kilometers.
        family_friendly_only: If True, only return family-friendly places.
        limit: Maximum number of recommendations to return (1-20, default 5).

    Returns:
        Dictionary with personalized recommendations sorted by relevance and distance
    """
    # Ensure data is loaded
    ensure_area_data_loaded()
    data = get_area_data_store()

    # Validate limit
    if limit < 1:
        limit = 1
    elif limit > 20:
        limit = 20

    # Normalize interests to lowercase
    normalized_interests = [i.lower().strip() for i in (interests or [])]

    # Score and filter places
    scored_places: list[tuple[AreaInfo, int]] = []

    for place in data:
        # Apply family-friendly filter
        if family_friendly_only and not place.family_friendly:
            continue

        # Apply distance filter
        if max_distance_km is not None and place.distance_km > max_distance_km:
            continue

        # Calculate relevance score based on interest matching
        score = 0
        if normalized_interests:
            # Check tags (case-insensitive)
            place_tags = [t.lower() for t in place.tags]
            for interest in normalized_interests:
                if interest in place_tags:
                    score += 2  # Direct tag match
                # Also check if interest matches category
                if interest == place.category.value:
                    score += 2  # Category match
                # Check partial matches in description or name
                if interest in place.description.lower():
                    score += 1
                if interest in place.name.lower():
                    score += 1

        scored_places.append((place, score))

    # Filter based on interests
    if normalized_interests:
        # Only include places with at least one match
        scored_places = [(p, s) for p, s in scored_places if s > 0]
    else:
        # No interests specified - provide diverse recommendations
        # Group by category and pick from each
        category_places: dict[AreaCategory, list[AreaInfo]] = {}
        for place, _ in scored_places:
            if place.category not in category_places:
                category_places[place.category] = []
            category_places[place.category].append(place)

        # Take closest from each category for diversity
        diverse_places: list[tuple[AreaInfo, int]] = []
        for cat_places in category_places.values():
            cat_places.sort(key=lambda p: p.distance_km)
            for p in cat_places[:2]:  # Take up to 2 from each category
                diverse_places.append((p, 1))
        scored_places = diverse_places

    # Sort by relevance score (descending), then by distance (ascending)
    scored_places.sort(key=lambda x: (-x[1], x[0].distance_km))

    # Apply limit
    recommendations = [place for place, _ in scored_places[:limit]]

    # Build filters applied info
    filters_applied: dict[str, Any] = {}
    if interests:
        filters_applied["interests"] = interests
    if max_distance_km is not None:
        filters_applied["max_distance_km"] = max_distance_km
    if family_friendly_only:
        filters_applied["family_friendly_only"] = family_friendly_only
    filters_applied["limit"] = limit

    # Build response
    response = RecommendationResponse(
        recommendations=recommendations,
        total_count=len(recommendations),
        filters_applied=filters_applied,
    )

    # Create helpful message
    if recommendations:
        if interests:
            interest_text = ", ".join(interests[:3])
            if len(interests) > 3:
                interest_text += f" and {len(interests) - 3} more"
            message = f"Based on your interests ({interest_text}), here are {len(recommendations)} recommendations."
        else:
            message = f"Here are {len(recommendations)} popular places near the property."
    else:
        message = "No places match your criteria. Try adjusting your filters."

    return {
        "status": "success",
        "recommendations": [r.model_dump() for r in response.recommendations],
        "total_count": response.total_count,
        "filters_applied": response.filters_applied,
        "message": message,
    }
