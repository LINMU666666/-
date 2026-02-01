# Real-Time Card Detection System

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
