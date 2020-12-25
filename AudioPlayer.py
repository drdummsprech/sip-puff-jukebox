from pathlib import Path

import vlc


class AudioPlayer:
    """
    Wrapper around VLC, which has to be installed on the system for this to work.
    """
    vlcInstance: vlc.Instance = vlc.Instance()
    player: vlc.MediaPlayer
    eq: vlc.AudioEqualizer

    def __init__(self):
        self.player = self.vlcInstance.media_player_new()
        self.eq = vlc.AudioEqualizer()
        self.player.set_equalizer(self.eq)

    def play(self, file: Path, level: float):
        """
        Plays an audio file with VLC.
        The gain level on VLC's preamp is set such that the resulting gain level of the file is +5dB.
        The most important effect of this is that all files sound roughly just as loud as each other.
        The rather high level of +5dB is due to the Rpi having a really low level headphone output.
        :param file: The path of the file to play
        :param level: The gain level to assume for this file
        :return:
        """
        self.eq.set_preamp(-level - 15)
        self.player.set_equalizer(self.eq)
        self.player.audio_set_volume(100)
        self.player.set_media(vlc.Media(file.__str__()))
        self.player.play()

    def stop(self):
        self.player.stop()
