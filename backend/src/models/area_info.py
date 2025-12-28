"""Area information models for local attractions and amenities."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AreaCategory(str, Enum):
    """Categories for area information."""

    GOLF = "golf"
    BEACH = "beach"
    RESTAURANT = "restaurant"
    ATTRACTION = "attraction"
    ACTIVITY = "activity"


class AreaInfo(BaseModel):
    """Information about a local place or attraction.

    Flexible model to accommodate different types of places
    (golf courses, beaches, restaurants, attractions, activities).
    """

    model_config = ConfigDict(strict=True)

    id: str = Field(..., description="Unique identifier for the place")
    name: str = Field(..., description="Name of the place")
    category: AreaCategory = Field(..., description="Category of the place")
    description: str = Field(..., description="Brief description")
    distance_km: float = Field(..., ge=0, description="Distance from property in km")

    # Optional fields that vary by category
    cuisine: str | None = Field(
        default=None, description="Cuisine type (for restaurants)"
    )
    price_range: str | None = Field(
        default=None, description="Price range indicator (e.g., €, ​€€, ​€€€)"
    )
    phone: str | None = Field(default=None, description="Contact phone number")
    website: str | None = Field(default=None, description="Website URL")
    address: str | None = Field(default=None, description="Street address")
    opening_hours: str | None = Field(default=None, description="Opening hours")
    features: list[str] = Field(
        default_factory=list, description="Key features or highlights"
    )
    family_friendly: bool = Field(
        default=True, description="Whether suitable for families"
    )
    tags: list[str] = Field(
        default_factory=list, description="Searchable tags for recommendations"
    )


class AreaInfoResponse(BaseModel):
    """Response model for area information queries."""

    model_config = ConfigDict(strict=True)

    places: list[AreaInfo] = Field(..., description="List of matching places")
    category: AreaCategory | None = Field(
        default=None, description="Filter category used"
    )
    total_count: int = Field(..., description="Total number of results")


class RecommendationRequest(BaseModel):
    """Request model for recommendations."""

    model_config = ConfigDict(strict=True)

    interests: list[str] = Field(
        default_factory=list, description="User interests (golf, beach, family, etc.)"
    )
    max_distance_km: float | None = Field(
        default=None, ge=0, description="Maximum distance filter"
    )
    family_friendly_only: bool = Field(
        default=False, description="Only return family-friendly options"
    )
    limit: int = Field(default=5, ge=1, le=20, description="Maximum recommendations")


class RecommendationResponse(BaseModel):
    """Response model for recommendations."""

    model_config = ConfigDict(strict=True)

    recommendations: list[AreaInfo] = Field(..., description="Recommended places")
    total_count: int = Field(..., description="Number of recommendations")
    filters_applied: dict[str, Any] = Field(
        default_factory=dict, description="Filters that were applied"
    )
