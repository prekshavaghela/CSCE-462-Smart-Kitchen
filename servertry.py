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
import statistics

HOST= '10.136.104.175' #'10.136.104.154' #
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

def quadrantsSeperate(data):
    
    data = amg.pixels
    
    bot_right = [data[4][4:], data[5][4:],data[6][4:],data[7][4:]]
    bot_left = [data[4][:4], data[5][:4],data[6][:4],data[7][:4]]
    top_right = [data[0][4:], data[1][4:],data[2][4:],data[3][4:]]
    top_left = [data[0][:4], data[1][:4],data[2][:4],data[3][:4]]
    
    #print(top_right, top_left)
    
    tempBR = quad_temp_check(bot_right)
    tempBL = quad_temp_check(bot_left)
    tempTR = quad_temp_check(top_right)
    tempTL = quad_temp_check(top_left)
    
    ##print( ("TEMPERATURES IN ALL QUADRANTS {0:.1f}, {1:.1f}, {2:.1f}, {3:.1f}").format( tempTR, tempTL, tempBR, tempBL) )
    
    return tempTR, tempTL, tempBR, tempBL

def quad_temp_check(side):
    avgTemp = 0
     
    for row in range(len(side)):
        for temp in range(len(side[row])):
            avgTemp += side[row][temp]
    #print(avgTemp)        
    return avgTemp/16

def number_read_change(prevData):
    
    data = amg.pixels
    dataTransformed = amg.pixels
#     print(prevData, data)
    maxVal= data[0][0]
    
    hotOrNot = False
    avgTemp = 0
    for row in range(len(data)):
        for temp in range(len(data[row])):
            avgTemp += data[row][temp]
            maxVal = max(maxVal, data[row][temp])
            #if temperature is above 300 degrees and stays above 300 for a while it is 100% on
            if(data[row][temp] > 100):
                hotOrNot = True
                print("Stove is HOT... determining if it is on")
                #dataTransformed[row][temp] = 1
                
            if( data[row][temp] - prevData[row][temp] == 0):
                dataTransformed[row][temp] =0
            elif(  1 > data[row][temp] - prevData[row][temp] > 0):
                dataTransformed[row][temp] =0
            elif 0 < prevData[row][temp] - data[row][temp] < 1:
                dataTransformed[row][temp] =0
            elif( data[row][temp] - prevData[row][temp] > 1 ):
                #temperature is increasing
                #print(data[row][temp], prevData[row][temp])
                dataTransformed[row][temp] = 1
            elif ( prevData[row][temp] - data[row][temp] > 1):
                #temperature is decreasing
                dataTransformed[row][temp] = -1
            
    #print(maxVal)
    #print(dataTransformed)
    return [data, dataTransformed, avgTemp/64, hotOrNot, maxVal]

def maxTempVals(tempVals):
    if( tempVals[0] == max(tempVals) ):
        #tempTR,
        return("bottom left quadrant most likely heat source.")
    elif( tempVals[1] == max(tempVals) ):
        #tempTL,
        return("top left quadrant most likely heat source.")
    elif( tempVals[2] == max(tempVals) ):
        #tempBR,
        return("bottom right quadrant most likely heat source.")
    else:
        return("top left quadrant most likely on heat source.")
        #tempBL
        
def is_incr_or_decr(data, hotOrNot, tempVals, maxVals):
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
    
    print(countIncr, countDecr, countSame)
    ##the issue we are running into is that the decrease is happening at a slower rate!!
#     if( len(maxVals) > 10):
#         if abs(maxVals[len(maxVals) -1]) > 400 and abs(maxVals[len(maxVals) -1] - maxVals[len(maxVals) -10] ):
#             return "stove on and dangerously high"
#
    if max(tempVals) > 100:
        x = maxTempVals(tempVals)
        return x + ": stove on and dangerous heat"
    
    
    if countDecr == max(countIncr, countDecr, countSame) and countDecr > 30:
        return "stove not on" #decreasing
    
    elif countIncr == max(countIncr, countDecr, countSame) and countIncr > 12:
        #maxTempVals(tempVals)
        return "stove on"
    
    
    elif countIncr < 3:
        return "stove not on " #(no incr)
    elif countDecr <= 6:
        x = maxTempVals(tempVals)
        return x + " stove on" # (no decr)"
    elif countSame > 45 and hotOrNot:
        return "stove temperature constant"
#     if countDecr + countSame > countIncr:
#         return "stove not on"
    
#     if countSame == max(countIncr, countDecr, countSame):
#         return "constant"
    x = maxTempVals(tempVals)
    return x + " inconsistent reading... recalculating"
#    return "constant {} {} {} ".format(countIncr, countDecr, countSame)
    
def getAvgTemp(data):
    avgTemp = 0
    for row in range(len(data)):
        for temp in range(len(data[row])):
            avgTemp += data[row][temp]
    
    return avgTemp/64
            
def server2():
    f = open("/home/pi/stoveTry1.csv", "w")
    
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
                                            
                        stringResults = ""
                        count=0
                        prevData = amg.pixels
                        
                        startTime = time.time()
                        #print(prevData)
                        
                        prevArray = []
                        prevArray.append(prevData)
                        prevTempReading = []
                    #     prevTempReading.append(
                        prevTimes = []
                    #     prevTimes.append(0)
                        #get an moving average
                        countIncr = 0
                        countDecr = 0
                        countSame = 0
                        maxVals = []
                        
                        while count< 200:
                            if( len(prevArray) > 40):
                                my_data, change, avgTemp, hotOrNot, maxVal = number_read_change(prevArray[len(prevArray)-40] )
                                
                                
                                if( len(maxVals) > 3):
                                    avgValMax = statistics.mean(maxVals)
                                    stdAvgVal = statistics.stdev(maxVals)
                                    
                                    if( avgValMax - 2*stdAvgVal < maxVal < avgValMax - 2*stdAvgVal):
                                        maxVals.append(maxVal)
                                else:
                                    maxVals.append(maxVal)
                                    
                                if hotOrNot:
                                    stringResults += "stove temperature extremely HOT"
                                    stringResults += "\n"
                                tempVals = quadrantsSeperate(my_data)
                                #print(tempVals)tempTR, tempTL, tempBR, tempBL
                                temperatureStr = ("TEMPERATURES IN TOP RIGHT: {0:.1f}, TEMPERATURES IN TOP LEFT: {1:.1f},TEMPERATURES IN BOTTOM RIGHT: {2:.1f}, TEMPERATURES IN BOTTOM LEFT: {3:.1f}").format( tempVals[0],  tempVals[1],  tempVals[2],  tempVals[3])
                                stringResults += temperatureStr
                                stringResults += "\n"
                                
                                valString = is_incr_or_decr(change, hotOrNot, tempVals, maxVals)
                                print(valString,"- Stove temperature: {0:.1f} degrees Celcius".format(avgTemp))
                                stringResults += valString
                                stringResults += "- Stove temperature: {0:.1f} degrees Celcius".format(avgTemp)
                                stringResults += "\n"
                                
                                prevData= my_data
                                
                            else:
                                print("Analyzing the stove's current conditions")
                                prevData = amg.pixels
                                avgTemp = getAvgTemp(prevData)
                                stringResults += "Calibrating the stoves current conditons for 20 seconds"
                                stringResults += "\n"
                                
                            prevArray.append(prevData)
                            prevTempReading.append(avgTemp)
                            prevTimes.append( time.time() - startTime)
                            
                    #         f.write(my_data)
                    #         f.write("\n")
                            #print(my_data)
                            #print(change)
                            
                            print()
                            time.sleep(0.5)
                            count+=1
                            
                        
                            encoded_data = stringResults.encode('utf-8')
                            conn.sendall(encoded_data)
                            print(stringResults)
                            stringResults = ""
                    
                    
                    elif str(data) == "Quit":
                        return
                    
                    if not data:
                        pass
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
                        
                        my_data = server2()
                        
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