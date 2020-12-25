import spidev

from bmp280.BMP280Base import BMP280Base, SamplingMode


class BMP280_SPI(BMP280Base):
    __bus: spidev

    def __init__(self, bus_number: int, bus_address: int, bus_mode: int, bus_speed: int):
        self.__bus = spidev.SpiDev()
        self.__bus.open(bus_number, bus_address)
        self.__bus.max_speed_hz = bus_speed
        self.__bus.mode = bus_mode

    def read_single_byte(self, addr: int):
        # reading must have the highest bit set to 1
        # after that we clock out the result
        values = self.__bus.xfer2([addr | 0x80, 0x0])
        return values[1]

    def read_multiple_bytes(self, addr: int, length: int):
        # reading must have the highest bit set to 1
        # after that we clock out the results
        data = [addr | 0x80] + (length * [0x0])
        values = self.__bus.xfer2(data)
        return values[1:]

    def write_single_byte(self, addr: int, value: int):
        # writing must have the highest bit set to 0
        self.__bus.xfer2([addr & 0b0111_1111, value])

    @staticmethod
    def create_default():
        bmp = BMP280_SPI(0, 0, 0b00, 500_000)
        bmp.__busNum = 0
        bmp.__address = 0
        bmp.__temperatureMode = SamplingMode.X_2
        bmp.__pressureMode = SamplingMode.X_2

        bmp.configure_sensor()
        return bmp
