import cv2
import numpy as np
import os

def remove_photo_watermark_web(input_path, output_path, x, y, w, h, style="Standard AI Inpaint"):
    if not os.path.exists(input_path):
        return False
        
    img = cv2.imread(input_path)
    if img is None:
        return False
        
    img_h, img_w = img.shape[:2]
    
    # Safety check: Keep the coordinates inside the image
    x = max(0, min(x, img_w - 1))
    y = max(0, min(y, img_h - 1))
    w = max(1, min(w, img_w - x))
    h = max(1, min(h, img_h - y))
    
    if "Heavy Blur" in style:
        roi = img[y:y+h, x:x+w]
        k_size = max(15, min(w, h) // 2)
        if k_size % 2 == 0: k_size += 1
        img[y:y+h, x:x+w] = cv2.GaussianBlur(roi, (k_size, k_size), 0)
        
    else:
        # THE MARGIN TRICK: We grab an extra 30 pixels of background around the logo
        margin = 30
        y1 = max(0, y - margin)
        y2 = min(img_h, y + h + margin)
        x1 = max(0, x - margin)
        x2 = min(img_w, x + w + margin)
        
        roi = img[y1:y2, x1:x2]
        mask = np.zeros(roi.shape[:2], dtype=np.uint8)
        
        local_y = y - y1
        local_x = x - x1
        
        # We tell the AI EXACTLY where the logo is inside this bordered box
        cv2.rectangle(mask, (local_x, local_y), (local_x + w, local_y + h), 255, -1)
        
        if "Smart Text Eraser" in style:
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            _, text_mask = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)
            final_mask = cv2.bitwise_and(text_mask, mask)
            kernel = np.ones((3,3), np.uint8)
            final_mask = cv2.dilate(final_mask, kernel, iterations=1)
            cleaned_roi = cv2.inpaint(roi, final_mask, 3, cv2.INPAINT_TELEA)
        else:
            cleaned_roi = cv2.inpaint(roi, mask, 3, cv2.INPAINT_TELEA)
            
        # Paste the cleaned area perfectly back into the image
        img[y1:y2, x1:x2] = cleaned_roi

    cv2.imwrite(output_path, img)
    return True