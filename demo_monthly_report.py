#!/usr/bin/env python3
"""
Demo script for the monthly activity report generator.
展示月度活动报告生成器的示例脚本。
"""

import subprocess
import os


def run_command(cmd, description):
    """Run a command and display its output."""
    print("=" * 80)
    print(f"示例 / Example: {description}")
    print("=" * 80)
    print(f"命令 / Command: {cmd}")
    print("-" * 80)
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(f"错误 / Error: {result.stderr}")
    print()


def main():
    """Run various examples of the monthly report generator."""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 15 + "月度活动报告生成器演示 / Monthly Report Demo" + " " * 16 + "║")
    print("╚" + "═" * 78 + "╝")
    print("\n")
    
    # Example 1: Chinese text report (default)
    run_command(
        "python3 monthly_report.py --days 60 | head -35",
        "生成中文文本报告（最近60天）/ Generate Chinese text report (last 60 days)"
    )
    
    # Example 2: English markdown report
    run_command(
        "python3 monthly_report.py --language en --format markdown --days 60 | head -35",
        "生成英文Markdown报告 / Generate English markdown report"
    )
    
    # Example 3: Save to file
    print("=" * 80)
    print("示例 / Example: 保存报告到文件 / Save report to file")
    print("=" * 80)
    output_file = "/tmp/monthly_activity_report.txt"
    cmd = f"python3 monthly_report.py --language zh --output {output_file}"
    print(f"命令 / Command: {cmd}")
    print("-" * 80)
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
    
    if os.path.exists(output_file):
        print(f"\n报告已保存到 / Report saved to: {output_file}")
        print("\n文件内容预览 / File preview:")
        with open(output_file, 'r', encoding='utf-8') as f:
            print(f.read()[:800])
    print()
    
    # Example 4: Custom date range
    run_command(
        "python3 monthly_report.py --since 2026-01-01 --until 2026-03-01 --language en | head -30",
        "自定义日期范围 / Custom date range (2026-01-01 to 2026-03-01)"
    )
    
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 28 + "演示完成 / Demo Complete" + " " * 27 + "║")
    print("╚" + "═" * 78 + "╝")
    print("\n")
    print("提示 / Tips:")
    print("  • 运行 'python3 monthly_report.py --help' 查看所有选项")
    print("  • Run 'python3 monthly_report.py --help' to see all options")
    print("\n")


if __name__ == '__main__':
    main()
