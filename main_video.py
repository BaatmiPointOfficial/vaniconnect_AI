import cv2
import numpy as np
import os
import shutil
import subprocess # 🌟 NEW: Needed for strict FFmpeg error catching
from moviepy.editor import VideoFileClip

def remove_watermark_pro(input_path, output_path, x, y, w, h):
    """
    High-quality Video Watermark Removal using Navier-Stokes Inpainting.
    """
    cap = cv2.VideoCapture(input_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # 🌟 FIX 1: FORCE EVEN DIMENSIONS! H.264 crashes if width/height are odd numbers.
    width = width if width % 2 == 0 else width - 1
    height = height if height % 2 == 0 else height - 1

    base_name = os.path.basename(input_path)
    temp_output = f"temp_pro_{base_name}"
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_output, fourcc, fps, (width, height))

    frames_processed = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        # Ensure the frame matches our safe even dimensions
        if frame.shape[1] != width or frame.shape[0] != height:
            frame = cv2.resize(frame, (width, height))
            
        # 1. Create a mask only for the watermark area
        mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        cv2.rectangle(mask, (x, y), (x + w, y + h), 255, -1)
        
        # 2. AI Inpainting
        frame = cv2.inpaint(frame, mask, 3, cv2.INPAINT_NS)
        out.write(frame)
        frames_processed += 1

    cap.release()
    out.release()

    # 🌟 FIX 2: PREVENT 0-BYTE UPLOADS!
    # If OpenCV couldn't read the format, stop and tell the frontend it failed.
    if frames_processed == 0:
        print("🚨 OpenCV Error: Could not read any frames from this video format!")
        if os.path.exists(temp_output): os.remove(temp_output)
        return False 

    # 3. Re-attach the original audio safely and encode to web-safe H.264
    try:
        original_clip = VideoFileClip(input_path)
        processed_clip = VideoFileClip(temp_output)
        
        if original_clip.audio is not None:
            final_video = processed_clip.set_audio(original_clip.audio)
        else:
            final_video = processed_clip
            
        final_video.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac", 
            preset="ultrafast",
            threads=8,
            ffmpeg_params=["-movflags", "+faststart"], # 🌟 MOVES INDEX TO THE FRONT!
            logger=None
        )
        
        original_clip.close()
        processed_clip.close()
        
    except Exception as e:
        print(f"⚠️ MoviePy failed ({e}). Running bulletproof FFmpeg web fallback...")
        
        try:
            # 🌟 FIX 3: STRICT SUBPROCESS
            # This uses standard terminal commands to force formatting and catches real errors
            # 🌟 ADDED FASTSTART HERE TOO
            conversion_command = [
                "ffmpeg", "-y", "-i", temp_output, 
                "-vcodec", "libx264", 
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart", 
                "-an", output_path
            ]
            subprocess.run(conversion_command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("✅ FFmpeg fallback conversion successful!")
        except Exception as ffmpeg_err:
            print(f"🚨 Critical: FFmpeg fallback failed ({ffmpeg_err}). Copying raw file.")
            shutil.copy(temp_output, output_path)

    finally:
        # Cleanup temporary files safely
        if os.path.exists(temp_output):
            os.remove(temp_output)

    return True