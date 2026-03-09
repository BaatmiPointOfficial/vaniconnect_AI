import cv2
import numpy as np
import os
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
    
    # Use a temporary file for the video frames
    temp_output = "temp_pro_process.mp4"
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_output, fourcc, fps, (width, height))

    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        # 1. Create a mask only for the watermark area
        mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        cv2.rectangle(mask, (x, y), (x + w, y + h), 255, -1)
        
        # 2. AI Inpainting (Navier-Stokes) - Much cleaner than blur
        # This fixes the 'eye-checking' smudge you saw earlier
        frame = cv2.inpaint(frame, mask, 3, cv2.INPAINT_NS)
        
        out.write(frame)

    cap.release()
    out.release()

    # 3. Re-attach the original audio for a professional result
    original_clip = VideoFileClip(input_path)
    processed_clip = VideoFileClip(temp_output)
    
    final_video = processed_clip.set_audio(original_clip.audio)
    final_video.write_videofile(
        output_path,
        codec="libx264",
        preset="ultrafast", # Best for your CPU performance
        threads=8,          # Maximum speed for your system
        logger=None
    )
    
    # Cleanup temporary files
    original_clip.close()
    processed_clip.close()
    if os.path.exists(temp_output):
        os.remove(temp_output)
    
    return True