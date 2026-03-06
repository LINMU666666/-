#!/usr/bin/env python3
"""
Unit tests for the monthly activity report generator.
"""

import unittest
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from monthly_report import ActivityReportGenerator


class TestActivityReportGenerator(unittest.TestCase):
    """Test cases for ActivityReportGenerator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.generator_zh = ActivityReportGenerator(language='zh')
        self.generator_en = ActivityReportGenerator(language='en')
    
    def test_initialization_chinese(self):
        """Test initialization with Chinese language."""
        self.assertEqual(self.generator_zh.language, 'zh')
        self.assertEqual(self.generator_zh.repo_path, '.')
    
    def test_initialization_english(self):
        """Test initialization with English language."""
        self.assertEqual(self.generator_en.language, 'en')
        self.assertEqual(self.generator_en.repo_path, '.')
    
    def test_translation_chinese(self):
        """Test Chinese translations."""
        self.assertEqual(self.generator_zh.t('title'), '月度活动报告')
        self.assertEqual(self.generator_zh.t('total_commits'), '总提交次数')
        self.assertEqual(self.generator_zh.t('authors'), '贡献者')
    
    def test_translation_english(self):
        """Test English translations."""
        self.assertEqual(self.generator_en.t('title'), 'Monthly Activity Report')
        self.assertEqual(self.generator_en.t('total_commits'), 'Total Commits')
        self.assertEqual(self.generator_en.t('authors'), 'Contributors')
    
    def test_parse_git_log_empty(self):
        """Test parsing empty git log."""
        self.generator_zh.parse_git_log("")
        self.assertEqual(len(self.generator_zh.commits), 0)
        self.assertEqual(len(self.generator_zh.authors), 0)
    
    def test_parse_git_log_with_commits(self):
        """Test parsing git log with commits."""
        sample_log = """COMMIT:abc123|John Doe|2026-02-01 10:00:00 +0000|Initial commit
10	5	README.md
20	3	main.py

COMMIT:def456|Jane Smith|2026-02-02 11:00:00 +0000|Add feature
15	0	feature.py"""
        
        self.generator_zh.parse_git_log(sample_log)
        
        self.assertEqual(len(self.generator_zh.commits), 2)
        self.assertEqual(self.generator_zh.authors['John Doe'], 1)
        self.assertEqual(self.generator_zh.authors['Jane Smith'], 1)
        self.assertEqual(len(self.generator_zh.file_changes), 3)
        
        # Check file stats
        self.assertEqual(self.generator_zh.file_changes['README.md']['additions'], 10)
        self.assertEqual(self.generator_zh.file_changes['README.md']['deletions'], 5)
        self.assertEqual(self.generator_zh.file_changes['main.py']['additions'], 20)
        self.assertEqual(self.generator_zh.file_changes['feature.py']['additions'], 15)
    
    def test_parse_git_log_binary_files(self):
        """Test parsing git log with binary files."""
        sample_log = """COMMIT:abc123|John Doe|2026-02-01 10:00:00 +0000|Add image
-	-	image.png
10	5	README.md"""
        
        self.generator_zh.parse_git_log(sample_log)
        
        # Binary files should have 0 additions/deletions
        self.assertEqual(self.generator_zh.file_changes['image.png']['additions'], 0)
        self.assertEqual(self.generator_zh.file_changes['image.png']['deletions'], 0)
        # But still tracked
        self.assertEqual(self.generator_zh.file_changes['image.png']['commits'], 1)
    
    def test_generate_text_report_format(self):
        """Test text report format generation."""
        # Mock git log
        with patch.object(self.generator_zh, 'get_git_log', return_value=""):
            report = self.generator_zh.generate_report(format='text')
            self.assertIn('没有找到提交记录', report)
    
    def test_generate_markdown_report_format(self):
        """Test markdown report format generation."""
        # Mock git log
        with patch.object(self.generator_en, 'get_git_log', return_value=""):
            report = self.generator_en.generate_report(format='markdown')
            self.assertIn('No commits found', report)
    
    def test_report_with_data(self):
        """Test report generation with actual data."""
        sample_log = """COMMIT:abc123|John Doe|2026-02-01 10:00:00 +0000|Test commit
10	5	test.py"""
        
        with patch.object(self.generator_zh, 'get_git_log', return_value=sample_log):
            report = self.generator_zh.generate_report(format='text')
            
            # Check report contains expected elements
            self.assertIn('月度活动报告', report)
            self.assertIn('总提交次数: 1', report)
            self.assertIn('John Doe', report)
            self.assertIn('test.py', report)
    
    def test_date_range_handling(self):
        """Test handling of custom date ranges."""
        start_date = datetime(2026, 1, 1)
        end_date = datetime(2026, 2, 1)
        
        with patch.object(self.generator_zh, 'get_git_log', return_value="") as mock:
            self.generator_zh.generate_report(since_date=start_date, until_date=end_date)
            # Verify get_git_log was called with correct dates
            mock.assert_called_once_with(start_date, end_date)
    
    def test_statistics_calculation(self):
        """Test statistics calculation."""
        sample_log = """COMMIT:abc123|John Doe|2026-02-01 10:00:00 +0000|Commit 1
100	50	file1.py
200	30	file2.py

COMMIT:def456|Jane Smith|2026-02-02 11:00:00 +0000|Commit 2
50	20	file1.py"""
        
        with patch.object(self.generator_en, 'get_git_log', return_value=sample_log):
            report = self.generator_en.generate_report(format='text')
            
            # Total additions should be 100 + 200 + 50 = 350
            self.assertIn('350', report)
            # Total deletions should be 50 + 30 + 20 = 100
            self.assertIn('100', report)
            # 2 commits
            self.assertIn('Total Commits: 2', report)
            # 2 files changed
            self.assertIn('Files Changed: 2', report)
    
    def test_top_files_sorting(self):
        """Test that top files are sorted correctly."""
        sample_log = """COMMIT:abc123|John Doe|2026-02-01 10:00:00 +0000|Test
10	5	small.py
100	50	large.py
50	25	medium.py"""
        
        self.generator_zh.parse_git_log(sample_log)
        
        # Get sorted files
        sorted_files = sorted(
            self.generator_zh.file_changes.items(),
            key=lambda x: x[1]['additions'] + x[1]['deletions'],
            reverse=True
        )
        
        # large.py should be first (150 total changes)
        self.assertEqual(sorted_files[0][0], 'large.py')
        # medium.py should be second (75 total changes)
        self.assertEqual(sorted_files[1][0], 'medium.py')
        # small.py should be third (15 total changes)
        self.assertEqual(sorted_files[2][0], 'small.py')


def run_tests():
    """Run all unit tests."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestActivityReportGenerator)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
