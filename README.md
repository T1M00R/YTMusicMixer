# Music Mix Creator

Automatically create music mix videos with audio visualization. The program downloads songs from YouTube, merges them with crossfade transitions, and adds a looping background video with audio visualization.

![Example Screenshot](docs/example.png)

## Features

- Download songs from YouTube URLs
- Merge multiple songs with smooth 5-second crossfade transitions
- Create audio visualization bars that react to the music
- Use any video as a looping background
- Generate timestamps for the tracklist
- Automatic cleanup of temporary files

## Requirements

- Python 3.8+
- FFmpeg installed and in system PATH
- Required Python packages:
```bash
pip install numpy opencv-python scipy yt-dlp tqdm
```

## Quick Start

1. Clone the repository:
```