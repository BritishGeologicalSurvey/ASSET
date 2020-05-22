#!/bin/bash
shr=$(date -u +%H)
if [ $shr -eq 0 ] || [ $shr -eq 6 ] || [ $shr -eq 12 ] || [ $shr -eq 18 ]; then
    echo $shr
else
    exit
fi

source ~/.bashrc
conda activate ash_dispersion_modelling
cd /home/vulcanomod/Operational_modelling/BGS-AADM
python weather.py > log/log_weather_$shr.txt # Download weather data
python control.py --set=True > log/log_models_$shr.txt # Add options
conda deactivate
sbatch post_processing.sh 'post_processing.py --set=True --mode=operational'
process_id=$!
wait $process_id
mv cdo.txt log/
mv post_processing.err log/
mv post_processing.txt log/
