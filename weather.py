import os
import datetime
import argparse
import pandas as pd
import sys
from shutil import which, move, rmtree, copy, copytree

def get_args():
    parser = argparse.ArgumentParser(description='Input data for the control script')
    parser.add_argument('-SET','--set',default='True',help='True or False. True: Read simulation parameters from '
                                                           'operational_settings.txt. False: simulation parameters are '
                                                           'read from the other arguments')
    parser.add_argument('-M','--mode',default='operational',help='operational: routine simulation mode controlled via '
                                                                 'operational_settings.txt\nmanual: run with user specific inputs')
    parser.add_argument('-LATMIN','--latmin',default='999',help='Domain minimum latitude')
    parser.add_argument('-LATMAX','--latmax',default='999',help='Domain maximum latitude')
    parser.add_argument('-LONMIN','--lonmin',default='999',help='Domain minimum longitude')
    parser.add_argument('-LONMAX','--lonmax',default='999',help='Domain maximum longitude')
    parser.add_argument('-D','--dur',default='96',help='Ash dispersion simulation duration')
    parser.add_argument('-V','--volc',default='999',help='Smithsonian Institude volcano ID')
    parser.add_argument('-START','--start_time',default='999',help='Starting date and time of the simulation in UTC '
                                                                   '(DD/MM/YYYY-HH:MM). Option valid only in manual mode')
    parser.add_argument('-RUN','--run_name',default='default',help='Run name. If not specified, the run name will be '
                                                                   'the starting time with format HH')
    parser.add_argument('-NR', '--no_refir',default='False',help='True: avoid running REFIR for ESPs. False: run REFIR '
                                                                 'for ESPs')
    args = parser.parse_args()
    settings_file = args.set
    mode = args.mode
    start_time = args.start_time
    start_time_datetime = ''
    run_name = args.run_name
    no_refir = args.no_refir

    if mode != 'manual' and mode != 'operational':
        print('Wrong value for variable --mode')
        print('Execution stopped')
        sys.exit()
    if no_refir.lower() == 'true':
        no_refir = True
    elif no_refir.lower() == 'false':
        no_refir = False
    else:
        print('WARNING. Wrong input for argument -NR --no_refir')
        no_refir = False

    if settings_file == 'True':
        settings_file = True
        with open('operational_settings.txt','r',encoding="utf-8", errors="surrogateescape") as settings:
            for line in settings:
                if line.split('=')[0] == 'LAT_MIN_[deg]':
                    lat_min = line.split('=')[1]
                    lat_min = lat_min.split('\n')[0]
                elif line.split('=')[0] == 'LAT_MAX_[deg]':
                    lat_max = line.split('=')[1]
                    lat_max = lat_max.split('\n')[0]
                elif line.split('=')[0] == 'LON_MIN_[deg]':
                    lon_min = line.split('=')[1]
                    lon_min = lon_min.split('\n')[0]
                elif line.split('=')[0] == 'LON_MAX_[deg]':
                    lon_max = line.split('=')[1]
                    lon_max = lon_max.split('\n')[0]
                elif line.split('=')[0] == 'VOLCANO_ID':
                    volc_id = line.split('=')[1]
                    volc_id = int(volc_id.split('\n')[0])
                elif line.split('=')[0] == 'DURATION_[hours]':
                    duration = line.split('=')[1]
                    duration = int(duration.split('\n')[0])
                elif line.split('=')[0] == 'RUN_NAME':
                    run_name = line.split('=')[1]
                    run_name = run_name.split('\n')[0]
                elif line.split('=')[0] == 'NO_REFIR':
                    no_refir = line.split('=')[1]
                    no_refir = no_refir.split('\n')[0]
                    if no_refir.lower() == 'true':
                        no_refir = True
                    elif no_refir.lower() == 'false':
                        no_refir = False
                    else:
                        no_refir = False
    elif settings_file == 'False':
        settings_file = False
        lat_min = args.latmin
        lat_max = args.latmax
        lon_min = args.lonmin
        lon_max = args.lonmax
        try:
            duration = int(args.dur)
            if duration <= 0:
                print('Please provide a valid duration (> 0)')
                sys.exit()
        except ValueError:
            print('Please provide a valid duration')
            sys.exit()
        try:
            volc_id = int(args.volc)
            if volc_id <= 0:
                print('Please provide a valid ID (> 0)')
                sys.exit()
        except ValueError:
            print('Please provide a valid ID')
        if lat_min == '999':
            print('Please specify a valid value for lat_min')
            sys.exit()
        if lat_max == '999':
            print('Please specify a valid value for lat_max')
            sys.exit()
        if lon_min == '999':
            print('Please specify a valid value for lon_min')
            sys.exit()
        if lon_max == '999':
            print('Please specify a valid value for lon_max')
            sys.exit()
        if float(lat_max) > 90 or float(lat_max) < -90:
            print('lat_max not in the valid range -90 < latitude < 90. Please specify a valid value')
            sys.exit()
        if float(lat_min) > 90 or float(lat_min) < -90:
            print('lat_min not in the valid range -90 < latitude < 90. Please specify a valid value')
            sys.exit()
        if float(lat_min) >= float(lat_max):
            print('lat_min greater than or equal to lat_max. Please check the values')
            sys.exit()
        if float(lon_min) > 180 or float(lon_min) < -180:
            print('lon_min not in the valid range -90 < longitude < 90. Please specify a valid value')
            sys.exit()
        if float(lon_max) > 180 or float(lon_max) < -180:
            print('lon_max not in the valid range -90 < longitude < 90. Please specify a valid value')
            sys.exit()
        if float(lon_min) >= float(lon_max):
            print('lon_min greater than or equal to lon_max. Please check the values')
            sys.exit()
    else:
        print('Wrong value for variable --set')
        sys.exit()
    if start_time != '999':
        try:
            start_time_datetime = datetime.datetime.strptime(start_time,format('%d/%m/%Y-%H:%M'))
        except ValueError:
            print('Unable to read starting time. Please check the format')
            sys.exit()
    return run_name, start_time, start_time_datetime, duration, lat_min, lat_max, lon_min, lon_max, no_refir, volc_id,\
           mode


def get_times(time):
    import urllib3
    http = urllib3.PoolManager()
    url_base = 'https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.'
    yesterday_t = time - datetime.timedelta(days=1)
    twodaysago_t = time - datetime.timedelta(days=2)
    syr = time.strftime('%Y')
    smo = time.strftime('%m')
    sda = time.strftime('%d')
    shr = time.strftime('%H')
    syr_y = yesterday_t.strftime('%Y')
    smo_y = yesterday_t.strftime('%m')
    sda_y = yesterday_t.strftime('%d')
    syr_2d = twodaysago_t.strftime('%Y')
    smo_2d = twodaysago_t.strftime('%m')
    sda_2d = twodaysago_t.strftime('%d')
    today = syr+smo+sda
    yesterday = syr_y+smo_y+sda_y
    twodaysago = syr_2d+smo_2d+sda_2d
    # Find most up to date GFS run
    time_gfs = time
    while time_gfs.strftime('%H') != '00' and time_gfs.strftime('%H') != '06' and time_gfs.strftime('%H') != '12' \
            and time_gfs.strftime('%H') != '18':
        time_gfs -= datetime.timedelta(hours=1)
    url = url_base + time_gfs.strftime('%Y') +  time_gfs.strftime('%m') + time_gfs.strftime('%d') + '/' + \
          time_gfs.strftime('%H') + '/gfs.t' + time_gfs.strftime('%H') + 'z.pgrb2b.0p25.f128'
    r = http.request('GET',url)
    if r.status != '202':
        time_gfs -= datetime.timedelta(hours=6)
        url = url_base + time_gfs.strftime('%Y') +  time_gfs.strftime('%m') + time_gfs.strftime('%d') + '/' + \
              time_gfs.strftime('%H') + '/gfs.t' + time_gfs.strftime('%H') + 'z.pgrb2b.0p25.f128'
    time_diff = time - time_gfs
    time_diff_hours, remainder = divmod(time_diff.seconds, 3600)
    shr_wt_run_st = '{:01d}'.format((int(time_gfs.strftime('%H'))))
    shr_wt_st = '{:01d}'.format(int(shr))
    time_diff_hours = "{:03d}".format(int(time_diff_hours))
    return syr,smo,sda,shr,shr_wt_st,shr_wt_run_st,today,yesterday,twodaysago,time_diff_hours


def get_volc_location():
    try:
        try:
            df = pd.read_excel('https://webapps.bgs.ac.uk/research/volcanoes/esp/volcanoExport.xlsx',
                                     sheetname='volcanoes')
        except TypeError:
            df = pd.read_excel('https://webapps.bgs.ac.uk/research/volcanoes/esp/volcanoExport.xlsx',
                                     sheet_name='volcanoes')
        nrows = df.shape[0]
        row = 0
        while True:
            if df['SMITHSONIAN_ID'][row] == volc_id:
                volc_lat = df['LATITUDE'][row]
                volc_lon = df['LONGITUDE'][row]
                break
            else:
                row += 1
                if row >= nrows:
                    print('ID not found')
                    break
    except BaseException:
        print('Unable to retrieve data from the ESPs database. Please provide inputs manually')
        print('Type volcano latitude')
        volc_lat = str(input())
        print('Type volcano longitude')
        volc_lon = str(input())
    return volc_lat, volc_lon


def get_grib():
    if shr_wt_run_st == '18':
        command = 'python gfs_grib_parallel.py -t 0 108 -x ' + lon_min + ' ' + lon_max + ' -y ' + lat_min + ' ' + \
                  lat_max + ' -c ' + shr_wt_run_st + ' -o gfs_0p25 ' + yesterday
    else:
        command = 'python gfs_grib_parallel.py -t 0 108 -x ' + lon_min + ' ' + lon_max + ' -y ' + lat_min + ' ' + \
                  lat_max + ' -c ' + shr_wt_run_st + ' -o gfs_0p25 ' + today
    lines = []
    lines_original = []
    with open('get_grib.sh', 'r', encoding="utf-8", errors="surrogateescape") as get_grib_script:
        for line in get_grib_script:
            lines_original.append(line)
            if '#SBATCH -n 1' in line:
                lines.append('#SBATCH -n 108\n')
            else:
                lines.append(line)
    lines.append(command + '\n')
    lines.append('wait\n')
    with open('get_grib.sh', 'w', encoding="utf-8", errors="surrogateescape") as get_grib_script:
        get_grib_script.writelines(lines)
    if which('sbatch') is None:
        os.system('sh get_grib.sh')
    else:
        os.system('sbatch -W get_grib.sh')
    with open('get_grib.sh', 'w', encoding="utf-8", errors="surrogateescape") as get_grib_script:
        get_grib_script.writelines(lines_original)
    gribfiles = []
    for file in os.listdir(os.getcwd()):
        if file.endswith('.grb'):
            gribfiles.append(file)
    return gribfiles


def convert_grib_to_nc():
    lines = []
    lines_original = []
    with open('grib2nc.sh', 'r', encoding="utf-8", errors="surrogateescape") as grib2nc_script:
        for line in grib2nc_script:
            lines_original.append(line)
            if 't_start=$1' in line:
                lines.append('t_start=' + time_diff_hours + '\n')
            elif 'OUTPUTFILE=' in line:
                lines.append('OUTPUTFILE=' + mode + '.nc\n')
            else:
                lines.append(line)
    lines.append('wait\n')
    with open('grib2nc.sh', 'w', encoding="utf-8", errors="surrogateescape") as grib2nc_script:
        grib2nc_script.writelines(lines)
    if which('sbatch') is None:
        scheduler_command = 'sh grib2nc.sh\n'
    else:
        scheduler_command = 'sbatch -W grib2nc.sh\n'
    with open(scheduler_file_path, 'a') as scheduler_file_update:
        scheduler_file_update.write(scheduler_command)
    return lines_original


def convert_grib_to_arl(gribfiles):
    arlfiles = []
    for file in gribfiles:
        arlfiles.append(file.split('.grb')[0] + '.arl')
    lines_original = []
    with open('api2arl.sh', 'r', encoding="utf-8", errors="surrogateescape") as api2arl_script:
        for line in api2arl_script:
            lines_original.append(line)
    commands = []
    lines = []
    for i in range(0, len(gribfiles)):
        commands.append(API2ARL + ' -dapi2arl.cfg -i' + gribfiles[i] + ' -o' + arlfiles[i] + ' -earldata.cfg_' + str(i)
                        + ' &\n')
    with open('api2arl.sh', 'r', encoding="utf-8", errors="surrogateescape") as api2arl_script:
        for line in api2arl_script:
            if '#SBATCH -n 1' in line:
                lines.append('#SBATCH -n ' + str(len(gribfiles)) + '\n')
            else:
                lines.append(line)
    for command in commands:
        lines.append(command)
    lines.append('wait\n')
    with open('api2arl.sh', 'w', encoding="utf-8", errors="surrogateescape") as api2arl_script:
        api2arl_script.writelines(lines)
    if which('sbatch') is None:
        scheduler_command = 'sh api2arl.sh\n'
    else:
        scheduler_command = 'sbatch -W api2arl.sh\n'
    with open(scheduler_file_path, 'a') as scheduler_file_update:
        scheduler_file_update.write(scheduler_command)
    return lines_original


def extract_data_gfs(wtfiles, wtfiles_interpolated, profiles_grb):
    print('Interpolating weather data to a finer grid around the source')
    slon_source = str(lon_source)
    slat_source = str(lat_source)
    lon_corner = float(lon_source)
    lat_corner = float(lat_source)
    lon_corner = str(int(lon_corner - 1))
    lat_corner = str(int(lat_corner - 1))
    print('Saving weather data along the vertical at the vent location')
    wgrib2_zoom_commands = []
    wgrib2_interpolation_commands = []
    if len(wtfiles) > 48:
        max_refir_weather_data = 48
    else:
        max_refir_weather_data = len(wtfiles)
    for i in range(0, max_refir_weather_data):
        wgrib2_zoom_commands.append(WGRIB2 + ' ' + wtfiles[i]
                                    + ' -set_grib_type same -new_grid_winds earth -new_grid latlon ' + lon_corner
                                    + ':200:0.01 ' + lat_corner + ':200:0.01 ' + wtfiles_interpolated[i])
        wgrib2_interpolation_commands.append(WGRIB2 + ' ' + wtfiles_interpolated[i] + ' -s -lon ' + slon_source + ' ' +
                                             slat_source + '  >' + profiles_grb[i])
    lines = []
    lines_original = []
    with open('wgrib2.sh', 'r', encoding="utf-8", errors="surrogateescape") as wgrib_script:
        for line in wgrib_script:
            lines_original.append(line)
            if '#SBATCH -n 1' in line:
                line = '#SBATCH -n ' + str(len(wgrib2_zoom_commands)) + '\n'
            lines.append(line)
    lines.append('cd ' + refir_weather_today_dir + '\n')
    # Prepare and run wgrib2 script to zoom
    for i in range(0, max_refir_weather_data - 1):
        line = wgrib2_zoom_commands[i] + ' &\n'
        lines.append(line)
    lines.append(wgrib2_zoom_commands[-1] + '\n')
    lines.append('wait\n')
    for i in range(0, max_refir_weather_data - 1):
        line = wgrib2_interpolation_commands[i] + ' &\n'
        lines.append(line)
    lines.append(wgrib2_interpolation_commands[-1] + '\n')
    lines.append('wait\n')
    with open('wgrib2.sh', 'w', encoding="utf-8", errors="surrogateescape") as wgrib_script:
        wgrib_script.writelines(lines)

    if which('sbatch') is None:
        scheduler_command = 'sh wgrib2.sh\n'
    else:
        scheduler_command = 'sbatch -W wgrib2.sh\n'
    with open(scheduler_file_path, 'a') as scheduler_file_update:
        scheduler_file_update.write(scheduler_command)
    return max_refir_weather_data, lines_original


def elaborate_refir_weather_data(n_refir_data, profiles_grb, profiles):
    for i in range(0, n_refir_data):
        with open(profiles_grb[i], "r", encoding="utf-8", errors="surrogateescape") as profile_file:
            records1 = []
            records2 = []
            nrecords = 0
            for line in profile_file:
                nrecords += 1
                records1.append(line.split(':'))
                records2.append(line.split('val='))
        u_tmp = []
        v_tmp = []
        hgt_tmp = []
        tmp_k_tmp = []
        mb_tmp = []
        u = []
        v = []
        wind = []
        hgt = []
        tmp_k = []
        tmp_c = []
        mb = []
        p = []
        j = 0
        temp_level = '999'
        while j < nrecords - 1:
            level = records1[j][4]
            if level[-2:] == 'mb':
                if records1[j][4] == '0.4 mb':
                    j += 1
                    continue
                else:
                    if records1[j][4].split(' ')[0] != temp_level and records1[j][3] != '5WAVH':
                        if len(hgt_tmp) > len(u_tmp):
                            hgt_tmp.pop()
                            tmp_k_tmp.pop()
                            mb_tmp.pop()
                    if records1[j][3] == 'HGT' and records1[j][4].split(' ')[0] != temp_level:
                        temp_level = records1[j][4].split(' ')[0]
                        hgt_tmp.append(records2[j][1])
                        mb_tmp.append(records1[j][4].split(' '))
                    elif records1[j][3] == 'TMP' and records1[j][4].split(' ')[0] == temp_level:
                        tmp_k_tmp.append(records2[j][1])
                    elif records1[j][3] == 'UGRD' and records1[j][4].split(' ')[0] == temp_level:
                        u_tmp.append(records2[j][1])
                    elif records1[j][3] == 'VGRD' and records1[j][4].split(' ')[0] == temp_level:
                        v_tmp.append(records2[j][1])
                if records1[j][4] == '1000 mb':
                    if records1[j][3] == 'HGT':
                        hgt_tmp.append(records2[j][1])
                        mb_tmp.append(records1[j][4].split(' '))
                    elif records1[j][3] == 'TMP':
                        tmp_k_tmp.append(records2[j][1])
                    elif records1[j][3] == 'UGRD':
                        u_tmp.append(records2[j][1])
                    elif records1[j][3] == 'VGRD':
                        v_tmp.append(records2[j][1])
            j += 1

        for j in range(0, len(u_tmp)):
            u.append(float(u_tmp[j]))
            v.append(float(v_tmp[j]))
            wind.append((u[j] ** 2 + v[j] ** 2) ** 0.5)
            hgt.append(float(hgt_tmp[j]))
            tmp_k.append(float(tmp_k_tmp[j]))
            tmp_c.append(tmp_k[j] - 273.15)
            mb.append(float(mb_tmp[j][0]))
            p.append(mb[j] * 100)
        p[len(u_tmp) - 1] = 100000

        with open(profiles[i], 'w', encoding="utf-8", errors="surrogateescape") as wt_output:
            wt_output.write('  HGT[m]         P[Pa]       T[K]       T[C]     U[m/s]     V[m/s]  WIND[m/s]\n')
            for j in range(0, len(u)):
                wt_output.write('%8.2f\t%9.2f\t%6.2f\t%6.2f\t%7.2f\t%7.2f\t%7.2f\n' % (
                    hgt[j], p[j], tmp_k[j], tmp_c[j], u[j], v[j], wind[j]))


HYSPLIT = '/home/vulcanomod/HYSPLIT'
API2ARL = os.path.join(HYSPLIT, 'hysplit.v5.2.0', 'exec', 'api2arl_v4')
WGRIB2 = '/home/vulcanomod/grib2/wgrib2/wgrib2'

run_name, start_time, start_time_datetime, duration, lat_min, lat_max, lon_min, lon_max, no_refir, volc_id, mode = \
    get_args()

if start_time != '999' and mode == 'manual':
    time_now = start_time_datetime
else:
    time_now = datetime.datetime.utcnow()
syr, smo, sda, shr, shr_wt_st, shr_wt_run_st, today, yesterday, twodaysago, time_diff_hours = get_times(time_now)

root = os.getcwd()
weather_scripts_dir = os.path.join(root, 'weather', 'scripts')
scheduler_file_path = os.path.join(weather_scripts_dir, 'scheduler_weather.sh')
with open(scheduler_file_path, 'w') as scheduler_file:
    scheduler_file.write('#!/bin/bash\n')
    scheduler_file.write('cd ' + weather_scripts_dir + '\n')
if mode == 'operational':
    data_dir = os.path.join(root,'weather', 'data', 'operational')
else:
    data_dir = os.path.join(root, 'weather', 'data', 'manual')
data_today_dir = os.path.join(data_dir, today)
if run_name == 'default':
    run_folder = shr_wt_st
else:
    run_folder = str(run_name)
data_run_dir = os.path.join(data_today_dir,run_folder)
data_twodaysago_dir = os.path.join(data_dir,twodaysago)

if not no_refir:
    refir_dir = ('/home/vulcanomod/REFIR')
    refir_weather_today_dir = os.path.join(refir_dir, 'raw_forecast_weather_data_' + today)
    # To create a reanalysis copy of the REFIR weather data folder in case the user wants to run in reanalysis mode
    refir_reanalysis_dir = os.path.join(refir_dir, 'raw_reanalysis_weather_data_' + today)
    refir_weather_twodaysago_dir = os.path.join(refir_dir, 'raw_forecast_weather_data_' + twodaysago)
    # Check if the weather data are in the run folder of REFIR, and if yes move it one level up
    os.chdir(refir_dir)
    refir_files_list = os.listdir(refir_dir)
    for file in refir_files_list:
        if file.startswith('run_' + today):
            try:
                move(os.path.join(refir_dir, file, 'raw_forecast_weather_data_' + today), refir_dir)
            except FileNotFoundError:
                print('Folder ' + refir_weather_today_dir + ' not present in ' + os.path.join(refir_dir, file))
try:
    os.mkdir(data_dir)
except FileExistsError:
    print('Folder ' + data_dir + ' already exists')
try:
    os.mkdir(data_today_dir)
except FileExistsError:
    print('Folder ' + data_today_dir + ' already exists')
try:
    os.mkdir(data_run_dir)
except FileExistsError:
    print('Folder ' + data_run_dir + ' already exists')
    rmtree(data_run_dir)
    os.mkdir(data_run_dir)

os.chdir(weather_scripts_dir)
gribfiles = get_grib()
gribfiles = sorted(gribfiles)
grib_to_nc_original_lines = convert_grib_to_nc()
grib_to_arl_original_lines = convert_grib_to_arl(gribfiles)

if not no_refir:
    try:
        rmtree(refir_weather_twodaysago_dir)
    except FileNotFoundError:
        print('Folder ' + refir_weather_twodaysago_dir + ' not present')
    try:
        os.mkdir(refir_weather_today_dir)
    except FileExistsError:
        print('Folder ' + refir_weather_today_dir + ' already exists')

if not no_refir:
    # Create profile files readable by REFIR
    lat_source, lon_source = get_volc_location()
    profiles = []
    profiles_grb = []
    wtfiles = []
    wtfiles_interpolated = []
    time_validity = datetime.datetime.strptime(today+shr_wt_run_st, format('%Y%m%d%H'))
    for i in range(0, duration + 1):
        wtfiles.append(os.path.join(refir_weather_today_dir, 'weather_data_' + today
                                    + '{:02}'.format(int(shr_wt_run_st)) + '_f' + '{:03}'.format(i)))
        wtfiles_interpolated.append(os.path.join(refir_weather_today_dir, 'weather_data_interpolated_'+ today
                                                 + '{:02}'.format(int(shr_wt_run_st)) + '_f' + '{:03}'.format(i)))
        time_validity_s = datetime.datetime.strftime(time_validity,format('%Y%m%d%H'))
        profiles_grb.append(os.path.join(refir_weather_today_dir, 'profile_' + time_validity_s + '.txt'))
        profiles.append(os.path.join(refir_weather_today_dir, 'profile_data_' + time_validity_s + '.txt'))
        time_validity += datetime.timedelta(hours=1)
    for i in range(0, len(wtfiles)):
        copy(gribfiles[i], wtfiles[i])
    max_refir_weather_data, extract_data_gfs_original_lines = \
        extract_data_gfs(wtfiles, wtfiles_interpolated, profiles_grb)

os.system('sh ' + scheduler_file_path)
if not no_refir:
    elaborate_refir_weather_data(max_refir_weather_data, profiles_grb, profiles)
if not no_refir:
    if os.path.exists(refir_reanalysis_dir):
        os.system('rm -r ' + refir_reanalysis_dir)
    os.system('cp -r ' + refir_weather_today_dir + ' ' + refir_reanalysis_dir)

# Remove arl time steps before the starting times before merging
arl_files_to_remove = []
all_files = os.listdir(os.getcwd())
for arl_file in all_files:
    if arl_file.endswith('.arl'):
       if int(arl_file.split('-')[0]) < int(float(time_diff_hours)):
           arl_files_to_remove.append(arl_file)
for file_to_remove in arl_files_to_remove:
    os.remove(file_to_remove)
os.system('cat *.arl > ' + mode + '.arl')

try:
    rmtree(data_twodaysago_dir)
except FileNotFoundError:
    print('Folder ' + data_twodaysago_dir + ' not present')

for file in os.listdir(weather_scripts_dir):
    if file.endswith('.grb') or file.endswith('0p25.arl'):
        os.remove(file)
    elif file.startswith(mode):
        move(file, data_run_dir)

os.system('rm arldata.cfg*')
with open('grib2nc.sh', 'w', encoding="utf-8", errors="surrogateescape") as grib2nc_script:
    grib2nc_script.writelines(grib_to_nc_original_lines)
with open('api2arl.sh', 'w', encoding="utf-8", errors="surrogateescape") as api2arl_script:
    api2arl_script.writelines(grib_to_arl_original_lines)
if not no_refir:
    with open('wgrib2.sh', 'w', encoding="utf-8", errors="surrogateescape") as wgrib_script:
        wgrib_script.writelines(extract_data_gfs_original_lines)

os.remove(scheduler_file_path)



