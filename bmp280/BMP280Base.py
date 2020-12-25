from abc import abstractmethod
from enum import IntFlag
import struct

from input.IPressureSensor import IPressureSensor


class Registers(IntFlag):
    """Memory addresses from the datasheet for various chip registers"""
    CONTROL = 0xF4
    CONFIG = 0xF5
    PRESSURE_BYTE_HIGH = 0xF7
    PRESSURE_BYTE_MIDDLE = 0xF8
    PRESSURE_BYTE_LOW = 0xF9
    TEMPERATURE_BYTE_HIGH = 0xFA
    TEMPERATURE_BYTE_MIDDLE = 0xFB
    TEMPERATURE_BYTE_LOW = 0xFC

    # ! CALIB_TEMP_1 is unsigned, 2 and 3 are signed
    CALIB_TEMP_1_LOW = 0x88
    CALIB_TEMP_1_HIGH = 0x89
    CALIB_TEMP_2_LOW = 0x8B
    CALIB_TEMP_2_HIGH = 0x8A
    CALIB_TEMP_3_LOW = 0x8D
    CALIB_TEMP_3_HIGH = 0x8C

    # CALIB_PRES_1 is unsigned, the rest is signed
    CALIB_PRES_1_LOW = 0x8E
    CALIB_PRES_1_HIGH = 0x8F
    CALIB_PRES_2_LOW = 0x90
    CALIB_PRES_2_HIGH = 0x91
    CALIB_PRES_3_LOW = 0x92
    CALIB_PRES_3_HIGH = 0x93
    CALIB_PRES_4_LOW = 0x94
    CALIB_PRES_4_HIGH = 0x95
    CALIB_PRES_5_LOW = 0x96
    CALIB_PRES_5_HIGH = 0x97
    CALIB_PRES_6_LOW = 0x98
    CALIB_PRES_6_HIGH = 0x99
    CALIB_PRES_7_LOW = 0x9A
    CALIB_PRES_7_HIGH = 0x9B
    CALIB_PRES_8_LOW = 0x9C
    CALIB_PRES_8_HIGH = 0x9D
    CALIB_PRES_9_LOW = 0x9E
    CALIB_PRES_9_HIGH = 0x9F


class SamplingMode(IntFlag):
    """Enum for the sampling modes that can be set for Temperature and pressure on the BMP 280"""
    NO_SAMPLING = 0b000  # Takes no samples at all
    X_1 = 0b001
    X_2 = 0b010
    X_4 = 0b011
    X_8 = 0b100
    X_16 = 0b101


class PowerMode(IntFlag):
    SLEEP = 0b0
    FORCED = 0b01
    NORMAL = 0b11


class FilterCoefficient(IntFlag):
    OFF = 0b0
    VAL_2 = 2
    VAL_4 = 4
    VAL_8 = 8
    VAL_16 = 16


class StandbyTime(IntFlag):
    """This is the time the chip will wait between measurements in normal mode"""
    MINIMUM = 0b000  # 0.5ms
    MS_62 = 0b001
    MS_125 = 0b010
    MS_250 = 0b011
    MS_500 = 0b100
    MS_1000 = 0b101
    MS_2000 = 0b110
    MS_4000 = 0b111


class BMP280Base(IPressureSensor):
    """
    Base class for the different bus variants of the BMP280.
    This contains all the logic for communicating with the chip except the actual
    bus specific commands for reading and writing to the chip
    """

    @abstractmethod
    def read_single_byte(self, addr: int) -> int:
        """
        This method should read a single byte from the given memory address
        :param addr: The address of the memory to read
        :return: The byte read as an int
        """
        pass

    @abstractmethod
    def read_multiple_bytes(self, addr: int, length: int) -> [int]:
        """
        This method should read multiple bytes from the chip's memory, starting from
        the given address and reading length bytes in total.
        It's important that the read happens as a single continuous read. Otherwise
        the chip does not guarantee proper shadowing of the data addresses and the
        returned value might be corrupted.
        :param addr: The starting address of the memory to read
        :param length: The number of bytes to read in total
        :return: The read bytes as ints
        """
        pass

    @abstractmethod
    def write_single_byte(self, addr: int, value: int):
        """
        This method should write a single byte to the chip's memory at the given address.
        :param addr: The address to write to
        :param value: The value to write to the address
        :return: None
        """
        pass

    __temperatureMode: SamplingMode = SamplingMode.X_1
    __pressureMode: SamplingMode = SamplingMode.X_1
    __powerMode: PowerMode = PowerMode.NORMAL

    __standbyTime: StandbyTime = StandbyTime.MINIMUM
    __filterCoeff: FilterCoefficient = FilterCoefficient.VAL_2

    __tempCalibData: [int]
    __presCalibData: [int]

    def check_chip_id(self) -> bool:
        """
        Tries to read the chip ID value from the chip and compares it to the
        expected value.
        :return: True if the correct chip ID could be read from the chip, false otherwise
        """
        return self.read_single_byte(0xD0) == 0x58

    def configure_sensor(self):
        """
        Configures the sensor by writing the options such as power mode to the chip.
        This also reads the factory calibration data off the chip.
        :return: None
        """

        # Create config register data
        config_data: int = (self.__filterCoeff << 1) + (self.__standbyTime << (1 + 3))
        self.write_single_byte(Registers.CONFIG, config_data)

        # Create control register data
        control_data: int = self.__powerMode + (self.__pressureMode << 2) + (self.__temperatureMode << (2 + 3))
        self.write_single_byte(Registers.CONTROL, control_data)

        # Read the calibration data raw values
        temp_calib_raw = self.read_multiple_bytes(Registers.CALIB_TEMP_1_LOW, 6)
        pres_calib_raw = self.read_multiple_bytes(Registers.CALIB_PRES_1_LOW, 18)

        # Both of these are actually 16 bit numbers in two halves, and in both cases the first 16 bit
        # number is unsigned, while the remaining ones are signed
        self.__tempCalibData = self.__convert_raw_calib_data(temp_calib_raw)
        self.__presCalibData = self.__convert_raw_calib_data(pres_calib_raw)

    @staticmethod
    def __convert_raw_calib_data(data: [int]) -> [int]:
        """
        Converts lists of ints of 8 bit numbers to lists of 16 bit numbers.
        The output is half the length of the input.
        The first pair will be treated as signed, the remaining pairs as unsigned
        :param data: The bytes to convert
        :return: A list with the converted ints
        """
        if len(data) % 2 != 0:
            raise Exception("Calib data has wrong size, must be divisible by 2")
        if len(data) < 6:
            raise Exception("Calib Data must at least be six bytes long")
        out: [int] = []

        # Calculate the unsigned value
        tmp = struct.unpack("<H", bytearray([data[0], data[1]]))
        out.append(tmp[0])

        for i in range(2, len(data), 2):
            tmp = struct.unpack("<h", bytearray([data[i], data[i + 1]]))
            out.append(tmp[0])
        return out

    def __read_three_byte_as_20bit_int(self, start: Registers) -> int:
        """
        The measurements are three bytes wide each but contain only 20 bytes
        of data. This method reads the three bytes and performs the necessary
        bit shifting.
        :param start: The memory address to start reading the 3 bytes from
        :return: The measurement value as an int
        """
        data: [int] = self.read_multiple_bytes(start, 3)

        high: int = data[0]
        middle: int = data[1]
        low: int = data[2]

        # 20 Bit value, only upper half of low byte is used
        val = (low >> 4) + (middle << 4) + (high << (4 + 8))
        return val

    def __read_temp_raw(self):
        """
        Reads the raw temperature value from from the chip.
        :return: The raw, unscaled and uncorrected temperature value
        """
        return self.__read_three_byte_as_20bit_int(Registers.TEMPERATURE_BYTE_HIGH)

    def read_pressure_raw(self):
        """
        Reads the raw pressure value from the chip.
        :return: The raw pressure value
        """
        return self.__read_three_byte_as_20bit_int(Registers.PRESSURE_BYTE_HIGH)

    def __compensate_temperature(self, raw_temperature):
        """
        Applies the calibration values to the raw temperature.
        The returned temperature is not yet converted to celsius
        :param raw_temperature: The raw temperature as read from the chip
        :return: The temperature after applying the calibration
        """
        var1 = (raw_temperature / 16384.0 - self.__tempCalibData[0] / 1024.0) * self.__tempCalibData[1]
        var2 = raw_temperature / 131072.0 - self.__tempCalibData[0] / 8192.0
        var2 = var2 * var2 * self.__tempCalibData[2]
        return (var1 + var2)

    def __compensate_pressure(self, raw_pressure, temp_compensated):
        """
        Apply the calibration and temperature compensation to the raw pressure value
        The temp value should be compensated, but not converted to degrees yet.
        This stuff is from the data sheet.
        :param raw_pressure: Raw pressure value
        :param temp_compensated: Compensated, but not yet Celsius scaled tempereature
        :return: The pressure after calibration and temperature compensation in Pascal
        """

        var1 = temp_compensated / 2.0 - 64000.0
        var2 = var1 * var1 * self.__presCalibData[5] / 32768.0
        var2 = var2 + var1 * self.__presCalibData[4] * 2.0
        var2 = var2 / 4.0 + self.__presCalibData[3] * 65536.0
        var1 = (self.__presCalibData[2] * var1 * var1 / 524288.0 + self.__presCalibData[1] * var1) / 524288.0
        var1 = (1.0 + var1 / 32768.0) * self.__presCalibData[0]
        if var1 == 0:
            return 0
        pressure = 1048576.0 - raw_pressure
        pressure = (pressure - var2 / 4096.0) * 6250.0 / var1
        var1 = self.__presCalibData[8] * pressure * pressure / 2147483648.0
        var2 = pressure * self.__presCalibData[7] / 32768.0
        pressure = pressure + (var1 + var2 + self.__presCalibData[6]) / 16.0

        return pressure

    def read_temperature(self):
        """
        :return: The temperature in Celsius
        """
        raw = self.__read_temp_raw()
        comp = self.__compensate_temperature(raw)
        return comp / 5120.0

    def get_pressure_in_Pascal(self):
        """
        :return: The pressure in Pascal
        """
        raw_temp = self.__read_temp_raw()
        comp_temp = self.__compensate_temperature(raw_temp)
        raw_pres = self.read_pressure_raw()
        comp_pres = self.__compensate_pressure(raw_pres, comp_temp)
        return comp_pres
