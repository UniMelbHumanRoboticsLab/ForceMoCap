#include <Wire.h>
#include "MLX90393.h" //From https://github.com/tedyapo/arduino-MLX90393 by Theodore Yapo
#include <Ewma.h>

// sensor array
#define num_of_sensors 4
MLX90393 sensors[num_of_sensors];
MLX90393::txyz data; // Create a structure, called data, of four floats (t, x, y, and z) to store reading from sensor
// struct object for collecting initial sensor and subsequent previous sensor readings
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
struct filter_3d
{
  Ewma adcFilter[3] { 0.1, 0.1, 0.1 };
};
float thres = 2000;
sensorReadings prevReadings[num_of_sensors]; // collect for online comparison
sensorReadings initReadings[num_of_sensors]; // to remove bias
filter_3d filters[num_of_sensors];
String measurements = "";

// CODE START //
void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  Wire.begin();
  init_sensor();
  calibrate_sensor();
  Serial.println("Sensors Calibrated");
}

void loop() {
  Serial.write(0x02); // STX - Start of text
  fix_saturate();
  Serial.println(measurements);
  measurements = "";
}

void init_sensor()
{
  Serial.println("Searching");
  for (int i = 0; i < num_of_sensors; i++) 
  {
    uint8_t bit1 = (i >> 1) & 1;  // Most significant bit
    uint8_t bit0 = i & 1;         // Least significant bit
    while (sensors[i].begin(bit1,bit0))
    {
      Serial.print(".");
    }
    uint8_t gain = 0;
    uint8_t hallconf = 0x00;
    uint8_t temp_comp = 0;
    uint8_t resx = 0;
    uint8_t resy = 0;
    uint8_t resz = 0;
    uint8_t digfil = 0;
    uint8_t osr = 0;

    sensors[i].setOverSampling(osr);
    sensors[i].setDigitalFiltering(digfil);
    sensors[i].setGainSel(gain);
    sensors[i].setHallConf(hallconf);
    sensors[i].setTemperatureCompensation(temp_comp);
    // sensors[i].setResolution(resx,resy,resz);

    sensors[i].getOverSampling(osr);
    sensors[i].getDigitalFiltering(digfil);
    sensors[i].getGainSel(gain);
    sensors[i].getHallConf(hallconf);
    sensors[i].getTemperatureCompensation(temp_comp);
    sensors[i].getResolution(resx,resy,resz);

    Serial.printf("Sensor%d found: osr:%d digfil:%d gain:%d hallconf:%d temp_comp:%d res:%d%d%d\n", i+1,osr,digfil,gain,hallconf,temp_comp,resx,resy,resz);
    delay(500);
  }
}

void remove_error(int i,bool debug)
{
  bool error = sensors[i].hasError(sensors[i].readData(data));
  while (error)
  {
    if (debug)
    {
      Serial.printf("Error%d found\n",i);
    }
    error = sensors[i].hasError(sensors[i].readData(data)); 
    delay(2);
  }
}

void calibrate_sensor()
{
  // average the offsets for 500 samples
  int num_of_samples = 100;
  delay(1000);
  for (int i = 0; i < num_of_sensors;i++)
  {
    
    for (int k = 0; k < num_of_samples; k++)
    {
      Serial.print(".");
      remove_error(i,true);
      initReadings[i].data_arr[0] = data.x+initReadings[i].data_arr[0];
      initReadings[i].data_arr[1] = data.y+initReadings[i].data_arr[1];
      initReadings[i].data_arr[2] = data.z+initReadings[i].data_arr[2];
      delay(2); // small delay for single sensor 
    }
    Serial.printf("Sensor%d calibrated\n",i);
    
  }
  
  for (int i = 0; i < num_of_sensors;i++)
  {
    initReadings[i].data_arr[0] = initReadings[i].data_arr[0]/num_of_samples;
    initReadings[i].data_arr[1] = initReadings[i].data_arr[1]/num_of_samples;
    initReadings[i].data_arr[2] = initReadings[i].data_arr[2]/num_of_samples;

    remove_error(i,true);
    prevReadings[i].data_arr[0] = data.x;
    prevReadings[i].data_arr[1] = data.y;
    prevReadings[i].data_arr[2] = data.z;
  } 
}

void fix_saturate(){
  for (int i = 0; i < num_of_sensors;i++)
  {
    remove_error(i,false);
    
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
      float filt_cur_axis_reading = filters[i].adcFilter[j].filter(cur_axis_reading);
      measurements += String(filt_cur_axis_reading-initReadings[i].data_arr[j],4) +"\t";

      // save previous reading for next iteration
      prevReadings[i].data_arr[j] = filt_cur_axis_reading;
    }
    // delay(2);
  }
  
}

// 