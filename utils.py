import os
from pathlib import Path
from typing import List, Dict
import subprocess
import logging

logger = logging.getLogger(__name__)

def get_audio_duration(file_path: str) -> float:
    """
    Get duration of audio file using FFprobe
    """
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
    except subprocess.CalledProcessError as e:
        logger.error(f"Error getting audio duration: {str(e)}")
        return 0.0

def generate_timestamps(
    original_files: List[str],
    merged_file: str
) -> str:
    """
    Generate timestamps for the tracklist
    """
    timestamps = []
    current_time = 0
    
    for file in original_files:
        duration = get_audio_duration(file)
        timestamp = f"{int(current_time//3600):02d}:{int((current_time%3600)//60):02d}:{int(current_time%60):02d}"
        title = Path(file).stem
        timestamps.append(f"{timestamp} - {title}")
        current_time += duration

    return "\n".join(timestamps)

def cleanup_files(temp_dir: Path):
    """
    Clean up temporary files
    """
    try:
        for file in temp_dir.glob("*"):
            file.unlink()
        temp_dir.rmdir()
        logger.info("Cleaned up temporary files")
    except Exception as e:
        logger.error(f"Error cleaning up files: {str(e)}") 