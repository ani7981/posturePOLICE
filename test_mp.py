import cv2
import mediapipe as mp
import urllib.request
import os
import numpy as np

MODEL_PATH = "pose_landmarker_lite.task"
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task"

if not os.path.exists(MODEL_PATH):
    print(f"Downloading {MODEL_PATH}...")
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
    print("Download complete.")

BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

options = PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=MODEL_PATH),
    running_mode=VisionRunningMode.IMAGE
)

print("Creating PoseLandmarker...")
with PoseLandmarker.create_from_options(options) as landmarker:
    print("Testing inference...")
    dummy_image = np.zeros((480, 640, 3), dtype=np.uint8)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=dummy_image)
    result = landmarker.detect(mp_image)
    print("Result pose count:", len(result.pose_landmarks))
    print("Done")
