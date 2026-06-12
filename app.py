import cv2
import mediapipe as mp
import serial
import serial.tools.list_ports
import time
import urllib.request
import os

def auto_detect_serial(default_port="COM3", baudrate=9600):
    """
    Attempts to auto-detect an Arduino or similar serial device.
    Falls back to the default port if none is definitively found.
    """
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        if "Arduino" in p.description or "CH340" in p.description or "USB Serial" in p.description:
            try:
                print(f"Auto-detected compatible device on port: {p.device}")
                return serial.Serial(p.device, baudrate, timeout=1)
            except Exception as e:
                print(f"Failed to connect to {p.device}: {e}")
    
    print(f"Attempting to connect to default port: {default_port}")
    try:
        return serial.Serial(default_port, baudrate, timeout=1)
    except Exception as e:
        print(f"Could not open serial port. Serial communication disabled. Error: {e}")
        return None

def download_model_if_missing():
    MODEL_PATH = "pose_landmarker_lite.task"
    MODEL_URL = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task"

    if not os.path.exists(MODEL_PATH):
        print(f"Downloading MediaPipe model to {MODEL_PATH}...")
        try:
            urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
            print("Download complete.")
        except Exception as e:
            print(f"Error downloading model: {e}")
            raise
    return MODEL_PATH

def main():
    # Download required model asset
    model_path = download_model_if_missing()

    # Initialize Serial connection
    ser = auto_detect_serial(default_port="COM3", baudrate=9600)
    last_sent_state = None

    # Initialize MediaPipe Pose Tasks API
    BaseOptions = mp.tasks.BaseOptions
    PoseLandmarker = mp.tasks.vision.PoseLandmarker
    PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
    VisionRunningMode = mp.tasks.vision.RunningMode

    options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=model_path),
        running_mode=VisionRunningMode.IMAGE
    )

    # Initialize Video Capture
    cap = cv2.VideoCapture(0)

    # Calibration baselines
    baseline_eyes_y = None
    baseline_shoulders_y = None
    baseline_shoulder_tilt = None

    # State management
    bad_posture_start_time = None
    is_bad_posture = False
    
    # Thresholds
    SLOUCH_THRESHOLD_Y = 0.03   # Downward drift of eyes or shoulders
    TILT_THRESHOLD_Y = 0.05     # Asymmetry in shoulder height
    VIOLATION_DURATION = 10.0   # Seconds before triggering bad posture status

    print("Starting PosturePOLICE...")
    print("Instructions:")
    print("- Sit up straight and press 'c' to calibrate your baseline posture.")
    print("- Press 'q' to quit the application.")

    with PoseLandmarker.create_from_options(options) as landmarker:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame. Exiting...")
                break

            # Flip frame horizontally for a selfie-view display
            frame = cv2.flip(frame, 1)
            
            # Convert the BGR image to RGB for MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            
            # Process the frame to find poses
            results = landmarker.detect(mp_image)

            # Default key check value
            key = cv2.waitKey(1) & 0xFF

            if results.pose_landmarks and len(results.pose_landmarks) > 0:
                landmarks = results.pose_landmarks[0]
                
                # Draw all points faintly
                h, w, _ = frame.shape
                for idx, lm in enumerate(landmarks):
                    x = int(lm.x * w)
                    y = int(lm.y * h)
                    cv2.circle(frame, (x, y), 2, (200, 200, 200), -1)

                # Extract specific landmarks (indices: 2=left_eye, 5=right_eye, 11=left_shoulder, 12=right_shoulder)
                # Note: 'left' and 'right' are from subject's perspective
                left_eye = landmarks[2]
                right_eye = landmarks[5]
                left_shoulder = landmarks[11]
                right_shoulder = landmarks[12]

                # Draw specific tracked points brightly
                for lm in [left_eye, right_eye, left_shoulder, right_shoulder]:
                    cx = int(lm.x * w)
                    cy = int(lm.y * h)
                    cv2.circle(frame, (cx, cy), 6, (0, 255, 0), -1)

                # Calculate midpoints and tilt metrics (y-coordinates: 0.0 at top, 1.0 at bottom)
                eyes_mid_y = (right_eye.y + left_eye.y) / 2.0
                shoulders_mid_y = (left_shoulder.y + right_shoulder.y) / 2.0
                shoulder_tilt = abs(left_shoulder.y - right_shoulder.y)

                # Check for calibration key
                if key == ord('c'):
                    baseline_eyes_y = eyes_mid_y
                    baseline_shoulders_y = shoulders_mid_y
                    baseline_shoulder_tilt = shoulder_tilt
                    print("Baseline calibrated successfully!")

                # Evaluate posture if the system has been calibrated
                if baseline_eyes_y is not None:
                    # Calculate deviations
                    eyes_slouch = (eyes_mid_y - baseline_eyes_y)
                    shoulders_slouch = (shoulders_mid_y - baseline_shoulders_y)
                    tilt_deviation = (shoulder_tilt - baseline_shoulder_tilt)

                    is_slouching = eyes_slouch > SLOUCH_THRESHOLD_Y or shoulders_slouch > SLOUCH_THRESHOLD_Y
                    is_tilting = tilt_deviation > TILT_THRESHOLD_Y

                    if is_slouching or is_tilting:
                        # User is currently out of bounds
                        if bad_posture_start_time is None:
                            bad_posture_start_time = time.time()
                        
                        elapsed_time = time.time() - bad_posture_start_time
                        
                        if elapsed_time >= VIOLATION_DURATION:
                            is_bad_posture = True
                            status_text = "STATUS: BAD POSTURE"
                            color = (0, 0, 255) # Red (BGR)
                        else:
                            time_left = int(VIOLATION_DURATION - elapsed_time)
                            status_text = f"WARNING: Fix Posture ({time_left}s)"
                            color = (0, 165, 255) # Orange (BGR)
                    else:
                        # User is within acceptable bounds
                        bad_posture_start_time = None
                        is_bad_posture = False
                        status_text = "STATUS: GOOD"
                        color = (0, 255, 0) # Green (BGR)

                    # Serial Communication logic
                    current_state = b'B' if is_bad_posture else b'G'
                    if ser and current_state != last_sent_state:
                        try:
                            ser.write(current_state)
                            last_sent_state = current_state
                            print(f"Sent signal over serial: {current_state}")
                        except Exception as e:
                            print(f"Serial write error: {e}")

                    cv2.putText(frame, status_text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2, cv2.LINE_AA)
                else:
                    # Uncalibrated state UI
                    cv2.putText(frame, "Press 'c' to Calibrate Baseline", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2, cv2.LINE_AA)
            
            else:
                # No person found in frame
                cv2.putText(frame, "Waiting for subject...", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2, cv2.LINE_AA)
                
                # Reset timers if person leaves the frame so they don't trigger a violation when returning
                bad_posture_start_time = None
                is_bad_posture = False
                
                # Send safe signal if subject is lost, to avoid persistent alarms
                if ser and last_sent_state != b'G':
                    try:
                        ser.write(b'G')
                        last_sent_state = b'G'
                    except Exception:
                        pass

            # Exit application on 'q'
            if key == ord('q'):
                break

            cv2.imshow('PosturePOLICE', frame)

    # Cleanup sequence
    cap.release()
    cv2.destroyAllWindows()
    if ser:
        try:
            # Ensure the device is sent a safe signal upon exiting
            ser.write(b'G')
            ser.close()
        except:
            pass

if __name__ == "__main__":
    main()
