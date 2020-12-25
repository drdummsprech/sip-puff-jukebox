import multiprocessing as mp
import time

from bmp280.BMP280_I2C import BMP280_I2C
from input.PressureInput import PressureInput
from input.SipPuffEvent import SipPuffEvent, SipPuffListener


class InputWorker(mp.Process, SipPuffListener):
    """
    This worker basically handles the sip-puff input.
    Input events are put into the output queue from which they have to be read.
    """
    output_queue: mp.Queue

    __sensor: BMP280_I2C
    __pressure_input: PressureInput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.output_queue = mp.Queue()
        self.daemon = True

        self.__sensor = BMP280_I2C.create_default()
        self.__pressure_input = PressureInput(self.__sensor)
        self.__pressure_input.register_listener(self)

    def run(self):
        while True:
            try:
                time.sleep(0.01)
                self.__pressure_input.update()
            except:
                print("Exception in Input worker")

    def handle_sip_puff_event(self, event: SipPuffEvent) -> None:
        self.output_queue.put(event)
