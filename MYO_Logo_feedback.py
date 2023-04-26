import time
import multiprocessing
import pandas as pd
from pyomyo import Myo, emg_mode

counter = 0
pause_counter = 0

def data_worker(mode, seconds, filepath, vibrated):
    """
    Function to collect EMG data from a Myo armband for a given number of seconds,
    save the data to a CSV file, and changes logo the armband when the 4th EMG signal
    exceeds the threshold.
    """
    # Initialize variables
    collect = True
    myo_data = []

    # Access global counter variable


    # Connect to the Myo armband
    m = Myo(mode=mode)
    m.connect()

    # Define the function that adds EMG data to the queue.
    def add_to_queue(emg, movement):
        # Append the value of the fourth EMG signal to the queue.
        myo_data.append(emg[3])

        # Access global counter variable
        global counter
        global pause_counter

        # Change Logo the armband if the 4th EMG signal exceeds the threshold
        if emg[3] > 300 and pause_counter == 0:
            m.set_leds([255, 255, 0], [255, 255, 0])
            vibrated.value = True
            if vibrated.value:
                #m.vibrate(1)
                vibrated.value = False

            counter += 1

            if counter>50:
                m.set_leds([255, 0, 0], [255, 0, 0])
                m.vibrate(1)
                counter = 0
                pause_counter = 50

        else:
            if pause_counter == 0:
                m.set_leds([0, 255, 0], [0, 255, 0])
            counter = 0

            if not pause_counter == 0:
                pause_counter -= 1


    # Add the EMG data handler to the Myo armband
    m.add_emg_handler(add_to_queue)

    # Add a battery handler to the Myo armband
    def print_battery(bat):
        print("Battery level:", bat)

    m.add_battery_handler(print_battery)

    # Set the LED colors and vibrate the armband to indicate that it is connected
    m.set_leds([255, 255, 255], [255, 255, 255])
    m.vibrate(1)

    # Start collecting data
    print("Data Worker started to collect")
    start_time = time.time()
    while collect:
        if time.time() - start_time < seconds:
            m.run()
        else:
            collect = False
            collection_time = time.time() - start_time
            print("Finished collecting.")
            print(f"Collection time: {collection_time}")
            print(len(myo_data), "frames collected")

            # Save the collected data to a CSV file
            myo_df = pd.DataFrame(myo_data, columns=["Channel_4"])
            myo_df.to_csv(filepath, index=False)
            print("CSV Saved at: ", filepath)

if __name__ == '__main__':
    # Set the collection time and output file name
    seconds = 10
    file_name = str(seconds) + "_test_emg.csv"

    # Set the Myo armband mode and initialize the shared value for vibration control
    mode = emg_mode.PREPROCESSED
    vibrating = multiprocessing.Value('b', False)

    # Start the data worker process
    p = multiprocessing.Process(target=data_worker, args=(mode, seconds, file_name, vibrating))
    p.start()

