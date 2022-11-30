#imports to send data
import socket
import numpy as np
import encodings
import RPi.GPIO as GPIO
import matplotlib.pyplot as plt
#import for thermal camera
import board
import busio
import time
import adafruit_amg88xx
import copy

HOST= '10.136.104.173' #'10.136.104.154' #
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

##input is the side currently and the same side/quadrant before
def getDataTransformed(side, prevData):
     
     #print("side", side)
     hotOrNot = False
     avgTemp = 0
     dataTransformed = copy.deepcopy(side)
     
     for row in range(len(side)):
        for temp in range(len(side[row])):
            avgTemp += side[row][temp]
            #if temperature is above 300 degrees and stays above 300 for a while it is 100% on
            if(side[row][temp] > 200):
                hotOrNot = True
                print("Stove is HOT... determining if it is on")
                #dataTransformed[row][temp] = 1
                
            if( side[row][temp] - prevData[row][temp] == 0):
                dataTransformed[row][temp] =0
            elif(  3 > side[row][temp] - prevData[row][temp] > 0):
                dataTransformed[row][temp] =0
            elif 0 < prevData[row][temp] - side[row][temp] < 1:
                dataTransformed[row][temp] =0
            elif( side[row][temp] - prevData[row][temp] > 3 ):
                #temperature is increasing
                #print(side[row][temp], prevData[row][temp])
                dataTransformed[row][temp] = 1
            elif ( prevData[row][temp] - side[row][temp] > 1):
                #temperature is decreasing
                dataTransformed[row][temp] = -1
     
     #print(dataTransformed, side)
     return [dataTransformed, avgTemp/16, hotOrNot]
            
            
def quadrantsSeperate(prevData):
    
    data = amg.pixels
    
    bot_right = [data[4][4:], data[5][4:],data[6][4:],data[7][4:]]
    bot_left = [data[4][:4], data[5][:4],data[6][:4],data[7][:4]]
    top_right = [data[0][:4], data[1][:4],data[2][:4],data[3][:4]]
    top_left = [data[0][:4], data[1][:4],data[2][:4],data[3][:4]]
    
    dataTransformedBR, avgTempBR, hotOrNotBR =getDataTransformed(bot_right,prevData[2])
    dataTransformedBL, avgTempBL, hotOrNotBL = getDataTransformed(bot_left, prevData[3])
    dataTransformedTR, avgTempTR, hotOrNotTR = getDataTransformed(top_right, prevData[0])
    dataTransformedTL, avgTempTL, hotOrNotTL = getDataTransformed(top_left, prevData[1])
    
    incrBR = is_incr_or_decr(dataTransformedBR, hotOrNotBR)
    incrTR = is_incr_or_decr(dataTransformedTR, hotOrNotTR)
    incrBL = is_incr_or_decr(dataTransformedBL, hotOrNotBL)
    incrTL = is_incr_or_decr(dataTransformedTL, hotOrNotTL)
    
    print("the top right quadrant is", incrTR,  ("- Stove temperature: {0:.1f} degrees Celcius").format(avgTempTR) )
    print("the top left quadrant is", incrTL,  ("- Stove temperature: {0:.1f} degrees Celcius").format(avgTempTL))
    print("the bottom right quadrant is", incrBR,  ("- Stove temperature: {0:.1f} degrees Celcius").format(avgTempBR) )
    print("the bottom left quadrant is", incrBL, ("- Stove temperature: {0:.1f} degrees Celcius").format(avgTempBL))
    
    
    return [top_right, top_left, bot_right, bot_left]
    
    #return [data, dataTransformed, avgTemp/64, hotOrNot]
def calibrateQuadrants():
    data = amg.pixels
    
    bot_right = [data[4][4:], data[5][4:],data[6][4:],data[7][4:]]
    bot_left = [data[4][:4], data[5][:4],data[6][:4],data[7][:4]]
    top_right = [data[0][:4], data[1][:4],data[2][:4],data[3][:4]]
    top_left = [data[0][:4], data[1][:4],data[2][:4],data[3][:4]]
    
    
    return [top_right, top_left, bot_right, bot_left], getAvgTemp(data)
# def number_read_change(prevData):
#     
#     data = amg.pixels
#     quadrantsSeperate(data)
#     dataTransformed = amg.pixels
# #     print(prevData, data)
#     hotOrNot = False
#     avgTemp = 0
#     for row in range(len(data)):
#         for temp in range(len(data[row])):
#             avgTemp += data[row][temp]
#             #if temperature is above 300 degrees and stays above 300 for a while it is 100% on
#             if(data[row][temp] > 200):
#                 hotOrNot = True
#                 print("Stove is HOT... determining if it is on")
#                 #dataTransformed[row][temp] = 1
#                 
#             if( data[row][temp] - prevData[row][temp] == 0):
#                 dataTransformed[row][temp] =0
#             elif(  3 > data[row][temp] - prevData[row][temp] > 0):
#                 dataTransformed[row][temp] =0
#             elif 0 < prevData[row][temp] - data[row][temp] < 1:
#                 dataTransformed[row][temp] =0
#             elif( data[row][temp] - prevData[row][temp] > 3 ):
#                 #temperature is increasing
#                 #print(data[row][temp], prevData[row][temp])
#                 dataTransformed[row][temp] = 1
#             elif ( prevData[row][temp] - data[row][temp] > 1):
#                 #temperature is decreasing
#                 dataTransformed[row][temp] = -1
#             
#             
#     return [data, dataTransformed, avgTemp/64, hotOrNot]


def is_incr_or_decr(data, hotOrNot):
    countIncr = 0
    countDecr = 0
    countSame = 0
    
    for row in range(len(data)):
        for temp in range(len(data[row])):
            if data[row][temp] == 0:
                countSame +=1
            if data[row][temp] == 1:
                countIncr +=1
            if data[row][temp] == -1:
                countDecr +=1
    
    ##the issue we are running into is that the decrease is happening at a slower rate!!
    if countDecr == max(countIncr, countDecr, countSame) and countDecr > 30:
        return "stove not on" #decreasing
    
    elif countIncr == max(countIncr, countDecr, countSame) and countIncr > 30:
        return "stove on"
    
    elif countSame > 50 and hotOrNot:
        return "stove temperature constant"
    
    elif countIncr < 4:
        return "stove not on " #(no incr)
    elif countDecr < 4:
        return "stove on" # (no decr)"
#     if countDecr + countSame > countIncr:
#         return "stove not on"
    
#     if countSame == max(countIncr, countDecr, countSame):
#         return "constant"
    return "inconsistent reading... recalculating"
#    return "constant {} {} {} ".format(countIncr, countDecr, countSame)
    
def getAvgTemp(data):
    avgTemp = 0
    for row in range(len(data)):
        for temp in range(len(data[row])):
            avgTemp += data[row][temp]
    
    return avgTemp/64
            
def server2():
    f = open("/home/pi/stoveTry1.csv", "w")
    count=0
    prevData = amg.pixels
    
    startTime = time.time()
    print(prevData)
    
    prevArray = []
#     prevArray.append(prevData)
    prevTempReading = []
#     prevTempReading.append(
    prevTimes = []
#     prevTimes.append(0)
    #get an moving average
    countIncr = 0
    countDecr = 0
    countSame = 0
    
    while count< 200:
        
        if( len(prevArray) > 40):
            my_data = quadrantsSeperate(prevArray[len(prevArray)-40] )
            prevData= my_data
            
            
        else:
            print("Analyzing the stove's current conditions")
            prevData, avgTemp = calibrateQuadrants()
            

        
        prevArray.append(prevData)
        prevTempReading.append(avgTemp)
        prevTimes.append( time.time() - startTime)
        
#         f.write(my_data)
#         f.write("\n")
        #print(my_data)
        #print(change)
        
        
        time.sleep(0.5)
        count+=1
        
    
    plt.plot(prevTimes,prevTempReading)
    plt.title("change in temperature over time")
    plt.xlabel("time")
    plt.ylabel("temperature (C)")
    plt.show()
    f.close()
    
    
#    print(
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
    while count < 2:
        GPIO.output(led_pin, GPIO.HIGH) # Turn LED on
        time.sleep(1)                   # Delay for 1 second
        GPIO.output(led_pin, GPIO.LOW)  # Turn LED off
        time.sleep(1)
        count+=1# Delay for 1 second


    GPIO.cleanup()
    server2()
#    my_server()