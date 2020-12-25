import multiprocessing as mp
import queue as not_mp
from threading import Thread


class QueueMerge:
    """
    Helper class for merging multiple queues from background processes into a single one.
    Reading from more than one queue isn't trivial, since reads either block or throw after timeout.
    This class uses threads to just forward from multiple multiprocessing queues into a single
    regular queue.
    """
    __queues: [mp.Queue] = []
    __threads: [Thread] = []
    outputQueue: not_mp.Queue = not_mp.Queue()

    def add_input_queue(self, queue: mp.Queue):
        self.__queues.append(queue)
        thread = Thread(target=self.__monitor_queue, args=[queue, self.outputQueue])
        thread.daemon = True
        self.__threads.append(thread)

        thread.start()

    @staticmethod
    def __monitor_queue(input_queue: mp.Queue, output_queue: not_mp.Queue):
        while True:
            try:
                e = input_queue.get()
                output_queue.put(e)
            except:
                print("Exception in QueueMerge")
