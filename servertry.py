#imports to send data
import socket
import numpy as np
import encodings
import RPi.GPIO as GPIO

#import for thermal camera
import board
import busio
import time
import adafruit_amg88xx

HOST= '10.0.0.244' #'10.136.104.154'
PORT = 65432
i2c = busio.I2C(board.SCL, board.SDA)
amg = adafruit_amg88xx.AMG88XX(i2c)

def read_camera():
    data = ""
    for row in amg.pixels:
        for temp in row:
            data += "{0:.1f}".format(temp)
            data += ", "
        data +="\n"
    return data
    
def my_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen(5)
        print("ENTERED")
        
        while True:
            conn, addr = s.accept()
            print("true")
            
            with conn:
                print("connected by ", addr)
                while True:
                    data = conn.recv(1024).decode('utf-8')
                    
                    if str(data) == "Data":
#                         print("enters")
                        my_data = read_camera()
                        encoded_data = my_data.encode('utf-8')
                        conn.sendall(encoded_data)
                    
                    
                    elif str(data) == "Quit":
                        return
                    
                    if not data:
                        pass
                
if __name__== "__main__":
    led_pin = 12

    # Use "GPIO" pin numbering
    GPIO.setmode(GPIO.BCM)

    # Set LED pin as output
    GPIO.setup(led_pin, GPIO.OUT)
    # Blink forever
    count = 1
    while count < 5:
        GPIO.output(led_pin, GPIO.HIGH) # Turn LED on
        time.sleep(1)                   # Delay for 1 second
        GPIO.output(led_pin, GPIO.LOW)  # Turn LED off
        time.sleep(1)
        count+=1# Delay for 1 second


    GPIO.cleanup()
    my_server()