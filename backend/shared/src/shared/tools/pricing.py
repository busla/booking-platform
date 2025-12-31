"""Pricing tools for vacation rental rate calculations.

These tools allow the booking agent to get pricing information,
calculate totals, explain seasonal variations, and validate minimum stays.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Any

from boto3.dynamodb.conditions import Key
from strands import tool

logger = logging.getLogger(__name__)

from shared.models.errors import ErrorCode, ToolError
from shared.models.pricing import Pricing
from shared.services.dynamodb import get_dynamodb_service


# Season categorization thresholds (rates in cents)
LOW_SEASON_MAX_RATE = 10000  # €100 or less is low season
HIGH_SEASON_MIN_RATE = 14000  # €140 or more is high/peak season


def _get_db():
    """Get shared DynamoDB service instance (singleton for performance)."""
    return get_dynamodb_service()


def _parse_date(date_str: str) -> date:
    """Parse date string in YYYY-MM-DD format."""
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def _get_applicable_pricing(check_in: date, check_out: date) -> Pricing | None:  # noqa: ARG001
    """Get the pricing configuration that applies to the given dates.

    For simplicity, we use the pricing that applies to the check-in date.
    In a more complex system, you might prorate across multiple seasons.
    """
    db = _get_db()

    # Query all active pricing records
    # In production, you'd use a more efficient query with GSI
    items = db.query(
        "pricing",
        Key("is_active").eq("true"),
        index_name="active-index",
    )

    check_in_str = check_in.isoformat()

    for item in items:
        start = item.get("start_date", "")
        end = item.get("end_date", "")
        if start <= check_in_str <= end:
            return Pricing(
                season_id=item["season_id"],
                season_name=item["season_name"],
                start_date=_parse_date(item["start_date"]),
                end_date=_parse_date(item["end_date"]),
                nightly_rate=int(item["nightly_rate"]),
                minimum_nights=int(item["minimum_nights"]),
                cleaning_fee=int(item["cleaning_fee"]),
                is_active=True,
            )

    return None


def _get_default_pricing() -> Pricing:
    """Return default pricing when no seasonal pricing is configured."""
    today = date.today()
    return Pricing(
        season_id="default",
        season_name="Standard Season",
        start_date=today,
        end_date=today + timedelta(days=365),
        nightly_rate=12000,  # €120.00 in cents
        minimum_nights=3,
        cleaning_fee=5000,  # €50.00 in cents
        is_active=True,
    )


def _get_all_seasons() -> list[Pricing]:
    """Get all active pricing seasons for comparison."""
    db = _get_db()
    try:
        items = db.query(
            "pricing",
            Key("is_active").eq("true"),
            index_name="active-index",
        )
    except Exception:
        items = []

    seasons = []
    for item in items:
        seasons.append(
            Pricing(
                season_id=item["season_id"],
                season_name=item["season_name"],
                start_date=_parse_date(item["start_date"]),
                end_date=_parse_date(item["end_date"]),
                nightly_rate=int(item["nightly_rate"]),
                minimum_nights=int(item["minimum_nights"]),
                cleaning_fee=int(item["cleaning_fee"]),
                is_active=True,
            )
        )
    return sorted(seasons, key=lambda s: s.start_date)


def _get_seasonal_context(current_rate: int, seasons: list[Pricing]) -> dict[str, Any]:
    """Generate context about how current rate compares to other seasons.

    Args:
        current_rate: The nightly rate for the requested dates
        seasons: All available seasons

    Returns:
        Dictionary with seasonal comparison info
    """
    if not seasons:
        return {
            "rate_category": "standard",
            "comparison_note": "",
            "savings_tip": "",
        }

    rates = [s.nightly_rate for s in seasons]
    min_rate = min(rates)
    max_rate = max(rates)

    # Categorize the current rate
    if current_rate <= LOW_SEASON_MAX_RATE:
        rate_category = "low"
    elif current_rate >= HIGH_SEASON_MIN_RATE:
        rate_category = "high"
    else:
        rate_category = "mid"

    # Find cheapest season for savings tip
    cheapest_season = min(seasons, key=lambda s: s.nightly_rate)
    savings_tip = ""
    if current_rate > min_rate:
        savings_per_night = (current_rate - min_rate) / 100
        savings_tip = (
            f"Tip: You could save €{savings_per_night:.0f}/night by booking during "
            f"{cheapest_season.season_name} ({cheapest_season.start_date.strftime('%b %d')} - "
            f"{cheapest_season.end_date.strftime('%b %d')})."
        )

    # Generate comparison note
    if rate_category == "low":
        comparison_note = "This is our lowest rate period - great value!"
    elif rate_category == "high":
        comparison_note = "This is our peak pricing period."
    else:
        comparison_note = "This is our mid-season rate."

    return {
        "rate_category": rate_category,
        "comparison_note": comparison_note,
        "savings_tip": savings_tip,
        "min_rate_eur": min_rate / 100,
        "max_rate_eur": max_rate / 100,
    }


@tool
def get_pricing(check_in: str, check_out: str) -> dict[str, Any]:
    """Get detailed pricing information for a stay.

    Use this tool when a guest asks about prices, rates, or costs
    for specific dates. Returns the applicable seasonal rate,
    minimum stay requirements, and fee breakdown.

    Args:
        check_in: Check-in date in YYYY-MM-DD format (e.g., '2025-07-15')
        check_out: Check-out date in YYYY-MM-DD format (e.g., '2025-07-22')

    Returns:
        Dictionary with pricing details including nightly rate, fees, and total
    """
    logger.info("get_pricing called", extra={"check_in": check_in, "check_out": check_out})
    try:
        start_date = _parse_date(check_in)
        end_date = _parse_date(check_out)
    except ValueError:
        return {
            "status": "error",
            "message": "Invalid date format. Please use YYYY-MM-DD format.",
        }

    if end_date <= start_date:
        return {
            "status": "error",
            "message": "Check-out date must be after check-in date.",
        }

    nights = (end_date - start_date).days

    # Get applicable pricing
    pricing = _get_applicable_pricing(start_date, end_date)
    if pricing is None:
        pricing = _get_default_pricing()

    # Check minimum nights
    if nights < pricing.minimum_nights:
        error = ToolError.from_code(
            ErrorCode.MINIMUM_NIGHTS_NOT_MET,
            details={
                "minimum_nights_required": str(pricing.minimum_nights),
                "nights_requested": str(nights),
                "season_name": pricing.season_name,
            },
        )
        return error.model_dump()

    # Calculate total
    subtotal = pricing.nightly_rate * nights
    total = subtotal + pricing.cleaning_fee

    # Get seasonal context for enhanced response (T073)
    all_seasons = _get_all_seasons()
    seasonal_context = _get_seasonal_context(pricing.nightly_rate, all_seasons)

    # Build the response message with seasonal context
    base_message = (
        f"For {nights} nights during {pricing.season_name}: "
        f"€{subtotal / 100:.2f} accommodation + €{pricing.cleaning_fee / 100:.2f} cleaning = "
        f"€{total / 100:.2f} total."
    )
    if seasonal_context.get("comparison_note"):
        base_message += f" {seasonal_context['comparison_note']}"

    result = {
        "status": "success",
        "check_in": check_in,
        "check_out": check_out,
        "nights": nights,
        "season_name": pricing.season_name,
        "nightly_rate_eur": pricing.nightly_rate / 100,
        "nightly_rate_cents": pricing.nightly_rate,
        "subtotal_eur": subtotal / 100,
        "cleaning_fee_eur": pricing.cleaning_fee / 100,
        "total_eur": total / 100,
        "total_cents": total,
        "minimum_nights": pricing.minimum_nights,
        "message": base_message,
        # Seasonal comparison info (T073 enhancement)
        "seasonal_context": {
            "rate_category": seasonal_context.get("rate_category", "standard"),
            "comparison_note": seasonal_context.get("comparison_note", ""),
            "savings_tip": seasonal_context.get("savings_tip", ""),
        },
    }

    return result


@tool
def calculate_total(
    check_in: str,
    check_out: str,
    include_breakdown: bool = True,
) -> dict[str, Any]:
    """Calculate the total cost for a stay with optional breakdown.

    Use this tool when a guest wants to know the final price
    or when preparing a booking summary. Includes all fees.

    Args:
        check_in: Check-in date in YYYY-MM-DD format (e.g., '2025-07-15')
        check_out: Check-out date in YYYY-MM-DD format (e.g., '2025-07-22')
        include_breakdown: Whether to include itemized breakdown (default: True)

    Returns:
        Dictionary with total amount and optional breakdown
    """
    logger.info("calculate_total called", extra={"check_in": check_in, "check_out": check_out, "include_breakdown": include_breakdown})
    try:
        start_date = _parse_date(check_in)
        end_date = _parse_date(check_out)
    except ValueError:
        return {
            "status": "error",
            "message": "Invalid date format. Please use YYYY-MM-DD format.",
        }

    if end_date <= start_date:
        return {
            "status": "error",
            "message": "Check-out date must be after check-in date.",
        }

    nights = (end_date - start_date).days

    # Get applicable pricing
    pricing = _get_applicable_pricing(start_date, end_date)
    if pricing is None:
        pricing = _get_default_pricing()

    # Check minimum nights
    if nights < pricing.minimum_nights:
        error = ToolError.from_code(
            ErrorCode.MINIMUM_NIGHTS_NOT_MET,
            details={
                "minimum_nights_required": str(pricing.minimum_nights),
                "nights_requested": str(nights),
            },
        )
        return error.model_dump()

    # Calculate amounts
    subtotal = pricing.nightly_rate * nights
    total = subtotal + pricing.cleaning_fee

    result: dict[str, Any] = {
        "status": "success",
        "check_in": check_in,
        "check_out": check_out,
        "total_eur": total / 100,
        "total_cents": total,
        "currency": "EUR",
    }

    if include_breakdown:
        result["breakdown"] = {
            "nights": nights,
            "nightly_rate_eur": pricing.nightly_rate / 100,
            "accommodation_eur": subtotal / 100,
            "cleaning_fee_eur": pricing.cleaning_fee / 100,
            "season": pricing.season_name,
        }
        result["message"] = (
            f"Total for your {nights}-night stay: €{total / 100:.2f}\n"
            f"• Accommodation: {nights} nights × €{pricing.nightly_rate / 100:.2f} = €{subtotal / 100:.2f}\n"
            f"• Cleaning fee: €{pricing.cleaning_fee / 100:.2f}"
        )
    else:
        result["message"] = f"Total: €{total / 100:.2f}"

    return result


@tool
def get_seasonal_rates() -> dict[str, Any]:
    """Get information about seasonal pricing and rates.

    Use this tool when a guest asks about general pricing,
    seasonal rates, or wants to know when prices are lower/higher.

    Returns:
        Dictionary with all seasonal rates and their periods
    """
    logger.info("get_seasonal_rates called")
    db = _get_db()

    # Query all pricing records
    # In production, filter by active status via GSI
    try:
        items = db.query(
            "pricing",
            Key("is_active").eq("true"),
            index_name="active-index",
        )
    except Exception:
        # If query fails (e.g., index doesn't exist), return defaults
        items = []

    if not items:
        # Return default seasonal structure
        return {
            "status": "success",
            "seasons": [
                {
                    "name": "Low Season",
                    "period": "November - March (excluding Christmas/New Year)",
                    "nightly_rate_eur": 100.00,
                    "minimum_nights": 3,
                },
                {
                    "name": "Mid Season",
                    "period": "April - June, September - October",
                    "nightly_rate_eur": 120.00,
                    "minimum_nights": 5,
                },
                {
                    "name": "High Season",
                    "period": "July - August",
                    "nightly_rate_eur": 150.00,
                    "minimum_nights": 7,
                },
                {
                    "name": "Peak Season",
                    "period": "Christmas, New Year, Easter",
                    "nightly_rate_eur": 180.00,
                    "minimum_nights": 7,
                },
            ],
            "cleaning_fee_eur": 50.00,
            "message": "Our rates vary by season. Low season offers the best value at €100/night, while peak periods are €180/night. All stays include a €50 cleaning fee.",
        }

    # Format actual pricing data
    seasons = []
    for item in items:
        seasons.append(
            {
                "name": item["season_name"],
                "start_date": item["start_date"],
                "end_date": item["end_date"],
                "nightly_rate_eur": int(item["nightly_rate"]) / 100,
                "minimum_nights": int(item["minimum_nights"]),
                "cleaning_fee_eur": int(item["cleaning_fee"]) / 100,
            }
        )

    # Sort by start date
    seasons.sort(key=lambda x: x["start_date"])

    return {
        "status": "success",
        "seasons": seasons,
        "message": f"We have {len(seasons)} seasonal rate periods. Let me know your dates and I can give you the exact price.",
    }


@tool
def check_minimum_stay(check_in: str, check_out: str) -> dict[str, Any]:
    """Check if a stay meets the minimum nights requirement for the season.

    Use this tool when a guest asks about minimum stay requirements,
    or to validate dates before proceeding with a booking.

    Args:
        check_in: Check-in date in YYYY-MM-DD format (e.g., '2025-07-15')
        check_out: Check-out date in YYYY-MM-DD format (e.g., '2025-07-22')

    Returns:
        Dictionary with validation result and minimum stay details
    """
    logger.info("check_minimum_stay called", extra={"check_in": check_in, "check_out": check_out})
    try:
        start_date = _parse_date(check_in)
        end_date = _parse_date(check_out)
    except ValueError:
        return {
            "status": "error",
            "message": "Invalid date format. Please use YYYY-MM-DD format.",
        }

    if end_date <= start_date:
        return {
            "status": "error",
            "message": "Check-out date must be after check-in date.",
        }

    nights = (end_date - start_date).days

    # Get applicable pricing for the check-in date
    pricing = _get_applicable_pricing(start_date, end_date)
    if pricing is None:
        pricing = _get_default_pricing()

    # Check if minimum nights requirement is met
    meets_minimum = nights >= pricing.minimum_nights

    if meets_minimum:
        return {
            "status": "success",
            "is_valid": True,
            "nights_requested": nights,
            "minimum_nights_required": pricing.minimum_nights,
            "season_name": pricing.season_name,
            "message": (
                f"Your {nights}-night stay meets the minimum requirement. "
                f"The minimum for {pricing.season_name} is {pricing.minimum_nights} nights."
            ),
        }
    else:
        # Calculate how many more nights needed
        additional_nights = pricing.minimum_nights - nights
        suggested_checkout = end_date + timedelta(days=additional_nights)

        return {
            "status": "error",
            "is_valid": False,
            "nights_requested": nights,
            "minimum_nights_required": pricing.minimum_nights,
            "additional_nights_needed": additional_nights,
            "season_name": pricing.season_name,
            "suggested_checkout": suggested_checkout.isoformat(),
            "message": (
                f"The minimum stay during {pricing.season_name} is {pricing.minimum_nights} nights. "
                f"You've selected {nights} night(s). Please add {additional_nights} more night(s), "
                f"or consider a checkout date of {suggested_checkout.strftime('%B %d, %Y')}."
            ),
        }


@tool
def get_minimum_stay_info(target_date: str) -> dict[str, Any]:
    """Get minimum stay requirement for a specific date.

    Use this tool when a guest asks about minimum stay requirements
    for a particular time of year without specific dates.

    Args:
        target_date: A date to check in YYYY-MM-DD format (e.g., '2025-07-15')

    Returns:
        Dictionary with minimum stay information for that season
    """
    logger.info("get_minimum_stay_info called", extra={"target_date": target_date})
    try:
        check_date = _parse_date(target_date)
    except ValueError:
        return {
            "status": "error",
            "message": "Invalid date format. Please use YYYY-MM-DD format.",
        }

    pricing = _get_applicable_pricing(check_date, check_date + timedelta(days=1))
    if pricing is None:
        pricing = _get_default_pricing()

    # Get all seasons to show comparison
    all_seasons = _get_all_seasons()
    season_minimums = [
        {"season": s.season_name, "minimum_nights": s.minimum_nights}
        for s in all_seasons
    ] if all_seasons else []

    return {
        "status": "success",
        "date": target_date,
        "season_name": pricing.season_name,
        "minimum_nights": pricing.minimum_nights,
        "nightly_rate_eur": pricing.nightly_rate / 100,
        "all_season_minimums": season_minimums,
        "message": (
            f"For {pricing.season_name} (around {check_date.strftime('%B %d')}), "
            f"the minimum stay is {pricing.minimum_nights} nights at €{pricing.nightly_rate / 100:.2f}/night."
        ),
    }
