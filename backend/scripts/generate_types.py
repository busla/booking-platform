#!/usr/bin/env python3
"""Generate TypeScript types from Pydantic models.

This script uses pydantic-to-typescript to generate TypeScript interfaces
from the backend Pydantic models. The generated types are written to
the frontend types directory.

Usage:
    python scripts/generate_types.py

Or via Taskfile:
    task types:generate
"""

import subprocess
import sys
from pathlib import Path


def main() -> int:
    """Generate TypeScript types from Pydantic models."""
    # Get project root directory
    script_dir = Path(__file__).parent
    backend_dir = script_dir.parent
    project_root = backend_dir.parent
    frontend_types_dir = project_root / "frontend" / "src" / "types"

    # Output file for generated types
    output_file = frontend_types_dir / "generated.ts"

    # Module containing Pydantic models
    models_module = "src.models"

    print(f"Generating TypeScript types from {models_module}...")
    print(f"Output: {output_file}")

    # Run pydantic2ts
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pydantic2ts",
                "--module",
                models_module,
                "--output",
                str(output_file),
                "--json2ts-cmd",
                "npx json2ts",
            ],
            cwd=backend_dir,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            print(f"Error generating types: {result.stderr}")
            # Fall back to JSON schema generation if json2ts is not available
            print("\nTrying JSON schema export instead...")
            return generate_json_schema_fallback(backend_dir, frontend_types_dir)

        print(result.stdout)
        print(f"Successfully generated TypeScript types at {output_file}")
        return 0

    except FileNotFoundError:
        print("pydantic2ts not found. Please install with: pip install pydantic-to-typescript")
        return 1


def generate_json_schema_fallback(backend_dir: Path, frontend_types_dir: Path) -> int:
    """Generate JSON Schema as fallback when json2ts is not available.

    This creates a JSON Schema file that can be used with online converters
    or other tools to generate TypeScript types.
    """
    import json
    import sys

    sys.path.insert(0, str(backend_dir))

    try:
        from src.models import (
            Availability,
            AvailabilityRange,
            AvailabilityResponse,
            Guest,
            GuestCreate,
            GuestUpdate,
            Payment,
            PaymentCreate,
            PaymentResult,
            PriceCalculation,
            Pricing,
            PricingCreate,
            Reservation,
            ReservationCreate,
            ReservationSummary,
            VerificationAttempt,
            VerificationCode,
            VerificationRequest,
            VerificationResult,
        )
    except ImportError as e:
        print(f"Error importing models: {e}")
        return 1

    # Collect all model schemas
    models = [
        Guest,
        GuestCreate,
        GuestUpdate,
        Reservation,
        ReservationCreate,
        ReservationSummary,
        Availability,
        AvailabilityRange,
        AvailabilityResponse,
        Pricing,
        PricingCreate,
        PriceCalculation,
        Payment,
        PaymentCreate,
        PaymentResult,
        VerificationCode,
        VerificationRequest,
        VerificationAttempt,
        VerificationResult,
    ]

    schemas = {}
    for model in models:
        try:
            schema = model.model_json_schema()
            schemas[model.__name__] = schema
        except Exception as e:
            print(f"Warning: Could not generate schema for {model.__name__}: {e}")

    # Write combined schema
    schema_file = frontend_types_dir / "models.schema.json"
    combined_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "definitions": schemas,
    }

    with open(schema_file, "w") as f:
        json.dump(combined_schema, f, indent=2)

    print(f"Generated JSON Schema at {schema_file}")
    print("\nTo convert to TypeScript, you can use:")
    print("  1. Install json-schema-to-typescript: npm install -g json-schema-to-typescript")
    print(f"  2. Run: json2ts -i {schema_file} -o {frontend_types_dir / 'generated.ts'}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
