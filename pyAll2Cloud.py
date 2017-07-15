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

    if len(sys.argv)==1:
        parser.print_help()
        sys.exit(1)
    
    args = parser.parse_args()

    # print ("processing with settings: ", args)
    for filename in glob(args.inputFile):
        if not filename.endswith('.all'):
            print ("File %s is not a .all file, skipping..." % (filename))
            continue

        convert(filename)


def convert(fileName):    
    recCount = 0

    r = pyall.ALLReader(fileName)
    eprint("loading navigation...")
    navigation = r.loadNavigation()
    eprint("done.")

    arr = np.array(navigation)
    times = arr[:,0]
    latitudes = arr[:,1]
    longitudes = arr[:,2]

    start_time = time.time() # time the process

    while r.moreData():
        TypeOfDatagram, datagram = r.readDatagram()
        if (TypeOfDatagram == 'X') or (TypeOfDatagram == 'D'):
            datagram.read()
            recDate = r.currentRecordDateTime()

            if datagram.NBeams > 1:
                # interpolate so we know where the ping is located
                lat = np.interp(pyall.to_timestamp(recDate), times, latitudes, left=None, right=None)
                lon = np.interp(pyall.to_timestamp(recDate), times, longitudes, left=None, right=None)
                # for each beam in the ping, compute the real world position
                for i in range(len(datagram.Depth)):
                    #native python version are faster than numpy
                    brg = 90 - (180/math.pi)*math.atan2(datagram.AlongTrackDistance[i], datagram.AcrossTrackDistance[i])
                    rng = math.sqrt((datagram.AcrossTrackDistance[i]*datagram.AcrossTrackDistance[i])+(datagram.AlongTrackDistance[i]* datagram.AlongTrackDistance[i]))
                    x,y,h = geodetic.calculateGeographicalPositionFromRangeBearing(lat, lon, brg + datagram.Heading, rng)
                    print ("%.10f, %.10f, %.3f" % (y, x, datagram.Depth[i] + datagram.TransducerDepth))
            recCount = recCount + 1

    r.close()
    eprint("Duration %.3fs" % (time.time() - start_time )) # time the process

    return navigation


def update_progress(job_title, progress):
    length = 20 # modify this to change the length
    block = int(round(length*progress))
    msg = "\r{0}: [{1}] {2}%".format(job_title, "#"*block + "-"*(length-block), round(progress*100, 2))
    if progress >= 1: msg += " DONE\r\n"
    sys.stdout.write(msg)
    sys.stdout.flush()

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

if __name__ == "__main__":
    main()

