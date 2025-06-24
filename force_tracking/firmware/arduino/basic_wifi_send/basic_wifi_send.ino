#include <WebServer.h>
#include <WiFi.h>
#include <WiFiUdp.h>

//set up to connect to an existing network (e.g. mobile hotspot from laptop that will run the python code)
const char* ssid = "Xiaomi13Ultra";
const char* password = "jq00170410";
WiFiUDP Udp;
unsigned int espPort = 4211;  //  port to listen on
char incomingPacket[255];  // buffer for incoming packets
int i = 0;
const int led = D10;
void setup()
{
  pinMode(led, OUTPUT);
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  Serial.println("");
  digitalWrite(led, HIGH);    // turn the LED on

  // Wait for connection
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("Connected to wifi");
  Udp.begin(espPort);
  Serial.printf("Now listening at IP %s, UDP port %d\n", WiFi.localIP().toString().c_str(), espPort);
  digitalWrite(led, LOW);    // turn the LED on

  // we recv one packet from the remote so we can know its IP and port
  bool readPacket = false;
  while (!readPacket) {
    int packetSize = Udp.parsePacket();
    Serial.println(packetSize);
    if (packetSize)
    {
    // receive incoming UDP packets
    Serial.printf("Received %d bytes from %s, port %d\n", packetSize, Udp.remoteIP().toString().c_str(), Udp.remotePort());
    int len = Udp.read(incomingPacket, 255);
    if (len > 0)
    {
      incomingPacket[len] = 0;
    }
    Serial.printf("UDP packet contents: %s\n", incomingPacket);
    readPacket = true;
    Udp.beginPacket(Udp.remoteIP(), Udp.remotePort());
    Udp.printf("%s\n", incomingPacket);
    Udp.endPacket();
    } 
    delay(100);
  }
}

void loop()
{
  Serial.println(i);

  Udp.beginPacket(Udp.remoteIP(), Udp.remotePort());
  Udp.printf("%d\n", i);
  Udp.endPacket();
  i = i + 1;
  
  delay(10);

}
