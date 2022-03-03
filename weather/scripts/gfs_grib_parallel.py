#!/usr/bin/env python
# -*- coding: UTF-8 -*-
""" 
Download GFS data required by FALL3D model. 
The NCEP operational Global Forecast System 
analysis and forecast grids are on a 0.25 by 0.25 
global latitude longitude grid. 
"""

import sys
import argparse
import configparser
from datetime import datetime 
from fall3dutil.grib_filter import GFS
from pathos.multiprocessing import ThreadingPool
import os
from shutil import which

timesteps = []
wtfiles_refir = []
gribfiles = []
arlfiles = []
HYSPLIT = '/home/vulcanomod/HYSPLIT'
API2ARL = os.path.join(HYSPLIT,'hysplit.v5.2.0','exec','api2arl_v4')

def lat_type(str):
    try:
        lat = float(str)
    except:
        raise argparse.ArgumentTypeError("invalid float value: '{0}'".format(str))

    if lat < -90 or lat > 90:
        raise argparse.ArgumentTypeError('latitude not in range -90..90')
    else:
        return lat

def lon_type(str):
    try:
        lon = float(str)
    except:
        raise argparse.ArgumentTypeError("invalid float value: '{0}'".format(str))

    if lon < -180 or lon > 360:
        raise argparse.ArgumentTypeError('longitude not in range -180..180 or 0..360')
    else:
        return lon

def date_type(s):
    try:
        return datetime.strptime(s, "%Y%m%d")
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)

def main():
    # Input parameters and options
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-x', '--lon',     help='longitude range [Default: %(default)s]',          default=(-180., 180.), nargs=2, type=lon_type,  metavar=('lonmin', 'lonmax'))
    parser.add_argument('-y', '--lat',     help='latitude range [Default: %(default)s]',           default=(-90., 90.),   nargs=2, type=lat_type,  metavar=('latmin', 'latmax'))
    parser.add_argument('-t', '--time',    help='time steps [Default: %(default)s]',               default=(0, 6),        nargs=2, type=int,       metavar=('tmin',   'tmax'))
    parser.add_argument('-r', '--res',     help='spatial resolution (deg) [Default: %(default)s]', default=0.25,                   type=float,     choices=(0.25, 0.5, 1.0) )
    parser.add_argument('-c', '--cycle',   help='cycle [Default: %(default)s]',                    default=0,                      type=int,       choices=(0,6,12,18))
    parser.add_argument('-s', '--step',    help='temporal resolution (h) [Default: %(default)s]',  default=1,                      type=int,       choices=(1, 3, 12))
    parser.add_argument('-a', '--area',    help='area name [Default: %(default)s]',                                                type=str,       metavar=('Area'))
    parser.add_argument('-i', '--input',   help='area definition file [Default: %(default)s]',     default='areas.def',            type=str,       metavar=('AreaFile'))
    parser.add_argument('-o', '--output',  help='output file [Default: FH-YYYYMMDD_HHz.grb]',      default='')
    parser.add_argument('-v', '--verbose', help="increase output verbosity", action="store_true")
    parser.add_argument('date',            help='Initial date in format YYYYMMDD',                                                 type=date_type, metavar='start_date')

    args = parser.parse_args()
    i = 0
    date = args.date.strftime("%Y%m%d")
    if args.cycle < 10:
        anl = '0' + str(args.cycle)
    else:
        anl = str(args.cycle)

    while i <= args.time[1]:
        timesteps.append(i)
        if i < 10:
            fcst = '00' + str(i)
        else:
            if i < 100:
                fcst = '0' + str(i)
            else:
                fcst = str(i)
        wtfiles_refir.append('weather_data_' + date + anl + '_f' + fcst)
        gribfiles.append(fcst + '-' + args.output + '.grb')
        arlfiles.append(fcst + '-' + args.output + '.arl')
        i += 1

    if args.area:
        print("Reading coordinates of {} from input file: {}".format(args.area,args.input))
        config = configparser.ConfigParser()
        config.read(args.input)
        block = config[args.area]
        args.lonmin = lon_type( block["lonmin"] )
        args.lonmax = lon_type( block["lonmax"] )
        args.latmin = lat_type( block["latmin"] )
        args.latmax = lat_type( block["latmax"] )
    else:
        args.lonmin = args.lon[0]
        args.lonmax = args.lon[1]
        args.latmin = args.lat[0]
        args.latmax = args.lat[1]

    if args.latmin > args.latmax:
        sys.exit("Error: Use '{-y,--lat} latmin latmax' or edit the area definition file "+args.input)

    if args.time[0] > args.time[1]:
        sys.exit("Error: Use '{-t,--time}' tmin tmax")

    if args.output:
        if not args.output.endswith('.grb'):
            args.output = args.output.strip() + '.grb'
    else:
        args.output = "{date}-{cycle:02d}z.grb".format(date  = args.date.strftime("%Y%m%d"), 
                                                       cycle = args.cycle)

    if args.res==0.25:
        if args.step != 1 and args.step != 3:
            print("wrong time step. setting to step=3")
            args.step=3
    elif args.res==0.5:
        if args.step != 3: 
            print("wrong time step. setting to step=3")
            args.step=3
    elif args.res==1.0:
        if args.step != 12:
            print("wrong time step. setting to step=12")
            args.step=12

    def launch_requests(time_step):
        args.time[0] = time_step
        args.time[1] = time_step
        request = GFS(args)
        request.save_data()

    def convert_to_arl(gribfile,arlfile):
        if which('sbatch') is None:
            os.system(API2ARL + ' -dapi2arl.cfg -i' + gribfile + ' -o' + arlfile)
        else:
            lines = []
            with open('api2arl.sh', 'r', encoding="utf-8", errors="surrogateescape") as api2arl_script:
                for line in api2arl_script:
                    if '$MYAPP' in line:
                        line = '$MYAPP -dapi2arl.cfg -i' + gribfile + ' -o' + arlfile
                    lines.append(line)
            with open('api2arl.sh', 'w', encoding="utf-8", errors="surrogateescape") as api2arl_script:
                api2arl_script.writelines(lines)
            os.system('sbatch api2arl.sh')

    pool = ThreadingPool(args.time[1]+1)
    pool.map(launch_requests,timesteps)

    pool = ThreadingPool(args.time[1]+1)
    pool.map(convert_to_arl,gribfiles,arlfiles)

if __name__ == '__main__':
    main()

for i in timesteps:
    os.system('cp ' + gribfiles[i] + ' ' + wtfiles_refir[i])  
