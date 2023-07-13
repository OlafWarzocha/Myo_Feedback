import multiprocessing
import queue
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import animation
from matplotlib.cm import get_cmap
from pyomyo import Myo, emg_mode

q = multiprocessing.Queue()

threshold = 300


# Class for handling the Myo armband and retrieving EMG data
class MyoWorker:
    def __init__(self, q):
        self.q = q

    def run(self):
        # Initialize the Myo armband
        m = Myo(mode=emg_mode.PREPROCESSED)
        m.connect()

        def add_to_queue(emg, movement):
            # Add the retrieved EMG data to the queue
            self.q.put(emg)

        def print_battery(bat):
            # Print the battery level
            print("Battery level:", bat)

        # Configure Myo settings and event handlers
        m.set_leds([255, 255, 255], [255, 255, 255])
        m.vibrate(1)
        m.add_battery_handler(print_battery)
        m.add_emg_handler(add_to_queue)

        while True:
            try:
                # Continuously retrieve EMG data
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

counter = 0


# Animation function for updating the plot
def animate(i):
    global counter

    # Retrieve EMG data from the global queue and store it in the local emg_queue
    while not q.empty():
        myox = list(q.get())
        if emg_queue.full():
            emg_queue.get()
        emg_queue.put(myox)

    channels = np.array(emg_queue.queue)

    if emg_queue.full():
        channel = channels[:, 7]  # 3 to retrieve data from the 4th channel and 7 for 8th channel
        line.set_ydata(channel)
        subplots.set_ylim(0, max(1024, max(channel)))

        if max(channel) > threshold:
            subplots.set_facecolor('yellow')
            counter += 1
            if counter >= 50:  # (50 = 1sec)
                subplots.set_facecolor('xkcd:mint green')
        else:
            subplots.set_facecolor('white')
            counter = 0

    subplots.axhline(y=threshold, color='red')


if __name__ == '__main__':
    myo_worker = MyoWorker(q)
    p = multiprocessing.Process(target=myo_worker.run)
    p.start()

    while q.empty():
        continue
    anim = animation.FuncAnimation(fig, animate, blit=False, interval=10)


    # Function to handle the plot window close event
    def on_close(event):
        p.terminate()
        raise KeyboardInterrupt


    fig.canvas.mpl_connect('close_event', on_close)

    try:
        # Display the plot
        plt.show()
    except KeyboardInterrupt:
        plt.close()
        p.close()
        quit()
