#!/usr/bin/env python3
"""Make a seamless 4-bar bass loop (90 BPM) with numpy and scipy only.

    python3 demo_loop.py [output.wav]      default: demo_loop.wav

Output: WAV, 16-bit, stereo, 44100 Hz. Prints the loop length and the seam check.
"""
import sys

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

SR = 44100
BPM = 90
LOOP = 4 * 4 * 60 / BPM          # 4 bars of 4 beats, in seconds
N = int(LOOP * SR)               # samples in one loop
STEP = int(60 / BPM / 4 * SR)    # one 16th note, in samples
ROOTS = [36, 33, 29, 31]         # C2, A1, F1, G1 (C - Am - F - G)


def lpf(sig, cutoff, order=4):
    return sosfilt(butter(order, cutoff / (SR / 2), btype="low", output="sos"), sig)


def bpf(sig, lo, hi, order=3):
    return sosfilt(butter(order, [lo / (SR / 2), hi / (SR / 2)], btype="band", output="sos"), sig)


def normalize(sig, peak=1.0):
    m = np.max(np.abs(sig))
    return sig / m * peak if m > 0 else sig


def filt_warm(sig, cutoff, btype="low", order=4):
    """Filter a loop without a click: run it twice through the filter, keep the second pass."""
    n = len(sig)
    sos = butter(order, cutoff / (SR / 2), btype=btype, output="sos")
    return sosfilt(sos, np.tile(sig, 2))[n:]


def master(sig):
    sig = filt_warm(sig, 14000)             # cut harsh highs
    sig = filt_warm(sig, 25, "high", 2)     # remove DC and ultra-low rumble
    return normalize(np.tanh(sig * 0.88), 0.92)   # soft limiter


def freq_lock(freq, loop_dur):
    """Nearest frequency that fits a whole number of cycles in the loop, so it starts and ends the same."""
    return round(freq * loop_dur) / loop_dur


def midi_freq(m):
    return 440.0 * (2.0 ** ((m - 69) / 12.0))


def bass_hit(freq, vel, dur_n, decay=3.0, brightness=3.5, harmonics=6):
    """One bass note: sub octave + filtered saw + a short noise punch, with a fast attack."""
    tt = np.arange(dur_n) / SR
    sub = np.sin(2 * np.pi * freq * 0.5 * tt) * 0.65
    saw = sum(np.sin(2 * np.pi * k * freq * tt) * (-1) ** (k + 1) / k
              for k in range(1, harmonics + 1)) * (2 / np.pi)
    saw = lpf(saw, freq * brightness) * 0.5
    rng = np.random.default_rng(int(freq) % 97)
    punch = bpf(rng.normal(0, 1, dur_n), 100, 700) * np.exp(-80 * tt) * 0.18
    atk = max(int(0.005 * SR), 1)
    env = np.zeros(dur_n)
    env[:atk] = np.linspace(0, 1, atk)
    env[atk:] = np.exp(-decay * tt[atk:] / (dur_n / SR))
    return (sub + saw + punch) * env * vel


def save(sig, path):
    """Stereo by delaying the right channel 7 ms (wrapped around, so the loop stays seamless)."""
    d = int(0.007 * SR)
    right = np.concatenate([sig[len(sig) - d:], sig[:len(sig) - d]])
    wavfile.write(path, SR, (np.stack([sig, right], axis=1) * 32767).astype(np.int16))


def seam_jump(mix):
    """Biggest sample-to-sample jump around the loop point (end -> start)."""
    join = np.concatenate([mix[-50:], mix[:50]])
    return float(np.max(np.abs(np.diff(join[47:53]))))


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "demo_loop.wav"
    t = np.arange(N) / SR
    drone = np.sin(2 * np.pi * freq_lock(midi_freq(36) / 2, LOOP) * t) * 0.3
    track = np.zeros(N)
    for bar, root in enumerate(ROOTS):
        for k in (0, 6, 10):                # hits on 16th steps 1, 7 and 11 of each bar
            s = (bar * 16 + k) * STEP
            track[s:s + 2 * STEP] += bass_hit(midi_freq(root), 0.9, 2 * STEP)
    mix = master(normalize(track) * 0.85 + drone)
    save(mix, out)
    print("written: %s (%.3f s, %d samples)" % (out, N / SR, N))
    print("seam max jump %.6f, average jump %.6f (seam below average = no click)"
          % (seam_jump(mix), float(np.mean(np.abs(np.diff(mix))))))


if __name__ == "__main__":
    main()
