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

def update_timestamps_with_titles(timestamps_file: Path, song_titles: List[str]):
    """Update timestamps.txt with generated song titles"""
    try:
        if not timestamps_file.exists():
            logger.error("Timestamps file not found")
            return False
            
        with open(timestamps_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        if len(lines) != len(song_titles):
            logger.error(f"Number of timestamps ({len(lines)}) doesn't match number of titles ({len(song_titles)})")
            return False
            
        # Update each line with new title
        new_lines = []
        for i, line in enumerate(lines):
            timestamp = line.split(" - ")[0]
            new_lines.append(f"{timestamp} - {song_titles[i]}\n")
            
        with open(timestamps_file, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
            
        logger.info("Successfully updated timestamps with generated titles")
        return True
        
    except Exception as e:
        logger.error(f"Error updating timestamps: {str(e)}")
        return False 