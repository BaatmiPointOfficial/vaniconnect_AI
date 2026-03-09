import cv2
import numpy as np
import os

# 1. FIXED THE FUNCTION NAME!
def enhance_photo_web(input_path, output_path, style="Auto Color Fix"):
    try:
        if not os.path.exists(input_path):
            print(f"❌ ERROR: Cannot find file at {input_path}")
            return False
            
        img = cv2.imread(input_path)
        if img is None:
            print("❌ ERROR: OpenCV failed to read the image.")
            return False

        if len(img.shape) == 3 and img.shape[2] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

        # 2. MATCHED THE REACT STYLES EXACTLY!
        if style == "Auto Color Fix":
            lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            cl = clahe.apply(l)
            limg = cv2.merge((cl,a,b))
            img = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
            
        elif style == "Sharpen & Clarify":
            kernel = np.array([[0, -1, 0], 
                               [-1, 5,-1], 
                               [0, -1, 0]])
            img = cv2.filter2D(img, -1, kernel)
            
        elif style == "HDR Portrait":
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype("float32")
            (h, s, v) = cv2.split(hsv)
            s = s * 1.4 # Boost saturation
            s = np.clip(s, 0, 255)
            hsv = cv2.merge([h,s,v])
            img = cv2.cvtColor(hsv.astype("uint8"), cv2.COLOR_HSV2BGR)
            img = cv2.convertScaleAbs(img, alpha=1.2, beta=15)

        cv2.imwrite(output_path, img)
        print(f"✅ SUCCESS: Photo enhanced using {style}!")
        return True

    except Exception as e:
        print(f"❌ PYTHON MATH ERROR: {str(e)}")
        return False