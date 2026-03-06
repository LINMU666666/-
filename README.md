# Project Tools / 项目工具

This repository contains multiple useful tools:
1. **Real-Time Card Detection System** - Monitor card game interactions
2. **Monthly Activity Report Generator** - Track git repository activities

---

## Real-Time Card Detection System

A Python-based real-time card detection system for monitoring computer game interactions by tracking and analyzing card appearances on the screen.

## Features

- **Real-time Screen Capture**: Continuously monitors your desktop screen using the `mss` library
- **Card Detection**: Uses computer vision techniques (OpenCV) to identify and track cards
- **Live Statistics**: Displays updated card detection statistics every second (configurable)
- **Performance Optimized**: Efficient frame processing with FPS tracking
- **Customizable**: Adjustable update intervals, monitor selection, and detection parameters

## Requirements

- Python 3.7+
- mss (screen capture)
- opencv-python (computer vision)
- numpy (numerical operations)

## Installation

1. Clone this repository:
```bash
git clone https://github.com/LINMU666666/-.git
cd -
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Run the card detector with default settings (1-second update interval):
```bash
python card_detector.py
```

### Advanced Usage

Customize the detection parameters:

```bash
# Update statistics every 2 seconds
python card_detector.py --interval 2.0

# Monitor a specific screen (e.g., second monitor)
python card_detector.py --monitor 2

# Run for a specific duration (e.g., 60 seconds)
python card_detector.py --duration 60

# Combine multiple options
python card_detector.py --interval 0.5 --monitor 1 --duration 120
```

### Command-line Arguments

- `--interval`: Statistics update interval in seconds (default: 1.0)
- `--monitor`: Monitor number to capture (default: 1 for primary monitor)
- `--duration`: How long to run in seconds (default: run indefinitely)

## How It Works

1. **Screen Capture**: The system uses `mss` to capture screen frames in real-time
2. **Frame Processing**: Each frame is processed using OpenCV to detect card-like objects
3. **Card Identification**: Cards are identified based on:
   - Shape detection (rectangular objects with specific aspect ratios)
   - Color analysis (red for hearts/diamonds, black for spades/clubs)
   - Edge detection and contour analysis
4. **Statistics Tracking**: 
   - Cumulative card counts are maintained across all frames
   - Per-frame statistics are processed and aggregated
   - Display updates occur at specified intervals
5. **Performance Monitoring**: Real-time FPS tracking to ensure optimal performance

## Output

The system displays statistics including:
- Session duration
- Total frames processed
- Current FPS (frames per second)
- Total cards detected
- Breakdown by card type with counts and percentages

Example output:
```
============================================================
Card Detection Statistics - 14:30:15
============================================================
Session Duration: 10.5 seconds
Frames Processed: 523
Current FPS: 49.8
Total Cards Detected: 145

Card Type Breakdown:
------------------------------------------------------------
  heart_or_diamond    :    78 ( 53.8%)
  spade_or_club       :    52 ( 35.9%)
  unknown_card        :    15 ( 10.3%)
============================================================
```

## Customization

You can customize the card detection logic by modifying the `CardDetector` class:

- **Card Types**: Adjust the `card_types` dictionary to define different card patterns
- **Detection Thresholds**: Modify area limits and aspect ratios in `detect_cards_in_frame()`
- **Color Ranges**: Update color detection logic in `_identify_card_type()`
- **Update Frequency**: Change the `update_interval` parameter

## Stopping the Program

Press `Ctrl+C` to stop the detection system. Final statistics will be displayed before exit.

## Performance Tips

- Lower the update interval for faster statistics updates (but higher CPU usage)
- Adjust the sleep time in the main loop to balance CPU usage and detection accuracy
- Use a specific monitor number if you have multiple displays
- Consider the game window size and card visibility for optimal detection

## License

MIT License

## Contributing

Contributions are welcome! Feel free to submit issues and pull requests.

---

## Monthly Activity Report Generator / 月度活动报告生成器

A tool to generate comprehensive activity reports from git repository history.
一个从git仓库历史生成全面活动报告的工具。

### Features / 特性

- **Bilingual Support / 双语支持**: Chinese (中文) and English
- **Multiple Formats / 多种格式**: Text and Markdown output
- **Flexible Time Ranges / 灵活的时间范围**: Custom date ranges or recent days
- **Detailed Statistics / 详细统计**:
  - Total commits, additions, deletions / 总提交数、增加行数、删除行数
  - File change tracking / 文件变更追踪
  - Contributor statistics / 贡献者统计
  - Top modified files / 修改最多的文件

### Usage / 使用方法

#### Basic Usage / 基础用法

Generate a report for the last 30 days in Chinese:
生成过去30天的中文报告:

```bash
python monthly_report.py
```

#### Advanced Usage / 高级用法

```bash
# English report for last 60 days
# 生成过去60天的英文报告
python monthly_report.py --language en --days 60

# Markdown format output
# Markdown格式输出
python monthly_report.py --format markdown

# Custom date range
# 自定义日期范围
python monthly_report.py --since 2026-01-01 --until 2026-02-01

# Save to file
# 保存到文件
python monthly_report.py --output report.txt

# All options combined
# 组合所有选项
python monthly_report.py --language en --format markdown --days 90 --output monthly_summary.md
```

#### Command-line Arguments / 命令行参数

- `--since YYYY-MM-DD` - Start date / 开始日期
- `--until YYYY-MM-DD` - End date / 结束日期
- `--days N` - Number of days to look back (default: 30) / 回溯天数（默认：30）
- `--format {text,markdown}` - Output format / 输出格式
- `--language {zh,en}` - Report language / 报告语言
- `--output FILE` - Save to file / 保存到文件
- `--repo PATH` - Repository path / 仓库路径

### Example Output / 输出示例

```
================================================================================
                                     月度活动报告                                     
================================================================================

时间范围: 2026-01-05 → 2026-03-06
报告生成时间: 2026-03-06 13:40:20

--------------------------------------------------------------------------------
概要统计
--------------------------------------------------------------------------------
  总提交次数: 2
  总增加行数: 886
  总删除行数: 0
  修改文件数: 7
  贡献者: 1

--------------------------------------------------------------------------------
贡献者:
--------------------------------------------------------------------------------
  copilot-swe-agent[bot]        :   2 总提交次数 (100.0%)

--------------------------------------------------------------------------------
修改最多的文件 (前10)
--------------------------------------------------------------------------------
  card_detector.py
    +284, -0 (284 行数变化, 1 修改次数)
  ...
```
