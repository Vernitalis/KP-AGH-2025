import serial
import time
import numpy as np
import statistics
import math

class BPMReader:
    def __init__(self, port, baudrate=9600, sampling_delay_ms = 4, max_data_length = 1500, max_bpm_tab_length = 6,
                 bpm_calculation_delay_s = 0.25, data_proportion_for_bmp_calculation = 0.5):
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
        self.first_reading_time = None
        self.time_s = []
        self.ecg_data = []
        self.max_bpm_tab_length = max_bpm_tab_length
        self.bpm_calculation_delay_s = bpm_calculation_delay_s
        self.data_proportion_for_bmp_calculation = data_proportion_for_bmp_calculation
        self.last_bpm_calculation_s = 0
        self.bpm_data_fft = []
        self.bpm_data_peaks = []
        self.bpm_fft_tuples_tab = []
        self.bpm_fft_tuples_max_length = math.floor((self.max_data_length / (1000 / self.sampling_delay_ms)) / self.bpm_calculation_delay_s) + 1
        self.bpm_fft_calculation_time_s = []
        self.is_reading = False

    def send_arduino_command(self, command) -> None:
        if self.serial_device is not None:
            try:
                self.serial_device.write(command.encode('utf-8'))
                print(f"Sent command: {command}")
            except Exception as e:
                print(f"Error sending command: {e}")

    def read_data_sample(self) -> None:
        if not self.is_reading:
            return
        current_time = time.time()
        if self.first_reading_time is None:
            self.first_reading_time = current_time

        if self.serial_device is not None:
            ecg_sample_str = self.serial_device.readline().decode('utf-8').strip()
            if ecg_sample_str != "":
                ecg_sample = float(ecg_sample_str)
            else:
                return
        elif self.signal_function is not None:
            ecg_sample = self.signal_function(current_time - self.first_reading_time)
            time.sleep(self.sampling_delay_ms / 1000.)
        else:
            raise AttributeError("Can't read data sample if neither serial device nor signal function attribute is provided")
        self.time_s.append(current_time - self.first_reading_time)
        self.ecg_data.append(ecg_sample)
        if len(self.time_s) > self.max_data_length:
            self.time_s.pop(0)
            self.ecg_data.pop(0)

    def calculate_bpm(self): # -> None|float:
        if len(self.ecg_data) / self.max_data_length < self.data_proportion_for_bmp_calculation:
            return None, None
        if self.time_s[-1] - self.last_bpm_calculation_s > self.bpm_calculation_delay_s:
            ecg_data = np.array(self.ecg_data[-int(self.max_data_length * self.data_proportion_for_bmp_calculation):])
            fft_magnitudes = np.abs(np.fft.rfft(ecg_data))[1:]
            fft_frequencies_hz = np.fft.rfftfreq(len(ecg_data), d=(self.time_s[-1] - self.time_s[-len(ecg_data)]) / len(ecg_data))[1:]
            peak_frequency_hz = fft_frequencies_hz[np.argmax(fft_magnitudes)]
            fft_tuples = list(zip(fft_magnitudes, fft_frequencies_hz))
            self.bpm_fft_tuples_tab.append(fft_tuples)
            self.bpm_fft_calculation_time_s.append(time.time() - self.first_reading_time)
            self.bpm_data_fft.append(peak_frequency_hz * 60)
            mean_ecg = statistics.fmean(self.ecg_data)
            std_ecg = statistics.stdev(self.ecg_data)
            std_3_ecg = 3 * std_ecg
            filtered = list(filter(lambda data: abs(data - mean_ecg) > std_3_ecg, self.ecg_data))
            self.bpm_data_peaks.append(len(filtered) / (self.time_s[-1] - self.time_s[0]) * 60)
            self.last_bpm_calculation_s = self.time_s[-1]

        if len(self.bpm_data_fft) > self.max_bpm_tab_length:
            self.bpm_data_fft.pop(0)
            self.bpm_data_peaks.pop(0)
        if len(self.bpm_fft_tuples_tab) > self.bpm_fft_tuples_max_length:
            self.bpm_fft_tuples_tab.pop(0)
            self.bpm_fft_calculation_time_s.pop(0)
        return statistics.fmean(self.bpm_data_fft), statistics.fmean(self.bpm_data_peaks)

    def set_signal_function(self, signal_function) -> None:
        if self.serial_device is not None:
            raise AttributeError("Can't set signal function if serial device is already set")
        self.signal_function = signal_function

    def close_serial_device(self) -> None:
        if self.serial_device is not None:
            self.serial_device.close()