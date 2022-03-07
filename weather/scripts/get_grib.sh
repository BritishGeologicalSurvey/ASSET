#!/bin/sh
#SBATCH --job-name=get_grib
## set the output and error files - default in slurm is to put both
## output and errors into slurm-<Job-ID>
#SBATCH -o get_grib.out
#SBATCH -e get_grib.err
## set the partition (a queue in SGE)
## request the use of 1 core
#SBATCH -n 108
source ~/.bashrc
cd /home/vulcanomod/Operational_modelling/weather/scripts
conda activate ash_dispersion_modelling

