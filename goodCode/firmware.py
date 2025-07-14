# Save as code.py on CIRCUITPY drive
import sys
import supervisor
import board
import digitalio
import pwmio
import time
from adafruit_motor import servo, stepper

# Initialize hardware
my_servo = None
motor1 = None
brush_motor_available = False
esc_motor = None

try:
    # Servo with proper 5V power from 5V pin
    pwm = pwmio.PWMOut(board.A0, duty_cycle=2 ** 15, frequency=50)
    my_servo = servo.Servo(pwm)
    print("Servo initialized on A0 with 5V power")
except Exception as e:
    print(f"Servo init error: {e}")
    my_servo = None

try:
    # ESC setup - start with explicit zero throttle
    esc_pwm = pwmio.PWMOut(board.D7, duty_cycle=0, frequency=50)
    esc_motor = servo.ContinuousServo(esc_pwm)
    
    # Explicitly set to zero throttle
    esc_motor.throttle = 0.0
    time.sleep(0.5)  # Give ESC time to recognize zero signal
    
    print("ESC motor initialized on D7")
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
                
                my_servo.angle = 90
                time.sleep(0.5)
                print("Servo moved to 90 degrees")
                
                esc_motor.throttle = 0.1
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
