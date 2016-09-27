import sys
sys.path.append("C:/development/Python/pyall")

import argparse
from datetime import datetime
import geodetic
from glob import glob
import math
# import numpy as np
import pyall
import time
import os.path
import warnings

# ignore numpy NaN warnings when applying a mask to the images.
warnings.filterwarnings('ignore')

def main():
    parser = argparse.ArgumentParser(description='Read Kongsberg ALL file and create a point cloud file from DXYZ data.')
    parser.add_argument('-i', dest='inputFile', action='store', help='-i <ALLfilename> : input ALL filename to image. It can also be a wildcard, e.g. *.all')

    if len(sys.argv)==1:
        parser.print_help()
        sys.exit(1)
    
    args = parser.parse_args()

    print ("processing with settings: ", args)
    for filename in glob(args.inputFile):
        # navigation = convert(filename)
        navigation = loadNavigation(filename)

def convert(fileName):    
    '''compute the approximate across and alongtrack resolution so we can make a nearly isometric Image'''
    '''we compute the across track by taking the average Dx value between beams'''
    '''we compute the alongtracks by computing the linear length between all nav updates and dividing this by the number of pings'''
    xResolution = 1
    YResolution = 1
    prevLong = 0 
    prevLat = 0
    r = pyall.ALLReader(fileName)
    recCount = 0
    acrossMeans = np.array([])
    alongIntervals = np.array([])
    leftExtents = np.array([])
    rightExtents = np.array([])
    beamCount = 0
    distanceTravelled = 0.0
    navigation = []
    selectedPositioningSystem = None
    start_time = time.time() # time the process

    while r.moreData():
        TypeOfDatagram, datagram = r.readDatagram()
        if (TypeOfDatagram == 'P'):
            datagram.read()
            if (selectedPositioningSystem == None):
                selectedPositioningSystem = datagram.Descriptor
            if (selectedPositioningSystem == datagram.Descriptor):
                if prevLat == 0:
                    prevLat =  datagram.Latitude
                    prevLong =  datagram.Longitude
                range,bearing1, bearing2  = geodetic.calculateRangeBearingFromGeographicals(prevLong, prevLat, datagram.Longitude, datagram.Latitude)
                # print (range,bearing1)
                distanceTravelled += range
                navigation.append([recCount, r.currentRecordDateTime(), datagram.Latitude, datagram.Longitude])
                prevLat =  datagram.Latitude
                prevLong =  datagram.Longitude
        # if (TypeOfDatagram == 'X') or (TypeOfDatagram == 'D'):
        #     datagram.read()
        #     if datagram.NBeams > 10000000000:
        #         acrossMeans = np.append(acrossMeans, np.average(np.diff(np.asarray(datagram.AcrossTrackDistance))))
        #         leftExtents = np.append(leftExtents, datagram.AcrossTrackDistance[0])
        #         rightExtents = np.append(rightExtents, datagram.AcrossTrackDistance[-1])
        #         recCount = recCount + 1
        #         beamCount = max(beamCount, len(datagram.Depth)) 
            
    r.close()
    if recCount == 0:
        return 0,0,0,0,0,[] 
    xResolution = np.average(acrossMeans)
    # distanceTravelled = 235
    yResolution = distanceTravelled / recCount
    print(    start_time = time.time() # time the process
)
    return navigation

def update_progress(job_title, progress):
    length = 20 # modify this to change the length
    block = int(round(length*progress))
    msg = "\r{0}: [{1}] {2}%".format(job_title, "#"*block + "-"*(length-block), round(progress*100, 2))
    if progress >= 1: msg += " DONE\r\n"
    sys.stdout.write(msg)
    sys.stdout.flush()

def loadNavigation(fileName):    
    '''loads all the navigation into lists'''
    start_time = time.time() # time the process
    navigation = []
    r = pyall.ALLReader(fileName)
    while r.moreData():
        TypeOfDatagram, datagram = r.readDatagram()
        if (TypeOfDatagram == 'P'):
            datagram.read()
            navigation.append([datagram.Time, datagram.Latitude, datagram.Longitude])
    r.close()
    print("Duration: %.2f" % (start_time - time.time())) # time the process
    return navigation

if __name__ == "__main__":
    main()

