# Elevator simulator

import numpy as np
import queue
import threading
import os
import time
from sortedcontainers import SortedSet

TOP_FLOOR = 20
BOTTOM_FLOOR = 0
SLEEP_SECONDS = 2

STATE_UP = "moving up"
STATE_DN = "moving down"
STATE_STOP = "stopped"
# or create an enum class
# class mode:
#    action


# Class to communicate between elevator_buttons, elevator_car, and controller
class sharedData:
    fifo_up = SortedSet()  # contains floors to stop at, next floor at the end
    target_floor = 0  # stop on this floor next
    state = STATE_UP  # elevator state: "stopped", "moving up", or "moving dn"
    current_floor = 0  # current floor, position of the elevator
    wake_controller = False  # indicates if elevator_buttons pushed new floor button
    ## Need indicator of overall direction of travel
    moving = False # 

shared_data = sharedData()  # instantiate object


# Elevator car thread, sets elevator state, then moves elevator to shared_data.target_floor
def elevator_car():
    i = 0
    while True:
        i += 1

        # Going up
        if shared_data.target_floor > shared_data.current_floor:
            shared_data.state = STATE_UP
            shared_data.moving = True
            shared_data.current_floor += 1

        # Going down
        elif shared_data.target_floor < shared_data.current_floor:
            shared_data.state = STATE_DN
            shared_data.moving = True
            shared_data.current_floor -= 1

        else:
            shared_data.wake_controller = True
            shared_data.moving = False # this line is required
            print("stopped")

        print(
            f"current_floor={shared_data.current_floor:d}, target_floor={shared_data.target_floor:d}, shared_data.fifo_up={shared_data.fifo_up:}, shared_data.state={shared_data.state:}"
        )
        time.sleep(SLEEP_SECONDS)


# Thread to handle pressing elevator buttons
def elevator_buttons():
    
    j = 0
    while True:
        j += 1
        # print(f"\nj={j:d}")
        f = input("Input floor number:\n")
        f = int(f)
        if f >= BOTTOM_FLOOR and f <= TOP_FLOOR:
            shared_data.fifo_up.add(f)
            print(
                f"elevator_buttons(): button pressed, shared_data.fifo_up={shared_data.fifo_up:}, shared_data.state={shared_data.state:}"
            )   
            shared_data.wake_controller = True  # indicate the pressing of a new button


# Business logic: how to assemble the shared_data.fifo_up which contains what floors the elevator will stop on
def controller():
    saved_floor = 0
    k = 0
    shared_data.fifo_up.add(BOTTOM_FLOOR)

    while True:
        k += 1

        if shared_data.wake_controller:
            if len(shared_data.fifo_up) > 0:
                if (shared_data.moving == False):
                    if (shared_data.state == STATE_UP):
                        shared_data.target_floor = shared_data.fifo_up[0] 
                        del shared_data.fifo_up[0] 
                    if (shared_data.state == STATE_DN):
                        shared_data.target_floor = shared_data.fifo_up[-1]
                        del shared_data.fifo_up[-1] 
                if (shared_data.moving == True):
                    if shared_data.state == STATE_UP:
                        if shared_data.current_floor < shared_data.fifo_up[0]:
                            saved_floor = shared_data.target_floor
                            shared_data.target_floor = shared_data.fifo_up[0]
                            shared_data.fifo_up.add(saved_floor)
                            del shared_data.fifo_up[0]
                        else:
                            dummy = 0
                            # Need another fifo for collecting the down floors
                    
                    if shared_data.state == STATE_DN:
                        if shared_data.current_floor > shared_data.fifo_up[-1]:
                            saved_floor = shared_data.target_floor
                            shared_data.target_floor = shared_data.fifo_up[-1]
                            shared_data.fifo_up.add(saved_floor)
                            del shared_data.fifo_up[-1]
                  

            shared_data.wake_controller = False

        time.sleep(SLEEP_SECONDS)  # allow for elevator_car thread to pick up changes to shared_data.target_floor


# Launch threads from main program
if __name__ == "__main__":

    # creating threads
    e1 = threading.Thread(target=elevator_car, name="e1")
    b1 = threading.Thread(target=elevator_buttons, name="b1")
    c1 = threading.Thread(target=controller, name="c1")

    # starting threads
    e1.start()
    b1.start()
    c1.start()

    # wait until all threads finish
    e1.join()
    b1.join()
    c1.join()
