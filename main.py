import tkinter as tk
from gui import ECGInterface
from BPMReader import BPMReader
from utils import periodic_function
import threading

SERIAL_PORT = "COM10"
BAUDRATE = 9600

def main():
    root = tk.Tk()

    bpm_reader = BPMReader(port=SERIAL_PORT, baudrate=BAUDRATE)
    bpm_reader.set_signal_function(periodic_function)
    keep_reading = True
    def bpm_keep_reading():
        while keep_reading:
            bpm_reader.read_data_sample()
    bpm_reading_thread = threading.Thread(target=bpm_keep_reading)
    app = ECGInterface(root, bpm_reader)

    def close_func():
        bpm_reader.close_serial_device()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", close_func)
    bpm_reading_thread.start()
    root.mainloop()
    keep_reading = False
    bpm_reading_thread.join()

if __name__ == "__main__":
    main()