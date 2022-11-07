# Python program to illustrate the concept
# of threading
import numpy as np
import queue
import threading

import os
import time
 
N_iter = 10
N_floors = 5
sleep_sec = 2
#elevator_btns = [0 for i in range(N_floors)]
elevator_btns = np.zeros(N_floors)
floor_up_btns = [0 for i in range(N_floors)]
floor_dn_btns = [0 for i in range(N_floors)]
#print("elevator_btns[2]=", elevator_btns[2])
target_floor = 2
floor_queue = queue.Queue()


def elevator_car():
   print("\nelevator_thread task assigned to thread: {}".format(threading.current_thread().name))
   print("\nID of process running elevator_thread: {}".format(os.getpid()))
   i = 0
   state = "stopped"
   curr_floor = 0
   while(1):
      i += 1
      print (f"\ni={i:d}\n")
      
      print ("\nread buttons:")
      target_floor = floor_queue.get()
    
      print ("current state=", state)
  

      print ("target_floor=", target_floor)
      
      if (state=="stopped"):
         print("stopped")
      if (target_floor>curr_floor):
         while(curr_floor!=target_floor):
            state="moving up"
            if (state=="moving up"):
               curr_floor += 1
               print("moving up, curr_floor=", curr_floor)
               time.sleep(sleep_sec)
            if (curr_floor==target_floor):
               state="stopped"
               print("stopped on floor=", curr_floor)
               time.sleep(sleep_sec)
      if (target_floor<curr_floor):
         while(curr_floor!=target_floor):
            state="moving dn"
            if (state=="moving dn"):
               curr_floor -= 1
               print("moving dn, curr_floor=", curr_floor)
               time.sleep(sleep_sec)
            if (curr_floor==target_floor):
               state="stopped"
               print("stopped on floor=", curr_floor)
               time.sleep(sleep_sec)
def elevator_buttons():

   print("\Elevator buttons assigned to thread: {}".format(threading.current_thread().name))
   print("ID of process running task 2: {}".format(os.getpid()))
   j = 0
   while(1):
      j += 1      
      print(f"\nj={j:d}")
      f = input("Input floor number:\n")
      f = int(f)
      floor_queue.put(f)      

         

if __name__ == "__main__":
    # print ID of current process
    print("ID of process running main program: {}".format(os.getpid()))

    # print name of main thread
    print("Main thread name: {}".format(threading.current_thread().name))
 

    # creating threads
    e1 = threading.Thread(target=elevator_car, name='e1')
    b1 = threading.Thread(target=elevator_buttons, name='b1')  
 

    # starting threads
    e1.start()
    b1.start()
 
    # wait until all threads finish   
    e1.join()
    b1.join()