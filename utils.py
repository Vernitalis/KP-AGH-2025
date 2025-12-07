import math
import random
import time


class SimulatedECGDevice:
    def __init__(self, heart_rate_bpm=70, y_shift=512):
        self.should_read = False
        self.heart_rate_bpm = heart_rate_bpm
        self.y_shift = y_shift
        self.start_time = None
        
    def read_message(self) -> str | None:
        if not self.should_read:
            return None
        
        if self.start_time is None:
            self.start_time = time.time()
        
        current_time = time.time() - self.start_time
        ecg_value = self._generate_ecg_signal(current_time)
        
        return str(int(ecg_value))
    
    def write(self, message: str) -> None:
        if isinstance(message, bytes):
            message = message.decode('utf-8')
        message = message.strip()
        if message == '1':
            self.should_read = True
            self.start_time = time.time()
        elif message == '0':
            self.should_read = False
    
    def close(self) -> None:
        pass
    
    def _generate_ecg_signal(self, time_s: float) -> float:
        heart_rate_hz = self.heart_rate_bpm / 60.0
        cardiac_cycle_s = 1.0 / heart_rate_hz

        phase = (time_s % cardiac_cycle_s) / cardiac_cycle_s

        p_wave = self._generate_p_wave(phase)
        qrs_complex = self._generate_qrs_complex(phase)
        t_wave = self._generate_t_wave(phase)

        ecg_signal = p_wave + qrs_complex + t_wave
        
        return ecg_signal + self.y_shift
    
    @staticmethod
    def _generate_p_wave(phase: float) -> float:
        p_start = 0.10
        p_duration = 0.09
        p_end = p_start + p_duration
        
        if p_start <= phase < p_end:
            p_phase = (phase - p_start) / p_duration
            amplitude = 8 * math.sin(math.pi * p_phase) ** 1.5
            return amplitude
        return 0
    
    @staticmethod
    def _generate_qrs_complex(phase: float) -> float:
        q_start = 0.30
        q_end = 0.32
        r_start = 0.32
        r_end = 0.36
        s_start = 0.36
        s_end = 0.38
        
        if q_start <= phase < q_end:
            q_phase = (phase - q_start) / (q_end - q_start)
            return -20 * math.sin(math.pi * q_phase)
        
        if r_start <= phase < r_end:
            r_phase = (phase - r_start) / (r_end - r_start)
            return 150 * math.sin(math.pi * r_phase) ** 0.6
        
        if s_start <= phase < s_end:
            s_phase = (phase - s_start) / (s_end - s_start)
            return -30 * math.sin(math.pi * s_phase)
        
        return 0
    
    @staticmethod
    def _generate_t_wave(phase: float) -> float:
        t_start = 0.55
        t_duration = 0.20
        t_end = t_start + t_duration
        
        if t_start <= phase < t_end:
            t_phase = (phase - t_start) / t_duration
            if t_phase < 0.5:
                amplitude = 30 * math.sin(math.pi * t_phase * 2) ** 1.3
            else:
                amplitude = 30 * math.sin(math.pi * (1 - (t_phase - 0.5) * 2)) ** 1.1
            return amplitude
        return 0