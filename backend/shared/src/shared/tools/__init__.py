"""Quesada Apartment booking agent tools.

This module exports all tools available to the booking agent.
Tools are organized by category:
- Availability: check_availability, get_calendar
- Pricing: get_pricing, calculate_total, get_seasonal_rates, check_minimum_stay, get_minimum_stay_info
- Reservations: create_reservation, get_reservation, get_my_reservations, modify_reservation, cancel_reservation
- Payments: process_payment, get_payment_status, retry_payment
- Guest: get_guest_info, update_guest_details
- Area Info: get_area_info, get_recommendations
- Property: get_property_details, get_photos

Authentication: Handled automatically by @requires_access_token decorator on
booking/reservation tools. When an unauthenticated user attempts a protected
action, the decorator generates an OAuth2 authorization URL that is streamed
to the client. The frontend handles the OAuth2 login flow with Amplify.
"""

# Force rebuild: 2025-12-29T22:56:00Z
import logging

logger = logging.getLogger(__name__)
logger.info("[TOOLS] Loading tools module v3...")

from shared.tools.area_info import get_area_info, get_recommendations
from shared.tools.property import get_photos, get_property_details
from shared.tools.availability import check_availability, get_calendar
from shared.tools.guest import (
    get_guest_info,
    update_guest_details,
)
from shared.tools.payments import get_payment_status, process_payment, retry_payment
from shared.tools.pricing import (
    calculate_total,
    check_minimum_stay,
    get_minimum_stay_info,
    get_pricing,
    get_seasonal_rates,
)
from shared.tools.reservations import (
    cancel_reservation,
    create_reservation,
    get_my_reservations,
    get_reservation,
    modify_reservation,
    set_auth_url_queue,
)

# All tools for the booking agent
ALL_TOOLS = [
    # Availability tools
    check_availability,
    get_calendar,
    # Pricing tools
    get_pricing,
    calculate_total,
    get_seasonal_rates,
    check_minimum_stay,
    get_minimum_stay_info,
    # Reservation tools (auth handled by @requires_access_token decorator)
    create_reservation,
    get_reservation,
    get_my_reservations,
    modify_reservation,
    cancel_reservation,
    # Payment tools
    process_payment,
    get_payment_status,
    retry_payment,
    # Guest profile tools
    get_guest_info,
    update_guest_details,
    # Area info tools
    get_area_info,
    get_recommendations,
    # Property tools
    get_property_details,
    get_photos,
]

logger.info(f"[TOOLS] ALL_TOOLS loaded with {len(ALL_TOOLS)} tools")
for i, tool in enumerate(ALL_TOOLS):
    logger.info(f"[TOOLS]   {i+1}. {tool.__name__}")

__all__ = [
    # Tool functions
    "check_availability",
    "get_calendar",
    "get_pricing",
    "calculate_total",
    "get_seasonal_rates",
    "check_minimum_stay",
    "get_minimum_stay_info",
    "create_reservation",
    "get_reservation",
    "get_my_reservations",
    "modify_reservation",
    "cancel_reservation",
    "process_payment",
    "get_payment_status",
    "retry_payment",
    "get_guest_info",
    "update_guest_details",
    "get_area_info",
    "get_recommendations",
    "get_property_details",
    "get_photos",
    # Auth queue setup for @requires_access_token callbacks
    "set_auth_url_queue",
    # Tool collection
    "ALL_TOOLS",
]
