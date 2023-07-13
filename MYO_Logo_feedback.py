import time
import multiprocessing
import pandas as pd
from pyomyo import Myo, emg_mode

counter = 0
pause_counter = 0
threshold = 300


def data_worker(mode, seconds, filepath, vibrating):
    collect = True
    myo_data = []  # List to store the collected EMG data

    m = Myo(mode=mode)
    m.connect()

    def print_battery(bat):
        print("Battery level:", bat)  # Print battery level

    m.add_battery_handler(print_battery)

    def add_to_queue(emg, movement):
        # Append the EMG data to myo_data
        myo_data.append(emg[3])  # 3 to retrieve data from the 4th channel and 7 for 8th channel

        global counter
        global pause_counter
        global threshold

        # print(counter)

        if emg[3] > threshold and pause_counter == 0:
            # If the EMG value exceeds the threshold and pause_counter is 0, perform actions
            m.set_leds([255, 255, 0], [255, 255, 0])

            counter += 1

            if counter > 50:
                # If counter exceeds 50, perform additional actions and reset counter

                m.set_leds([255, 0, 0], [255, 0, 0])
                counter = 0
                pause_counter = 50

        else:
            if pause_counter == 0:
                # If pause_counter is 0, set LEDs to indicate normal state
                m.set_leds([0, 255, 0], [0, 255, 0])

            counter = 0

            if not pause_counter == 0:
                # If pause_counter is not 0, decrement it
                pause_counter -= 1

    m.add_emg_handler(add_to_queue)

    m.set_leds([255, 255, 255], [255, 255, 255])
    m.vibrate(1)

    print("Data Worker started to collect")
    start_time = time.time()
    while collect:
        if time.time() - start_time < seconds:
            # Keep collecting data until the specified collection time is reached
            m.run()
        else:
            collect = False
            collection_time = time.time() - start_time
            print("Finished collecting.")
            print(f"Collection time: {collection_time}")
            print(len(myo_data), "frames collected")

            # Convert myo_data to a DataFrame and save it to a CSV file
            myo_df = pd.DataFrame(myo_data, columns=["Channel_4"])
            myo_df.to_csv(filepath, index=False)
            print("CSV Saved at: ", filepath)


if __name__ == '__main__':
    # Set the collection time and output file name
    seconds = 20
    file_name = str(seconds) + "_test_emg.csv"

    # Set the Myo armband mode and initialize the shared value for vibration control
    mode = emg_mode.PREPROCESSED
    vibrating = multiprocessing.Value('b', False)

    # Start the data worker process
    p = multiprocessing.Process(target=data_worker, args=(mode, seconds, file_name, vibrating))
    p.start()
