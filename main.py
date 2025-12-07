import tkinter as tk
from gui import ECGInterface
from BPMReader import BPMReader
from utils import SimulatedECGDevice

SERIAL_PORT = "COM10"
BAUDRATE = 9600

def main():
    root = tk.Tk()

    bpm_reader = BPMReader(port=SERIAL_PORT, baudrate=BAUDRATE)

    if bpm_reader.serial_device is None:
        simulated_device = SimulatedECGDevice(heart_rate_bpm=70)
        bpm_reader.serial_device = simulated_device
    
    app = ECGInterface(root, bpm_reader)

    def close_func():
        bpm_reader.close_serial_device()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", close_func)
    root.mainloop()

if __name__ == "__main__":
    main()