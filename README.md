# 7.1 Pink Noise Calibrator

A minimal GUI tool for calibrating 7.1 surround speaker levels using pink noise.

![Python](https://img.shields.io/badge/python-3.8+-blue) ![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)

## What it does

Plays pink noise through one speaker at a time so you can measure each channel individually with an SPL meter and adjust your EQ accordingly.

## Usage

1. Set your system volume to your usual listening level
2. Click a channel button to play pink noise through that speaker
3. Hold your SPL meter at your listening position (C-weighting)
4. Note the reading, then move to the next channel
5. Use the **Output Level** slider to adjust the signal level (-40 to 0 dBFS)

## Channel layout

| Button | Speaker |
|--------|---------|
| Front L / Front R | Front left / right |
| Center | Center |
| Sub | Subwoofer (LFE) |
| Rear L / Rear R | Rear surround |
| Side L / Side R | Side surround |

## Requirements

```
pip install numpy sounddevice
```

Python 3.8+ and Windows with a 7.1 audio device configured.

## Notes

- Output is normalized peak audio scaled by the dBFS slider value
- Default is -20 dBFS. Raise it if your speakers are hard to measure
- Only one channel plays at a time; clicking a playing channel stops it
- Channel routing follows the Windows 7.1 standard: FL, FR, C, LFE, BL, BR, SL, SR
