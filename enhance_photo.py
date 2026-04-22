import cv2
from cv2 import dnn_superres
import numpy as np

def enhance_photo_web(input_path, output_path, factor=4, face_restoration=True, color_correction=True):
    try:
        print(f"🧠 AI Engine starting safely: Reading {input_path}")
        img = cv2.imread(input_path)
        
        if img is None:
            print("❌ Error: Could not read image.")
            return False

        # 1. THE MEMORY SAVER SHIELD 🛡️ (NEW)
        # If the image is too big, the AI will crash the RAM. Shrink it first!
        max_dim = 800 
        height, width = img.shape[:2]
        if max(height, width) > max_dim:
            scale = max_dim / max(height, width)
            img = cv2.resize(img, (int(width * scale), int(height * scale)), interpolation=cv2.INTER_AREA)
            print(f"📉 Image too large! Shrunk to {img.shape[1]}x{img.shape[0]} to protect RAM.")

        # 2. COLOR CORRECTION
        if color_correction:
            print("🎨 Applying Auto Color Correction...")
            lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            cl = clahe.apply(l)
            limg = cv2.merge((cl,a,b))
            img = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

        # 3. REAL AI UPSCALING
        print("⚡ Booting up EDSR Neural Network...")
        sr = dnn_superres.DnnSuperResImpl_create()
        
        model_path = "EDSR_x4.pb" 
        sr.readModel(model_path)
        sr.setModel("edsr", 4) 
        
        print("⏳ Hallucinating new pixels... (This may take 10-20 seconds)")
        result = sr.upsample(img)

        # 4. FACE SHARPENING
        if face_restoration:
            print("✨ Applying crisp edges...")
            gaussian_blur = cv2.GaussianBlur(result, (9, 9), 10.0)
            result = cv2.addWeighted(result, 1.5, gaussian_blur, -0.5, 0)

        # 5. Save the AI-enhanced image
        cv2.imwrite(output_path, result)
        print(f"✅ SUCCESS: AI Photo enhanced safely!")
        return True

    except Exception as e:
        print(f"❌ PYTHON AI ERROR: {str(e)}")
        return False