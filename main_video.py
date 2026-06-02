import cv2
import numpy as np
import os
import shutil
import subprocess
import urllib.request
import onnxruntime as ort
from moviepy.editor import VideoFileClip

# 🚀 INITIALIZE THE LAMA AI ENGINE GLOBALLY (Keeps it warm in server memory)
MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "big-lama.onnx")

# 🔥 AUTO-DOWNLOADER SHIELD: If the live server doesn't have the model, pull it from the Hugging Face mirror
if not os.path.exists(MODEL_PATH):
    print("📥 AI Model file not found. Auto-downloading from production mirror...")
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    
    # Stable, industry-standard LaMa ONNX mirror
    url = "https://huggingface.co/Carve/LaMa-ONNX/resolve/main/lama_fp32.onnx"
    
    try:
        # User-Agent headers prevent Hugging Face from blocking the automated server request
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        with urllib.request.urlopen(req) as response, open(MODEL_PATH, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
        print("✅ AI Model downloaded successfully!")
    except Exception as download_err:
        print(f"🚨 Mirror download failed ({download_err}). Server will boot in fallback mode.")

try:
    if os.path.exists(MODEL_PATH):
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
        ort_session = ort.InferenceSession(MODEL_PATH, providers=providers)
        print("🚀 LaMa AI Inpainting Engine Initialized Successfully!")
    else:
        ort_session = None
except Exception as e:
    print(f"⚠️ ONNX Session initialization failed ({e}). Falling back to classical.")
    ort_session = None


def remove_watermark_pro(input_path, output_path, x, y, w, h):
    """
    High-quality Video Watermark Removal with an Universal Format Pre-Converter.
    Guarantees compatibility for HEVC, MOV, MKV, and mobile uploads.
    """
    # 🌟 STEP 1: THE UNIVERSAL FORMAT CONVERTER SHIELD
    base_name = os.path.basename(input_path)
    normalized_input = f"normalized_{base_name}.mp4"
    
    print(f"🔄 Normalizing video format for processing: {base_name}")
    try:
        conversion_cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-vcodec", "libx264",
            "-acodec", "aac",
            "-pix_fmt", "yuv420p",
            "-preset", "ultrafast",
            normalized_input
        ]
        subprocess.run(conversion_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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

    # --- AI CROP BOUNDS SETUP ---
    # Calculate localized area to slice out for processing (speeds up server performance)
    padding = 16
    x1 = max(0, int(x) - padding)
    y1 = max(0, int(y) - padding)
    x2 = min(width, int(x + w) + padding)
    y2 = min(height, int(y + h) + padding)

    # Force crop dimensions to be multiples of 8 for matrix calculation stability
    crop_w = x2 - x1
    crop_h = y2 - y1
    if crop_w % 8 != 0: x2 = min(width, x2 + (8 - (crop_w % 8)))
    if crop_h % 8 != 0: y2 = min(height, y2 + (8 - (crop_h % 8)))

    frames_processed = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        if frame.shape[1] != width or frame.shape[0] != height:
            frame = cv2.resize(frame, (width, height))
            
        # Create full frame mask coordinates
        mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        cv2.rectangle(mask, (int(x), int(y)), (int(x + w), int(y + h)), 255, -1)
        
        # 🌟 STEP 2 PROCESSING CORE: PREMIUM AI OR STABLE FALLBACK
        if ort_session is not None:
            try:
                # 1. Isolate the watermark crop zone
                crop_frame = frame[y1:y2, x1:x2]
                crop_mask = mask[y1:y2, x1:x2]
                orig_h, orig_w = crop_frame.shape[:2]

                # 2. Rescale crop segment to stable 512x512 square matrix for neural network compatibility
                crop_frame_resized = cv2.resize(crop_frame, (512, 512))
                crop_mask_resized = cv2.resize(crop_mask, (512, 512))

                # 3. Align color format from OpenCV BGR to Neural Network RGB
                crop_rgb = cv2.cvtColor(crop_frame_resized, cv2.COLOR_BGR2RGB)
                
                # 4. Construct high-dimensional mathematical image tensor arrays
                img_tensor = crop_rgb.astype(np.float32) / 255.0
                img_tensor = np.transpose(img_tensor, (2, 0, 1))[np.newaxis, ...]
                
                mask_tensor = crop_mask_resized.astype(np.float32)
                mask_tensor = np.where(mask_tensor > 0, 1.0, 0.0).astype(np.float32)
                mask_tensor = mask_tensor[np.newaxis, np.newaxis, ...]

                # 5. Run raw AI mathematical pixel inference
                ai_outputs = ort_session.run(None, {
                    ort_session.get_inputs()[0].name: img_tensor,
                    ort_session.get_inputs()[1].name: mask_tensor
                })

                # 6. Reconstruct execution array output back to pixel matrix bytes
                ai_output = ai_outputs[0][0]
                ai_output = np.transpose(ai_output, (1, 2, 0))
                ai_output = np.clip(ai_output * 255.0, 0, 255).astype(np.uint8)
                clean_crop_bgr = cv2.cvtColor(ai_output, cv2.COLOR_RGB2BGR)

                # 7. Stretch pixel data back to match native high-res framing dimensions
                clean_crop_final = cv2.resize(clean_crop_bgr, (orig_w, orig_h))
                frame[y1:y2, x1:x2] = clean_crop_final

            except Exception as ai_err:
                # Quick local fallback if a specific video frame encounters an array layout error
                frame = cv2.inpaint(frame, mask, 1, cv2.INPAINT_TELEA)
        else:
            # Fallback directly to clean geometry mode if AI session is unavailable
            frame = cv2.inpaint(frame, mask, 1, cv2.INPAINT_TELEA)

        out.write(frame)
        frames_processed += 1

    cap.release()
    out.release()

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
        if os.path.exists(temp_output):
            os.remove(temp_output)
        if os.path.exists(normalized_input):
            os.remove(normalized_input)

    return True