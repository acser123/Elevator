# Elevator simulator

from multiprocessing import shared_memory, sharedctypes
from tarfile import FIFOTYPE
import numpy as np
import queue
import threading
import os
import time
from sortedcontainers import SortedSet

TOP_FLOOR = 20
BOTTOM_FLOOR = 0
SLEEP_SECONDS = 2

# Direction of travel states
UP = "moving up"
DN = "moving down"




# Class to communicate between elevator_buttons, elevator_car, and controller
# TODO: this needs to be protected, otherwise timing related problems occur
class sharedData:
    fifo_up = SortedSet()   # n up direction travel, contains floors to stop at, next floor at the beginning
    fifo_dn = SortedSet()   # n up direction travel, contains floors to stop at, next floor at the end
    target_floor = 0        # stop on this floor next
    travel_direction = UP   # elevator direction of travel: "moving up", or "moving dn"
    moving = False          # Movement indicator True/False
    current_floor = 0       # current floor, position of the elevator
    wake_controller = False # indicates if elevator_buttons pushed new floor button
    lock = threading.Lock() # Mutex lock to ensure that only one thread is changing a variable at any time
   
    

shared_data = sharedData()  # instantiate object


# Elevator car thread, sets elevator travel_direction, then moves elevator to shared_data.target_floor
def elevator_car():
    i = 0
    while True:
        i += 1

        # Going up
        #shared_data.lock.acquire()
        if shared_data.target_floor > shared_data.current_floor:
            
            shared_data.travel_direction = UP
            shared_data.moving = True
            shared_data.current_floor += 1
            

        # Going down
        elif shared_data.target_floor < shared_data.current_floor:
            
            shared_data.travel_direction = DN
            shared_data.moving = True
            shared_data.current_floor -= 1
            
        else:
            
            shared_data.wake_controller = True
            shared_data.moving = False # this line is required
            print(f"stopped on floor {shared_data.current_floor:}")
            

        print(
            f"current_floor={shared_data.current_floor:d}, target_floor={shared_data.target_floor:d}, fifo_up={shared_data.fifo_up:}, fifo_dn={shared_data.fifo_dn:}, travel_direction={shared_data.travel_direction:}"
        )
        #shared_data.lock.release()
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
            #shared_data.lock.acquire()
            # Add new floor to the appropriate fifo up or dn
            # If we passed that floor, we will deal with it in the controller() thread
            if shared_data.travel_direction == UP:
                shared_data.fifo_up.add(f)
            if shared_data.travel_direction == DN:
                shared_data.fifo_dn.add(f) 
            print(
                f"elevator_buttons(): button pressed, fifo_up={shared_data.fifo_up:}, fifo_dn={shared_data.fifo_dn:}, shared_data.travel_direction={shared_data.travel_direction:}"
            )   
            shared_data.wake_controller = True  # indicate the pressing of a new button
            #shared_data.lock.release()

# Business logic: how to assemble the shared_data.fifo_up which contains what floors the elevator will stop on
def controller():
    saved_floor = 0
    k = 0
    shared_data.lock.acquire()
    shared_data.fifo_up.add(BOTTOM_FLOOR)
    shared_data.travel_direction = UP
    shared_data.lock.release()

    while True:
        k += 1
      
        # Either a button was pushed or the elevator reached the target floor and stopped

        if shared_data.wake_controller:
            # Acquire mutex to protect controller logic
            #shared_data.lock.acquire()
            
            # Upward travel logic
            # Can't do any operation on an empty fifo
            if len(shared_data.fifo_up) > 0:
                # Direction of travel is up
                if shared_data.travel_direction == UP:
                    if (shared_data.moving == False):
                        
                        shared_data.target_floor = shared_data.fifo_up[0]
                        del shared_data.fifo_up[0]
                       

                    if shared_data.moving == True:
                        if shared_data.current_floor < shared_data.fifo_up[0]:
                            # Elevator needs to stop on a lower floor than what was the original destination
                            # We need to insert a new target floor and save the old target floor on the fifo
                            
                            saved_floor = shared_data.target_floor
                            shared_data.target_floor = shared_data.fifo_up[0]
                            shared_data.fifo_up.add(saved_floor)
                            del shared_data.fifo_up[0]
                            
                        else:
                            # Save lower floor pushed than current floor for the next downward travel stop
                            
                            shared_data.fifo_dn.add(shared_data.fifo_up[0])
                            del shared_data.fifo_up[0]
                            


                        
                       

            # --------------------------------------
            # Downward travel logic
            # Can't do any operation on an empty fifo
            if len(shared_data.fifo_dn) > 0:
                # Direction of travel is up
                if shared_data.travel_direction == DN:
                    if (shared_data.moving == False):
                        
                        shared_data.target_floor = shared_data.fifo_dn[-1]
                        del shared_data.fifo_dn[-1]
                     
                    if shared_data.moving == True:
                        if shared_data.current_floor > shared_data.fifo_dn[-1]:
                            # Elevator needs to stop on a lower floor than what was the original destination
                            # We need to insert a new target floor and save the old target floor on the fifo
                            
                            saved_floor = shared_data.target_floor
                            shared_data.target_floor = shared_data.fifo_dn[-1]
                            shared_data.fifo_dn.add(saved_floor)
                            del shared_data.fifo_dn[-1]
                            
                        else:
                            # Save higher floor pushed than current floor for the next upward travel stop
                            
                            shared_data.fifo_up.add(shared_data.fifo_dn[-1])
                            del shared_data.fifo_dn[-1]                  
                            
            ## ------
            # Changing direction of travel

            # No more floors on upward travel, elevator stops and there are floors pushed below, then elevator needs
            # to start going down
            if len(shared_data.fifo_up) == 0:
                if shared_data.travel_direction == UP:
                    if (shared_data.moving == False):
                        if len(shared_data.fifo_dn) > 0:
                            shared_data.target_floor = shared_data.fifo_dn[-1]
                            del shared_data.fifo_dn[-1]
                        # Change travel direction
                        shared_data.travel_direction = DN

            # No more floors on downward travel,elevator stops and there are floors pushed above, then elevator needs
            # to start going up
            if len(shared_data.fifo_dn) == 0:
                if shared_data.travel_direction == DN:
                    if (shared_data.moving == False):
                        if len(shared_data.fifo_up) > 0:
                            shared_data.target_floor = shared_data.fifo_up[0]
                            del shared_data.fifo_up[0]
                        # Change travel direction
                        shared_data.travel_direction = UP

            # Release mutex lock
            #shared_data.lock.release()
        # Reset interrupt flag
        shared_data.wake_controller = False
        
        # Ensure you can receive updates
        time.sleep(SLEEP_SECONDS)  # allow for controller() thread to pick up changes faster than elevator_car() to shared_data.target_floor


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