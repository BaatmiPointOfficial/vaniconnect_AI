import yt_dlp
import os
import uuid

def download_youtube_video(video_url, output_folder="downloads", quality="720p"):
    try:
        os.makedirs(output_folder, exist_ok=True)
        
        # 🛡️ THE FIX: Generate a random ID to bypass Windows naming errors completely
        random_id = uuid.uuid4().hex[:8]
        is_audio = (quality == "audio")
        ext = "mp3" if is_audio else "mp4"
        
        safe_filename = f"yt_{random_id}.{ext}"
        final_path = os.path.join(output_folder, safe_filename)

        # Map the UI selection to the correct yt-dlp format codes
        if quality == "best":
            format_str = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        elif quality == "720p":
            format_str = 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best'
        elif quality == "480p":
            format_str = 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best'
        elif quality == "audio":
            format_str = 'bestaudio/best'
        else:
            format_str = 'best[ext=mp4]/best' # Fallback
            
        ydl_opts = {
            'format': format_str, 
            'outtmpl': final_path,  # 🎯 FORCE THE SAFE NAME HERE
            'quiet': False,
            'no_warnings': True
        }
        
        if is_audio:
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        else:
            ydl_opts['merge_output_format'] = 'mp4'
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
            
        # Return only the clean, safe filename (e.g. yt_8f3a2b1c.mp4) to React
        return safe_filename
            
    except Exception as e:
        print(f"🚨 YouTube Download Error: {e}")
        return None