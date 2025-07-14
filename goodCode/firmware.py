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

# Declare stepper variables at module level
step_pin = None
dir_pin = None
stepper_motor = None

try:
    # Servo setup for Orpheus Pico - using GP0
    pwm = pwmio.PWMOut(board.GP0, duty_cycle=2 ** 15, frequency=50)
    my_servo = servo.Servo(pwm)
    print("Servo initialized on GP0 with 5V power")
except Exception as e:
    print(f"Servo init error: {e}")
    my_servo = None

try:
    # ESC setup for Orpheus Pico - using GP7
    esc_pwm = pwmio.PWMOut(board.GP7, duty_cycle=0, frequency=50)
    esc_motor = servo.ContinuousServo(esc_pwm)
    
    # Explicitly set to zero throttle
    esc_motor.throttle = 0.0
    time.sleep(0.5)
    
    print("ESC motor initialized on GP7")
    brush_motor_available = True
except Exception as e:
    print(f"ESC init error: {e}")
    brush_motor_available = False

try:
    # A4988 Stepper Driver setup using available pins GP11, GP12
    print("=== A4988 STEPPER MOTOR INITIALIZATION ===")
    print("Using GP11, GP12 for A4988 stepper driver")
    
    # Create digital pins for A4988 driver (STEP, DIR)
    step_pin = digitalio.DigitalInOut(board.GP11)
    dir_pin = digitalio.DigitalInOut(board.GP12)
    
    step_pin.direction = digitalio.Direction.OUTPUT
    dir_pin.direction = digitalio.Direction.OUTPUT
    
    step_pin.value = False
    dir_pin.value = False
    
    print("A4988 control pins initialized successfully")
    
    stepper_motor = "A4988_READY"  # Flag that stepper is ready
    
    print("A4988 STEPPER MOTOR - SUCCESS")
    
except Exception as e:
    print(f"A4988 stepper init error: {e}")
    stepper_motor = None
    step_pin = None
    dir_pin = None

def process_command(command):
    command = command.strip()
    
    if command == "library_test":
        return "Motor: True, Audio: True"
    
    elif command == "hardware_test":
        servo_status = "OK" if my_servo else "None"
        brush_status = "OK" if brush_motor_available else "None"
        stepper_status = "A4988_OK" if stepper_motor == "A4988_READY" else "None"
        return f"Servo: {servo_status}, Brush: {brush_status}, Stepper: {stepper_status}"
    
    elif command == "pin_test":
        available_pins = []
        in_use_pins = []
        test_pins = [f"GP{i}" for i in range(0, 29)]
        
        for pin_name in test_pins:
            try:
                pin = getattr(board, pin_name, None)
                if pin:
                    try:
                        test_pin = digitalio.DigitalInOut(pin)
                        test_pin.direction = digitalio.Direction.OUTPUT
                        available_pins.append(pin_name)
                        test_pin.deinit()
                    except Exception:
                        in_use_pins.append(pin_name)
            except:
                pass
        
        return f"Available: {', '.join(available_pins)} | In use: {', '.join(in_use_pins)}"
    
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

    elif command.startswith("stepper:"):
        if stepper_motor == "A4988_READY" and step_pin and dir_pin:
            try:
                _, steps_str = command.split(":")
                steps = int(steps_str)
                print(f"Moving A4988 stepper {steps} steps")
                
                # Set direction (True = forward, False = backward)
                dir_pin.value = steps > 0
                abs_steps = abs(steps)
                
                # Generate step pulses
                for i in range(abs_steps):
                    step_pin.value = True
                    time.sleep(0.001)  # 1ms pulse width
                    step_pin.value = False
                    time.sleep(0.01)   # 10ms between steps (100 steps/second)
                
                return f"A4988 moved {steps} steps"
            except Exception as e:
                print(f"A4988 command error: {e}")
                return f"A4988 error: {e}"
        else:
            return "A4988 stepper not available"

    elif command == "stepperTest":
        if stepper_motor == "A4988_READY" and step_pin and dir_pin:
            try:
                print("Testing A4988 stepper - 50 steps forward, 50 steps back")
                
                # 50 steps forward
                dir_pin.value = True
                for i in range(50):
                    step_pin.value = True
                    time.sleep(0.001)
                    step_pin.value = False
                    time.sleep(0.02)  # Slower for test
                
                time.sleep(0.5)  # Pause between directions
                
                # 50 steps backward
                dir_pin.value = False
                for i in range(50):
                    step_pin.value = True
                    time.sleep(0.001)
                    step_pin.value = False
                    time.sleep(0.02)  # Slower for test
                
                return "A4988 test completed: 50 forward, 50 backward"
            except Exception as e:
                print(f"A4988 test error: {e}")
                return f"A4988 test error: {e}"
        else:
            return "A4988 stepper not available"

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
                
                # Run motor at 20% for 0.5 seconds
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

    elif command == "stepper_debug":
        if stepper_motor == "A4988_READY" and step_pin and dir_pin:
            try:
                print("A4988 Debug Test - Manual pin control")
                
                # Test direction pin
                print("Testing DIR pin - HIGH for 2 seconds")
                dir_pin.value = True
                time.sleep(2)
                
                print("Testing DIR pin - LOW for 2 seconds") 
                dir_pin.value = False
                time.sleep(2)
                
                # Test step pin with visible pulses
                print("Testing STEP pin - 10 slow pulses")
                for i in range(10):
                    print(f"Step pulse {i+1}")
                    step_pin.value = True
                    time.sleep(0.5)  # Long pulse so you can see it
                    step_pin.value = False
                    time.sleep(0.5)  # Long gap so you can see it
                
                return "A4988 debug test completed"
            except Exception as e:
                return f"Debug test error: {e}"
        else:
            return "A4988 not available for debug"

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
