import os
from pathlib import Path
import requests
import json
from typing import Dict
import logging

logger = logging.getLogger(__name__)

def generate_mix_description(api_key: str, genre: str = "lofi jazz") -> Dict[str, str]:
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
                "content": "You are a creative music description writer. Be engaging and specific."
            },
            {
                "role": "user",
                "content": f"""Create a YouTube music mix description package with the following format:

1. A captivating paragraph description for a {genre} mix that mentions the mood, instruments, and ideal listening scenarios
2. 10 CSV tags optimized for music platforms
3. 10 creative song titles that fit the genre

Format the response exactly like this example:
Description:
[paragraph description]

Tags:
[tag1],[tag2],[tag3],...

Song Titles:
1. [Title 1]
2. [Title 2]
...etc"""
            }
        ],
        "max_tokens": 500,
        "temperature": 0.7,
        "top_p": 0.9,
        "stream": False,
        "presence_penalty": 0,
        "frequency_penalty": 0.5
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
        
        # Save the response
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        with open(output_dir / "mix_description.txt", "w", encoding="utf-8") as f:
            f.write(content)
            
        return {"success": True, "content": content}
        
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"} 