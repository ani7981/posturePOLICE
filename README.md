# PosturePOLICE

PosturePOLICE is a real-time posture monitoring system that uses computer vision to detect slouching or tilting and provides physical feedback via an Arduino-powered vibration motor.

## Project Architecture

The system operates through three primary layers:

1.  **MediaPipe Pose Geometry:** A Python application captures video from a webcam and uses the MediaPipe Pose Landmarker (Lite) to track 33 3D landmarks on the user's body. It specifically monitors the vertical position and alignment of the eyes and shoulders.
2.  **Python State Logic:**
    *   **Calibration:** The user sit straight and sets a "baseline" posture.
    *   **Detection:** The system calculates real-time deviations from the baseline.
    *   **Thresholding:** If the user's eyes or shoulders drop below a slouch threshold, or if their shoulders tilt beyond a symmetry threshold for more than 10 consecutive seconds, a "BAD POSTURE" state is triggered.
3.  **Arduino Serial Communication:** Once a state change is detected, Python sends a single-character command (`'B'` for Bad, `'G'` for Good) over a USB Serial connection. The Arduino receives this command and toggles physical actuators.

## Bill of Materials (BOM)

### Hardware
*   **Microcontroller:** Arduino Uno, Nano, or compatible board.
*   **Feedback Device:** 5V Vibration Motor or Piezo Buzzer.
*   **Indicator:** 1x LED (Internal LED on Pin 13 can be used).
*   **Webcam:** Standard USB webcam or integrated laptop camera.
*   **Miscellaneous:** Breadboard, jumper wires, and a USB cable.

### Software
*   **Python 3.10+**
*   **Arduino IDE** (for uploading the firmware)
*   **Arduino Libraries:**
    *   `LiquidCrystal`: For controlling the 16x2 LCD display.
*   **Python Libraries:**
    *   `opencv-python`: For video capture and UI rendering.
    *   `mediapipe`: For high-fidelity pose estimation.
    *   `pyserial`: For communication with the Arduino.

## Setup Instructions

### 1. Hardware Assembly
1.  Connect the positive terminal of the **Vibration Motor** to Digital Pin **8** on the Arduino.
2.  Connect the negative terminal of the motor to **GND**.
3.  (Optional) Connect an external LED to Pin **13** if you prefer a brighter visual indicator than the onboard LED.

### 2. Arduino Firmware
1.  Open `arduino_sketch.ino` in the Arduino IDE.
2.  Select your board and port from the **Tools** menu.
3.  Click **Upload**.

### 3. Python Environment
1.  Navigate to the project directory in your terminal.
2.  Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: The script will automatically download the required `pose_landmarker_lite.task` model file (approx. 3MB) on its first run.*

## Execution Guide

1.  Plug the Arduino into your computer via USB.
2.  Run the Python application:
    ```bash
    python app.py
    ```
3.  **Calibration:**
    *   Position yourself in front of the camera.
    *   Sit with your ideal "Good Posture."
    *   Press the **'c'** key on your keyboard to calibrate the baseline.
4.  **Monitoring:**
    *   The screen will show "STATUS: GOOD" in green.
    *   If you slouch or tilt, a countdown warning will appear.
    *   If the posture isn't corrected within 10 seconds, the status turns red, and the Arduino will trigger the vibration motor.
5.  **Exit:**
    *   Press **'q'** to close the application and stop the serial connection.
