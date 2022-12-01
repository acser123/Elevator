# Elevator simulator

from multiprocessing import shared_memory, sharedctypes
from tarfile import FIFOTYPE
import numpy as np
import queue
import threading
import os
import time
from sortedcontainers import SortedSet

# Building setup
TOP_FLOOR = 20
BOTTOM_FLOOR = 0

# Elevator car needs this much time to get to move between floors
SLEEP_SECONDS = 5

# Direction of travel states
UP = "traveling up"
DN = "traveling down"
NO_DIRECTION = "no travel direction"




# Class to communicate between elevator_buttons, elevator_car, and controller

# Note: 1) access to data should be protected by acquiring and releasing the lock

# TODO: this needs to be protected, otherwise timing related problems occur
class sharedData:
    fifo_up = SortedSet()   # n up direction travel, contains floors to stop at, next floor at the beginning
    fifo_dn = SortedSet()   # n up direction travel, contains floors to stop at, next floor at the end
    target_floor = 0        # stop on this floor next
    travel_direction = NO_DIRECTION   # elevator direction of travel: UP or DN or NO_DIRECTION
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
 
        if shared_data.target_floor > shared_data.current_floor:
            
            shared_data.moving = True
            shared_data.current_floor += 1
            
            # Delete the next element of the fifo 
            # This is needed so that a rapid succession of buttons can be presseed while the elevator is not moving
            shared_data.lock.acquire()
            if len(shared_data.fifo_up) > 0 and shared_data.fifo_up[0] == shared_data.current_floor:
                del shared_data.fifo_up[0]
            shared_data.lock.release()

        # Going down
        elif shared_data.target_floor < shared_data.current_floor:
            
            shared_data.moving = True
            shared_data.current_floor -= 1
            
            # Delete the next element of the fifo 
            # This is needed so that a rapid succession of buttons can be presseed while the elevator is not moving
            shared_data.lock.acquire()
            if len(shared_data.fifo_dn) > 0 and shared_data.fifo_dn[-1] == shared_data.current_floor:
                del shared_data.fifo_dn[-1]
            shared_data.lock.release()
                
        # Stopped on a floor target_floor == current_floor, either stop or get a new target_floor from fifo_up or fifo_dn
        else:
            shared_data.lock.acquire()
            shared_data.wake_controller = True
            shared_data.moving = False # this line is required
            print(f"stopped on floor {shared_data.current_floor:}")
            shared_data.lock.release()

        print(
            f"current_floor={shared_data.current_floor:d}, moving={shared_data.moving:}, target_floor={shared_data.target_floor:d}, fifo_up={shared_data.fifo_up:}, fifo_dn={shared_data.fifo_dn:}, travel_direction={shared_data.travel_direction:}"
        )
        
        # It takes time for the elevator_car to move between floors
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
            
            shared_data.lock.acquire()

            # Add new floor to the appropriate fifo up or dn
            # If we passed that floor, we will deal with it in the controller() thread
            # TODO: Move this code to controller() for better partitioning of components
            if shared_data.travel_direction == UP:
                shared_data.fifo_up.add(f)
            if shared_data.travel_direction == DN:
                shared_data.fifo_dn.add(f) 
            if shared_data.travel_direction == NO_DIRECTION:
                if shared_data.current_floor < f:
                    shared_data.fifo_up.add(f)
                if shared_data.current_floor > f:
                    shared_data.fifo_dn.add(f)
           
            print(
                f"elevator_buttons(): button pressed, fifo_up={shared_data.fifo_up:}, fifo_dn={shared_data.fifo_dn:}, shared_data.travel_direction={shared_data.travel_direction:}"
            )   
            
            # indicate the pressing of a new button
            shared_data.wake_controller = True  # indicate the pressing of a new button
            shared_data.lock.release()

            # No sleep here, this is a realtime method/function, button can be pushed at any time

# Elevator controller business logic: how to assemble the shared_data.fifo_up and shared_data.fifo_dn which contain what floors the elevator will stop on
def controller():
    saved_floor = 0
    k = 0
    
    shared_data.lock.acquire()
    shared_data.travel_direction = NO_DIRECTION
    shared_data.lock.release()

    while True:
        k += 1
        
        # Either a button was pushed or the elevator reached the target floor and stopped
        if shared_data.wake_controller:
            
            # Acquire mutex to protect controller logic
            shared_data.lock.acquire()
            
            # Start going in a direction (elevator was not going anywhere but now received a button push
            if shared_data.travel_direction == NO_DIRECTION and shared_data.moving == False:
                if len(shared_data.fifo_up) > 0:
                    print("controller: NO_DIRECTION -> UP")
                    shared_data.travel_direction = UP
                if len(shared_data.fifo_dn) > 0:
                    print("controller: NO_DIRECTION -> DN")
                    shared_data.travel_direction = DN


            # Upward travel logic
            # (Upward travel logic is parallel to Downward travel logic, below)

            # Direction of travel is up
            if shared_data.travel_direction == UP:
                
                # Elevator stopped and there is no more floors pushed on fifo_up
                if len(shared_data.fifo_up) == 0 and shared_data.current_floor == shared_data.target_floor:
                    print("controller: UP -> NO_DIRECTION")
                    shared_data.travel_direction == NO_DIRECTION
                
                # Can't do any operation on an empty fifo
                if len(shared_data.fifo_up) > 0:
                
                    # Elevator is not moving
                    if (shared_data.moving == False):
                        
                        # Pop the lowest element of the fifo_up and set it as the target_floor
                        # Only allow for setting the target floor when it is higher than the current target floor
                        if shared_data.fifo_up[0] > shared_data.current_floor:
                            shared_data.target_floor = shared_data.fifo_up[0]
                            print(f"controller: UP, moving=False, set target_floor={shared_data.target_floor:}")
                 
                    # Elevator is moving
                    if shared_data.moving == True:

                        # Elevator has not yet reached the target floor but moving towards it
                        if shared_data.current_floor < shared_data.fifo_up[0]:
                            # A button was pushed and now the Elevator needs to stop on a lower floor than what was the original destination
                            # We need to insert a new target floor and save the old target floor on the fifo
                            if shared_data.fifo_up[0] < shared_data.target_floor:
                                saved_floor = shared_data.target_floor
                                shared_data.target_floor = shared_data.fifo_up[0]
                                shared_data.fifo_up.add(saved_floor)
                                print(f"controller: UP, inserting new floor, moving={shared_data.moving:0}, curr_floor<fifo_up[0], fifo_up[0]<target_floor, set target_floor={shared_data.target_floor:}")
                        #else:
                   # Need to move all floors from the beginning of the fifo_up to fifo_dn that are smaller than the current floor

                    for val in shared_data.fifo_up:
                               
                        if val < shared_data.current_floor:
                            shared_data.fifo_dn.add(val)
                            shared_data.fifo_up.remove(val)
                            print(f"controller: UP, removed val={val:}")
                            print(f"controller: UP, moving=True, cleanup, moved val={val:} from fifo_up to fifo_dn")
                         
                        
                       

            # --------------------------------------
            # Downward travel logic

            # Direction of travel is down
            if shared_data.travel_direction == DN:

                if len(shared_data.fifo_dn) == 0 and shared_data.current_floor == shared_data.target_floor:
                    print("controller: DN -> NO_DIRECTION")
                    shared_data.travel_direction == NO_DIRECTION

                # Can't do any operation on an empty fifo
                if len(shared_data.fifo_dn) > 0:
                
                    # Elevator is not moving
                    if (shared_data.moving == False):
                        
                        # Pop the highest element of the fifo_dn and set it as the target_floor
                        # Only allow for setting the target floor when it is higher than the current target floor
                        if shared_data.fifo_dn[-1] < shared_data.current_floor:
                            shared_data.target_floor = shared_data.fifo_dn[-1]
                            print(f"controller: DN, moving=False, set target_floor={shared_data.target_floor:}")
                 
                    # Elevator is moving
                    if shared_data.moving == True:

                        # Elevator has not yet reached the target floor but moving towards it
                        if shared_data.current_floor > shared_data.fifo_dn[-1]:
                            # A button was pushed and now the Elevator needs to stop on a higher floor than what was the original destination
                            # We need to insert a new target floor and save the old target floor on the fifo
                            if shared_data.fifo_dn[-1] > shared_data.target_floor:
                                saved_floor = shared_data.target_floor
                                shared_data.target_floor = shared_data.fifo_dn[-1]
                                shared_data.fifo_dn.add(saved_floor)
                                print(f"controller: DN, inserting new floor, moving={shared_data.moving:0}, curr_floor>fifo_dn[-1], fifo_dn[-1]>target_floor, set target_floor={shared_data.target_floor:}")
                    
                    # Need to move all floors from the end of the fifo_dn to fifo_up that are larger than the current floor

                    for val in shared_data.fifo_dn:
                               
                        if val > shared_data.current_floor:
                            shared_data.fifo_up.add(val)
                            shared_data.fifo_dn.remove(val)
                            print(f"controller: DN, removed val={val:}")
                            print(f"controller: DN, moving=True, cleanup, moved val={val:} from fifo_dn to fifo_up")
                         
                        
                       
            
                                
            ## ------
            # Changing direction of travel

            # 

            # No more floors on upward travel, elevator stops and there are floors pushed below, then elevator needs
            # to start going down
            if len(shared_data.fifo_up) == 0 and shared_data.travel_direction == UP and shared_data.moving == False and shared_data.current_floor == shared_data.target_floor:
            
                if len(shared_data.fifo_dn) > 0:
                    shared_data.target_floor = shared_data.fifo_dn[-1]
                    del shared_data.fifo_dn[-1]
                    print(f"controller: change direction of travel, from UP, moving=False, set target_floor={shared_data.target_floor:}")

                    # Change travel direction
                    shared_data.travel_direction = DN
                else:
                    shared_data.travel_direction = NO_DIRECTION
            
            # No more floors on downward travel,elevator stops and there are floors pushed above, then elevator needs
            # to start going up
            if len(shared_data.fifo_dn) == 0 and shared_data.travel_direction == DN and shared_data.moving == False and shared_data.current_floor == shared_data.target_floor:
            
                if len(shared_data.fifo_up) > 0:
                    shared_data.target_floor = shared_data.fifo_up[0]
                    del shared_data.fifo_up[0]
                    print(f"controller: change direction of travel, from DN, moving=False, set target_floor={shared_data.target_floor:}")

                    # Change travel direction
                    shared_data.travel_direction = UP
                else:
                    shared_data.travel_direction = NO_DIRECTION

            # Release mutex lock
            shared_data.lock.release()
            # Reset interrupt flag
            shared_data.wake_controller = False
        
            # No sleep here, this is a realtime method/function, controller cannot sleep, because
            # the elevator moves and a button can be pushed at any time which need to be processed


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