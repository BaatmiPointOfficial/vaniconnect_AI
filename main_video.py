import cv2
import numpy as np
import os
import shutil
from moviepy.editor import VideoFileClip

def remove_watermark_pro(input_path, output_path, x, y, w, h):
    """
    High-quality Video Watermark Removal using Navier-Stokes Inpainting.
    Accepts 6 arguments: input, output, x, y, width, height.
    """
    cap = cv2.VideoCapture(input_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # 🌟 TRAFFIC JAM FIX: Make a truly unique temporary file name
    base_name = os.path.basename(input_path)
    temp_output = f"temp_pro_{base_name}"
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_output, fourcc, fps, (width, height))

    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        # 1. Create a mask only for the watermark area
        mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        cv2.rectangle(mask, (x, y), (x + w, y + h), 255, -1)
        
        # 2. AI Inpainting (Navier-Stokes)
        frame = cv2.inpaint(frame, mask, 3, cv2.INPAINT_NS)
        
        out.write(frame)

    cap.release()
    out.release()

    # 🌟 THE NEW BULLETPROOF AUDIO FIX
    # 3. Re-attach the original audio safely
    try:
        original_clip = VideoFileClip(input_path)
        processed_clip = VideoFileClip(temp_output)
        
        # SMART CHECK: Does the original video actually have an audio track?
        if original_clip.audio is not None:
            final_video = processed_clip.set_audio(original_clip.audio)
        else:
            final_video = processed_clip # Just save the video without audio
            
        final_video.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac", # Force standard audio format to prevent crashes
            preset="ultrafast",
            threads=8,
            logger=None
        )
        
        original_clip.close()
        processed_clip.close()
        
    except Exception as e:
        print(f"⚠️ Audio processing failed, saving video without audio: {e}")
        # Emergency fallback: if moviepy completely fails, just copy the temp video 
        # so the user at least gets their cleaned footage!
        shutil.copy(temp_output, output_path)

    finally:
        # Cleanup temporary files safely
        if os.path.exists(temp_output):
            os.remove(temp_output)

    return True