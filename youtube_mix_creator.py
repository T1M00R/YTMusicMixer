import os
from pathlib import Path
from typing import List
import logging
from config import Config
from downloader import download_songs
from audio_processor import merge_audio_files
from video_creator import create_video
from utils import generate_timestamps, cleanup_files, update_timestamps_with_titles
from description_generator import generate_mix_description
from dotenv import load_dotenv

# Set up logging with more visible format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# At the start of your script
load_dotenv()
api_key = os.getenv("PERPLEXITY_API_KEY")

def create_music_mix(config: Config) -> bool:
    """
    Main function to create a music mix video
    """
    try:
        # Create output directories if they don't exist
        os.makedirs(config.TEMP_DIR, exist_ok=True)
        os.makedirs(config.OUTPUT_DIR, exist_ok=True)

        # Check if we have any songs to process
        if not config.song_urls:
            logger.error("No songs found in song_list.txt")
            return False

        # Step 1: Download songs
        logger.info("Downloading songs...")
        downloaded_files = download_songs(
            config.song_urls,
            config.TEMP_DIR
        )

        if not downloaded_files:
            logger.error("No songs were downloaded successfully")
            return False

        # Step 2: Merge audio files with crossfade
        logger.info("Merging audio files...")
        merged_audio = merge_audio_files(
            downloaded_files,
            config.TEMP_DIR,
            crossfade_duration=5
        )

        # Step 3: Generate timestamps
        logger.info("Generating timestamps...")
        timestamps = generate_timestamps(downloaded_files, merged_audio)

        # Step 4: Create video
        logger.info("Creating video...")
        final_video = create_video(
            merged_audio,
            config.BACKGROUND_VIDEO,
            config.OUTPUT_DIR,
        )

        # Write timestamps to file
        timestamp_file = config.OUTPUT_DIR / "timestamps.txt"
        with open(timestamp_file, "w", encoding="utf-8") as f:
            f.write(timestamps)
        logger.info(f"Timestamps written to {timestamp_file}")

        # Cleanup temporary files
        if config.CLEANUP_TEMP:
            cleanup_files(config.TEMP_DIR)

        logger.info(f"Music mix video created successfully: {final_video}")

        # Generate description if API key is available
        if api_key:
            logger.info("Generating mix description...")
            result = generate_mix_description(api_key, len(downloaded_files))
            if result["success"]:
                logger.info("Description generated successfully")
                # Update timestamps with generated song titles
                if "song_titles" in result:
                    timestamp_file = config.OUTPUT_DIR / "timestamps.txt"
                    update_timestamps_with_titles(timestamp_file, result["song_titles"])
            else:
                logger.error(f"Error generating description: {result['error']}")

        return True

    except Exception as e:
        logger.error(f"Error creating music mix: {str(e)}")
        return False

if __name__ == "__main__":
    config = Config()
    create_music_mix(config) 