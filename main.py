import matplotlib.pyplot as plt
import matplotlib.animation as animation
from BPMReader import BPMReader
from utils import periodic_function

fig, ax = plt.subplots()
line_raw, = ax.plot([], [], 'b-')
plt.xlabel('Time [s]')
plt.ylabel('ECG Value')
plt.title('ECG readings')

BPM_reader = BPMReader("...")
BPM_reader.set_signal_function(periodic_function)

def update_plot(frame, min_max_delta = 1):
    try:
        BPM_reader.read_data_sample()
        line_raw.set_xdata(BPM_reader.time_s)
        line_raw.set_ydata(BPM_reader.ecg_data)
        ax.set_xlim(BPM_reader.time_s[0], BPM_reader.time_s[-1])
        ax.set_ylim(min(BPM_reader.ecg_data) - min_max_delta, max(BPM_reader.ecg_data) + min_max_delta)
        ax.relim()
        ax.autoscale_view(True, True, True)
        bpm = BPM_reader.calculate_bpm()
        if bpm is not None:
            print(f"BPM: {bpm}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return line_raw, ax

ani = animation.FuncAnimation(fig, update_plot, interval=1, blit=False, cache_frame_data=True)
plt.show()
print("Plot window closed. Closing serial port.")
BPM_reader.close_serial_device()
