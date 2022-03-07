#!/bin/sh
#SBATCH --job-name=HYSPLIT
## set the output and error files - default in slurm is to put both
## output and errors into slurm-<Job-ID>
#SBATCH -o hysplit.out
#SBATCH -e hysplit.err
## set the partition (a queue in SGE)
## request the use of 14 core
#SBATCH -n 16
#SBATCH -N 1
source ~/.bashrc
