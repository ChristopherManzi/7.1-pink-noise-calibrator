# 7.1 Pink Noise Calibrator

A minimal GUI tool for calibrating 7.1 surround speaker levels using pink noise. It
plays pink noise through one speaker at a time so you can measure each channel
individually with an SPL meter and adjust your EQ accordingly.

## What it does

- **One channel at a time** — clicking a playing channel stops it, so nothing overlaps
- **Adjustable output level** — a slider from -40 to 0 dBFS, default -20 dBFS
- **Standard routing** — channels follow the Windows 7.1 order: FL, FR, C, LFE, BL,
  BR, SL, SR

## Requirements

| | |
|---|---|
| OS | Windows with a configured 7.1 audio device |
| Runtime | Python 3.8 or newer |
| Dependencies | `numpy`, `sounddevice` |

```bash
pip install numpy sounddevice
```

## Usage

1. Set your system volume to your usual listening level.
2. Click a channel button to play pink noise through that speaker.
3. Hold your SPL meter at your listening position (C-weighting).
4. Note the reading, then move to the next channel.
5. Use the **Output Level** slider to adjust the signal level; raise it if your
   speakers are hard to measure.

### Channel layout

| Button | Speaker |
|--------|---------|
| Front L / Front R | Front left / right |
| Center | Center |
| Sub | Subwoofer (LFE) |
| Rear L / Rear R | Rear surround |
| Side L / Side R | Side surround |

Output is normalized peak audio scaled by the dBFS slider value.

## License

Copyright © Christopher Manzi 2026. All rights reserved.
