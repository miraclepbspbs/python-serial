import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import serial
import serial.tools.list_ports
import threading
import time
import math

class SerialDebugger:
    def __init__(self, root):
        self.root = root
        self.root.title("Serial Port Debugger")
        self.root.geometry("1200x700")
        
        self.serial_port = None
        self.is_open = False
        self.receive_thread = None
        self.running = False
        
        # PID parameters
        self.pid_params = {
            'angle': {'p': tk.DoubleVar(value=0.0), 'i': tk.DoubleVar(value=0.0), 'd': tk.DoubleVar(value=0.0)},
            'speed': {'p': tk.DoubleVar(value=0.0), 'i': tk.DoubleVar(value=0.0), 'd': tk.DoubleVar(value=0.0)},
            'turn': {'p': tk.DoubleVar(value=0.0), 'i': tk.DoubleVar(value=0.0), 'd': tk.DoubleVar(value=0.0)}
        }
        
        # Speed monitoring variables
        self.speed_data = []  # Store speed data
        self.max_data_points = 100  # Maximum points to display
        self.speed_monitoring = False  # Whether speed monitoring is active
        self.speed_pause = False  # Whether graph is paused
        self.last_speed_time = 0  # Last time speed data was received
        
        self.create_widgets()
        self.update_port_list()
        
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # Serial tab
        serial_frame = ttk.Frame(notebook, padding="10")
        notebook.add(serial_frame, text="Serial Debug")
        
        # PID tab
        pid_frame = ttk.Frame(notebook, padding="10")
        notebook.add(pid_frame, text="PID Tuning")
        
        # Configuration frame
        config_frame = ttk.LabelFrame(serial_frame, text="Serial Configuration", padding="10")
        config_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Port selection
        ttk.Label(config_frame, text="Port:").grid(row=0, column=0, sticky=tk.W)
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(config_frame, textvariable=self.port_var, width=15)
        self.port_combo.grid(row=0, column=1, padx=(5, 10), sticky=tk.W)
        
        # Refresh button
        self.refresh_btn = ttk.Button(config_frame, text="Refresh", command=self.update_port_list)
        self.refresh_btn.grid(row=0, column=2, padx=(0, 10))
        
        # Baudrate selection
        ttk.Label(config_frame, text="Baudrate:").grid(row=0, column=3, sticky=tk.W)
        self.baudrate_var = tk.StringVar(value="9600")
        baudrate_combo = ttk.Combobox(config_frame, textvariable=self.baudrate_var, width=10)
        baudrate_combo['values'] = ("9600", "19200", "38400", "57600", "115200")
        baudrate_combo.grid(row=0, column=4, padx=(5, 10), sticky=tk.W)
        
        # Data bits
        ttk.Label(config_frame, text="Data Bits:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.databits_var = tk.StringVar(value="8")
        databits_combo = ttk.Combobox(config_frame, textvariable=self.databits_var, width=10)
        databits_combo['values'] = ("5", "6", "7", "8")
        databits_combo.grid(row=1, column=1, padx=(5, 10), sticky=tk.W, pady=(5, 0))
        
        # Stop bits
        ttk.Label(config_frame, text="Stop Bits:").grid(row=1, column=2, sticky=tk.W, pady=(5, 0))
        self.stopbits_var = tk.StringVar(value="1")
        stopbits_combo = ttk.Combobox(config_frame, textvariable=self.stopbits_var, width=10)
        stopbits_combo['values'] = ("1", "1.5", "2")
        stopbits_combo.grid(row=1, column=3, padx=(5, 10), sticky=tk.W, pady=(5, 0))
        
        # Parity
        ttk.Label(config_frame, text="Parity:").grid(row=1, column=4, sticky=tk.W, pady=(5, 0))
        self.parity_var = tk.StringVar(value="None")
        parity_combo = ttk.Combobox(config_frame, textvariable=self.parity_var, width=10)
        parity_combo['values'] = ("None", "Even", "Odd", "Mark", "Space")
        parity_combo.grid(row=1, column=5, padx=(5, 0), sticky=tk.W, pady=(5, 0))
        
        # Connect button
        self.connect_btn = ttk.Button(config_frame, text="Connect", command=self.toggle_connection)
        self.connect_btn.grid(row=0, column=6, rowspan=2, padx=(10, 0), pady=(5, 0))
        
        # Send frame
        send_frame = ttk.LabelFrame(serial_frame, text="Send Data", padding="10")
        send_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Send text area
        self.send_text = scrolledtext.ScrolledText(send_frame, height=4)
        self.send_text.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        send_frame.columnconfigure(0, weight=1)
        
        # Send options
        self.send_hex_var = tk.BooleanVar()
        send_hex_check = ttk.Checkbutton(send_frame, text="Hex Format", variable=self.send_hex_var)
        send_hex_check.grid(row=1, column=0, sticky=tk.W)
        
        # Send button
        self.send_btn = ttk.Button(send_frame, text="Send", command=self.send_data)
        self.send_btn.grid(row=1, column=2, sticky=tk.E)
        
        # Receive frame
        receive_frame = ttk.LabelFrame(serial_frame, text="Received Data", padding="10")
        receive_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        serial_frame.rowconfigure(2, weight=1)
        serial_frame.columnconfigure(0, weight=1)
        
        # Receive text area
        self.receive_text = scrolledtext.ScrolledText(receive_frame, height=15)
        self.receive_text.grid(row=0, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        receive_frame.rowconfigure(0, weight=1)
        receive_frame.columnconfigure(0, weight=1)
        
        # Receive options
        self.receive_hex_var = tk.BooleanVar()
        receive_hex_check = ttk.Checkbutton(receive_frame, text="Hex Format", variable=self.receive_hex_var)
        receive_hex_check.grid(row=1, column=0, sticky=tk.W)
        
        # Auto scroll
        self.auto_scroll_var = tk.BooleanVar(value=True)
        auto_scroll_check = ttk.Checkbutton(receive_frame, text="Auto Scroll", variable=self.auto_scroll_var)
        auto_scroll_check.grid(row=1, column=1, sticky=tk.W)
        
        # Clear button
        self.clear_btn = ttk.Button(receive_frame, text="Clear", command=self.clear_received)
        self.clear_btn.grid(row=1, column=2, sticky=tk.E)
        
        # Save button
        self.save_btn = ttk.Button(receive_frame, text="Save Log", command=self.save_log)
        self.save_btn.grid(row=1, column=3, sticky=tk.E, padx=(5, 0))
        
        # PID Tuning Frame
        pid_control_frame = ttk.LabelFrame(pid_frame, text="PID Parameters", padding="10")
        pid_control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        pid_frame.columnconfigure(0, weight=1)
        pid_frame.rowconfigure(0, weight=1)
        
        # Angle PID
        angle_frame = ttk.LabelFrame(pid_control_frame, text="Angle Control", padding="5")
        angle_frame.grid(row=0, column=0, padx=(0, 10), sticky=(tk.W, tk.E))
        self.create_pid_sliders(angle_frame, "angle", 0)
        
        # Speed PID
        speed_frame = ttk.LabelFrame(pid_control_frame, text="Speed Control", padding="5")
        speed_frame.grid(row=0, column=1, padx=(0, 10), sticky=(tk.W, tk.E))
        self.create_pid_sliders(speed_frame, "speed", 1)
        
        # Turn PID
        turn_frame = ttk.LabelFrame(pid_control_frame, text="Turn Control", padding="5")
        turn_frame.grid(row=0, column=2, padx=(0, 10), sticky=(tk.W, tk.E))
        self.create_pid_sliders(turn_frame, "turn", 2)
        
        # PID Value Display
        self.pid_value_labels = {}
        for i, control_type in enumerate(['angle', 'speed', 'turn']):
            self.pid_value_labels[control_type] = {}
            for j, param in enumerate(['p', 'i', 'd']):
                label = ttk.Label(pid_control_frame, text=f"{control_type.capitalize()} {param.upper()}: 0.00")
                label.grid(row=j+1, column=i, padx=5, pady=2)  # Fixed grid positioning
                self.pid_value_labels[control_type][param] = label
        
        # PID Control Buttons
        pid_btn_frame = ttk.Frame(pid_control_frame)
        pid_btn_frame.grid(row=4, column=0, columnspan=3, pady=(10, 0), sticky=tk.E)
        
        self.load_pid_btn = ttk.Button(pid_btn_frame, text="Load from Device", command=self.load_pid_params)
        self.load_pid_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.save_pid_btn = ttk.Button(pid_btn_frame, text="Save to Device", command=self.save_pid_params)
        self.save_pid_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.reset_pid_btn = ttk.Button(pid_btn_frame, text="Reset Fields", command=self.reset_pid_params)
        self.reset_pid_btn.pack(side=tk.LEFT)
        
        # Speed Monitoring Frame
        speed_monitor_frame = ttk.LabelFrame(pid_frame, text="Speed Monitoring", padding="10")
        speed_monitor_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        pid_frame.columnconfigure(1, weight=2)
        
        # Canvas for graph
        self.speed_canvas = tk.Canvas(speed_monitor_frame, bg="white", height=200)
        self.speed_canvas.grid(row=0, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        speed_monitor_frame.rowconfigure(0, weight=1)
        speed_monitor_frame.columnconfigure(0, weight=1)
        
        # Speed monitoring controls
        self.start_speed_btn = ttk.Button(speed_monitor_frame, text="Start Monitoring", command=self.start_speed_monitoring)
        self.start_speed_btn.grid(row=1, column=0, padx=(0, 5))
        
        self.pause_speed_btn = ttk.Button(speed_monitor_frame, text="Pause", command=self.toggle_speed_pause)
        self.pause_speed_btn.grid(row=1, column=1, padx=(0, 5))
        
        self.clear_speed_btn = ttk.Button(speed_monitor_frame, text="Clear", command=self.clear_speed_data)
        self.clear_speed_btn.grid(row=1, column=2, padx=(0, 5))
        
        # Speed value display
        self.speed_value_label = ttk.Label(speed_monitor_frame, text="Current Speed: 0.00")
        self.speed_value_label.grid(row=1, column=3, padx=(10, 0))
        
        # PID Communication Log
        pid_log_frame = ttk.LabelFrame(pid_frame, text="Communication Log", padding="10")
        pid_log_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        pid_frame.rowconfigure(1, weight=1)
        
        self.pid_log_text = scrolledtext.ScrolledText(pid_log_frame, height=8)
        self.pid_log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        pid_log_frame.rowconfigure(0, weight=1)
        pid_log_frame.columnconfigure(0, weight=1)
        
        # Bind events to update labels when sliders change
        for control_type in self.pid_params:
            for param in self.pid_params[control_type]:
                self.pid_params[control_type][param].trace('w', self.update_pid_labels)
        
    def create_pid_sliders(self, parent, control_type, row):
        # P parameter
        ttk.Label(parent, text="P:").grid(row=0, column=0, sticky=tk.W, pady=2)
        p_scale = ttk.Scale(parent, from_=0, to=100, variable=self.pid_params[control_type]['p'], 
                           orient=tk.HORIZONTAL, length=200)
        p_scale.grid(row=0, column=1, padx=(5, 10), pady=2, sticky=tk.W)
        
        # I parameter
        ttk.Label(parent, text="I:").grid(row=1, column=0, sticky=tk.W, pady=2)
        i_scale = ttk.Scale(parent, from_=0, to=100, variable=self.pid_params[control_type]['i'], 
                           orient=tk.HORIZONTAL, length=200)
        i_scale.grid(row=1, column=1, padx=(5, 10), pady=2, sticky=tk.W)
        
        # D parameter
        ttk.Label(parent, text="D:").grid(row=2, column=0, sticky=tk.W, pady=2)
        d_scale = ttk.Scale(parent, from_=0, to=100, variable=self.pid_params[control_type]['d'], 
                           orient=tk.HORIZONTAL, length=200)
        d_scale.grid(row=2, column=1, padx=(5, 10), pady=2, sticky=tk.W)
        
    def update_pid_labels(self, *args):
        for control_type in self.pid_params:
            for param in self.pid_params[control_type]:
                value = self.pid_params[control_type][param].get()
                self.pid_value_labels[control_type][param].config(
                    text=f"{control_type.capitalize()} {param.upper()}: {value:.2f}"
                )
                
    def start_speed_monitoring(self):
        """
        Start monitoring speed data from the device
        """
        if not self.is_open or not self.serial_port:
            messagebox.showwarning("Not Connected", "Please connect to a serial port first")
            return
            
        self.speed_monitoring = True
        self.speed_pause = False
        self.pause_speed_btn.config(text="Pause")
        
        try:
            # Send command to start speed monitoring
            self.serial_port.write(b"START_SPEED\n")
            self.pid_log_message("Sent: START_SPEED\n")
        except Exception as e:
            messagebox.showerror("Send Error", f"Failed to send speed monitoring command: {str(e)}")
            
    def toggle_speed_pause(self):
        """
        Toggle pause state of speed monitoring
        """
        self.speed_pause = not self.speed_pause
        self.pause_speed_btn.config(text="Resume" if self.speed_pause else "Pause")
        if not self.speed_pause:
            self.pid_log_message("Speed graph resumed\n")
        else:
            self.pid_log_message("Speed graph paused\n")
            
    def clear_speed_data(self):
        """
        Clear speed data and graph
        """
        self.speed_data = []
        self.last_speed_time = 0
        self.speed_canvas.delete("all")
        self.speed_value_label.config(text="Current Speed: 0.00")
        self.pid_log_message("Speed data cleared\n")
        
    def add_speed_data(self, speed):
        """
        Add speed data point and update graph
        """
        current_time = time.time() * 1000000  # microseconds
        
        # Add new data point
        self.speed_data.append((current_time, speed))
        
        # Keep only the latest data points
        if len(self.speed_data) > self.max_data_points:
            self.speed_data.pop(0)
            
        # Update speed value display
        self.speed_value_label.config(text=f"Current Speed: {speed:.2f}")
        
        # Update graph if not paused
        if not self.speed_pause:
            self.update_speed_graph()
            
    def update_speed_graph(self):
        """
        Update the speed graph display
        """
        if not self.speed_data:
            return
            
        # Clear canvas
        self.speed_canvas.delete("all")
        
        # Graph dimensions
        canvas_width = self.speed_canvas.winfo_width()
        canvas_height = self.speed_canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            return
            
        # Padding
        padding = 20
        graph_width = canvas_width - 2 * padding
        graph_height = canvas_height - 2 * padding
        
        # Find min and max values
        min_time = min(data[0] for data in self.speed_data)
        max_time = max(data[0] for data in self.speed_data)
        min_speed = min(data[1] for data in self.speed_data)
        max_speed = max(data[1] for data in self.speed_data)
        
        # Add some padding to y-axis
        speed_range = max_speed - min_speed
        if speed_range == 0:
            speed_range = 1
        min_speed -= speed_range * 0.1
        max_speed += speed_range * 0.1
        
        # Time range
        time_range = max_time - min_time
        if time_range == 0:
            time_range = 1
            
        # Draw grid lines and labels
        self.speed_canvas.create_line(padding, padding, padding, canvas_height - padding, fill="gray")
        self.speed_canvas.create_line(padding, canvas_height - padding, canvas_width - padding, canvas_height - padding, fill="gray")
        
        # Draw data points
        if len(self.speed_data) > 1:
            points = []
            for i, (t, speed) in enumerate(self.speed_data):
                x = padding + (t - min_time) / time_range * graph_width
                y = canvas_height - padding - (speed - min_speed) / (max_speed - min_speed) * graph_height
                points.append(x)
                points.append(y)
                
            # Draw line connecting points
            self.speed_canvas.create_line(points, fill="blue", width=2)
            
            # Draw data points
            for i in range(0, len(points), 2):
                x, y = points[i], points[i+1]
                self.speed_canvas.create_oval(x-2, y-2, x+2, y+2, fill="red", outline="red")
            
    def update_port_list(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combo['values'] = ports
        if ports and not self.port_var.get():
            self.port_var.set(ports[0])
            
    def toggle_connection(self):
        if not self.is_open:
            self.connect_serial()
        else:
            self.disconnect_serial()
            
    def connect_serial(self):
        try:
            port = self.port_var.get()
            baudrate = int(self.baudrate_var.get())
            databits = int(self.databits_var.get())
            
            # Map stop bits
            stopbits_map = {"1": serial.STOPBITS_ONE, 
                           "1.5": serial.STOPBITS_ONE_POINT_FIVE, 
                           "2": serial.STOPBITS_TWO}
            stopbits = stopbits_map[self.stopbits_var.get()]
            
            # Map parity
            parity_map = {"None": serial.PARITY_NONE,
                         "Even": serial.PARITY_EVEN,
                         "Odd": serial.PARITY_ODD,
                         "Mark": serial.PARITY_MARK,
                         "Space": serial.PARITY_SPACE}
            parity = parity_map[self.parity_var.get()]
            
            # Create serial port object
            self.serial_port = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=databits,
                stopbits=stopbits,
                parity=parity,
                timeout=1
            )
            
            self.is_open = True
            self.connect_btn.config(text="Disconnect")
            self.send_btn.config(state=tk.NORMAL)
            self.load_pid_btn.config(state=tk.NORMAL)
            self.save_pid_btn.config(state=tk.NORMAL)
            self.start_speed_btn.config(state=tk.NORMAL)
            
            # Start receiving thread
            self.running = True
            self.receive_thread = threading.Thread(target=self.receive_data, daemon=True)
            self.receive_thread.start()
            
            self.log_message(f"Connected to {port} at {baudrate} baud\n")
            self.pid_log_message(f"Connected to {port} at {baudrate} baud\n")
            
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect: {str(e)}")
            
    def disconnect_serial(self):
        try:
            self.running = False
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
                
            self.is_open = False
            self.connect_btn.config(text="Connect")
            self.send_btn.config(state=tk.DISABLED)
            self.load_pid_btn.config(state=tk.DISABLED)
            self.save_pid_btn.config(state=tk.DISABLED)
            self.start_speed_btn.config(state=tk.DISABLED)
            
            # Stop speed monitoring
            self.speed_monitoring = False
            
            self.log_message("Disconnected\n")
            self.pid_log_message("Disconnected\n")
            
        except Exception as e:
            messagebox.showerror("Disconnection Error", f"Failed to disconnect: {str(e)}")
            
    def send_data(self):
        if not self.is_open or not self.serial_port:
            messagebox.showwarning("Not Connected", "Please connect to a serial port first")
            return
            
        try:
            data = self.send_text.get("1.0", tk.END).strip()
            if not data:
                return
                
            if self.send_hex_var.get():
                # Convert hex string to bytes
                data = data.replace(" ", "").replace("\n", "").replace("\r", "")
                if len(data) % 2 != 0:
                    data = "0" + data  # Pad with leading zero if needed
                byte_data = bytes.fromhex(data)
                self.serial_port.write(byte_data)
                self.log_message(f"Sent (HEX): {data}\n")
            else:
                # Send as ASCII string
                self.serial_port.write(data.encode('utf-8'))
                self.log_message(f"Sent: {data}\n")
                
            # Clear send text area
            self.send_text.delete("1.0", tk.END)
            
        except Exception as e:
            messagebox.showerror("Send Error", f"Failed to send data: {str(e)}")
            
    def receive_data(self):
        while self.running and self.serial_port and self.serial_port.is_open:
            try:
                if self.serial_port.in_waiting > 0:
                    data = self.serial_port.read(self.serial_port.in_waiting)
                    if data:
                        self.root.after(0, self.display_received_data, data)
                time.sleep(0.00001)  # 10us sleep to meet timing requirements
            except Exception as e:
                self.root.after(0, messagebox.showerror, "Receive Error", f"Failed to receive data: {str(e)}")
                break
                
    def display_received_data(self, data):
        try:
            if self.receive_hex_var.get():
                # Display as hex
                hex_data = data.hex()
                # Format hex data in groups of two characters
                formatted_hex = ' '.join(hex_data[i:i+2] for i in range(0, len(hex_data), 2))
                self.receive_text.insert(tk.END, formatted_hex + ' ')
            else:
                # Display as ASCII
                decoded_data = data.decode('utf-8', errors='replace')
                self.receive_text.insert(tk.END, decoded_data)
                
                # Check if this is speed data
                if self.speed_monitoring:
                    self.parse_speed_data(decoded_data)
                
            # Auto scroll to bottom
            if self.auto_scroll_var.get():
                self.receive_text.see(tk.END)
                
        except Exception as e:
            messagebox.showerror("Display Error", f"Failed to display received data: {str(e)}")
            
    def parse_speed_data(self, data):
        """
        Parse speed data from received string
        Expected format: "SPEED:left_speed:right_speed\n"
        """
        lines = data.split('\n')
        for line in lines:
            if line.startswith("SPEED:"):
                try:
                    # Parse speed data
                    parts = line.split(':')
                    if len(parts) >= 2:
                        speeds = parts[1].split(',')
                        if len(speeds) >= 2:
                            left_speed = float(speeds[0])
                            right_speed = float(speeds[1])
                            # Use average of both wheels
                            avg_speed = (left_speed + right_speed) / 2
                            self.add_speed_data(avg_speed)
                except Exception as e:
                    pass  # Ignore parsing errors
                    
    def log_message(self, message):
        self.receive_text.insert(tk.END, message)
        if self.auto_scroll_var.get():
            self.receive_text.see(tk.END)
            
    def pid_log_message(self, message):
        self.pid_log_text.insert(tk.END, message)
        self.pid_log_text.see(tk.END)
            
    def clear_received(self):
        self.receive_text.delete("1.0", tk.END)
        
    def save_log(self):
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            if file_path:
                content = self.receive_text.get("1.0", tk.END)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                messagebox.showinfo("Save Log", "Log saved successfully")
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save log: {str(e)}")
            
    def load_pid_params(self):
        """
        Load PID parameters from the device
        Sends command to request current PID parameters
        """
        if not self.is_open or not self.serial_port:
            messagebox.showwarning("Not Connected", "Please connect to a serial port first")
            return
            
        try:
            # Send command to request PID parameters
            # Using a common format: "GET_PID\n"
            self.serial_port.write(b"GET_PID\n")
            self.pid_log_message("Sent: GET_PID\n")
        except Exception as e:
            messagebox.showerror("Send Error", f"Failed to send PID request: {str(e)}")
            
    def save_pid_params(self):
        """
        Save current PID parameters to the device
        """
        if not self.is_open or not self.serial_port:
            messagebox.showwarning("Not Connected", "Please connect to a serial port first")
            return
            
        try:
            # Format PID parameters for sending to device
            angle_p = self.pid_params['angle']['p'].get()
            angle_i = self.pid_params['angle']['i'].get()
            angle_d = self.pid_params['angle']['d'].get()
            
            speed_p = self.pid_params['speed']['p'].get()
            speed_i = self.pid_params['speed']['i'].get()
            speed_d = self.pid_params['speed']['d'].get()
            
            turn_p = self.pid_params['turn']['p'].get()
            turn_i = self.pid_params['turn']['i'].get()
            turn_d = self.pid_params['turn']['d'].get()
            
            # Send command to set PID parameters
            # Using a common format: "SET_PID angle_p angle_i angle_d speed_p speed_i speed_d turn_p turn_i turn_d\n"
            pid_cmd = f"SET_PID {angle_p} {angle_i} {angle_d} {speed_p} {speed_i} {speed_d} {turn_p} {turn_i} {turn_d}\n"
            self.serial_port.write(pid_cmd.encode('utf-8'))
            self.pid_log_message(f"Sent: {pid_cmd}")
        except Exception as e:
            messagebox.showerror("Send Error", f"Failed to send PID parameters: {str(e)}")
            
    def reset_pid_params(self):
        """
        Reset PID parameter fields to zero
        """
        for control_type in self.pid_params:
            for param in self.pid_params[control_type]:
                self.pid_params[control_type][param].set(0.0)
        self.pid_log_message("PID fields reset to zero\n")

def main():
    root = tk.Tk()
    app = SerialDebugger(root)
    root.mainloop()

if __name__ == "__main__":
    main()