import socket
import threading
import time



HOST = "10.136.104.175" #"10.168.1.39" #  # The server's hostname or IP address
PORT = 65432      # The port used by the server




#f = open("prekshaTry7.csv", "w")

def my_client():

    # Define Threadding to run after every 11 seconds
    # dont send Request to often or you will crash server

    threading.Timer(11, my_client).start()
    #print("not connected yet")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:        # define socket TCP
        s.connect((HOST, PORT))

        #print("connected")
        #my_inp = input("Enter command ")
        my_inp = "Data"
        #count =0

        while True:
            my_inp = "Data"
            # encode the message
            my_inp = my_inp.encode('utf-8')

            # send request ti server
            s.sendall(my_inp)

            # Get the Data from Server and process the Data
            data = s.recv(1024).decode('utf-8')

            # Process the data i mean split comma seperated value
           #
            
            print(data)
            print("\n")
            #my_inp = input("Enter command ")

        
        s.close()
        time.sleep(5)
        f.close()

        


if __name__ == "__main__":

    my_client()
    
    f.close()