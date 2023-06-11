import multiprocessing
import queue
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import animation
from matplotlib.cm import get_cmap
from pyomyo import Myo, emg_mode

print("Press ctrl+pause/break to stop")

q = multiprocessing.Queue()

threshold = 300

class MyoWorker:
    def __init__(self, q):
        self.q = q

    def run(self):
        m = Myo(mode=emg_mode.PREPROCESSED)
        m.connect()

        def add_to_queue(emg, movement):
            self.q.put(emg)

        def print_battery(bat):
            print("Battery level:", bat)

        m.set_leds([255, 0, 0], [255, 0, 0])
        m.vibrate(1)
        m.add_battery_handler(print_battery)
        m.add_emg_handler(add_to_queue)

        while True:
            try:
                m.run()
            except:
                print("Worker Stopped")
                quit()

# ------------ Plot Setup ---------------
QUEUE_SIZE = 50
SENSORS = 1
plt.rcParams["figure.figsize"] = (4, 16)
fig, subplots = plt.subplots(SENSORS, 1)
fig.canvas.manager.set_window_title("8 Channel EMG plot")
fig.tight_layout()
name = "tab10"
cmap = get_cmap(name)
colors = cmap.colors

line, = subplots.plot(range(QUEUE_SIZE), [0] * QUEUE_SIZE)

emg_queue = queue.Queue(QUEUE_SIZE)

counter = 0  # counter for tracking time above the red line

def animate(i):
    global counter

    # Myo Plot
    while not q.empty():
        myox = list(q.get())
        if emg_queue.full():
            emg_queue.get()
        emg_queue.put(myox)

    channels = np.array(emg_queue.queue)

    if emg_queue.full():
        channel = channels[:, 3]  # retrieve data from the 4th channel
        line.set_ydata(channel)
        subplots.set_ylim(0, max(1024, max(channel)))

        # Check if EMG signal is above the red line
        if max(channel) > threshold:
            subplots.set_facecolor('yellow')
            counter += 1
            if counter >= 50:  # (50 = 1sec)
                subplots.set_facecolor('xkcd:mint green')
        else:
            subplots.set_facecolor('white')
            counter = 0
        #print(counter)

    # Add a vertical line at y=200
    subplots.axhline(y=threshold, color='red')

if __name__ == '__main__':
    # Start Myo Process
    myo_worker = MyoWorker(q)
    p = multiprocessing.Process(target=myo_worker.run)
    p.start()

    while q.empty():
        continue
    anim = animation.FuncAnimation(fig, animate, blit=False, interval=5)

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