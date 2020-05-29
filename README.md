BGS-AADM - British Geological Survey Automatic Ash Dispersion Modelling
Fabio Dioguardi. British Geological Survey, The Lyell Centre, Edinburgh, United Kingdom. Email: fabiod@bgs.ac.uk

This package is designed to simplify and speed-up dispersion modelling applications for volcanic eruptions in real-time, i.e. in forecast mode. Dispersion models currently supported are:
	- HYSPLIT, the NOAA Lagrangian dispersion model (https://www.ready.noaa.gov/HYSPLIT.php)
	- FALL3D, the INGV-BSC Eulerian dispersion model (https://gitlab.com/fall3d-distribution/v8.0).
Both models are currently installed on the BGS HPC cluster.

The package contains the following files and folders:
- simulation_settings.py
- operational_settings.txt
- weather.py
- control.py
- post_processing.py
- fix_config.txt
- run_models.sh
- post_processing.sh
- TGSDs
- Runs
- weather
- log

- simulation_settings.py
Python script with a GUI interface that creates the control file operational_settings.txt, which is used to specify some modelling parameters. Note that it is always possible to edit operational_settings.txt manually.

- operational_settings.txt
Text file that is used to store simulation settings. This is particularly useful to avoid listing all the arguments of the Python scripts (see below). This text file can be both edited manually or via the Python script simulation_settings.py

- weather.py
Python script that downloads, processes and stores the weather data necessary to run the dispersion models. It takes the following arguments.
usage: weather.py [-h] [-SET SET] [-M MODE] [-LATMIN LATMIN] [-LATMAX LATMAX]
                  [-LONMIN LONMIN] [-LONMAX LONMAX] [-D DUR] [-V VOLC]
                  [-START START_TIME]
  -h, --help            show this help message and exit
  -SET SET, --set SET   True or False. True: Read simulation parameters from
                        operational_settings.txt. False: simulation parameters
                        are read from the other arguments
  -M MODE, --mode MODE  operational: routine simulation mode controlled via
                        operational_settings.txt manual: run with user
                        specific inputs
  -LATMIN LATMIN, --latmin LATMIN
                        Domain minimum latitude
  -LATMAX LATMAX, --latmax LATMAX
                        Domain maximum latitude
  -LONMIN LONMIN, --lonmin LONMIN
                        Domain minimum longitude
  -LONMAX LONMAX, --lonmax LONMAX
                        Domain maximum longitude
  -D DUR, --dur DUR     Ash dispersion simulation duration
  -V VOLC, --volc VOLC  Smithsonian Institude volcano ID
  -START START_TIME, --start_time START_TIME
                        Starting date and time of the simulation in UTC
                        (DD/MM/YYYY-HH:MM). Option valid only in manual mode

- control.py.
Python script that controls all the models execution. It takes the following arguments:
usage: control.py [-h] [-M MODE] [-SET SET] [-V VOLC] [-NP NP] [-S S] [-I I]
                  [-LATMIN LATMIN] [-LATMAX LATMAX] [-LONMIN LONMIN]
                  [-LONMAX LONMAX] [-D DUR] [-START START_TIME]
  -h, --help            show this help message and exit
  -M MODE, --mode MODE  operational: routine simulation mode controlled via
                        operational_settings.txt manual: run with user
                        specific inputs
  -SET SET, --set SET   True: Read simulation parameters from
                        operational_settings.txt. False: simulation parameters
                        are read from the other arguments
  -V VOLC, --volc VOLC  This is the volcano ID based on the Smithsonian
                        Institute IDs
  -NP NP, --np NP       Number of processes for parallel processing
  -S S, --s S           True or False. True: run REFIR for 5 minutes; False:
                        run REFIR for the duration set by the ESPs database
  -I I, --i I           True or False. True: Icelandic volcanoes scenarios;
                        False: other volcanoes
  -LATMIN LATMIN, --latmin LATMIN
                        Domain minimum latitude
  -LATMAX LATMAX, --latmax LATMAX
                        Domain maximum latitude
  -LONMIN LONMIN, --lonmin LONMIN
                        Domain minimum longitude
  -LONMAX LONMAX, --lonmax LONMAX
                        Domain maximum longitude
  -D DUR, --dur DUR     Ash dispersion simulation duration
  -START START_TIME, --start_time START_TIME
                        Starting date and time of the simulation in UTC
                        (DD/MM/YYYY-HH:MM). Option valid only in manual mode

- post_processing.py
Python script that automatically produce contour plots of the simulation outputs by using the ash-model-plotting package (see Dependencies).
usage: post_processing.py [-h] [-M MODE] [-SET SET] [-LATMIN LATMIN]
                          [-LATMAX LATMAX] [-LONMIN LONMIN] [-LONMAX LONMAX]
  -h, --help            show this help message and exit
  -M MODE, --mode MODE  operational: routine simulation mode controlled via
                        operational_settings.txt manual: run with user
                        specific inputs
  -SET SET, --set SET   Read simulation parameters from
                        operational_settings.txt
  -LATMIN LATMIN, --latmin LATMIN
                        Domain minimum latitude
  -LATMAX LATMAX, --latmax LATMAX
                        Domain maximum latitude
  -LONMIN LONMIN, --lonmin LONMIN
                        Domain minimum longitude
  -LONMAX LONMAX, --lonmax LONMAX
                        Domain maximum longitude

- fix_config.txt
Text file that is used by REFIR (in particular FOXI.py) to run the simulation. This file is edited is some of its entries by control.py depending on the User input and is then transferred to the REFIR simulation folder. Note that some configurations listed in this files may need to be changed via FIX.py of REFIR package. 
Note that: 
	- when running BGS-AADM in manual mode, FIX.py of REFIR package is run before FOXI.py, therefore this file is not used but it's instead created via FIX.py in the REFIR simulation folder. 
	- when running BGS-AADM in operational mode, only FOXI.py is run, hence fix_config.txt is first edited by control.py and then transferred to the REFIR simulation folder.

- run_models.sh
Bash script that automatically performs all the simulation steps above. It is currently set to work for operational applications, but it can be edited for any application.

- post_processing.sh
Slurm script to run post_processing.py using the HPC cluster. It is used in this way:
sbatch post_processing.sh 'python post_processing.py ARGS', where ARGS is the list of arguments required by post_processing.py. It is important to enclose the whole Python command in quotation marks.

- TGSDs
Folder that contains text files with the total grain size distributions of Icelandic volcanoes. The user can use a different TGSD in manual mode by editing the file "user_defined" and using the format of the other files.  

- Runs
Fodlder that stores all the simulation outputs. It contains two subfolders: "manual" and "operational". The former stores the outputs of simulations run in manual mode, the latter hose of simulations run in operational mode. Both subfolders have the following subfolders:
	- FALL3D. This stores the outputs of FALL3D and contains a template of the FALL3D input file that is edited by control.py in run time. The template can be edited in any of its part following the instruction of FALL3D user manual (https://gitlab.com/fall3d-distribution/v8.0/-/wikis/home), with a note that all the variables with "xx" are overwritten by control.py.
	- HYSPLIT. This stores the output of HYSPLIT simulations and contains two files that are needed by HYSPLIT: ASCDATA.CFG and SETUP.CFG. The former should not be edited since it contains general configurations. SETUP.CFG contains some simulation settings which can be edited by the user following HYSPLIT User manual (https://www.ready.noaa.gov/hysplitusersguide/). 
For each model, in each application three simulations are carried out, each corresponding to the REFIR solutions: (average, maximum and minimum). When simulations are run, the following subfolders are created:
+ FALL3D
	+ YYYYMMDD :date of the simulation
		+ HH :time of the simulation in hours
			+ avg :average solution simulation
				+ iris_outputs: outputs produced by post_processing.py
			+ max :maximum solution simulation
				+ iris_outputs: outputs produced by post_processing.py 
			+ min :minimum solution simulation
				+ iris_outputs: outputs produced by post_processing.py 
+ HYSPLIT
	+ YYYYMMDD: date of the simulation
		+ HH :time of the simulation in hours
			+ avg :average solution simulation
				+ output: folder that stores the processed HYSPLIT runs in both native and NetCDF format
					+ iris_outputs: outputs produced by post_processing.py 
				+ runs: folder that contains each individual HYSPLIT run. In fact, the HYSPLIT simulation is split in different sub-simulations corresponding to the different pollutant (=grainsize bin), as to obtain an efficient parallelization. Result of each individual pollutant-run are then merged together to produce a single output file in "output"
					+ poll"n": folder containing the pollutant-specific HYSPLIT run for the nth pollutant
						+ run: folder containing the HYSPLIT input file and output files produced at run-time
						+ output: folder containing the HYSPLIT output file of the pollutant-specific simulation
			+ max :maximum solution simulation
				+ output: folder that stores the processed HYSPLIT runs in both native and NetCDF format
					+ iris_outputs: outputs produced by post_processing.py 
				+ runs: folder that contains each individual HYSPLIT run. In fact, the HYSPLIT simulation is split in different sub-simulations corresponding to the different pollutant (=grainsize bin), as to obtain an efficient parallelization. Result of each individual pollutant-run are then merged together to produce a single output file in "output"
					+ poll"n": folder containing the pollutant-specific HYSPLIT run for the nth pollutant
						+ run: folder containing the HYSPLIT input file and output files produced at run-time
						+ output: folder containing the HYSPLIT output file of the pollutant-specific simulation
			+ min :minimum solution simulation
				+ output: folder that stores the processed HYSPLIT runs in both native and NetCDF format
					+ iris_outputs: outputs produced by post_processing.py 
				+ runs: folder that contains each individual HYSPLIT run. In fact, the HYSPLIT simulation is split in different sub-simulations corresponding to the different pollutant (=grainsize bin), as to obtain an efficient parallelization. Result of each individual pollutant-run are then merged together to produce a single output file in "output"
					+ poll"n": folder containing the pollutant-specific HYSPLIT run for the nth pollutant
						+ run: folder containing the HYSPLIT input file and output files produced at run-time
						+ output: folder containing the HYSPLIT output file of the pollutant-specific simulation

- weather
Folder that contains scripts that are used to retrieve and process weather data necessary for REFIR and the dispersion simulations. 
	+ scripts. This folder contains the following scripts and files:
		+ api2arl.cfg. HYSPLIT configuration file that is used to convert GRIB2 files into the native HYSPLIT format ARL.
		+ gfs_grib_parallel.py. Python script that has been modified by a similar script available in the FALL3D package to download all the necessary GFS forecast files and convert them into ARL for HYSPLIT. This script interfaces with fall3dutil package (see Dependencies below)
		+ grib2nc.sh. Bash script to convert the downloaded grib file into NetCDF format and merge them all in one single file used by FALL3D.
	+ data: folder storing the weather data files ready to be used by FALL3D and HYSPLIT in the subfolders listed below. Both subfolders contain two HYSPLIT configuration files (oct1618.BIN, oct1718.BIN) that should not be edited or deleted.
		+ manual: folder storing the weather data used by the simulation in manual mode
		+ operational: folder storing the weather data used by the simulation in operational mode


- log
Folder that stores all the log files produced by the scripts above.

### DEPENDENCIES ###
To run the whole package, the following dependencies must be satisfied.
- Python environment
All the scripts work for Python version > 3.
The following Python modules must be installed: basemap, pandas, xlrd, future, pillow, cdsapi, pathos, gdal, utm, fall3dutil, urllib3
It is convenient to set up a Anaconda environment that can be activated before using BGS-AADM. This can be done with the following command:
conda create -n myenv python=3.7 basemap, pandas, xlrd, future, pillow, cdsapi, pathos, gdal, utm, fall3dutil, urllib3
Note that the package fall3dutil should be installed with pip from inside the environment when this is activated:
python pip -m install fall3dutil.
- Dispersion models
The system assumes that the following dispersion models are installed in the system: FALL3D and HYSPLIT. The paths to the FALL3D and HYSPLIT executables are specified in the control.py file. If these needs to be changed, the user should modify the following variables in control.py:
	+ FALL3D: path to the FALL3D executable Fall3d.r8.x (e.g. /path/to/FALL3D/executables/Fall3d.r8.x)
	+ HYSPLIT: path to the HYSPLIT folder "exec" with all the HYSPLIT scripts (e.g. /path/to/HYSPLIT/scripts/exec)
- wgrib2
The system assumes the executable is in the system PATH
- plot_ash_model_results
Executable of the ash-model-plotting package (https://github.com/BritishGeologicalSurvey/ash-model-plotting) that must be installed in the system. This program is called from post_processing.py, which in turn needs to be run after the ash-model-plotting Conda environment has been activated (see ash-model-plotting instructions)



Improvements for the future:
- check what control.py actually does when FOXI runs for 1 time step in manual mode and with ED specified and short simulation set to True
- add flexible control for the TGSD (e.g. specify the TGSD name in input)
- selection of one dispersion model only
- implementation of NAME (reanalysis mode only unless usage of GFS data is implemented)
- possibility to bypass REFIR and use all data from ESPs database and/or specify plume height and MER in input
- reanalysis mode with ERA5 data