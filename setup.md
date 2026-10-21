
# PurifyX - Complete Setup and Hardware Requirements

## 1. Project Overview

PurifyX is an AI-powered water quality assessment and experimental treatment prototype combining an ESP32 microcontroller, water quality sensors, an AI classification model, a Python desktop dashboard, and a nanoparticle-based filtration system.

The system is designed to collect sensor readings, classify water conditions, display results, record measurements, and generate PDF reports.

The AI classification categories are:
- Safe
- Treat
- Unsafe
- Uncertain

IMPORTANT: PurifyX is an experimental prototype, not a certified drinking-water safety device. AI predictions, sensor readings, filtration performance, and visual clarity do not independently establish that water is safe to drink.

## 2. Repository Structure

Recommended project structure:

purifyx-ai-water-monitoring/
├── README.md
├── SETUP.md
├── requirements.txt
├── .gitignore
├── purifyx_dashboard.py
├── purifyx_esp32.ino
├── model/
│   └── README.md
├── hardware/
│   ├── README.md
│   └── wiring.md
└── results/
    └── README.md

The filenames above are examples. Retain the actual filenames used by the project.

## 3. Software Requirements

### A. Python Dashboard

Required software:
- Python 3
- pip, Python's package installer
- Visual Studio Code or another Python editor
- USB serial drivers appropriate for the ESP32 development board, if required

Recommended: Python 3.11 in a virtual environment, subject to compatibility with the project's AI and GUI dependencies.

Verify Python installation:

    py --version
    py -m pip --version

If the commands are unavailable, install Python from:

https://www.python.org/downloads/

On Windows, enable the option to add Python to PATH during installation if offered.

### B. Install Python Dependencies

Open PowerShell or the VS Code terminal in the project directory.

Create a virtual environment:

    py -m venv .venv

Activate it:

    .venv\Scripts\Activate.ps1

If PowerShell blocks activation, use Command Prompt instead:

    .venv\Scripts\activate.bat

Upgrade pip:

    python -m pip install --upgrade pip

Install dependencies:

    python -m pip install -r requirements.txt

The requirements file should contain every third-party package imported by the Python application or required by its model runtime.

### C. Run the Python Dashboard

Connect the ESP32 to the computer using a USB data cable.

Check the COM port in Windows Device Manager under Ports (COM & LPT).

From the project directory, run:

    python purifyx_dashboard.py

Replace the filename with the actual Python entry-point filename if different.

If the application cannot connect to the ESP32, verify:
- The correct COM port is selected.
- The USB cable supports data transfer.
- The firmware is running.
- The serial baud rate matches between the firmware and Python application.
- No other program is using the same COM port.

The exact serial baud rate and dashboard configuration must be checked against the source code.

## 4. ESP32 Firmware Requirements

### A. Required Software

Install Arduino IDE:

https://www.arduino.cc/en/software

Install the ESP32 board support package through Arduino IDE's Boards Manager. Select the package published by Espressif Systems.

Official installation instructions:

https://docs.espressif.com/projects/arduino-esp32/en/latest/installing.html

### B. Firmware Libraries

The firmware may require the following libraries, depending on the actual source code:

- Wire: I2C communication, normally included with the ESP32 Arduino core.
- LiquidCrystal_I2C: I2C LCD control, if used by the firmware.
- OneWire: communication with OneWire temperature sensors.
- DallasTemperature: high-level support for compatible Dallas/Maxim temperature sensors.

Install external libraries using Arduino IDE's Library Manager.

Only install libraries that the actual firmware imports. The exact LCD library and temperature sensor model must be confirmed from the source code and bill of materials.

### C. Compile and Upload

1. Open Arduino IDE.
2. Open the actual ESP32 firmware file.
3. Select the appropriate ESP32 board.
4. Select the correct serial port.
5. Install any missing libraries reported by the compiler.
6. Compile the sketch.
7. Connect the ESP32 using a USB data cable.
8. Upload the firmware.
9. Open Serial Monitor to inspect sensor readings and diagnostic messages.

The board model, upload settings, and serial baud rate must match the hardware and firmware configuration.

The Arduino `.ino` format uses C++ syntax and the Arduino framework, even though the code is commonly referred to as ESP32 C code.

## 5. Hardware Components

The following components are identified in the current PurifyX design notes. Verify exact manufacturers, module variants, and quantities against the physical prototype.

| Component | Purpose |
|---|---|
| ESP32 development board | Main microcontroller for sensor acquisition and system control |
| pH sensor module and probe | Measures the pH of the water sample |
| Turbidity sensor module | Estimates water cloudiness |
| TDS sensor module and probe | Estimates total dissolved solids using the sensor's electrical measurement |
| Temperature sensor | Measures water temperature; confirm the exact model |
| I2C-compatible LCD | Displays system information and readings |
| Indicator LEDs | Provide visual status indications |
| Push buttons | Provide user input or control functions |
| Buzzer | Provides audible alerts |
| Nanoparticle-based filtration assembly | Experimental water-treatment stage |
| USB data cable | Provides programming and serial communication with the ESP32 |
| Breadboard or PCB, jumper wires and suitable connectors | Electrical interconnections and prototyping |

Additional supplies may be required depending on the physical implementation, including a suitable power supply, sensor interface boards, calibration solutions, tubing, filter housing, and filtration materials.

Do not assume that every item above has been independently verified against the final bill of materials.

## 6. ESP32 GPIO Pin Assignments

The following assignments reflect the current project notes. Confirm them against the firmware before wiring or modifying the hardware.

| Component / Signal | ESP32 GPIO or Address |
|---|---|
| pH sensor analog signal | GPIO 34 |
| Turbidity sensor analog signal | GPIO 35 |
| Temperature sensor OneWire data | GPIO 4 |
| TDS sensor analog signal | GPIO 12 |
| LED output 1 | GPIO 26 |
| LED output 2 | GPIO 27 |
| LED output 3 | GPIO 14 |
| LED output 4 | GPIO 25 |
| Push button 1 | GPIO 13 |
| Push button 2 | GPIO 33 |
| Push button 3 | GPIO 32 |
| Buzzer | GPIO 18 |
| I2C LCD address | 0x27 |

### Wiring Notes

- Connect all modules to an appropriate common ground.
- Verify the supply voltage and output-voltage limits of every sensor module before connecting it to the ESP32.
- ESP32 GPIOs are not generally 5 V tolerant. Do not feed a 5 V signal directly into an ESP32 input.
- GPIO 34 and GPIO 35 are input-only pins on the classic ESP32 and are suitable for analog input.
- GPIO 12 has boot-strapping implications on common ESP32 variants. Confirm that the TDS module's output and startup behavior do not interfere with booting.
- The LCD's I2C address is recorded as 0x27. Its SDA and SCL pins must be verified from the firmware and board configuration.
- The four LEDs' individual colors and meanings must be documented from the actual wiring and code.
- Button wiring, pull-up or pull-down configuration, and active logic levels must match the firmware.
- Never connect an unverified sensor output directly to the board.

## 7. AI Model Requirements

PurifyX uses an AI classification workflow associated with Edge Impulse.

Recorded model information:
- Project identifier: xo_nebula-project-1
- Classification categories: Safe, Treat, Unsafe, Uncertain
- Previously reported accuracy: 99.93%
- Previously reported training records: 226,171
- Previously reported validation records: 56,543

These values should be accompanied by the evaluation method, dataset description, split strategy, and class-wise metrics when available.

The exact runtime requirements depend on how inference is performed:
- If inference occurs remotely or through an Edge Impulse service, document that service and its requirements.
- If inference runs locally in Python, document the model format and runtime dependencies.
- If inference runs directly on the ESP32, document the model deployment format and firmware libraries.

Do not assume a particular inference method until it has been confirmed from the implementation.

## 8. Running the Complete System

1. Inspect the sensor wiring and verify power connections.
2. Upload the ESP32 firmware.
3. Connect the ESP32 to the computer through USB.
4. Identify the correct COM port.
5. Activate the Python virtual environment.
6. Install the required Python packages.
7. Run the Python dashboard.
8. Confirm that readings are being received and displayed correctly.
9. Test logging, classification, and PDF report generation.
10. Record the initial and final sensor readings for controlled filtration experiments.

Keep sensor calibration, sample preparation, test conditions, and limitations documented so results can be reproduced.

## 9. Troubleshooting

### Python package errors

Install the missing package in the active virtual environment and update requirements.txt if it is a genuine project dependency.

### COM port unavailable

Check Device Manager, the USB cable, board drivers, and whether another application is using the port.

### No sensor readings

Verify wiring, GPIO assignments, sensor supply voltage, ground connections, sensor calibration, and firmware diagnostics.

### LCD blank

Check power, SDA/SCL wiring, contrast, and the configured I2C address.

### ESP32 upload failure

Verify the selected board and COM port. Check the USB data cable and board-specific boot or reset procedure.

### Incorrect AI classification

Check sensor calibration, input units, feature ordering, preprocessing, and model compatibility.

## 10. Safety and Limitations

PurifyX is a research and demonstration prototype.

- Visual clarity is not proof of potable water.
- TDS and turbidity measurements do not detect every chemical or biological hazard.
- A pH reading alone does not establish drinking-water safety.
- AI classifications must not be treated as a substitute for accredited laboratory testing.
- Nanoparticle-based filtration must be evaluated for particle release, residual contaminants, and treatment effectiveness.
- Do not consume experimental treated water unless its safety has been independently established through appropriate testing.

## 11. Future Improvements

- Add a verified wiring diagram and bill of materials.
- Record exact software and library versions.
- Add reproducible sensor calibration procedures.
- Document the model's evaluation methodology and class-wise performance.
- Add before-and-after measurements with controlled test conditions.
- Include prototype photographs and a demonstration video.
- Document known bugs, limitations, and future hardware revisions.
