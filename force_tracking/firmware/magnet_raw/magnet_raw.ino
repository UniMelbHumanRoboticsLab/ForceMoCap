#include <Wire.h>
#include "MLX90393.h" //From https://github.com/tedyapo/arduino-MLX90393 by Theodore Yapo

MLX90393 mlx0;
MLX90393 mlx1;
MLX90393 mlx2;
MLX90393 mlx3;
MLX90393::txyz data; //Create a structure, called data, of four floats (t, x, y, and z)
int num_of_sensor = 4;

float DataR[35];
float Data[35];

// Define the size of the moving average filter
const int filterSize = 20;

// Initialize an array to store past readings
float filterArray[filterSize];



  
void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);

  Wire.begin();
  mlx0.begin(0,0);
  mlx1.begin(0,1);
  mlx2.begin(1,0);
  mlx3.begin(1,1);

  tcaselect(0);    // 0 - 7 of the TCA9548A channels

  
  mlx0.setOverSampling(0);
  mlx1.setOverSampling(0);
  mlx2.setOverSampling(0);
  mlx3.setOverSampling(0);

  mlx0.setDigitalFiltering(0);
  mlx1.setDigitalFiltering(0);
  mlx2.setDigitalFiltering(0);
  mlx3.setDigitalFiltering(0);
  delay(100);
  
  tcaselect(0);    // 0 - 7 of the TCA9548A channels


  mlx0.readData(data); //Read the values from the sensor
  Data[0]=data.x;Data[1]=data.y;Data[2]=data.z;
  
  mlx1.readData(data); //Read the values from the sensor
  Data[3]=data.x;Data[4]=data.y;Data[5]=data.z;

  mlx2.readData(data); //Read the values from the sensor
  Data[6]=data.x;Data[7]=data.y;Data[8]=data.z;

  mlx3.readData(data); //Read the values from the sensor
  Data[9]=data.x;Data[10]=data.y;Data[11]=data.z;

  delay(300);


  mlx0.readData(data); //Read the values from the sensor
  Data[0]=data.x;Data[1]=data.y;Data[2]=data.z;
  
  mlx1.readData(data); //Read the values from the sensor
  Data[3]=data.x;Data[4]=data.y;Data[5]=data.z;

  mlx2.readData(data); //Read the values from the sensor
  Data[6]=data.x;Data[7]=data.y;Data[8]=data.z;

  mlx3.readData(data); //Read the values from the sensor
  Data[9]=data.x;Data[10]=data.y;Data[11]=data.z;
//  
}

void loop() {
  // put your main code here, to run repeatedly:
  // Serial.print("Time: ");
  // int   tt = millis();
  // Serial.print(tt);
  // Serial.print(",");
    
  
  // tcaselect(0);    // 0 - 7 of the TCA9548A channels

  mlx0.readData(data); //Read the values from the sensor
  DataR[0]=data.x;DataR[1]=data.y;DataR[2]=data.z;
  
  mlx1.readData(data); //Read the values from the sensor
  DataR[3]=data.x;DataR[4]=data.y;DataR[5]=data.z;

  mlx2.readData(data); //Read the values from the sensor
  DataR[6]=data.x;DataR[7]=data.y;DataR[8]=data.z;

  mlx3.readData(data); //Read the values from the sensor
  DataR[9]=data.x;DataR[10]=data.y;DataR[11]=data.z;


  for (int i = 0; i < num_of_sensor*3; i++)
  {
    Serial.print(DataR[i]);
    Serial.print("\t");
  }
  Serial.println();
  

// Read new data and update the filter
    float filteredValue = movingAverage(DataR[11] - Data[11]);
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
