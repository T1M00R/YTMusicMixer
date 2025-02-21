import os
from pathlib import Path
from typing import List
import logging
from config import Config
from downloader import download_songs
from audio_processor import merge_audio_files
from video_creator import create_video
from utils import generate_timestamps, cleanup_files, update_timestamps_with_titles, rename_audio_files
from description_generator import generate_mix_description, update_description_with_timestamps
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

def get_matching_output_paths(output_dir: Path) -> tuple[Path, Path, Path]:
    """Generate matching output paths for video, timestamps, and description"""
    counter = 1
    while True:
        # Check if this number is already used
        video_path = output_dir / f"final_mix_{counter}.mp4"
        if not video_path.exists():
            # Found an unused number, create matching paths
            timestamp_path = output_dir / f"timestamps_{counter}.txt"
            description_path = output_dir / f"mix_description_{counter}.txt"
            return video_path, timestamp_path, description_path
        counter += 1

def get_genre_input() -> str:
    """Prompt user for music genre"""
    print("\nAvailable genres examples:")
    print("- lofi jazz")
    print("- ambient electronic")
    print("- chill hip hop")
    print("- synthwave")
    print("- piano ambient")
    print("(Press Enter for test mode)")
    
    genre = input("\nEnter the genre for your mix: ").strip()
    return "test" if not genre else genre

def create_music_mix(config: Config) -> bool:
    """
    Main function to create a music mix video
    """
    try:
        # Get genre from user
        genre = get_genre_input()
        
        # Create output directories if they don't exist
        os.makedirs(config.TEMP_DIR, exist_ok=True)
        os.makedirs(config.OUTPUT_DIR, exist_ok=True)
        os.makedirs(config.BACKGROUNDS_DIR, exist_ok=True)

        # Get matching numbered output paths
        final_video, timestamp_output, description_output = get_matching_output_paths(config.OUTPUT_DIR)

        # Check if we have any songs to process
        if not config.song_urls:
            logger.error("No songs found in audio directory")
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
            config.background_source,
            config.OUTPUT_DIR,
            final_video.name
        )

        # Write timestamps to file
        with open(timestamp_output, "w", encoding="utf-8") as f:
            f.write(timestamps)
        logger.info(f"Timestamps written to {timestamp_output}")

        # Cleanup temporary files
        if config.CLEANUP_TEMP:
            cleanup_files(config.TEMP_DIR)

        logger.info(f"Music mix video created successfully: {final_video}")

        # Generate description if API key is available and genre is not "test"
        if api_key and genre.lower() != "test":
            logger.info("Generating mix description...")
            result = generate_mix_description(api_key, len(downloaded_files), genre)
            if result["success"]:
                logger.info("Description generated successfully")
                
                # Write description content to the numbered description file
                with open(description_output, "w", encoding="utf-8") as f:
                    f.write(result["content"])
                
                if "song_titles" in result:
                    if update_timestamps_with_titles(timestamp_output, result["song_titles"]):
                        update_description_with_timestamps(description_output, timestamp_output)
            else:
                logger.error(f"Error generating description: {result['error']}")
        else:
            logger.info("Skipping description generation (test mode)")

        return True

    except Exception as e:
        logger.error(f"Error creating music mix: {str(e)}")
        return False

if __name__ == "__main__":
    config = Config()
    create_music_mix(config) 