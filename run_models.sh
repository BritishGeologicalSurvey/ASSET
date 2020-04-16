#!/bin/bash
shr=$(date -u +%H)
if [ $shr -eq 0 ] || [ $shr -eq 6 ] || [ $shr -eq 12 ] || [ $shr -eq 18 ]; then
    echo $shr
else
    exit
fi

source ~/.bashrc
conda activate ash_dispersion_modelling
cd /home/vulcanomod/Operational_modelling
/home/vulcanomod/anaconda3/bin/python weather.py > log/log_weather_$shr.txt # Download weather data
/home/vulcanomod/anaconda3/bin/python control.py --set=True > log/log_models_$shr.txt # Add options
conda deactivate
sbatch post_processing.sh 'post_processing.py --set=True --mode=operational'
mv post_processing.err log/
mv post_provessing.txt log/