import smbus

from bmp280.BMP280Base import BMP280Base, SamplingMode


class BMP280_I2C(BMP280Base):
    __address: int = 0x76  # Hardcoded in the chip

    __bus: smbus.SMBus

    def __init__(self, bus_number: int):
        self.__bus = smbus.SMBus(bus_number)

    def read_single_byte(self, addr: int):
        return self.__bus.read_byte_data(self.__address, addr)

    def read_multiple_bytes(self, addr: int, length: int):
        return self.__bus.read_i2c_block_data(self.__address, addr, length)

    def write_single_byte(self, addr: int, value: int):
        self.__bus.write_byte_data(self.__address, addr, value)

    @staticmethod
    def create_default():
        bmp = BMP280_I2C(1)
        bmp.__temperatureMode = SamplingMode.X_2
        bmp.__pressureMode = SamplingMode.X_2

        bmp.configure_sensor()
        if not bmp.check_chip_id():
            raise Exception("Error reading chip ID from BMP 280. This is a sign for connection problems.")
        return bmp
