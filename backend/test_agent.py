#!/usr/bin/env python3
"""Quick test script for the Quesada Apartment booking agent."""

from src.agent import create_booking_agent


def main() -> None:
    """Test the booking agent with a simple conversation."""
    print("Creating Quesada Apartment booking agent...")
    agent = create_booking_agent()

    print("\n" + "=" * 60)
    print("Testing agent with a greeting...")
    print("=" * 60 + "\n")

    # Test 1: Simple greeting
    response = agent("Hi! I'm interested in booking a stay at your beach house.")
    print(f"User: Hi! I'm interested in booking a stay at your beach house.\n")
    print(f"Agent: {response.message}\n")

    print("\n" + "=" * 60)
    print("Testing agent with availability question...")
    print("=" * 60 + "\n")

    # Test 2: Availability question (agent has no tools yet, should explain gracefully)
    response = agent("Do you have availability in January 2025?")
    print(f"User: Do you have availability in January 2025?\n")
    print(f"Agent: {response.message}\n")

    print("\n" + "=" * 60)
    print("Testing Spanish language support...")
    print("=" * 60 + "\n")

    # Test 3: Spanish language
    response = agent("Hola, me gustaría saber más sobre la casa de playa.")
    print(f"User: Hola, me gustaría saber más sobre la casa de playa.\n")
    print(f"Agent: {response.message}\n")

    print("\n" + "=" * 60)
    print("Agent test complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
