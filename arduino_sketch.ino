#include <LiquidCrystal.h>

/*
 * posturePOLICE Firmware
 * ----------------------
 * Hardware Mapping:
 * - LCD RS: Pin 12
 * - LCD Enable: Pin 11
 * - LCD D4: Pin 5
 * - LCD D5: Pin 4
 * - LCD D6: Pin 3
 * - LCD D7: Pin 2
 * - LED: Pin 13 (Monitor edge)
 * - Buzzer: Pin 8 (Active buzzer)
 */

// Initialize the LCD library with the interface pins
LiquidCrystal lcd(12, 11, 5, 4, 3, 2);

const int ledPin = 13;
const int buzzerPin = 8;

char currentStatus = 'G'; // 'G' for Good, 'B' for Bad
unsigned long lastBlinkTime = 0;
bool buzzerState = false;

void setup() {
  // Initialize serial communication
  Serial.begin(9600);
  
  // Initialize pins
  pinMode(ledPin, OUTPUT);
  pinMode(buzzerPin, OUTPUT);
  
  // Initialize LCD
  lcd.begin(16, 2);
  
  // Display Splash Screen
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("posturePOLICE");
  lcd.setCursor(0, 1);
  lcd.print("System Ready...");
  
  // Initial hardware state
  digitalWrite(ledPin, LOW);
  digitalWrite(buzzerPin, LOW);
  
  delay(2000); // Allow splash screen to be read
}

void loop() {
  // Read incoming serial data
  if (Serial.available() > 0) {
    char incomingByte = Serial.read();
    
    // Only update if the status has actually changed to minimize LCD flickering
    if (incomingByte == 'G' || incomingByte == 'B') {
      if (incomingByte != currentStatus) {
        currentStatus = incomingByte;
        updateUI();
      }
    }
  }

  // Handle real-time effects for BAD posture (pulsing buzzer)
  if (currentStatus == 'B') {
    unsigned long currentMillis = millis();
    if (currentMillis - lastBlinkTime >= 200) { // 200ms pulse interval
      lastBlinkTime = currentMillis;
      buzzerState = !buzzerState;
      digitalWrite(buzzerPin, buzzerState ? HIGH : LOW);
    }
    digitalWrite(ledPin, HIGH); // Solid LED for poor posture
  } else {
    // Good posture: ensure everything is off
    digitalWrite(buzzerPin, LOW);
    digitalWrite(ledPin, LOW);
  }
}

void updateUI() {
  lcd.clear();
  lcd.setCursor(0, 0);
  
  if (currentStatus == 'G') {
    lcd.print("POSTURE: GOOD");
    lcd.setCursor(0, 1);
    lcd.print("Keep it up!");
  } 
  else if (currentStatus == 'B') {
    lcd.print("POSTURE: POOR");
    lcd.setCursor(0, 1);
    lcd.print("SIT UP STRAIGHT!");
  }
}
