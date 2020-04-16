#!/bin/sh
#SBATCH --job-name=post_processing
# set the output and error files - default in slurm is to put both
# output and errors into slurm-<Job-ID>
#SBATCH -o post_processing.txt
#SBATCH -e post_processing.err
# set the partition (a queue in SGE)
#SBATCH -p defq
#SBATCH --time=18:00:00
# request the use of 6 cores
#SBATCH -n 6
#export DISPLAY=10.141.255.254:12 
source ~/.bashrc
conda activate ash_model_plotting
export MYAPP=python
FLAGS=$1
echo "$MYAPP $FLAGS"                                 
$MYAPP $FLAGS                                 
