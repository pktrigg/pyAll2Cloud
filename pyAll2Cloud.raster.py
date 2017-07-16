import sys
sys.path.append("C:/Python27/ArcGIS10.3/pyall-master")
sys.path.append("C:/development/python/pyall")

# import arcpy
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
from scipy.interpolate import griddata
from PIL import Image,ImageDraw,ImageFont, ImageOps, ImageChops
import shadedRelief as sr

gridXOrigin = 0
gridYOrigin = 0
gridResolution = 0

# ignore numpy NaN warnings when applying a mask to the images.
warnings.filterwarnings('ignore')

def main():
    start_time = time.time() # time the process
    parser = argparse.ArgumentParser(description='Read Kongsberg ALL file and create a point cloud file from DXYZ data.')
    parser.add_argument('-i', dest='inputFile', action='store', help='-i <ALLfilename> : input ALL filename to image. It can also be a wildcard, e.g. *.all')
    parser.add_argument('-o', dest='outputFile', action='store', help='-o <Geodatabase> : provide geodatabase to store the ESRI Raster')
    if len(sys.argv)==1:
        parser.print_help()
        sys.exit(1)
    
    args = parser.parse_args()

    print ("processing with settings: ", args)
    for filename in glob(args.inputFile):
        if not filename.endswith('.all'):
            print ("File %s is not a .all file, skipping..." % (filename))
            continue
        tdr = convert(filename)


        latitudes = tdr[:,0]
        longitudes = tdr[:,1]
        depths = tdr[:,2]

        miny = np.min(latitudes)
        maxy = np.max(latitudes)
        minx = np.min(longitudes)
        maxx = np.max(longitudes)

        gridXOrigin 

        # width = maxx - minx
        # height = maxy - miny
        # meanwidth = np.average(np.diff(np.sort(longitudes))) # calculate mean distance between soundings
        # meanheight = np.average(np.diff(np.sort(latitudes)))
        
        # meanwidth = meanwidth * 3 # we want at least 3 soundings per grid
        # meanheight = meanheight * 3

        # # hcells, wcells, meanwidth, meanheight = minimum_grid_size(width, height, meanwidth, meanheight)

        # if meanwidth < 0.0001:
        #     meanwidth = 0.0001
        # if meanheight < 0.0001:
        #     meanheight = 0.0001

        gridResolution = 0.1/111319.9
        wcells = int(math.ceil(width / gridResolution))
        hcells = int(math.ceil(height / gridResolution))


        xi = np.linspace(minx, maxx,  wcells)
        yi = np.linspace(miny, maxy,  hcells)

        grid_x, grid_y = np.meshgrid(xi, yi, indexing = 'ij')

        grid_z1 = griddata((longitudes, latitudes), depths, (grid_x, grid_y), method='linear', fill_value=18.0)

        print ("Hillshading...")
        #Create hillshade a little brighter and invert so hills look like hills
        colorMap = None
        hs = sr.calcHillshade(grid_z1, 1, 45, 30)
        img = Image.fromarray(hs).convert('RGBA')
        img.save(os.path.splitext(filename)[0]+'_cloud.png')
        print ("Saved to: ", os.path.splitext(filename)[0]+'_cloud.png')
                

        # depths = np.ones((hcells, wcells), np.float32)
        # depths = depths * -9999

        # esri_min_point = arcpy.Point(minx, miny)

        # er = float(minx)
        # ec = float(miny)

        # for x in range(wcells):
        #     rows = np.where((tdr[:,1] > (er-(meanwidth/2))) & (tdr[:,1] < (er+(meanwidth/2))))
        #     for y in range(hcells-1, 0, -1):
        #         columns = np.where((tdr[:,0] > (ec-(meanheight/2))) & (tdr[:,0] < (ec+(meanheight/2))))
        #         match = np.intersect1d(rows[0], columns[0], True)
        #         if np.size(match) > 0:
        #             depths[y, x] = float(np.average(tdr[(match,2)]))
        #         ec = ec + meanheight
        #         print "y: " + str(y) + " of " + str(hcells) + ", " + "x: " + str(x) + " of " + str(wcells) + ":" + str(er) + "," + str(ec)
        #     ec = float(miny)
        #     er = er + meanwidth
        #     print "y: " + str(y) + " of " + str(hcells) + ", " + "x: " + str(x) + " of " + str(wcells) + ":" + str(er) + "," + str(ec)
        # esriarray = np.array(depths)








        # myRaster = arcpy.NumPyArrayToRaster(esriarray, esri_min_point, meanwidth, meanheight, -9999)
        # myRaster.save("C:/Python27/ArcGIS10.3/TemplateSSDM_WGS84_LL/GIS/FGDB/TemplateSSDM_WGS84_LL.gdb/pythonRaster")


def convert(filename):    
    recCount = 0
    prevLong = 0 
    prevLat = 0
    distanceTravelled = 0.0

    r = pyall.ALLReader(filename)
    navigation = r.loadNavigation()

    arr = np.array(navigation)
    times = arr[:,0]
    latitudes = arr[:,1]
    longitudes = arr[:,2]

    output_array = []

    start_time = time.time() # time the process

    while r.moreData():
        TypeOfDatagram, datagram = r.readDatagram()
        if (TypeOfDatagram == 'X') or (TypeOfDatagram == 'D'):
            datagram.read()
            recDate = r.currentRecordDateTime()

            if datagram.NBeams > 1:
                # interpolate so we know where the ping is located
                lat = np.interp(get_timestamp(recDate), times, latitudes, left=None, right=None)
                lon = np.interp(get_timestamp(recDate), times, longitudes, left=None, right=None)
                
                if prevLat == 0:
                    prevLat =  lat
                    prevLong =  lon
                
                rng,bearing1, bearing2  = geodetic.calculateRangeBearingFromGeographicals(prevLong, prevLat, lon, lat)
                prevLat =  lat
                prevLong =  lon
                distanceTravelled += rng
                print ("%.3f, %.3f, %.3f" % (lat, lon, rng))
                # for each beam in the ping, compute the real world position
                for i in range(len(datagram.Depth)):
                    datagram.Depth[i] = datagram.Depth[i] + datagram.TransducerDepth
                    # we need to compute a vector range and bearing based on the Dx and dY
                    rng, brg = geodetic.calculateRangeBearingFromGridPosition(0,0,datagram.AcrossTrackDistance[i], datagram.AlongTrackDistance[i])
                    x,y,h = geodetic.calculateGeographicalPositionFromRangeBearing(lat, lon, brg + datagram.Heading, rng)
                    # print ("%.10f, %.10f, %.3f" % (x, y, datagram.Depth[i]))
                    output_array.append([float(x), float(y), float(datagram.Depth[i])])
            recCount = recCount + 1

            if recCount == 10:
                break
    r.close()
    yResolution = distanceTravelled / recCount
    print("Duration %.3fs" % (time.time() - start_time )) # time the process

    nparray = np.array(output_array)

    return nparray, yResolution

def xy2RowCol(x,y):
    '''convert from latitude longitude to matrix row and column'''
    col = int ((x - gridXOrigin / gridResolution))
    row = int ((y - gridYOrigin / gridResolution))
    return row,col

def update_progress(job_title, progress):
    length = 20 # modify this to change the length
    block = int(round(length*progress))
    msg = "\r{0}: [{1}] {2}%".format(job_title, "#"*block + "-"*(length-block), round(progress*100, 2))
    if progress >= 1: msg += " DONE\r\n"
    sys.stdout.write(msg)
    sys.stdout.flush()

def get_timestamp(recordDate):
    ts = time.mktime(recordDate.timetuple())
    return (recordDate - datetime(1970, 1, 1)).total_seconds()

def minimum_grid_size(width, height, meanwidth, meanheight):

    wcells = int(math.ceil(width / meanwidth))
    hcells = int(math.ceil(height / meanheight))
    try:
        depths = np.ones((hcells, wcells), np.float32)
        return hcells, wcells, meanwidth, meanheight
    except:
        print ("not enough memory, doubling grid size and trying again...")
        return minimum_grid_size(width, height, meanwidth*2, meanheight*2)

if __name__ == "__main__":
    main()

