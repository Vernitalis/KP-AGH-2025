import serial
import time

class BPMReader:
    def __init__(self, port, baudrate=9600, sampling_delay_ms = 20, max_data_length = 300):
        try:
            self.serialDevice = serial.Serial(port, baudrate, timeout=1)
            self.serialDevice.flushInput()
            time.sleep(2)
        except serial.SerialException as e:
            print(f"Error opening serial port: {e}")
        self.sampling_delay_ms = sampling_delay_ms
        self.max_data_length = max_data_length
        self.time_s = []
        self.ecg_data = []

    def read_data_sample(self):
        ecg_sample_str = self.serialDevice.readline().decode('utf-8').strip()
        if ecg_sample_str != "":
            ecg_sample = float(ecg_sample_str)
            if len(self.time_s) != 0:
                self.time_s.append(self.time_s[-1] + self.sampling_delay_ms / 1000.)
            else:
                self.time_s.append(0.)
            self.ecg_data.append(ecg_sample)
            if len(self.time_s) > self.max_data_length:
                self.time_s.pop(0)
                self.ecg_data.pop(0)
