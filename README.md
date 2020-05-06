BGS-AADM
British Geological Survey Automatic Ash Dispersion Modelling

This package is designed to simplify and speed-up dispersion modelling applications for volcanic eruptions in real-time, i.e. in forecast mode.
The package contains the following files and folders:
- simulation_settings.py
- operational_settings.txt
- weather.py
- control.py
- post_processing.py
- post_processing.sh
- TGSDs
- Runs
- weather
- log




Improvements for the future:
- selection of one dispersion model only
- implementation of NAME (reanalysis mode only unless usage of GFS data is implemented)
- possibility to bypass REFIR and use all data from ESPs database and/or specify plume height and MER in input
- reanalysis mode with ERA5 data