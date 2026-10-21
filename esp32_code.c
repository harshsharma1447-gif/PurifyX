
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <xo_nebula-project-1_inferencing.h>

// ================= LCD =================
LiquidCrystal_I2C lcd(0x27, 16, 2);

// ================= SENSOR PINS =================
#define PH_PIN         34
#define TURBIDITY_PIN  35
#define TEMP_PIN       4
#define TDS_PIN        12   // NEW: TDS analog pin

// ================= LED PINS =================
#define GREEN_LED  26
#define YELLOW_LED 27
#define RED_LED    14
#define BLUE_LED   25

// ================= BUTTON PINS =================
#define MODE_BUTTON 13
#define TEST_BUTTON 33
#define RAW_BUTTON  32

// ================= BUZZER PIN =================
#define BUZZER_PIN 18

// ================= TEMP SENSOR =================
OneWire oneWire(TEMP_PIN);
DallasTemperature tempSensor(&oneWire);

// ================= MODE =================
bool wordMode = false;

bool lastModeButtonState = HIGH;
bool lastTestButtonState = HIGH;
bool lastRawButtonState  = HIGH;

bool rawMode = false;

// ================= PREV VALUES FOR INC/DEC =================
float prevCombined = 0.0;

// ================= BUZZER STATE =================
bool buzzerMuted   = false;   // true when muted (all 3 buttons pressed)
bool buzzerTesting = false;   // true during test sequence

// 2. ADD THIS GLOBAL ARRAY
float features[4];            // now we have 4 features: pH, turb, temp, TDS

// ================= SIMULATION MODE =================
bool  testMode        = false;
bool  testPaused      = false;
float testPH          = 7.0;
float testTurbidity   = 1.0;
float testTemperature = 25.0;
float testTDS         = 300.0; // simple default for simulation

// When the desktop AI Simulation Lab sends an explicit result,
// use it for the physical LED/buzzer/LCD status while simulation is active.
// Empty string = let the ESP32 AI classifier decide normally.
String simulatedStatus = "";

// ================= DISPLAY TOGGLE (STATUS SCREEN) =================
unsigned long lastScreenToggle = 0;
bool          showStatusScreen = false;  // false = show values, true = show status text

// ================= SENSOR FUNCTIONS =================

// 3. ADD THIS FUNCTION (outside setup() and loop())
int raw_feature_get_data(size_t offset, size_t length, float *out_ptr) {
    memcpy(out_ptr, features + offset, length * sizeof(float));
    return 0;
}

// ---------- pH ----------
float readPH() {
  int   raw     = analogRead(PH_PIN);
  float voltage = raw * (3.3 / 4095.0);

  float ph = 7 + ((3.00 - voltage) * 3.0);

  if (ph < 0)  ph = 0;
  if (ph > 14) ph = 14;

  return ph;
}

// ---------- TURBIDITY ----------
float readTurbidity() {
  long sum = 0;

  for (int i = 0; i < 10; i++) {
    sum += analogRead(TURBIDITY_PIN);
    delay(5);
  }

  float raw  = sum / 10.0;
  float turb = (raw / 4095.0) * 10.0;

  turb = 10.0 - turb;

  if (turb < 0)  turb = 0;
  if (turb > 10) turb = 10;

  return turb;
}

// ---------- TEMPERATURE ----------
float readTemp() {
  tempSensor.requestTemperatures();
  return tempSensor.getTempCByIndex(0);
}

// ---------- TDS (simple example, adjust formula as needed) ----------
float readTDS() {
  int raw = analogRead(TDS_PIN);

  // Simple linear scale: map 0–4095 to ~0–1000 ppm (placeholder)
  float tds = (raw / 4095.0) * 1000.0;

  if (tds < 0)    tds = 0;
  if (tds > 2000) tds = 2000; // clamp

  return tds;
}

// Helper: compute a simple combined value (you can adjust this formula)
float readCombined(float ph, float turb, float temp, float tds) {
  float phNorm   = ph   / 14.0;
  float turbNorm = turb / 10.0;
  float tempNorm = temp / 40.0;   // assume 0–40°C range
  float tdsNorm  = tds  / 1000.0; // assume 0–1000 ppm range

  float combined = (phNorm + turbNorm + tempNorm + tdsNorm) / 4.0;
  return combined;
}

// ================= LED FUNCTIONS =================

void allLEDOff() {
  digitalWrite(GREEN_LED, LOW);
  digitalWrite(YELLOW_LED, LOW);
  digitalWrite(RED_LED, LOW);
  digitalWrite(BLUE_LED, LOW);
}

void allLEDOn() {
  digitalWrite(GREEN_LED, HIGH);
  digitalWrite(YELLOW_LED, HIGH);
  digitalWrite(RED_LED, HIGH);
  digitalWrite(BLUE_LED, HIGH);
}

void safeLED() {
  digitalWrite(GREEN_LED, HIGH);
  digitalWrite(YELLOW_LED, LOW);
  digitalWrite(RED_LED, LOW);
}

void treatLED() {
  digitalWrite(GREEN_LED, LOW);
  digitalWrite(YELLOW_LED, HIGH);
  digitalWrite(RED_LED, LOW);
}

void unsafeLED() {
  digitalWrite(GREEN_LED, LOW);
  digitalWrite(YELLOW_LED, LOW);
  digitalWrite(RED_LED, HIGH);
}

// ================= STARTUP =================

void startupAnimation() {
  allLEDOn();

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Welcome to");
  lcd.setCursor(0, 1);
  lcd.print("W.I.S.H");
  delay(2000);

  for (int cycle = 0; cycle < 3; cycle++) {
    for (int dots = 1; dots <= 3; dots++) {
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("Connecting");
      lcd.setCursor(0, 1);
      lcd.print("System");
      for (int i = 0; i < dots; i++) {
        lcd.print(".");
      }
      delay(500);
    }
  }

  allLEDOff();
  lcd.clear();
}

// ================= TEST MODE =================

void testSequence() {
  buzzerTesting = true;  // start test buzzer mode

  allLEDOn();

  for (int cycle = 0; cycle < 3; cycle++) {
    for (int dots = 1; dots <= 3; dots++) {
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("Testing");
      lcd.setCursor(0, 1);
      lcd.print("System");
      for (int i = 0; i < dots; i++) {
        lcd.print(".");
      }

      // Slow beep every 1 second during test
      digitalWrite(BUZZER_PIN, HIGH);
      delay(200);
      digitalWrite(BUZZER_PIN, LOW);
      delay(800);
    }
  }

  allLEDOff();
  lcd.clear();

  buzzerTesting = false;  // end test buzzer mode
}

// ================= RAW DATA DISPLAY =================

void showRawData(int phRaw, int turbRaw, int tdsRaw, float temp, float ph, float turb, float tds) {
  float combined = readCombined(ph, turb, temp, tds);

  String trend = "";
  if (prevCombined == 0.0) {
    trend = "Inc +";  // first reading
  } else if (combined >= prevCombined) {
    trend = "Inc +";
  } else {
    trend = "Dec -";
  }

  prevCombined = combined;

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("pHr:");
  lcd.print(phRaw);
  lcd.print(" Tr:");
  lcd.print(turbRaw);

  lcd.setCursor(0, 1);
  lcd.print("TDSr:");
  lcd.print(tdsRaw);
  lcd.print(" ");
  lcd.print(trend);
}

// ================= BUZZER FUNCTIONS =================

void buzzerOff() {
  digitalWrite(BUZZER_PIN, LOW);
}

void buzzerOn() {
  digitalWrite(BUZZER_PIN, HIGH);
}

// ================= SIMULATION SERIAL HANDLER =================
void handleSerialCommands() {
  if (!Serial.available()) return;

  String cmd = Serial.readStringUntil('\n');
  cmd.trim();

  if (cmd.startsWith("TEST,")) {
    // Supported:
    // TEST,ph,turb,temp,tds
    // TEST,ph,turb,temp,tds,SAFE
    // TEST,ph,turb,temp,tds,TREAT
    // TEST,ph,turb,temp,tds,UNSAFE

    int c1 = cmd.indexOf(',');
    int c2 = cmd.indexOf(',', c1 + 1);
    int c3 = cmd.indexOf(',', c2 + 1);
    int c4 = cmd.indexOf(',', c3 + 1);

    if (c1 > 0 && c2 > c1 && c3 > c2) {
      String phStr   = cmd.substring(c1 + 1, c2);
      String turbStr = cmd.substring(c2 + 1, c3);

      String tempStr;
      String tdsStr;
      String statusStr = "";

      if (c4 > c3) {
        tempStr = cmd.substring(c3 + 1, c4);

        // Everything after the fourth comma may contain TDS and optional status.
        String remaining = cmd.substring(c4 + 1);
        int c5 = remaining.indexOf(',');

        if (c5 >= 0) {
          tdsStr = remaining.substring(0, c5);
          statusStr = remaining.substring(c5 + 1);
        } else {
          tdsStr = remaining;
        }
      } else {
        tempStr = cmd.substring(c3 + 1);
        tdsStr = "";
      }

      float ph   = phStr.toFloat();
      float turb = turbStr.toFloat();
      float temp = tempStr.toFloat();
      float tds  = tdsStr.length() ? tdsStr.toFloat() : testTDS;

      testPH          = ph;
      testTurbidity   = turb;
      testTemperature = temp;
      testTDS         = tds;

      statusStr.trim();
      statusStr.toUpperCase();

      if (statusStr == "SAFE" ||
          statusStr == "TREAT" ||
          statusStr == "UNSAFE") {
        simulatedStatus = statusStr;
      } else {
        simulatedStatus = "";
      }

      testMode   = true;
      testPaused = false;

      Serial.println("SIMULATION: TEST command received");
      Serial.print("SIM PH: ");   Serial.println(testPH);
      Serial.print("SIM TURB: "); Serial.println(testTurbidity);
      Serial.print("SIM TEMP: "); Serial.println(testTemperature);
      Serial.print("SIM TDS: ");  Serial.println(testTDS);

      if (simulatedStatus.length() > 0) {
        Serial.print("SIM STATUS: ");
        Serial.println(simulatedStatus);
      } else {
        Serial.println("SIM STATUS: AI CLASSIFIER");
      }
    }
  }

  else if (cmd.startsWith("SIMSTATUS,")) {
    // Explicitly controls the physical simulation result.
    // SIMSTATUS,SAFE
    // SIMSTATUS,TREAT
    // SIMSTATUS,UNSAFE
    // SIMSTATUS,OFF

    String statusCmd = cmd.substring(strlen("SIMSTATUS,"));
    statusCmd.trim();
    statusCmd.toUpperCase();

    if (statusCmd == "SAFE" ||
        statusCmd == "TREAT" ||
        statusCmd == "UNSAFE") {

      simulatedStatus = statusCmd;
      testMode = true;
      testPaused = false;

      Serial.print("SIMULATION: STATUS OVERRIDE = ");
      Serial.println(simulatedStatus);
    }
    else if (statusCmd == "OFF") {
      simulatedStatus = "";
      Serial.println("SIMULATION: STATUS OVERRIDE OFF");
    }
  }

  else if (cmd == "PAUSETEST") {
    if (testMode) {
      testPaused = true;
      Serial.println("SIMULATION: PAUSED");
    }
  }

  else if (cmd == "STOPTEST") {
    testMode        = false;
    testPaused      = false;
    simulatedStatus = "";

    // Immediately restore safe hardware outputs until the next live
    // sensor/classifier cycle computes the real state.
    buzzerOff();
    allLEDOff();

    Serial.println("SIMULATION: STOPTEST, Live Monitoring Restored");
  }
}

// ================= SETUP =================

void setup() {
  Serial.begin(115200);

  lcd.init();
  lcd.backlight();

  tempSensor.begin();

  pinMode(GREEN_LED, OUTPUT);
  pinMode(YELLOW_LED, OUTPUT);
  pinMode(RED_LED, OUTPUT);
  pinMode(BLUE_LED, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);  // Buzzer pin

  pinMode(MODE_BUTTON, INPUT_PULLUP);
  pinMode(TEST_BUTTON, INPUT_PULLUP);
  pinMode(RAW_BUTTON, INPUT_PULLUP);

  pinMode(TDS_PIN, INPUT);      // TDS input

  buzzerOff();  // Start with buzzer off

  startupAnimation();
}

// ================= LOOP =================

void loop() {

  // ================= BUTTON READINGS =================

  bool modeButtonState = digitalRead(MODE_BUTTON);
  bool testButtonState = digitalRead(TEST_BUTTON);
  bool rawButtonState  = digitalRead(RAW_BUTTON);

  // ================= MODE BUTTON =================

  if (modeButtonState == LOW && lastModeButtonState == HIGH) {
    wordMode = !wordMode;
    lcd.clear();
    delay(200);
  }
  lastModeButtonState = modeButtonState;

  // ================= TEST BUTTON =================
  if (testButtonState == LOW && lastTestButtonState == HIGH) {
    testSequence();
  }
  lastTestButtonState = testButtonState;

  // ================= RAW BUTTON (RAW MODE ONLY) =================
  if (rawButtonState == LOW && lastRawButtonState == HIGH) {
    rawMode = !rawMode;  // toggle raw mode on LCD
    lcd.clear();
    delay(200);
  }
  lastRawButtonState = rawButtonState;

  // ================= 3-BUTTON SIMULTANEOUS PRESS (TOGGLE BUZZER MUTE) =================

  if (modeButtonState == LOW && testButtonState == LOW && rawButtonState == LOW) {
    // Toggle mute state
    buzzerMuted = !buzzerMuted;

    if (buzzerMuted) {
      buzzerOff();  // mute: turn off
    }
    delay(200);  // simple debounce
    while (digitalRead(MODE_BUTTON) == LOW &&
           digitalRead(TEST_BUTTON) == LOW &&
           digitalRead(RAW_BUTTON) == LOW) {
      // wait for release
    }
  }

  // ================= BLUE LED =================
  if (wordMode)
    digitalWrite(BLUE_LED, HIGH);
  else
    digitalWrite(BLUE_LED, LOW);

  // ================= SERIAL COMMANDS (SIMULATION) =================
  handleSerialCommands();

  // ================= SENSOR READINGS =================

  int   phRaw   = analogRead(PH_PIN);
  int   turbRaw = analogRead(TURBIDITY_PIN);
  int   tdsRaw  = analogRead(TDS_PIN);

  float ph;
  float turb;
  float temp;
  float tempRaw;
  float tds;

  if (testMode) {
    // Use simulated values (frozen if testPaused)
    ph      = testPH;
    turb    = testTurbidity;
    temp    = testTemperature;
    tempRaw = temp;
    tds     = testTDS;
  } else {
    // Use real sensors
    ph      = readPH();
    turb    = readTurbidity();
    temp    = readTemp();
    tempRaw = temp;
    tds     = readTDS();
  }

  // 4. ADD FEATURES POPULATION AFTER SENSOR READINGS
  features[0] = ph;
  features[1] = turb;
  features[2] = temp;
  features[3] = tds;  // NEW

  // 5. RUN THE AI
  ei_impulse_result_t result = {0};

  signal_t signal;
  signal.total_length = 4;        // we now have 4 features
  signal.get_data     = &raw_feature_get_data;

  EI_IMPULSE_ERROR res = run_classifier(&signal, &result, false);
  if (res != EI_IMPULSE_OK) {
    Serial.println("AI Error");
    return;
  }

  String status = "Safe";

  // ================= STATUS LOGIC =================

  float safeScore   = result.classification[0].value;
  float treatScore  = result.classification[1].value;
  float unsafeScore = result.classification[2].value;

  // Normal/live mode: use the Edge Impulse classifier exactly as before.
  // Simulation mode: if the desktop app supplied an explicit result,
  // use that result for the ACTUAL physical LED, buzzer and LCD status.
  if (testMode && simulatedStatus.length() > 0) {

    if (simulatedStatus == "SAFE") {
      status = "Safe";
      safeLED();
    }
    else if (simulatedStatus == "TREAT") {
      status = "Treat";
      treatLED();
    }
    else if (simulatedStatus == "UNSAFE") {
      status = "Unsafe";
      unsafeLED();
    }
  }
  else {
    // No simulation override: preserve the original AI behavior.
    if (safeScore >= treatScore && safeScore >= unsafeScore) {
      status = "Safe";
      safeLED();
    }
    else if (treatScore >= unsafeScore) {
      status = "Treat";
      treatLED();
    }
    else {
      status = "Unsafe";
      unsafeLED();
    }
  }

  // 7. PRINT AI CONFIDENCE FOR DEBUGGING
  Serial.print("Safe: ");
  Serial.println(safeScore);
  Serial.print("Treat: ");
  Serial.println(treatScore);
  Serial.print("Unsafe: ");
  Serial.println(unsafeScore);

  // ================= WORD STATES =================

  // pH: Acidic / Neutral / Basic
  String phState;
  if (ph < 6.5)
    phState = "Acidic";
  else if (ph > 7.5)
    phState = "Basic";
  else
    phState = "Neutral";

  // Turbidity: Clear / Cloud / Dirty (same as before)
  String turbState;
  if (turb < 3)
    turbState = "Clear";
  else if (turb < 7)
    turbState = "Cloud";
  else
    turbState = "Dirty";

  // Temperature: Hot / Cold / Room
  String tempWord;
  if (temp > 30)
    tempWord = "Hot";
  else if (temp < 20)
    tempWord = "Cold";
  else
    tempWord = "Room";

  // TDS: Low / Mid / High (simple thresholds, adjust as needed)
  String tdsWord;
  if (tds < 300)
    tdsWord = "Low";
  else if (tds < 600)
    tdsWord = "Mid";
  else
    tdsWord = "High";

  // ================= BUZZER LOGIC =================

  if (buzzerTesting) {
    buzzerOff();
  }
  else {
    if (buzzerMuted) {
      buzzerOff();
    }
    else {
      if (status == "Treat") {
        digitalWrite(BUZZER_PIN, HIGH);
        delay(100);
        digitalWrite(BUZZER_PIN, LOW);
        delay(100);
      }
      else if (status == "Unsafe") {
        buzzerOn();
      }
      else {
        buzzerOff();
      }
    }
  }

  // ================= SCREEN TOGGLE (EVERY 2 SECONDS) =================

  unsigned long now = millis();
  if (now - lastScreenToggle >= 2000) {
    lastScreenToggle = now;
    showStatusScreen = !showStatusScreen;
    lcd.clear();
  }

  // ================= LCD DISPLAY =================

  if (rawMode) {
    // RAW MODE: show pHr, Tr, TDSr, Tpr and trend at end
    showRawData(phRaw, turbRaw, tdsRaw, temp, ph, turb, tds);
  }
  else if (!wordMode) {
    // ---------- NUMBER MODE ----------
    if (!showStatusScreen) {
      // Screen A: pH, Temp, Turb, TDS
      lcd.setCursor(0, 0);
      lcd.print("pH:");
      lcd.print(ph, 1);

      lcd.setCursor(9, 0);
      lcd.print("Tp:");
      lcd.print(temp, 1);

      lcd.setCursor(0, 1);
      lcd.print("Tb:");
      lcd.print(turb, 1);

      lcd.setCursor(9, 1);
      lcd.print("TDS:");
      lcd.print((int)tds);
    } else {
      // Screen B: status text
      lcd.setCursor(0, 0);
      if (status == "Safe") {
        lcd.print("Water is Safe   ");
      } else if (status == "Treat") {
        lcd.print("Treat Water!!   ");
      } else {
        lcd.print("Water is Unsafe ");
      }
      lcd.setCursor(0, 1);
      lcd.print("                ");
    }
  }
  else {
    // ---------- WORD MODE ----------
    if (!showStatusScreen) {
      // Screen A: pH state, Temp word, Turb state, TDS word
      lcd.setCursor(0, 0);
      lcd.print("pH:");
      lcd.print(phState);

      lcd.setCursor(9, 0);
      lcd.print("Tp:");
      lcd.print(tempWord);

      lcd.setCursor(0, 1);
      lcd.print("Tb:");
      lcd.print(turbState);

      lcd.setCursor(9, 1);
      lcd.print("TDS:");
      lcd.print(tdsWord);
    } else {
      // Screen B: status text
      lcd.setCursor(0, 0);
      if (status == "Safe") {
        lcd.print("Water is Safe   ");
      } else if (status == "Treat") {
        lcd.print("Treat Water!!   ");
      } else {
        lcd.print("Water is Unsafe ");
      }
      lcd.setCursor(0, 1);
      lcd.print("                ");
    }
  }

  // ================= SERIAL =================

  Serial.println("========== SENSOR DATA ==========");

  Serial.print("pH Raw: ");
  Serial.println(phRaw);
  Serial.print("pH Value: ");
  Serial.println(ph);
  Serial.println();

  Serial.print("Turbidity Raw: ");
  Serial.println(turbRaw);
  Serial.print("Turbidity Value: ");
  Serial.println(turb);
  Serial.println();

  Serial.print("TDS Raw: ");
  Serial.println(tdsRaw);
  Serial.print("TDS Value: ");
  Serial.println(tds);
  Serial.println();

  Serial.print("Temperature Raw: ");
  Serial.println(tempRaw);
  Serial.print("Temperature Value: ");
  Serial.println(temp);
  Serial.println();

  Serial.print("Status: ");
  Serial.println(status);

  if (testMode) {
    if (testPaused) {
      Serial.println("Simulation Paused");
    } else {
      Serial.println("Simulation Active");

      if (simulatedStatus.length() > 0) {
        Serial.print("Simulation Status Override: ");
        Serial.println(simulatedStatus);
      } else {
        Serial.println("Simulation Status Source: AI Classifier");
      }
    }
  } else {
    Serial.println("Live Monitoring");
  }

  Serial.println("=================================");

  delay(200);
}
