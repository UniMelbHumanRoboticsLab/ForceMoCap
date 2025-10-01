
// WIFI
#include <WebServer.h>
#include <WiFi.h>
#include <WiFiUdp.h>
//set up to connect to an existing network (e.g. mobile hotspot from laptop that will run the python code)
const char* ssid = "XiaomiJQ";
const char* password = "jq00170410";
WiFiUDP Udp;
unsigned int espPort = 4212;  //  port to listen on
char incomingPacket[255];  // buffer for incoming packets

// FSR
// int fsrPins[9] = {A0,A1,A2,A3,A4,A5,A8,A9,A10}; //analog pin 0
// int fsrPins[9] = {A5,A3,A1,A8,A10,A4,A2,A0,A9}; //analog pin for Left
int fsrPins[9] = {A0,A5,A3,A8,A10,A1,A4,A2,A9}; //analog pin for Right

float resistor = 2201.0;
float Vin = 3.3;
String measurements = "";

void setup(){
  Serial.begin(9600);

  // Wifi
  pinMode(LED_BUILTIN, OUTPUT);
  delay(1000);
  WiFi.begin(ssid, password);
  Serial.println("");
  digitalWrite(LED_BUILTIN, LOW);
  // Wait for connection
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  // Serial.println("Connected to wifi");
  Udp.begin(espPort);
  Serial.printf("Now listening at IP %s, UDP port %d\n", WiFi.localIP().toString().c_str(), espPort);

  // recv one packet from the remote so we can know its IP and port
  bool readPacket = false;
  while (!readPacket) {
    int packetSize = Udp.parsePacket();
    if (packetSize)
     {
      // receive incoming UDP packets
      // Serial.printf("Received %d bytes from %s, port %d\n", packetSize, Udp.remoteIP().toString().c_str(), Udp.remotePort());
      int len = Udp.read(incomingPacket, 255);
      if (len > 0)
      {
        incomingPacket[len] = 0;
      }
      Serial.printf("UDP packet contents: %s\n", incomingPacket);
      Udp.beginPacket(Udp.remoteIP(), Udp.remotePort());
      Udp.printf("%s\n", incomingPacket);
      Udp.endPacket();
      readPacket = true;
    } 
  }
  digitalWrite(LED_BUILTIN, HIGH);    // turn the LED off

  analogReadResolution(12);
  
  delay(5000);
  Serial.println("Starting UDP");
}

void loop(){
  measurements = "s";
  for (int fsrPin=0; fsrPin < 9; fsrPin++)
  {
    int fsrReading = analogRead(fsrPins[fsrPin]); 
    float Vout = fsrReading * (3.3 / 4095.0);
    float resistance = resistor*(Vin/Vout-1);
    if (isinf(resistance) | (resistance>10000000.0))
    {
      resistance = 10000000.0;
    }
    float conductance = 1/resistance*1000.0;
    measurements += String(conductance,4) +"\t";
    // delay(1); // give delay between analog reads
  }

  // print measurements:
  Serial.println(measurements);

  // send packet
  Udp.beginPacket(Udp.remoteIP(), Udp.remotePort());
  Udp.printf("%s\n", measurements.c_str());
  Udp.endPacket();

  // check esp if there is an incoming message
  int packetSize = Udp.parsePacket();
  if (packetSize)
  {
    int len = Udp.read(incomingPacket, 255);
    if (len > 0)
    {
      incomingPacket[len] = 0;
    }
    
    if (strcmp(incomingPacket,"STOP")==0)
    {
      // Serial.println("UDP packet contents: %s\n", incomingPacket);
      ESP.restart();
    }
  } 
  delay(10);
}

