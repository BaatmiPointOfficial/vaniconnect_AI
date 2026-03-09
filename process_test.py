from moviepy.editor import VideoFileClip

print("🎬 Starting Phase 2: Video Processing Test...")

# 1. Load the 18-second video we downloaded in Phase 1
try:
    video = VideoFileClip("test_video.mp4")
except Exception as e:
    print("❌ Error: Make sure test_video.mp4 is in your folder!")
    exit()

# 2. Simulate "Watermark Removal" by cropping the bottom 10%
# (We will plug your exact old logic in here later!)
print("✂️ Cropping the bottom of the video to hide watermarks...")
width, height = video.size
clean_video = video.crop(y1=0, y2=height * 0.9)

# 3. Save the new video
print("⏳ Processing... (This might take a minute, computers have to work hard for video!)")
clean_video.write_videofile("clean_video.mp4", codec="libx264", audio_codec="aac")

print("✅ SUCCESS! Look in your folder for the new clean_video.mp4!")