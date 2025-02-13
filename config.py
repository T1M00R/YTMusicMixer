from pathlib import Path
from typing import List

class Config:
    """Configuration for YTMusicMixer"""
    # Directories
    BASE_DIR = Path(__file__).parent
    TEMP_DIR = BASE_DIR / "temp"
    OUTPUT_DIR = BASE_DIR / "output"
    AUDIO_DIR = BASE_DIR / "audio"  # This is where we'll look for WAV files
    BACKGROUNDS_DIR = BASE_DIR / "backgrounds"

    # Input files
    SONG_LIST_FILE = BASE_DIR / "song_list.txt"

    # Background image setting
    BACKGROUND_IMAGE = str(BASE_DIR / "backgrounds" / "bg1.jpg")

    # Background video setting
    BACKGROUND_VIDEO = str(BASE_DIR / "backgrounds" / "bg.mp4")

    # Cleanup settings
    CLEANUP_TEMP = True

    @property
    def background_video(self) -> str:
        """Get background video path, converting GIF if necessary"""
        # Check for MP4 first
        mp4_path = self.BACKGROUNDS_DIR / "bg.mp4"
        if mp4_path.exists():
            return str(mp4_path)
            
        # Check for GIF
        gif_path = self.BACKGROUNDS_DIR / "bg.gif"
        if gif_path.exists():
            from video_creator import convert_gif_to_mp4
            return convert_gif_to_mp4(gif_path, self.TEMP_DIR)
            
        raise FileNotFoundError(
            "No background video found! Please add either:\n"
            f"- {mp4_path} (MP4 file)\n"
            f"- {gif_path} (GIF file)\n"
            "in the backgrounds folder."
        )

    @property
    def song_urls(self) -> List[str]:
        """Get list of WAV files from audio directory"""
        if not self.AUDIO_DIR.exists():
            self.AUDIO_DIR.mkdir(exist_ok=True)
            return []
        
        # Get all .wav files from the audio directory
        wav_files = list(self.AUDIO_DIR.glob("*.wav"))
        return [str(file) for file in wav_files] 