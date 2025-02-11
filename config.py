from pathlib import Path
from typing import List

class Config:
    """Configuration for YTMusicMixer"""
    # Directories
    BASE_DIR = Path(__file__).parent
    TEMP_DIR = BASE_DIR / "temp"
    OUTPUT_DIR = BASE_DIR / "output"
    AUDIO_DIR = BASE_DIR / "audio"  # This is where we'll look for WAV files

    # Input files
    SONG_LIST_FILE = BASE_DIR / "song_list.txt"

    # Background image setting
    BACKGROUND_IMAGE = str(BASE_DIR / "backgrounds" / "bg1.jpg")

    # Background video setting
    BACKGROUND_VIDEO = str(BASE_DIR / "backgrounds" / "bg.mp4")

    # Cleanup settings
    CLEANUP_TEMP = True


    @property
    def song_urls(self) -> List[str]:
        """Get list of WAV files from audio directory"""
        if not self.AUDIO_DIR.exists():
            self.AUDIO_DIR.mkdir(exist_ok=True)
            return []
        
        # Get all .wav files from the audio directory
        wav_files = list(self.AUDIO_DIR.glob("*.wav"))
        return [str(file) for file in wav_files] 