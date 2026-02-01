#!/usr/bin/env python3
"""
Unit tests for the card detection system.
Tests core functionality without requiring display access.
"""

import unittest
import numpy as np
from collections import defaultdict
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path to import card_detector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from card_detector import CardDetector


class TestCardDetector(unittest.TestCase):
    """Test cases for CardDetector class."""
    
    @patch('card_detector.mss')
    def setUp(self, mock_mss):
        """Set up test fixtures."""
        # Mock the mss screen capture
        mock_mss.return_value = MagicMock()
        self.detector = CardDetector(update_interval=1.0, monitor_number=1)
    
    def test_initialization(self):
        """Test CardDetector initialization."""
        self.assertEqual(self.detector.update_interval, 1.0)
        self.assertEqual(self.detector.monitor_number, 1)
        self.assertIsInstance(self.detector.card_counts, defaultdict)
        self.assertEqual(self.detector.total_frames_processed, 0)
        self.assertEqual(self.detector.total_cards_detected, 0)
    
    def test_reset_frame_stats(self):
        """Test frame statistics reset."""
        self.detector.total_frames_processed = 10
        self.detector.reset_frame_stats()
        # Should maintain cumulative stats
        self.assertEqual(self.detector.total_frames_processed, 10)
    
    def test_identify_card_type_red_card(self):
        """Test card type identification for red cards."""
        # Create a red-ish image (BGR format)
        red_roi = np.ones((100, 100, 3), dtype=np.uint8)
        red_roi[:, :, 0] = 50  # B
        red_roi[:, :, 1] = 50  # G
        red_roi[:, :, 2] = 200  # R
        
        card_type = self.detector._identify_card_type(red_roi)
        self.assertEqual(card_type, 'heart_or_diamond')
    
    def test_identify_card_type_black_card(self):
        """Test card type identification for black cards."""
        # Create a black-ish image
        black_roi = np.ones((100, 100, 3), dtype=np.uint8) * 30
        
        card_type = self.detector._identify_card_type(black_roi)
        self.assertEqual(card_type, 'spade_or_club')
    
    def test_identify_card_type_empty_roi(self):
        """Test card type identification with empty ROI."""
        empty_roi = np.array([])
        
        card_type = self.detector._identify_card_type(empty_roi)
        self.assertIsNone(card_type)
    
    def test_detect_cards_in_frame(self):
        """Test card detection in a frame."""
        # Create a simple test frame with a rectangular object
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Draw a white rectangle (simulating a card)
        frame[100:300, 100:250] = [255, 255, 255]
        
        detected_cards = self.detector.detect_cards_in_frame(frame)
        
        # Should return a dict (may or may not detect based on thresholds)
        self.assertIsInstance(detected_cards, defaultdict)
    
    def test_statistics_tracking(self):
        """Test that statistics are properly tracked."""
        # Manually update statistics
        self.detector.card_counts['heart_or_diamond'] = 5
        self.detector.card_counts['spade_or_club'] = 3
        self.detector.total_cards_detected = 8
        self.detector.total_frames_processed = 10
        
        # Verify counts
        self.assertEqual(self.detector.card_counts['heart_or_diamond'], 5)
        self.assertEqual(self.detector.card_counts['spade_or_club'], 3)
        self.assertEqual(self.detector.total_cards_detected, 8)
        self.assertEqual(self.detector.total_frames_processed, 10)
    
    def test_card_types_defined(self):
        """Test that card types are properly defined."""
        self.assertIn('spade', self.detector.card_types)
        self.assertIn('heart', self.detector.card_types)
        self.assertIn('diamond', self.detector.card_types)
        self.assertIn('club', self.detector.card_types)
    
    @patch('card_detector.mss')
    def test_custom_update_interval(self, mock_mss):
        """Test custom update interval."""
        mock_mss.return_value = MagicMock()
        detector = CardDetector(update_interval=2.5)
        self.assertEqual(detector.update_interval, 2.5)
    
    @patch('card_detector.mss')
    def test_custom_monitor_number(self, mock_mss):
        """Test custom monitor number."""
        mock_mss.return_value = MagicMock()
        detector = CardDetector(monitor_number=2)
        self.assertEqual(detector.monitor_number, 2)


class TestCardDetectionLogic(unittest.TestCase):
    """Test card detection logic with various scenarios."""
    
    @patch('card_detector.mss')
    def setUp(self, mock_mss):
        """Set up test fixtures."""
        mock_mss.return_value = MagicMock()
        self.detector = CardDetector()
    
    def test_color_based_detection_various_colors(self):
        """Test color-based detection with various color inputs."""
        # Test with different color scenarios (BGR format)
        test_cases = [
            (np.array([[[50, 50, 200]]]), 'heart_or_diamond'),  # Red (BGR)
            (np.array([[[30, 30, 30]]]), 'spade_or_club'),  # Black
            (np.array([[[100, 100, 100]]]), 'unknown_card'),  # Gray
        ]
        
        for roi, expected_type in test_cases:
            result = self.detector._identify_card_type(roi)
            self.assertEqual(result, expected_type, 
                           f"Failed for ROI with avg color {np.mean(roi, axis=(0,1))}")
    
    def test_frame_processing_increments_counter(self):
        """Test that frame processing increments the counter."""
        initial_count = self.detector.total_frames_processed
        
        # Create a dummy frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        self.detector.detect_cards_in_frame(frame)
        
        # Counter should not increment just from detection
        # (it increments in capture_and_process_frame)
        self.assertEqual(self.detector.total_frames_processed, initial_count)


def run_tests():
    """Run all unit tests."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(TestCardDetector))
    suite.addTests(loader.loadTestsFromTestCase(TestCardDetectionLogic))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
