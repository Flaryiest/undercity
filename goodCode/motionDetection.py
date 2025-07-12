import cv2
import numpy as np
import time
import math
import music

cap = cv2.VideoCapture(0)

output_width = 1280
output_height = 720

fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter('continuous_output.avi', fourcc, 20.0, (output_width, output_height))

background_subtractor = cv2.createBackgroundSubtractorMOG2(detectShadows=True)
motion_threshold = 1000  

print("Starting 60-second recording with motion detection...")
print("Motion detection cycles: ON for 6 seconds, OFF for 6 seconds")
print("Press 'q' to quit early")

start_time = time.time()
recording_duration = 60  
cycle_duration = 6 

frame_center_x = output_width // 2  # 640
frame_center_y = output_height // 2  # 360

music.play_squid_music()

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    elapsed_time = time.time() - start_time
    if elapsed_time >= recording_duration:
        print(f"\n60 seconds completed! Recording finished.")
        break
    
    frame = cv2.resize(frame, (output_width, output_height))

    crosshair_size = 20
    cv2.line(frame, (frame_center_x - crosshair_size, frame_center_y), 
             (frame_center_x + crosshair_size, frame_center_y), (255, 255, 255), 2)
    cv2.line(frame, (frame_center_x, frame_center_y - crosshair_size), 
             (frame_center_x, frame_center_y + crosshair_size), (255, 255, 255), 2)

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
            
            cv2.putText(frame, f"Distance: {distance_pixels:.1f}px", (center_x - 100, center_y + 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            cv2.putText(frame, f"X: {distance_x:+d}, Y: {distance_y:+d}", (center_x - 100, center_y + 80), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            cv2.putText(frame, f"Total Area: {int(total_area)}", (center_x - 100, center_y + 110), 
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
    
    cv2.putText(frame, "RECORDING", (20, 150), 
               cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
    
    remaining_time = recording_duration - elapsed_time
    cv2.putText(frame, f"Time left: {remaining_time:.1f}s", (20, 200), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
    
    cycle_remaining = cycle_duration - (cycle_position if motion_detection_active else (cycle_position - cycle_duration))
    cycle_status = "ON" if motion_detection_active else "OFF"
    cv2.putText(frame, f"Cycle: {cycle_status} ({cycle_remaining:.1f}s left)", (20, 250), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
    
    if motion_detection_active:
        cv2.putText(frame, f"Motion objects: {motion_count}", (20, 290), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    out.write(frame)
    
    cv2.imshow('Motion Detection - 60 Second Recording', frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        print(f"\nRecording stopped early at {elapsed_time:.1f} seconds")
        break

cap.release()
out.release()
cv2.destroyAllWindows()

print("Recording saved as 'continuous_output.avi'")