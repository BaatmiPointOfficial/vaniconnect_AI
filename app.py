import os
import boto3
from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import yt_down  # Your YouTube downloader!
import main_photo # Your Photo editor!
import main_video
import bg_remove
import add_logo
import enhance_photo
import enhance_video
import trim_video

# 1. Start the API & Load Secrets
app = FastAPI(title="VaniConnect AI Engine")
# Open the security gates so Vercel can talk to us!
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows any website to connect (we can lock this down to just your Vercel URL later!)
    allow_credentials=True,
    allow_methods=["*"],  # Allows POST, GET, etc.
    allow_headers=["*"],
)
load_dotenv()

r2_access_key = os.getenv('R2_ACCESS_KEY_ID')
r2_secret_key = os.getenv('R2_SECRET_ACCESS_KEY')
r2_endpoint = os.getenv('R2_ENDPOINT_URL')
bucket_name = os.getenv('R2_BUCKET_NAME')

# 2. Connect to Cloudflare R2
s3 = boto3.client(
    's3',
    endpoint_url=r2_endpoint,
    aws_access_key_id=r2_access_key,
    aws_secret_access_key=r2_secret_key,
    region_name='auto' 
)

@app.get("/")
def read_root():
    return {"message": "✅ VaniConnect AI Engine is Live and Running!"}

@app.post("/api/remove-photo-watermark")
async def process_photo(
    file: UploadFile, 
    x: int = Form(...), 
    y: int = Form(...), 
    w: int = Form(...), 
    h: int = Form(...),
    style: str = Form("Standard AI Inpaint")
):
    # Step 1: Save the photo from the website to your laptop
    input_filename = f"temp_{file.filename}"
    output_filename = f"clean_{file.filename}"
    
    with open(input_filename, "wb") as buffer:
        buffer.write(await file.read())

    # Step 2: Run your exact "Surgeon" logic!
    print(f"✂️ Removing watermark from {input_filename}...")
    success = main_photo.remove_photo_watermark_web(
        input_path=input_filename, 
        output_path=output_filename, 
        x=x, y=y, w=w, h=h, style=style
    )

    if not success:
        return {"error": "Failed to process photo"}

    # Step 3: Upload the clean photo to Cloudflare R2
    print("☁️ Uploading clean photo to Cloudflare...")
    with open(output_filename, 'rb') as clean_file:
        s3.put_object(
            Bucket=bucket_name, 
            Key=f'processed_photos/{output_filename}', 
            Body=clean_file
        )
        
    # Step 4: Give the website the public link so the user can download it!
    # (We will format this URL in the next step, for now we just return a success message)
    return {"message": "Success!", "file_name": output_filename}
@app.post("/api/youtube-downloader")
async def process_youtube(
    url: str = Form(...),
    quality: str = Form("720p")
):
    print(f"📥 Downloading YouTube video: {url} at {quality}...")
    
    # Step 1: Run your exact "Delivery Driver" logic
    safe_filename = yt_down.download_youtube_video(
        video_url=url, 
        output_folder="downloads", 
        quality=quality
    )
    
    if not safe_filename:
        return {"error": "Failed to download video from YouTube"}
        
    file_path = os.path.join("downloads", safe_filename)
    
    # Step 2: Upload the downloaded video to Cloudflare R2
    print(f"☁️ Uploading {safe_filename} to Cloudflare...")
    with open(file_path, 'rb') as video_file:
        s3.put_object(
            Bucket=bucket_name, 
            Key=f'downloads/{safe_filename}', 
            Body=video_file
        )
        
    # Step 3: Delete the local file so your laptop doesn't run out of storage!
    try:
        os.remove(file_path)
    except Exception as e:
        print(f"Could not delete local file: {e}")
        
    return {"message": "Success!", "file_name": safe_filename}
@app.post("/api/remove-video-watermark")
async def process_video(
    file: UploadFile, 
    x: int = Form(...), 
    y: int = Form(...), 
    w: int = Form(...), 
    h: int = Form(...)
):
    input_filename = f"temp_vid_{file.filename}"
    output_filename = f"clean_vid_{file.filename}"
    
    # 1. Save uploaded video locally
    with open(input_filename, "wb") as buffer:
        buffer.write(await file.read())

    print(f"🎬 Processing Video Watermark for {input_filename}...")
    
    # 2. Run your professional Navier-Stokes logic
    success = main_video.remove_watermark_pro(
        input_path=input_filename, 
        output_path=output_filename, 
        x=x, y=y, w=w, h=h
    )

    if not success:
        return {"error": "Video processing failed"}

    # 3. Upload the professional result to Cloudflare
    print("☁️ Uploading clean video to Cloudflare...")
    with open(output_filename, 'rb') as clean_file:
        s3.put_object(
            Bucket=bucket_name, 
            Key=f'processed_videos/{output_filename}', 
            Body=clean_file
        )
        
    # 4. Clean up local files
    os.remove(input_filename)
    os.remove(output_filename)
        
    return {"message": "Success!", "file_name": output_filename}
@app.post("/api/remove-background")
async def process_background(file: UploadFile):
    input_filename = f"temp_bg_{file.filename}"
    
    # Force the output to be a .png so it keeps the transparent background!
    base_name = os.path.splitext(file.filename)[0]
    output_filename = f"nobg_{base_name}.png" 
    
    # 1. Save uploaded photo
    with open(input_filename, "wb") as buffer:
        buffer.write(await file.read())

    print(f"🧽 Removing background from {input_filename}...")
    
    # 2. Run your rembg logic
    success = bg_remove.remove_background_web(
        input_path=input_filename, 
        output_path=output_filename
    )

    if not success:
        return {"error": "Background removal failed"}

    # 3. Upload to Cloudflare (as a transparent PNG)
    print("☁️ Uploading transparent photo to Cloudflare...")
    with open(output_filename, 'rb') as clean_file:
        s3.put_object(
            Bucket=bucket_name, 
            Key=f'processed_backgrounds/{output_filename}', 
            Body=clean_file,
            ContentType='image/png' 
        )
        
    # 4. Clean up
    os.remove(input_filename)
    os.remove(output_filename)
        
    return {"message": "Success!", "file_name": output_filename}

@app.post("/api/add-custom-logo")
async def process_add_logo(
    video_file: UploadFile, 
    logo_file: UploadFile, 
    x: int = Form(...), 
    y: int = Form(...), 
    logo_w: int = Form(...), 
    logo_h: int = Form(100) # Your script requires this argument, even though it calculates height automatically!
):
    input_video = f"temp_vid_{video_file.filename}"
    input_logo = f"temp_logo_{logo_file.filename}"
    output_video = f"watermarked_{video_file.filename}"
    
    # 1. Save both uploaded files to the laptop
    with open(input_video, "wb") as buffer:
        buffer.write(await video_file.read())
        
    with open(input_logo, "wb") as buffer:
        buffer.write(await logo_file.read())

    print(f"📌 Stamping logo onto {input_video}...")
    
    # 2. Run your logo logic
    success = add_logo.add_user_controlled_logo(
        video_path=input_video, 
        logo_path=input_logo, 
        output_path=output_video, 
        x=x, y=y, logo_w=logo_w, logo_h=logo_h
    )

    if not success:
        return {"error": "Failed to add logo to video"}

    # 3. Upload the final video to Cloudflare
    print("☁️ Uploading watermarked video to Cloudflare...")
    with open(output_video, 'rb') as clean_file:
        s3.put_object(
            Bucket=bucket_name, 
            Key=f'processed_videos/{output_video}', 
            Body=clean_file
        )
        
    # 4. Clean up all 3 local files
    os.remove(input_video)
    os.remove(input_logo)
    os.remove(output_video)
        
    return {"message": "Success!", "file_name": output_video}

@app.post("/api/enhance-photo")
async def process_enhance_photo(
    file: UploadFile,
    style: str = Form("Auto Color Fix") # Matches your React dropdown!
):
    input_filename = f"temp_enhance_{file.filename}"
    output_filename = f"enhanced_{file.filename}"
    
    # 1. Save uploaded photo locally
    with open(input_filename, "wb") as buffer:
        buffer.write(await file.read())

    print(f"✨ Enhancing photo {input_filename} with style: '{style}'...")
    
    # 2. Run your OpenCV enhancement logic
    success = enhance_photo.enhance_photo_web(
        input_path=input_filename, 
        output_path=output_filename, 
        style=style
    )

    if not success:
        return {"error": "Photo enhancement failed"}

    # 3. Upload the beautiful result to Cloudflare
    print("☁️ Uploading enhanced photo to Cloudflare...")
    with open(output_filename, 'rb') as clean_file:
        s3.put_object(
            Bucket=bucket_name, 
            Key=f'processed_enhancements/{output_filename}', 
            Body=clean_file
        )
        
    # 4. Clean up local files
    os.remove(input_filename)
    os.remove(output_filename)
        
    return {"message": "Success!", "file_name": output_filename}

@app.post("/api/enhance-video")
async def process_enhance_video(file: UploadFile):
    input_filename = f"temp_enhvid_{file.filename}"
    output_filename = f"enhanced_{file.filename}"
    
    # 1. Save uploaded video locally
    with open(input_filename, "wb") as buffer:
        buffer.write(await file.read())

    print(f"⚡ Enhancing video {input_filename} in Turbo Mode...")
    
    # 2. Run your smart OpenCV logic
    success = enhance_video.enhance_video_smartly(
        input_path=input_filename, 
        output_path=output_filename
    )

    if not success:
        return {"error": "Video enhancement failed"}

    # 3. Upload the brightened video to Cloudflare
    print("☁️ Uploading enhanced video to Cloudflare...")
    with open(output_filename, 'rb') as clean_file:
        s3.put_object(
            Bucket=bucket_name, 
            Key=f'processed_videos/{output_filename}', 
            Body=clean_file
        )
        
    # 4. Clean up local files
    os.remove(input_filename)
    os.remove(output_filename)
        
    return {"message": "Success!", "file_name": output_filename}

@app.post("/api/clipcut-pro")
async def process_clipcut(
    file: UploadFile,
    start_sec: float = Form(...),
    end_sec: float = Form(...),
    text: str = Form("VaniConnect AI")
):
    input_filename = f"temp_clip_{file.filename}"
    trimmed_filename = f"trimmed_{file.filename}"
    final_filename = f"final_clipcut_{file.filename}"
    
    # 1. Save uploaded video locally
    with open(input_filename, "wb") as buffer:
        buffer.write(await file.read())

    print(f"✂️ 1/2: Trimming video from {start_sec}s to {end_sec}s...")
    
    # 2. Run trimming function
    trim_success = trim_video.trim_video(
        input_path=input_filename, 
        output_path=trimmed_filename,
        start_sec=start_sec,
        end_sec=end_sec
    )

    if not trim_success:
        return {"error": "Video trimming failed"}

    print(f"✍️ 2/2: Adding professional text overlay: '{text}'...")

    # 3. Add text overlay to the trimmed video!
    text_success = trim_video.add_professional_text(
        input_path=trimmed_filename,
        output_path=final_filename,
        text=text
    )

    if not text_success:
        return {"error": "Text overlay failed"}

    # 4. Upload the final masterpiece to Cloudflare
    print("☁️ Uploading ClipCut Pro video to Cloudflare...")
    with open(final_filename, 'rb') as clean_file:
        s3.put_object(
            Bucket=bucket_name, 
            Key=f'processed_videos/{final_filename}', 
            Body=clean_file
        )
        
    # 5. Clean up all 3 local files so your laptop stays clean
    os.remove(input_filename)
    os.remove(trimmed_filename)
    os.remove(final_filename)
        
    return {"message": "Success!", "file_name": final_filename}