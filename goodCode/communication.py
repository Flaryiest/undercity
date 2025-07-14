import serial
import serial.tools.list_ports
import time

def find_xiao_port():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if "usbmodem" in port.device.lower() or "2e8a" in str(port.hwid):
            return port.device
    return None

def find_xiao_ports():
    ports = serial.tools.list_ports.comports()
    xiao_ports = []
    for port in ports:
        if "usbmodem" in port.device.lower() or "2e8a" in str(port.hwid):
            xiao_ports.append(port.device)
    return sorted(xiao_ports)

xiao_ports = find_xiao_ports()
if len(xiao_ports) >= 2:
    PORT = xiao_ports[1] 
else:
    PORT = find_xiao_port() or "/dev/cu.usbmodem11401"

BAUD = 115200

try:
    ser = serial.Serial(PORT, BAUD, timeout=2)
    time.sleep(1)
    print(f"Connected to Xiao RP2040 on {PORT}")
    

    ser.write(b'\x03')
    time.sleep(0.5)
    
    ser.write(b'\x04')
    time.sleep(5)
    
    while ser.in_waiting > 0:
        ser.read(ser.in_waiting)
        time.sleep(0.1)
    
    print("Waiting for CircuitPython to be ready...")
    ready = False
    start_time = time.time()
    while not ready and (time.time() - start_time) < 10:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            print(f"Received: {line}")
            if "ready for commands" in line:
                ready = True
        time.sleep(0.1)
    
    if not ready:
        print("Warning: Didn't receive ready message")
    
    def send_command(cmd, timeout=10):
        print(f"Sending: {cmd}")
        ser.write((cmd + "\r\n").encode("utf-8"))
        time.sleep(0.1)
        
        response = ""
        attempts = 0
        max_attempts = timeout * 10  # 10 attempts per second
        while attempts < max_attempts:  
            if ser.in_waiting > 0:
                data = ser.readline().decode('utf-8', errors='ignore').strip()
                if data and not data.startswith('>>>') and not data.startswith('...') and data != cmd:
                    return data
            time.sleep(0.1)
            attempts += 1
        return "No response"

    print("\nTesting commands:")
    time.sleep(2) 
    print("Response:", send_command("library_test"))
    time.sleep(0.5)
    print("Response:", send_command("hardware_test"))
    time.sleep(2)

    print("Response:", send_command("servoTest"))
    time.sleep(6)
    ser.close()
    
except serial.SerialException as e:
    print(f"Error connecting to {PORT}: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
