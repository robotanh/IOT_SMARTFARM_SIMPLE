from adafruit import Adafruit_MQTT
from timer import *
import threading
import fsm
import time
import random
from rs485 import *
import datetime

state = {
    "next-cycle": 1,
    "mixer1": 2,
    "mixer2": 2,
    "mixer3": 2,
    "selector": None,
    "pump-in": 2,
    "pump-out": 2,
    "time-start": "19:23",
    "active": 0,
}

sched_active = []

def data_callback(feed_id, payload):
    key = feed_id #.replace("assignment.", "")
    print("Received payload:", payload)
    if key == "next-cycle":
        try:
            state["next-cycle"] = payload['cycles']
            time_start = payload['time-start']
            if len(time_start) == 4:
                formatted_time_start = f"{time_start[:2]}:{time_start[2:]}" 
                state["time-start"] = formatted_time_start
                print(f"Updated {key} to {payload['cycles']} cycles and cooldown time to {formatted_time_start}")
            else:
                print("Invalid time format for time-start:", time_start)
        except ValueError:
            print("Invalid payload format for assignment.nextcycle:", payload)
    elif key in state:
        state[key] = payload
        print(f"Updated {key} to {state[key]}")
    else:
        print(f"No handler found for feed: {feed_id}")

def main_loop():
    start_sched = fsm.FarmScheduler()
    while True:
        print(sched_active)
        if sched_active:
            for schedule in sched_active:
                start_sched.add_schedule(schedule)
                sched_active.remove(schedule)
            start_sched.run()
        time.sleep(1)
    
def add_sched():
    while True:
        # print(state)
        if state["active"] == 1:
            sched_active.append(state.copy())
            print("Activated new schedule!")
            print(state)
            state["active"] = 0  # Reset the active flag
        time.sleep(1)
    
def publish_data(client):
    sensor = Physic()
    while True:
        print("Current date and time: ", datetime.datetime.now())
        # Publish random data to a feed
        feed_id1 = "temperature"  
        feed_id2 = "humidity"
        value1 = int(sensor.readSensors("soil_temperature"))%100
        value2 = int(sensor.readSensors("soil_moisture")) 
        # value1 = random.randint(20, 30)
        # value2 = random.randint(20, 30)
        client.publish(feed_id1, value1)
        client.publish(feed_id2, value2)
        # client.publish(feed_id1, readTemperature())
        # client.publish(feed_id2, readMoisture())
        print(f"Published {value1} to {feed_id1}")
        print(f"Published {value2} to {feed_id2}")
        time.sleep(5)  

# Initialize the Adafruit MQTT client and set the callback
adafruit_client = Adafruit_MQTT()
adafruit_client.setRecvCallBack(data_callback)


add_sched_thread = threading.Thread(target=add_sched)
main_loop_thread = threading.Thread(target=main_loop)
publish_thread = threading.Thread(target=publish_data, args=(adafruit_client.client,))

add_sched_thread.start()
main_loop_thread.start()
publish_thread.start()

add_sched_thread.join()
main_loop_thread.join()
publish_thread.join()
