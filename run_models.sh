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
python weather.py > log/log_weather_$shr.txt # Download weather data
python control.py --set=True > log/log_models_$shr.txt # Add options
conda deactivate
python post_processing.py --set=True --mode=operational > log/log_post_processing_$shr.txt
cp /home/vulcanomod/BGS-AADM/weather/scripts/*.sh weather/scripts/

