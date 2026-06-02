import tkinter as tk
import numpy as np
import sounddevice as sd
import threading

SAMPLE_RATE = 48000
TOTAL_CHANNELS = 8
BUFFER_SECONDS = 3

# Windows 7.1 channel order: FL, FR, C, LFE, BL, BR, SL, SR
CHANNELS = [
    ("Front L",  0),
    ("Front R",  1),
    ("Center",   2),
    ("Sub",      3),
    ("Rear L",   4),
    ("Rear R",   5),
    ("Side L",   6),
    ("Side R",   7),
]

def generate_pink_noise(n_samples):
    white = np.random.randn(n_samples).astype(np.float64)
    pink = np.zeros(n_samples, dtype=np.float64)
    b0 = b1 = b2 = b3 = b4 = b5 = b6 = 0.0
    for i in range(n_samples):
        w = white[i]
        b0 = 0.99886 * b0 + w * 0.0555179
        b1 = 0.99332 * b1 + w * 0.0750759
        b2 = 0.96900 * b2 + w * 0.1538520
        b3 = 0.86650 * b3 + w * 0.3104856
        b4 = 0.55000 * b4 + w * 0.5329522
        b5 = -0.7616 * b5 - w * 0.0168980
        pink[i] = b0 + b1 + b2 + b3 + b4 + b5 + b6 + w * 0.5362
        b6 = w * 0.115926
    peak = np.max(np.abs(pink))
    if peak > 0:
        pink /= peak
    pink *= 1.0  # normalized to peak 1.0; amplitude applied at playback
    return pink.astype(np.float32)


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Level Calibration")
        self.root.resizable(False, False)
        self.root.configure(bg="#1e1e1e")

        self.noise = None
        self.stream = None
        self.pos = 0
        self.active = None
        self.lock = threading.Lock()
        self.buttons = {}
        self.volume_db = tk.DoubleVar(value=-20.0)

        self._build_ui()
        threading.Thread(target=self._load_noise, daemon=True).start()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        tk.Label(self.root, text="Level Calibration",
                 font=("Segoe UI", 13, "bold"),
                 bg="#1e1e1e", fg="white").pack(pady=(16, 2))

        tk.Label(self.root, text="Pink Noise · 7.1 Channel Selection",
                 font=("Segoe UI", 9), bg="#1e1e1e", fg="#777").pack(pady=(0, 14))

        self.status = tk.Label(self.root, text="Generating noise...",
                               font=("Segoe UI", 9, "italic"),
                               bg="#1e1e1e", fg="#f0a000")
        self.status.pack(pady=(0, 8))

        grid = tk.Frame(self.root, bg="#1e1e1e")
        grid.pack(padx=24, pady=4)

        for i, (name, ch) in enumerate(CHANNELS):
            row, col = divmod(i, 2)
            cell = tk.Frame(grid, bg="#1e1e1e")
            cell.grid(row=row, column=col, padx=8, pady=5, sticky="ew")

            btn = tk.Button(cell, text=f"▶  {name}", width=14,
                            font=("Segoe UI", 10),
                            bg="#2d2d2d", fg="#cccccc",
                            activebackground="#3a3a3a", activeforeground="white",
                            relief="flat", bd=0, cursor="hand2", state="disabled",
                            command=lambda n=name, c=ch: self._toggle(n, c))
            btn.pack(ipady=6)
            self.buttons[name] = btn

        tk.Frame(self.root, bg="#333", height=1).pack(fill="x", padx=20, pady=12)

        vol_frame = tk.Frame(self.root, bg="#1e1e1e")
        vol_frame.pack(padx=24, pady=(0, 8), fill="x")

        tk.Label(vol_frame, text="Output Level",
                 font=("Segoe UI", 9), bg="#1e1e1e", fg="#aaa").pack(side="left")

        self.vol_label = tk.Label(vol_frame, text="-20 dBFS",
                                   font=("Segoe UI", 9, "bold"),
                                   bg="#1e1e1e", fg="white", width=8)
        self.vol_label.pack(side="right")

        self.slider = tk.Scale(self.root, from_=-40, to=0,
                               resolution=1, orient="horizontal",
                               variable=self.volume_db,
                               command=self._on_volume_change,
                               bg="#1e1e1e", fg="#aaa",
                               troughcolor="#2d2d2d", activebackground="#4caf50",
                               highlightthickness=0, bd=0,
                               showvalue=False, length=240)
        self.slider.pack(padx=24, pady=(0, 12))

        tk.Button(self.root, text="■  Stop",
                  font=("Segoe UI", 10, "bold"), width=20,
                  bg="#7a1c1c", fg="white",
                  activebackground="#9e2525", activeforeground="white",
                  relief="flat", bd=0, cursor="hand2",
                  command=self._stop).pack(pady=(0, 16), ipady=6)

    def _on_volume_change(self, _=None):
        db = self.volume_db.get()
        self.vol_label.config(text=f"{int(db):+d} dBFS")

    def _get_amplitude(self):
        return 10 ** (self.volume_db.get() / 20.0)

    def _load_noise(self):
        n = BUFFER_SECONDS * SAMPLE_RATE
        buf = generate_pink_noise(n)
        with self.lock:
            self.noise = buf
        self.root.after(0, self._on_ready)

    def _on_ready(self):
        self.status.config(text="Ready", fg="#4caf50")
        for btn in self.buttons.values():
            btn.config(state="normal")

    def _toggle(self, name, ch_idx):
        if self.active == name:
            self._stop()
        else:
            self._stop()
            self._play(name, ch_idx)

    def _play(self, name, ch_idx):
        self.active = name
        self.pos = 0

        for n, btn in self.buttons.items():
            btn.config(bg="#2d2d2d", fg="#cccccc",
                       text=f"▶  {n}")
        self.buttons[name].config(bg="#1b5e20", fg="white",
                                  text=f"■  {name}")
        self.status.config(text=f"Playing: {name}", fg="#4caf50")

        noise = self.noise
        noise_len = len(noise)

        def callback(outdata, frames, time, status):
            out = np.zeros((frames, TOTAL_CHANNELS), dtype=np.float32)
            start = self.pos % noise_len
            end = start + frames
            if end <= noise_len:
                out[:, ch_idx] = noise[start:end]
            else:
                first = noise_len - start
                out[:first, ch_idx] = noise[start:]
                out[first:, ch_idx] = noise[:frames - first]
            out *= self._get_amplitude()
            self.pos += frames
            outdata[:] = out

        self.stream = sd.OutputStream(
            samplerate=SAMPLE_RATE,
            channels=TOTAL_CHANNELS,
            dtype="float32",
            callback=callback,
            blocksize=1024,
        )
        self.stream.start()

    def _stop(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        self.active = None
        for n, btn in self.buttons.items():
            btn.config(bg="#2d2d2d", fg="#cccccc", text=f"▶  {n}")
        if self.noise is not None:
            self.status.config(text="Ready", fg="#4caf50")

    def _on_close(self):
        self._stop()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
