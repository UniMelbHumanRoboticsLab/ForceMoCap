#include <Wire.h>
#include "MLX90393.h" //From https://github.com/tedyapo/arduino-MLX90393 by Theodore Yapo

MLX90393 mlx0;
MLX90393 mlx1;
MLX90393 mlx2;
MLX90393 mlx3;
MLX90393::txyz data; //Create a structure, called data, of four floats (t, x, y, and z)


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

  // char buff[21];  
  // sprintf(buff,"IMU1:%7.2f,%7.2f,%7.2f | ",DataR[0],DataR[1],DataR[2]);   
  // Serial.print(buff);
  // sprintf(buff,"IMU2:%7.2f,%7.2f,%7.2f | ",DataR[3],DataR[4],DataR[5]);   
  // Serial.print(buff);
  // sprintf(buff,"IMU3:%7.2f,%7.2f,%7.2f | ",DataR[6],DataR[7],DataR[8]);   
  // Serial.print(buff);
  // sprintf(buff,"IMU4:%7.2f,%7.2f,%7.2f",DataR[9],DataR[10],DataR[11]);   
  // Serial.println(buff);

  for (int i = 0; i < 12; i++)
  {
    Serial.print(DataR[i]);
    Serial.print("\t");
  }
  Serial.println();
  
  // Serial.print(DataR[1]- Data[1]);
  // Serial.print("\t");
  // Serial.print(DataR[2]- Data[2]);
  // Serial.print("\t");
  // Serial.print(DataR[3]- Data[3]);
  // Serial.print("\t");
  // Serial.print(DataR[4]- Data[4]);
  // Serial.print("\t");
  // Serial.print(DataR[5]- Data[5]);
  // Serial.print("\t");
  // Serial.print(DataR[6]- Data[6]);
  // Serial.print("\t");
  // Serial.print(DataR[7]- Data[7]);
  // Serial.print("\t");
  // Serial.print(DataR[8]- Data[8]);
  // Serial.print("\t");
  // Serial.print(DataR[9]- Data[9]);
  // Serial.print("\t");
  // Serial.print(DataR[10]- Data[10]);
  // Serial.print("\t");
  // Serial.println(DataR[11]);

  //  // Calculate the differences
  // float diff1 = DataR[9] - Data[9];
  // float diff2 = DataR[10] - Data[10];
  // float diff3 = DataR[11] - Data[11];

  // // Calculate the sum of squares
  // float sumOfSquares = diff1 * diff1 + diff2 * diff2 + diff3 * diff3;

  // // Calculate the square root of the summation
  // float result = sqrt(sumOfSquares);

  // Print the result
  // Serial.print(result);

  // tcaselect(1);    // 0 - 7 of the TCA9548A channels

  // mlx0.readData(data); //Read the values from the sensor
  // DataR[12]=data.x;DataR[13]=data.y;DataR[14]=data.z;
  
  // mlx1.readData(data); //Read the values from the sensor
  // DataR[15]=data.x;DataR[16]=data.y;DataR[17]=data.z;

  // mlx2.readData(data); //Read the values from the sensor
  // DataR[18]=data.x;DataR[19]=data.y;DataR[20]=data.z;

  // mlx3.readData(data); //Read the values from the sensor
  // DataR[21]=data.x;DataR[22]=data.y;DataR[23]=data.z;

  // tcaselect(2);    // 0 - 7 of the TCA9548A channels

  // mlx0.readData(data); //Read the values from the sensor
  // DataR[24]=data.x;DataR[25]=data.y;DataR[26]=data.z;
  
  // mlx1.readData(data); //Read the values from the sensor
  // DataR[27]=data.x;DataR[28]=data.y;DataR[29]=data.z;

  // mlx2.readData(data); //Read the values from the sensor
  // DataR[30]=data.x;DataR[31]=data.y;DataR[32]=data.z;

  // mlx3.readData(data); //Read the values from the sensor
  // DataR[33]=data.x;DataR[34]=data.y;DataR[35]=data.z;
  // Serial.print(",");
  // Serial.print(DataR[12]-Data[12],0);
  // Serial.print(",");
  // Serial.print(DataR[13]-Data[13],0);
  // Serial.print(",");
  // Serial.print(DataR[14]-Data[14],0);
  // Serial.print(",");
  // Serial.print(DataR[15]-Data[15],0);
  // Serial.print(",");
  // Serial.print(DataR[16]-Data[16],0);
  // Serial.print(",");
  // Serial.print(DataR[17]-Data[17],0);
  // Serial.print(",");
  // Serial.print(DataR[18]-Data[18],0);
  // Serial.print(",");
  // Serial.print(DataR[19]-Data[19],0);
  // Serial.print(",");
  // Serial.print(DataR[20]-Data[20],0);
  // Serial.print(",");
  // Serial.print(DataR[21]-Data[21],0);
  // Serial.print(",");
  // Serial.print(DataR[22]-Data[22],0);
  // Serial.print(",");
  // Serial.print(DataR[23]-Data[23],0);
  // Serial.print(",");
  // Serial.print(DataR[24]-Data[24],0);
  // Serial.print(",");
  // Serial.print(DataR[25]-Data[25],0);
  // Serial.print(",");
  // Serial.print(DataR[26]-Data[26],0);
  // Serial.print(",");
  // Serial.print(DataR[27]-Data[27],0);
  // Serial.print(",");
  // Serial.print(DataR[28]-Data[28],0);
  // Serial.print(",");
  // Serial.print(DataR[29]-Data[29],0);
  // Serial.print(",");
  // Serial.print(DataR[30]-Data[30],0);
  // Serial.print(",");
  // Serial.print(DataR[31]-Data[31],0);
  // Serial.print(",");
  // Serial.print(DataR[32]-Data[32],0);
  // Serial.print(",");
  // Serial.print(DataR[33]-Data[33],0);
  // Serial.print(",");
  // Serial.print(DataR[34]-Data[34],0);
  // Serial.print(",");
  // Serial.print(DataR[35]-Data[35],0);

  

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
