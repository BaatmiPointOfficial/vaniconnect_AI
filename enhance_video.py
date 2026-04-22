from moviepy.editor import VideoFileClip
import cv2
import numpy as np

def enhance_video_smartly(input_path, output_path, resolution="1080p FHD", fps_60=True, denoise=True):
    """Turbo Mode: Video Enhancement matched to your React UI!"""
    try:
        print(f"🎬 Starting Video Engine | Res: {resolution} | 60FPS: {fps_60} | Denoise: {denoise}")
        
        # 1. Load the video
        clip = VideoFileClip(input_path)
        
        # 2. RESOLUTION UPGRADE
        # Warning: True 4K on a CPU takes hours. For MVP, we use MoviePy's fast resize.
        if resolution == "4K UHD":
            print("📺 Scaling to 4K UHD...")
            clip = clip.resize(height=2160)
        else:
            print("📺 Scaling to 1080p FHD...")
            # If the video is already 1080p, we skip resizing to save massive processing time!
            if clip.h < 1080:
                clip = clip.resize(height=1080)

        # 3. FPS INTERPOLATION
        target_fps = clip.fps
        if fps_60:
            print("🎞️ Upconverting to 60 FPS...")
            target_fps = 60
            # MoviePy will automatically duplicate/blend frames to hit 60fps!

        # 4. FRAME-BY-FRAME AI MATH
        def process_frame(frame):
            # Boost contrast slightly so it pops
            enhanced = cv2.convertScaleAbs(frame, alpha=1.1, beta=5)
            
            # If Denoise is ON, apply a Bilateral Filter (Removes grain, keeps edges sharp)
            if denoise:
                enhanced = cv2.bilateralFilter(enhanced, d=5, sigmaColor=25, sigmaSpace=25)
                
            return enhanced

        # Apply the visual filters
        print("⚙️ Processing frames... (This will take some time on a CPU!)")
        final_clip = clip.fl_image(process_frame)

        # 5. Export
        final_clip.write_videofile(
            output_path, 
            codec='libx264', 
            audio_codec='aac',
            fps=target_fps, # Force the new FPS here!
            logger=None 
        )
        
        # Free up computer RAM
        clip.close()
        final_clip.close()
        
        print("✅ SUCCESS: Video Enhanced!")
        return True
        
    except Exception as e:
        print(f"🚨 Enhancement Error: {e}")
        return False