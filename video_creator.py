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
import time
import librosa
from typing import List, Tuple

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

def get_color_schemes() -> dict:
    """Define available color schemes"""
    return {
        "1": {
            "name": "Neon Sunset",
            "colors": [
                (255, 94, 225),    # Neon Pink
                (255, 50, 150),    # Hot Pink
                (255, 140, 0),     # Vivid Orange
                (255, 215, 0)      # Golden Yellow
            ]
        },
        "2": {
            "name": "Cyberpunk",
            "colors": [
                (255, 0, 80),      # Hot Pink
                (123, 0, 255),     # Purple
                (0, 255, 255),     # Cyan
                (0, 255, 140)      # Neon Green
            ]
        },
        "3": {
            "name": "Northern Lights",
            "colors": [
                (0, 255, 135),     # Aqua
                (0, 255, 255),     # Cyan
                (0, 191, 255),     # Deep Sky Blue
                (148, 0, 211)      # Violet
            ]
        },
        "4": {
            "name": "Synthwave",
            "colors": [
                (255, 0, 136),     # Hot Pink
                (158, 0, 255),     # Purple
                (0, 183, 255),     # Blue
                (255, 174, 0)      # Orange
            ]
        }
    }

def select_color_scheme() -> List[Tuple[int, int, int]]:
    """Prompt user to select a color scheme"""
    schemes = get_color_schemes()
    
    print("\nAvailable color schemes:")
    for key, scheme in schemes.items():
        print(f"{key}. {scheme['name']}")
    
    while True:
        choice = input("\nSelect a color scheme (1-4): ").strip()
        if choice in schemes:
            return schemes[choice]["colors"]
        print("Invalid choice. Please try again.")

def create_visualization_frame(
    audio_chunk: np.ndarray,
    background: np.ndarray,
    height: int = 1080,
    width: int = 1920,
    n_points: int = 100, #num bars
    colors: List[Tuple[int, int, int]] = None
) -> np.ndarray:
    """Create a single frame with clean audio visualization bars"""
    # Create layers
    vis_layer = np.zeros((height, width, 3), dtype=np.uint8)
    glow_layer = np.zeros((height, width, 3), dtype=np.uint8)
    
    if len(audio_chunk) > 0:
        # Process audio data
        spectrum = np.abs(np.fft.fft(audio_chunk))[:n_points]
        spectrum = spectrum / max(spectrum.max(), 1)
        
        # Apply smoothing with momentum
        if not hasattr(create_visualization_frame, 'prev_spectrum'):
            create_visualization_frame.prev_spectrum = spectrum
            create_visualization_frame.velocity = np.zeros_like(spectrum)
        
        # Physics-based smoothing
        target = spectrum
        current = create_visualization_frame.prev_spectrum
        velocity = create_visualization_frame.velocity
        
        spring_constant = 0.3
        damping = 0.7
        
        acceleration = (target - current) * spring_constant - velocity * damping
        velocity += acceleration
        current += velocity
        
        create_visualization_frame.prev_spectrum = current
        create_visualization_frame.velocity = velocity
        
        spectrum = current
        
        # Adjust these values to change bar appearance
        bar_width = int((width // (n_points * 1.2)) * 0.65)  # Reduced width by 65%
        bar_color = (255, 255, 255)  # Pure white
        glow_color = (255, 255, 255)  # White glow
        corner_radius = int(bar_width * 0.3)  # Slightly smaller corners
        
        for i in range(n_points):
            # Calculate bar height and position
            bar_height = int(spectrum[i] * height * 0.4)
            x = int(width * (i + 0.5) / n_points)
            y = height - bar_height - 20
            bottom_y = height - 20
            
            # Convert all coordinates to integers
            x1 = int(x - bar_width//2)
            x2 = int(x + bar_width//2)
            x1_corner = int(x - bar_width//2 + corner_radius)
            x2_corner = int(x + bar_width//2 - corner_radius)
            
            # Draw the corners
            center_tl = (x1_corner, int(y + corner_radius))
            center_tr = (x2_corner, int(y + corner_radius))
            center_bl = (x1_corner, bottom_y - corner_radius)
            center_br = (x2_corner, bottom_y - corner_radius)
            
            cv2.ellipse(vis_layer, center_tl, (corner_radius, corner_radius), 0, 180, 270, bar_color, -1)
            cv2.ellipse(vis_layer, center_tr, (corner_radius, corner_radius), 0, 270, 360, bar_color, -1)
            cv2.ellipse(vis_layer, center_bl, (corner_radius, corner_radius), 0, 90, 180, bar_color, -1)
            cv2.ellipse(vis_layer, center_br, (corner_radius, corner_radius), 0, 0, 90, bar_color, -1)
            
            # Main rectangles with integer coordinates
            cv2.rectangle(vis_layer,
                (x1, int(y + corner_radius)),
                (x2, bottom_y - corner_radius),
                bar_color, -1)
            
            cv2.rectangle(vis_layer,
                (x1_corner, int(y)),
                (x2_corner, bottom_y),
                bar_color, -1)
            
            # Glow effect with integer coordinates
            cv2.rectangle(glow_layer,
                (x1, int(y - 10)),
                (x2, bottom_y),
                glow_color, -1)
    
    # Process glow
    glow_layer = cv2.GaussianBlur(glow_layer, (21, 21), 7)
    
    # Compose final frame with transparency
    frame = background.copy()
    # Add glow with 20% opacity
    frame = cv2.addWeighted(frame, 1.0, glow_layer, 0.2, 0)
    
    # Add bars with 20% opacity
    vis_mask = cv2.cvtColor(vis_layer, cv2.COLOR_BGR2GRAY) > 0
    frame[vis_mask] = cv2.addWeighted(frame[vis_mask], 0.2, vis_layer[vis_mask], 0.8, 0)
    
    return frame

def create_video(
    audio_file: str,
    background_source: tuple[str, str],
    output_dir: Path,
    output_filename: str = "final_mix.mp4"
) -> str:
    """Create video with audio visualization"""
    output_file = str(output_dir / output_filename)
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Get audio data
        sample_rate, audio_data = get_audio_data(audio_file, temp_dir)
        duration = get_duration(audio_file)
        
        # Video settings
        fps = 30
        n_frames = int(duration * fps)
        samples_per_frame = int(len(audio_data) / n_frames)
        
        background_path, bg_type = background_source
        
        # Handle background based on type
        if bg_type == "video":
            # Pre-load background video frames
            background_cap = cv2.VideoCapture(background_path)
            if not background_cap.isOpened():
                raise Exception("Could not open background video")
            
            total_bg_frames = int(background_cap.get(cv2.CAP_PROP_FRAME_COUNT))
            background_frames = []
            
            # Load background frames with progress bar
            with tqdm(total=total_bg_frames, desc="Loading background", unit="frames") as pbar:
                while True:
                    ret, frame = background_cap.read()
                    if not ret:
                        break
                    background_frames.append(cv2.resize(frame, (1920, 1080)))
                    pbar.update(1)
            background_cap.release()
            
            if not background_frames:
                raise Exception("No background frames loaded")
        else:
            # Load and prepare static image
            background_img = cv2.imread(background_path)
            if background_img is None:
                raise Exception("Could not load background image")
            background_img = cv2.resize(background_img, (1920, 1080))
            background_frames = [background_img]  # Use single frame
        
        # Prepare video writer
        temp_video = os.path.join(temp_dir, "temp_video.mp4")
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(temp_video, fourcc, fps, (1920, 1080))
        
        # Use Neon Sunset as default
        colors = get_color_schemes()["1"]["colors"]
        
        # Generate frames with progress bar
        with tqdm(total=n_frames, desc="Generating frames", unit="frames") as pbar:
            for frame_idx in range(n_frames):
                # Get background frame (loop if needed)
                bg_idx = frame_idx % len(background_frames)
                background = background_frames[bg_idx].copy()
                
                # Process audio chunk
                start_idx = frame_idx * samples_per_frame
                end_idx = min(start_idx + samples_per_frame, len(audio_data))
                audio_chunk = audio_data[start_idx:end_idx]
                
                # Create visualization frame
                frame = create_visualization_frame(audio_chunk, background, colors=colors)
                out.write(frame)
                pbar.update(1)
        
        out.release()
        
        # Show progress for final encoding
        logger.info("Encoding final video...")
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
        
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # Monitor encoding progress
        duration_seconds = duration
        pattern = re.compile(r"time=(\d{2}):(\d{2}):(\d{2}.\d{2})")
        
        with tqdm(total=int(duration_seconds), desc="Encoding", unit="sec") as pbar:
            while True:
                line = process.stderr.readline()
                if not line and process.poll() is not None:
                    break
                    
                match = pattern.search(line)
                if match:
                    h, m, s = map(float, match.groups())
                    current_time = h * 3600 + m * 60 + s
                    pbar.n = int(current_time)
                    pbar.refresh()
        
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

def convert_gif_to_mp4(gif_path: Path, temp_dir: Path) -> str:
    """Convert GIF to MP4 for use as background"""
    output_path = temp_dir / "bg_converted.mp4"
    
    # Updated video filter settings to stretch to full screen
    video_filters = [
        "scale=1920:1080:force_original_aspect_ratio=disable",  # Force stretch to exact dimensions
        "format=yuv420p"  # Ensure compatible color format
    ]
    
    # First try with libx264
    command_x264 = [
        "ffmpeg", "-y",
        "-i", str(gif_path),
        "-movflags", "faststart",
        "-vf", ",".join(video_filters),
        "-r", "30",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        str(output_path)
    ]
    
    # Fallback command using MPEG4 codec
    command_mpeg4 = [
        "ffmpeg", "-y",
        "-i", str(gif_path),
        "-movflags", "faststart",
        "-vf", ",".join(video_filters),
        "-r", "30",
        "-c:v", "mpeg4",
        "-q:v", "6",
        str(output_path)
    ]
    
    try:
        logger.info("Converting GIF to MP4...")
        try:
            subprocess.run(command_x264, check=True, capture_output=True)
        except subprocess.CalledProcessError:
            logger.info("libx264 not available, trying MPEG4 codec...")
            subprocess.run(command_mpeg4, check=True, capture_output=True)
            
        logger.info("GIF conversion successful")
        return str(output_path)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error converting GIF to MP4: {e.stderr.decode()}")
        logger.info("Please install FFmpeg with x264 support: sudo apt-get install ffmpeg x264 libx264-dev")
        raise
    except Exception as e:
        logger.error(f"Unexpected error converting GIF to MP4: {str(e)}")
        raise

def test_visualization(
    duration: float = 5.0,
    fps: int = 30,
    test_freq: float = 2.0
) -> None:
    """Test audio visualization bars with a synthetic sine wave"""
    # Get color scheme from user
    colors = select_color_scheme()
    
    # Create synthetic audio data (sine wave)
    sample_rate = 44100
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_data = np.sin(2 * np.pi * test_freq * t)
    
    # Create a simple white background
    background = np.full((1080, 1920, 3), 255, dtype=np.uint8)
    
    # Calculate frames
    n_frames = int(duration * fps)
    samples_per_frame = int(len(audio_data) / n_frames)
    
    # Create window
    cv2.namedWindow('Visualization Test', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Visualization Test', 960, 540)  # Half resolution for display
    
    # Generate and display frames
    for i in range(n_frames):
        # Get audio chunk for this frame
        start = i * samples_per_frame
        end = start + samples_per_frame
        chunk = audio_data[start:end]
        
        # Create visualization frame
        frame = create_visualization_frame(chunk, background, colors=colors)
        
        # Show frame
        cv2.imshow('Visualization Test', frame)
        
        # Break loop if 'q' is pressed
        if cv2.waitKey(int(1000/fps)) & 0xFF == ord('q'):
            break
    
    cv2.destroyAllWindows()

if __name__ == "__main__":
    # Test the visualization
    test_visualization() 