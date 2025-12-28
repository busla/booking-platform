#!/usr/bin/env python3
"""Seed development database with test data.

This script populates DynamoDB tables with realistic test data for local
development and testing. Data is structured to test various scenarios:
- Seasonal pricing with different rates and minimum stays
- Sample availability records
- Test reservations and guests (optional)

Usage:
    python scripts/seed_data.py --env dev
    python scripts/seed_data.py --env dev --pricing-only
    python scripts/seed_data.py --env dev --clear-first

Or via Taskfile:
    task seed:dev
"""

import argparse
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import boto3  # noqa: E402


def get_table_name(env: str, table: str) -> str:
    """Get full table name with environment prefix."""
    return f"booking-{env}-{table}"


def create_seasonal_pricing(env: str) -> list[dict]:
    """Create realistic seasonal pricing data for 2025.

    Pricing structure for a vacation rental in Greece:
    - Low Season: Winter months (cheaper, shorter minimum stay)
    - Mid Season: Spring/Fall (moderate pricing)
    - High Season: Summer peak (premium pricing, longer minimum stay)
    - Peak Season: Holidays (highest pricing)
    """
    seasons = [
        {
            "season_id": "low-winter-2025",
            "season_name": "Low Season (Winter)",
            "start_date": "2025-01-01",
            "end_date": "2025-03-31",
            "nightly_rate": 8000,  # €80.00
            "minimum_nights": 3,
            "cleaning_fee": 5000,  # €50.00
            "is_active": "true",  # DynamoDB string for GSI
        },
        {
            "season_id": "mid-spring-2025",
            "season_name": "Mid Season (Spring)",
            "start_date": "2025-04-01",
            "end_date": "2025-06-30",
            "nightly_rate": 10000,  # €100.00
            "minimum_nights": 5,
            "cleaning_fee": 5000,
            "is_active": "true",
        },
        {
            "season_id": "high-summer-2025",
            "season_name": "High Season (Summer)",
            "start_date": "2025-07-01",
            "end_date": "2025-08-31",
            "nightly_rate": 15000,  # €150.00
            "minimum_nights": 7,
            "cleaning_fee": 6000,  # €60.00
            "is_active": "true",
        },
        {
            "season_id": "mid-fall-2025",
            "season_name": "Mid Season (Fall)",
            "start_date": "2025-09-01",
            "end_date": "2025-11-30",
            "nightly_rate": 10000,  # €100.00
            "minimum_nights": 5,
            "cleaning_fee": 5000,
            "is_active": "true",
        },
        {
            "season_id": "peak-christmas-2025",
            "season_name": "Peak Season (Christmas & New Year)",
            "start_date": "2025-12-01",
            "end_date": "2025-12-31",
            "nightly_rate": 18000,  # €180.00
            "minimum_nights": 7,
            "cleaning_fee": 6000,
            "is_active": "true",
        },
        # 2026 seasons for cross-year bookings
        {
            "season_id": "low-winter-2026",
            "season_name": "Low Season (Winter)",
            "start_date": "2026-01-01",
            "end_date": "2026-03-31",
            "nightly_rate": 8500,  # €85.00 (slight increase)
            "minimum_nights": 3,
            "cleaning_fee": 5000,
            "is_active": "true",
        },
    ]

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(get_table_name(env, "pricing"))

    print(f"Seeding pricing table: {table.name}")

    for season in seasons:
        table.put_item(Item=season)
        rate_eur = season["nightly_rate"] / 100
        print(f"  ✓ {season['season_name']}: €{rate_eur:.2f}/night, min {season['minimum_nights']} nights")

    return seasons


def create_sample_availability(env: str) -> list[dict]:
    """Create sample availability records.

    Sets up availability for the next 6 months with some blocked dates
    to simulate existing bookings.
    """
    from datetime import timedelta

    # Start from today
    today = date.today()

    # Sample blocked periods (existing bookings)
    blocked_periods = [
        # Week blocked in 2 weeks
        {
            "start": today + timedelta(days=14),
            "end": today + timedelta(days=21),
            "reason": "Booked - Guest: Smith Family",
        },
        # Long weekend blocked in 1 month
        {
            "start": today + timedelta(days=30),
            "end": today + timedelta(days=33),
            "reason": "Booked - Guest: Johnson",
        },
        # Two weeks in summer (July 15-28)
        {
            "start": date(2025, 7, 15),
            "end": date(2025, 7, 28),
            "reason": "Booked - Guest: Williams Family",
        },
    ]

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(get_table_name(env, "availability"))

    print(f"Seeding availability table: {table.name}")

    records = []
    for period in blocked_periods:
        record = {
            "date_range": f"{period['start'].isoformat()}#{period['end'].isoformat()}",
            "start_date": period["start"].isoformat(),
            "end_date": period["end"].isoformat(),
            "is_available": False,
            "reason": period["reason"],
        }
        table.put_item(Item=record)
        records.append(record)
        print(f"  ✓ Blocked: {period['start']} to {period['end']} ({period['reason']})")

    return records


def create_sample_guests(env: str) -> list[dict]:
    """Create sample guest records for testing."""
    import uuid

    guests = [
        {
            "guest_id": str(uuid.uuid4()),
            "email": "john.smith@example.com",
            "first_name": "John",
            "last_name": "Smith",
            "phone": "+1-555-0101",
            "country": "US",
            "is_verified": True,
            "verification_method": "email",
            "created_at": "2025-01-15T10:30:00Z",
        },
        {
            "guest_id": str(uuid.uuid4()),
            "email": "maria.garcia@example.com",
            "first_name": "Maria",
            "last_name": "Garcia",
            "phone": "+34-600-123456",
            "country": "ES",
            "is_verified": True,
            "verification_method": "phone",
            "created_at": "2025-02-01T14:20:00Z",
        },
        {
            "guest_id": str(uuid.uuid4()),
            "email": "test.user@example.com",
            "first_name": "Test",
            "last_name": "User",
            "phone": "+44-7700-900123",
            "country": "GB",
            "is_verified": False,
            "verification_method": None,
            "created_at": "2025-02-20T09:00:00Z",
        },
    ]

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(get_table_name(env, "guests"))

    print(f"Seeding guests table: {table.name}")

    for guest in guests:
        table.put_item(Item=guest)
        status = "✓" if guest["is_verified"] else "○"
        print(f"  {status} {guest['first_name']} {guest['last_name']} ({guest['email']})")

    return guests


def clear_table(env: str, table_name: str) -> int:
    """Clear all items from a table.

    Returns:
        Number of items deleted
    """
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(get_table_name(env, table_name))

    # Scan and delete all items
    response = table.scan()
    items = response.get("Items", [])

    # Get key schema to determine primary key attributes
    key_attrs = [k["AttributeName"] for k in table.key_schema]

    with table.batch_writer() as batch:
        for item in items:
            key = {k: item[k] for k in key_attrs if k in item}
            batch.delete_item(Key=key)

    # Handle pagination for large tables
    while response.get("LastEvaluatedKey"):
        response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        items.extend(response.get("Items", []))
        with table.batch_writer() as batch:
            for item in response.get("Items", []):
                key = {k: item[k] for k in key_attrs if k in item}
                batch.delete_item(Key=key)

    return len(items)


def main() -> int:
    """Run the seed script."""
    parser = argparse.ArgumentParser(description="Seed development database with test data")
    parser.add_argument(
        "--env",
        choices=["dev", "staging", "prod"],
        default="dev",
        help="Target environment (default: dev)",
    )
    parser.add_argument(
        "--pricing-only",
        action="store_true",
        help="Only seed pricing data",
    )
    parser.add_argument(
        "--clear-first",
        action="store_true",
        help="Clear existing data before seeding",
    )
    parser.add_argument(
        "--skip-guests",
        action="store_true",
        help="Skip seeding guest data",
    )

    args = parser.parse_args()

    # Safety check for production
    if args.env == "prod":
        confirm = input("⚠️  WARNING: You are about to modify PRODUCTION data. Type 'yes' to continue: ")
        if confirm.lower() != "yes":
            print("Aborted.")
            return 1

    print(f"\n🌱 Seeding {args.env} environment\n")

    # Optionally clear existing data
    if args.clear_first:
        print("Clearing existing data...")
        tables = ["pricing"] if args.pricing_only else ["pricing", "availability", "guests"]
        for table in tables:
            try:
                count = clear_table(args.env, table)
                print(f"  Cleared {count} items from {table}")
            except Exception as e:
                print(f"  Could not clear {table}: {e}")
        print()

    # Seed pricing (always)
    try:
        create_seasonal_pricing(args.env)
    except Exception as e:
        print(f"  ❌ Failed to seed pricing: {e}")
        return 1

    if args.pricing_only:
        print("\n✅ Pricing seeded successfully!")
        return 0

    # Seed availability
    print()
    try:
        create_sample_availability(args.env)
    except Exception as e:
        print(f"  ❌ Failed to seed availability: {e}")
        # Non-fatal, continue

    # Seed guests (optional)
    if not args.skip_guests:
        print()
        try:
            create_sample_guests(args.env)
        except Exception as e:
            print(f"  ❌ Failed to seed guests: {e}")
            # Non-fatal, continue

    print("\n✅ Seed completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
