import serial
import time

class BPMReader:
    def __init__(self, port, baudrate=9600, sampling_delay_ms = 20, max_data_length = 300):
        try:
            self.serial_device = serial.Serial(port, baudrate, timeout=1)
            self.serial_device.flushInput()
            time.sleep(2)
        except serial.SerialException as e:
            print(f"Error opening serial port: {e}")
            print("Use set_signal_function to provide simulated signal instead")
            self.serial_device = None
            self.signal_function = None
        self.sampling_delay_ms = sampling_delay_ms
        self.max_data_length = max_data_length
        self.time_s = []
        self.ecg_data = []

    def read_data_sample(self):
        if self.serial_device is not None:
            ecg_sample_str = self.serial_device.readline().decode('utf-8').strip()
            if ecg_sample_str != "":
                ecg_sample = float(ecg_sample_str)
            else:
                ecg_sample = None
        elif self.signal_function is not None:
            ecg_sample = self.signal_function(self.time_s[-1] if len(self.time_s) > 0 else self.sampling_delay_ms / 1000.)
        else:
            raise AttributeError("Can't read data sample if neither serial device nor signal function attribute is provided")
        if len(self.time_s) != 0:
            self.time_s.append(self.time_s[-1] + self.sampling_delay_ms / 1000.)
        else:
            self.time_s.append(0.)
        self.ecg_data.append(ecg_sample)
        if len(self.time_s) > self.max_data_length:
            self.time_s.pop(0)
            self.ecg_data.pop(0)

    def set_signal_function(self, signal_function):
        if self.serial_device is not None:
            raise AttributeError("Can't set signal function if serial device is already set")
        self.signal_function = signal_function