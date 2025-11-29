import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
from matplotlib.lines import Line2D


class ECGInterface:
    def __init__(self, root, bpm_reader):
        self.root = root
        self.bpm_reader = bpm_reader

        self.root.title("Monitor EKG")
        self.root.geometry("800x600")

        self.create_widgets()
        self.setup_plot()

        self.anim = animation.FuncAnimation(
            self.fig, self.update_plot, interval=20, cache_frame_data=False
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
        self.fig, self.ax = plt.subplots(figsize=(5, 4), dpi=100)
        self.line_raw, = self.ax.plot([], [], 'g-', linewidth=1.5)

        self.ax.set_title("Sygnał EKG (Arduino)")
        self.ax.set_xlabel("Czas [s]")
        self.ax.set_ylabel("Amplituda")
        self.ax.grid(True, linestyle='--', alpha=0.5)

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
            self.bpm_reader.read_data_sample()

            if not self.bpm_reader.time_s:
                return self.line_raw,

            self.line_raw.set_xdata(self.bpm_reader.time_s)
            self.line_raw.set_ydata(self.bpm_reader.ecg_data)

            self.ax.set_xlim(self.bpm_reader.time_s[0], self.bpm_reader.time_s[-1] + 0.1)

            y_data = self.bpm_reader.ecg_data
            if y_data:
                ymin, ymax = min(y_data), max(y_data)
                margin = (ymax - ymin) * 0.1 if ymax != ymin else 1.0
                self.ax.set_ylim(ymin - margin, ymax + margin)

            bpm = self.bpm_reader.calculate_bpm()
            if bpm is not None:
                self.bpm_label.configure(text=f"BPM: {int(bpm)}")
        except Exception as e:
            print(f"Plot error: {e}")

        return self.line_raw,