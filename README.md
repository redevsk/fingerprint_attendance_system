# Fingerprint Attendance System

A complete biometric attendance tracking solution that combines Arduino-based fingerprint scanning with a Python desktop application for attendance management.

## Overview

This system allows educational institutions or organizations to track attendance using fingerprint biometrics. It consists of two main components:

1. **Arduino Fingerprint Sensor Module**: Hardware component that captures and processes fingerprints
2. **Python Desktop Application**: GUI application for managing users, viewing attendance logs, and registering fingerprints

## Features

- Secure biometric attendance tracking
- Real-time attendance logging with time-in and time-out functionality
- User registration and management
- Fingerprint enrollment and deletion
- Attendance log viewing and filtering by date
- Export attendance data to CSV
- LCD display for user feedback
- Audible feedback (beeps) for successful/failed operations

## Hardware Requirements

- Arduino board (Uno/Nano/Mega)
- Fingerprint sensor module (compatible with Adafruit Fingerprint library)
- 16x2 I2C LCD display
- Buzzer
- Connecting wires
- USB cable for Arduino-PC connection

## Software Requirements

- Arduino IDE
- Python 3.x
- Required Python libraries:
  - tkinter (GUI)
  - pyserial (Arduino communication)
  - mysql-connector-python (Database)

## Installation

### Arduino Setup

1. Connect the hardware components:
   - Fingerprint sensor to pins 2 (RX) and 3 (TX)
   - I2C LCD to SDA/SCL pins
   - Buzzer to pin 13

2. Install required Arduino libraries:
   - Adafruit Fingerprint Sensor Library
   - LiquidCrystal I2C Library

3. Upload the `FP_sensor.ino` sketch to your Arduino board

### Python Application Setup

1. Install required Python libraries:
   ```
   pip install pyserial mysql-connector-python
   ```

2. Set up a MySQL server (e.g., XAMPP, WAMP, or standalone MySQL)

3. Run the Python application:
   ```
   python attendance_system.py
   ```
   - The application will automatically create the required database and tables

## Usage

### Time In/Out Tab

1. Place a registered finger on the sensor
2. The system will identify the user and record attendance
3. First scan of the day records "Time In"
4. Subsequent scan records "Time Out"

### Logs Tab

- View attendance records filtered by date
- Click "Today" to view current day's records
- Click "Refresh" to update the view
- Click "Export to CSV" to save attendance data

### Registration Tab

- Add new users with student ID, name, and course information
- Select a user and click "Register Fingerprint" to enroll their fingerprint
- Follow the on-screen instructions to complete fingerprint enrollment
- Fingerprints can be deleted if needed

## Arduino-Python Communication

The Arduino and Python application communicate via serial connection. The Arduino sends fingerprint scan results and enrollment status, while the Python application sends commands for mode changes and fingerprint operations.

## Database Structure

The system uses a MySQL database with two main tables:

1. **users**: Stores user information and fingerprint registration status
2. **attendance**: Records time-in and time-out data for each user

## Troubleshooting

### Arduino Detection Issues

If the Python application cannot detect the Arduino:

1. **Reset the Arduino**:
   - Press the reset button on the Arduino board
   - Disconnect and reconnect the USB cable

2. **Close and Restart**:
   - Close the Arduino IDE completely
   - Close the Python application
   - Restart the Python application

3. **Try Different USB Ports**:
   - If the issue persists, try connecting the Arduino to a different USB port
   - Some USB ports may have power or driver issues

4. **Check COM Port**:
   - Open Device Manager (Windows) or Terminal (Mac/Linux) to verify the Arduino is recognized
   - Note the correct COM port number and update it in the application if needed

5. **Driver Issues**:
   - Reinstall Arduino drivers if necessary
   - For Windows, you might need to install/update the FTDI or CH340 drivers

6. **Cable Problems**:
   - Try a different USB cable as some cables may be charge-only

### Fingerprint Sensor Limitations and Issues

- **Storage Capacity**: The AS608 fingerprint sensor supports storing only 1-127 fingerprint images. Attempting to store more than 127 fingerprints may cause unpredictable behavior or system failures.
- **Memory Management**: When approaching the maximum capacity (127 fingerprints), consider deleting unused fingerprints to maintain system stability.
- **Recognition Accuracy**: The sensor may have difficulty recognizing fingerprints if they are dirty, wet, or positioned incorrectly.
- **Enrollment Quality**: For best results, ensure proper finger positioning during enrollment and require multiple scans for each fingerprint.

### Other Common Issues

- **Arduino Connection Issues**: Check COM port settings and ensure the Arduino is properly connected
- **Database Connection Issues**: Verify MySQL server is running and credentials are correct
- **Fingerprint Recognition Problems**: Try re-enrolling the fingerprint with better positioning
- **Serial Communication Errors**: Verify baud rate settings match between Arduino code and Python application

## Files Description

- **FP_sensor.ino**: Arduino sketch for fingerprint sensor control
- **attendance_system.py**: Python application for the GUI and database management
- **attendance_logs_*.csv**: Exported attendance data files

## License

This project is available for educational and personal use.

## Credits

This system uses the following open-source libraries:
- Adafruit Fingerprint Sensor Library
- LiquidCrystal I2C Library
- Python tkinter, pyserial, and mysql-connector libraries
