#### Requirements
- [Python 3](https://wiki.python.org/moin/BeginnersGuide/Download)
- [GNU Radio 3.10+](https://wiki.gnuradio.org/index.php/InstallingGR)
- [NumPy](https://numpy.org/install/)  
> Make sure all dependencies are installed.

#### How to Run
Save the script as `program.py` (or any name you choose), then open a terminal in the script directory, then run:
```
python3 program.py
```
#### Code Structure
The script is organized into the following parts:

1. Analog signal generation
   Generates an FM-modulated audio tone and outputs complex IQ samples.
2. Digital signal generation 
   Generates a pseudo-random bit stream, maps it to BPSK symbols, and forms a sampled digital waveform.
3. Power measurement
   Computes average signal power in linear and logarithmic (dB) units.
4. Signal classification
   Classifies the signal as analog or digital based on phase-jump behavior.
5. Detection logic
   Compares signal power to a threshold to determine if the signal is detected.
6. Output
   Prints results in a readable format and provides a short summary.
* Detailed explanations and inline comments are provided directly in the code.

#### Classification Method
The classification method is based on phase-jump behavior.

- The analog FM signal has relatively smooth phase evolution
- The digital BPSK signal has abrupt phase reversals between symbols

The script computes the phase difference between neighboring IQ samples and measures how often large phase jumps occur.
If large phase jumps occur frequently, the signal is classified as digital.
Otherwise, it is classified as analog.

This method was chosen because it is simple, computationally efficient, and well matched to the difference between FM and BPSK signals.
It is not intended to be a perfect universal classifier, but it is reasonable and effective for this task.

> Tested on Linux (Debian) with GNU Radio 3.10+.