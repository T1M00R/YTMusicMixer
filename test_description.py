import os
from pathlib import Path
from dotenv import load_dotenv
from description_generator import generate_mix_description
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_description_api():
    # Load environment variables
    load_dotenv()
    api_key = os.getenv("PERPLEXITY_API_KEY")
    
    if not api_key:
        logger.error("No API key found in .env file")
        return
    
    # Test with different genres
    test_genres = [
        "lofi jazz",
        "ambient electronic",
        "chill hip hop"
    ]
    
    for genre in test_genres:
        logger.info(f"\nTesting with genre: {genre}")
        result = generate_mix_description(api_key, genre)
        
        if result["success"]:
            logger.info("Success! Content:")
            print("\n" + result["content"] + "\n")
        else:
            logger.error(f"Error: {result['error']}")

if __name__ == "__main__":
    test_description_api() 