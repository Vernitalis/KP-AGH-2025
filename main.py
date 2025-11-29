import tkinter as tk
from gui import ECGInterface
from BPMReader import BPMReader
from utils import periodic_function

SERIAL_PORT = "COM10"
BAUDRATE = 9600

def main():
    root = tk.Tk()

    bpm_reader = BPMReader(port=SERIAL_PORT, baudrate=BAUDRATE)
    bpm_reader.set_signal_function(periodic_function)

    app = ECGInterface(root, bpm_reader)

    def close_func():
        bpm_reader.close_serial_device()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", close_func)
    root.mainloop()

if __name__ == "__main__":
    main()