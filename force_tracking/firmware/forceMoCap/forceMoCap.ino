///////////////////////////////////// UDP ////////////////////////////////////////////////////
#include <WebServer.h>
#include <WiFi.h>
#include <WiFiUdp.h>

//set up to connect to an existing network (e.g. mobile hotspot from laptop that will run the python code)
const char* ssid = "Optus_A0516A";
const char* password = "lakes95962ca";
WiFiUDP Udp;
unsigned int espPort = 4211;  //  port to listen on
char incomingPacket[255];  // buffer for incoming packets

///////////////////////////////////// Sensor ////////////////////////////////////////////////////
#include <Wire.h>
#include "MLX90393.h" //From https://github.com/tedyapo/arduino-MLX90393 by Theodore Yapo

int delayyy = 1;
// create an array of sensors
#define num_of_sensors 1
MLX90393 sensors [num_of_sensors];
// MLX90393 mlx3;
MLX90393::txyz data; //Create a structure, called data, of four floats (t, x, y, and z)

// create an array of struct objects for collecting initial sensor and subsequent previous sensor readings
struct sat_flags
{
  bool sat = false; 
  bool sat_dir = false; // true: positive saturation, false: negative saturation
};
struct sensorReadings
{
  float data_arr[3]; // collect xyz readings
  float sat_val[3]; // collect the saturation readings when found
  sat_flags xyz_flags[3];
};
sensorReadings prevReadings[num_of_sensors];
sensorReadings initReadings[num_of_sensors];

float thres = 2000;

////////////////////// LED ////////////////////////////
const int led = D10;

void setup() {
  ///////////////////// Initialize Sensor ////////////////////////////////
  Serial.begin(9600);
  pinMode(led, OUTPUT);
  Serial.println("Starting Sensor");

  Wire.begin();
  sensors[0].begin(0,0);
  // sensors[1].begin(0,1);
  // sensors[2].begin(1,0);
  // sensors[3].begin(1,1);

  for (int i = 0; i < num_of_sensors;i++)
  {
    sensors[i].setOverSampling(0);
    sensors[i].setDigitalFiltering(0);
  }

  // average the offsets for n samples
  int num_of_samples = 50;
  delay(1000);
  for (int k = 0; k < num_of_samples; k++)
  {
    for (int i = 0; i < num_of_sensors;i++)
    {
      sensors[i].readData(data);
      initReadings[i].data_arr[0] = data.x+initReadings[i].data_arr[0];
      initReadings[i].data_arr[1] = data.y+initReadings[i].data_arr[1];
      initReadings[i].data_arr[2] = data.z+initReadings[i].data_arr[2];
    }
  }

  // collect the first prevReadings
  for (int i = 0; i < num_of_sensors;i++)
  {
    sensors[i].readData(data);
    initReadings[i].data_arr[0] = initReadings[i].data_arr[0]/num_of_samples;
    initReadings[i].data_arr[1] = initReadings[i].data_arr[1]/num_of_samples;
    initReadings[i].data_arr[2] = initReadings[i].data_arr[2]/num_of_samples;

    prevReadings[i].data_arr[0] = data.x;
    prevReadings[i].data_arr[1] = data.y;
    prevReadings[i].data_arr[2] = data.z;
  } 

  ///////////////////// Initialize UDP Connection ////////////////////////////////
  Serial.println("Starting UDP");
  int status = WL_IDLE_STATUS;
  WiFi.begin(ssid, password);
  // Serial.println("");

  // Wait for connection
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("Connected to wifi");
  Udp.begin(espPort);
  digitalWrite(led, HIGH);   // turn the LED on 
  Serial.printf("Now listening at IP %s, UDP port %d\n", WiFi.localIP().toString().c_str(), espPort);

  // we recv one packet from the remote so we can know its IP and port
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
      // Serial.printf("UDP packet contents: %s\n", incomingPacket);
      readPacket = true;
      digitalWrite(led, LOW);    // turn the LED off
    } 
  }
}

void loop() {
  String measurements = "";
  for (int i = 0; i < num_of_sensors;i++)
  {
    sensors[i].readData(data);

    // check saturation for each measurement axis
    for (int j = 0; j < 3; j++)
    {
      // set which axis to target
      float cur_axis_reading = 0.0;
      float corrected_axis_reading = 0.0;
      if (j == 0)
      {
        cur_axis_reading = data.x;
      }
      else if (j == 1)
      {
        cur_axis_reading = data.y;
      }
      else if (j == 2)
      {
        cur_axis_reading = data.z;
      }

      // check current axis saturation
      // when it is unsaturated
      if (!prevReadings[i].xyz_flags[j].sat)
      {
        // conditions for negative saturation and positive saturation 
        if ((cur_axis_reading - prevReadings[i].data_arr[j]) < -thres)
        {
          prevReadings[i].xyz_flags[j].sat = true; prevReadings[i].xyz_flags[j].sat_dir = true; // change the flags
          prevReadings[i].sat_val[j] = abs(prevReadings[i].data_arr[j]); // collect the saturation bounds
          corrected_axis_reading = cur_axis_reading+2*prevReadings[i].sat_val[j]-initReadings[i].data_arr[j];
        }
        else if ((cur_axis_reading - prevReadings[i].data_arr[j]) > thres)
        {
          prevReadings[i].xyz_flags[j].sat = true; prevReadings[i].xyz_flags[j].sat_dir = false;
          prevReadings[i].sat_val[j] = abs(prevReadings[i].data_arr[j]); // collect the saturation bounds
          corrected_axis_reading = cur_axis_reading-2*prevReadings[i].sat_val[j]-initReadings[i].data_arr[j];
        }
        else
        {
          corrected_axis_reading = cur_axis_reading-initReadings[i].data_arr[j];
        }
      }
      else
      {
        // when in positive saturation
        if (prevReadings[i].xyz_flags[j].sat_dir)
        {
          // condition to return to unsaturation
          if ((cur_axis_reading - prevReadings[i].data_arr[j]) > thres)
          {
            prevReadings[i].xyz_flags[j].sat = false;
            corrected_axis_reading = cur_axis_reading-initReadings[i].data_arr[j];
          }
          else
          {
            corrected_axis_reading = cur_axis_reading+2*prevReadings[i].sat_val[j]-initReadings[i].data_arr[j];
          }
        }
        // when in negative saturation
        else if (!prevReadings[i].xyz_flags[j].sat_dir)
        {
          // condition to return to unsaturation
          if ((cur_axis_reading - prevReadings[i].data_arr[j]) < -thres)
          {
            prevReadings[i].xyz_flags[j].sat = false;
            corrected_axis_reading = cur_axis_reading-initReadings[i].data_arr[j];
          }
          else
          {
            corrected_axis_reading = cur_axis_reading-2*prevReadings[i].sat_val[j]-initReadings[i].data_arr[j];
          }
        }
      }
      // Serial.printf("%f\t",corrected_axis_reading);
      measurements += String(corrected_axis_reading,4) +" ";

      // save previous reading for next iteration checking
      prevReadings[i].data_arr[j] = cur_axis_reading;
    }
  }
  Serial.println(measurements);
  
  // once we know where we got the inital packet from, send data back to that IP address and port
  Udp.beginPacket(Udp.remoteIP(), espPort);
  Udp.printf("%s\n", measurements.c_str());
  Udp.endPacket();
}

