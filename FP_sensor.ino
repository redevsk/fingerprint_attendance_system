#include <Adafruit_Fingerprint.h>
#include <LiquidCrystal_I2C.h>
#include <SoftwareSerial.h>

#define BUZZER_PIN 13
#define TX_PIN 3
#define RX_PIN 2

SoftwareSerial mySerial(RX_PIN, TX_PIN);
Adafruit_Fingerprint finger = Adafruit_Fingerprint(&mySerial);

LiquidCrystal_I2C lcd(0x27, 16, 2);

#define MODE_NORMAL 0
#define MODE_REGISTER 1

int currentMode = MODE_NORMAL;
int lastID = 0;

void setup() {
  Serial.begin(9600);
  
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);
  
  lcd.init();
  lcd.backlight();
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Initializing...");
  
  finger.begin(57600);
  
  if (finger.verifyPassword()) {
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Sensor Ready");
    beepSuccess();
  } else {
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Sensor Error!");
    beepError();
    while (1) { delay(1); }
  }
  
  delay(1000);
  showWelcomeScreen();
}

void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    processCommand(command);
  }
  
  if (currentMode == MODE_NORMAL) {
    lcd.setCursor(0, 1);
    lcd.print("Place finger...  ");
    
    int fingerprintID = scanFingerprint();
    if (fingerprintID > 0) {
      lastID = fingerprintID;
      
      Serial.print("ID:");
      Serial.println(fingerprintID);
      
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("ID #");
      lcd.print(fingerprintID);
      lcd.setCursor(0, 1);
      lcd.print("Attendance logged");
      
      beepSuccess();
      delay(2000);
      showWelcomeScreen();
    }
  }
  else if (currentMode == MODE_REGISTER) {
    delay(100);
  }
}

void processCommand(String command) {
  if (command.startsWith("MODE:")) {
    String mode = command.substring(5);
    if (mode == "NORMAL") {
      currentMode = MODE_NORMAL;
      showWelcomeScreen();
    } else if (mode == "REGISTER") {
      currentMode = MODE_REGISTER;
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("Register Mode");
      lcd.setCursor(0, 1);
      lcd.print("Follow PC Guide");
    }
  }
  else if (command.startsWith("ENROLL:")) {
    int id = command.substring(7).toInt();
    if (id > 0 && id < 256) {
      enrollFingerprint(id);
    }
  }
  else if (command == "DELETE_ALL") {
    deleteAllFingerprints();
  }
  else if (command.startsWith("DELETE:")) {
    int id = command.substring(7).toInt();
    if (id > 0 && id < 256) {
      deleteFingerprint(id);
    }
  }
}

int scanFingerprint() {
  int p = finger.getImage();
  if (p != FINGERPRINT_OK) return -1;
  
  p = finger.image2Tz();
  if (p != FINGERPRINT_OK) return -1;
  
  p = finger.fingerFastSearch();
  if (p != FINGERPRINT_OK) return -1;
  
  return finger.fingerID;
}

void enrollFingerprint(int id) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Enrolling ID #");
  lcd.print(id);
  
  lcd.setCursor(0, 1);
  lcd.print("Place finger");
  
  while (finger.getImage() != FINGERPRINT_OK) {
    delay(100);
    if (Serial.available() > 0) {
      String command = Serial.readStringUntil('\n');
      if (command == "CANCEL") {
        lcd.clear();
        lcd.setCursor(0, 0);
        lcd.print("Enrollment");
        lcd.setCursor(0, 1);
        lcd.print("Cancelled");
        Serial.println("ENROLL:CANCELLED");
        delay(2000);
        showWelcomeScreen();
        return;
      }
    }
  }
  
  int p = finger.image2Tz(1);
  if (p != FINGERPRINT_OK) {
    reportEnrollError("Template error");
    return;
  }
  
  lcd.setCursor(0, 1);
  lcd.print("Remove finger   ");
  delay(2000);
  
  while (finger.getImage() != FINGERPRINT_NOFINGER) {
    delay(100);
  }
  
  lcd.setCursor(0, 1);
  lcd.print("Place again     ");
  
  while (finger.getImage() != FINGERPRINT_OK) {
    delay(100);
    if (Serial.available() > 0) {
      String command = Serial.readStringUntil('\n');
      if (command == "CANCEL") {
        lcd.clear();
        lcd.setCursor(0, 0);
        lcd.print("Enrollment");
        lcd.setCursor(0, 1);
        lcd.print("Cancelled");
        Serial.println("ENROLL:CANCELLED");
        delay(2000);
        showWelcomeScreen();
        return;
      }
    }
  }
  
  p = finger.image2Tz(2);
  if (p != FINGERPRINT_OK) {
    reportEnrollError("Template error");
    return;
  }
  
  p = finger.createModel();
  if (p != FINGERPRINT_OK) {
    reportEnrollError("Model error");
    return;
  }
  
  p = finger.storeModel(id);
  if (p != FINGERPRINT_OK) {
    reportEnrollError("Storage error");
    return;
  }
  
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("ID #");
  lcd.print(id);
  lcd.setCursor(0, 1);
  lcd.print("Enrolled!");
  Serial.println("ENROLL:SUCCESS");
  beepSuccess();
  delay(2000);
  showWelcomeScreen();
}

void reportEnrollError(String error) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Enroll Failed");
  lcd.setCursor(0, 1);
  lcd.print(error);
  Serial.println("ENROLL:FAILED");
  beepError();
  delay(2000);
  showWelcomeScreen();
}

void deleteFingerprint(int id) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Deleting ID #");
  lcd.print(id);
  
  int p = finger.deleteModel(id);
  
  if (p == FINGERPRINT_OK) {
    lcd.setCursor(0, 1);
    lcd.print("Deleted!");
    Serial.println("DELETE:SUCCESS");
    beepSuccess();
  } else {
    lcd.setCursor(0, 1);
    lcd.print("Failed!");
    Serial.println("DELETE:FAILED");
    beepError();
  }
  
  delay(2000);
  showWelcomeScreen();
}

void deleteAllFingerprints() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Deleting All");
  lcd.setCursor(0, 1);
  lcd.print("Fingerprints...");
  
  int p = finger.emptyDatabase();
  
  if (p == FINGERPRINT_OK) {
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("All Fingerprints");
    lcd.setCursor(0, 1);
    lcd.print("Deleted!");
    Serial.println("DELETE_ALL:SUCCESS");
    beepSuccess();
  } else {
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Delete All");
    lcd.setCursor(0, 1);
    lcd.print("Failed!");
    Serial.println("DELETE_ALL:FAILED");
    beepError();
  }
  
  delay(2000);
  showWelcomeScreen();
}

void showWelcomeScreen() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Attendance System");
  if (currentMode == MODE_NORMAL) {
    lcd.setCursor(0, 1);
    lcd.print("Place finger...  ");
  } else {
    lcd.setCursor(0, 1);
    lcd.print("Register Mode");
  }
}

void beepSuccess() {
  digitalWrite(BUZZER_PIN, HIGH);
  delay(100);
  digitalWrite(BUZZER_PIN, LOW);
  delay(100);
  digitalWrite(BUZZER_PIN, HIGH);
  delay(100);
  digitalWrite(BUZZER_PIN, LOW);
}

void beepError() {
  digitalWrite(BUZZER_PIN, HIGH);
  delay(500);
  digitalWrite(BUZZER_PIN, LOW);
}