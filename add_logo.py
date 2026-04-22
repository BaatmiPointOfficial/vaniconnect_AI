import cv2
import os
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip

def add_user_controlled_logo(video_path, logo_path, output_path, x, y, logo_w, logo_h):
    if not os.path.exists(video_path) or not os.path.exists(logo_path):
        return False

    try:
        video = VideoFileClip(video_path)
        
        # Calculate proper height to maintain aspect ratio
        logo_img = cv2.imread(logo_path, cv2.IMREAD_UNCHANGED)
        if logo_img is None:
            return False
            
        aspect_ratio = logo_img.shape[0] / logo_img.shape[1]
        actual_height = int(logo_w * aspect_ratio)
        
        logo = (ImageClip(logo_path)
                .set_duration(video.duration)
                .resize(width=logo_w, height=actual_height)
                .set_position((x, y))) 

        final_video = CompositeVideoClip([video, logo])
        
        final_video.write_videofile(
            output_path, 
            codec="libx264", 
            audio_codec="aac", 
            preset="ultrafast",
            threads=4,
            fps=video.fps,
            logger=None
        )
        
        video.close()
        final_video.close()
        return True
        
    except Exception as e:
        print(f"Python Error: {e}")
        return False