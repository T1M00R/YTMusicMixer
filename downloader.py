import yt_dlp
from pathlib import Path
from typing import List
import logging

logger = logging.getLogger(__name__)

def download_songs(urls: List[str], output_dir: Path) -> List[str]:
    """
    Download songs from YouTube URLs using yt-dlp
    """
    downloaded_files = []
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
        for url in urls:
            try:
                info = ydl.extract_info(url, download=True)
                file_path = output_dir / f"{info['title']}.mp3"
                downloaded_files.append(str(file_path))
                logger.info(f"Downloaded: {info['title']}")
            except Exception as e:
                logger.error(f"Error downloading {url}: {str(e)}")

    return downloaded_files 