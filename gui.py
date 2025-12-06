import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
from matplotlib.lines import Line2D
import numpy as np


class ECGInterface:
    def __init__(self, root, bpm_reader):
        self.root = root
        self.bpm_reader = bpm_reader

        self.root.title("Monitor EKG")
        self.root.geometry("800x600")

        self.create_widgets()
        self.setup_plot()

        self.anim = animation.FuncAnimation(
            self.fig, self.update_plot, interval=1000./30., cache_frame_data=False
        )

    def create_widgets(self) -> None:
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(side='top', fill='x')

        self.bpm_label = ttk.Label(control_frame, text="BPM: --", font=("Courier New", 24, "bold"))
        self.bpm_label.pack(side='left', padx=20)

        self.btn_text = tk.StringVar(value="START")
        self.toggle_btn = ttk.Button(control_frame, textvariable=self.btn_text, command=self.toggle_reading)
        self.toggle_btn.pack(side='right', padx=20)

    def setup_plot(self) -> None:
        self.fig, self.axes = plt.subplots(nrows=2, figsize=(5, 4), dpi=100)
        self.line_raw, = self.axes[0].plot([], [], 'g-', linewidth=1.5)

        self.axes[0].set_title("Sygnał EKG (Arduino)")
        self.axes[0].set_xlabel("Czas [s]")
        self.axes[0].set_ylabel("Amplituda")
        self.axes[0].grid(True, linestyle='--', alpha=0.5)

        fft_length = self.bpm_reader.max_data_length * self.bpm_reader.data_proportion_for_bmp_calculation
        fft_length = fft_length / 2 + 1 if fft_length % 2 == 0 else (fft_length + 1) / 2
        fft_length -= 1
        self.bpm_fft_amplitudes = np.zeros((int(fft_length), self.bpm_reader.bpm_fft_tuples_max_length))
        self.spectrogram = self.axes[1].imshow(
            self.bpm_fft_amplitudes,
            cmap='viridis',
            origin='lower',
            aspect='auto',
            interpolation='lanczos',
        )
        self.fig.colorbar(self.spectrogram, ax=self.axes[1])
        self.axes[1].set_title("Spektrogram")
        self.axes[1].set_xlabel("Czas [s]")
        self.axes[1].set_ylabel("Częstotliwość")
        self.axes[1].grid(True, linestyle='--', alpha=0.5)
        self.axes[1].set_autoscale_on(False)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

    def toggle_reading(self) -> None:
        if not self.bpm_reader.is_reading:
            self.bpm_reader.is_reading = True
            self.btn_text.set("STOP")
            self.bpm_reader.send_arduino_command('1')
        else:
            self.bpm_reader.is_reading = False
            self.btn_text.set("START")
            self.bpm_reader.send_arduino_command('0')

    def update_plot(self, frame) -> tuple[Line2D]:
        try:
            if not self.bpm_reader.time_s:
                return self.line_raw,

            self.line_raw.set_xdata(self.bpm_reader.time_s)
            self.line_raw.set_ydata(self.bpm_reader.ecg_data)

            self.axes[0].set_xlim(self.bpm_reader.time_s[0], self.bpm_reader.time_s[-1] + 0.1)

            y_data = self.bpm_reader.ecg_data
            if y_data:
                ymin, ymax = min(y_data), max(y_data)
                margin = (ymax - ymin) * 0.1 if ymax != ymin else 1.0
                self.axes[0].set_ylim(ymin - margin, ymax + margin)

            bpm_fft, bpm_peaks = self.bpm_reader.calculate_bpm()
            if bpm_fft is not None:
                self.bpm_label.configure(text=f"BPM (FFT): {int(bpm_fft)}")
            # if bpm_peaks is not None:
            #     self.bpm_label.configure(text=f"BPM: {int(bpm_peaks)}")
            if len(self.bpm_reader.bpm_fft_tuples_tab) != 0:
                for i, bpm_fft_tuples in enumerate(self.bpm_reader.bpm_fft_tuples_tab):
                    self.bpm_fft_amplitudes[:, i] = [fft_tuple[0] for fft_tuple in bpm_fft_tuples]
                self.spectrogram.set_data(self.bpm_fft_amplitudes)
                self.spectrogram.set_clim(vmin=self.bpm_fft_amplitudes.min(),
                                          vmax=self.bpm_fft_amplitudes.max())
                frequencies = [fft_tuple[1] for fft_tuple in self.bpm_reader.bpm_fft_tuples_tab[0]]
                extent = [self.bpm_reader.bpm_fft_calculation_time_s[0], self.bpm_reader.bpm_fft_calculation_time_s[-1] + 0.1, frequencies[0], frequencies[-1]]
                self.spectrogram.set_extent(extent)
                self.axes[1].set_xlim(extent[0], extent[1])
                self.axes[1].set_ylim(extent[2], extent[3])

        except Exception as e:
            print(f"Plot error: {e}")
            raise
        return self.line_raw, self.spectrogram