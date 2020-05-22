import os
import datetime
import shutil
import argparse
from pathos.multiprocessing import ThreadingPool
import pandas as pd

parser = argparse.ArgumentParser(description='Input data for the control script')
parser.add_argument('-SET','--set',default='True',help='True or False. True: Read simulation parameters from operational_settings.txt. False: simulation parameters are read from the other arguments')
parser.add_argument('-M','--mode',default='operational',help='operational: routine simulation mode controlled via operational_settings.txt\nmanual: run with user specific inputs')
parser.add_argument('-LATMIN','--latmin',default='999',help='Domain minimum latitude')
parser.add_argument('-LATMAX','--latmax',default='999',help='Domain maximum latitude')
parser.add_argument('-LONMIN','--lonmin',default='999',help='Domain minimum longitude')
parser.add_argument('-LONMAX','--lonmax',default='999',help='Domain maximum longitude')
parser.add_argument('-D','--dur',default='96',help='Ash dispersion simulation duration')
parser.add_argument('-V','--volc',default='999',help='Smithsonian Institude volcano ID')
parser.add_argument('-START','--start_time',default='999',help='Starting date and time of the simulation in UTC (DD/MM/YYYY-HH:MM). Option valid only in manual mode')
args = parser.parse_args()
settings_file = args.set
mode = args.mode
start_time = args.start_time

if mode != 'manual' and mode != 'operational':
    print('Wrong value for variable --mode')
    print('Execution stopped')
    exit()

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
            exit()
    except:
        print('Please provide a valid duration')
        exit()
    try:
        volc_id = int(args.volc)
        if volc_id <= 0:
            print('Please provide a valid ID (> 0)')
            exit()
    except:
        print('Please provide a valid ID')
    if lat_min == '999':
        print('Please specify a valid value for lat_min')
        exit()
    if lat_max == '999':
        print('Please specify a valid value for lat_max')
        exit()
    if lon_min == '999':
        print('Please specify a valid value for lon_min')
        exit()
    if lon_max == '999':
        print('Please specify a valid value for lon_max')
        exit()
    if float(lat_max) > 90 or float(lat_max) < -90:
        print('lat_max not in the valid range -90 < latitude < 90. Please specify a valid value')
        exit()
    if float(lat_min) > 90 or float(lat_min) < -90:
        print('lat_min not in the valid range -90 < latitude < 90. Please specify a valid value')
        exit()
    if float(lat_min) >= float(lat_max):
        print('lat_min greater than or equal to lat_max. Please check the values')
        exit()
    if float(lon_min) > 180 or float(lon_min) < -180:
        print('lon_min not in the valid range -90 < longitude < 90. Please specify a valid value')
        exit()
    if float(lon_max) > 180 or float(lon_max) < -180:
        print('lon_max not in the valid range -90 < longitude < 90. Please specify a valid value')
        exit()
    if float(lon_min) >= float(lon_max):
        print('lon_min greater than or equal to lon_max. Please check the values')
        exit()
else:
    print('Wrong value for variable --set')
    exit()
if start_time != '999':
    try:
        start_time_datetime = datetime.datetime.strptime(start_time,format('%d/%m/%Y-%H:%M'))
    except:
        print('Unable to read starting time. Please check the format')
        exit()

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
    while time_gfs.strftime('%H') != '00' and time_gfs.strftime('%H') != '06' and time_gfs.strftime('%H') != '12' and time_gfs.strftime('%H') != '18':
        time_gfs -= datetime.timedelta(hours=1)
    url = url_base + time_gfs.strftime('%Y') +  time_gfs.strftime('%m') + time_gfs.strftime('%d') + '/' + time_gfs.strftime('%H') + '/gfs.t' + time_gfs.strftime('%H') + 'z.pgrb2b.0p25.f128'
    r = http.request('GET',url)
    if r.status != '202':
        time_gfs -= datetime.timedelta(hours=6)
        url = url_base + time_gfs.strftime('%Y') +  time_gfs.strftime('%m') + time_gfs.strftime('%d') + '/' + time_gfs.strftime('%H') + '/gfs.t' + time_gfs.strftime('%H') + 'z.pgrb2b.0p25.f128'
    time_diff = time - time_gfs
    time_diff_hours, remainder = divmod(time_diff.seconds, 3600)
    shr_wt_run_st = '{:01d}'.format((int(time_gfs.strftime('%H'))))
    shr_wt_st = '{:01d}'.format(int(shr))
    time_diff_hours = "{:03d}".format(int(time_diff_hours))
    return syr,smo,sda,shr,shr_wt_st,shr_wt_run_st,today,yesterday,twodaysago,time_diff_hours

def get_volc_location():
    try:
        df = pd.read_excel('http://www.bgs.ac.uk/research/volcanoes/esp/volcanoExport.xlsx', sheet_name='volcanoes')
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
    except:
        print('Unable to retrieve data from the ESPs database. Please provide inputs manually')
        print('Type volcano latitude')
        volc_lat = str(input())
        print('Type volcano longitude')
        volc_lon = str(input())
    return volc_lat, volc_lon

def extract_data_gfs(wtfile, wtfile_int, profile_grb, profile):
    print('Interpolating weather data to a finer grid around the source')
    slon_source = str(lon_source)
    slat_source = str(lat_source)
    lon_corner = float(lon_source)
    lat_corner = float(lat_source)
    lon_corner = str(int(lon_corner - 2))
    lat_corner = str(int(lat_corner - 2))
    os.system('srun -J wgrib2 wgrib2 ' + wtfile + ' -set_grib_type same -new_grid_winds earth -new_grid latlon ' + lon_corner + ':400:0.01 ' + lat_corner + ':400:0.01 ' + wtfile_int)
    print('Saving weather data along the vertical at the vent location')
    os.system('srun -J wgrib2 wgrib2 ' + wtfile_int + ' -s -lon ' + slon_source + ' ' + slat_source + '  >' + profile_grb)
    file = open(profile_grb, "r",encoding="utf-8", errors="surrogateescape")
    records1 = []
    records2 = []
    nrecords = 0
    for line in file:
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
    i = 0
    temp_level = '999'
    while i < nrecords - 1:
        level = records1[i][4]
        if level[-2:] == 'mb':
            if records1[i][4] == '0.4 mb':
                i += 1
                continue
            else:
                if records1[i][4].split(' ')[0] != temp_level and records1[i][3] != '5WAVH':
                    if len(hgt_tmp) > len(u_tmp):
                        hgt_tmp.pop()
                        tmp_k_tmp.pop()
                        mb_tmp.pop()
                if records1[i][3] == 'HGT' and records1[i][4].split(' ')[0] != temp_level:
                    temp_level = records1[i][4].split(' ')[0]
                    hgt_tmp.append(records2[i][1])
                    mb_tmp.append(records1[i][4].split(' '))
                elif records1[i][3] == 'TMP' and records1[i][4].split(' ')[0] == temp_level:
                    tmp_k_tmp.append(records2[i][1])
                elif records1[i][3] == 'UGRD' and records1[i][4].split(' ')[0] == temp_level:
                    u_tmp.append(records2[i][1])
                elif records1[i][3] == 'VGRD' and records1[i][4].split(' ')[0] == temp_level:
                    v_tmp.append(records2[i][1])
            if records1[i][4] == '1000 mb':
                if records1[i][3] == 'HGT':
                    hgt_tmp.append(records2[i][1])
                    mb_tmp.append(records1[i][4].split(' '))
                elif records1[i][3] == 'TMP':
                    tmp_k_tmp.append(records2[i][1])
                elif records1[i][3] == 'UGRD':
                    u_tmp.append(records2[i][1])
                elif records1[i][3] == 'VGRD':
                    v_tmp.append(records2[i][1])
        i += 1

    for i in range(0, len(u_tmp)):
        u.append(float(u_tmp[i]))
        v.append(float(v_tmp[i]))
        wind.append((u[i] ** 2 + v[i] ** 2) ** 0.5)
        hgt.append(float(hgt_tmp[i]))
        tmp_k.append(float(tmp_k_tmp[i]))
        tmp_c.append(tmp_k[i] - 273.15)
        mb.append(float(mb_tmp[i][0]))
        p.append(mb[i] * 100)

    p[len(u_tmp) - 1] = 100000
    wt_output = open(profile, 'w',encoding="utf-8", errors="surrogateescape")
    wt_output.write('  HGT[m]         P[Pa]       T[K]       T[C]     U[m/s]     V[m/s]  WIND[m/s]\n')

    for i in range(0, len(u)):
        wt_output.write('%8.2f %13.2f %10.2f %10.2f %10.2f %10.2f %10.2f\n' % (
        hgt[i], p[i], tmp_k[i], tmp_c[i], u[i], v[i], wind[i]))
    wt_output.close()

if start_time != '999' and mode == 'manual':
    time_now = start_time_datetime
else:
    time_now = datetime.datetime.utcnow()
syr,smo,sda,shr,shr_wt_st,shr_wt_run_st,today,yesterday,twodaysago,time_diff_hours = get_times(time_now)

root = os.getcwd()
weather_scripts_dir = os.path.join(root,'weather','scripts')
if mode == 'operational':
    data_dir = os.path.join(root,'weather','data','operational')
else:
    data_dir = os.path.join(root, 'weather', 'data', 'manual')
data_today_dir = os.path.join(data_dir,today)
data_run_dir = os.path.join(data_today_dir,shr_wt_st)
data_twodaysago_dir = os.path.join(data_dir,twodaysago)
#refir_dir = os.path.join(cwd,'REFIR')
refir_dir = ('/home/vulcanomod/REFIR')
refir_weather_today_dir = os.path.join(refir_dir,'raw_forecast_weather_data_' + today)
refir_weather_twodaysago_dir = os.path.join(refir_dir,'raw_forecast_weather_data_' + twodaysago)

# Check if the weather data are in the run folder of REFIR, and if yes move it one level up
os.chdir(refir_dir)
refir_files_list = os.listdir(refir_dir)
for file in refir_files_list:
    if file.startswith('run_' + today):
        try:
            shutil.move(os.path.join(refir_dir,file,'raw_forecast_weather_data_' + today),refir_dir)
        except:
            print('Folder ' + refir_weather_today_dir + ' not present in ' + os.path.join(refir_dir,file))
try:
    os.mkdir(data_dir)
except:
    print('Folder ' + data_dir + ' already exists')
try:
    os.mkdir(data_today_dir)
except:
    print('Folder ' + data_today_dir + ' already exists')
try:
    os.mkdir(data_run_dir)
except:
    print('Folder ' + data_run_dir + ' already exists')
    shutil.rmtree(data_run_dir)
    os.mkdir(data_run_dir)

os.chdir(weather_scripts_dir)
if shr_wt_run_st == '18':
    command = 'python gfs_grib_parallel.py -t 0 108 -x ' + lon_min + ' ' + lon_max + ' -y ' + lat_min + ' ' + lat_max + ' -c ' + shr_wt_run_st + ' -o gfs_0p25 ' + yesterday
else:
    command = 'python gfs_grib_parallel.py -t 0 108 -x ' + lon_min + ' ' + lon_max + ' -y ' + lat_min + ' ' + lat_max + ' -c ' + shr_wt_run_st + ' -o gfs_0p25 ' + today
os.system(command)
os.system('srun -J grib2nc sh grib2nc.sh ' + time_diff_hours)
if mode == 'manual':
    os.rename('operational.nc',mode + '.nc')
os.system('cat *.arl > ' + mode + '.arl')
try:
    shutil.rmtree(refir_weather_twodaysago_dir)
except:
    print('Folder ' + refir_weather_twodaysago_dir + ' not present')
try:
    os.mkdir(refir_weather_today_dir)
except:
    print('Folder ' + refir_weather_today_dir + ' already exists')
    #shutil.rmtree(refir_weather_today_dir)
    #os.mkdir(refir_weather_today_dir)
for file in os.listdir(weather_scripts_dir):
    if file.startswith('weather_data'):
        try:
            shutil.move(file,refir_weather_today_dir)
        except:
            print('File ' + file + ' already present in ' + refir_weather_today_dir)
            os.remove(file)
    elif file.endswith('.grb') or file.endswith('0p25.arl'):
        os.remove(file)
    #elif file.startswith('operational.'):
    elif file.startswith(mode):
        shutil.move(file, data_run_dir)

if mode == 'operational':
    # Create profile files readable by REFIR
    lat_source, lon_source = get_volc_location()
    profiles = []
    profiles_grb = []
    wtfiles = []
    wtfiles_interpolated = []
    time_validity = datetime.datetime.strptime(today+shr_wt_run_st,format('%Y%m%d%H'))
    for i in range(0,duration + 1):
        wtfiles.append('weather_data_'+ today + '{:02}'.format(int(shr_wt_run_st)) + '_f' + '{:03}'.format(i))
        wtfiles_interpolated.append('weather_data_interpolated_'+ today + '{:02}'.format(int(shr_wt_run_st)) + '_f' + '{:03}'.format(i))
        time_validity_s = datetime.datetime.strftime(time_validity,format('%Y%m%d%H'))
        profiles_grb.append('profile_' + time_validity_s + '.txt')
        profiles.append('profile_data_' + time_validity_s + '.txt')
        time_validity += datetime.timedelta(hours=1)
    os.chdir(refir_weather_today_dir)
    pool = ThreadingPool(duration + 1)
    pool.map(extract_data_gfs,wtfiles,wtfiles_interpolated,profiles_grb,profiles)
    os.chdir(weather_scripts_dir)
try:
    shutil.rmtree(data_twodaysago_dir)
except:
    print('Folder ' + data_twodaysago_dir + ' not present')

os.remove('arldata.cfg')




