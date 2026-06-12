const int ledPin = 13;
const int motorPin = 8;

void setup() {
  // Initialize serial communication at 9600 baud
  Serial.begin(9600);
  
  // Configure the pins as outputs
  pinMode(ledPin, OUTPUT);
  pinMode(motorPin, OUTPUT);
  
  // Ensure both are initially turned off
  digitalWrite(ledPin, LOW);
  digitalWrite(motorPin, LOW);
}

void loop() {
  // Check if data is available to read
  if (Serial.available() > 0) {
    // Read the incoming byte
    char incomingByte = Serial.read();
    
    // Process the command
    if (incomingByte == 'B') {
      // Bad posture: Turn on LED and vibration motor
      digitalWrite(ledPin, HIGH);
      digitalWrite(motorPin, HIGH);
    } 
    else if (incomingByte == 'G') {
      // Good posture: Turn off LED and vibration motor
      digitalWrite(ledPin, LOW);
      digitalWrite(motorPin, LOW);
    }
    // Any other characters (like newlines or noise) are ignored
  }
}
