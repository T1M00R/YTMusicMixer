from pathlib import Path
from typing import List

class Config:
    # Directories
    BASE_DIR = Path(__file__).parent
    TEMP_DIR = BASE_DIR / "temp"
    OUTPUT_DIR = BASE_DIR / "output"

    # Song list file
    SONG_LIST_FILE = BASE_DIR / "song_list.txt"

    # Background image setting
    BACKGROUND_IMAGE = str(BASE_DIR / "backgrounds" / "bg1.jpg")

    # Cleanup settings
    CLEANUP_TEMP = True

    @property
    def song_urls(self) -> List[str]:
        """Read song URLs from song_list.txt"""
        if not self.SONG_LIST_FILE.exists():
            return []
        
        with open(self.SONG_LIST_FILE, 'r') as f:
            # Remove empty lines and whitespace
            urls = [line.strip() for line in f.readlines() if line.strip()]
        return urls 