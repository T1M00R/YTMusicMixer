import subprocess
from pathlib import Path
from typing import List
import logging

logger = logging.getLogger(__name__)

def merge_audio_files(
    audio_files: List[str],
    output_dir: Path,
    crossfade_duration: int = 5
) -> str:
    """
    Merge audio files with crossfade using FFmpeg
    """
    output_file = str(output_dir / "merged_audio.mp3")
    
    # Create complex FFmpeg filter for crossfade between multiple files
    filter_complex = ""
    
    # First file doesn't need crossfade input
    filter_complex += f"[0:a]"
    
    # Add crossfade for subsequent files
    for i in range(1, len(audio_files)):
        # Crossfade between current and previous file
        filter_complex += f"[{i}:a]acrossfade=d={crossfade_duration}:c1=tri:c2=tri"
        
        # If not the last file, add a temporary output label
        if i < len(audio_files) - 1:
            filter_complex += f"[tmp{i}];"
            filter_complex += f"[tmp{i}]"

    # Build FFmpeg command
    command = ["ffmpeg", "-y"]
    
    # Add input files
    for audio_file in audio_files:
        command.extend(["-i", audio_file])
    
    command.extend([
        "-filter_complex", filter_complex,
        "-c:a", "libmp3lame",
        "-q:a", "2",
        output_file
    ])

    try:
        subprocess.run(command, check=True, capture_output=True)
        logger.info("Successfully merged audio files")
        return output_file
    except subprocess.CalledProcessError as e:
        logger.error(f"Error merging audio files: {e.stderr.decode()}")
        raise 