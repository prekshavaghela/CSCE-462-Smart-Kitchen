# calibration script
import time
import adafruit_amg88xx
import board
import busio

i2c = busio.I2C(board.SCL, board.SDA)
amg = adafruit_amg88xx.AMG88XX(i2c)



def number_read_change(prevData):
    
    data = amg.pixels
    dataTransformed = amg.pixels
#     print(prevData, data)
    hotOrNot = False
    avgTemp = 0
    for row in range(len(data)):
        for temp in range(len(data[row])):
            avgTemp += data[row][temp]
            #if temperature is above 300 degrees and stays above 300 for a while it is 100% on
            if(data[row][temp] > 200):
                hotOrNot = True
                print("Stove is HOT... determining if it is on")
                #dataTransformed[row][temp] = 1
                
            if( data[row][temp] - prevData[row][temp] == 0):
                dataTransformed[row][temp] =0
            elif(  3 > data[row][temp] - prevData[row][temp] > 0):
                dataTransformed[row][temp] =0
            elif 0 < prevData[row][temp] - data[row][temp] < 1:
                dataTransformed[row][temp] =0
            elif( data[row][temp] - prevData[row][temp] > 3 ):
                #temperature is increasing
                #print(data[row][temp], prevData[row][temp])
                dataTransformed[row][temp] = 1
            elif ( prevData[row][temp] - data[row][temp] > 1):
                #temperature is decreasing
                dataTransformed[row][temp] = -1
            
            
    return [data, dataTransformed, avgTemp/64, hotOrNot]


def is_incr(data, hotOrNot):
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
                
    return countIncr

def is_decr(data, hotOrNot):
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
                
    return countDecr

def getAvgTemp(data):
    avgTemp = 0
    for row in range(len(data)):
        for temp in range(len(data[row])):
            avgTemp += data[row][temp]
    
    return avgTemp/64


startScript = input("Make sure stove top is empty of all other items and surface is at room temperature. Once ready type 'yes'")

if startScript == ("yes" or "Y" or "Yes" or "YES"):
    
    
    onStove = input("Turn on stove. Leave the area that you want to detect unobstructed and ensure you are out of range. When ready type yes.")
    if onStove == ("yes" or "Y" or "Yes" or "YES"):
        print("Please leave this area unobstructed for the next 55 to 60 seconds")
        time.sleep(5)
        
        count=0
        prevData = amg.pixels
        avgTemp = getAvgTemp(prevData)
        firstData = avgTemp
        prevArray = []
        prevArray.append(prevData)
        maxCountDecr = 0
        
        while count< 100:
            if( len(prevArray) > 20):
                my_data, change, avgTemp, hotOrNot = number_read_change(prevArray[len(prevArray)-20] )
                maxCountDecr = max(maxCountDecr, is_decr(change, hotOrNot) )
                print(maxCountDecr)
                #print(valString,"- Stove temperature: {0:.1f} degrees Celcius".format(avgTemp))
                prevData= my_data
                
            else:
                print("Analyzing the stove's current conditions")
                prevData = amg.pixels
                avgTemp = getAvgTemp(prevData)
                
            prevArray.append(prevData)
            time.sleep(0.5)
            count+=1
            
        maxCountDecr = max(4, maxCountDecr)
        
        if maxCountDecr > 9:
                maxCountDecr = 9
                
        print(("when stove is on: calibrated max increase of {} points of interest").format(maxCountDecr) )
        
        print("now for the next stage of calibration")
        
        offStove = input("Turn OFF stove. Leave the area that you want to detect unobstructed and ensure you are out of range. When ready type yes.")
        
        if offStove == ("yes" or "Y" or "Yes" or "YES"):
            print("Please leave this area unobstructed for the next 55 to 60 seconds")
            time.sleep(5)
            
            count=0
            prevData = amg.pixels
            avgTemp = getAvgTemp(prevData)
            firstData = avgTemp
            prevArray = []
            prevArray.append(prevData)
            maxCountIncr = 0
            
            while count< 100:
                if( len(prevArray) > 20):
                    my_data, change, avgTemp, hotOrNot = number_read_change(prevArray[len(prevArray)-20] )
                    maxCountIncr = max(maxCountIncr, is_incr(change, hotOrNot) )
                    print(maxCountIncr)
                    #print(valString,"- Stove temperature: {0:.1f} degrees Celcius".format(avgTemp))
                    prevData= my_data
                    
                else:
                    print("Analyzing the stove's current conditions")
                    prevData = amg.pixels
                    avgTemp = getAvgTemp(prevData)
                    
                prevArray.append(prevData)
                time.sleep(0.5)
                count+=1
                
            maxCountIncr = max(4, maxCountIncr)
            
            if maxCountIncr > 9:
                maxCountIncr = 9
                
            
            print( ("when stove is off: calibrated max increase of {} points of interest").format(maxCountIncr) )
        else:
            print("Try again once stove is clear.")
        
    else:
        print("Try again once stove is clear.")
        
        
            
else:
    print("Try again once stove is clear.")
    
# find out that number 4 not the same for all stoves.
# 
# so.. user has to say they're testing increase first
# 
# user input: increasing
# 
# then they set up stove top from  cold to on. prompts user with instructions and we look at how much temperature is differing from sample to sample.  then we can define as 4 or whatever
# 
# then same for user input decreasing and we look at average temperature decrease per 20 second increments. 