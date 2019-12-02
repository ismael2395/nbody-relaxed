#!/bin/bash
# The interpreter used to execute the script

#“#SBATCH” directives that convey submission options:

#SBATCH --job-name=download_trees
#SBATCH --mail-user=imendoza@umich.edu
#SBATCH --mail-type=BEGIN,END
#SBATCH --cpus-per-task=1
#SBATCH --nodes=4
#SBATCH --ntasks-per-node=4
#SBATCH --mem-per-cpu=1G
#SBATCH --time=10:00:00
#SBATCH --account=cavestru
#SBATCH --partition=standard
#SBATCH --output=/home/%u/%x-%j.log

# The application(s) to execute along with its input arguments and options:

python download.py