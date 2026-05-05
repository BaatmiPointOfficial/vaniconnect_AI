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
        max_dim = 1600 
        height, width = img.shape[:2]
        if max(height, width) > max_dim:
            scale = max_dim / max(height, width)
            img = cv2.resize(img, (int(width * scale), int(height * scale)), interpolation=cv2.INTER_LANCZOS4)

        # 🌟 2. SAFE COLOR CORRECTION
        if color_correction:
            # We gently lift shadows without crushing the blacks or muddying the image
            lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            # Lowered the clipLimit to 1.2. This prevents the "dirty" look on selfies!
            clahe = cv2.createCLAHE(clipLimit=1.2, tileGridSize=(8,8))
            cl = clahe.apply(l)
            
            limg = cv2.merge((cl,a,b))
            img = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
            
            # (Notice I completely removed the cv2.detailEnhance line that was ruining it!)

        # 3. FAST AI UPSCALING (FSRCNN)
        print("⚡ Booting up FSRCNN Neural Network...")
        sr = dnn_superres.DnnSuperResImpl_create()
        model_path = "FSRCNN_x4.pb" 
        sr.readModel(model_path)
        sr.setModel("fsrcnn", 4) 
        
        result = sr.upsample(img)

        # ✨ 4. CLEAN SHARPENING
        if face_restoration:
            print("✨ Applying clean unsharp mask...")
            # The aggressive matrix made noisy photos look terrible. 
            # This Gaussian approach is much safer for skin and faces.
            gaussian_blur = cv2.GaussianBlur(result, (5, 5), 0)
            result = cv2.addWeighted(result, 1.5, gaussian_blur, -0.5, 0)

        cv2.imwrite(output_path, result)
        print(f"✅ SUCCESS: Photo enhanced cleanly!")
        return True

    except Exception as e:
        print(f"❌ PYTHON AI ERROR: {str(e)}")
        return False