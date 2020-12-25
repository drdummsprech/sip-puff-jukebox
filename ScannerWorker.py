import multiprocessing as mp

from scanner.ScannerEvents import ScannerEventHandler, ScannerEvent
from scanner.UsbRootScanner import Scanner


class ScannerWorker(mp.Process, ScannerEventHandler):
    """
    This worker handles the scanning of thumbdrives for music.
    Information about the results is put into the output queue, from which it has to be read.
    """
    output_queue: mp.Queue
    __scanner: Scanner

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.output_queue = mp.Queue()
        self.daemon = True

        self.__scanner = Scanner(self)

    def run(self):
        while True:
            try:
                self.__scanner.work_loop()
            except:
                print("Exception in Scanner worker")

    def handle_scanner_event(self, event: ScannerEvent):
        self.output_queue.put(event)
