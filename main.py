from AudioPlayer import AudioPlayer
from InputWorker import InputWorker
from MusicDB import MusicDB
from ScannerWorker import ScannerWorker
from input.SipPuffEvent import SipPuffEvent
from helpers.QueueMerge import QueueMerge
from scanner.ScannerEvents import ScannerEvent, RootPathAppeared, RootPathRemoved, AudioFileFound

if __name__ == '__main__':
    # Create the database
    mdb = MusicDB()

    # initialize input system
    inputProcess = InputWorker()
    inputProcess.start()

    # initialize scanner
    scannerProcess = ScannerWorker()
    scannerProcess.start()

    # merge the outputs into a single queue
    qm = QueueMerge()
    qm.add_input_queue(inputProcess.output_queue)
    qm.add_input_queue(scannerProcess.output_queue)

    # initialize audio player
    player = AudioPlayer()

    while True:
        # Endless work loop. We read an event and act on it
        event = qm.outputQueue.get()
        # print(event.__str__())

        if isinstance(event, ScannerEvent):
            # Scanner event handler block
            if isinstance(event, RootPathAppeared):
                mdb.add_root_path(event.rootPath)
            elif isinstance(event, RootPathRemoved):
                mdb.remove_root_path(event.rootPath)
            elif isinstance(event, AudioFileFound):
                mdb.add_entry(event.path, event.gain_level)
                print(event.path.__str__() + ": " + event.gain_level.__str__())

        elif isinstance(event, SipPuffEvent):
            # Input event handler block
            if event in SipPuffEvent.get_all_puff_events():
                music = (mdb.get_random_entry())
                if music:
                    player.play(music.path, music.gain_level)
            elif event in SipPuffEvent.get_all_sip_events():
                player.stop()
