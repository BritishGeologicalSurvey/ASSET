ASSET - Automatic aSh diSpersion modElling Tool
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
                  [-START START_TIME] [-RUN RUN_NAME] [-NR NO_REFIR]
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
  -RUN RUN_NAME, --run_name RUN_NAME
                        Run name. If not specified, the run name will be the
                        starting time with format HH
  -NR NO_REFIR, --no_refir NO_REFIR
                        True: avoid running REFIR for ESPs. False: run REFIR for ESPs

- control.py.
Python script that controls all the models execution. It takes the following arguments:
usage: control.py [-h] [-M MODE] [-SET SET] [-V VOLC] [-NP NP] [-S S] [-I I]
                  [-LATMIN LATMIN] [-LATMAX LATMAX] [-LONMIN LONMIN]
                  [-LONMAX LONMAX] [-D DUR] [-START START_TIME]
                  [-SR SOURCE_RESOLUTION] [-PER PER] [-OI OUTPUT_INTERVAL]
                  [-TGSD TGSD] [-MOD MODEL] [-RUN RUN_NAME] [-NR NO_REFIR]
                  [-MER MER [MER ...]] [-PH PLH [PLH ...]]
                  [-ED ER_DURATION [ER_DURATION ...]] [-NRP NO_REFIR_PLOTS]

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
  -D DUR, --dur DUR     Ash dispersion simulation duration (hours)
  -START START_TIME, --start_time START_TIME
                        Starting date and time of the simulation in UTC
                        (DD/MM/YYYY-HH:MM). Option valid only in manual mode
  -SR SOURCE_RESOLUTION, --source_resolution SOURCE_RESOLUTION
                        Time resolution of the source (minutes)
  -PER PER, --per PER   Total lagrangian particles emission rate
                        (particle/hour)
  -OI OUTPUT_INTERVAL, --output_interval OUTPUT_INTERVAL
                        Output time interval in hours
  -TGSD TGSD, --tgsd TGSD
                        Total Grain Size Distribution file name
  -MOD MODEL, --model MODEL
                        Dispersion model to use. Options are: hysplit, fall3d,
                        all (both hysplit and fall3d)
  -RUN RUN_NAME, --run_name RUN_NAME
                        Run name. If not specified, the run name will be the
                        starting time with format HH
  -NR NO_REFIR, --no_refir NO_REFIR
                        True: avoid running REFIR for ESPs. False: run REFIR
                        for ESPs
  -MER MER [MER ...], --mer MER [MER ...]
                        Mass Eruption Rate (kg/s). Used if -NR True. If not
                        specified and -NR True, the ESPs database is used
  -PH PLH [PLH ...], --plh PLH [PLH ...]
                        Plume top height a.s.l. (m). Used if -NR True. If not
                        specified and -NR True, the ESPs database is used
  -ED ER_DURATION [ER_DURATION ...], --er_duration ER_DURATION [ER_DURATION ...]
                        Eruption duration (hours). If specified, it overcomes
                        the ESPs database duration (if used by REFIR)
  -NRP NO_REFIR_PLOTS, --no_refir_plots NO_REFIR_PLOTS
                        True: avoid saving and updating plots during the REFIR
                        run. This overcomes any related setting in
                        fix_config.txt. False: keep the fix_config.txt plot
                        settings

- post_processing.py
Python script that automatically produce contour plots of the simulation outputs by using the ash-model-plotting package (see Dependencies).
usage: post_processing.py [-h] [-M MODE] [-SET SET] [-LATMIN LATMIN]
                          [-LATMAX LATMAX] [-LONMIN LONMIN] [-LONMAX LONMAX] [-MOD MODEL] [-NR NO_REFIR]
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
  -MOD MODEL, --model MODEL
                        Dispersion model to use. Options are: hysplit, fall3d, all (both hysplit and fall3d)
  -NR NO_REFIR, --no_refir NO_REFIR
                        True: avoid running REFIR for ESPs. False: run REFIR for ESPs

- fix_config.txt
Text file that is used by REFIR (in particular FOXI.py) to run the simulation. This file is edited is some of its entries by control.py depending on the User input and is then transferred to the REFIR simulation folder. Note that some configurations listed in this files may need to be changed via FIX.py of REFIR package. 
Note that: 
	- when running BGS-AADM in manual mode, FIX.py of REFIR package is run before FOXI.py, therefore this file is not used but it's instead created via FIX.py in the REFIR simulation folder. 
	- when running BGS-AADM in operational mode, only FOXI.py is run, hence fix_config.txt is first edited by control.py and then transferred to the REFIR simulation folder.

- run_models.sh
Bash script that automatically performs all the simulation steps above. It is currently set to work for operational applications, but it can be edited for any application.

- TGSDs
Folder that contains text files with the total grain size distributions of Icelandic volcanoes. The user can use a different TGSD in manual mode by editing the file "user_defined" and using the format of the other files.  

- Runs
Foldder that stores all the simulation outputs. It contains two subfolders: "manual" and "operational". The former stores the outputs of simulations run in manual mode, the latter hose of simulations run in operational mode. Both subfolders have the following subfolders:
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
				+ iris_outputs: outputs produced by post_processing.py
			+ max :maximum solution simulation
				+ iris_outputs: outputs produced by post_processing.py 
			+ min :minimum solution simulation
				+ iris_outputs: outputs produced by post_processing.py 

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
With Conda, it is possible to set a virtual environmnent with all the required dependencies specific for ASSET. This simplifies the installation of the different packages and the management of the Python installation in the system.

Instructions for setting the Conda environment:

1) create the environment with all the needed additional packages:
	`conda env create -f environment.yml`
2) activate the environment with:
	`conda activate vigil`
3) to exit from the environment:
	`conda deactivate`

If required, the name of the environment can be changed by editing
`environment.yml`.

- Dispersion models
The system assumes that the following dispersion models are installed in the system: FALL3D and HYSPLIT. The scripts assume that the following environment variables are set in the system:
	+ FALL3D: path to the FALL3D bin folder where Fall3d.r8.x is 
	+ HYSPLIT: path to the HYSPLIT folder "exec" with all the HYSPLIT scripts

- wgrib2
The scripts assume that the following environment variable is set in the system:
	+ REFIR: path to the folder storing the REFIR scripts

- REFIR
The scripts assume that the following environment variable is set in the system:
	+ WGRIB2: path to the folder where the wgrib2 executable is

- plot_ash_model_results
Executable of the ash-model-plotting package (https://github.com/BritishGeologicalSurvey/ash-model-plotting) that must be installed in the system. This program is called from post_processing.py, which in turn needs to be run after the ash-model-plotting Conda environment has been activated (see ash-model-plotting instructions)

IMPORTANT: I have modified grib_filter.py in /home/vulcanomod/anaconda3/envs/ash_dispersion_modelling/lib/python3.7/site-packages/fall3dutil to have the right new GFS URL format

Working on bypassing REFIR option. For the moment, the input flags have been implmented.

Improvements for the future:
- implementation of NAME (reanalysis mode only unless usage of GFS data is implemented)
- reanalysis mode with ERA5 data
- possibility to use FPLUME for initializing the plume in dispersion simulations. This is straightforward for FALL3D, it requires some extra pre-processing for HYSPLIT