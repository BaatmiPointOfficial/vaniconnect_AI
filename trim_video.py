from moviepy.editor import VideoFileClip
import cv2
import os

def trim_video(input_path, output_path, start_sec, end_sec):
    """ Cuts the video to the specified time range. """
    with VideoFileClip(input_path) as video:
        new_video = video.subclip(start_sec, end_sec)
        new_video.write_videofile(output_path, codec="libx264", audio_codec="aac", 
                                 preset="ultrafast", threads=8, logger=None)
    return True

def add_professional_text(input_path, output_path, text="VaniConnect AI"):
    """ Adds a professional text overlay using OpenCV (No ImageMagick needed). """
    cap = cv2.VideoCapture(input_path)
    fps, width, height = cap.get(cv2.CAP_PROP_FPS), int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    temp_v = "temp_text.mp4"
    out = cv2.VideoWriter(temp_v, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))

    while True:
        ret, frame = cap.read()
        if not ret: break
        # Draw Text
        cv2.putText(frame, text, (50, height - 50), cv2.FONT_HERSHEY_DUPLEX, 1.5, (255, 255, 255), 2)
        out.write(frame)
    cap.release(); out.release()

    # Re-attach audio
    with VideoFileClip(input_path) as original, VideoFileClip(temp_v) as processed:
        final = processed.set_audio(original.audio)
        final.write_videofile(output_path, codec="libx264", preset="ultrafast", threads=8, logger=None)
    os.remove(temp_v)
    return True