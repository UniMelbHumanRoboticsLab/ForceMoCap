# pyRFT

Python interface for RFT series, Robotus 6-axis Force/Torque Sensor, over UART using pyserial

## prerequisite

- [pyserial](https://pyserial.readthedocs.io/en/latest/pyserial.html)

## RFT_UART.py

### RFTseries class

Main class for communicate with RFT series sensor.
Class initialization will automatically start reading response daemon thread.
You can access data received by `getResponse(resonseID)` method.
For example, `getResponse(ID_READ_MODEL_NAME)` will return the latest response of read model name command.

all methods

- sendCommand(command)
- getResponse(responseID)
- hardTare()
- softTare()
- getTareFT()
- close()

## RFT_UART_command.py

This file contains all the command for RFT series sensor.

## RFT_UART_response.py

This file contains depacket function for any response.

## example

```python
from RFT_UART import *
import time

PORT = "your sensor port"

rft = RFTseries(PORT)
rft.sendCommand(COMMAND_STOP_FT_DATA_OUTPUT)
rft.ser.flush()
rft.sendCommand(COMMNAD_READ_MODEL_NAME)
time.sleep(1)
print(responseReadModelName(rft.getResponse(1)))
rft.sendCommand(COMMAND_READ_SERIAL_NUMBER)
time.sleep(1)
print(responseReadSerialNUmber(rft.getResponse(2)))
rft.sendCommand(COMMAND_READ_BAUDRATE)
time.sleep(1)
print(responseReadBaudrate(rft.getResponse(7)))
rft.sendCommand(COMMAND_START_FT_DATA_OUTPUT)
time.sleep(1)
rft.sendCommand(commandSetBias(1))
for i in range(5000):
    print(responseReadFTData(rft.getResponse(11)))
    time.sleep(1/200)
```
