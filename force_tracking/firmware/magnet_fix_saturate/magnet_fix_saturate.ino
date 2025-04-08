#include <Wire.h>
#include "MLX90393.h" //From https://github.com/tedyapo/arduino-MLX90393 by Theodore Yapo

int delayyy = 1;
// create an array of sensors
#define num_of_sensors 4
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

float thres = 2000;

sensorReadings prevReadings[num_of_sensors];
sensorReadings initReadings[num_of_sensors];

// Initialize an array to store past readings
const int filterSize = 20;
float filterArray[filterSize];

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);

  Wire.begin();
  sensors[0].begin(0,0);
  sensors[1].begin(0,1);
  sensors[2].begin(1,0);
  sensors[3].begin(1,1);

  tcaselect(0);    // 0 - 7 of the TCA9548A channels

  for (int i = 0; i < num_of_sensors;i++)
  {
    sensors[i].setOverSampling(0);
    sensors[i].setDigitalFiltering(0);
  }
  
  
  tcaselect(0);    // 0 - 7 of the TCA9548A channels

  // average the offsets for 10 samples
  int num_of_samples = 500;
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
}

void loop() {

  for (int i = 0; i < num_of_sensors;i++)
  {
    sensors[i].readData(data);

    // check saturation for each measurement axis
    for (int j = 0; j < 3; j++)
    {
      // set which axis to target
      float cur_axis_reading = 0.0;
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
          Serial.print(cur_axis_reading+2*prevReadings[i].sat_val[j]-initReadings[i].data_arr[j]);
        }
        else if ((cur_axis_reading - prevReadings[i].data_arr[j]) > thres)
        {
          prevReadings[i].xyz_flags[j].sat = true; prevReadings[i].xyz_flags[j].sat_dir = false;
          prevReadings[i].sat_val[j] = abs(prevReadings[i].data_arr[j]); // collect the saturation bounds
          Serial.print(cur_axis_reading-2*prevReadings[i].sat_val[j]-initReadings[i].data_arr[j]);
        }
        else
        {
          Serial.print(cur_axis_reading-initReadings[i].data_arr[j]);
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
            Serial.print(cur_axis_reading-initReadings[i].data_arr[j]);
          }
          else
          {
            Serial.print(cur_axis_reading+2*prevReadings[i].sat_val[j]-initReadings[i].data_arr[j]);
          }
        }
        // when in negative saturation
        else if (!prevReadings[i].xyz_flags[j].sat_dir)
        {
          // condition to return to unsaturation
          if ((cur_axis_reading - prevReadings[i].data_arr[j]) < -thres)
          {
            prevReadings[i].xyz_flags[j].sat = false;
            Serial.print(cur_axis_reading-initReadings[i].data_arr[j]);
          }
          else
          {
            Serial.print(cur_axis_reading-2*prevReadings[i].sat_val[j]-initReadings[i].data_arr[j]);
          }
        }
      }
      Serial.print("\t");

      // save previous reading for next iteration
      prevReadings[i].data_arr[j] = cur_axis_reading;
    }
  }
  Serial.println();

// Read new data and update the filter
    // float filteredValue = movingAverage(DataR[11] - Data[11]);
// Use the filtered value for printing or other purposes
  //  Serial.println(filteredValue, 0);
}

// Initialize I2C buses using TCA9548A I2C Multiplexer
void tcaselect(uint8_t i2c_bus) {
    if (i2c_bus > 7) return;
    Wire.beginTransmission(0x70);
    Wire.write(1 << i2c_bus);
    Wire.endTransmission(); 
}

// Function to add a new reading to the filter array and return the average
float movingAverage(float newValue) {
    // Shift all previous readings to make room for the new reading
    for (int i = filterSize - 1; i > 0; i--) {
        filterArray[i] = filterArray[i - 1];
    }
    // Add the new reading
    filterArray[0] = newValue;

    // Calculate the average
    float sum = 0;
    for (int i = 0; i < filterSize; i++) {
        sum += filterArray[i];
    }
    return sum / filterSize;
}
