import sys
sys.path.append("C:/development/Python/pyall")

import argparse
from datetime import datetime
import geodetic
from glob import glob
import math
import numpy as np
import pyall
import time
import os.path
import warnings

# ignore numpy NaN warnings when applying a mask to the images.
warnings.filterwarnings('ignore')

def main():
    start_time = time.time() # time the process
    parser = argparse.ArgumentParser(description='Read Kongsberg ALL file and create a point cloud file from DXYZ data.')
    parser.add_argument('-i', dest='inputFile', action='store', help='-i <ALLfilename> : input ALL filename to image. It can also be a wildcard, e.g. *.all')
    parser.add_argument('-t', dest='travelTime', action='store_true', help='-t enable travel time mode - output two way travel time rather than depth')

    if len(sys.argv)==1:
        parser.print_help()
        sys.exit(1)
    
    args = parser.parse_args()

    print ("processing with settings: ", args)
    for filename in glob(args.inputFile):
        if not filename.endswith('.all'):
            print ("File %s is not a .all file, skipping..." % (filename))
            continue

        convert(filename)


def convert(fileName):    
    recCount = 0

    r = pyall.ALLReader(fileName)
    navigation = r.loadNavigation()

    arr = np.array(navigation)
    times = arr[:,0]
    latitudes = arr[:,1]
    longitudes = arr[:,2]

    start_time = time.time() # time the process

    while r.moreData():
        TypeOfDatagram, datagram = r.readDatagram()
        if (travelTime):
            if (TypeOfDatagram == 'N'):
                datagram.read()
                travelTimeSwath = [0 for i in range(datagram.NumReceiveBeams)]
                for i in range(datagram.NumReceiveBeams):
                    travelTimeSwath[i] = datagram.TwoWayTravelTime[i]
        
        if (TypeOfDatagram == 'X') or (TypeOfDatagram == 'D'):
            datagram.read()
            recDate = r.currentRecordDateTime()

            if datagram.NBeams > 1:
                # interpolate so we know where the ping is located
                lat = np.interp(recDate.timestamp(), times, latitudes, left=None, right=None)
                lon = np.interp(recDate.timestamp(), times, longitudes, left=None, right=None)

                # for each beam in the ping, compute the real world position
                for i in range(len(datagram.Depth)):
                    datagram.Depth[i] = datagram.Depth[i] + datagram.TransducerDepth
                    # we need to compute a vector range and bearing based on the Dx and dY
                    rng, brg = geodetic.calculateRangeBearingFromGridPosition(0,0,datagram.AcrossTrackDistance[i], datagram.AlongTrackDistance[i])
                    x,y,h = geodetic.calculateGeographicalPositionFromRangeBearing(lat, lon, brg + datagram.Heading, rng)
                    if travelTime:
                        print ("%.10f, %.10f, %.3f" % (x, y, travelTimeSwath[i]))
                    else:
                        print ("%.10f, %.10f, %.3f" % (x, y, datagram.Depth[i]))
            recCount = recCount + 1
                
    r.close()
    print("Duration %.3fs" % (time.time() - start_time )) # time the process

    return navigation

def update_progress(job_title, progress):
    length = 20 # modify this to change the length
    block = int(round(length*progress))
    msg = "\r{0}: [{1}] {2}%".format(job_title, "#"*block + "-"*(length-block), round(progress*100, 2))
    if progress >= 1: msg += " DONE\r\n"
    sys.stdout.write(msg)
    sys.stdout.flush()

if __name__ == "__main__":
    main()

