COMMNAD_READ_MODEL_NAME                 = bytes.fromhex('01 00 00 00 00 00 00 00')
COMMAND_READ_SERIAL_NUMBER              = bytes.fromhex('02 00 00 00 00 00 00 00')
COMMAND_READ_FIRMWARE_VERSION           = bytes.fromhex('03 00 00 00 00 00 00 00')
COMMAND_READ_BAUDRATE                   = bytes.fromhex('07 00 00 00 00 00 00 00')
COMMAND_READ_FILTER                     = bytes.fromhex('09 00 00 00 00 00 00 00')
COMMAND_READ_FT_DATA                    = bytes.fromhex('0A 00 00 00 00 00 00 00')
COMMAND_START_FT_DATA_OUTPUT            = bytes.fromhex('0B 00 00 00 00 00 00 00')
COMMAND_STOP_FT_DATA_OUTPUT             = bytes.fromhex('0C 00 00 00 00 00 00 00')
COMMAND_READ_DATA_OUTPUT_RATE           = bytes.fromhex('10 00 00 00 00 00 00 00')
COMMAND_READ_COUNT_OVERLOAD_OCCURRENCE  = bytes.fromhex('12 00 00 00 00 00 00 00')
def commandSetBaudrate(baudrate: int):
    if baudrate == 115200:
        return bytes.fromhex('06 00 00 00 00 00 00 00')
    elif baudrate == 921600:
        return bytes.fromhex('06 01 00 00 00 00 00 00')
    elif baudrate == 460800:
        return bytes.fromhex('06 02 00 00 00 00 00 00')
    elif baudrate == 230400:
        return bytes.fromhex('06 03 00 00 00 00 00 00')
    elif baudrate == 115200:
        return bytes.fromhex('06 04 00 00 00 00 00 00')
    elif baudrate == 57600:
        return bytes.fromhex('06 05 00 00 00 00 00 00')
    else:
        print("baudrate not supported. Supported baudrates are 115200, 921600, 460800, 230400, 115200, 57600")
        raise ValueError('Invalid baudrate')
def commandSetFilter(type: int, parameter: int):
    if (type != 0) and (type != 1):
        print("Invalid type. Supported types are 0 and 1")
        raise ValueError('Invalid type')
    if parameter < 0 or parameter > 14:
        print("Invalid parameter. Supported parameters are 0 to 14")
        raise ValueError('Invalid parameter')
    return b'\10' + int.to_bytes(type) + int.to_bytes(parameter) + b'\00\00\00\00\00'
def commandSetDataOutputRate(hz: int):
    paramDict = { 200: 0, 10: 1, 20: 2,
                  50: 3, 100: 4, 200: 5,
                  333: 6, 500: 7, 1000: 8 }
    parameter = paramDict.get(hz)
    if parameter == None:
        print("Invalid hz. Supported hz are 200, 10, 20, 50, 100, 200, 333, 500, 1000")
        raise ValueError('Invalid hz')
    return b'\17' + int.to_bytes(parameter) + b'\00\00\00\00\00\00'
def commandSetBias(bias: bool):
    return b'\21' + (b'\01' if bias else b'\00') + b'\00\00\00\00\00\00'