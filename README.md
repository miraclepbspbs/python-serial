# Serial Port Debugger Tools
```bash
python serial_debugger.py
```

This repository contains two Python-based serial port debugging tools:
1. A GUI-based debugger using tkinter with PID tuning capabilities
2. A command-line interface (CLI) debugger

## Requirements

- Python 3.6+
- pyserial package

To install the required package:
```bash
pip install pyserial
```

## Files

- [serial_debugger.py](file:///c%3A/Users/30408/Desktop/%E6%96%B0%E5%BB%BA%E6%96%87%E4%BB%B6%E5%A4%B9/serial_debugger.py) - GUI version of the serial debugger with PID tuning
- [serial_cli.py](file:///c%3A/Users/30408/Desktop/%E6%96%B0%E5%BB%BA%E6%96%87%E4%BB%B6%E5%A4%B9/serial_cli.py) - Command-line version of the serial debugger

## GUI Serial Debugger

### Features

- User-friendly graphical interface with tabbed layout
- Serial port configuration (baudrate, data bits, stop bits, parity)
- Real-time sending and receiving of data
- Support for both ASCII and hexadecimal formats
- Auto-scroll and clear functions
- Save received data to log files
- **PID parameter tuning for STM32F103C8T6 balance car**

### Usage

Run the GUI debugger:

```bash
python serial_debugger.py
```

### How to Use

#### Serial Debug Tab
1. Select the serial port from the dropdown (click "Refresh" to update the list)
2. Configure the serial port parameters:
   - Baudrate: Common values are 9600, 19200, 38400, 57600, 115200
   - Data Bits: 5, 6, 7, or 8
   - Stop Bits: 1, 1.5, or 2
   - Parity: None, Even, Odd, Mark, or Space
3. Click "Connect" to establish connection
4. Type data in the "Send Data" area and click "Send" to transmit
5. Received data will appear in the "Received Data" area
6. Use "Hex Format" checkboxes to send/receive data in hexadecimal
7. Use "Clear" to clear the received data area
8. Use "Save Log" to save the received data to a file

#### PID Tuning Tab
The PID tuning tab is specifically designed for STM32F103C8T6 balance cars and allows you to:
1. Set parameters for three PID controllers:
   - **Angle Control**: Maintains the upright position of the balance car
   - **Speed Control**: Controls the movement speed of the car
   - **Turn Control**: Controls the turning direction of the car
2. Load current parameters from the device using "Load from Device"
3. Save parameters to the device using "Save to Device"
4. Reset all fields to zero using "Reset Fields"

The communication with the balance car uses these commands:
- `GET_PID` - Request current PID parameters from the device
- `SET_PID <angle_p> <angle_i> <angle_d> <speed_p> <speed_i> <speed_d> <turn_p> <turn_i> <turn_d>` - Set PID parameters

Note: Your STM32F103C8T6 balance car firmware must support these commands for the PID tuning to work.

## Command-Line Serial Debugger

### Features

- Lightweight terminal-based interface
- Full serial port configuration through command-line arguments
- Real-time data sending and receiving
- Support for both ASCII and hexadecimal formats

### Usage

List available serial ports:
```bash
python serial_cli.py -l
```

Connect to a serial port:
```bash
python serial_cli.py -p PORT [-b BAUDRATE] [--parity PARITY] [--stopbits STOPBITS]
```

Example:
```bash
python serial_cli.py -p COM1 -b 9600
```

### Command-Line Arguments

- `-p PORT`, `--port PORT`: Serial port to connect to (e.g., COM1, /dev/ttyUSB0)
- `-b BAUDRATE`, `--baudrate BAUDRATE`: Baudrate (default: 9600)
- `-d DATABITS`, `--databits DATABITS`: Data bits (5, 6, 7, or 8, default: 8)
- `--parity PARITY`: Parity (N=None, E=Even, O=Odd, M=Mark, S=Space, default: N)
- `--stopbits STOPBITS`: Stop bits (1, 1.5, or 2, default: 1)
- `-l`, `--list`: List available serial ports

### In-Program Commands

Once connected, you can:
- Type messages and press Enter to send them as ASCII
- Use `!hex DATA` to send hexadecimal data (e.g., `!hex 48656c6c6f`)
- Use `!quit` to exit the program

## License

This project is open source.