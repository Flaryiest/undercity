import serial
import serial.tools.list_ports
import time

def find_xiao_port():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if "usbmodem" in port.device.lower() or "2e8a" in str(port.hwid):
            return port.device
    return None

PORT = find_xiao_port() or "/dev/cu.usbmodem11401"
BAUD = 115200

try:
    ser = serial.Serial(PORT, BAUD, timeout=2)
    time.sleep(1)
    print(f"Connected to Orpheus Pico on {PORT}")
    
    # Reset and initialize
    ser.write(b'\x03')
    time.sleep(0.5)
    ser.write(b'\x04')
    time.sleep(3)
    
    while ser.in_waiting > 0:
        ser.read(ser.in_waiting)
        time.sleep(0.1)
    
    def send_command(cmd, timeout=15):
        print(f"\nSending: {cmd}")
        ser.write((cmd + "\r\n").encode("utf-8"))
        time.sleep(0.2)
        
        attempts = 0
        max_attempts = timeout * 10
        while attempts < max_attempts:  
            if ser.in_waiting > 0:
                data = ser.readline().decode('utf-8', errors='ignore').strip()
                if data and not data.startswith('>>>') and not data.startswith('...') and data != cmd:
                    print(f"Response: {data}")
                    return data
            time.sleep(0.1)
            attempts += 1
        print("Response: No response")
        return "No response"

    print("\n" + "="*50)
    print("    A4988 STEPPER MOTOR DEBUG TEST")
    print("="*50)
    
    # 1. Check hardware status
    print("\n1. HARDWARE STATUS CHECK:")
    send_command("hardware_test")
    
    # 2. Check pin status
    print("\n2. PIN STATUS CHECK:")
    send_command("pin_test")
    
    # 3. Debug test - check pin signals
    print("\n3. PIN SIGNAL DEBUG TEST:")
    print("   This will test DIR and STEP pins with slow signals")
    print("   Check with multimeter or LED:")
    print("   - GP11 (STEP) should pulse HIGH/LOW")
    print("   - GP12 (DIR) should go HIGH then LOW")
    print("   Starting debug test...")
    
 
    print("   6b. Large backward movement (100 steps):")
    send_command("brushMotor:30")
    time.sleep(5)
    
    # 7. Final status check
    print("\n7. FINAL STATUS CHECK:")
    send_command("hardware_test")
    
    print("\n" + "="*50)
    print("    STEPPER DEBUG TEST COMPLETED")
    print("="*50)
    print("\nIf the motor didn't move, check:")
    print("1. A4988 wiring:")
    print("   - STEP → GP11")
    print("   - DIR → GP12") 
    print("   - VDD → 3.3V")
    print("   - GND → GND")
    print("   - VMOT → 12V motor power")
    print("   - ENABLE → GND (or floating)")
    print("2. Stepper motor connections to A4988 (1A,1B,2A,2B)")
    print("3. Power supply (12V for motor)")
    print("4. A4988 current adjustment (potentiometer)")
    
    ser.close()
    
except serial.SerialException as e:
    print(f"Error connecting to {PORT}: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
