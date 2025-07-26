import serial
import serial.tools.list_ports
import threading
import sys
import argparse

class SerialCLI:
    def __init__(self, port, baudrate=9600, bytesize=8, parity='N', stopbits=1):
        self.serial_port = None
        self.running = False
        self.port = port
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.parity = parity
        self.stopbits = stopbits
        
    def connect(self):
        """Connect to the serial port"""
        try:
            # Map parity string to serial constants
            parity_map = {
                'N': serial.PARITY_NONE,
                'E': serial.PARITY_EVEN,
                'O': serial.PARITY_ODD,
                'M': serial.PARITY_MARK,
                'S': serial.PARITY_SPACE
            }
            
            # Map stopbits to serial constants
            stopbits_map = {
                1: serial.STOPBITS_ONE,
                1.5: serial.STOPBITS_ONE_POINT_FIVE,
                2: serial.STOPBITS_TWO
            }
            
            self.serial_port = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=self.bytesize,
                parity=parity_map[self.parity],
                stopbits=stopbits_map[self.stopbits],
                timeout=1
            )
            
            print(f"Connected to {self.port} at {self.baudrate} baud")
            return True
            
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False
            
    def disconnect(self):
        """Disconnect from the serial port"""
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            print("Disconnected")
            
    def receive_data(self):
        """Receive data in a separate thread"""
        while self.running:
            try:
                if self.serial_port.in_waiting > 0:
                    data = self.serial_port.read(self.serial_port.in_waiting)
                    if data:
                        # Print received data as both hex and ASCII
                        print(f"RX HEX: {data.hex()}")
                        try:
                            ascii_data = data.decode('utf-8')
                            print(f"RX ASCII: {ascii_data}")
                        except UnicodeDecodeError:
                            print("RX ASCII: (unreadable)")
                # Small delay to prevent high CPU usage
                import time
                time.sleep(0.01)
            except Exception as e:
                if self.running:  # Only print error if we're still supposed to be running
                    print(f"Receive error: {e}")
                break
                
    def send_data(self, data, is_hex=False):
        """Send data to the serial port"""
        if not self.serial_port or not self.serial_port.is_open:
            print("Not connected to a serial port")
            return
            
        try:
            if is_hex:
                # Remove spaces and convert hex string to bytes
                hex_data = data.replace(" ", "").replace("\n", "").replace("\r", "")
                if len(hex_data) % 2 != 0:
                    hex_data = "0" + hex_data
                byte_data = bytes.fromhex(hex_data)
                self.serial_port.write(byte_data)
                print(f"Sent (HEX): {hex_data}")
            else:
                self.serial_port.write(data.encode('utf-8'))
                print(f"Sent: {data}")
        except Exception as e:
            print(f"Send error: {e}")
            
    def run(self):
        """Run the main loop"""
        if not self.connect():
            return
            
        self.running = True
        
        # Start receive thread
        receive_thread = threading.Thread(target=self.receive_data, daemon=True)
        receive_thread.start()
        
        print("Serial terminal started. Type your messages and press Enter to send.")
        print("Commands:")
        print("  !hex <data> - Send hex data")
        print("  !quit - Exit the program")
        print("-" * 40)
        
        try:
            while self.running:
                user_input = input()
                
                if user_input.lower() == "!quit":
                    self.running = False
                    break
                elif user_input.startswith("!hex "):
                    hex_data = user_input[5:]  # Remove "!hex " prefix
                    self.send_data(hex_data, is_hex=True)
                elif user_input:
                    self.send_data(user_input, is_hex=False)
                    
        except KeyboardInterrupt:
            print("\nInterrupted by user")
        finally:
            self.running = False
            self.disconnect()

def list_ports():
    """List all available serial ports"""
    ports = serial.tools.list_ports.comports()
    if not ports:
        print("No serial ports found")
        return
        
    print("Available serial ports:")
    for port in ports:
        print(f"  {port.device}: {port.description}")

def main():
    parser = argparse.ArgumentParser(description="Serial Port CLI Debugger")
    parser.add_argument("-p", "--port", help="Serial port to connect to")
    parser.add_argument("-b", "--baudrate", type=int, default=9600, help="Baudrate (default: 9600)")
    parser.add_argument("-d", "--databits", type=int, default=8, choices=[5, 6, 7, 8], help="Data bits (default: 8)")
    parser.add_argument("--parity", default="N", choices=["N", "E", "O", "M", "S"], 
                        help="Parity (N=None, E=Even, O=Odd, M=Mark, S=Space) (default: N)")
    parser.add_argument("--stopbits", type=float, default=1, choices=[1, 1.5, 2], help="Stop bits (default: 1)")
    parser.add_argument("-l", "--list", action="store_true", help="List available serial ports")
    
    args = parser.parse_args()
    
    # List ports if requested
    if args.list:
        list_ports()
        return
    
    # Check if port is specified
    if not args.port:
        print("Error: No serial port specified")
        print("Use -l to list available ports or -p to specify a port")
        return
    
    # Create and run the CLI debugger
    cli = SerialCLI(
        port=args.port,
        baudrate=args.baudrate,
        bytesize=args.databits,
        parity=args.parity,
        stopbits=args.stopbits
    )
    cli.run()

if __name__ == "__main__":
    main()