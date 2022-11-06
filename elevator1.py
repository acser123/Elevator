# Python program to illustrate the concept
# of threading

import threading

import os
 
N_iter = 10
N_floors = 5
elevator_btns = [0 for i in range(N_floors)]
floor_up_btns = [0 for i in range(N_floors)]
floor_dn_btns = [0 for i in range(N_floors)]
#print("elevator_btns[2]=", elevator_btns[2])
target_floor = 2

def elevator_car():
   print("\nelevator_thread task assigned to thread: {}".format(threading.current_thread().name))
   print("\nID of process running elevator_thread: {}".format(os.getpid()))
   i = 0
   state = "stopped"
   curr_floor = 0
   while(i<N_iter):
      i += 1
      print (f"\ni={i:d}\n")
      print ("\nread buttons")
      print ("current state=", state)
      if (state=="stopped"):
         print("stopped")
         if (elevator_btns[target_floor]==1 and curr_floor!=target_floor):
            state="moving up"
      if (state=="moving up"):
         curr_floor += 1
         print("moving up, curr_floor=", curr_floor)
         if (curr_floor==target_floor):
            state="stopped"
            elevator_btns[target_floor]=0
            print("stopped on floor=", curr_floor)
      #print("\nif stopped  then decide direction and get moving")
      #print("\nif moving and between floors then decide stop on next floor")
      #print("\nif stopped then write buttons")

def elevator_buttons():

   print("\Elevator buttons assigned to thread: {}".format(threading.current_thread().name))
   print("ID of process running task 2: {}".format(os.getpid()))
   j = 0
   while(j<N_iter):
      j += 1      
      print(f"\nj={j:d}")
      if (elevator_btns[target_floor]==0):
         print("pushing elevator_button[target_floor]")
         elevator_btns[target_floor]=1          

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