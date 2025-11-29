import math
import random

def periodic_function(time_s, dominant_signal_parameters=None, noise_signal_parameters=None,
                      normal_noise_parameters=None, y_shift=370) -> float:
    if dominant_signal_parameters is None:
        dominant_signal_parameters = {
            "amplitude": 50.0,
            "frequency_hz": 1.25,
            "phase_rad": 0.5,
        }
    if noise_signal_parameters is None:
        noise_signal_parameters = {
            "amplitude": 1,
            "frequency_hz": 20.0,
            "phase_rad": 0.0,
        }
    if normal_noise_parameters is None:
        normal_noise_parameters = {
            "mean": 0.0,
            "std": 2,
        }
    dsp = dominant_signal_parameters
    nsp = noise_signal_parameters
    nnp = normal_noise_parameters
    dominant_signal = dsp["amplitude"] * math.sin(2 * math.pi * dsp["frequency_hz"] * time_s + dsp["phase_rad"])
    noise_signal = nsp["amplitude"] * math.sin(2 * math.pi * nsp["frequency_hz"] * time_s + nsp["phase_rad"])
    normal_noise = random.gauss(nnp["mean"], nnp["std"])
    return dominant_signal + noise_signal + normal_noise + y_shift