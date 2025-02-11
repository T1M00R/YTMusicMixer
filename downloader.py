import yt_dlp
from pathlib import Path
from typing import List
import logging
import shutil
import subprocess

logger = logging.getLogger(__name__)

def download_songs(urls: List[str], output_dir: Path) -> List[str]:
    """
    Process song sources - either download from YouTube or copy local files
    """
    downloaded_files = []
    
    for source in urls:
        try:
            if source.startswith(('http://', 'https://')):
                # YouTube URL - download it
                file_path = download_from_youtube(source, output_dir)
            else:
                # Local file - copy to temp directory
                file_path = copy_local_file(source, output_dir)
            
            if file_path:
                downloaded_files.append(str(file_path))
                logger.info(f"Processed: {Path(file_path).stem}")
        except Exception as e:
            logger.error(f"Error processing {source}: {str(e)}")

    return downloaded_files

def download_from_youtube(url: str, output_dir: Path) -> str:
    """Download song from YouTube"""
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': str(output_dir / '%(title)s.%(ext)s'),
        'quiet': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return str(output_dir / f"{info['title']}.mp3")

def copy_local_file(file_path: str, output_dir: Path) -> str:
    """Copy local audio file to temp directory"""
    source = Path(file_path)
    if not source.exists():
        raise FileNotFoundError(f"Audio file not found: {file_path}")
        
    if source.suffix.lower() not in ['.mp3', '.wav']:
        raise ValueError(f"Unsupported audio format: {source.suffix}")
    
    dest = output_dir / source.name
    shutil.copy2(source, dest)
    
    # Convert wav to mp3 if needed
    if source.suffix.lower() == '.wav':
        mp3_path = dest.with_suffix('.mp3')
        convert_to_mp3(dest, mp3_path)
        dest.unlink()  # Remove the wav file
        return str(mp3_path)
    
    return str(dest)

def convert_to_mp3(wav_path: Path, mp3_path: Path):
    """Convert WAV to MP3"""
    command = [
        "ffmpeg", "-y",
        "-i", str(wav_path),
        "-codec:a", "libmp3lame",
        "-qscale:a", "2",
        str(mp3_path)
    ]
    subprocess.run(command, check=True, capture_output=True) 