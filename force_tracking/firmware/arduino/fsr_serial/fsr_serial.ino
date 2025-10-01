//From the bildr article http://bildr.org/2012/11/flexiforce-arduino/

// int fsrPins[9] = {A0,A1,A2,A3,A4,A5,A8,A9,A10}; //analog pin 0
int fsrPins[9] = {A5,A3,A1,A8,A10,A4,A2,A0,A9}; //analog pin for Left

float resistor = 2201.0;
float Vin = 3.3;
String measurements = "";

void setup(){
  Serial.begin(9600);
  analogReadResolution(12);
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
    measurements += String(resistance,4) +"\t";
    // measurements += String(fsrReading) +"\t";
    delay(1); // give delay between analog reads
  }

  // print out the value you read:
  Serial.println(measurements);
  // delay(10); //100Hz
}