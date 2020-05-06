BGS-AADM
British Geological Survey Automatic Ash Dispersion Modelling

This package is designed to simplify and speed-up dispersion modelling applications for volcanic eruptions in real-time, i.e. in forecast mode.
The package contains the following files and folders:
- simulation_settings.py
- operational_settings.txt
- weather.py
- control.py
- fix_config.txt
- post_processing.py
- post_processing.sh
- TGSDs
- Runs
- weather
- log

- simulation_settings.py
Python script with a GUI interface that creates the control file operational_settings.txt, which is used to specify some modelling parameters. Note that it is always possible to edit operational_settings.txt manually.

- weather.py
Python script that downloads, processes and stores the weather data necessary to run the dispersion models. It takes the following arguments.
weather.py [-h] [--set SET] [--mode MODE] [--latmin LATMIN]
                  [--latmax LATMAX] [--lonmin LONMIN] [--lonmax LONMAX]
                  [--dur DUR] [--volc VOLC]
  -h, --help       show this help message and exit
  --set SET        True or False. True: Read simulation parameters from operational_settings.txt. False: simulation parameters are read from the other arguments
  --mode MODE      operational: routine simulation mode controlled via operational_settings.txt manual: run with user specific inputs
  --latmin LATMIN  Domain minimum latitude
  --latmax LATMAX  Domain maximum latitude
  --lonmin LONMIN  Domain minimum longitude
  --lonmax LONMAX  Domain maximum longitude
  --dur DUR        Simulation duration
  --volc VOLC      Smithsonian Institude volcano ID
Note that, if --set=True, the scripts reads the parameters from operational_settings.txt. Otherwise the other parameters must be specified.

- control.py.
Python script that controls all the models execution. It takes the following arguments:
control.py [-h] [--mode MODE] [--set SET] [--volc VOLC] [--np NP]
                  [--s S] [--i I] [--latmin LATMIN] [--latmax LATMAX]
                  [--lonmin LONMIN] [--lonmax LONMAX] [--dur DUR]
  -h, --help       show this help message and exit
  --mode MODE      operational: routine simulation mode controlled via operational_settings.txt manual: run with user specific inputs
  --set SET        True: Read simulation parameters from operational_settings.txt. False: simulation parameters are read from the other arguments
  --volc VOLC      This is the volcano ID based on the Smithsonian Institute IDs
  --np NP          Number of processes for parallel processing
  --s S            True or False. True: run REFIR for 5 minutes; False: run REFIR for the duration set by the ESPs database
  --i I            True or False. True: Icelandic volcanoes scenarios; False: other volcanoes
  --latmin LATMIN  Domain minimum latitude
  --latmax LATMAX  Domain maximum latitude
  --lonmin LONMIN  Domain minimum longitude
  --lonmax LONMAX  Domain maximum longitude
  --dur DUR        Ash dispersion simulation duration



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
- selection of one dispersion model only
- implementation of NAME (reanalysis mode only unless usage of GFS data is implemented)
- possibility to bypass REFIR and use all data from ESPs database and/or specify plume height and MER in input
- reanalysis mode with ERA5 data