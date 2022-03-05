#!/bin/sh
#SBATCH --job-name=get_grib
## set the output and error files - default in slurm is to put both
## output and errors into slurm-<Job-ID>
#SBATCH -o get_grib.out
#SBATCH -e get_grib.err
## set the partition (a queue in SGE)
## request the use of 1 core
#SBATCH -n 1
source ~/.bashrc
conda activate ash_dispersion_modelling

