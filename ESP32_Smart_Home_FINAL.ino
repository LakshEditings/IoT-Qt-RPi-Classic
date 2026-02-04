#include <WiFi.h>
#include <PubSubClient.h>
#include <EEPROM.h>
#include <time.h>

// ================= WIFI =================
const char* ssid = "Laksh";
const char* password = "Lakshen8";

// ================= MQTT =================
const char* mqtt_server = "broker.hivemq.com";
const int mqtt_port = 1883;

const char* mqtt_topic_light1 = "home/light/light_1";
const char* mqtt_topic_light2 = "home/light/light_2";
const char* mqtt_topic_light3 = "home/light/light_3";
const char* mqtt_topic_light4 = "home/light/light_4";

const char* energy_topic = "home/light/energy";
const char* motion_topic = "home/light/motion";  // NEW: Motion status topic

// ================= PINS =================
const int light1Pin = 2;
const int light2Pin = 18;
const int light3Pin = 19;
const int light4Pin = 21;

// REAL ADC PINS for ACS712 sensors
const int sensor1Pin = 34;
const int sensor2Pin = 35;

const int MOTION_PIN = 5;  // PIR sensor

// ═══════════════════════════════════════════════
// TIMER & MOTION SENSOR SYSTEM
// ═══════════════════════════════════════════════

// ON TIMER: Manual override disables for the day
bool timerDisabledToday[4] = {false, false, false, false};
int lastDayOfYear = -1;

// MOTION SENSOR: Simple - motion → ON for 5 minutes (no time restrictions)
bool motionEnabled = true;           // Enable/disable from UI
bool motionActive = false;            // Currently in motion-triggered state
unsigned long motionTimeout = 0;      // When motion timeout ends
const unsigned long MOTION_DURATION = 300000;  // 5 minutes in milliseconds

// ================= EEPROM =================
#define EEPROM_SIZE 64
#define OFFSET1_ADDR 0
#define OFFSET2_ADDR 8

// ================= SENSOR CONFIG =================
float offset1 = 1.65;
float offset2 = 1.65;
float voltage_mains = 230.0;

WiFiClient espClient;
PubSubClient client(espClient);

// Energy accumulators
static float energy1 = 0;
static float energy2 = 0;

// ================= WIFI =================
void setupWiFi() {
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi Connected");
  
  // Configure NTP for accurate time (IST = UTC+5:30 = 19800 seconds)
  configTime(19800, 0, "pool.ntp.org");
  Serial.println("NTP time sync requested");
  
  delay(2000);
}

// ================= MQTT CALLBACK =================
void callback(char* topic, byte* payload, unsigned int length) {
  String message;
  for (int i = 0; i < length; i++) message += (char)payload[i];

  String top = String(topic);

  bool manualChange = false;
  int lightIdx = -1;

  if (top == mqtt_topic_light1) {
    // Don't override if motion mode is active
    if (!motionActive) {
      digitalWrite(light1Pin, message == "ON" ? LOW : HIGH);
    }
    manualChange = true;
    lightIdx = 0;
  }
  else if (top == mqtt_topic_light2) {
    digitalWrite(light2Pin, message == "ON" ? LOW : HIGH);
    manualChange = true;
    lightIdx = 1;
  }
  else if (top == mqtt_topic_light3) {
    digitalWrite(light3Pin, message == "ON" ? LOW : HIGH);
    manualChange = true;
    lightIdx = 2;
  }
  else if (top == mqtt_topic_light4) {
    digitalWrite(light4Pin, message == "ON" ? LOW : HIGH);
    manualChange = true;
    lightIdx = 3;
  }

  // Manual control disables ON TIMER for that day
  if (manualChange && lightIdx >= 0) {
    timerDisabledToday[lightIdx] = true;
    Serial.printf("⚠️  Manual control → ON Timer disabled for Light%d today\n", lightIdx+1);
  }
}

// ================= MQTT CONNECT =================
void connectToMQTT() {
  while (!client.connected()) {
    if (client.connect("ESP32_SMART_HOME")) {
      client.subscribe(mqtt_topic_light1);
      client.subscribe(mqtt_topic_light2);
      client.subscribe(mqtt_topic_light3);
      client.subscribe(mqtt_topic_light4);
      Serial.println("MQTT connected & subscribed");
    } else {
      Serial.print("MQTT failed, rc=");
      Serial.println(client.state());
      delay(2000);
    }
  }
}

// ================= OFFSET CALIBRATION =================
void calibrateOffsets() {
  float sum1 = 0, sum2 = 0;

  Serial.println("Calibrating offsets (no load)...");
  for (int i = 0; i < 1500; i++) {
    sum1 += analogRead(sensor1Pin) * 3.3 / 4095.0;
    sum2 += analogRead(sensor2Pin) * 3.3 / 4095.0;
    delay(2);
  }

  offset1 = sum1 / 1500;
  offset2 = sum2 / 1500;

  EEPROM.put(OFFSET1_ADDR, offset1);
  EEPROM.put(OFFSET2_ADDR, offset2);
  EEPROM.commit();

  Serial.println("✓ Offsets calibrated & saved");
}

// ================= TRUE RMS =================
float readCurrent(int pin, float offset) {
  const int samples = 2000;
  float sum = 0;

  for (int i = 0; i < samples; i++) {
    float voltage = analogRead(pin) * 3.3 / 4095.0;
    float centered = voltage - offset;
    sum += centered * centered;
    delayMicroseconds(200);
  }

  float rmsVoltage = sqrt(sum / samples);
  float current = rmsVoltage / 0.185;   // ACS712 sensitivity

  if (current < 0.03) current = 0;
  return current;
}

// ================= SETUP =================
void setup() {
  Serial.begin(115200);
  Serial.println("\n╔════════════════════════════════════════╗");
  Serial.println("║   ESP32 Smart Home Control System     ║");
  Serial.println("╚════════════════════════════════════════╝");

  pinMode(light1Pin, OUTPUT);
  pinMode(light2Pin, OUTPUT);
  pinMode(light3Pin, OUTPUT);
  pinMode(light4Pin, OUTPUT);

  // Active-LOW relays: HIGH = OFF
  digitalWrite(light1Pin, HIGH);
  digitalWrite(light2Pin, HIGH);
  digitalWrite(light3Pin, HIGH);
  digitalWrite(light4Pin, HIGH);

  pinMode(MOTION_PIN, INPUT);

  EEPROM.begin(EEPROM_SIZE);

  // Run ONCE with NO LOAD, then comment out
  // calibrateOffsets();

  EEPROM.get(OFFSET1_ADDR, offset1);
  EEPROM.get(OFFSET2_ADDR, offset2);

  Serial.printf("ACS712 Offset1: %.4fV\n", offset1);
  Serial.printf("ACS712 Offset2: %.4fV\n", offset2);

  setupWiFi();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
  connectToMQTT();

  // Initialize day tracking
  struct tm timeinfo;
  if (getLocalTime(&timeinfo)) {
    lastDayOfYear = timeinfo.tm_yday;
    Serial.printf("✓ Current day: %d\n", lastDayOfYear);
  }

  Serial.println("\n╔════════════════════════════════════════╗");
  Serial.println("║         System Ready!                  ║");
  Serial.println("╚════════════════════════════════════════╝\n");
}

// ================= LOOP =================
void loop() {
  if (!client.connected()) connectToMQTT();
  client.loop();

  static unsigned long lastMillis = 0;

  if (millis() - lastMillis >= 1000) {
    lastMillis = millis();

    // ────────────────────────────────────
    //  CHECK FOR NEW DAY (reset ON timer flags)
    // ────────────────────────────────────
    struct tm timeinfo;
    if (getLocalTime(&timeinfo)) {
      int currentDay = timeinfo.tm_yday;
      if (currentDay != lastDayOfYear) {
        for (int i = 0; i < 4; i++) timerDisabledToday[i] = false;
        lastDayOfYear = currentDay;
        Serial.println("🌅 New day - ON Timer flags reset");
      }
    }

    // ────────────────────────────────────
    //  MOTION SENSOR: Simple 5-minute trigger
    // ────────────────────────────────────
    bool motionDetected = digitalRead(MOTION_PIN);

    if (motionDetected == HIGH && motionEnabled) {
      if (!motionActive) {
        // Start motion mode
        motionActive = true;
        motionTimeout = millis() + MOTION_DURATION;
        digitalWrite(light1Pin, LOW);  // Turn ON Light1
        Serial.println("🚶 [MOTION] Detected → Light1 ON for 5 minutes");
        
        // Publish motion event to MQTT
        client.publish(motion_topic, "{\"motion\":1,\"active\":1}");
      }
    }

    // Check motion timeout
    if (motionActive && millis() > motionTimeout) {
      digitalWrite(light1Pin, HIGH);  // Turn OFF
      motionActive = false;
      Serial.println("⏰ [MOTION] Timeout → Light1 OFF");
      
      // Publish motion end to MQTT
      client.publish(motion_topic, "{\"motion\":0,\"active\":0}");
    }

    // ────────────────────────────────────
    //  READ SENSOR CURRENTS
    // ────────────────────────────────────
    float current1 = readCurrent(sensor1Pin, offset1);
    float current2 = readCurrent(sensor2Pin, offset2);

    float power1 = voltage_mains * current1;
    float power2 = voltage_mains * current2;

    energy1 += power1 / 3600000.0;
    energy2 += power2 / 3600000.0;

    // ────────────────────────────────────
    //  SERIAL MONITOR OUTPUT
    // ────────────────────────────────────
    Serial.println("═══════════ ENERGY MONITOR ═══════════");
    Serial.printf("L1: %.3f A | %.1f W | %.6f kWh\n", current1, power1, energy1);
    Serial.printf("L2: %.3f A | %.1f W | %.6f kWh\n", current2, power2, energy2);
    
    if (motionActive) {
      unsigned long remaining = (motionTimeout - millis()) / 1000;
      Serial.printf("🚶 [MOTION ACTIVE] Light1 ON - %lu sec remaining\n", remaining);
    }

    // Show timer disable status
    for (int i = 0; i < 4; i++) {
      if (timerDisabledToday[i]) {
        Serial.printf("⚠️  Light%d: Timer disabled (manual override)\n", i+1);
      }
    }

    // ────────────────────────────────────
    //  PUBLISH ENERGY to MQTT
    // ────────────────────────────────────
    char msg[350];
    snprintf(msg, sizeof(msg),
      "{\"L1\":{\"current\":%.3f,\"power\":%.1f,\"energy\":%.6f},"
      "\"L2\":{\"current\":%.3f,\"power\":%.1f,\"energy\":%.6f},"
      "\"motionEnabled\":%d,\"motionActive\":%d,\"timerDisabled\":[%d,%d,%d,%d]}",
      current1, power1, energy1,
      current2, power2, energy2,
      motionEnabled ? 1 : 0,
      motionActive ? 1 : 0,
      timerDisabledToday[0], timerDisabledToday[1], 
      timerDisabledToday[2], timerDisabledToday[3]
    );

    client.publish(energy_topic, msg);
    Serial.println("📡 MQTT published\n");
  }
}
