import os
from pathlib import Path
import requests
import json
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

def generate_mix_description(api_key: str, num_songs: int, genre: str = "lofi jazz") -> Dict[str, str]:
    """Generate a music mix description using Perplexity API"""
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "sonar-pro",
        "messages": [
            {
                "role": "system",
                "content": """You are a music channel creator writing YouTube descriptions.
                Write in a casual, authentic voice - like a real person sharing their favorite music.
                Avoid overly poetic or AI-sounding language.
                Keep it simple and genuine, like talking to a friend."""
            },
            {
                "role": "user",
                "content": f"""Create a YouTube music mix description package. Use this exact format with spacers:

Thank you for tuning in! :D 
[Optional: Add a personal note about the background video/art]

. . . . . . . . . . . . . . . . . . . . 

[Write a short, natural description for this {genre} mix. Focus on:
- What makes this mix special
- When/where to listen to it
- Keep it casual and authentic, like a real person wrote it
- Avoid flowery/poetic language
- 2-3 sentences max]

. . . . . . . . . . . . . . . . . . . . 

Tags:
[tag1],[tag2],[tag3],... (15 tags max)

. . . . . . . . . . . . . . . . . . . . 

Song Titles:
1. [Title 1]
2. [Title 2]
...etc

Important rules for titles:
- Create exactly {num_songs} unique titles
- Each title must be completely different
- No repeating words or themes
- Mix different concepts (nature, urban, emotions, time)
- Keep titles memorable but natural"""
            }
        ],
        "max_tokens": 500,
        "temperature": 0.9,
        "top_p": 0.95,
        "presence_penalty": 0.8
    }

    try:
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            error_text = response.text
            logger.error(f"API Error: {response.status_code} - {error_text}")
            return {"success": False, "error": f"API Error: {error_text}"}
            
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        
        # Extract song titles
        song_titles = extract_song_titles(content)
        
        # Don't save the file here anymore, just return the content
        return {
            "success": True, 
            "content": content,
            "song_titles": song_titles
        }
        
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}

def extract_song_titles(content: str) -> List[str]:
    """Extract song titles from the API response"""
    try:
        # Find the song titles section
        titles_section = content.split("Song Titles:")[1].strip()
        # Split into lines and clean up
        titles = []
        for line in titles_section.split("\n"):
            if line.strip() and ". " in line:
                # Remove number and leading/trailing whitespace
                title = line.split(". ", 1)[1].strip()
                titles.append(title)
        return titles
    except Exception as e:
        logger.error(f"Error extracting song titles: {str(e)}")
        return []

def update_description_with_timestamps(description_file: Path, timestamps_file: Path):
    """Update the song titles in the description with timestamps"""
    try:
        # Read the timestamps
        with open(timestamps_file, "r", encoding="utf-8") as f:
            timestamps = f.readlines()
        
        # Read the description
        with open(description_file, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Split content into sections
        sections = content.split("\n\n")
        
        # Find the Song Titles section
        for i, section in enumerate(sections):
            if section.startswith("Song Titles:"):
                # Replace the song titles with timestamps
                sections[i] = "Tracklist:\n" + "".join(timestamps)
                break
        
        # Combine sections back together
        updated_content = "\n\n".join(sections)
        
        # Write updated content back to file
        with open(description_file, "w", encoding="utf-8") as f:
            f.write(updated_content)
            
        logger.info("Successfully updated description with timestamps")
        return True
        
    except Exception as e:
        logger.error(f"Error updating description with timestamps: {str(e)}")
        return False 