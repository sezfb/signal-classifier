import numpy as np
from gnuradio import gr, blocks, analog, digital


def generate_fm_analog_signal(
    samp_rate=48000,       # samples per second
    duration_s=0.25,       # signal duration in seconds
    audio_tone_hz=1000,    # modulating signal frequency (audio tone)
    freq_dev_hz=5000,      # frequency deviation (Hz) for FM modulation
    gain=1.0               # checks detected / not detected
):
    """
    Create an FM-modulated audio tone:

    1. Define the function and its input parameters.
    2. Generate modulating signal (audio tone).
    3. Apply FM modulation to produce a complex IQ signal.
    4. Apply processing (amplitude scaling, sample limiting).
    5. Execute flowgraph and collect samples.
    6. Convert to NumPy array for further analysis.
    """
    tb = gr.top_block()
    n_samp = int(samp_rate * duration_s)  # total samples

    # generate modulating signal (audio sine wave)
    audio_tone = analog.sig_source_f(
        samp_rate,
        analog.GR_SIN_WAVE,
        audio_tone_hz,
        0.8
    )

    # convert frequency deviation (Hz) to phase increment per sample
    sensitivity = 2.0 * np.pi * freq_dev_hz / samp_rate

    # apply FM modulation to input audio_tone
    fm_mod = analog.frequency_modulator_fc(sensitivity)

    amp = blocks.multiply_const_cc(gain)                # scale signal amplitude
    head = blocks.head(gr.sizeof_gr_complex, n_samp)    # limit number of samples
    sink = blocks.vector_sink_c()                       # store output samples
    tb.connect(audio_tone, fm_mod, amp, head, sink)
    tb.run()

    return np.array(sink.data(), dtype=np.complex64)    # return IQ samples as NumPy array


def generate_bpsk_digital_signal(
    n_symbols=4000,     # BPSK symbols
    sps=8,              # samples per symbol
    gain=1.0,           # checks detected / not detected
    seed=12345          # to control randomness
):
    """
    The bit array is converted into a GNU Radio bit stream,
    then mapped into BPSK symbols (signal representation),
    and each symbol is repeated for sps samples to form
    a discrete-time waveform.

    * Without oversampling, each symbol would be represented
      by a single sample, which is unrealistic.
      Repeating each symbol creates a proper discrete-time waveform,
      making phase transitions meaningful and improving
      classification reliability.
    """
    # pseudo-random bit stream generator
    rng = np.random.default_rng(seed)
    bits = rng.integers(0, 2, size=n_symbols, dtype=np.uint8)

    tb = gr.top_block()

    # main digital signal path
    src_bits = blocks.vector_source_b(bits.tolist(), False)
    mapper = digital.chunks_to_symbols_bc([-1+0j, 1+0j])
    repeater = blocks.repeat(gr.sizeof_gr_complex, sps)

    # reuse the same processing as in the analog signal (see above)
    amp = blocks.multiply_const_cc(gain)
    head = blocks.head(gr.sizeof_gr_complex, n_symbols * sps)
    sink = blocks.vector_sink_c()
    tb.connect(src_bits, mapper, repeater, amp, head, sink)
    tb.run()

    return np.array(sink.data(), dtype=np.complex64)


# --------------    Signal analysis

def measure_power(samples):
    """
    Measure received signal power in relative units :
    - power is estimated as : P = mean(|x[n]|^2)
    - dBFS-like relative units: P_dB = 10 * log10(P)

    * Since there is no calibrated SDR front-end here,
      relative units are the correct choice instead of true dBm.
    """
    power_linear = float(np.mean(np.abs(samples) ** 2))
    power_db = 10.0 * np.log10(power_linear + 1e-15)
    return power_linear, power_db


def classify_signal(samples, phase_jump_threshold=0.02):
    """
    Signal crasifier ( analog/digital ) :
    - observable property used here : phase-jump behavior

    Rationale:
    - FM analog tone has relatively smooth phase evolution
    - BPSK has abrupt phase reversals (often near pi)

    Metric:
    - compute instantaneous phase difference:
          dphi[n] = angle(x[n] * conj(x[n-1]))
    - count how often |dphi| is large (> pi/2)
    * if large jumps happen often enough, classify as digital
    """
    if len(samples) < 2:
        return "unknown", 0.0

    dphi = np.angle(samples[1:] * np.conj(samples[:-1]))
    large_jump_ratio = float(np.mean(np.abs(dphi) > (np.pi / 2.0)))

    predicted_type = "digital" if large_jump_ratio > phase_jump_threshold else "analog"
    return predicted_type, large_jump_ratio


def analyze_signal(samples, label, power_threshold_db=-6.0):
    """
    Analyze signal :
    - measure signal power
    - apply detection threshold
    - classify as analog or digital
    - return structured result
    """
    power_linear, power_db = measure_power(samples)
    detected = power_db > power_threshold_db
    predicted_type, jump_ratio = classify_signal(samples)

    return {
        "label": label,
        "predicted_type": predicted_type,
        "power_linear": power_linear,
        "power_db": power_db,
        "detected": detected,
        "phase_jump_ratio": jump_ratio,
        "threshold_db": power_threshold_db,
    }


def print_result(result):
    print("-" * 65)
    print(f"Signal label            :  {result['label']}")
    print(f"Classified as           :  {result['predicted_type']}")
    print(f"Measured power (linear) :  {result['power_linear']:.6f}")
    print(f"Measured power (dBFS)   :  {result['power_db']:.2f} dB")
    print(f"Threshold               :  {result['threshold_db']:.2f} dB")
    print(f"Detection status        :  {'detected' if result['detected'] else 'not detected'}")
    print(f"Phase jump ratio        :  {result['phase_jump_ratio']:.4f}")
    print("-" * 65)
    print()


def main():

    # you have to modify gain and/or sps to simulate different signal scenarios
    # adjust this threshold to control detection outcomer

    power_threshold_db = -5.0
    
    # --------- Signal 1: Analog FM tone
    analog_samples = generate_fm_analog_signal(
        samp_rate=48000,
        duration_s=0.25,
        audio_tone_hz=1000,
        freq_dev_hz=5000,
        gain=0.1
    )
    analog_result = analyze_signal(
        analog_samples,
        label="Analog FM-modulated audio tone",
        power_threshold_db=power_threshold_db
    )

    # --------- Signal 2: Digital BPSK with pseudo-random bits
    digital_samples = generate_bpsk_digital_signal(
        n_symbols=4000,
        sps=8,
        gain=0.1,
        seed=12345
    )
    digital_result = analyze_signal(
        digital_samples,
        label="Digital BPSK pseudo-random bit stream",
        power_threshold_db=power_threshold_db
    )

    # --------- Logging / printing
    print_result(analog_result)
    print_result(digital_result)

if __name__ == "__main__":
    main()