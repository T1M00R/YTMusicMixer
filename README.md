# YTMusicMixer

Automatically create music mix videos from YouTube songs or local audio files. Downloads tracks, merges them with crossfade transitions, adds a looping background video with audio visualization, and generates AI-powered mix descriptions.

![Example Screenshot](docs/example.png)

## Features

- Download songs from YouTube URLs
- Support for local MP3 and WAV files
- Merge multiple songs with smooth 5-second crossfade transitions
- Create audio visualization bars that react to the music
- Use any video as a looping background
- Generate timestamps for the tracklist
- AI-powered mix descriptions using Perplexity API
- Automatic cleanup of temporary files

## Requirements

- Python 3.8+
- FFmpeg installed and in system PATH
- Perplexity API key (for mix descriptions)
- Required Python packages:
```bash
pip install -r requirements.txt
```

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ytmusicmixer.git
cd ytmusicmixer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create project structure and environment file:
```bash
mkdir -p backgrounds temp output audio
touch .env
```

4. Configure environment:
Add your Perplexity API key to `.env`:
```bash
PERPLEXITY_API_KEY=your_api_key_here
```

5. Add your media:
- Place your background video in the `backgrounds` folder as `bg.mp4`
- Place your WAV files in the `audio` folder
- Recommended background video: looping video in 1920x1080p resolution

6. Run the program:
```bash
python youtube_mix_creator.py
```

## Testing

To test the AI description generation without creating a video:
```bash
python test_description.py
```

This will:
- Test the Perplexity API connection
- Generate descriptions for different music genres
- Save results to `output/mix_description.txt`

## Output

The program creates:
- `output/final_mix.mp4`: The final music mix video with visualization
- `output/timestamps.txt`: Timestamps for each song in the mix
- `output/mix_description.txt`: AI-generated mix description and tags

## Configuration

Edit `config.py` to customize:
- Output directories
- Background video path
- Temporary file cleanup settings
- Audio file handling

## Troubleshooting

1. FFmpeg not found:
   - Make sure FFmpeg is installed and in your system PATH
   - Windows: Download from https://ffmpeg.org/download.html
   - Linux: `sudo apt install ffmpeg`
   - macOS: `brew install ffmpeg`

2. API errors:
   - Verify your Perplexity API key in `.env`
   - Check internet connection
   - Ensure API key has sufficient credits

3. Video creation errors:
   - Ensure background video is readable and not corrupted
   - Check available disk space
   - Verify audio files are valid WAV format

## License

MIT License - See LICENSE file for details

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request