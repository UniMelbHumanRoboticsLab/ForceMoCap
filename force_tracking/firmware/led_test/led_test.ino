// define led according to pin diagram in article
const int led = D10; // there is no LED_BUILTIN available for the XIAO ESP32C3.

void setup() {
  Serial.begin(9600);
  // initialize digital pin led as an output
  pinMode(led, OUTPUT);
}

void loop() {
  Serial.println("Hi");
  digitalWrite(led, HIGH);   // turn the LED on 
  delay(1000);               // wait for a second
  digitalWrite(led, LOW);    // turn the LED off
  delay(1000);               // wait for a second
}

