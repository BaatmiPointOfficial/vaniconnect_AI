import cv2
import numpy as np
import os
import shutil
import subprocess
import urllib.request  # <-- Make sure this is imported at the top
import onnxruntime as ort
from moviepy.editor import VideoFileClip

# 🚀 INITIALIZE THE LAMA AI ENGINE GLOBALLY
MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "big-lama.onnx")

# 🔥 PRO-UPGRADE: If the live server doesn't have the model, pull it from the cloud mirror automatically
if not os.path.exists(MODEL_PATH):
    print("📥 AI Model file not found. Auto-downloading from production mirror...")
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    url = "https://github.com/anotherjesse/onnx2torch/releases/download/v0.0.1/big-lama.onnx"
    urllib.request.urlretrieve(url, MODEL_PATH)
    print("✅ AI Model downloaded successfully!")

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