import cv2
import numpy as np
import time
import math
import music
import torch
import torch.nn.functional as F
from torchvision.transforms import Compose
import urllib.request
import os

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

print("Loading MiDaS depth estimation model...")
try:
    model_type = "MiDaS_small"
    midas = torch.hub.load("intel-isl/MiDaS", model_type, trust_repo=True)
    midas.to(device)
    midas.eval()
    
    midas_transforms = torch.hub.load("intel-isl/MiDaS", "transforms", trust_repo=True)
    transform = midas_transforms.small_transform
    print("MiDaS model loaded successfully!")
except Exception as e:
    print(f"Error loading MiDaS: {e}")
    print("Falling back to motion detection without depth...")
    midas = None
    transform = None

def estimate_depth(frame):
    """Estimate depth using MiDaS model"""
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
    """Get average depth at object center"""
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

background_subtractor = cv2.createBackgroundSubtractorMOG2(detectShadows=True)
motion_threshold = 1000

print("Starting 60-second recording with AI depth estimation...")
print("Motion detection cycles: ON for 6 seconds, OFF for 6 seconds")
print("Press 'q' to quit early")

start_time = time.time()
recording_duration = 60  
cycle_duration = 6 

frame_center_x = output_width // 2
frame_center_y = output_height // 2

music.play_squid_music()

depth_frame_skip = 5
frame_counter = 0
last_depth_map = None
last_depth_normalized = None

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    elapsed_time = time.time() - start_time
    if elapsed_time >= recording_duration:
        print(f"\n60 seconds completed! Recording finished.")
        break
    
    frame = cv2.resize(frame, (output_width, output_height))
    frame_counter += 1

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
    motion_detection_active = cycle_position < cycle_duration
    
    motion_detected = False
    motion_count = 0
    
    if motion_detection_active:
        fg_mask = background_subtractor.apply(frame)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (8, 8))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
        
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        all_motion_points = []
        total_area = 0
        
        for contour in contours:
            area = cv2.contourArea(contour)
            
            if area > motion_threshold:
                motion_detected = True
                
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    all_motion_points.append((cx, cy, area))
                    total_area += area
        
        if motion_detected and all_motion_points:
            weighted_x = sum(point[0] * point[2] for point in all_motion_points) / total_area
            weighted_y = sum(point[1] * point[2] for point in all_motion_points) / total_area
            
            center_x = int(weighted_x)
            center_y = int(weighted_y)
            
            distance_x = center_x - frame_center_x
            distance_y = center_y - frame_center_y
            distance_pixels = math.sqrt(distance_x**2 + distance_y**2)
            
            object_depth = None
            depth_confidence = "N/A"
            
            if last_depth_map is not None:
                object_depth = get_object_depth(last_depth_map, center_x, center_y)
                if object_depth is not None:
                    depth_relative = object_depth
                    depth_confidence = f"{depth_relative:.1f}"
            
            box_size = 200
            half_size = box_size // 2
            
            x1 = max(0, center_x - half_size)
            y1 = max(0, center_y - half_size)
            x2 = min(output_width, center_x + half_size)
            y2 = min(output_height, center_y + half_size)
            
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 4)
            
            cv2.putText(frame, "MOTION CENTER", (center_x - 100, center_y - 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)
            
            cv2.circle(frame, (center_x, center_y), 8, (0, 255, 0), -1)
            
            cv2.line(frame, (frame_center_x, frame_center_y), (center_x, center_y), (255, 0, 255), 3)
            
            cv2.putText(frame, f"2D Distance: {distance_pixels:.1f}px", (center_x - 120, center_y + 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            cv2.putText(frame, f"X: {distance_x:+d}, Y: {distance_y:+d}", (center_x - 120, center_y + 80), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            if object_depth is not None:
                cv2.putText(frame, f"Rel. Depth: {depth_confidence}", (center_x - 120, center_y + 110), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            else:
                cv2.putText(frame, "Depth: Processing...", (center_x - 120, center_y + 110), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (128, 128, 128), 2)
            
            cv2.putText(frame, f"Total Area: {int(total_area)}", (center_x - 120, center_y + 140), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        motion_count = len([c for c in contours if cv2.contourArea(c) > motion_threshold])
    else:
        background_subtractor.apply(frame, learningRate=0.01)
    
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
    
    cycle_remaining = cycle_duration - (cycle_position if motion_detection_active else (cycle_position - cycle_duration))
    cycle_status = "ON" if motion_detection_active else "OFF"
    cv2.putText(frame, f"Cycle: {cycle_status} ({cycle_remaining:.1f}s left)", (20, 270), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
    
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

print("Recording saved as 'depth_motion_output.avi'")