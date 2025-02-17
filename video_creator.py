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
    height: int = 1080,
    width: int = 1920,
    n_bars: int = 128,
    gradient_start: tuple = (0, 191, 255),    # Deep Sky Blue
    gradient_end: tuple = (135, 206, 250)     # Light Sky Blue
) -> np.ndarray:
    """Create a single frame with audio visualization bars"""
    # Create a black background for the visualization
    vis_overlay = np.zeros((height, width, 3), dtype=np.uint8)
    glow_overlay = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Calculate bar positions and dimensions
    bar_width = int(width / (n_bars * 1.5))
    bar_spacing = int(width / n_bars)
    max_bar_height = int(height * 0.25)
    corner_radius = min(bar_width // 2, 3)
    
    # Improved audio processing for better sync
    if len(audio_chunk) > 0:
        # Apply window function to reduce edge artifacts
        window = np.hanning(len(audio_chunk))
        audio_chunk = audio_chunk * window
        
        # Compute FFT and get magnitude spectrum
        spectrum = np.abs(np.fft.fft(audio_chunk))[:n_bars]
        
        # Apply frequency weighting
        freq_weights = np.linspace(0.5, 2.0, n_bars)  # Bass boost
        freq_weights[n_bars//4:3*n_bars//4] *= 1.5    # Mid boost
        spectrum = spectrum * freq_weights
        
        # Apply smoothing
        spectrum = np.convolve(spectrum, np.hanning(5), mode='same')
        
        # Dynamic normalization with memory
        if not hasattr(create_visualization_frame, 'max_spectrum'):
            create_visualization_frame.max_spectrum = spectrum.max()
        else:
            # Smooth maximum value changes
            create_visualization_frame.max_spectrum = max(
                spectrum.max(),
                create_visualization_frame.max_spectrum * 0.95
            )
        
        # Normalize and apply non-linear scaling
        spectrum = spectrum / create_visualization_frame.max_spectrum
        spectrum = np.clip(spectrum, 0.05, 1.0)
        spectrum = np.power(spectrum, 0.7)  # Adjust response curve
        
        # Add temporal smoothing
        if not hasattr(create_visualization_frame, 'prev_heights'):
            create_visualization_frame.prev_heights = np.zeros(n_bars)
        
        # Calculate new heights with smoothing
        target_heights = spectrum * max_bar_height
        smoothing_factor = 0.3  # Adjust this value to control smoothing (0-1)
        bar_heights = np.maximum(
            create_visualization_frame.prev_heights * (1 - smoothing_factor) +
            target_heights * smoothing_factor,
            4
        ).astype(np.int32)
        
        # Store heights for next frame
        create_visualization_frame.prev_heights = bar_heights
    else:
        bar_heights = np.full(n_bars, 4, dtype=np.int32)

    # Pre-calculate x positions
    start_x = (width - (n_bars * bar_spacing)) // 2
    x_positions = np.arange(n_bars) * bar_spacing + start_x
    
    # Draw bars with alpha channel for better visibility
    for i in range(n_bars):
        gradient_factor = bar_heights[i] / max_bar_height
        # BGR format for OpenCV
        bar_color = tuple(int(start + (end - start) * gradient_factor) 
                         for start, end in zip(gradient_start, gradient_end))
        
        x1, x2 = x_positions[i], x_positions[i] + bar_width
        y1 = height - bar_heights[i] - 30
        y2 = height - 30
        
        # Draw bars with increased opacity
        cv2.rectangle(vis_overlay, (x1, y1 + corner_radius), (x2, y2 - corner_radius), bar_color, -1, cv2.LINE_AA)
        cv2.rectangle(vis_overlay, (x1 + corner_radius, y1), (x2 - corner_radius, y2), bar_color, -1, cv2.LINE_AA)
        
        # Rounded corners
        cv2.circle(vis_overlay, (x1 + corner_radius, y1 + corner_radius), corner_radius, bar_color, -1, cv2.LINE_AA)
        cv2.circle(vis_overlay, (x2 - corner_radius, y1 + corner_radius), corner_radius, bar_color, -1, cv2.LINE_AA)
        cv2.circle(vis_overlay, (x1 + corner_radius, y2 - corner_radius), corner_radius, bar_color, -1, cv2.LINE_AA)
        cv2.circle(vis_overlay, (x2 - corner_radius, y2 - corner_radius), corner_radius, bar_color, -1, cv2.LINE_AA)
        
        # Enhanced glow effect with brighter glow
        glow_color = tuple(min(int(c * 1.8), 255) for c in bar_color)  # Increased brightness
        cv2.rectangle(glow_overlay, (x1-4, y1-4), (x2+4, y2+4), 
                     tuple(c//2 for c in glow_color), -1, cv2.LINE_AA)  # Increased glow opacity
    
    # Apply enhanced glow effect
    glow_overlay = cv2.GaussianBlur(glow_overlay, (21, 21), 11)
    
    # Combine layers with proper alpha blending
    frame = background.copy()
    frame = cv2.addWeighted(frame, 0.7, glow_overlay, 0.6, 0)  # Increased glow intensity and dimmed background
    frame = cv2.addWeighted(frame, 0.7, vis_overlay, 1.0, 0)   # Make bars more visible
    
    return frame

def create_video(
    audio_file: str,
    background_video: str,
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
        
        # Pre-load background video frames for better performance
        background_cap = cv2.VideoCapture(background_video)
        if not background_cap.isOpened():
            raise Exception("Could not open background video")
        
        total_bg_frames = int(background_cap.get(cv2.CAP_PROP_FRAME_COUNT))
        background_frames = []
        
        # Add progress bar for background loading
        logger.info("Loading background video frames...")
        with tqdm(total=total_bg_frames, desc="Loading background", unit="frames") as pbar:
            for _ in range(total_bg_frames):
                ret, frame = background_cap.read()
                if ret:
                    background_frames.append(cv2.resize(frame, (1920, 1080)))
                pbar.update(1)
        background_cap.release()
        
        # Prepare video writer with hardware acceleration if available
        temp_video = os.path.join(temp_dir, "temp_video.mp4")
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(temp_video, fourcc, fps, (1920, 1080))
        
        # Generate frames with enhanced progress bar
        with tqdm(
            total=n_frames,
            desc="Generating frames",
            unit="frames",
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]"
        ) as pbar:
            start_time = time.time()
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
                
                # Update progress with FPS calculation
                if frame_idx % 30 == 0:  # Update every 30 frames
                    elapsed_time = time.time() - start_time
                    if elapsed_time > 0:  # Prevent division by zero
                        current_fps = frame_idx / elapsed_time
                        remaining_frames = n_frames - frame_idx
                        time_left = remaining_frames / current_fps if current_fps > 0 else 0
                        pbar.set_postfix({
                            'FPS': f"{current_fps:.1f}",
                            'Time Left': f"{time_left/60:.1f}min"
                        })
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