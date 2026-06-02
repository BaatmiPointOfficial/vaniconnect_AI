import cv2
import numpy as np
import os
import shutil
import subprocess
import urllib.request
import onnxruntime as ort
from moviepy.editor import VideoFileClip

# 🚀 INITIALIZE THE LAMA AI ENGINE GLOBALLY
MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "big-lama.onnx")

# 🔥 PRO-UPGRADE: Fixed production mirror link with secure browser headers to bypass blockades
if not os.path.exists(MODEL_PATH):
    print("📥 AI Model file not found. Auto-downloading from production mirror...")
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    
    # Using the highly stable, industry-standard Carve LaMa mirror
    url = "https://huggingface.co/Carve/LaMa-ONNX/resolve/main/lama_fp32.onnx"
    
    try:
        # Add User-Agent headers so Hugging Face accepts the server request without throwing a 404/403
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        with urllib.request.urlopen(req) as response, open(MODEL_PATH, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
        print("✅ AI Model downloaded successfully!")
    except Exception as download_err:
        print(f"🚨 Mirror download failed ({download_err}). Server will boot in fallback mode.")

try:
    if os.path.exists(MODEL_PATH):
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
        ort_session = ort.InferenceSession(MODEL_PATH, providers=providers)
        print("🚀 LaMa AI Inpainting Engine Initialized Successfully!")
    else:
        ort_session = None
except Exception as e:
    print(f"⚠️ ONNX Session initialization failed ({e}). Falling back to classical.")
    ort_session = None