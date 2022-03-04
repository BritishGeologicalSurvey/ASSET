#!/bin/sh
#SBATCH --job-name=FALL3D
## set the output and error files - default in slurm is to put both
## output and errors into slurm-<Job-ID>
#SBATCH -o fall3d.txt
#SBATCH -e fall3d.err
## set the partition (a queue in SGE)
## request the use of 14 core
#SBATCH -n 64
source ~/.bashrc
