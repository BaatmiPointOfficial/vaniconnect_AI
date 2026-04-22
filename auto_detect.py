import cv2
import easyocr
import os

# Initialize the EasyOCR reader (This downloads the model on the first run!)
# 'mr' is Marathi, 'hi' is Hindi, 'en' is English. We load all three just in case!
reader = easyocr.Reader(['mr', 'hi', 'en'], gpu=False) 

def find_text_watermark(video_path):
    """
    Grabs the first frame of a video, finds text, and returns x, y, w, h.
    """
    print(f"🤖 AI Auto: Scanning {video_path} for text watermarks...")
    
    # 1. Open the video and grab the first frame
    cap = cv2.VideoCapture(video_path)
    success, frame = cap.read()
    cap.release()

    if not success:
        print("❌ Could not read video frame.")
        return None

    # 2. Ask EasyOCR to find text in the frame
    # We use detail=1 to get the bounding boxes!
    results = reader.readtext(frame, detail=1)

    if not results:
        print("❌ AI Auto could not find any text.")
        return None

    # 3. Find the biggest/most confident text box
    # results format: [([[x1,y1], [x2,y1], [x2,y2], [x1,y2]], 'text', confidence)]
    best_box = results[0][0] 
    
    # Extract the top-left and bottom-right corners
    x1 = int(best_box[0][0])
    y1 = int(best_box[0][1])
    x2 = int(best_box[2][0])
    y2 = int(best_box[2][1])

    # 4. Calculate x, y, w, h
    x = x1
    y = y1
    w = x2 - x1
    h = y2 - y1

    # Add a tiny bit of "padding" so the AI erases perfectly around the edges
    padding = 50
    x = max(0, x - padding)
    y = max(0, y - padding)
    w = w + (padding * 2)
    h = h + (padding * 2)

    print(f"🎯 AI Auto Found Target! Coordinates: x={x}, y={y}, w={w}, h={h}")
    return {"x": x, "y": y, "w": w, "h": h}