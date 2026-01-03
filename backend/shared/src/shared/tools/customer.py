"""Customer verification tools for email-based authentication.

These tools handle customer identity verification using one-time codes
sent to email addresses. This implements passwordless authentication
for the booking flow.
"""

import logging
import random
import string
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from strands import tool

logger = logging.getLogger(__name__)

from shared.models.errors import ErrorCode, ToolError
from shared.services.dynamodb import DynamoDBService, get_dynamodb_service


def _get_db() -> DynamoDBService:
    """Get shared DynamoDB service instance (singleton for performance)."""
    return get_dynamodb_service()


def _generate_verification_code() -> str:
    """Generate a 6-digit verification code."""
    return "".join(random.choices(string.digits, k=6))


def _generate_customer_id() -> str:
    """Generate a unique customer ID."""
    return str(uuid.uuid4())


def _find_customer_by_email(db: DynamoDBService, email: str) -> dict[str, Any] | None:
    """Find a customer by email using the GSI.

    The customers table uses customer_id as the partition key with an email-index GSI.
    We must query the GSI to find customers by email.
    """
    from boto3.dynamodb.conditions import Key

    try:
        results = db.query(
            "customers",
            Key("email").eq(email),
            index_name="email-index",
        )
        return results[0] if results else None
    except Exception:
        return None


@tool
def initiate_verification(email: str) -> dict[str, Any]:
    """Send a verification code to the customer's email address.

    Use this tool when you need to verify a customer's identity before
    creating a reservation. This is required before any booking can
    be confirmed.

    The verification code is sent to the provided email address and
    expires in 10 minutes.

    NOTE: This is a mock implementation - in production, integrate
    with Amazon SES or Cognito passwordless auth.

    Args:
        email: Customer's email address (e.g., 'customer@example.com')

    Returns:
        Dictionary with verification status and next steps
    """
    logger.info("initiate_verification called", extra={"email": email})
    # Basic email validation
    email = email.strip().lower()
    if not email or "@" not in email or "." not in email:
        return {
            "status": "error",
            "code": "INVALID_EMAIL",
            "message": "Please provide a valid email address.",
        }

    db = _get_db()

    # Generate verification code
    code = _generate_verification_code()
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=10)

    # Store verification code with TTL
    verification_record = {
        "email": email,
        "code": code,
        "created_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
        "ttl": int(expires_at.timestamp()),  # DynamoDB TTL
        "attempts": 0,
        "verified": False,
    }

    db.put_item("verification_codes", verification_record)

    # MOCK: In production, send email via SES
    # For development, we log the code (would be removed in production)
    print(f"[MOCK EMAIL] Verification code for {email}: {code}")

    # Check if returning customer (query GSI)
    existing_customer = _find_customer_by_email(db, email)
    is_returning = existing_customer is not None

    return {
        "status": "success",
        "email": email,
        "is_returning_customer": is_returning,
        "expires_in_minutes": 10,
        "message": f"A verification code has been sent to {email}. The code will expire in 10 minutes.",
        "next_step": "Ask the customer to provide the verification code they received.",
        # Include code in dev mode for testing (remove in production)
        "_dev_code": code,
    }


@tool
def verify_code(email: str, code: str) -> dict[str, Any]:
    """Verify a customer's email using the code they received.

    Use this tool when a customer provides their verification code.
    Upon successful verification, a customer record is created or
    updated, and a customer_id is returned for use in reservations.

    Args:
        email: Customer's email address (must match the one used in initiate_verification)
        code: The 6-digit verification code received by email

    Returns:
        Dictionary with verification result and customer_id if successful
    """
    logger.info("verify_code called", extra={"email": email})
    email = email.strip().lower()
    code = code.strip()

    if not code or len(code) != 6 or not code.isdigit():
        return {
            "status": "error",
            "code": "INVALID_CODE_FORMAT",
            "message": "Please enter the code you received by email.",
        }

    db = _get_db()

    # Get verification record
    verification = db.get_item("verification_codes", {"email": email})

    if not verification:
        error = ToolError.from_code(
            ErrorCode.VERIFICATION_FAILED,
            details={"reason": "no_verification_found", "email": email},
        )
        return error.model_dump()

    # Check if already verified
    if verification.get("verified"):
        error = ToolError.from_code(
            ErrorCode.VERIFICATION_FAILED,
            details={"reason": "already_verified"},
        )
        return error.model_dump()

    # Check expiration
    expires_at = datetime.fromisoformat(verification["expires_at"])
    if datetime.now(timezone.utc) > expires_at.replace(tzinfo=timezone.utc):
        error = ToolError.from_code(
            ErrorCode.VERIFICATION_FAILED,
            details={"reason": "code_expired"},
        )
        return error.model_dump()

    # Check attempts (max 5 tries)
    attempts = verification.get("attempts", 0)
    if attempts >= 5:
        error = ToolError.from_code(
            ErrorCode.VERIFICATION_FAILED,
            details={"reason": "too_many_attempts", "attempts": str(attempts)},
        )
        return error.model_dump()

    # Verify code
    if verification["code"] != code:
        # Increment attempts
        db.update_item(
            "verification_codes",
            {"email": email},
            "SET attempts = :attempts",
            {":attempts": attempts + 1},
        )
        remaining = 5 - (attempts + 1)
        error = ToolError.from_code(
            ErrorCode.VERIFICATION_FAILED,
            details={"reason": "invalid_code", "remaining_attempts": str(remaining)},
        )
        return error.model_dump()

    # Mark as verified
    db.update_item(
        "verification_codes",
        {"email": email},
        "SET verified = :verified",
        {":verified": True},
    )

    now = datetime.now(timezone.utc)

    # Get or create customer record (query GSI)
    existing_customer = _find_customer_by_email(db, email)

    if existing_customer:
        # Update existing customer (PK is customer_id)
        customer_id = existing_customer["customer_id"]
        db.update_item(
            "customers",
            {"customer_id": customer_id},
            "SET email_verified = :verified, updated_at = :now",
            {":verified": True, ":now": now.isoformat()},
        )

        return {
            "status": "success",
            "customer_id": customer_id,
            "email": email,
            "is_returning_customer": True,
            "customer_name": existing_customer.get("name"),
            "total_previous_bookings": existing_customer.get("total_bookings", 0),
            "message": f"Welcome back! Your email has been verified. You have {existing_customer.get('total_bookings', 0)} previous bookings with us.",
        }
    else:
        # Create new customer
        customer_id = _generate_customer_id()
        customer_record = {
            "customer_id": customer_id,
            "email": email,
            "email_verified": True,
            "first_verified_at": now.isoformat(),
            "total_bookings": 0,
            "preferred_language": "en",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        db.put_item("customers", customer_record)

        return {
            "status": "success",
            "customer_id": customer_id,
            "email": email,
            "is_returning_customer": False,
            "message": "Your email has been verified! You can now proceed with your booking.",
            "next_step": "Would you like to provide your name and phone number for the reservation?",
        }


@tool
def get_customer_info(email: str) -> dict[str, Any]:
    """Get information about an existing customer by email.

    Use this tool to check if a customer has booked before and retrieve
    their stored preferences. This enables personalized service for
    returning customers.

    Args:
        email: Customer's email address

    Returns:
        Dictionary with customer info or indication that customer is new
    """
    logger.info("get_customer_info called", extra={"email": email})
    email = email.strip().lower()

    if not email or "@" not in email:
        return {
            "status": "error",
            "code": "INVALID_EMAIL",
            "message": "Please provide a valid email address.",
        }

    db = _get_db()

    # Query GSI to find customer by email
    customer = _find_customer_by_email(db, email)

    if not customer:
        return {
            "status": "not_found",
            "email": email,
            "is_returning_customer": False,
            "message": "This appears to be a new customer. Email verification will be required for booking.",
        }

    # Returning customer found
    return {
        "status": "success",
        "customer_id": customer["customer_id"],
        "email": email,
        "name": customer.get("name"),
        "phone": customer.get("phone"),
        "preferred_language": customer.get("preferred_language", "en"),
        "is_returning_customer": True,
        "email_verified": customer.get("email_verified", False),
        "total_bookings": customer.get("total_bookings", 0),
        "first_stay": customer.get("first_verified_at"),
        "message": f"Returning customer found! {customer.get('name') or 'Customer'} has made {customer.get('total_bookings', 0)} previous bookings.",
    }


@tool
def update_customer_details(
    customer_id: str,
    name: str | None = None,
    phone: str | None = None,
    preferred_language: str | None = None,
) -> dict[str, Any]:
    """Update a customer's profile information.

    Use this tool to save additional customer details like name and phone
    after they've been verified. This information is used for the
    reservation and future bookings.

    Args:
        customer_id: The verified customer's ID
        name: Full name of the customer (optional)
        phone: Phone number (optional)
        preferred_language: Language preference - 'en' or 'es' (optional)

    Returns:
        Dictionary with update status
    """
    logger.info("update_customer_details called", extra={"customer_id": customer_id})
    if not customer_id:
        return {
            "status": "error",
            "code": "MISSING_CUSTOMER_ID",
            "message": "Customer ID is required to update details.",
        }

    # Validate language if provided
    if preferred_language and preferred_language not in ("en", "es"):
        return {
            "status": "error",
            "code": "INVALID_LANGUAGE",
            "message": "Language must be 'en' (English) or 'es' (Spanish).",
        }

    db = _get_db()

    # Find customer by ID (customer_id is the partition key)
    customer = db.get_item("customers", {"customer_id": customer_id})
    if not customer:
        error = ToolError.from_code(
            ErrorCode.VERIFICATION_REQUIRED,
            details={"customer_id": customer_id},
        )
        return error.model_dump()

    # Build update expression
    update_parts = []
    expression_values: dict[str, Any] = {}

    if name:
        update_parts.append("name = :name")
        expression_values[":name"] = name.strip()

    if phone:
        update_parts.append("phone = :phone")
        expression_values[":phone"] = phone.strip()

    if preferred_language:
        update_parts.append("preferred_language = :lang")
        expression_values[":lang"] = preferred_language

    if not update_parts:
        return {
            "status": "error",
            "code": "NO_UPDATES",
            "message": "Please provide at least one field to update (name, phone, or language).",
        }

    # Add updated_at
    update_parts.append("updated_at = :now")
    expression_values[":now"] = datetime.now(timezone.utc).isoformat()

    update_expression = "SET " + ", ".join(update_parts)

    # Update customer record (PK is customer_id)
    db.update_item(
        "customers",
        {"customer_id": customer_id},
        update_expression,
        expression_values,
    )

    return {
        "status": "success",
        "customer_id": customer_id,
        "updated_fields": [k.replace(":", "") for k in expression_values if k != ":now"],
        "message": "Customer details updated successfully.",
    }
