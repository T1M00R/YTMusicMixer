import subprocess
from pathlib import Path
import logging
from tqdm import tqdm
import re
import numpy as np
from scipy.io import wavfile
import cv2
import tempfile
import os

logger = logging.getLogger(__name__)

def get_duration(file_path: str) -> float:
    """Get duration of audio file in seconds"""
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        file_path
    ]
    try:
        output = subprocess.check_output(cmd)
        return float(output)
    except:
        return 0

def get_audio_data(audio_file: str, temp_dir: str) -> tuple:
    """Convert mp3 to wav and read audio data"""
    wav_file = os.path.join(temp_dir, "temp_audio.wav")
    
    # Convert mp3 to wav using ffmpeg
    command = [
        "ffmpeg", "-y",
        "-i", audio_file,
        "-acodec", "pcm_s16le",
        "-ar", "44100",
        wav_file
    ]
    subprocess.run(command, check=True, capture_output=True)
    
    # Read wav file
    sample_rate, audio_data = wavfile.read(wav_file)
    if len(audio_data.shape) > 1:
        audio_data = audio_data.mean(axis=1)  # Convert stereo to mono
    
    return sample_rate, audio_data

def create_visualization_frame(
    audio_chunk: np.ndarray,
    background: np.ndarray,
    height: int = 720,
    width: int = 1280,
    n_bars: int = 64,
    bar_color: tuple = (0, 255, 255)  # Cyan color in BGR
) -> np.ndarray:
    """Create a single frame with audio visualization bars"""
    frame = background.copy()
    
    # Calculate bar positions and dimensions
    bar_width = int(width / (n_bars * 2))
    bar_spacing = int(width / n_bars)
    max_bar_height = int(height * 0.4)
    
    # Process audio chunk for visualization
    if len(audio_chunk) > 0:
        # Use FFT to get frequency spectrum
        spectrum = np.abs(np.fft.fft(audio_chunk))[:n_bars]
        # Normalize and scale
        spectrum = spectrum / np.max(spectrum) if np.max(spectrum) > 0 else spectrum
    else:
        spectrum = np.zeros(n_bars)
    
    # Draw bars
    for i in range(n_bars):
        bar_height = int(spectrum[i] * max_bar_height)
        if bar_height < 5:
            bar_height = 5
            
        x1 = int(i * bar_spacing)
        y1 = height - bar_height
        x2 = x1 + bar_width
        y2 = height
        
        # Draw the bar
        cv2.rectangle(frame, (x1, y1), (x2, y2), bar_color, -1)
        
        # Draw mirror bar at top
        y1_mirror = 0
        y2_mirror = bar_height
        cv2.rectangle(frame, (x1, y1_mirror), (x2, y2_mirror), bar_color, -1)
    
    return frame

def create_video(
    audio_file: str,
    background_image: str,
    output_dir: Path,
) -> str:
    """Create video with audio visualization"""
    output_file = str(output_dir / "final_mix.mp4")
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Get audio data
        sample_rate, audio_data = get_audio_data(audio_file, temp_dir)
        duration = get_duration(audio_file)
        
        # Video settings
        fps = 30
        n_frames = int(duration * fps)
        samples_per_frame = int(len(audio_data) / n_frames)
        
        # Read and resize background
        background = cv2.imread(background_image)
        background = cv2.resize(background, (1280, 720))
        
        # Prepare video writer
        temp_video = os.path.join(temp_dir, "temp_video.mp4")
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(temp_video, fourcc, fps, (1280, 720))
        
        # Generate frames with progress bar
        with tqdm(total=n_frames, desc="Generating frames") as pbar:
            for frame_idx in range(n_frames):
                start_idx = frame_idx * samples_per_frame
                end_idx = start_idx + samples_per_frame
                audio_chunk = audio_data[start_idx:end_idx]
                
                frame = create_visualization_frame(audio_chunk, background)
                out.write(frame)
                pbar.update(1)
        
        out.release()
        
        # Combine video with audio
        command = [
            "ffmpeg", "-y",
            "-i", temp_video,
            "-i", audio_file,
            "-c:v", "mpeg4",
            "-c:a", "copy",
            "-shortest",
            "-q:v", "5",
            output_file
        ]
        
        subprocess.run(command, check=True, capture_output=True)
        logger.info("Successfully created video with visualization")
        return output_file
        
    except Exception as e:
        logger.error(f"Error creating video: {str(e)}")
        raise
    
    finally:
        # Cleanup temporary directory
        for file in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, file))
        os.rmdir(temp_dir) 