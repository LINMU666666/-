#!/usr/bin/env python3
"""
Real-time Card Detection System
Monitors computer screen for card game interactions and tracks card appearances.
"""

import time
import cv2
import numpy as np
from mss import mss
from collections import defaultdict
from datetime import datetime


class CardDetector:
    """
    Real-time card detection system for monitoring game interactions.
    Captures screen continuously and analyzes card patterns.
    """
    
    def __init__(self, update_interval=1.0, monitor_number=1):
        """
        Initialize the card detector.
        
        Args:
            update_interval: Time in seconds between statistics updates (default: 1.0)
            monitor_number: Which monitor to capture (default: 1 for primary)
        """
        self.update_interval = update_interval
        self.monitor_number = monitor_number
        self.sct = mss()
        
        # Card detection statistics
        self.card_counts = defaultdict(int)
        self.total_frames_processed = 0
        self.total_cards_detected = 0
        self.session_start_time = None
        
        # Card type definitions (can be customized based on game)
        self.card_types = {
            'spade': {'color_range': ([0, 0, 0], [50, 50, 50])},
            'heart': {'color_range': ([0, 0, 150], [100, 100, 255])},
            'diamond': {'color_range': ([0, 0, 150], [100, 100, 255])},
            'club': {'color_range': ([0, 0, 0], [50, 50, 50])},
        }
        
        # Performance tracking
        self.last_update_time = None
        self.fps_counter = 0
        self.current_fps = 0
        
    def reset_frame_stats(self):
        """
        Reset per-frame statistics while maintaining cumulative data.
        
        This method is called after each statistics update interval.
        Currently maintains all cumulative statistics (card_counts, total_cards_detected, etc.)
        Can be extended in the future to reset per-interval metrics if needed.
        """
        # Currently, we maintain all cumulative statistics across the session
        # This method is a placeholder for future per-interval stat tracking
        pass
    
    def detect_cards_in_frame(self, frame):
        """
        Detect and identify cards in the current frame.
        
        Args:
            frame: numpy array representing the captured screen
            
        Returns:
            dict: Detected card types and their counts in this frame
        """
        frame_card_counts = defaultdict(int)
        
        # Convert to different color spaces for analysis
        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply edge detection to find potential card boundaries
        edges = cv2.Canny(gray_frame, 50, 150)
        
        # Find contours (potential cards)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Analyze each potential card region
        for contour in contours:
            # Filter by area (cards should be reasonably sized)
            area = cv2.contourArea(contour)
            if area < 1000 or area > 100000:  # Adjust thresholds as needed
                continue
            
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)
            
            # Check aspect ratio (cards are typically rectangular)
            aspect_ratio = float(w) / h if h > 0 else 0
            if aspect_ratio < 0.5 or aspect_ratio > 0.8:  # Typical card ratio
                continue
            
            # Extract region of interest
            roi = frame[y:y+h, x:x+w]
            
            # Analyze colors in the region to determine card type
            card_type = self._identify_card_type(roi)
            if card_type:
                frame_card_counts[card_type] += 1
        
        return frame_card_counts
    
    def _identify_card_type(self, roi):
        """
        Identify the type of card based on color analysis.
        
        Args:
            roi: Region of interest containing a potential card
            
        Returns:
            str: Card type identifier or None
        """
        if roi.size == 0:
            return None
        
        # Calculate average color
        avg_color = np.mean(roi, axis=(0, 1))
        
        # Simple color-based classification
        # Red-ish cards (hearts, diamonds)
        if avg_color[2] > 150 and avg_color[0] < 100 and avg_color[1] < 100:
            return 'heart_or_diamond'
        # Black-ish cards (spades, clubs)
        elif avg_color[0] < 50 and avg_color[1] < 50 and avg_color[2] < 50:
            return 'spade_or_club'
        # Other patterns could be detected here
        else:
            return 'unknown_card'
    
    def capture_and_process_frame(self):
        """
        Capture a single frame from the screen and process it.
        
        Returns:
            tuple: (frame as numpy array, detected cards dict)
        """
        # Capture screen
        monitor = self.sct.monitors[self.monitor_number]
        screenshot = self.sct.grab(monitor)
        
        # Convert to numpy array
        frame = np.array(screenshot)
        
        # Convert from BGRA to BGR
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        
        # Detect cards in this frame
        detected_cards = self.detect_cards_in_frame(frame)
        
        # Update statistics
        self.total_frames_processed += 1
        for card_type, count in detected_cards.items():
            self.card_counts[card_type] += count
            self.total_cards_detected += count
        
        return frame, detected_cards
    
    def display_statistics(self):
        """Display current detection statistics."""
        current_time = time.time()
        elapsed_time = current_time - self.session_start_time if self.session_start_time else 0
        
        print("\n" + "="*60)
        print(f"Card Detection Statistics - {datetime.now().strftime('%H:%M:%S')}")
        print("="*60)
        print(f"Session Duration: {elapsed_time:.1f} seconds")
        print(f"Frames Processed: {self.total_frames_processed}")
        print(f"Current FPS: {self.current_fps:.1f}")
        print(f"Total Cards Detected: {self.total_cards_detected}")
        print("\nCard Type Breakdown:")
        print("-"*60)
        
        if self.card_counts:
            for card_type, count in sorted(self.card_counts.items()):
                percentage = (count / self.total_cards_detected * 100) if self.total_cards_detected > 0 else 0
                print(f"  {card_type:20s}: {count:5d} ({percentage:5.1f}%)")
        else:
            print("  No cards detected yet...")
        
        print("="*60)
    
    def run(self, duration=None):
        """
        Run the card detection system.
        
        Args:
            duration: How long to run in seconds (None = run indefinitely)
        """
        print("Starting Real-Time Card Detection System...")
        print(f"Monitoring: Monitor {self.monitor_number}")
        print(f"Update Interval: {self.update_interval} seconds")
        print("Press Ctrl+C to stop\n")
        
        self.session_start_time = time.time()
        self.last_update_time = self.session_start_time
        
        try:
            while True:
                # Check if we should stop
                if duration and (time.time() - self.session_start_time) >= duration:
                    break
                
                # Capture and process frame
                frame, detected_cards = self.capture_and_process_frame()
                
                # Update FPS counter
                self.fps_counter += 1
                
                # Check if it's time to display statistics
                current_time = time.time()
                time_since_update = current_time - self.last_update_time
                
                if time_since_update >= self.update_interval:
                    # Calculate FPS
                    self.current_fps = self.fps_counter / time_since_update
                    
                    # Display statistics
                    self.display_statistics()
                    
                    # Reset counters
                    self.last_update_time = current_time
                    self.fps_counter = 0
                    
                    # Reset per-frame statistics if needed
                    self.reset_frame_stats()
                
                # Small delay to prevent CPU overuse (adjust as needed)
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            print("\n\nStopping card detection system...")
        finally:
            # Display final statistics
            print("\n\nFinal Statistics:")
            self.display_statistics()
            print("\nSession ended.")


def main():
    """Main entry point for the card detection system."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Real-time card detection system for monitoring game interactions'
    )
    parser.add_argument(
        '--interval',
        type=float,
        default=1.0,
        help='Statistics update interval in seconds (default: 1.0)'
    )
    parser.add_argument(
        '--monitor',
        type=int,
        default=1,
        help='Monitor number to capture (default: 1 for primary monitor)'
    )
    parser.add_argument(
        '--duration',
        type=float,
        default=None,
        help='How long to run in seconds (default: run indefinitely)'
    )
    
    args = parser.parse_args()
    
    # Create and run detector
    detector = CardDetector(
        update_interval=args.interval,
        monitor_number=args.monitor
    )
    detector.run(duration=args.duration)


if __name__ == '__main__':
    main()
