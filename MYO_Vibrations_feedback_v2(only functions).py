import multiprocessing
import queue
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import animation
from matplotlib.cm import get_cmap

from pyomyo import Myo, emg_mode

print("Press ctrl+pause/break to stop")

# ------------ Myo Setup ---------------
q = multiprocessing.Queue()

def worker(q):
    # https://morioh.com/p/2cd313a4d9f2
    m = Myo(mode=emg_mode.PREPROCESSED)
    m.connect()

    def add_to_queue(emg, movement):
        q.put(emg)

    def print_battery(bat):
            print("Battery level:", bat)

    # RGB logo and bar LEDs
    m.set_leds([255, 255, 255], [255, 255, 255])
    # Vibrate to know we connected
    #m.vibrate(1)
    m.add_battery_handler(print_battery)
    m.add_emg_handler(add_to_queue)

    """worker function"""
    while True:
        try:
            m.run()
        except:
            print("Worker Stopped")
            quit()

# ------------ Plot Setup ---------------
QUEUE_SIZE = 100
SENSORS = 1
# Set the size of the plot
plt.rcParams["figure.figsize"] = (4,16)
# using the variable axs for multiple Axes
fig, subplots = plt.subplots(SENSORS, 1)
fig.canvas.manager.set_window_title("8 Channel EMG plot")
fig.tight_layout()
# Set each line to a different color

name = "tab10" # Change this if you have sensors > 10
cmap = get_cmap(name)  # type: matplotlib.colors.ListedColormap
colors = cmap.colors  # type: list

line, = subplots.plot(range(QUEUE_SIZE), [0] * QUEUE_SIZE)

emg_queue = queue.Queue(QUEUE_SIZE)

def animate(i):
    # Myo Plot
    while not (q.empty()):
        myox = list(q.get())
        if emg_queue.full():
            emg_queue.get()
        emg_queue.put(myox)

    channels = np.array(emg_queue.queue)

    if emg_queue.full():
        channel = channels[:, 3]  # retrieve data from the 4th channel
        line.set_ydata(channel)
        subplots.set_ylim(0, max(1024, max(channel)))

    # Add a vertical line at y=200
    subplots.axhline(y=200, color='red')

if __name__ == '__main__':
        # Start Myo Process
        p = multiprocessing.Process(target=worker, args=(q,))
        p.start()

        while q.empty():
            # Wait until we actually get data
            continue
        anim = animation.FuncAnimation(fig, animate, blit=False, interval=2)

        def on_close(event):
            p.terminate()
            raise KeyboardInterrupt

        fig.canvas.mpl_connect('close_event', on_close)

        try:
            plt.show()
        except KeyboardInterrupt:
            plt.close()
            p.close()
            quit()