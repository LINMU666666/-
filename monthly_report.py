#!/usr/bin/env python3
"""
Monthly Activity Report Generator
生成月度活动报告工具

Analyzes git repository history to generate comprehensive reports
of activities, commits, and changes over specified time periods.
"""

import subprocess
import argparse
from datetime import datetime, timedelta
from collections import defaultdict
import re
import sys


class ActivityReportGenerator:
    """
    Generates activity reports from git repository history.
    从git仓库历史生成活动报告
    """
    
    def __init__(self, repo_path='.', language='zh'):
        """
        Initialize the report generator.
        
        Args:
            repo_path: Path to git repository (default: current directory)
            language: Report language ('zh' for Chinese, 'en' for English)
        """
        self.repo_path = repo_path
        self.language = language
        self.commits = []
        self.file_changes = defaultdict(lambda: {'additions': 0, 'deletions': 0, 'commits': 0})
        self.authors = defaultdict(int)
        self.commit_messages = []
        
        # Translations
        self.translations = {
            'zh': {
                'title': '月度活动报告',
                'period': '时间范围',
                'summary': '概要统计',
                'total_commits': '总提交次数',
                'total_additions': '总增加行数',
                'total_deletions': '总删除行数',
                'files_changed': '修改文件数',
                'authors': '贡献者',
                'top_files': '修改最多的文件 (前10)',
                'file': '文件',
                'changes': '修改次数',
                'lines_changed': '行数变化',
                'commit_history': '提交历史',
                'date': '日期',
                'author': '作者',
                'message': '消息',
                'no_commits': '在指定时间范围内没有找到提交记录',
                'generated_at': '报告生成时间',
            },
            'en': {
                'title': 'Monthly Activity Report',
                'period': 'Time Period',
                'summary': 'Summary Statistics',
                'total_commits': 'Total Commits',
                'total_additions': 'Total Lines Added',
                'total_deletions': 'Total Lines Deleted',
                'files_changed': 'Files Changed',
                'authors': 'Contributors',
                'top_files': 'Top 10 Most Modified Files',
                'file': 'File',
                'changes': 'Changes',
                'lines_changed': 'Lines Changed',
                'commit_history': 'Commit History',
                'date': 'Date',
                'author': 'Author',
                'message': 'Message',
                'no_commits': 'No commits found in the specified time range',
                'generated_at': 'Report Generated',
            }
        }
    
    def t(self, key):
        """Get translation for a key."""
        return self.translations.get(self.language, self.translations['en']).get(key, key)
    
    def get_git_log(self, since_date=None, until_date=None):
        """
        Retrieve git log for specified date range.
        
        Args:
            since_date: Start date (datetime object or None for 1 month ago)
            until_date: End date (datetime object or None for now)
        """
        if since_date is None:
            since_date = datetime.now() - timedelta(days=30)
        if until_date is None:
            until_date = datetime.now()
        
        # Format dates for git
        since_str = since_date.strftime('%Y-%m-%d')
        until_str = until_date.strftime('%Y-%m-%d')
        
        # Get commit log with stats
        cmd = [
            'git', '-C', self.repo_path,
            'log', '--all',
            '--numstat',
            '--pretty=format:COMMIT:%H|%an|%ad|%s',
            '--date=iso',
            f'--since={since_str}',
            f'--until={until_str}'
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"Error running git command: {e}", file=sys.stderr)
            return ""
    
    def parse_git_log(self, log_output):
        """
        Parse git log output and extract statistics.
        
        Args:
            log_output: Output from git log command
        """
        lines = log_output.strip().split('\n')
        current_commit = None
        
        for line in lines:
            if line.startswith('COMMIT:'):
                # Parse commit info
                parts = line[7:].split('|')
                if len(parts) >= 4:
                    commit_hash = parts[0]
                    author = parts[1]
                    date = parts[2]
                    message = '|'.join(parts[3:])  # In case message contains |
                    
                    current_commit = {
                        'hash': commit_hash[:7],  # Short hash
                        'author': author,
                        'date': date,
                        'message': message,
                        'files': []
                    }
                    self.commits.append(current_commit)
                    self.authors[author] += 1
                    self.commit_messages.append(message)
            elif line.strip() and current_commit:
                # Parse file change stats
                parts = line.split('\t')
                if len(parts) == 3:
                    additions = parts[0]
                    deletions = parts[1]
                    filename = parts[2]
                    
                    # Handle binary files (marked as '-')
                    try:
                        add_count = int(additions) if additions != '-' else 0
                        del_count = int(deletions) if deletions != '-' else 0
                    except ValueError:
                        add_count = 0
                        del_count = 0
                    
                    self.file_changes[filename]['additions'] += add_count
                    self.file_changes[filename]['deletions'] += del_count
                    self.file_changes[filename]['commits'] += 1
                    
                    current_commit['files'].append({
                        'name': filename,
                        'additions': add_count,
                        'deletions': del_count
                    })
    
    def generate_report(self, since_date=None, until_date=None, format='text'):
        """
        Generate activity report.
        
        Args:
            since_date: Start date (datetime object or None)
            until_date: End date (datetime object or None)
            format: Output format ('text' or 'markdown')
        
        Returns:
            str: Formatted report
        """
        # Reset statistics
        self.commits = []
        self.file_changes = defaultdict(lambda: {'additions': 0, 'deletions': 0, 'commits': 0})
        self.authors = defaultdict(int)
        self.commit_messages = []
        
        # Get and parse log
        log_output = self.get_git_log(since_date, until_date)
        if not log_output.strip():
            return f"\n{self.t('no_commits')}\n"
        
        self.parse_git_log(log_output)
        
        # Generate report based on format
        if format == 'markdown':
            return self._generate_markdown_report(since_date, until_date)
        else:
            return self._generate_text_report(since_date, until_date)
    
    def _generate_text_report(self, since_date, until_date):
        """Generate plain text report."""
        if since_date is None:
            since_date = datetime.now() - timedelta(days=30)
        if until_date is None:
            until_date = datetime.now()
        
        lines = []
        width = 80
        
        # Header
        lines.append("=" * width)
        lines.append(self.t('title').center(width))
        lines.append("=" * width)
        lines.append("")
        
        # Time period
        lines.append(f"{self.t('period')}: {since_date.strftime('%Y-%m-%d')} → {until_date.strftime('%Y-%m-%d')}")
        lines.append(f"{self.t('generated_at')}: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # Summary statistics
        lines.append("-" * width)
        lines.append(self.t('summary'))
        lines.append("-" * width)
        
        total_additions = sum(f['additions'] for f in self.file_changes.values())
        total_deletions = sum(f['deletions'] for f in self.file_changes.values())
        
        lines.append(f"  {self.t('total_commits')}: {len(self.commits)}")
        lines.append(f"  {self.t('total_additions')}: {total_additions:,}")
        lines.append(f"  {self.t('total_deletions')}: {total_deletions:,}")
        lines.append(f"  {self.t('files_changed')}: {len(self.file_changes)}")
        lines.append(f"  {self.t('authors')}: {len(self.authors)}")
        lines.append("")
        
        # Top contributors
        if self.authors:
            lines.append("-" * width)
            lines.append(f"{self.t('authors')}:")
            lines.append("-" * width)
            for author, count in sorted(self.authors.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / len(self.commits) * 100) if self.commits else 0
                lines.append(f"  {author:30s}: {count:3d} {self.t('total_commits').lower()} ({percentage:5.1f}%)")
            lines.append("")
        
        # Top modified files
        if self.file_changes:
            lines.append("-" * width)
            lines.append(self.t('top_files'))
            lines.append("-" * width)
            
            sorted_files = sorted(
                self.file_changes.items(),
                key=lambda x: x[1]['additions'] + x[1]['deletions'],
                reverse=True
            )[:10]
            
            for filename, stats in sorted_files:
                total_changes = stats['additions'] + stats['deletions']
                lines.append(f"  {filename}")
                lines.append(f"    +{stats['additions']}, -{stats['deletions']} " +
                           f"({total_changes} {self.t('lines_changed').lower()}, " +
                           f"{stats['commits']} {self.t('changes').lower()})")
            lines.append("")
        
        # Recent commits
        if self.commits:
            lines.append("-" * width)
            lines.append(f"{self.t('commit_history')} ({len(self.commits)} {self.t('total_commits').lower()})")
            lines.append("-" * width)
            
            for commit in self.commits[:20]:  # Show last 20 commits
                date_str = commit['date'][:19]  # Get date without timezone
                lines.append(f"  [{commit['hash']}] {date_str}")
                lines.append(f"  {self.t('author')}: {commit['author']}")
                lines.append(f"  {self.t('message')}: {commit['message']}")
                if commit['files']:
                    lines.append(f"  {self.t('files_changed')}: {len(commit['files'])}")
                lines.append("")
        
        lines.append("=" * width)
        
        return '\n'.join(lines)
    
    def _generate_markdown_report(self, since_date, until_date):
        """Generate markdown format report."""
        if since_date is None:
            since_date = datetime.now() - timedelta(days=30)
        if until_date is None:
            until_date = datetime.now()
        
        lines = []
        
        # Header
        lines.append(f"# {self.t('title')}")
        lines.append("")
        lines.append(f"**{self.t('period')}:** {since_date.strftime('%Y-%m-%d')} → {until_date.strftime('%Y-%m-%d')}")
        lines.append(f"**{self.t('generated_at')}:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # Summary statistics
        lines.append(f"## {self.t('summary')}")
        lines.append("")
        
        total_additions = sum(f['additions'] for f in self.file_changes.values())
        total_deletions = sum(f['deletions'] for f in self.file_changes.values())
        
        lines.append(f"- **{self.t('total_commits')}:** {len(self.commits)}")
        lines.append(f"- **{self.t('total_additions')}:** {total_additions:,}")
        lines.append(f"- **{self.t('total_deletions')}:** {total_deletions:,}")
        lines.append(f"- **{self.t('files_changed')}:** {len(self.file_changes)}")
        lines.append(f"- **{self.t('authors')}:** {len(self.authors)}")
        lines.append("")
        
        # Top contributors
        if self.authors:
            lines.append(f"## {self.t('authors')}")
            lines.append("")
            lines.append(f"| {self.t('author')} | {self.t('total_commits')} | Percentage |")
            lines.append("|---|---:|---:|")
            for author, count in sorted(self.authors.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / len(self.commits) * 100) if self.commits else 0
                lines.append(f"| {author} | {count} | {percentage:.1f}% |")
            lines.append("")
        
        # Top modified files
        if self.file_changes:
            lines.append(f"## {self.t('top_files')}")
            lines.append("")
            lines.append(f"| {self.t('file')} | Additions | Deletions | {self.t('changes')} |")
            lines.append("|---|---:|---:|---:|")
            
            sorted_files = sorted(
                self.file_changes.items(),
                key=lambda x: x[1]['additions'] + x[1]['deletions'],
                reverse=True
            )[:10]
            
            for filename, stats in sorted_files:
                lines.append(f"| `{filename}` | +{stats['additions']} | -{stats['deletions']} | {stats['commits']} |")
            lines.append("")
        
        # Recent commits
        if self.commits:
            lines.append(f"## {self.t('commit_history')}")
            lines.append("")
            
            for commit in self.commits[:20]:  # Show last 20 commits
                date_str = commit['date'][:10]  # Get date only
                lines.append(f"### [{commit['hash']}] {commit['message']}")
                lines.append("")
                lines.append(f"- **{self.t('date')}:** {date_str}")
                lines.append(f"- **{self.t('author')}:** {commit['author']}")
                if commit['files']:
                    lines.append(f"- **{self.t('files_changed')}:** {len(commit['files'])}")
                lines.append("")
        
        return '\n'.join(lines)


def main():
    """Main entry point for the activity report generator."""
    parser = argparse.ArgumentParser(
        description='Generate activity reports from git repository history / 生成git仓库活动报告'
    )
    parser.add_argument(
        '--since',
        type=str,
        help='Start date (YYYY-MM-DD format, default: 30 days ago)'
    )
    parser.add_argument(
        '--until',
        type=str,
        help='End date (YYYY-MM-DD format, default: today)'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='Number of days to look back (default: 30, ignored if --since is provided)'
    )
    parser.add_argument(
        '--format',
        choices=['text', 'markdown'],
        default='text',
        help='Output format (default: text)'
    )
    parser.add_argument(
        '--language',
        '--lang',
        choices=['zh', 'en'],
        default='zh',
        help='Report language: zh (Chinese) or en (English) (default: zh)'
    )
    parser.add_argument(
        '--output',
        '-o',
        type=str,
        help='Output file path (default: print to stdout)'
    )
    parser.add_argument(
        '--repo',
        type=str,
        default='.',
        help='Path to git repository (default: current directory)'
    )
    
    args = parser.parse_args()
    
    # Parse dates
    since_date = None
    until_date = None
    
    if args.since:
        try:
            since_date = datetime.strptime(args.since, '%Y-%m-%d')
        except ValueError:
            print(f"Error: Invalid date format for --since: {args.since}", file=sys.stderr)
            sys.exit(1)
    else:
        since_date = datetime.now() - timedelta(days=args.days)
    
    if args.until:
        try:
            until_date = datetime.strptime(args.until, '%Y-%m-%d')
        except ValueError:
            print(f"Error: Invalid date format for --until: {args.until}", file=sys.stderr)
            sys.exit(1)
    
    # Generate report
    generator = ActivityReportGenerator(repo_path=args.repo, language=args.language)
    report = generator.generate_report(since_date, until_date, format=args.format)
    
    # Output report
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"Report saved to: {args.output}")
    else:
        print(report)


if __name__ == '__main__':
    main()
