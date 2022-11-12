# Python program to illustrate the concept
# of threading
import numpy as np
import queue
import threading

import os
import time
 
#N_iter = 10
NUMBER_OF_FLOORS = 5
SLEEP_SECONDS = 2

#floor_queue = queue.Queue()

# Class to communicate between elevator_buttons, elevator_car, and controller
class sharedData:
    fifo = [] # contains floors to stop at, next floor at the end
    target_floor = 0 # stop on this floor next
    state="stopped" # elevator state: "stopped", "moving up", or "moving dn"
    current_floor=0 # current floor, positionn of the elevator
    new_floor_added=False # indicates if elevator_buttons pushed new floor button


shared_data = sharedData() # instantiate object


# Elevator car thread, sets elevator state, then moves elevator to shared_data.target_floor
def elevator_car(): 
   i = 0
   while(1):
      i += 1
      
      # Going up
      if (shared_data.target_floor>shared_data.current_floor):
            # print (f"\ni={i:d}\n")
            while(shared_data.current_floor!=shared_data.target_floor):
               shared_data.state="moving up"
               if (shared_data.state=="moving up"):
                  shared_data.current_floor += 1
                  #shared_data.new_floor_added=False
                  print(f"moving up, current_floor={shared_data.current_floor:d}, target_floor={shared_data.target_floor:d}, shared_data.fifo={shared_data.fifo:}, shared_data.state={shared_data.state:}, shared_data.new_floor_added={shared_data.new_floor_added:}")
                  time.sleep(SLEEP_SECONDS) # allow to pick up any changes to target_floor
              
               if (shared_data.current_floor==shared_data.target_floor):
                  shared_data.state="stopped"
                  print(f"*** stopped, current_floor={shared_data.current_floor:d}, target_floor={shared_data.target_floor:d}, shared_data.fifo={shared_data.fifo:}, shared_data.state={shared_data.state:}, shared_data.new_floor_added={shared_data.new_floor_added:}")
                  time.sleep(SLEEP_SECONDS) # allow to pick up any changes to target_floor
      # Going down
      if (shared_data.target_floor<shared_data.current_floor):
            # print (f"\ni={i:d}\n")
            while(shared_data.current_floor!=shared_data.target_floor):
               shared_data.state="moving dn"
               if (shared_data.state=="moving dn"):
                  shared_data.current_floor -= 1
                  #shared_data.new_floor_added=False
                  print(f"moving dn, current_floor={shared_data.current_floor:d}, target_floor={shared_data.target_floor:d}, shared_data.fifo={shared_data.fifo:}, shared_data.state={shared_data.state:}, shared_data.new_floor_added={shared_data.new_floor_added:}")
                  
                  time.sleep(SLEEP_SECONDS)
               if (shared_data.current_floor==shared_data.target_floor):
                  shared_data.state="stopped"
                  print(f"*** stopped, current_floor={shared_data.current_floor:d}, target_floor={shared_data.target_floor:d}, shared_data.fifo={shared_data.fifo:}, shared_data.state={shared_data.state:}, shared_data.new_floor_added={shared_data.new_floor_added:}")
                  time.sleep(SLEEP_SECONDS)

# Thread to handle pressing elevator buttons
def elevator_buttons():

   j = 0
   while(1):
      j += 1      
      #print(f"\nj={j:d}")
      f = input("Input floor number:\n")
      f = int(f)
      shared_data.fifo.insert(-1,f)
      
      shared_data.new_floor_added=True # indicate the pressing of a new button

# Business logic: how to assemble the shared_data.fifo      
def controller():
   
   k = 0
   while(1):
      k += 1      
      #print(f"\nk={k:d}")
      #shared_data.fifo.sort(reverse=True)
      #print("\nbefore pop Floor shared_data=",shared_data.fifo)


      #
      if(shared_data.state=="moving up" and shared_data.new_floor_added==True):
        if (len(shared_data.fifo)>0):
            shared_data.fifo.sort(reverse=True)
        
            if(shared_data.target_floor>shared_data.fifo[-1]):
               next_target_floor = shared_data.target_floor
               shared_data.target_floor=shared_data.fifo.pop()
               shared_data.fifo.insert(-1,next_target_floor)
            
            #
            
            shared_data.new_floor_added=False     
            time.sleep(SLEEP_SECONDS) # allow for elevator_car thread to pick up changes to shared_data.target_floor

      #
      elif(shared_data.state=="moving up" and shared_data.new_floor_added==False):
        if (len(shared_data.fifo)>0): 
            shared_data.fifo.sort(reverse=True)
            #shared_data.target_floor=shared_data.fifo.pop()
            #shared_data.new_floor_added=False
            #print()
            time.sleep(SLEEP_SECONDS) # allow for elevator_car thread to pick up changes to shared_data.target_floor
            
      #
      elif(shared_data.state=="moving dn" and shared_data.new_floor_added==True):
        if (len(shared_data.fifo)>0):
            shared_data.fifo.sort(reverse=False)
            if(shared_data.target_floor<shared_data.fifo[-1]):
               next_target_floor = shared_data.target_floor
               shared_data.target_floor=shared_data.fifo.pop()
               shared_data.fifo.insert(-1,next_target_floor)
            #
            
            shared_data.new_floor_added=False
            time.sleep(SLEEP_SECONDS) # allow for elevator_car thread to pick up changes to shared_data.target_floor

      #
      elif(shared_data.state=="moving dn" and shared_data.new_floor_added==False):
        if (len(shared_data.fifo)>0): 
            shared_data.fifo.sort(reverse=False)
            #shared_data.target_floor=shared_data.fifo.pop()
            #shared_data.new_floor_added=False
            #print()
            
      elif(shared_data.state=="stopped" and shared_data.new_floor_added==True):
         if (len(shared_data.fifo)>0): 
            shared_data.fifo.sort(reverse=True)
            shared_data.target_floor=shared_data.fifo.pop()
            time.sleep(SLEEP_SECONDS) # allow for elevator_car thread to pick up changes to shared_data.target_floor
            
      #
      elif(shared_data.state=="stopped" and shared_data.new_floor_added==False):
         if (len(shared_data.fifo)>0): 
            shared_data.fifo.sort(reverse=True)
            shared_data.target_floor=shared_data.fifo.pop()
            #shared_data.new_floor_added=True
            time.sleep(SLEEP_SECONDS) # allow for elevator_car thread to pick up changes to shared_data.target_floor
         

# Launch threads from main program
if __name__ == "__main__":


    # creating threads
    e1 = threading.Thread(target=elevator_car, name='e1')
    b1 = threading.Thread(target=elevator_buttons, name='b1')  
    c1 = threading.Thread(target=controller, name='c1') 

    # starting threads
    e1.start()
    b1.start()
    c1.start()
  
    
    # wait until all threads finish   
    e1.join()
    b1.join()
    c1.join()