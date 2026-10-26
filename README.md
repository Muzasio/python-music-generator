# Python Music Generator

Royalty-free background music for videos, made from scratch in Python with only **numpy** and **scipy**. No samples, no sound libraries, no external programs.

```
 notes + rhythm ──► instruments (bass, piano, drone, noise) ──► mix ──► master bus ──► WAV
                      sine waves, filters, envelopes                   filters + soft limiter   16-bit stereo 44.1 kHz
```

## Quick start

```sh
pip install numpy scipy
python3 demo_loop.py
```

Expected output:

```
written: demo_loop.wav (10.667 s, 470400 samples)
seam max jump 0.000542, average jump 0.001073 (seam below average = no click)
```

Tested on CachyOS with Python 3.14.8, numpy 2.5.4, scipy 1.18.1.

## Rules of the project

- Python with `numpy` and `scipy` only.
- Output: WAV, 16-bit, stereo, 44100 Hz, ready for a video editor.
- Loops must repeat with no click.

## Building blocks

All of these are in [`demo_loop.py`](demo_loop.py).

| Block | What it does |
|---|---|
| `lpf`, `bpf` | Low-pass and band-pass filters (Butterworth, `sosfilt`) |
| `bass_hit` | One bass note: sub octave + filtered saw wave + short noise punch. `decay` 2.0 = long, 4.5 = tight; `brightness` 3.0 = dark, 5.0 = bright |
| `filt_warm` | Filters a loop without a click (see below) |
| `master` | Final step: cut highs above 14 kHz, remove rumble below 25 Hz, soft limiter (`tanh`) |
| `freq_lock` | Moves a frequency so a whole number of cycles fits the loop |
| `save` | Writes stereo by delaying the right channel 7 ms (wrapped, so the loop stays seamless) |

A muted piano note is a sine at the note plus 3 quieter overtones (2×, 3×, 4×), a fast attack, an exponential fade and a low-pass filter at about 3500 Hz. Lower cutoffs (1800 Hz) sound too muffled.

## How seamless loops work

A loop clicks when the end does not match the start. Two things cause it:

```
 1. Oscillator out of phase          2. Filter start-up transient
    end ──╮      ╭── start               filter "wakes up" at sample 0,
          ╰─ jump ┘                      so the start differs from the end
    fix: freq_lock()                     fix: filt_warm()
```

1. **Phase:** a sine returns to the same value at the end only if its frequency fits a whole number of cycles in the loop. `freq_lock(freq, loop_seconds)` rounds it to the nearest one.
2. **Filters:** an IIR filter starts from zero, so its first samples differ from its steady state. `filt_warm` filters two copies back to back and keeps the second one.
3. **Noise** cannot be phase-locked. Fade it to zero before each beat ends (a gate), so it is silent at the loop point.
4. **Several loops in one file:** join them first, then run the master bus once over the whole signal.

### What did not work

| Attempt | Result | Why |
|---|---|---|
| Crossfading the end into the start | Click stayed (jump 0.63 to 0.85) | A crossfade blends two values that are far apart; it cannot remove the jump |
| Master bus on each loop separately | Click at the join (0.63) | Filter state and `tanh` limiting differ at the end of one part and the start of the next |
| Phase-locking alone | Click from the drone (0.97) | The filter transient was still there; `filt_warm` brought it down to 0.00124 |

**How to measure the seam:** compare the biggest jump around the loop point with the average jump of the whole signal (see `seam_jump` in the demo). Comparing only the last and first sample can give false alarms.

## Music used

- Chord progression: **C major → A minor → F major → G major** (bass roots C2, A1, F1, G1).
- Tension: a low E (41.2 Hz) with a tritone B♭ (58.3 Hz) above it.

## Track types made so far

| Section | Variants | Length | Feel |
|---|---|---|---|
| Intro | 3 | 15 s | cold open, pulse build, drop entry |
| Suspense | 3 | 15 s | dread, creeping, tension hold |
| Explanation | 5 | 20 s | focused flow, technical, deep dive, sharp, ambient groove |
| Bass loop | 1 | 42.7 s | bass only, then bass + piano, seamless |

The tracks themselves are not in this repo yet.

## Not done yet

- "Failed" section tracks (dissonant drop, glitch, slow descent).
- Sound effects: whoosh, impact, glitch, tension sting.
- Better sound with the same two libraries: FM synthesis, wavetables, convolution reverb, granular pads.
- Wider stereo (mid-side, panning per instrument).
- Loop markers inside the WAV file (`scipy` cannot write them).
