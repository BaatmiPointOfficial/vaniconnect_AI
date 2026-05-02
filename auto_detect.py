import cv2
import easyocr
import os

# Initialize the EasyOCR reader
reader = easyocr.Reader(['mr', 'hi', 'en'], gpu=False) 

def find_text_watermark(file_path):
    """
    Smartly reads an image OR grabs the first frame of a video, 
    finds text, and returns x, y, w, h.
    """
    print(f"🤖 AI Auto: Scanning {file_path} for text watermarks...")
    
    # 1. SMART CHECK: Is this a video or a photo?
    is_video = file_path.lower().endswith(('.mp4', '.mov', '.avi'))
    
    if is_video:
        print("🎬 Video detected! Extracting first frame...")
        cap = cv2.VideoCapture(file_path)
        success, img = cap.read()
        cap.release()
        if not success:
            print("❌ Could not read video frame.")
            return None
    else:
        print("📸 Photo detected! Reading image...")
        img = cv2.imread(file_path)
        if img is None:
            print("❌ Could not read the image file.")
            return None

    # 2. Ask EasyOCR to find text in the frame/image
    results = reader.readtext(img, detail=1)

    if not results:
        print("❌ AI Auto could not find any text.")
        return None

    # 3. Find the biggest/most confident text box
    best_box = results[0][0] 
    
    x1 = int(best_box[0][0])
    y1 = int(best_box[0][1])
    x2 = int(best_box[2][0])
    y2 = int(best_box[2][1])

    # 4. Calculate x, y, w, h with padding
    x = x1
    y = y1
    w = x2 - x1
    h = y2 - y1

    padding = 50
    x = max(0, x - padding)
    y = max(0, y - padding)
    w = w + (padding * 2)
    h = h + (padding * 2)

    print(f"🎯 AI Auto Found Target! Coordinates: x={x}, y={y}, w={w}, h={h}")
    return {"x": x, "y": y, "w": w, "h": h}