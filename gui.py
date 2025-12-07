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
        self.is_reading = False

        self.root.title("Monitor EKG")
        self.root.geometry("800x600")

        self.create_widgets()
        self.setup_plot()

        self.anim = animation.FuncAnimation(
            self.fig, self.update_plot, interval=1000./24., cache_frame_data=False
        )

    def create_widgets(self) -> None:
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(side='top', fill='x')

        bpm_frame = ttk.Frame(control_frame)
        bpm_frame.pack(side='left', padx=20)
        
        self.bpm_label_fft = ttk.Label(bpm_frame, text="BPM (FFT): --", font=("Courier New", 16, "bold"))
        self.bpm_label_fft.pack(side='top', anchor='w')
        
        self.bpm_label_peaks = ttk.Label(bpm_frame, text="BPM (Peaks): --", font=("Courier New", 16, "bold"))
        self.bpm_label_peaks.pack(side='top', anchor='w')

        self.btn_text = tk.StringVar(value="START")
        self.toggle_btn = ttk.Button(control_frame, textvariable=self.btn_text, command=self.toggle_reading)
        self.toggle_btn.pack(side='right', padx=20)

    def setup_plot(self) -> None:
        self.fig, self.axes = plt.subplots(nrows=2, figsize=(5, 4), dpi=100)
        self.fig.subplots_adjust(hspace=0.4)
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
            norm=plt.matplotlib.colors.LogNorm(vmin=1, vmax=100)
        )
        self.fig.colorbar(self.spectrogram, ax=self.axes[1])
        self.axes[1].set_title("Spektrogram")
        self.axes[1].set_xlabel("Czas [s]")
        self.axes[1].set_ylabel("Częstotliwość [Hz]")
        self.axes[1].set_yscale('log')
        self.axes[1].set_autoscale_on(False)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

    def toggle_reading(self) -> None:
        if not self.is_reading:
            self.is_reading = True
            self.btn_text.set("STOP")
            if hasattr(self.bpm_reader.serial_device, 'write'):
                self.bpm_reader.serial_device.write('1')
            else:
                self.bpm_reader.send_arduino_command('1')
        else:
            self.is_reading = False
            self.btn_text.set("START")
            if hasattr(self.bpm_reader.serial_device, 'write'):
                self.bpm_reader.serial_device.write('0')
            else:
                self.bpm_reader.send_arduino_command('0')

    def update_plot(self, frame) -> tuple[Line2D]:
        try:
            if self.is_reading:
                self.bpm_reader.read_data_sample()
            
            if not self.bpm_reader.time_s:
                return self.line_raw, self.spectrogram

            current_time = self.bpm_reader.time_s[-1]
            time_window = 10.0  # seconds
            start_time = max(0, current_time - time_window)
            
            times = self.bpm_reader.time_s
            start_idx = 0
            if times[0] < start_time:
                left, right = 0, len(times) - 1
                while left < right:
                    mid = (left + right) // 2
                    if times[mid] < start_time:
                        left = mid + 1
                    else:
                        right = mid
                start_idx = left
            
            display_time = self.bpm_reader.time_s[start_idx:]
            display_data = self.bpm_reader.ecg_data[start_idx:]
            
            self.line_raw.set_xdata(display_time)
            self.line_raw.set_ydata(display_data)

            self.axes[0].set_xlim(start_time, current_time + 0.1)

            if len(display_data) > 0:
                ymin, ymax = min(display_data), max(display_data)
                margin = (ymax - ymin) * 0.1 if ymax != ymin else 1.0
                self.axes[0].set_ylim(ymin - margin, ymax + margin)

            bpm_fft, bpm_peaks = self.bpm_reader.calculate_bpm()
            if bpm_fft is not None and bpm_peaks is not None:
                self.bpm_label_fft.configure(text=f"BPM (FFT): {int(bpm_fft)}")
                self.bpm_label_peaks.configure(text=f"BPM (Peaks): {int(bpm_peaks)}")

            if len(self.bpm_reader.bpm_fft_tuples_tab) > 0:
                for i, bpm_fft_tuples in enumerate(self.bpm_reader.bpm_fft_tuples_tab):
                    self.bpm_fft_amplitudes[:, i] = [fft_tuple[0] for fft_tuple in bpm_fft_tuples]
                self.spectrogram.set_data(self.bpm_fft_amplitudes)
                amp_min = max(self.bpm_fft_amplitudes.min(), 1)
                amp_max = max(self.bpm_fft_amplitudes.max(), amp_min + 1)
                self.spectrogram.set_norm(plt.matplotlib.colors.LogNorm(vmin=amp_min, vmax=amp_max))
                frequencies = [fft_tuple[1] for fft_tuple in self.bpm_reader.bpm_fft_tuples_tab[0]]
                extent = [self.bpm_reader.bpm_fft_calculation_time_s[0], self.bpm_reader.bpm_fft_calculation_time_s[-1] + 0.1, frequencies[0], frequencies[-1]]
                self.spectrogram.set_extent(extent)
                self.axes[1].set_xlim(extent[0], extent[1])
                self.axes[1].set_ylim(extent[2], extent[3])

        except Exception as e:
            print(f"Plot error: {e}")
            raise
        return self.line_raw, self.spectrogram