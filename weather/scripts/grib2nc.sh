#!/bin/bash

TABLEFILE=/home/vulcanomod/FALL3D/fall3d-8.0.1/Other/Meteo/Utils/grib_utils/gfs_0p25.levels
OUTPUTFILE=operational.nc
GRIBDIR=.
t_start=$1

for i in $(seq -w $t_start 108)
do
    GRIBFILE="${GRIBDIR}/${i}-gfs_0p25.grb"
    echo "$GRIBFILE"
    if [ $i -eq 0 ]
    then
        wgrib2 $GRIBFILE -nc_table $TABLEFILE -nc3 -netcdf $OUTPUTFILE
    else
        wgrib2 $GRIBFILE -nc_table $TABLEFILE -append -nc3 -netcdf $OUTPUTFILE
    fi
done
