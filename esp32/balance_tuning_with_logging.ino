/**
 * ESP32 Balance Tuning Script with CSV Data Logging
 * 
 * This sketch runs PD control for balancing while logging all sensor data
 * to CSV format via serial for later analysis.
 * 
 * CSV Format: timestamp_ms,angle,gyro_rate,error,pwm,enabled
 * 
 * Commands from Pi:
 * - 'S' = Start control (enabled = true)
 * - 'X' = Stop control (enabled = false)
 * - 'L' = Start CSV logging
 * - 'N' = Stop CSV logging
 */

#include <Wire.h>
#include <MPU6050.h>

// ---------- Motor 1 pins (e.g. LEFT) ----------
const int L_EN  = 14;
const int R_EN  = 27;
const int L_PWM = 33;
const int R_PWM = 32;

// ---------- Motor 2 pins (e.g. RIGHT) ----------
const int L_EN2  = 25;
const int R_EN2  = 26;
const int L_PWM2 = 4;
const int R_PWM2 = 5;

// ---------- IMU ----------
MPU6050 mpu;
bool imuReady = false;

// ---------- Control params ----------
float targetAngle = 0.0;        // we want to keep this at 0 deg (upright)
float angle = 0.0;              // filtered angle (deg) about Y axis now
float prevError = 0.0;
unsigned long lastTime = 0;

// PD gains (you WILL need to tune these)
float Kp = 70.0;                // proportional
float Kd = 0.0;                 // derivative

// Complementary filter
float alpha = 0.98;             // gyro weight

// ---------- State ----------
bool enabled = true;            // robot only runs control when true
bool csvLogging = false;        // CSV data logging flag

// ---------- CSV Data ----------
unsigned long csvStartTime = 0;

// ---------- Motor helper ----------
// This now drives *both* BTS7960 boards with the same pwm
void setMotor(int pwm) {
  // pwm: -255 .. 255 (negative = reverse, positive = forward)
  pwm = constrain(pwm, -255, 255);

  if (pwm > 0) {
    // forward
    analogWrite(L_PWM,  pwm);
    analogWrite(R_PWM,  0);
    analogWrite(L_PWM2, pwm);
    analogWrite(R_PWM2, 0);
  } else if (pwm < 0) {
    // reverse
    int p = -pwm;
    analogWrite(L_PWM,  0);
    analogWrite(R_PWM,  p);
    analogWrite(L_PWM2, 0);
    analogWrite(R_PWM2, p);
  } else {
    // stop
    analogWrite(L_PWM,  0);
    analogWrite(R_PWM,  0);
    analogWrite(L_PWM2, 0);
    analogWrite(R_PWM2, 0);
  }
}

// ---------- Serial command handler from Pi ----------
void handleSerial() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == 'S') {          // Start control
      enabled = true;
      Serial.println("# CMD: START (enabled = true)");
    }
    else if (c == 'X') {     // Stop control
      enabled = false;
      setMotor(0);           // make sure motors stop immediately
      Serial.println("# CMD: STOP (enabled = false)");
    }
    else if (c == 'L') {     // Start CSV logging
      csvLogging = true;
      csvStartTime = millis();
      Serial.println("# CSV_LOGGING: START");
      Serial.println("# CSV Format: timestamp_ms,angle,gyro_rate,accel_angle,error,derror,pwm,enabled");
      Serial.println("timestamp_ms,angle,gyro_rate,accel_angle,error,derror,pwm,enabled");
    }
    else if (c == 'N') {     // Stop CSV logging
      csvLogging = false;
      Serial.println("# CSV_LOGGING: STOP");
    }
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  // Motor 1 setup
  pinMode(L_EN, OUTPUT);
  pinMode(R_EN, OUTPUT);
  pinMode(L_PWM, OUTPUT);
  pinMode(R_PWM, OUTPUT);
  digitalWrite(L_EN, HIGH);
  digitalWrite(R_EN, HIGH);

  // Motor 2 setup
  pinMode(L_EN2, OUTPUT);
  pinMode(R_EN2, OUTPUT);
  pinMode(L_PWM2, OUTPUT);
  pinMode(R_PWM2, OUTPUT);
  digitalWrite(L_EN2, HIGH);
  digitalWrite(R_EN2, HIGH);

  // IMU setup
  Wire.begin(21, 22);   // SDA=21, SCL=22 on ESP32
  mpu.initialize();

  if (mpu.testConnection()) {
    Serial.println("# MPU6050 connected ✅");
    imuReady = true;
  } else {
    Serial.println("# MPU6050 NOT connected ❌");
    imuReady = false;
  }

  // Optional: small delay for IMU to settle
  delay(1000);

  // Initialize timing
  lastTime = millis();

  // Start ENABLED for safety
  enabled = true;
  setMotor(0);
  Serial.println("# System ready. Commands: S=start, X=stop, L=log CSV, N=stop log");
  Serial.println("# PD Gains: Kp=" + String(Kp) + ", Kd=" + String(Kd));
}

void loop() {
  handleSerial();   // always listen to the Pi

  if (!imuReady) {
    // If IMU isn't working, just stop the motor
    setMotor(0);
    delay(500);
    return;
  }

  // ----- Timing -----
  unsigned long now = millis();
  float dt = (now - lastTime) / 1000.0f;  // seconds
  if (dt <= 0) dt = 0.001f;
  lastTime = now;

  // ----- Read IMU -----
  int16_t ax, ay, az;
  int16_t gx, gy, gz;
  mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);

  // Pitch about Y axis (using ax vs az)
  float accAngleY = atan2(-(float)ax, (float)az) * 180.0f / PI;  // angle about Y

  // Gyro rate about Y axis (deg/s)
  float gyroRateY = gy / 131.0f;  // deg/s

  // ----- Complementary filter for angle about Y -----
  float gyroAngle = angle + gyroRateY * dt;
  angle = alpha * gyroAngle + (1.0f - alpha) * accAngleY;

  int motorPwm = 0;
  float error = 0.0f;
  float dError = 0.0f;

  if (enabled) {
    // ----- PD control -----
    error = targetAngle - angle;            // if angle > 0 (tilted one way), error drives motor to push back
    dError = (error - prevError) / dt;

    float output = Kp * error + Kd * dError;

    prevError = error;

    // Map PD output to motor PWM
    motorPwm = (int)output;
    motorPwm = constrain(motorPwm, -255, 255);

    setMotor(-motorPwm);
  } else {
    // Disabled: make sure motor is off and reset error state
    setMotor(0);
    prevError = 0.0f;
    error = targetAngle - angle;  // Still calculate for logging
  }

  // ----- CSV Logging -----
  if (csvLogging) {
    // Output CSV: timestamp_ms,angle,gyro_rate,accel_angle,error,derror,pwm,enabled
    Serial.print(now);
    Serial.print(",");
    Serial.print(angle, 3);
    Serial.print(",");
    Serial.print(gyroRateY, 3);
    Serial.print(",");
    Serial.print(accAngleY, 3);
    Serial.print(",");
    Serial.print(error, 3);
    Serial.print(",");
    Serial.print(dError, 3);
    Serial.print(",");
    Serial.print(motorPwm);
    Serial.print(",");
    Serial.println(enabled ? 1 : 0);
  } else {
    // ----- Debug output (human-readable) -----
    static unsigned long lastPrint = 0;
    if (now - lastPrint > 100) {  // print at ~10 Hz
      lastPrint = now;
      Serial.print("# enabled=");
      Serial.print(enabled);
      Serial.print(" angleY=");
      Serial.print(angle, 2);
      Serial.print("  error=");
      Serial.print(error, 2);
      Serial.print("  pwm=");
      Serial.println(motorPwm);
    }
  }
}
