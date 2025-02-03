import subprocess
from pathlib import Path
from typing import List
import logging
from tqdm import tqdm
import time
import re

logger = logging.getLogger(__name__)

def get_duration(file_path: str) -> float:
    """Get duration of audio file in seconds"""
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        file_path
    ]
    try:
        output = subprocess.check_output(cmd)
        return float(output)
    except:
        return 0

def create_video(
    audio_file: str,
    background_image: str,
    output_dir: Path,
) -> str:
    """
    Create video with single background image and audio
    """
    output_file = str(output_dir / "final_mix.mp4")
    duration = get_duration(audio_file)
    
    # Build FFmpeg command for single image with optimized encoding
    command = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", background_image,
        "-i", audio_file,
        "-c:v", "mpeg4",
        "-c:a", "copy",
        "-shortest",
        "-pix_fmt", "yuv420p",
        "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2",  # Reduced resolution
        "-q:v", "5",  # Slightly reduced quality for speed
        "-r", "30",  # Reduced framerate
        "-threads", "4",  # Use multiple threads
        output_file
    ]

    try:
        # Start FFmpeg process
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )

        # Setup progress bar
        pbar = tqdm(total=100, desc="Creating video")
        
        # Track progress
        last_progress = 0
        while True:
            if process.stderr is None:
                break
                
            line = process.stderr.readline()
            if not line:
                break
                
            # Extract time information
            time_match = re.search(r"time=(\d+):(\d+):(\d+)", line)
            if time_match:
                hours, minutes, seconds = map(int, time_match.groups())
                current_time = hours * 3600 + minutes * 60 + seconds
                progress = min(100, int(100 * current_time / duration))
                
                # Update progress bar
                if progress > last_progress:
                    pbar.update(progress - last_progress)
                    last_progress = progress

        pbar.close()
        process.wait()

        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, command)

        logger.info("Successfully created video")
        return output_file
    except subprocess.CalledProcessError as e:
        logger.error(f"Error creating video: {e.stderr if hasattr(e, 'stderr') else str(e)}")
        raise 