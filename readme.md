# Sip 'n Puff Jukebox

Executive summary:
- Take a Raspberry Pi
- Put a BMP280 into a box and add a connector for a hose
- Have the RPi play random music from a thumbdrive when you blow into the hose, have it stop when you suck

Parts possibly interesting for reuse are the code for reading from the BMP280 and the code for turning pressure readings into input events.


## BOM

- Raspberry Pi 4
- Power supply for the Pi
- SD card for the Pi
- Housing for the Pi (optional)
- Some BMP280 module
- Wires for connecting the BMP to the GPIO Pins
- Case for the BMP280
- Hose connector for the case
- Hose

- Housing for the Pi (optional)


##  Project context and requirements

<sob-story> A friend of mine had his back surgery go wrong and currently has basically no control of any of his limbs. Due to the current pandemic, there's also no visits possible. So he's staring at a hospital ceiling the entire day and has absolutely nothing to do. </sob-story>
So I decided to build him a sip and puff jukebox, so he can at least listen to music and decide, within limits, what he wants to hear without relying on outside help.

This gives a bit of context for the requirements.
- The resulting device has to be simple enough to operate to explain it within 20 seconds to a nurse.
- The resulting device should have no user interface between a hose you blow into or suck from.
- It has to be tolerant against hard power off. This means neither getting problems itself nor corrupting attached storage with music.
- It has to have a volume auto-leveling feature, since the user cannot change the volume itself.
- The parts the user interacts with have to be disinfectable.


## Overview

One distinct component is the abstraction over the BMP280.
There's a number of existing libraries for interfacing with that chip on a Pi already, but few that use SPI.
Initial planning foresaw two sensors in a differential setup, which would have required at least one connected via SPI, so the code here has the actual bus connection abstracted away from everything else.
This turned out to not be a good idea, though, since the drift between two sensors turned out to be unsatisfylingly high.

The second distinct component is the input generation from pressure values.
It includes a filter for estimating current ambient pressure.
This is necessary because the pressure itself can change due to e.g. weather phenomena or elevation changes.
Even short-term indoor use is problematic with a naive approach, since the differentials we want to observe are close to the sensor's accuracy (though way above its precision).
Apart from that it's a rather simple state machine.

The third component is the thumbdrive scanner.
It relies on known mount points for the thumbdrives.
The whole design assumes read only mounts, since that allows for adding or removing drives at any time.
The files on the drives also get their loudness calculated while being scanned to suppress volume jumps between songs.
There is also support for reading the gain levels from a specifically named json file on the root of the drive.
This mechanism works by hashes instead of file names to support renaming of contents on the stick and specifically exclude the possibility of any reasobale change made by a random user to the thumb drive leading to too high a volume level being output.

This all gets strung together in the main.py.
The results of the scanner are saved in some in-memory data structure and based on sipping or puffing VLC is instructed to either stop or play a random piece of music.


## Remarks

The software part is basically a 2-day hackjob and the last time I had touched Python before this was when 2.7 was current.
Caution is advised.
