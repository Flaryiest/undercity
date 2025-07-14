import cv2
import numpy as np
import time
import math
from music import CycleMusic, play_squid_music, stop_music
import torch
import torch.nn.functional as F
from torchvision.transforms import Compose
import urllib.request
import os
import serial
import serial.tools.list_ports

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def find_xiao_port():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if "usbmodem" in port.device.lower() or "2e8a" in str(port.hwid):
            return port.device
    return None

try:
    PORT = find_xiao_port() or "/dev/cu.usbmodem11401"
    ser = serial.Serial(PORT, 115200, timeout=1)
    time.sleep(2)
    print(f"Connected to Xiao RP2040 on {PORT}")
    
    ser.write(b'\x03')
    time.sleep(0.5)
    ser.write(b'\x04')
    time.sleep(3)
    
    while ser.in_waiting > 0:
        ser.read(ser.in_waiting)
        time.sleep(0.1)
        
    motor_available = True
    print("Motor control ready")
except Exception as e:
    print(f"Motor connection failed: {e}")
    motor_available = False
    ser = None

def send_motor_command(cmd):
    """Send command to Xiao RP2040 and get response"""
    if not motor_available or ser is None:
        return "Motor not available"
    
    try:
        ser.write((cmd + "\r\n").encode("utf-8"))
        time.sleep(0.1)
        
        attempts = 0
        while attempts < 5:  # 0.5 second timeout
            if ser.in_waiting > 0:
                response = ser.readline().decode('utf-8', errors='ignore').strip()
                if response and not response.startswith('>>>') and response != cmd:
                    return response
            time.sleep(0.1)
            attempts += 1
        return "No response"
    except Exception as e:
        return f"Error: {e}"

def trigger_motor_and_servo():
    """Trigger servo first, then motor using combined command"""
    if motor_available:
        print("Motion detected! Running servo-then-motor sequence...")
        send_motor_command("servoThenMotor")
        print("Servo-then-motor sequence completed")

try:
    model_type = "MiDaS_small"
    midas = torch.hub.load("intel-isl/MiDaS", model_type, trust_repo=True)
    midas.to(device)
    midas.eval()
    
    midas_transforms = torch.hub.load("intel-isl/MiDaS", "transforms", trust_repo=True)
    transform = midas_transforms.small_transform
    print("MiDaS model loaded")
except Exception as e:
    print(f"Error loading MiDaS: {e}")
    midas = None
    transform = None

def estimate_depth(frame):
    if midas is None:
        return None
    
    try:
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        input_batch = transform(rgb_frame).to(device)
        
        with torch.no_grad():
            prediction = midas(input_batch)
            
            prediction = F.interpolate(
                prediction.unsqueeze(1),
                size=frame.shape[:2],
                mode="bicubic",
                align_corners=False,
            ).squeeze()
        
        depth_map = prediction.cpu().numpy()
        
        depth_normalized = cv2.normalize(depth_map, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
        
        return depth_map, depth_normalized
    
    except Exception as e:
        print(f"Error in depth estimation: {e}")
        return None, None

def get_object_depth(depth_map, center_x, center_y, window_size=20):
    if depth_map is None:
        return None
    
    half_window = window_size // 2
    x_start = max(0, center_x - half_window)
    x_end = min(depth_map.shape[1], center_x + half_window)
    y_start = max(0, center_y - half_window)
    y_end = min(depth_map.shape[0], center_y + half_window)
    
    roi = depth_map[y_start:y_end, x_start:x_end]
    
    return np.median(roi)

cap = cv2.VideoCapture(0)

output_width = 1280
output_height = 720

fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter('depth_motion_output.avi', fourcc, 20.0, (output_width, output_height))

# Create TWO separate background subtractors
background_subtractor_active = cv2.createBackgroundSubtractorMOG2(
    detectShadows=True,
    varThreshold=50,
    history=800
)

background_subtractor_pause = cv2.createBackgroundSubtractorMOG2(
    detectShadows=True,
    varThreshold=50,
    history=800
)

motion_threshold = 7000

print("Starting 60-second recording with AI depth estimation")
print("Motion detection cycles: OFF for first 6 seconds, then ON for 6 seconds")
print("Music: Squid music plays initially, then switches to green/red light cycling")
print("Press 'q' to quit early")

start_time = time.time()
recording_duration = 60  
cycle_duration = 6 

frame_center_x = output_width // 2
frame_center_y = output_height // 2

play_squid_music() 

cycle_music = CycleMusic(cycle_duration=6)
music_switched = False

depth_frame_skip = 5
frame_counter = 0
last_depth_map = None
last_depth_normalized = None

last_motion_trigger = 0
motion_cooldown = 2.0  # 2 seconds between triggers instead of 1.0
previous_detection_state = False
state_change_buffer_time = 2.0  
state_change_time = 0
contour_groups = []

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    elapsed_time = time.time() - start_time
    if elapsed_time >= recording_duration:
        print(f"\n60 seconds completed. Recording finished.")
        break
    
    frame = cv2.resize(frame, (output_width, output_height))
    frame_counter += 1

    if not music_switched and elapsed_time >= cycle_duration:
        print("Starting green/red light sound effects (squid music continues)...")
        cycle_music.start()
        music_switched = True

    current_music_state = "squid"
    music_remaining = 0
    if music_switched:
        current_music_state, music_remaining = cycle_music.update()

    crosshair_size = 20
    cv2.line(frame, (frame_center_x - crosshair_size, frame_center_y), 
             (frame_center_x + crosshair_size, frame_center_y), (255, 255, 255), 2)
    cv2.line(frame, (frame_center_x, frame_center_y - crosshair_size), 
             (frame_center_x, frame_center_y + crosshair_size), (255, 255, 255), 2)

    if midas is not None and frame_counter % depth_frame_skip == 0:
        depth_result = estimate_depth(frame)
        if depth_result[0] is not None:
            last_depth_map, last_depth_normalized = depth_result

    cycle_position = elapsed_time % (cycle_duration * 2)
    motion_detection_active = cycle_position >= cycle_duration
    
    # Detect state changes and completely reset background models
    state_just_changed = motion_detection_active != previous_detection_state
    if state_just_changed:
        state_change_time = elapsed_time
        print(f"Motion detection state changed to: {'ON' if motion_detection_active else 'OFF'}")
        
        # Reset contour_groups when state changes
        contour_groups = []
        
        # COMPLETE RESET: Create fresh background subtractors
        if motion_detection_active:
            # Starting motion detection - create fresh subtractor
            background_subtractor_active = cv2.createBackgroundSubtractorMOG2(
                detectShadows=True,
                varThreshold=50,
                history=800
            )
            print("Created fresh background model for motion detection")
        else:
            # Starting pause - create fresh subtractor
            background_subtractor_pause = cv2.createBackgroundSubtractorMOG2(
                detectShadows=True,
                varThreshold=50,
                history=800
            )
            print("Created fresh background model for pause period")
    
    # Check if we're in the buffer period after state change
    in_buffer_period = state_just_changed and (elapsed_time - state_change_time) < state_change_buffer_time
    
    motion_detected = False
    motion_count = 0
    
    if motion_detection_active:
        if in_buffer_period:
            # During buffer period, just learn background without detecting motion
            background_subtractor_active.apply(frame, learningRate=0.3)  # Very fast learning
            motion_detected = False
            contour_groups = []  # Reset during buffer period
            print(f"Buffer period: {state_change_buffer_time - (elapsed_time - state_change_time):.1f}s remaining")
        else:
            # Normal motion detection with completely fresh background model
            fg_mask = background_subtractor_active.apply(frame, learningRate=0.002)
            
            # More aggressive morphological operations
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (16, 16))
            fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
            fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
            
            kernel_erode = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (8, 8))
            fg_mask = cv2.erode(fg_mask, kernel_erode, iterations=2)
            fg_mask = cv2.dilate(fg_mask, kernel_erode, iterations=2)
            
            contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter and validate contours
            valid_contours = []
            for contour in contours:
                area = cv2.contourArea(contour)
                
                if area > motion_threshold:
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h if h > 0 else 0
                    
                    if 0.3 < aspect_ratio < 3.0:
                        hull = cv2.convexHull(contour)
                        hull_area = cv2.contourArea(hull)
                        solidity = area / hull_area if hull_area > 0 else 0
                        
                        if solidity > 0.5:
                            perimeter = cv2.arcLength(contour, True)
                            if perimeter > 0:
                                circularity = 4 * np.pi * area / (perimeter * perimeter)
                                if circularity > 0.3:
                                    valid_contours.append(contour)
            
            # Group nearby contours
            def group_nearby_contours(contours, max_distance=150):
                if not contours:
                    return []
                
                centers = []
                for contour in contours:
                    M = cv2.moments(contour)
                    if M["m00"] != 0:
                        cx = int(M["m10"] / M["m00"])
                        cy = int(M["m01"] / M["m00"])
                        centers.append((cx, cy, contour))
                
                groups = []
                used = set()
                
                for i, (cx1, cy1, contour1) in enumerate(centers):
                    if i in used:
                        continue
                    
                    group = [(cx1, cy1, contour1)]
                    used.add(i)
                    
                    for j, (cx2, cy2, contour2) in enumerate(centers[i+1:], i+1):
                        if j in used:
                            continue
                        
                        distance = math.sqrt((cx1 - cx2)**2 + (cy1 - cy2)**2)
                        if distance <= max_distance:
                            group.append((cx2, cy2, contour2))
                            used.add(j)
                    
                    total_area = sum(cv2.contourArea(item[2]) for item in group)
                    if total_area > motion_threshold * 0.5:
                        groups.append(group)
                
                return groups
            
            contour_groups = group_nearby_contours(valid_contours)
            
            all_motion_points = []
            total_area = 0
            
            for group in contour_groups:
                group_area = sum(cv2.contourArea(item[2]) for item in group)
                weighted_x = sum(item[0] * cv2.contourArea(item[2]) for item in group) / group_area
                weighted_y = sum(item[1] * cv2.contourArea(item[2]) for item in group) / group_area
                
                all_motion_points.append((int(weighted_x), int(weighted_y), group_area))
                total_area += group_area
                motion_detected = True
            
            # Motor trigger with short cooldown to prevent spam
            if motion_detected and total_area > 10000 and (elapsed_time - last_motion_trigger) > motion_cooldown:
                print(f"Motion area: {total_area} - triggering motor/servo")
                time.sleep(0.3)
                trigger_motor_and_servo()
                last_motion_trigger = elapsed_time  # Update the trigger time
            
            # Draw detection results
            if motion_detected and all_motion_points:
                for center_x, center_y, area in all_motion_points:
                    box_size = min(300, max(150, int(math.sqrt(area/10))))
                    half_size = box_size // 2
                    
                    x1 = max(0, center_x - half_size)
                    y1 = max(0, center_y - half_size)
                    x2 = min(output_width, center_x + half_size)
                    y2 = min(output_height, center_y + half_size)
                    
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 4)
                    cv2.putText(frame, f"MOTION GROUP", (center_x - 80, center_y - 20), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                    cv2.circle(frame, (center_x, center_y), 6, (0, 255, 0), -1)
                    cv2.putText(frame, f"Area: {int(area)}", (center_x - 60, center_y + 40), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        motion_count = len(contour_groups) if 'contour_groups' in locals() else 0
    else:
        # During pause, use separate background subtractor
        background_subtractor_pause.apply(frame, learningRate=0.01)  # Moderate learning
        contour_groups = []  # Reset during pause
    
    previous_detection_state = motion_detection_active
    
    if motion_detection_active:
        detection_status = "MOTION DETECTION: ON"
        detection_color = (0, 255, 0)
        if motion_detected:
            status_text = "MOTION DETECTED"
            status_color = (0, 255, 0)
        else:
            status_text = "NO MOTION"
            status_color = (255, 255, 255)
    else:
        detection_status = "MOTION DETECTION: OFF"
        detection_color = (0, 0, 255)
        status_text = "DETECTION PAUSED"
        status_color = (128, 128, 128)
    
    cv2.putText(frame, detection_status, (20, 50), 
               cv2.FONT_HERSHEY_SIMPLEX, 1.0, detection_color, 3)
    
    cv2.putText(frame, status_text, (20, 100), 
               cv2.FONT_HERSHEY_SIMPLEX, 1.0, status_color, 3)
    
    depth_status = "AI DEPTH: ON" if midas is not None else "AI DEPTH: FAILED"
    depth_color = (0, 255, 255) if midas is not None else (0, 0, 255)
    cv2.putText(frame, depth_status, (20, 150), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.8, depth_color, 2)
    
    cv2.putText(frame, "RECORDING", (20, 190), 
               cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
    
    remaining_time = recording_duration - elapsed_time
    cv2.putText(frame, f"Time left: {remaining_time:.1f}s", (20, 230), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
    
    if motion_detection_active:
        cycle_remaining = (cycle_duration * 2) - cycle_position
    else:
        cycle_remaining = cycle_duration - cycle_position
    
    cycle_status = "ON" if motion_detection_active else "OFF"
    cv2.putText(frame, f"Cycle: {cycle_status} ({cycle_remaining:.1f}s left)", (20, 270), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
    
    if music_switched:
        music_display = f"Music: squid + {current_music_state}-light ({music_remaining:.1f}s)"
        music_color = (0, 255, 0) if current_music_state == "green" else (0, 0, 255)
    else:
        music_display = f"Music: squid only ({(cycle_duration - elapsed_time):.1f}s left)"
        music_color = (255, 255, 0)
    
    cv2.putText(frame, music_display, (20, 330), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, music_color, 2)
    
    if motion_detection_active:
        cv2.putText(frame, f"Motion objects: {motion_count}", (20, 300), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    out.write(frame)
    
    cv2.imshow('AI Depth Motion Detection', frame)
    
    if last_depth_normalized is not None:
        depth_display = cv2.resize(last_depth_normalized, (320, 240))
        cv2.imshow('Depth Map', depth_display)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        print(f"\nRecording stopped early at {elapsed_time:.1f} seconds")
        break

cap.release()
out.release()
cv2.destroyAllWindows()

if motor_available and ser:
    send_motor_command("brushMotor:0")  # Ensure motor is stopped
    ser.close()

stop_music()


