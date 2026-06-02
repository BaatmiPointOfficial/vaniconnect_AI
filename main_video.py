import cv2
import numpy as np
import os
import shutil
import subprocess
from moviepy.editor import VideoFileClip

def remove_watermark_pro(input_path, output_path, x, y, w, h):
    """
    High-quality Video Watermark Removal with an Universal Format Pre-Converter.
    Guarantees compatibility for HEVC, MOV, MKV, and mobile uploads.
    """
    # 🌟 STEP 1: THE UNIVERSAL FORMAT CONVERTER SHIELD
    # Create a temporary path to store a normalized version of the video
    base_name = os.path.basename(input_path)
    normalized_input = f"normalized_{base_name}.mp4"
    
    print(f"🔄 Normalizing video format for processing: {base_name}")
    try:
        # This converts ANY weird video format/codec into a standard H.264 MP4 that OpenCV can read perfectly
        conversion_cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-vcodec", "libx264",
            "-acodec", "aac",
            "-pix_fmt", "yuv420p",
            "-preset", "ultrafast",
            normalized_input
        ]
        subprocess.run(conversion_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Use our safely normalized file as the actual source for OpenCV
        processing_source = normalized_input
    except Exception as e:
        print(f"⚠️ Pre-conversion failed ({e}). Falling back to raw input path.")
        processing_source = input_path

    # 🌟 STEP 2: OPEN CV PROCESSING
    cap = cv2.VideoCapture(processing_source)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Force even dimensions for H.264 compliance
    width = width if width % 2 == 0 else width - 1
    height = height if height % 2 == 0 else height - 1

    temp_output = f"temp_pro_{base_name}"
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_output, fourcc, fps, (width, height))

    frames_processed = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        if frame.shape[1] != width or frame.shape[0] != height:
            frame = cv2.resize(frame, (width, height))
            
        # Create mask and apply inpainting
        mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        cv2.rectangle(mask, (x, y), (int(x + w), int(y + h)), 255, -1)
        
        # CHANGE THIS OLD LINE:
# frame = cv2.inpaint(frame, mask, 3, cv2.INPAINT_NS)

# TO THIS NEW LINE:
        frame = cv2.inpaint(frame, mask, 1, cv2.INPAINT_TELEA)
        out.write(frame)
        frames_processed += 1

    cap.release()
    out.release()

    # If parsing completely failed, clean up and exit
    if frames_processed == 0:
        print("🚨 OpenCV Error: Frame processing failed entirely.")
        if os.path.exists(temp_output): os.remove(temp_output)
        if os.path.exists(normalized_input): os.remove(normalized_input)
        return False 

    # 🌟 STEP 3: AUDIO RE-ATTACHMENT & FINAL ENCODE
    try:
        original_clip = VideoFileClip(processing_source)
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
            ffmpeg_params=["-movflags", "+faststart"],
            logger=None
        )
        original_clip.close()
        processed_clip.close()
        print("✅ Production clip built successfully via MoviePy!")
        
    except Exception as e:
        print(f"⚠️ MoviePy failed ({e}). Running secondary FFmpeg web fallback...")
        try:
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
            print(f"🚨 Critical: Fallback failed ({ffmpeg_err}). Copying raw file.")
            shutil.copy(temp_output, output_path)

    finally:
        # Final housekeeping cleanup
        if os.path.exists(temp_output):
            os.remove(temp_output)
        if os.path.exists(normalized_input):
            os.remove(normalized_input)

    return True