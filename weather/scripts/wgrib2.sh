#!/bin/sh
#SBATCH --job-name=wgrib2
# set the output and error files - default in slurm is to put both
# output and errors into slurm-<Job-ID>
#SBATCH -o wgrib2.out
#SBATCH -e wgrib2.err
# set the partition (a queue in SGE)
# request the use of 1 core
#SBATCH -n 1
source ~/.bashrc
cd /home/vulcanomod/Operational_modelling/weather/scripts

