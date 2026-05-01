import os
import json
import boto3
import shutil
import razorpay
from fastapi import FastAPI, Request, BackgroundTasks, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Optional
import firebase_admin
from firebase_admin import credentials, firestore

# 🤖 YOUR AI TOOLS

import main_photo 
import main_video
import bg_remove
import add_logo
import enhance_photo
import enhance_video
import auto_detect 
import db

# 1️⃣ LOAD SECRETS FIRST
load_dotenv()

# 2️⃣ INITIALIZE THE APP (ONLY ONCE!)
app = FastAPI(title="VaniConnect AI Engine")

# 3️⃣ OPEN THE SECURITY GATES (CORS) - THIS FIXES YOUR BUTTON!
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://vaniconnect-studio.vercel.app",
        
    ],
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

# 4️⃣ SET UP RATE LIMITER
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 5️⃣ SET UP DOWNLOADS FOLDER
os.makedirs("downloads", exist_ok=True) 
app.mount("/downloads", StaticFiles(directory="downloads"), name="downloads")

# 6️⃣ CONNECT TO CLOUDFLARE R2
r2_access_key = os.getenv('R2_ACCESS_KEY_ID')
r2_secret_key = os.getenv('R2_SECRET_ACCESS_KEY')
r2_endpoint = os.getenv('R2_ENDPOINT_URL')
bucket_name = os.getenv('R2_BUCKET_NAME')

s3 = boto3.client(
    's3',
    endpoint_url=r2_endpoint,
    aws_access_key_id=r2_access_key,
    aws_secret_access_key=r2_secret_key,
    region_name='auto' 
)

# 7️⃣ RAZORPAY SETUP
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

rzp_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

class OrderRequest(BaseModel):
    user_id: str

class VerifyRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    user_id: str

# 8️⃣ FIREBASE ADMIN SETUP
firebase_secret = os.environ.get("FIREBASE_KEY")
cred = credentials.Certificate(json.loads(firebase_secret))

# 🔥 FIX: Check if Firebase is already initialized to prevent reload crashes
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

firestore_db = firestore.client()
# ---------------------------------------------------------
# 🚀 ROUTES
# ---------------------------------------------------------

@app.get("/")
def read_root():
    return {"message": "✅ VaniConnect AI Engine is Live and Running!"}

# 1️⃣ CREATE THE ORDER
@app.post("/api/create-order")
async def create_order(req: OrderRequest):
    try:
        # ₹299 is 99900 paise in Razorpay
        order_amount = 29900  
        
        razorpay_order = rzp_client.order.create({
            "amount": order_amount,
            "currency": "INR",
            "receipt": f"receipt_{req.user_id}",
            "payment_capture": "1" # Auto-capture the payment
        })
        
        return {
            "order_id": razorpay_order['id'],
            "amount": order_amount,
            "currency": "INR"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 2️⃣ VERIFY PAYMENT & UNLOCK PRO IN FIREBASE
@app.post("/api/verify-payment")
async def verify_payment(req: VerifyRequest):
    try:
        # 1. Razorpay securely checks if the payment is legitimate
        rzp_client.utility.verify_payment_signature({
            'razorpay_order_id': req.razorpay_order_id,
            'razorpay_payment_id': req.razorpay_payment_id,
            'razorpay_signature': req.razorpay_signature
        })
        
        # 2. 🚨 UNLOCK THE FIREBASE USER
        try:
            user_ref = firestore_db.collection('users').document(req.user_id)
            
            # 🔥 We use .set() with merge=True so it creates the user if they don't exist yet!
            user_ref.set({"isProUser": True}, merge=True)
            
            print(f"✅ Successfully upgraded user {req.user_id} to PRO in Firestore!")
        except Exception as e:
            print(f"🔥 FIREBASE ERROR: {e}")
            # We just print the error to the terminal, but we don't crash the app
            # because the Razorpay payment was actually successful!
        
        return {"status": "success", "message": "Payment verified. Pro Unlocked!"}
    
    except razorpay.errors.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Payment verification failed!")
# 👇 (Paste the rest of your AI tool routes down here like /api/enhance, etc.) 👇
@app.get("/")
def read_root():
    return {"message": "✅ VaniConnect AI Engine is Live and Running!"}

@app.post("/api/remove-photo-watermark")
@limiter.limit("5/minute")
async def process_photo(
    request: Request,
    file: UploadFile = File(...), 
    x: int = Form(0), 
    y: int = Form(0), 
    w: int = Form(0), 
    h: int = Form(0),
    style: str = Form("Standard AI Inpaint"),
    mode: str = Form("manual"),
    user_id: str = Form(...) # 🌟 1. Added the Catching Mitt!
):
    # ❌ 2. Deleted the hardcoded admin_user_1!
    
    user_data = db.get_or_create_user(user_id)

    # 2. Safety Check: If Firebase returns NOTHING, stop gracefully!
    if not user_data:
        print(f"🚨 Blocked: User {user_id} not found in Firebase!")
        raise HTTPException(status_code=401, detail="User profile not found. Please log in securely.")

    # 3. Use the NEW Firebase vocabulary
    is_pro = user_data.get("isProUser", False)
    credits_left = user_data.get("free_credits", 0)

    # 4. The Paywall Logic
    if not is_pro and credits_left <= 0:
        print(f"🚨 Blocked: User {user_id} is out of credits!")
        raise HTTPException(status_code=402, detail="PaywallTrigger: Daily limit reached. Upgrade to Pro.")
    
    input_filename = f"downloads/temp_{file.filename}"
    output_filename = f"downloads/clean_{file.filename}"
    
    with open(input_filename, "wb") as buffer:
        buffer.write(await file.read())

    print(f"✂️ Removing photo watermark from {input_filename} in {mode.upper()} mode...")
    
    # 🌟 THE AI AUTO LOGIC FOR PHOTOS!
    if mode == "auto":
        print("🤖 Handing photo to EasyOCR to find the watermark...")
        box = auto_detect.find_text_watermark(input_filename) 
        
        if box:
            x, y, w, h = box['x'], box['y'], box['w'], box['h']
            print(f"✅ AI found the text at: x={x}, y={y}, w={w}, h={h}")
        else:
            return {"error": "AI Auto could not find clear text in the image. Please use Manual Select."}

    success = main_photo.remove_photo_watermark_web(
        input_path=input_filename, 
        output_path=output_filename, 
        x=x, y=y, w=w, h=h, style=style
    )

    if not success:
        return {"error": "Failed to process photo"}

    try:
        with open(output_filename, 'rb') as clean_file:
            s3.put_object(
                Bucket=bucket_name, 
                Key=f'processed_photos/clean_{file.filename}', 
                Body=clean_file
            )
    except Exception as e:
        print(f"Cloudflare upload skipped: {e}")

    try:
        os.remove(input_filename)
    except Exception as e:
        print(f"Cleanup issue: {e}")

    # 🌟 3. FIXED INDENTATION: Now credit is deducted safely!
    if not is_pro:
        db.deduct_credit(user_id) 
        print(f"💸 Credit deducted! Remaining: {credits_left - 1}")
        
    return {"message": "Success!", "file_name": f"clean_{file.filename}"} 


@app.post("/api/remove-video-watermark")
@limiter.limit("5/minute")
async def process_video(
    request: Request,
    file: UploadFile = File(...), 
    x: int = Form(0), 
    y: int = Form(0), 
    w: int = Form(0), 
    h: int = Form(0),
    mode: str = Form("manual"), 
    user_id: str = Form(...) # 🌟 1. Added the Catching Mitt!
):
    # ❌ 2. Deleted the hardcoded admin_user_1!
    
    user_data = db.get_or_create_user(user_id)

    # 2. Safety Check: If Firebase returns NOTHING, stop gracefully!
    if not user_data:
        print(f"🚨 Blocked: User {user_id} not found in Firebase!")
        raise HTTPException(status_code=401, detail="User profile not found. Please log in securely.")

    # 3. Use the NEW Firebase vocabulary
    is_pro = user_data.get("isProUser", False)
    credits_left = user_data.get("free_credits", 0)

    # 4. The Paywall Logic
    if not is_pro and credits_left <= 0:
        print(f"🚨 Blocked: User {user_id} is out of credits!")
        raise HTTPException(status_code=402, detail="PaywallTrigger: Daily limit reached. Upgrade to Pro.")

    # 1. Save directly into the safe 'downloads' folder
    input_filename = f"downloads/temp_vid_{file.filename}"
    output_filename = f"downloads/clean_vid_{file.filename}"
    
    with open(input_filename, "wb") as buffer:
        buffer.write(await file.read())

    print(f"🎬 Processing Video Watermark for {input_filename} in {mode.upper()} mode...")
    
    # 🌟 THE AI AUTO LOGIC!
    if mode == "auto":
        print("🤖 Handing video to EasyOCR to find the watermark...")
        box = auto_detect.find_text_watermark(input_filename)
        
        if box:
            x, y, w, h = box['x'], box['y'], box['w'], box['h']
            print(f"✅ AI found the logo at: x={x}, y={y}, w={w}, h={h}")
        else:
            # If the AI fails to find text, tell the frontend to show an error
            return {"error": "AI Auto could not find any clear text in the video. Please use Manual Select."}

    # 2. Run your professional Navier-Stokes logic
    success = main_video.remove_watermark_pro(
        input_path=input_filename, 
        output_path=output_filename, 
        x=x, y=y, w=w, h=h
    )

    if not success:
        return {"error": "Video processing failed"}

    # 3. Upload to Cloudflare (Wrap in try/except)
    print("☁️ Uploading clean video to Cloudflare...")
    try:
        with open(output_filename, 'rb') as clean_file:
            s3.put_object(
                Bucket=bucket_name, 
                Key=f'processed_videos/clean_vid_{file.filename}', 
                Body=clean_file
            )
    except Exception as e:
        print(f"Cloudflare upload skipped (Local Mode): {e}")
        
    # 4. Clean up input file
    try:
        os.remove(input_filename)
    except Exception as e:
        print(f"Cleanup issue: {e}")

    # 🌟 3. FIXED INDENTATION: This is now safely outside the try/except block!
    if not is_pro:
        db.deduct_credit(user_id)
        print(f"💸 Credit deducted! Remaining: {credits_left - 1}")
        
    return {"message": "Success!", "file_name": f"clean_vid_{file.filename}"}

@app.post("/api/remove-bg")
@limiter.limit("5/minute")
async def process_background(
     request: Request,
    file: UploadFile = File(...),
    bg_color: Optional[str] = Form(None),       
    bg_image: Optional[UploadFile] = File(None) ,
    user_id: str = Form(...)
):
   # 1. Grab the REAL user_id from the frontend (Replace hardcoded string later!)
   
    user_data = db.get_or_create_user(user_id)

    # 2. Safety Check: If Firebase returns NOTHING, stop gracefully!
    if not user_data:
        print(f"🚨 Blocked: User {user_id} not found in Firebase!")
        raise HTTPException(status_code=401, detail="User profile not found. Please log in securely.")

    # 3. Use the NEW Firebase vocabulary
    is_pro = user_data.get("isProUser", False)
    credits_left = user_data.get("free_credits", 0)

    # 4. The Paywall Logic
    if not is_pro and credits_left <= 0:
        print(f"🚨 Blocked: User {user_id} is out of credits!")
        # 402 Payment Required is the perfect status code here!
        raise HTTPException(status_code=402, detail="PaywallTrigger: Daily limit reached. Upgrade to Pro.")
    
    # --- YOUR EXISTING LOGIC STARTS HERE ---
    input_filename = f"temp_bg_{file.filename}"
    base_name = os.path.splitext(file.filename)[0]
    
    transparent_filename = f"nobg_{base_name}.png"
    pro_output_filename = f"pro_bg_{base_name}.jpg"
    
    with open(input_filename, "wb") as buffer:
        buffer.write(await file.read())

    print(f"🧽 Removing background from {input_filename}...")
    
    success = bg_remove.remove_background_web(input_path=input_filename, output_path=transparent_filename)
    if not success:
        return {"error": "Background removal failed"}

    file_to_upload = transparent_filename
    content_type = 'image/png'

    if bg_color or bg_image:
        custom_bg_path = None
        if bg_image:
            custom_bg_path = f"temp_custom_bg_{bg_image.filename}"
            with open(custom_bg_path, "wb") as buffer:
                buffer.write(await bg_image.read())
                
        print("🎨 Applying Pro Background...")
        pro_success = bg_remove.apply_pro_background(
            transparent_filename, pro_output_filename, 
            bg_color_hex=bg_color, bg_image_path=custom_bg_path
        )
        if pro_success:
            file_to_upload = pro_output_filename
            content_type = 'image/jpeg'
            
        if custom_bg_path and os.path.exists(custom_bg_path):
            os.remove(custom_bg_path)

    shutil.copy(file_to_upload, f"downloads/{file_to_upload}")

    print(f"☁️ Uploading {file_to_upload} to Cloudflare...")
    with open(file_to_upload, 'rb') as final_file:
        s3.put_object(
            Bucket=bucket_name, 
            Key=f'processed_backgrounds/{file_to_upload}', 
            Body=final_file,
            ContentType=content_type 
        )
        
    if os.path.exists(input_filename): os.remove(input_filename)
    if os.path.exists(transparent_filename): os.remove(transparent_filename)
    if os.path.exists(pro_output_filename): os.remove(pro_output_filename)
    
        
    # 💰 5. DEDUCT CREDIT: The job was successful, subtract 1 credit!
    # If they are NOT a pro user, deduct a credit. (Pro users don't lose credits)
    if not is_pro:
        db.deduct_credit(user_id)
        print(f"💸 Credit deducted! Remaining: {credits_left - 1}")
        
    return {"message": "Success!", "file_name": file_to_upload}

@app.post("/api/add-custom-logo")
@limiter.limit("5/minute")
async def process_add_logo(
    request: Request,
    video_file: UploadFile = File(...), 
    logo_file: UploadFile = File(...), 
    x: int = Form(...), 
    y: int = Form(...), 
    logo_w: int = Form(...), 
    logo_h: int = Form(100),
    user_id: str = Form(...) # 🌟 1. Added the Catching Mitt!
):
    # ❌ 2. Deleted the hardcoded admin_user_1!
    
    user_data = db.get_or_create_user(user_id)

    # 2. Safety Check: If Firebase returns NOTHING, stop gracefully!
    if not user_data:
        print(f"🚨 Blocked: User {user_id} not found in Firebase!")
        raise HTTPException(status_code=401, detail="User profile not found. Please log in securely.")

    # 3. Use the NEW Firebase vocabulary
    is_pro = user_data.get("isProUser", False)
    credits_left = user_data.get("free_credits", 0)

    # 4. The Paywall Logic
    if not is_pro and credits_left <= 0:
        print(f"🚨 Blocked: User {user_id} is out of credits!")
        # 402 Payment Required is the perfect status code here!
        raise HTTPException(status_code=402, detail="PaywallTrigger: Daily limit reached. Upgrade to Pro.")

    # 1. 📂 THE FOLDER FIX: Save everything directly into the 'downloads' folder
    input_video = f"downloads/temp_vid_{video_file.filename}"
    input_logo = f"downloads/temp_logo_{logo_file.filename}"
    output_video = f"downloads/watermarked_{video_file.filename}"
    
    # Save both uploaded files directly to the safe folder
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

    # 3. THE CLOUD FIX: Wrap in a try/except so local tests don't crash without Wi-Fi
    print("☁️ Uploading watermarked video to Cloudflare...")
    try:
        with open(output_video, 'rb') as clean_file:
            s3.put_object(
                Bucket=bucket_name, 
                Key=f'processed_videos/watermarked_{video_file.filename}', 
                Body=clean_file
            )
    except Exception as e:
        print(f"Cloudflare upload skipped (Local Mode): {e}")
        
    # 4. 🛑 THE DELETE FIX: Clean up inputs, but KEEP the output video!
    try:
        os.remove(input_video)
        os.remove(input_logo)
        # os.remove(output_video) <-- Commented out so the frontend can play it!
    except Exception as e:
        print(f"Cleanup issue: {e}")
        
    # Send JUST the final file name back to React
    if not is_pro:
        db.deduct_credit(user_id)
        print(f"💸 Credit deducted! Remaining: {credits_left - 1}")

    return {"message": "Success!", "file_name": f"watermarked_{video_file.filename}"}

@app.post("/api/enhance-photo")
@limiter.limit("5/minute")
async def process_enhance_photo(
    request: Request,
    file: UploadFile = File(...),
    factor: int = Form(4), 
    face_restoration: str = Form("true"), 
    color_correction: str = Form("false"),
    user_id: str = Form(...) # 🌟 1. Added the Catching Mitt!
):
    # ❌ 2. Deleted the hardcoded admin_user_1!
    
    user_data = db.get_or_create_user(user_id)

    # 2. Safety Check: If Firebase returns NOTHING, stop gracefully!
    if not user_data:
        print(f"🚨 Blocked: User {user_id} not found in Firebase!")
        raise HTTPException(status_code=401, detail="User profile not found. Please log in securely.")

    # 3. Use the NEW Firebase vocabulary
    is_pro = user_data.get("isProUser", False)
    credits_left = user_data.get("free_credits", 0)

    # 4. The Paywall Logic
    if not is_pro and credits_left <= 0:
        print(f"🚨 Blocked: User {user_id} is out of credits!")
        raise HTTPException(status_code=402, detail="PaywallTrigger: Daily limit reached. Upgrade to Pro.")

    # 1. 📂 THE FOLDER FIX: Save directly into the safe 'downloads' folder
    input_filename = f"downloads/temp_enhance_{file.filename}"
    output_filename = f"downloads/enhanced_{file.filename}"
    
    # Save uploaded photo locally
    with open(input_filename, "wb") as buffer:
        buffer.write(await file.read())

    print(f"✨ Enhancing photo {input_filename} | Factor: {factor}x | Face: {face_restoration} | Color: {color_correction}")
    
    # 2. Run your OpenCV enhancement logic
    # We pass all the React UI settings directly to your engine!
    success = enhance_photo.enhance_photo_web(
        input_path=input_filename, 
        output_path=output_filename, 
        factor=factor,
        face_restoration=(face_restoration == "true"),
        color_correction=(color_correction == "false")
    )

    if not success:
        return {"error": "Photo enhancement failed"}

    # 3. ☁️ THE CLOUD FIX: Wrap in try/except so local tests don't crash
    print("☁️ Uploading enhanced photo to Cloudflare...")
    try:
        with open(output_filename, 'rb') as clean_file:
            s3.put_object(
                Bucket=bucket_name, 
                Key=f'processed_enhancements/enhanced_{file.filename}', 
                Body=clean_file
            )
    except Exception as e:
        print(f"Cloudflare upload skipped (Local Mode): {e}")
        
    # 4. 🛑 THE DELETE FIX: Keep the output file alive!
    try:
        os.remove(input_filename)
        # os.remove(output_filename) <-- Commented out so frontend can show it!
    except Exception as e:
        print(f"Cleanup issue: {e}")
        
    # 5. THE DOUBLE-DOWNLOAD FIX: Send ONLY the file name back to React
    if not is_pro:
        db.deduct_credit(user_id)
        print(f"💸 Credit deducted! Remaining: {credits_left - 1}")

    return {"message": "Success!", "file_name": f"enhanced_{file.filename}"}

@app.post("/api/enhance-video")
@limiter.limit("5/minute") # <-- 1. The Bouncer: Only 5 downloads per minute!
async def process_enhance_video(
    request: Request,
    file: UploadFile = File(...),
    # 🛡️ THE SHIELD: Catch the UI settings so React doesn't crash!
    resolution: str = Form("1080p FHD"), 
    fps_60: str = Form("true"), 
    denoise: str = Form("true"),
    user_id: str = Form(...) # 🌟 1. Added the Catching Mitt!
):
    # ❌ 2. Deleted the hardcoded admin_user_1!
    
    user_data = db.get_or_create_user(user_id)

    # 2. Safety Check: If Firebase returns NOTHING, stop gracefully!
    if not user_data:
        print(f"🚨 Blocked: User {user_id} not found in Firebase!")
        raise HTTPException(status_code=401, detail="User profile not found. Please log in securely.")

    # 3. Use the NEW Firebase vocabulary
    is_pro = user_data.get("isProUser", False)
    credits_left = user_data.get("free_credits", 0)

    # 4. The Paywall Logic
    if not is_pro and credits_left <= 0:
        print(f"🚨 Blocked: User {user_id} is out of credits!")
        raise HTTPException(status_code=402, detail="PaywallTrigger: Daily limit reached. Upgrade to Pro.")
    
    # 1. 📂 THE FOLDER FIX: Force the engine to save inside the 'downloads' folder
    input_filename = f"downloads/temp_enhvid_{file.filename}"
    output_filename = f"downloads/enhanced_{file.filename}"
    
    # Save uploaded video locally
    with open(input_filename, "wb") as buffer:
        buffer.write(await file.read())

    print(f"⚡ Enhancing video {input_filename} in Turbo Mode... (UI Settings Caught but using Turbo Override)")
    
    # Run your smart MoviePy logic (Turbo Mode)
    success = enhance_video.enhance_video_smartly(
        input_path=input_filename, 
        output_path=output_filename
    )

    if not success:
        return {"error": "Video enhancement failed"}

    # Upload the brightened video to Cloudflare
    print("☁️ Uploading enhanced video to Cloudflare...")
    try:
        with open(output_filename, 'rb') as clean_file:
            s3.put_object(
                Bucket=bucket_name, 
                Key=f'processed_videos/enhanced_{file.filename}', 
                Body=clean_file
            )
    except Exception as e:
        print(f"Cloudflare upload skipped: {e}")
        
    # 2. 🛑 THE DELETE FIX: Keep the output file alive!
    try:
        os.remove(input_filename) # We can safely delete the temporary input video
    except Exception:
        pass
        
    # Send JUST the file name back to the website so it knows what to look for
    if not is_pro:
        db.deduct_credit(user_id)
        print(f"💸 Credit deducted! Remaining: {credits_left - 1}")
        
    return {"message": "Success!", "file_name": f"enhanced_{file.filename}"}

@app.post("/api/clipcut-pro")
@limiter.limit("5/minute") # <-- 1. The Bouncer: Only 5 downloads per minute!
async def process_clipcut(
    request: Request,
    file: UploadFile = File(...),
    start_time: str = Form("00:00:00"), 
    end_time: str = Form("00:00:10"),   
    text: str = Form("VaniConnect AI"),
    user_id: str = Form(...) # 🌟 1. Added the Catching Mitt!
):
    # ❌ 2. Deleted the hardcoded admin_user_1!
    
    user_data = db.get_or_create_user(user_id)

    # 2. Safety Check: If Firebase returns NOTHING, stop gracefully!
    if not user_data:
        print(f"🚨 Blocked: User {user_id} not found in Firebase!")
        raise HTTPException(status_code=401, detail="User profile not found. Please log in securely.")

    # 3. Use the NEW Firebase vocabulary
    is_pro = user_data.get("isProUser", False)
    credits_left = user_data.get("free_credits", 0)

    # 4. The Paywall Logic
    if not is_pro and credits_left <= 0:
        print(f"🚨 Blocked: User {user_id} is out of credits!")
        raise HTTPException(status_code=402, detail="PaywallTrigger: Daily limit reached. Upgrade to Pro.")
    
    input_filename = f"downloads/temp_clip_{file.filename}"
    trimmed_filename = f"downloads/trimmed_{file.filename}"
    final_filename = f"downloads/final_clipcut_{file.filename}"
    
    # 1. Save uploaded video locally
    with open(input_filename, "wb") as buffer:
        buffer.write(await file.read())

    print(f"✂️ 1/2: Trimming video from {start_time} to {end_time}...")
    
    # 2. Run trimming function (MoviePy understands HH:MM:SS perfectly!)
    trim_success = trim_video.trim_video(
        input_path=input_filename, 
        output_path=trimmed_filename,
        start_sec=start_time,
        end_sec=end_time
    )

    if not trim_success:
        return {"error": "Video trimming failed. Make sure Start Time is before End Time!"}

    print(f"✍️ 2/2: Adding professional text overlay: '{text}'...")

    # 3. Add text overlay
    text_success = trim_video.add_professional_text(
        input_path=trimmed_filename,
        output_path=final_filename,
        text=text
    )

    if not text_success:
        return {"error": "Text overlay failed"}

    # 4. Upload to Cloudflare (optional cloud step)
    print("☁️ Uploading ClipCut Pro video to Cloudflare...")
    try:
        with open(final_filename, 'rb') as clean_file:
            s3.put_object(
                Bucket=bucket_name, 
                Key=f'processed_videos/{final_filename}', 
                Body=clean_file
            )
    except Exception as e:
        print(f"Cloud upload skipped: {e}")
        
    # 5. Clean up local files
    try:
        os.remove(input_filename)
        os.remove(trimmed_filename)
    except Exception:
        pass

    # 🌟 3. Fixed the indentation here! 
    if not is_pro:
        db.deduct_credit(user_id)
        print(f"💸 Credit deducted! Remaining: {credits_left - 1}")
        
    return {"message": "Success!", "file_name": f"final_clipcut_{file.filename}"}


@app.get("/test-db")
def test_database():
    user_data = db.get_or_create_user("ceo@vaniconnect.com")
    return {"message": "Database is working perfectly!", "user_data": user_data}