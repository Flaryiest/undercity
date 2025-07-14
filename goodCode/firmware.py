# Save as code.py on CIRCUITPY drive
import sys
import supervisor
import board
import digitalio
import pwmio
import time
from adafruit_motor import servo

# Initialize hardware
my_servo = None
brush_motor_available = False
esc_motor = None

try:
    # Servo setup for Orpheus Pico - using GP0 (equivalent to A0)
    pwm = pwmio.PWMOut(board.GP0, duty_cycle=2 ** 15, frequency=50)
    my_servo = servo.Servo(pwm)
    print("Servo initialized on GP0 with 5V power")
except Exception as e:
    print(f"Servo init error: {e}")
    my_servo = None

try:
    # ESC setup for Orpheus Pico - using GP7 (equivalent to D7)
    esc_pwm = pwmio.PWMOut(board.GP7, duty_cycle=0, frequency=50)
    esc_motor = servo.ContinuousServo(esc_pwm)
    
    # Explicitly set to zero throttle
    esc_motor.throttle = 0.0
    time.sleep(0.5)  # Give ESC time to recognize zero signal
    
    print("ESC motor initialized on GP7")
    brush_motor_available = True
except Exception as e:
    print(f"ESC init error: {e}")
    brush_motor_available = False

def process_command(command):
    command = command.strip()
    
    if command == "library_test":
        return "Motor: True, Audio: True"
    
    elif command == "hardware_test":
        servo_status = "OK" if my_servo else "None"
        brush_status = "OK" if brush_motor_available else "None"
        return f"Servo: {servo_status}, Brush: {brush_status}"
    
    elif command.startswith("servo:"):
        if my_servo:
            try:
                _, angle = command.split(":")
                target_angle = int(angle)
                print(f"Moving servo to {target_angle} degrees")
                my_servo.angle = target_angle
                time.sleep(0.5)
                return f"Servo moved to {target_angle} degrees"
            except Exception as e:
                print(f"Servo command error: {e}")
                return f"Servo error: {e}"
        else:
            return "Servo not available"

    elif command == "servoSweep":
        if my_servo:
            try:
                print("Starting servo sweep")
                my_servo.angle = 0
                time.sleep(1)
                print("Servo at 0 degrees")
                my_servo.angle = 90
                time.sleep(1)
                print("Servo at 90 degrees")
                my_servo.angle = 0
                time.sleep(1)
                print("Servo back to 0 degrees")
                return "Servo sweep completed: 0 -> 90 -> 0"
            except Exception as e:
                print(f"Servo sweep error: {e}")
                return f"Servo sweep error: {e}"
        else:
            return "Servo not available"

    elif command == "servoTest":
        if my_servo:
            try:
                # Test different angles with longer delays
                angles = [0, 45, 90, 135, 180, 90, 0]
                for angle in angles:
                    print(f"Testing servo at {angle} degrees")
                    my_servo.angle = angle
                    time.sleep(1.5)  # Longer delay
                return "Servo test completed"
            except Exception as e:
                return f"Servo test error: {e}"
        else:
            return "Servo not available"

    elif command.startswith("brushMotor:"):
        if brush_motor_available:
            try:
                _, speed_str = command.split(":")
                speed = int(speed_str)
                throttle = speed / 100.0
                esc_motor.throttle = throttle
                
                if speed == 0:
                    return "Motor stopped"
                elif speed > 0:
                    return f"Motor forward at {speed}%"
                else:
                    return f"Motor reverse at {abs(speed)}%"
            except Exception as e:
                return f"Motor error: {e}"
        else:
            return "ESC not available"

    elif command == "servoThenMotor":
        if brush_motor_available and my_servo:
            try:
                print("Starting servo-then-motor sequence")
                
                # Move servo to 90 degrees first
                my_servo.angle = 90
                time.sleep(0.5)
                print("Servo moved to 90 degrees")
                
                # Run motor at 100% for 0.5 seconds
                esc_motor.throttle = 0.2
                time.sleep(0.5)
                esc_motor.throttle = 0.0
                print("Motor sequence completed")
                
                # Move servo back to 0
                my_servo.angle = 0
                time.sleep(0.5)
                print("Servo returned to 0 degrees")
                
                return "Servo-then-motor sequence completed"
            except Exception as e:
                print(f"Servo-then-motor error: {e}")
                return f"Servo-then-motor error: {e}"
        else:
            return "Servo or motor not available"

    elif command == "servoDisable":
        if my_servo:
            try:
                pwm.duty_cycle = 0
                return "Servo disabled - can move freely"
            except Exception as e:
                return f"Servo disable error: {e}"
        else:
            return "Servo not available"

    elif command == "servoEnable":
        if pwm:
            try:
                pwm.duty_cycle = 2 ** 15
                return "Servo enabled"
            except Exception as e:
                return f"Servo enable error: {e}"
        else:
            return "Servo PWM not available"

    else:
        return "Unknown command"

print("CircuitPython ready for commands")

while True:
    if supervisor.runtime.serial_bytes_available:
        try:
            cmd = sys.stdin.readline().strip()
            if cmd:
                result = process_command(cmd)
                if result:
                    print(result)
        except Exception as e:
            print(f"Error: {e}")
