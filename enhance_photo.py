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

        # 🌟 2. THE FREE SHADOW REMOVER & HDR ENHANCER
        if color_correction:
            print("☀️ Running Shadow Recovery & HDR Enhancement...")
            
            # Step A: Recover dark shadows using LAB lightness curve
            lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            # CLAHE specifically targets and boosts shadow contrast
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            cl = clahe.apply(l)
            
            # Merge back into a color image
            limg = cv2.merge((cl,a,b))
            img = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
            
            # Step B: OpenCV's hidden "Magic HDR" filter
            # This is the secret to pulling incredible texture out of the shadows
            img = cv2.detailEnhance(img, sigma_s=10, sigma_r=0.15)

        # 3. FAST AI UPSCALING (FSRCNN)
        print("⚡ Booting up FSRCNN Neural Network...")
        sr = dnn_superres.DnnSuperResImpl_create()
        model_path = "FSRCNN_x4.pb" 
        sr.readModel(model_path)
        sr.setModel("fsrcnn", 4) 
        
        result = sr.upsample(img)

        # ✨ 4. PRO-LEVEL SHARPENING (Fixing the crunchy look)
        if face_restoration:
            print("✨ Applying final crisp polish...")
            
            # Create a professional sharpening matrix
            kernel = np.array([[0, -1, 0], 
                               [-1, 5,-1], 
                               [0, -1, 0]])
            sharpened = cv2.filter2D(result, -1, kernel)
            
            # Blend the sharpened image with the smooth upscaled image 
            # (70% smooth, 30% sharp) to make faces look completely natural
            result = cv2.addWeighted(result, 0.7, sharpened, 0.3, 0)

        cv2.imwrite(output_path, result)
        print(f"✅ SUCCESS: Photo enhanced with Shadow Recovery!")
        return True

    except Exception as e:
        print(f"❌ PYTHON AI ERROR: {str(e)}")
        return False