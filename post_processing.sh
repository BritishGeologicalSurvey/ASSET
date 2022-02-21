#!/bin/sh
#SBATCH --job-name=post_processing
# set the output and error files - default in slurm is to put both
# output and errors into slurm-<Job-ID>
#SBATCH -o post_processing.txt
#SBATCH -e post_processing.err
# set the partition (a queue in SGE)
#SBATCH -p defq
#SBATCH --time=18:00:00
# request the use of 16 core
#SBATCH -n 16
source ~/.bashrc
conda activate ash_model_plotting
export MYAPP=python
FLAGS=$1
echo "$MYAPP $FLAGS"                                 
$MYAPP $FLAGS                                 
mv cdo.txt log/
mv post_processing.err log/
mv post_processing.txt log/
