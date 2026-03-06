#!/usr/bin/env python3
"""
Demo script showing how to use the card detection system programmatically.
This can be used as a starting point for custom implementations.
"""

from card_detector import CardDetector
import time


def demo_basic_usage():
    """Basic usage example - run for 5 seconds."""
    print("Demo 1: Basic Usage")
    print("-" * 60)
    
    detector = CardDetector(update_interval=1.0)
    detector.run(duration=5)


def demo_fast_updates():
    """Fast updates example - update every 0.5 seconds."""
    print("\nDemo 2: Fast Updates")
    print("-" * 60)
    
    detector = CardDetector(update_interval=0.5)
    detector.run(duration=3)


def demo_custom_monitor():
    """Custom monitor example - useful for multi-monitor setups."""
    print("\nDemo 3: Custom Monitor Selection")
    print("-" * 60)
    print("Note: Set monitor_number=2 for second monitor, etc.")
    
    # For this demo, we'll use monitor 1 (primary)
    detector = CardDetector(
        update_interval=1.0,
        monitor_number=1
    )
    detector.run(duration=5)


def demo_programmatic_access():
    """
    Programmatic access example - shows how to use the detector
    in your own code with custom logic.
    """
    print("\nDemo 4: Programmatic Access")
    print("-" * 60)
    
    detector = CardDetector(update_interval=2.0)
    
    # You can access detector properties and methods
    print(f"Update interval: {detector.update_interval}s")
    print(f"Monitor: {detector.monitor_number}")
    print(f"Initial cards detected: {detector.total_cards_detected}")
    
    # Run the detector
    detector.run(duration=5)
    
    # Access final statistics
    print("\nFinal results:")
    print(f"Total frames: {detector.total_frames_processed}")
    print(f"Total cards: {detector.total_cards_detected}")
    print(f"Card breakdown: {dict(detector.card_counts)}")


if __name__ == '__main__':
    print("="*60)
    print("Card Detection System - Demo Examples")
    print("="*60)
    print("\nNote: These demos require a display/screen to work.")
    print("In headless environments, they will fail with '$DISPLAY not set'")
    print("\nPress Ctrl+C at any time to stop a demo.\n")
    
    try:
        # Run each demo
        # Uncomment the demos you want to run
        
        # demo_basic_usage()
        # demo_fast_updates()
        # demo_custom_monitor()
        # demo_programmatic_access()
        
        print("\nTo run demos, uncomment the desired demo function calls")
        print("in the __main__ section of this script.\n")
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\n\nError running demo: {e}")
        print("Note: Screen capture requires a display server to be running.")
