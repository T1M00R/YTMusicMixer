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

def get_video_frame(video_capture, frame_number, width, height):
    """Get a frame from the video at the specified position"""
    video_capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number % int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT)))
    ret, frame = video_capture.read()
    if ret:
        return cv2.resize(frame, (width, height))
    return None

def create_visualization_frame(
    audio_chunk: np.ndarray,
    background: np.ndarray,
    height: int = 720,
    width: int = 1280,
    n_bars: int = 128,
    bar_color: tuple = (255, 255, 255)
) -> np.ndarray:
    """Create a single frame with audio visualization bars"""
    frame = background.copy()
    
    # Calculate bar positions and dimensions
    bar_width = int(width / (n_bars * 1.5))
    bar_spacing = int(width / n_bars)
    max_bar_height = int(height * 0.2)
    corner_radius = min(bar_width // 2, 3)
    
    # Process audio chunk for visualization using vectorized operations
    if len(audio_chunk) > 0:
        # Use numpy's optimized FFT
        spectrum = np.abs(np.fft.fft(audio_chunk))[:n_bars]
        weights = np.linspace(1.0, 3.0, n_bars)
        spectrum = spectrum * weights
        # Vectorized normalization
        spectrum = np.clip(spectrum / np.max(spectrum) if np.max(spectrum) > 0 else spectrum, 0.01, 1.0)
        bar_heights = np.maximum(spectrum * max_bar_height, 4).astype(np.int32)
    else:
        bar_heights = np.full(n_bars, 4, dtype=np.int32)

    # Pre-calculate x positions
    start_x = (width - (n_bars * bar_spacing)) // 2
    x_positions = np.arange(n_bars) * bar_spacing + start_x
    
    # Create visualization overlay
    vis_overlay = np.zeros((height, width, 3), dtype=np.uint8)
    glow_overlay = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Vectorized bar drawing
    for i in range(n_bars):
        x1, x2 = x_positions[i], x_positions[i] + bar_width
        y1 = height - bar_heights[i] - 30
        y2 = height - 30
        
        # Main bar
        cv2.rectangle(vis_overlay, (x1, y1), (x2, y2), bar_color, -1, cv2.LINE_AA)
        
        # Glow
        cv2.rectangle(glow_overlay, (x1-4, y1-4), (x2+4, y2+4), 
                     tuple(map(lambda x: x//4, bar_color)), -1, cv2.LINE_AA)
    
    # Apply optimized glow effect
    glow_overlay = cv2.GaussianBlur(glow_overlay, (21, 21), 11)
    
    # Combine layers efficiently
    frame = cv2.addWeighted(frame, 1.0, glow_overlay, 0.3, 0)
    frame = cv2.addWeighted(frame, 1.0, vis_overlay, 1.0, 0)
    
    return frame

def create_video(
    audio_file: str,
    background_video: str,
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
        
        # Pre-load background video frames for better performance
        background_cap = cv2.VideoCapture(background_video)
        if not background_cap.isOpened():
            raise Exception("Could not open background video")
        
        total_bg_frames = int(background_cap.get(cv2.CAP_PROP_FRAME_COUNT))
        background_frames = []
        
        logger.info("Loading background video frames...")
        for _ in range(total_bg_frames):
            ret, frame = background_cap.read()
            if ret:
                background_frames.append(cv2.resize(frame, (1280, 720)))
        background_cap.release()
        
        # Prepare video writer with hardware acceleration if available
        temp_video = os.path.join(temp_dir, "temp_video.mp4")
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(temp_video, fourcc, fps, (1280, 720))
        
        # Generate frames with progress bar
        with tqdm(total=n_frames, desc="Generating frames") as pbar:
            for frame_idx in range(n_frames):
                # Get background frame from memory
                background = background_frames[frame_idx % len(background_frames)]
                
                # Process audio chunk
                start_idx = frame_idx * samples_per_frame
                end_idx = start_idx + samples_per_frame
                audio_chunk = audio_data[start_idx:end_idx]
                
                # Create visualization frame
                frame = create_visualization_frame(audio_chunk, background)
                out.write(frame)
                pbar.update(1)
        
        out.release()
        
        # Combine video with audio using more efficient settings
        command = [
            "ffmpeg", "-y",
            "-i", temp_video,
            "-i", audio_file,
            "-c:v", "mpeg4",
            "-c:a", "copy",
            "-shortest",
            "-threads", str(os.cpu_count()),
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