import cv2
from cv2 import dnn_superres
import numpy as np

def enhance_photo_web(input_path, output_path, factor=4, face_restoration=True, color_correction=True):
    try:
        print(f"🧠 AI Engine starting: Reading {input_path}")
        img = cv2.imread(input_path)
        
        if img is None:
            return False

        # 1. THE RELAXED MEMORY SHIELD
        # We increased this to 1600 to preserve the original quality!
        max_dim = 1600 
        height, width = img.shape[:2]
        if max(height, width) > max_dim:
            scale = max_dim / max(height, width)
            img = cv2.resize(img, (int(width * scale), int(height * scale)), interpolation=cv2.INTER_LANCZOS4)
            print(f"📉 Shrunk to {img.shape[1]}x{img.shape[0]} to protect RAM.")

        # 2. COLOR CORRECTION (Softened)
        if color_correction:
            print("🎨 Applying Auto Color Correction...")
            lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            # Reduced clipLimit so it doesn't look over-saturated/burnt
            clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8,8))
            cl = clahe.apply(l)
            limg = cv2.merge((cl,a,b))
            img = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

        # 3. FAST AI UPSCALING (FSRCNN)
        print("⚡ Booting up FSRCNN Neural Network (High Speed)...")
        sr = dnn_superres.DnnSuperResImpl_create()
        
        # Make sure you uploaded FSRCNN_x4.pb to Hugging Face!
        model_path = "FSRCNN_x4.pb" 
        sr.readModel(model_path)
        sr.setModel("fsrcnn", 4) 
        
        result = sr.upsample(img)

        # 4. SMART SHARPENING (Fixing the crunchy look)
        if face_restoration:
            print("✨ Applying soft detail enhancement...")
            # Softened the blur and weights so it doesn't look artificial
            gaussian_blur = cv2.GaussianBlur(result, (5, 5), 0)
            result = cv2.addWeighted(result, 1.2, gaussian_blur, -0.2, 0)

        cv2.imwrite(output_path, result)
        print(f"✅ SUCCESS: AI Photo enhanced!")
        return True

    except Exception as e:
        print(f"❌ PYTHON AI ERROR: {str(e)}")
        return False