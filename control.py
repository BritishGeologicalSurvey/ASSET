import os
import datetime
from shutil import which, copy, copyfile, rmtree
import argparse
from pathos.multiprocessing import ThreadingPool
import sys

# Folder structure
ROOT = os.getcwd()
REFIR = '/home/vulcanomod/REFIR'
RUNS = os.path.join(ROOT,'Runs')
TGSDS = os.path.join(ROOT,'TGSDs')

def read_args():
    parser = argparse.ArgumentParser(description='Input data for the control script')
    parser.add_argument('-M', '--mode', default='operational',
                        help='operational: routine simulation mode controlled via operational_settings.txt'
                             '\nmanual: run with user specific inputs')
    parser.add_argument('-SET', '--set', default='True',
                        help='True: Read simulation parameters from operational_settings.txt. False: simulation '
                             'parameters are read from the other arguments')
    parser.add_argument('-V', '--volc', default=999,
                        help='This is the volcano ID based on the Smithsonian Institute IDs')
    parser.add_argument('-NP', '--np', default=0, help='Number of processes for parallel processing')
    parser.add_argument('-S', '--s', default='True',
                        help='True or False. True: run REFIR for 5 minutes; False: run REFIR for the duration set by '
                             'the ESPs database')
    parser.add_argument('-I', '--i', default='True',
                        help='True or False. True: Icelandic volcanoes scenarios; False: other volcanoes')
    parser.add_argument('-LATMIN', '--latmin', default=999, help='Domain minimum latitude')
    parser.add_argument('-LATMAX', '--latmax', default=999, help='Domain maximum latitude')
    parser.add_argument('-LONMIN', '--lonmin', default=999, help='Domain minimum longitude')
    parser.add_argument('-LONMAX', '--lonmax', default=999, help='Domain maximum longitude')
    parser.add_argument('-D', '--dur', default=96, help='Ash dispersion simulation duration (hours)')
    parser.add_argument('-START', '--start_time', default='999',
                        help='Starting date and time of the simulation in UTC (DD/MM/YYYY-HH:MM). Option valid only in '
                             'manual mode')
    parser.add_argument('-SR', '--source_resolution', default=60, help='Time resolution of the source (minutes)')
    parser.add_argument('-PER', '--per', default=1000000,
                        help='Total lagrangian particles emission rate (particle/hour)')
    parser.add_argument('-OI', '--output_interval', default=1, help='Output time interval in hours')
    parser.add_argument('-TGSD', '--tgsd', default='undefined', help='Total Grain Size Distribution file name')
    parser.add_argument('-MOD', '--model', default='all',
                        help='Dispersion model to use. Options are: hysplit, fall3d, all (both hysplit and fall3d)')
    parser.add_argument('-RUN', '--run_name', default='default',
                        help='Run name. If not specified, the run name will be the starting time with format HH')
    parser.add_argument('-NR', '--no_refir', default='False',
                        help='True: avoid running REFIR for ESPs. False: run REFIR for ESPs')
    parser.add_argument('-MER', '--mer', nargs='+', default=[],
                        help='Mass Eruption Rate (kg/s). Used if -NR True. If not specified and -NR True, the'
                             ' ESPs database is used')
    parser.add_argument('-PH', '--plh', nargs='+', default=[],
                        help='Plume top height a.s.l. (m). Used if -NR True. If not specified and -NR True, the'
                             ' ESPs database is used')
    parser.add_argument('-ED', '--er_duration', nargs='+', default=[],
                        help='Eruption duration (hours). If specified, it overcomes the ESPs database duration '
                             '(if used by REFIR)')
    parser.add_argument('-NRP', '--no_refir_plots', default='False',
                        help='True: avoid saving and updating plots during the REFIR run. This overcomes any related'
                             ' setting in fix_config.txt. \n False: keep the fix_config.txt plot settings')
    args = parser.parse_args()
    mode = args.mode
    settings_file = args.set
    volc_id = args.volc
    n_processes = args.np
    short_simulation = args.s
    Iceland_scenario = args.i
    lon_min = args.lonmin
    lon_max = args.lonmax
    lat_min = args.latmin
    lat_max = args.latmax
    run_duration = args.dur
    start_time = args.start_time
    source_resolution = args.source_resolution
    output_interval = args.output_interval
    tgsd = args.tgsd
    per = args.per
    models_in = args.model
    mer_input_s = args.mer
    plh_input_s = args.plh
    er_duration_input_s = args.er_duration
    run_name_in = args.run_name
    no_refir = args.no_refir
    no_refir_plots = args.no_refir_plots
    mer_input = []
    plh_input = []
    er_duration_input = []
    if settings_file.lower() == 'true':
        settings_file = True
        return settings_file, tgsd, short_simulation, start_time, 999, no_refir_plots, mode, no_refir, plh_input, \
               mer_input, er_duration_input, volc_id, n_processes, Iceland_scenario, lon_min, lon_max, lat_min, \
               lat_max, 999, 999, 999, source_resolution, 999, output_interval, 999, 999
    elif settings_file.lower() == 'false':
        settings_file = False
    else:
        print('Wrong value for variable --set')
    if short_simulation.lower() == 'true':
        short_simulation = True
    elif short_simulation.lower() == 'false':
        short_simulation = False
    else:
        print('Wrong value for variable --s')
    if mode != 'manual' and mode != 'operational':
        print('Wrong value for variable --mode')
        print('Execution stopped')
        sys.exit()
    if start_time != '999':
        try:
            start_time_datetime = datetime.datetime.strptime(start_time, format('%d/%m/%Y-%H:%M'))
        except:
            print('Unable to read starting time. Please check the format')
            sys.exit()
    if no_refir.lower() == 'true':
        no_refir = True
    elif no_refir.lower() == 'false':
        no_refir = False
    else:
        print('WARNING. Wrong input for argument -NR --no_refir')
        no_refir = False
    if no_refir and (len(er_duration_input_s) == 0 or len(mer_input_s) == 0 or len(plh_input_s) == 0):
        print('Warning. REFIR deactivated and not all ESPs specified. The ESPs database is going to be used')
    if no_refir:
        if len(er_duration_input_s) != len(mer_input_s) or len(er_duration_input_s) != len(plh_input_s) or len(
                mer_input_s) != len(plh_input_s):
            print('ERROR. Number of PLH, MER and ED scenarios are not consistent')
            sys.exit()
        for i in range(0, len(mer_input_s)):
            if float(mer_input_s[i]) <= 0:
                print('ERROR. Negative value of MER provided')
                sys.exit()
            mer_input.append(float(mer_input_s[i]))
        if not mer_input:
            mer_input.append(999)
        for i in range(0, len(plh_input_s)):
            if float(plh_input_s[i]) <= 0:
                print('ERROR. Negative value of PLH provided')
                sys.exit()
            plh_input.append(float(plh_input_s[i]))
        if not plh_input:
            plh_input.append(999)
        for i in range(0, len(er_duration_input_s)):
            if float(er_duration_input_s[i]) <= 0:
                print('ERROR. Negative value of eruption duration provided')
                sys.exit()
            er_duration_input.append(float(er_duration_input_s[i]))
    if not er_duration_input:
        er_duration_input.append(999)
    if no_refir_plots.lower() == 'true':
        no_refir_plots = True
    elif no_refir_plots.lower() == 'false':
        no_refir_plots = False
    else:
        print('WARNING. Wrong input for argument -NRP --no_refir_plot. Keeping the plotting settings in fix_config.txt')
        no_refir_plots = False
    lon_max = float(lon_max)
    lon_min = float(lon_min)
    lat_max = float(lat_max)
    lat_min = float(lat_min)
    if lat_min == 999:
        print('Please specify a valid value for lat_min')
        sys.exit()
    if lat_max == 999:
        print('Please specify a valid value for lat_max')
        sys.exit()
    if lon_min == 999:
        print('Please specify a valid value for lon_min')
        sys.exit()
    if lon_max == 999:
        print('Please specify a valid value for lon_max')
        sys.exit()
    if lat_max > 90 or lat_max < -90:
        print('lat_max not in the valid range -90 < latitude < 90. Please specify a valid value')
        sys.exit()
    if lat_min > 90 or lat_min < -90:
        print('lat_min not in the valid range -90 < latitude < 90. Please specify a valid value')
        sys.exit()
    if lat_min >= lat_max:
        print('lat_min greater than or equal to lat_max. Please check the values')
        sys.exit()
    if lon_min > 180 or lon_min < -180:
        print('lon_min not in the valid range -90 < longitude < 90. Please specify a valid value')
        sys.exit()
    if lon_max > 180 or lon_max < -180:
        print('lon_max not in the valid range -90 < longitude < 90. Please specify a valid value')
        sys.exit()
    if lon_min >= lon_max:
        print('lon_min greater than or equal to lon_max. Please check the values')
        sys.exit()
    tot_dx = lon_max - lon_min
    tot_dy = lat_max - lat_min
    try:
        volc_id = int(volc_id)
        if volc_id <= 0 or volc_id == 999:
            print('Please provide a valid volcano ID')
            sys.exit()
    except:
        print('Please provide a valid volcano ID')
        sys.exit()
    try:
        n_processes = int(n_processes)
        if n_processes <= 0:
            print('Please provide a valid number of processes (> 0)')
            sys.exit()
    except:
        print('Please provide a valid number of processes')
    try:
        run_duration = int(run_duration)
        if run_duration <= 0:
            print('Please provide a valid duration (> 0)')
            sys.exit()
    except:
        print('Please provide a valid duration')
        sys.exit()
    if Iceland_scenario.lower() == 'true':
        Iceland_scenario = True
    elif Iceland_scenario.lower() == 'false':
        Iceland_scenario = False
    else:
        print('Wrong value for variable --i')
        sys.exit()
    try:
        source_resolution = int(source_resolution)
    except:
        print('Please provide a valid integer for the source resolution in minutes')
        sys.exit()
    base = 5
    source_resolution = base * round(source_resolution / base) #Ensure the source resolution is always a multiple of 5
    try:
        tot_particle_rate = int(per)
    except:
        print('Please provide a valid number for the Total particle emission rate')
        sys.exit()
    if int(output_interval) <= 0:
        print('Please provide a valid number for the output interval in hours')
        sys.exit()
    else:
        output_interval = str(output_interval)
    if models_in == 'all':
        models = ['hysplit', 'fall3d']
    elif models_in == 'hysplit':
        models = ['hysplit']
    elif models_in == 'fall3d':
        models = ['fall3d']
    else:
        print('Wrong model selection')
        sys.exit()
    run_name = str(run_name_in)
    return settings_file, tgsd, short_simulation, start_time, start_time_datetime, no_refir_plots, mode, no_refir, \
           plh_input, mer_input, er_duration_input, volc_id, n_processes, Iceland_scenario, lon_min, lon_max, lat_min, \
           lat_max, tot_dx, tot_dy, run_duration, source_resolution, tot_particle_rate, output_interval, models, \
           run_name

def read_operational_settings_file():
    mer_input = []
    plh_input = []
    er_duration_input = []
    with open('operational_settings.txt','r',encoding="utf-8", errors="surrogateescape") as settings:
        for line in settings:
            if line.split('=')[0] == 'LAT_MIN_[deg]':
                lat_min = float(line.split('=')[1])
            elif line.split('=')[0] == 'LAT_MAX_[deg]':
                lat_max = float(line.split('=')[1])
            elif line.split('=')[0] == 'LON_MIN_[deg]':
                lon_min = float(line.split('=')[1])
            elif line.split('=')[0] == 'LON_MAX_[deg]':
                lon_max = float(line.split('=')[1])
            elif line.split('=')[0] == 'VOLCANO_ID':
                volc_id = int(line.split('=')[1])
            elif line.split('=')[0] == 'NP':
                n_processes = int(line.split('=')[1])
            elif line.split('=')[0] == 'DURATION_[hours]':
                run_duration = int(line.split('=')[1])
            elif line.split('=')[0] == 'SHORT_SIMULATION':
                short_simulation = line.split('=')[1]
                try:
                    short_simulation = short_simulation.split('\n')[0]
                except:
                    None
                if short_simulation.lower() == 'true':
                    short_simulation = True
                elif short_simulation.lower() == 'false':
                    short_simulation = False
            elif line.split('=')[0] == 'ICELAND_SCENARIO':
                Iceland_scenario = line.split('=')[1]
                try:
                    Iceland_scenario = Iceland_scenario.split('\n')[0]
                except:
                    None
                if Iceland_scenario.lower() == 'true':
                    Iceland_scenario = True
                elif Iceland_scenario.lower() == 'false':
                    Iceland_scenario = False
            elif line.split('=')[0] == 'NO_REFIR':
                no_refir = line.split('=')[1]
                try:
                    no_refir = no_refir.split('\n')[0]
                except:
                    None
                if no_refir.lower() == 'true':
                    no_refir = True
                elif no_refir.lower() == 'false':
                    no_refir = False
            elif line.split('=')[0] == 'ERUPTION_DURATION_[hours]':
                er_duration_input_s = line.split('=')[1]
                try:
                    er_duration_input.append(float(er_duration_input_s))
                    if er_duration_input[0] <= 0:
                        print('ERROR. Negative value of eruption duration provided.')
                        sys.exit()
                except:
                    try:
                        er_duration_input_s = er_duration_input_s.split('\t')
                        for i in range(1, len(er_duration_input_s)):
                            if float(er_duration_input_s[i]) <= 0:
                                print('ERROR. Negative value of eruption duration provided.')
                                sys.exit()
                            er_duration_input.append(float(er_duration_input_s[i]))
                    except:
                        er_duration_input.append(999)
                if not er_duration_input:
                    er_duration_input.append(999)
            elif line.split('=')[0] == 'ERUPTION_PLH_[m_asl]':
                plh_input_s = line.split('=')[1]
                try:
                    plh_input.append(float(plh_input_s))
                    if plh_input[0] <= 0:
                        print('ERROR. Negative value of PLH provided.')
                        sys.exit()
                except:
                    try:
                        plh_input_s = plh_input_s.split('\t')
                        for i in range(1, len(plh_input_s)):
                            if float(plh_input_s[i]) <= 0:
                                print('ERROR. Negative value of PLH provided.')
                                sys.exit()
                            plh_input.append(float(plh_input_s[i]))
                    except:
                        plh_input.append(999)
                if not plh_input:
                    plh_input.append(999)
            elif line.split('=')[0] == 'ERUPTION_MER_[kg/s]':
                mer_input_s = line.split('=')[1]
                try:
                    mer_input.append(float(mer_input_s))
                    if mer_input[0] <= 0:
                        print('ERROR. Negative value of MER provided.')
                        sys.exit()
                except:
                    try:
                        mer_input_s = mer_input_s.split('\t')
                        for i in range(1, len(mer_input_s)):
                            if float(mer_input_s[i]) <= 0:
                                print('ERROR. Negative value of MER provided.')
                                sys.exit()
                            mer_input.append(float(mer_input_s[i]))
                    except:
                        mer_input.append(999)
                if not mer_input:
                    mer_input.append(999)
            elif line.split('=')[0] == 'SOURCE_RESOLUTION_[minutes]':
                try:
                    source_resolution = line.split('=')[1]
                    source_resolution = int(source_resolution)
                    base = 5
                    source_resolution = base * round(source_resolution / base)  # Ensure the source resolution is
                    # always a multiple of 5
                except:
                    source_resolution = 60
            elif line.split('=')[0] == 'PARTICLE_EMISSION_RATE_[p/hr]':
                try:
                    tot_particle_rate = line.split('=')[1]
                    tot_particle_rate = int(tot_particle_rate)
                except:
                    tot_particle_rate = 1000000
            elif line.split('=')[0] == 'OUTPUT_INTERVAL_[hr]':
                try:
                    output_interval = line.split('=')[1]
                    output_interval = output_interval.split('\n')[0]
                    int(output_interval)
                except:
                    output_interval = '1'
            elif line.split('=')[0] == 'TGSD':
                tgsd = line.split('=')[1]
                tgsd = tgsd.split('\n')[0]
            elif line.split('=')[0] == 'RUN_NAME':
                run_name = line.split('=')[1]
                run_name = run_name.split('\n')[0]
            elif line.split('=')[0] == 'MODELS':
                try:
                    models_in = line.split('=')[1]
                    models_in = models_in.split('\n')[0]
                except:
                    models_in = 'all'
                if models_in == 'all':
                    models = ['hysplit', 'fall3d']
                elif models_in == 'hysplit':
                    models = ['hysplit']
                elif models_in == 'fall3d':
                    models = ['fall3d']
                else:
                    print('Wrong model selection')
                    sys.exit()
    tot_dx = lon_max - lon_min
    tot_dy = lat_max - lat_min
    return lat_min, lat_max, lon_min, lon_max, tot_dx, tot_dy, volc_id, n_processes, run_duration, short_simulation, \
           Iceland_scenario, no_refir, er_duration_input, plh_input, mer_input, source_resolution, tot_particle_rate, \
           output_interval, tgsd, run_name, models

def get_times(time):
    twodaysago_t = time - datetime.timedelta(days=2)
    syr = time.strftime('%Y')
    smo = time.strftime('%m')
    sda = time.strftime('%d')
    shr = time.strftime('%H')
    syr_2d = twodaysago_t.strftime('%Y')
    smo_2d = twodaysago_t.strftime('%m')
    sda_2d = twodaysago_t.strftime('%d')
    twodaysago = syr_2d+smo_2d+sda_2d
    shr_wt_st = '{:01d}'.format(int(shr))
    shr_wt_end = str(int(shr_wt_st) + int(run_duration))
    return syr,smo,sda,shr,shr_wt_st,shr_wt_end,twodaysago

def read_esps_database():
    import pandas as pd
    try:
        database = pd.read_excel('https://webapps.bgs.ac.uk/research/volcanoes/esp/volcanoExport.xlsx',
                                 sheetname='volcanoes')
    except:
        database = pd.read_excel('https://webapps.bgs.ac.uk/research/volcanoes/esp/volcanoExport.xlsx',
                                     sheet_name='volcanoes')
    nrows = database.shape[0]
    row = 0
    while True:
        if database['SMITHSONIAN_ID'][row] == volc_id:
            volc_lat = str(database['LATITUDE'][row])
            volc_lon = str(database['LONGITUDE'][row])
            summit = database['ELEVATION_m'][row]
            esps_dur = database['DURATION_hour'][row]
            esps_plh = database['HEIGHT_ABOVE_VENT_km'][row] * 1000
            esps_plh += summit
            esps_mer = database['MASS_ERUPTION_RATES_kg/s'][row]
            break
        else:
            row += 1
            if row >= nrows:
                print('ID not found')
                break
    return esps_dur, esps_plh, esps_mer, summit, volc_lat, volc_lon

def run_foxi():
    copy(os.path.join(ROOT, 'fix_config.txt'), os.path.join(REFIR, 'fix_config.txt'))
    fix_config_file = os.path.join(REFIR, 'fix_config.txt')
    REFIR_CONFIG = os.path.join(REFIR, 'refir_config')
    REFIR_CONFIG_OPERATIONAL = os.path.join(REFIR_CONFIG,'operational_setting')
    print('Storing configuration files in ' + REFIR_CONFIG_OPERATIONAL)
    setting_files = os.listdir(REFIR_CONFIG)
    try:
        os.mkdir(REFIR_CONFIG_OPERATIONAL)
    except FileExistsError:
        print('Folder ' + REFIR_CONFIG_OPERATIONAL + ' already exists')
    for file in setting_files:
        if file.endswith('ini'):
            copy(os.path.join(REFIR_CONFIG,file),os.path.join(REFIR_CONFIG_OPERATIONAL,file))
    fix_config_records = []
    with open(fix_config_file, 'r', encoding="utf-8", errors="surrogateescape") as fix_config:
        for line in fix_config:
            fix_config_records.append(line.split('\n')[0])
    try:
        esps_dur, esps_plh, dummy, summit, volc_lat, volc_lon = read_esps_database()
    except:
        print('Unable to read ESPs database')
        sys.exit()
    if er_duration_input[0] != 999:
        esps_dur = er_duration_input[0]
    if esps_dur > run_duration:
        esps_dur = run_duration

    if short_simulation:
        time_end = time_now + datetime.timedelta(minutes=5)
    else:
        time_end = time_now + datetime.timedelta(hours=esps_dur)

    start_time = datetime.datetime.strftime(time_now, "%Y-%m-%d %H:%M:%S")
    stop_time = datetime.datetime.strftime(time_end, "%Y-%m-%d %H:%M:%S")

    if Iceland_scenario:
        if volc_id == 372020:
            volc_number = 0
        elif volc_id == 372030:
            volc_number = 1
        elif volc_id == 372070:
            volc_number = 2
        elif volc_id == 373010:
            volc_number = 3
        elif volc_id == 372010:
            volc_number = 4
        elif volc_id == 373050:
            volc_number = 7
        elif volc_id == 374010:
            volc_number = 8
        elif volc_id == 371020:
            volc_number = 9
        elif volc_id == 371030:
            volc_number = 10
    else:
        volc_number = 0
    if source_resolution == 15:
        refir_PM_TAV = 1
    elif source_resolution == 30:
        refir_PM_TAV = 2
    elif source_resolution == 60:
        refir_PM_TAV = 3
    elif source_resolution == 180:
        refir_PM_TAV = 4
    elif source_resolution == 360:
        refir_PM_TAV = 5
    else:
        refir_PM_TAV = 0
    with open(fix_config_file, 'w', encoding="utf-8", errors="surrogateescape") as fix_config:
        for i in range(0, len(fix_config_records)):
            if i == 0:
                fix_config.write(str(volc_number) + '\n')
            elif i == 36:
                fix_config.write(str(summit) + '\n')
            elif i == 163:
                fix_config.write('2\n')
            elif i == 164:
                fix_config.write('1\n')
            elif i == 166:
                fix_config.write(start_time + '\n')
            elif i == 167:
                fix_config.write(stop_time + '\n')
            elif i == 169:
                fix_config.write(str(refir_PM_TAV) + '\n')
            elif i == 172:
                fix_config.write('1\n')
            elif i == 173:
                fix_config.write(str(esps_dur) + '\n')
            elif i == 174:
                fix_config.write(str(esps_plh) + '\n')
            elif i == 177:
                fix_config.write('1\n')
            else:
                fix_config.write(fix_config_records[i] + '\n')

    os.chdir(REFIR)
    if no_refir_plots:
        foxi_command = 'python FOXI.py -M background -N operational -NP True'
    else:
        foxi_command = 'python FOXI.py -M background -N operational'
    os.system(foxi_command)
    os.chdir(ROOT)
    return esps_dur, esps_plh, summit, volc_lat, volc_lon

def run_refir():
    REFIR_CONFIG = os.path.join(REFIR,'refir_config')
    REFIR_CONFIG_OPERATIONAL = os.path.join(REFIR_CONFIG, 'operational_setting')
    os.system('source activate refir')
    os.chdir(REFIR_CONFIG)
    foxset_command = 'python FoxSet.py'
    os.system(foxset_command)
    os.chdir(REFIR)
    fix_command = 'python FIX.py &'
    os.system(fix_command)
    foxi_command = 'python FOXI.py'
    os.system(foxi_command)
    try:
        dummy1, dummy2, dummy3, summit, volc_lat, volc_lon = read_esps_database()
    except:
        volcano_list_file = os.path.join(REFIR_CONFIG, 'volcano_list.ini')
        with open(volcano_list_file,'r',encoding="utf-8", errors="surrogateescape") as volcano_list:
            for line in volcano_list:
                try:
                    if int(line.split('\t')[0]) == volc_id:
                        volc_lat = line.split('\t')[1]
                        volc_lon = line.split('\t')[2]
                        summit = float(line.split('\t')[3])
                except:
                    continue
    paths = []
    files = os.listdir(REFIR)
    for file in files:
        if os.path.isdir(file):
            paths.append(os.path.join(REFIR, file))
    latest_run_path = max(paths, key=os.path.getmtime)
    refir_run = os.path.join(REFIR, latest_run_path)
    refir_config = os.path.join(refir_run, 'fix_config.txt')
    with open(refir_config, 'r',encoding="utf-8", errors="surrogateescape") as refir_config_r:
        lines = []
        for line in refir_config_r:
            lines.append(line)
    if er_duration_input[0] != 999:
        er_dur = er_duration_input[0]
    else:
        er_dur = lines[173] # This is updated by FIX if the ESPs usage is activated in FIX. Otherwise this is 0.
        er_dur = float(er_dur.split('\n')[0])
    if er_dur > run_duration or er_dur == 0:
        er_dur = run_duration
    print('Restoring pre-existing coniguration files in ' + REFIR_CONFIG)
    original_config_files = os.listdir(REFIR_CONFIG_OPERATIONAL)
    for file in original_config_files:
        copy(os.path.join(REFIR_CONFIG_OPERATIONAL,file),REFIR_CONFIG)
    os.chdir(ROOT)
    return er_dur, summit, volc_lat, volc_lon

def run_models(short_simulation, eruption_dur):
    def read_refir_outputs(short_simulation):
        files = os.listdir(REFIR)
        paths = []
        mer_file = ''
        plh_file = ''
        tavg_plh_file = ''
        tavg_mer_file = ''
        refir_run_name = ''
        for file in files:
            file_path = os.path.join(REFIR,file)
            if os.path.isdir(file_path) and file.startswith('run_'):
                paths.append(file_path)
        latest_run_path = max(paths, key=os.path.getmtime)
        refir_run = os.path.join(REFIR,latest_run_path)
        files = os.listdir(refir_run)
        for file in files:
            if file.endswith('_STATUS_REPORT.txt'):
                refir_run_name = file.split('_STATUS_REPORT.txt')[0]  # Get REFIR run name
        for file in files:
            if file.endswith('tavg_FMER.txt'):
                tavg_mer_file = os.path.join(refir_run, file)
            elif file.endswith('tavg_PLH.txt'):
                tavg_plh_file = os.path.join(refir_run, file)
            elif mode == 'manual' and file == refir_run_name + '_FMER.txt':
                mer_file = os.path.join(refir_run, file)
            elif mode == 'manual' and file == refir_run_name + '_PLH.txt':
                plh_file = os.path.join(refir_run, file)
            elif mode == 'operational' and file == 'operational_FMER.txt':
                mer_file = os.path.join(refir_run, file)
            elif mode == 'operational' and file == 'operational_PLH.txt':
                plh_file = os.path.join(refir_run, file)
        if mode == 'manual':
            lines = 0
            with open(mer_file, 'r', encoding="utf-8", errors="surrogateescape") as mer_file_r:
                for line in mer_file_r:
                    lines += 1
            if lines == 2:
                short_simulation = True  # always convert to a short simulation if REFIR has been run manually for
                # one time step only
            else:
                short_simulation = False
            mer_file_r.close()
        new_er_dur = 0
        if short_simulation:
            with open(mer_file, 'r', encoding="utf-8", errors="surrogateescape") as mer_file_r:
                mer_min = ''
                mer_avg = ''
                mer_max = ''
                for line in mer_file_r:
                    try:
                        minute = int(line.split('\t')[1])
                        mer_min = line.split('\t')[2]
                        mer_min = mer_min.split('.')[0]
                        mer_avg = line.split('\t')[3]
                        mer_avg = mer_avg.split('.')[0]
                        mer_max = line.split('\t')[4]
                        mer_max = mer_max.split('\n')[0]
                        mer_max = mer_max.split('.')[0]
                    except:
                        continue
            with open(plh_file, 'r', encoding="utf-8", errors="surrogateescape") as plh_file_r:
                plh_min = ''
                plh_avg = ''
                plh_max = ''
                for line in plh_file_r:
                    try:
                        minute = int(line.split('\t')[1])
                        plh_min = line.split('\t')[2]
                        plh_min = plh_min.split('.')[0]
                        plh_avg = line.split('\t')[3]
                        plh_avg = plh_avg.split('.')[0]
                        plh_max = line.split('\t')[4]
                        plh_max = plh_max.split('\n')[0]
                        plh_max = plh_max.split('.')[0]
                    except:
                        continue
        else:
            lines = 0
            with open(tavg_mer_file, 'r', encoding="utf-8", errors="surrogateescape") as mer_file_r:
                for line in mer_file_r:
                    lines += 1
            mer_min = ''
            mer_avg = ''
            mer_max = ''
            if lines == 1:
                mer_file_r = open(mer_file, 'r', encoding="utf-8", errors="surrogateescape")
            else:
                mer_file_r = open(tavg_mer_file, 'r', encoding="utf-8", errors="surrogateescape")
            for line in mer_file_r:
                try:
                    minute = int(line.split('\t')[1])
                    new_er_dur = minute
                    if minute % source_resolution == 0 or (minute - 1) % source_resolution == 0 or (minute + 1) % \
                            source_resolution == 0:
                        mer_min_tmp = line.split('\t')[2]
                        mer_min_tmp = mer_min_tmp.split('.')[0]
                        mer_min += ' ' + mer_min_tmp
                        mer_avg_tmp = line.split('\t')[3]
                        mer_avg_tmp = mer_avg_tmp.split('.')[0]
                        mer_avg += ' ' + mer_avg_tmp
                        mer_max_tmp = line.split('\t')[4]
                        mer_max_tmp = mer_max_tmp.split('.')[0]
                        mer_max += ' ' + mer_max_tmp
                except:
                    continue
            mer_file_r.close()
            lines = 0
            with open(tavg_plh_file, 'r', encoding="utf-8", errors="surrogateescape") as plh_file_r:
                for line in plh_file_r:
                    lines += 1
            plh_min = ''
            plh_avg = ''
            plh_max = ''
            if lines == 1:
                plh_file_r = open(plh_file, 'r', encoding="utf-8", errors="surrogateescape")
            else:
                plh_file_r = open(tavg_plh_file, 'r', encoding="utf-8", errors="surrogateescape")
            for line in plh_file_r:
                try:
                    minute = int(line.split('\t')[1])
                    if minute % source_resolution == 0 or (minute - 1) % source_resolution == 0 or (minute + 1) % \
                            source_resolution == 0:
                        plh_min_tmp = line.split('\t')[2]
                        plh_min_tmp = plh_min_tmp.split('.')[0]
                        plh_min += ' ' + plh_min_tmp
                        plh_avg_tmp = line.split('\t')[3]
                        plh_avg_tmp = plh_avg_tmp.split('.')[0]
                        plh_avg += ' ' + plh_avg_tmp
                        plh_max_tmp = line.split('\t')[4]
                        plh_max_tmp = plh_max_tmp.split('.')[0]
                        plh_max += ' ' + plh_max_tmp
                except:
                    continue
            plh_file_r.close()
            if 0 < new_er_dur < source_resolution:
                mer_min_new = 0
                mer_avg_new = 0
                mer_max_new = 0
                plh_min_new = 0
                plh_avg_new = 0
                plh_max_new = 0
                plh_min = ''
                plh_avg = ''
                plh_max = ''
                mer_min = ''
                mer_avg = ''
                mer_max = ''
                mer_file_r = open(mer_file, 'r', encoding="utf-8", errors="surrogateescape")
                minute_old = 0
                for line in mer_file_r:
                    try:
                        minute = int(line.split('\t')[1])
                        delta_min = minute - minute_old
                        mer_min_tmp = line.split('\t')[2]
                        mer_min_tmp = mer_min_tmp.split('.')[0]
                        mer_min_new += float(mer_min_tmp) * delta_min
                        mer_avg_tmp = line.split('\t')[3]
                        mer_avg_tmp = mer_avg_tmp.split('.')[0]
                        mer_avg_new += float(mer_avg_tmp) * delta_min
                        mer_max_tmp = line.split('\t')[4]
                        mer_max_tmp = mer_max_tmp.split('.')[0]
                        mer_max_new += float(mer_max_tmp) * delta_min
                        minute_old = minute
                    except:
                        continue
                mer_min_new = mer_min_new / new_er_dur
                mer_min += ' ' + '{:.0f}'.format(mer_min_new)
                mer_avg_new = mer_avg_new / new_er_dur
                mer_avg += ' ' + '{:.0f}'.format(mer_avg_new)
                mer_max_new = mer_max_new / new_er_dur
                mer_max += ' ' + '{:.0f}'.format(mer_max_new)
                mer_file_r.close()
                plh_file_r = open(plh_file, 'r', encoding="utf-8", errors="surrogateescape")
                minute_old = 0
                for line in plh_file_r:
                    try:
                        minute = int(line.split('\t')[1])
                        delta_min = minute - minute_old
                        plh_min_tmp = line.split('\t')[2]
                        plh_min_tmp = plh_min_tmp.split('.')[0]
                        plh_min_new += float(plh_min_tmp) * delta_min
                        plh_avg_tmp = line.split('\t')[3]
                        plh_avg_tmp = plh_avg_tmp.split('.')[0]
                        plh_avg_new += float(plh_avg_tmp) * delta_min
                        plh_max_tmp = line.split('\t')[4]
                        plh_max_tmp = plh_max_tmp.split('.')[0]
                        plh_max_new += float(plh_max_tmp) * delta_min
                        minute_old = minute
                    except:
                        continue
                plh_min_new = plh_min_new / new_er_dur
                plh_min += ' ' + '{:.0f}'.format(plh_min_new)
                plh_avg_new = plh_avg_new / new_er_dur
                plh_avg += ' ' + '{:.0f}'.format(plh_avg_new)
                plh_max_new = plh_max_new / new_er_dur
                plh_max += ' ' + '{:.0f}'.format(plh_max_new)
                plh_file_r.close()
#            else:
#                new_er_dur = 0
        return mer_avg, mer_max, mer_min, plh_avg, plh_max, plh_min, short_simulation, new_er_dur

    def controller(model):
        def run_fall3d():
            GFSGRIB = os.path.join(ROOT, 'weather', 'data', mode)
            FALL3D = '/home/vulcanomod/FALL3D/fall3d-8.0.1/bin/Fall3d.r8.x'
            FALL3D_RUNS = os.path.join(RUNS, 'FALL3D')
            try:
                os.mkdir(FALL3D_RUNS)
            except FileExistsError:
                print('Folder ' + FALL3D_RUNS + ' exists')
            WTDATA = os.path.join(GFSGRIB, syr + smo + sda, run_folder, mode + '.nc')
            RUNS_DAY = os.path.join(FALL3D_RUNS, syr + smo + sda)
            try:
                os.mkdir(RUNS_DAY)
            except FileExistsError:
                print('Folder ' + RUNS_DAY + ' exists')
            RUNS_TIME = os.path.join(RUNS_DAY, run_folder)
            try:
                os.mkdir(RUNS_TIME)
            except FileExistsError:
                print('Folder ' + RUNS_TIME + ' exists')
            OP_INPUT = os.path.join(FALL3D_RUNS, mode + '_fall3d.inp')

            def update_input_files(mer, plh, er_dur, solution):
                def distribute_processes(n):
                    n = n / len(solutions)
                    npx = int(n ** (1 / 3))
                    npy = npx
                    npz = npx
                    if npx ** 3 < n:
                        npx += 1
                        npy = npx
                        npz = npx - 1
                        np = npx * npy * npz
                        if np > n:
                            npy -= 1
                            np = npx * npy * npz
                            if np > n:
                                npx -= 1
                    while n_levels / npz < 4:
                        npz -= 1
                    np = npx * npy * npz
                    return np, npx, npy, npz

                def convert_to_decimal(time_input):
                    hours = float(datetime.datetime.strftime(time_input, "%H"))
                    minutes = int(datetime.datetime.strftime(time_input, "%M"))
                    decimal_time = hours + minutes / 60
                    return decimal_time

                RUN = os.path.join(RUNS_TIME, solution)
                try:
                    os.mkdir(RUN)
                except FileExistsError:
                    print('Folder ' + RUN + ' exists')
                INPUT = os.path.join(RUN, mode + '_' + solution + '.inp')
                copyfile(OP_INPUT,INPUT)
                TGSD_FILE = os.path.join(RUN, mode + '_' + solution + '.tgsd.tephra')
                copyfile(os.path.join(TGSDS,tgsd),TGSD_FILE)
                if not short_simulation:
                    mer_vector = mer.split(' ')
                    mer_vector = mer_vector[1:]
                    plh_vector = plh.split(' ')
                    plh_vector = plh_vector[1:]
                else:
                    mer_vector = []
                    mer_vector.append(mer)
                    plh_vector = []
                    plh_vector.append(plh)
                mer_string = ''
                plh_abv = ''
                max_altitude = 0
                for i in range(0,len(plh_vector)):
                    if float(plh_vector[i]) > max_altitude:
                        max_altitude = float(plh_vector[i])
                    if no_refir:
                        plh_abv += str(float(plh_vector[i]) - summit)  + ' '
                    else:
                        plh_abv += str(float(plh_vector[i])) + ' '    # FALL3D wants height above vent, which is what
                        # REFIR produces
                    mer_string += mer_vector[i] + ' '
                max_altitude += 8000
                max_altitude = round(max_altitude, -3)
                dz = 1000
                n_levels = int(max_altitude / dz + 1)
                source_start_string = ''
                source_end_string = ''
                levels = '0'
                altitude = 0
                while altitude < max_altitude:
                    altitude += dz
                    levels += ' ' + str(int(altitude))
                time_emission = time_now
                if not short_simulation:
                    effective_time_end_emission = time_emission + datetime.timedelta(hours=er_dur)
                    time_end_emission = time_emission + datetime.timedelta(minutes=source_resolution)
                    decimal_time_start = convert_to_decimal(time_emission)
                    decimal_time_end = decimal_time_start + source_resolution / 60
                    while True:
                        if time_end_emission >= effective_time_end_emission:
                            delta_time = (time_end_emission - effective_time_end_emission).seconds
                            decimal_time_end -= delta_time / 3600
                            source_start_string += '{:.1f}'.format(decimal_time_start) + ' '
                            source_end_string += '{:.1f}'.format(decimal_time_end) + ' '
                            break
                        else:
                            source_start_string += '{:.1f}'.format(decimal_time_start) + ' '
                            source_end_string += '{:.1f}'.format(decimal_time_end) + ' '
                            decimal_time_start += source_resolution / 60
                            decimal_time_end += source_resolution / 60
                            time_end_emission += datetime.timedelta(minutes=source_resolution)
                else:
                    decimal_time_start = convert_to_decimal(time_emission)
                    source_start_string += '{:.1f}'.format(decimal_time_start)
                    decimal_time_end = decimal_time_start + er_dur
                    source_end_string += '{:.1f}'.format(decimal_time_end)
                np, npx, npy, npz = distribute_processes(n_processes)
                lines = []
                with open(INPUT, 'r', encoding="utf-8", errors="surrogateescape") as fall3d_input:
                    for line in fall3d_input:
                        try:
                            record = line.split(' = ')
                            if record[0] == '   YEAR ':
                                line = record[0] + ' = ' + syr + '\n'
                            elif record[0] == '   MONTH':
                                line = record[0] + ' = ' + smo + '\n'
                            elif record[0] == '   DAY  ':
                                line = record[0] + ' = ' + sda + '\n'
                            elif record[0] == '   RUN_START_(HOURS_AFTER_00)':
                                line = record[0] + ' = ' + shr + '\n'
                            elif record[0] == '   RUN_END_(HOURS_AFTER_00)  ':
                                line = record[0] + ' = ' + shr_wt_end + '\n'
                            elif record[0] == '   METEO_DATA_FILE           ':
                                line = record[0] + ' = ' + WTDATA + '\n'
                            elif record[0] == '   DBS_BEGIN_METEO_DATA_(HOURS_AFTER_00)':
                                line = record[0] + ' = ' + shr_wt_st + '\n'
                            elif record[0] == '   DBS_END_METEO_DATA_(HOURS_AFTER_00)  ':
                                line = record[0] + ' = ' + shr_wt_end + '\n'
                            elif record[0] == '   LONMIN':
                                line = record[0] + ' = ' + '{:.2f}'.format(float(lon_min)) + '\n'
                            elif record[0] == '   LONMAX':
                                line = record[0] + ' = ' + '{:.2f}'.format(float(lon_max)) + '\n'
                            elif record[0] == '   LATMIN':
                                line = record[0] + ' = ' + '{:.2f}'.format(float(lat_min)) + '\n'
                            elif record[0] == '   LATMAX':
                                line = record[0] + ' = ' + '{:.2f}'.format(float(lat_max)) + '\n'
                            elif record[0] == '   NZ':
                                line = record[0] + ' = ' + str(n_levels) + '\n'
                            elif record[0] == '   ZMAX_(M)':
                                line = record[0] + ' = ' + str(max_altitude) + '\n'
                            elif record[0] == '   SOURCE_START_(HOURS_AFTER_00)':
                                line = record[0] + ' = ' + source_start_string + '\n'
                            elif record[0] == '   SOURCE_END_(HOURS_AFTER_00)  ':
                                line = record[0] + ' = ' + source_end_string + '\n'
                            elif record[0] == '   LON_VENT       ':
                                line = record[0] + ' = ' + '{:.2f}'.format(float(volc_lon)) + '\n'
                            elif record[0] == '   LAT_VENT       ':
                                line = record[0] + ' = ' + '{:.2f}'.format(float(volc_lat)) + '\n'
                            elif record[0] == '   VENT_HEIGHT_(M)':
                                line = record[0] + ' = ' + str(summit) + '\n'
                            elif record[0] == '   HEIGHT_ABOVE_VENT_(M)        ':
                                line = record[0] + ' = ' + plh_abv + '\n'
                            elif record[0] == '   MASS_FLOW_RATE_(KGS)         ':
                                line = record[0] + ' = ' + mer_string + '\n'
                            elif record[0] == '      THICKNESS_(M)':
                                line = record[0] + ' = ' + plh_abv + '\n'
                            elif record[0] == '   OUTPUT_TIME_INTERVAL_(HOURS) ':
                                line = record[0] + ' = ' + output_interval + '\n'
                            try:
                                record = line.split('VALUES')
                                if record[0] == '      Z-':
                                    line = record[0] + 'VALUES ' + levels[2:] + '\n'
                            except:
                                None
                        except:
                                None
                        lines.append(line)
                with open(INPUT,'w',encoding="utf-8", errors="surrogateescape") as fall3d_input:
                    fall3d_input.writelines(lines)
                return np, npx, npy, npz


            processes_distributions = []
            if not no_refir:
                processes_distributions.append(update_input_files(mer_avg, plh_avg, eruption_dur, 'avg'))
                processes_distributions.append(update_input_files(mer_max, plh_max, eruption_dur, 'max'))
                processes_distributions.append(update_input_files(mer_min, plh_min, eruption_dur, 'min'))
            else:
                for i in range(0, len(solutions)):
                    processes_distributions.append(update_input_files(str(eruption_mer[i]), str(eruption_plh[i]),
                                                                      eruption_dur[i], solutions[i]))


            def run_fall3d_mpi(solution, processes):
                RUN = os.path.join(RUNS_TIME, solution)
                INPUT = os.path.join(RUN, mode + '_' + solution + '.inp')
                np = processes[0]
                npx = processes[1]
                npy = processes[2]
                npz = processes[3]
                command_setdbs = 'mpirun -n ' + str(np) + ' ' + FALL3D + ' SetDbs ' + INPUT + ' ' + str(npx) + ' ' + \
                                 str(npy) + ' ' + str(npz) + '\n'
                command_setsrc = FALL3D + ' SetSrc ' + INPUT + '\n'
                command_fall3d = 'mpirun -n ' + str(np) + ' ' + FALL3D + ' Fall3D ' + INPUT + ' ' + str(npx) + ' ' + \
                                 str(npy) + ' ' + str(npz) + '\n'
                fall3d_script = os.path.join(RUN, 'fall3d.sh')
                copy(os.path.join(RUNS, 'FALL3D', 'fall3d.sh'), fall3d_script)
                lines = []
                if which('sbatch') is None:
                    with open(fall3d_script, 'r', encoding="utf-8", errors="surrogateescape") as fall3d_script_input:
                        for line in fall3d_script_input:
                            if '#SBATCH' not in line or '##' not in line:
                                lines.append(line)
                    lines.append(command_setdbs)
                    lines.append(command_setsrc)
                    lines.append(command_fall3d)
                    lines.append('wait\n')
                    with open(fall3d_script, 'w', encoding="utf-8", errors="surrogateescape") as fall3d_script_input:
                        fall3d_script_input.writelines(lines)
                    os.system('sh ' + fall3d_script)
                else:
                    with open(fall3d_script, 'r', encoding="utf-8", errors="surrogateescape") as fall3d_script_input:
                        for line in fall3d_script_input:
                            if '#SBATCH -n' in line:
                                lines.append('#SBATCH -n ' + str(np) + '\n')
                            else:
                                lines.append(line)
                    lines.append(command_setdbs)
                    lines.append(command_setsrc)
                    lines.append(command_fall3d)
                    lines.append('wait\n')
                    with open(fall3d_script, 'w', encoding="utf-8", errors="surrogateescape") as fall3d_script_input:
                        fall3d_script_input.writelines(lines)
                    os.system('sbatch -W ' + fall3d_script)

            try:
                pool_fall3d = ThreadingPool(len(solutions))
                pool_fall3d.map(run_fall3d_mpi, solutions, processes_distributions)
            except:
                print('Error processing FALL3D in parallel')


        def run_hysplit():
            ARL = os.path.join(ROOT, 'weather', 'data', mode)
            HYSPLIT = '/home/vulcanomod/HYSPLIT/hysplit.v5.2.0/exec'
            HYSPLIT_RUNS = os.path.join(RUNS, 'HYSPLIT')
            try:
                os.mkdir(HYSPLIT_RUNS)
            except FileExistsError:
                print('Folder ' + HYSPLIT_RUNS + ' exists')
            ASCDATA = os.path.join(HYSPLIT_RUNS, 'ASCDATA.CFG')
            SETUP = os.path.join(HYSPLIT_RUNS, 'SETUP.CFG')
            WTDATA = os.path.join(ARL, syr + smo + sda, run_folder)
            HYSPLIT_RUNS_DAY = os.path.join(HYSPLIT_RUNS, syr + smo + sda)
            try:
                os.mkdir(HYSPLIT_RUNS_DAY)
            except FileExistsError:
                print('Folder ' + HYSPLIT_RUNS_DAY + ' exists')
            SIM = os.path.join(HYSPLIT_RUNS_DAY, run_folder)
            try:
                os.mkdir(SIM)
            except FileExistsError:
                print('Folder ' + SIM + ' exists')

            def read_tgsd_file(tgsd_in):
                # Read grainsize distribution
                tgsd_file = os.path.join(TGSDS, tgsd_in)
                bins_records = []
                wt_fraction = []
                diam = []
                diam_strings = []
                rho = []
                rho_strings = []
                shape = []
                shape_strings = []
                wt_fraction_strings = []
                pollutants = []
                pollutants_strings = []
                with open(tgsd_file, 'r', encoding="utf-8", errors="surrogateescape") as tgsd_records:
                    for line in tgsd_records:
                        bins_records.append(line)
                n_bins = bins_records[0].split('  ')[1]
                n_bins = n_bins.split('\n')[0]
                for i in range(1, len(bins_records)):
                    wt_fraction.append(0.0)
                    diam.append(0.0)
                    rho.append(0.0)
                    shape.append(0.0)
                for i in range(1, len(bins_records)):
                    diam[i - 1] = bins_records[i].split('  ')[1]
                    rho[i - 1] = bins_records[i].split('  ')[2]
                    shape[i - 1] = bins_records[i].split('  ')[3]
                    wt_fraction[i-1] = bins_records[i].split('  ')[4]
                    wt_fraction_strings.append('wt_fr[' + str(i) + ']')
                    diam_strings.append('diam[' + str(i) + ']')
                    rho_strings.append('rho[' + str(i) + ']')
                    shape_strings.append('shape[' + str(i) + ']')
                    if i < 10:
                        pollutants.append('AS0' + str(i))
                    else:
                        pollutants.append('AS' + str(i))
                    pollutants_strings.append('poll[' + str(i) + ']')

                return n_bins, diam, rho, shape, wt_fraction, pollutants, diam_strings, rho_strings, shape_strings, \
                       wt_fraction_strings, pollutants_strings

            def update_control_files(mer, plh, er_dur, solution):
                SIM_solution = os.path.join(SIM, solution)
                met = mode + '.arl'
                ADD_WTDATA = ARL
                metdata = 'oct1618.BIN'
                try:
                    os.mkdir(SIM_solution)
                except FileExistsError:
                    print('Folder ' + SIM_solution + ' exists')
                os.chdir(SIM_solution)
                syr_2ch = syr[2:4]
                em_rates = []
                if not short_simulation:
                    plh_vector = plh.split(' ')
                    plh_vector = plh_vector[1:]
                else:
                    plh_vector = []
                    plh_vector.append(plh)
                for i in range(0, len(plh_vector)):
                    if no_refir:
                        plh_vector[i] = float(plh_vector[i])
                    else:
                        plh_vector[i] = float(plh_vector[i]) + summit  # Currently HYSPLIT is setup to use heights
                        # asl (see SETUP.CFG) but this can be changed back to above ground
                max_altitude = max(plh_vector) + 8000
                if short_simulation == False: # HYSPLIT will use EMITIMES
                    efile = 'EMITIMES'
                    for i in range(0, len(wt_fraction)):
                        em_rates.append(0.0)  # Here divide per the number of processes
                    em_duration = '0.0'
                else:
                    mer = float(mer) * 3600.0 * 1000 #Convert in g/h for HYSPLIT
                    efile = ''
                    for i in range(0, len(wt_fraction)):
                        em_rates.append(mer * float(wt_fraction[i]))
                    em_duration = str(er_dur)
                n_source_locations = 2 * len(plh_vector)
                max_altitude = round(max_altitude, -3)
                dz = 1000
                n_levels = int(max_altitude / dz + 1)
                levels = '0'
                altitude = 0
                while altitude < max_altitude:
                    altitude += dz
                    levels += ' ' + str(int(altitude))
                tot_particles = tot_particle_rate * er_dur
                with open('CONTROL', 'w', encoding="utf-8", errors="surrogateescape") as control_file:
                    control_file.write(syr_2ch + ' ' + smo + ' ' + sda + ' ' + shr + '\n')
                    control_file.write(str(n_source_locations) + '\n')
                    for j in range(0, len(plh_vector)):
                        control_file.write('{:.2f}'.format(float(volc_lat)) + ' ' +
                                           '{:.2f}'.format(float(volc_lon)) + ' ' + str(summit) + '\n')
                        control_file.write('{:.2f}'.format(float(volc_lat)) + ' ' +
                                           '{:.2f}'.format(float(volc_lon)) + ' ' +
                                           '{:.2f}'.format(float(plh_vector[j])) + '\n')
                    control_file.write(str(run_duration) + '\n')
                    control_file.write('0\n')
                    control_file.write(str(max_altitude) + '\n')
                    control_file.write('2\n')
                    control_file.write(WTDATA + '/\n')
                    control_file.write(met + '\n')
                    control_file.write(ADD_WTDATA + '/\n')
                    control_file.write(metdata + '\n')
                    control_file.write(n_bins + '\n')
                    for i in range(1, int(n_bins) + 1):
                        control_file.write(pollutants[i - 1] + '\n')
                        control_file.write('{:.1f}'.format(em_rates[i - 1]) + '\n')
                        control_file.write(em_duration + '\n')
                        control_file.write(syr_2ch + ' ' + smo + ' ' + sda + ' ' + shr + ' 00\n')
                    control_file.write('1\n')
                    control_file.write('{:.1f}'.format(grid_centre_lat) + ' ' +
                                       '{:.1f}'.format(grid_centre_lon) + '\n')
                    control_file.write('0.05 0.05\n')
                    control_file.write(str(tot_dy) + ' ' + str(tot_dx) + '\n')
                    control_file.write('./\n')
                    control_file.write('cdump\n')
                    control_file.write(str(n_levels) + '\n')
                    control_file.write(levels + '\n')
                    control_file.write(syr_2ch + ' ' + smo + ' ' + sda + ' ' + shr + ' 00\n')
                    control_file.write('99 12 31 24 60\n')
                    control_file.write('00 ' + output_interval + ' 00\n')
                    control_file.write(n_bins + '\n')
                    for i in range(1, int(n_bins) + 1):
                        diam_micron = float(diam[i - 1]) * 1000.0
                        rho_gcc = float(rho[i - 1]) / 1000.0
                        control_file.write('{:.2f}'.format(diam_micron) + ' ' + '{:.1f}'.format(rho_gcc) + ' ' +
                                           shape[i - 1] + '\n')
                        control_file.write('0.0 0.0 0.0 0.0 0.0\n')
                        control_file.write('0.0 0.0 0.0\n')
                        control_file.write('0.0\n')
                        control_file.write('0.0\n')
                    copyfile(SETUP, os.path.join(os.getcwd(), 'SETUP.CFG'))
                    lines = []
                    with open('SETUP.CFG', 'r', encoding="utf-8", errors="surrogateescape") as setup_file:
                        for line in setup_file:
                            record = line.split(' = ')
                            if record[0] == ' numpar':
                                line = record[0] + ' = ' + str(int(tot_particle_rate)) + ',\n'
                            elif record[0] == ' maxpar':
                                line = record[0] + ' = ' + str(int(tot_particles)) + ',\n'
                            elif record[0] == ' efile':
                                line = record[0] + ' = \'' + efile  + '\',\n'
                            lines.append(line)
                    with open('SETUP.CFG', 'w', encoding="utf-8", errors="surrogateescape") as setup_file:
                        setup_file.writelines(lines)
                    copyfile(ASCDATA, os.path.join(os.getcwd(), 'ASCDATA.CFG'))
                return

            def create_emission_file(mer, plh, er_dur, wt, solution):
                SIM_solution = os.path.join(SIM, solution)
                try:
                    os.mkdir(SIM_solution)
                except FileExistsError:
                    print('Folder ' + SIM_solution + ' exists')
                emission_file = os.path.join(SIM_solution, 'EMITIMES')
                mer_vector = mer.split(' ')
                mer_vector = mer_vector[1:]
                plh_vector = plh.split(' ')
                plh_vector = plh_vector[1:]
                n_records = 0
                time = 0
                em_file_records = []
                em_file_records.append('YYYY MM DD HH DURATION(hhhh) #RECORDS\n')
                em_file_records.append('YYYY MM DD HH MM DURATION(hhmm) LAT LON HGT(m) RATE(/h) AREA(m2) HEAT(w)\n')
                start_time_short = datetime.datetime.strftime(time_now, "%Y %m %d %H")
                time_emission = time_now
                eruption_dur_s = '{:03d}'.format(int(round(er_dur + 0.49)))
                em_file_records.append(start_time_short + ' ' + eruption_dur_s + ' ' + str(n_records) + '\n')
                effective_time_end_emission = time_emission + datetime.timedelta(hours=er_dur)
                while True:
                    time_end_emission = time_emission + datetime.timedelta(minutes=source_resolution)
                    if time_end_emission >= effective_time_end_emission:
                        time_emission_s = datetime.datetime.strftime(time_emission, "%Y %m %d %H %M")
                        time_difference = time_end_emission - effective_time_end_emission
                        time_end_emission -= time_difference
                        time_step_s = ' '
                        time_step_minutes = source_resolution
                        time_step_hours = int(time_step_minutes / 60)
                        if time_step_hours >= 1:
                            remainder = time_step_minutes % 60
                        else:
                            remainder = time_step_minutes
                        time_step_s += '{:02d}'.format(time_step_hours)
                        time_step_s += '{:02d}'.format(remainder) + ' '
                        plh = float(plh_vector[time]) + summit
                        for j in range(0, len(wt)):
                            mer_bin = float(mer_vector[time]) * 3600 * 1000 * float(wt[j])
                            em_file_records.append(time_emission_s + time_step_s + volc_lat + ' ' + volc_lon + ' ' +
                                               str(summit) + ' ' + '{:.5E}'.format(mer_bin) + ' 0.0 0.0\n')
                            n_records += 1
                        for j in range(0, len(wt)):
                            mer_bin = float(mer_vector[time]) * 3600 * 1000 * float(wt[j])
                            em_file_records.append(time_emission_s + time_step_s + volc_lat + ' ' + volc_lon + ' ' +
                                                   '{:.1f}'.format(plh) + ' ' + '{:.5E}'.format(mer_bin) + ' 0.0 0.0\n')
                            n_records += 1
                        break
                    else:
                        time_emission_s = datetime.datetime.strftime(time_emission, "%Y %m %d %H %M")
                        time_step_s = ' '
                        time_step_minutes = source_resolution
                        time_step_hours = int(time_step_minutes / 60)
                        if time_step_hours >= 1:
                            remainder = time_step_minutes % 60
                        else:
                            remainder = time_step_minutes
                        time_step_s += '{:02d}'.format(time_step_hours)
                        time_step_s += '{:02d}'.format(remainder) + ' '
                        plh = float(plh_vector[time]) + summit
                        for j in range(0, len(wt)):
                            mer_bin = float(mer_vector[time]) * 3600 * 1000 * float(wt[j])
                            em_file_records.append(time_emission_s + time_step_s + volc_lat + ' ' + volc_lon + ' '
                                               + str(summit) + ' ' + '{:.5E}'.format(mer_bin) + ' 0.0 0.0\n')
                            n_records += 1
                        for j in range(0, len(wt)):
                            mer_bin = float(mer_vector[time]) * 3600 * 1000 * float(wt[j])
                            em_file_records.append(time_emission_s + time_step_s + volc_lat + ' ' + volc_lon + ' '
                                               + '{:.1f}'.format(plh) + ' ' + '{:.5E}'.format(mer_bin) + ' 0.0 0.0\n')
                            n_records += 1
                        time += 1
                        time_emission += datetime.timedelta(minutes=source_resolution)
                        time_end_emission += datetime.timedelta(minutes=source_resolution)
                em_file_records[2] = start_time_short + ' ' + eruption_dur_s + ' ' + str(n_records) + '\n'  # Overwrite
                # with the correct number of records
                with open(emission_file, 'w', encoding="utf-8", errors="surrogateescape") as em_file:
                    for record in em_file_records:
                        em_file.write(record)


            try:
                n_bins, diam, rho, shape, wt_fraction, pollutants, diam_strings, rho_strings, shape_strings, \
                wt_fraction_strings, pollutants_strings = read_tgsd_file(tgsd)
            except:
                print('Unable to process file ' + tgsd)
                sys.exit()

            if not no_refir:
                if short_simulation == False:
                    for solution in solutions:
                        create_emission_file(mer_avg, plh_avg, eruption_dur, wt_fraction, solution)
                update_control_files(mer_avg, plh_avg, eruption_dur, 'avg')
                update_control_files(mer_max, plh_max, eruption_dur, 'max')
                update_control_files(mer_min, plh_min, eruption_dur, 'min')
            else:
                for i in range(0, len(solutions)):
                    if short_simulation == False:
                            create_emission_file(str(eruption_mer[i]), str(eruption_plh[i]), eruption_dur[i],
                                                 wt_fraction[i], solutions[i])
                    update_control_files(str(eruption_mer[i]), str(eruption_plh[i]), eruption_dur[i], solutions[i])


            def run_hysplit_mpi(solution):
                SIM_solution = os.path.join(SIM, solution)
                os.chdir(SIM_solution)
                np = n_processes / len(solutions)
                if np > int(n_bins):
                    np = int(n_bins)
                # Run HYSPLIT
                hysplit_script = os.path.join(os.getcwd(), 'hysplit.sh')
                copy(os.path.join(HYSPLIT_RUNS, 'hysplit.sh'), hysplit_script)
                lines = []
                hycm_std_command = 'mpirun -np ' + '{:.0f}'.format(np) + ' ' + os.path.join(HYSPLIT, 'hycm_std') + '\n'
                con2cdf_command = os.path.join(HYSPLIT, 'con2cdf4') + ' cdump cdump.nc'
                if which('sbatch') is None:
                    with open(hysplit_script, 'r', encoding="utf-8", errors="surrogateescape") as hysplit_script_input:
                        for line in hysplit_script_input:
                            if '#SBATCH' not in line or '##' not in line:
                                lines.append(line)
                        lines.append(hycm_std_command)
                        lines.append(con2cdf_command)
                        lines.append('wait\n')
                    with open(hysplit_script, 'w', encoding="utf-8", errors="surrogateescape") as hysplit_script_input:
                        hysplit_script_input.writelines(lines)
                    os.system('sh ' + hysplit_script)
                else:
                    with open(hysplit_script, 'r', encoding="utf-8", errors="surrogateescape") as hysplit_script_input:
                        for line in hysplit_script_input:
                            if '#SBATCH -n' in line:
                                lines.append('#SBATCH -n ' + str(np) + '\n')
                            else:
                                lines.append(line)
                        lines.append(hycm_std_command)
                        lines.append(con2cdf_command)
                        lines.append('wait\n')
                    with open(hysplit_script, 'w', encoding="utf-8", errors="surrogateescape") as hysplit_script_input:
                        hysplit_script_input.writelines(lines)
                    os.system('sbatch -W hysplit.sh')

            try:
                pool_fall3d = ThreadingPool(len(solutions))
                pool_fall3d.map(run_hysplit_mpi, solutions)
            except:
                print('Error processing HYSPLIT in parallel')

        if model == 'fall3d':
            run_fall3d()
        elif model == 'hysplit':
            run_hysplit()

    if not no_refir:
        mer_avg, mer_max, mer_min, plh_avg, plh_max, plh_min, short_simulation, new_er_dur = \
            read_refir_outputs(short_simulation)
        if new_er_dur != 0:
            eruption_dur = new_er_dur / 60
    pool_programs = ThreadingPool(2)
    pool_programs.map(controller, models)

settings_file, tgsd, short_simulation, start_time, start_time_datetime, no_refir_plots, mode, no_refir, plh_input, \
mer_input, er_duration_input, volc_id, n_processes, Iceland_scenario, lon_min, lon_max, lat_min, lat_max, tot_dx, \
tot_dy, run_duration, source_resolution, tot_particle_rate, output_interval, models, run_name = read_args()
if settings_file:
    lat_min, lat_max, lon_min, lon_max, tot_dx, tot_dy, volc_id, n_processes, run_duration, short_simulation, \
    Iceland_scenario, no_refir, er_duration_input, plh_input, mer_input, source_resolution, tot_particle_rate, \
    output_interval, tgsd, run_name, models = read_operational_settings_file()
dx = tot_dx / 2
dy = tot_dy / 2
grid_centre_lat = lat_min + dy
grid_centre_lon = lon_min + dx
# Check the tgsd file is available in TGSDs
tgsd_file = os.path.join(TGSDS,tgsd)
if not os.path.exists(tgsd_file):
    print('Unable to read file ' + tgsd + ' in ' + TGSDS)
    print('Please provide a readable TGSD file in ' + TGSDS + ' named ' + tgsd)
    s_input = input('Press Enter when the file is available')
    if s_input != '':
        print('Wrong input. Simulation aborting')
        sys.exit()
if start_time != '999' and mode == 'manual':
    time_now = start_time_datetime
else:
    time_now = datetime.datetime.utcnow()
syr,smo,sda,shr,shr_wt_st,shr_wt_end,twodaysago = get_times(time_now)

if run_name == 'default':
    run_folder = shr_wt_st
else:
    run_folder = str(run_name)

if no_refir:
    short_simulation = True
    dummy1, dummy2, dummy3, summit, volc_lat, volc_lon = read_esps_database()
    eruption_dur = []
    eruption_plh = []
    eruption_mer = []
    if mer_input[0] == 999 or plh_input[0] == 999 or er_duration_input[0] == 999:
        eruption_dur.append(dummy1)
        eruption_plh.append(dummy2)
        eruption_mer.append(dummy3)
        solutions = ['avg']
    else:
        eruption_dur = er_duration_input
        eruption_plh = plh_input
        eruption_mer = mer_input
        solutions = []
        for i in range(0, len(eruption_dur)):
            solutions.append('run_' + str(i + 1))
else:
    solutions = ['avg', 'max', 'min']
    if mode == 'operational':
        eruption_dur, eruption_plh, summit, volc_lat, volc_lon = run_foxi()
    else:
        eruption_dur, summit, volc_lat, volc_lon = run_refir()


os.chdir(ROOT)

def clean_folders():
    for file in os.listdir(REFIR):
        if file.startswith('run_' + twodaysago):
            rmtree(os.path.join(REFIR,file))
    for file in os.listdir(os.path.join(RUNS,'FALL3D')):
        if file == twodaysago:
            rmtree(os.path.join(RUNS,'FALL3D',file))
    for file in os.listdir(os.path.join(RUNS,'HYSPLIT')):
        if file == twodaysago:
            rmtree(os.path.join(RUNS,'HYSPLIT',file))
        elif file.startswith('EMITIMES_'):
            os.remove(os.path.join(RUNS,'HYSPLIT',file))

if mode == 'manual':
    RUNS = os.path.join(RUNS,'manual')
    try:
        os.mkdir(RUNS)
    except FileExistsError:
        print('Folder ' + RUNS + ' exists')
else:
    RUNS = os.path.join(RUNS, 'operational')
    try:
        os.mkdir(RUNS)
    except FileExistsError:
        print('Folder ' + RUNS + ' exists')

run_models(short_simulation, eruption_dur)
clean_folders()

