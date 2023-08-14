import time
import multiprocessing
import pandas as pd
from pyomyo import Myo, emg_mode

counter = 0  # Counter to keep track of consecutive frames above the threshold
pause_counter = 0  # Counter to introduce a pause after reaching the threshold
threshold = 150  # Threshold value for detecting a signal above which actions are performed

def data_worker(mode, seconds, filepath, vibrating):

    collect = True
    myo_data = []  # List to store the collected EMG data

    m = Myo(mode=mode)
    m.connect()

    def print_battery(bat):
        print("Battery level:", bat)    # Print battery level

    m.add_battery_handler(print_battery)

    def add_to_queue(emg, movement):
        # Callback function for handling incoming EMG data

        myo_data.append(emg[3])  # 3 to retrieve data from the 4th channel and 7 for 8th channel

        global counter
        global pause_counter
        global threshold

        print(counter)

        if emg[3] > threshold and pause_counter == 0:
            # If the EMG value is above the threshold and no pause is active

            m.set_leds([255, 255, 0], [255, 255, 0])  # Set LED color to yellow [255, 255, 0]

            if not vibrating.value:
                m.vibrate(1)  # Vibrate the Myo armband for 1 second
                vibrating.value = True

            counter += 1

            if counter > 50:
                # If counter exceeds 50, perform additional actions and reset counter

                m.set_leds([255, 0, 0], [255, 0, 0])  # Set LED color to red
                m.vibrate(1)  # Vibrate the Myo armband for 1 second
                counter = 0
                pause_counter = 50  # Introduce a pause of 50 frames
                m.vibrate(1)  # Vibrate the Myo armband for 1 second

        else:
            if pause_counter == 0:
                m.set_leds([0, 255, 255], [0, 255, 255])  # Set LED color to green [0, 255, 0]

            counter = 0
            vibrating.value = False

            if not pause_counter == 0:
                pause_counter -= 1

    m.add_emg_handler(add_to_queue)  # Register the add_to_queue callback for handling EMG data

    m.set_leds([255, 255, 255], [255, 255, 255])  # Set LED color to white
    m.vibrate(1)  # Vibrate the Myo armband for 1 second

    print("Data Worker started to collect")
    start_time = time.time()
    while collect:
        if time.time() - start_time < seconds:
            m.run()  # Run the Myo thread to collect data
        else:
            collect = False
            collection_time = time.time() - start_time
            print("Finished collecting.")
            print(f"Collection time: {collection_time}")
            print(len(myo_data), "frames collected")

            myo_df = pd.DataFrame(myo_data, columns=["Channel_4"])
            myo_df.to_csv(filepath, index=False)  # Save collected data to a CSV file
            print("CSV Saved at: ", filepath)


if __name__ == '__main__':
    seconds = 2000
    file_name = str(seconds) + "_test_emg.csv"

    mode = emg_mode.PREPROCESSED
    vibrating = multiprocessing.Value('b', False)  # Shared value to track vibrating state

    p = multiprocessing.Process(target=data_worker, args=(mode, seconds, file_name, vibrating))
    p.start()
