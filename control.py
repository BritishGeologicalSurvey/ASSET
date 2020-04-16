import os
import datetime
import shutil
import argparse
from pathos.multiprocessing import ThreadingPool

# Folder structure
ROOT = os.getcwd()
#REFIR = os.path.join(ROOT,'REFIR')
REFIR = '/home/vulcanomod/REFIR'
RUNS = os.path.join(ROOT,'Runs')
TGSDS = os.path.join(ROOT,'TGSDs')

# Parse input arguments
parser = argparse.ArgumentParser(description='Input data for the control script')
parser.add_argument('--mode',default='operational',help='operational: routine simulation mode controlled via operational_settings.txt\nmanual: run with user specific inputs')
parser.add_argument('--set',default='True',help='Read simulation parameters from operational_settings.txt')
parser.add_argument('--volc',default=999,help='This is the volcano ID based on the Smithsonian Institute IDs')
parser.add_argument('--np',default=0,help='Number of processes for parallel processing')
parser.add_argument('--s',default='True',help='True or False. True: run REFIR for 5 minutes; False: run REFIR for the duration set by the ESPs database')
parser.add_argument('--i',default='True',help='True or False. True: Icelandic volcanoes scenarios; False: other volcanoes')
parser.add_argument('--latmin',default=999,help='Domain minimum latitude')
parser.add_argument('--latmax',default=999,help='Domain maximum latitude')
parser.add_argument('--lonmin',default=999,help='Domain minimum longitude')
parser.add_argument('--lonmax',default=999,help='Domain maximum longitude')
parser.add_argument('--dur',default=96,help='Ash dispersion simulation duration')
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
if settings_file == 'True':
    settings_file = True
elif settings_file == 'False':
    settings_file = False
else:
    print('Wrong value for variable --set')
if short_simulation == 'True':
    short_simulation = True
elif short_simulation == 'False':
    short_simulation = False
else:
    print('Wrong value for variable --s')
if mode != 'manual' and mode != 'operational':
    print('Wrong value for variable --mode')
    print('Execution stopped')
    exit()

def convert_args(volc_id, n_processes, Iceland_scenario, lon_min, lon_max, lat_min, lat_max, run_duration):
    lon_max = float(lon_max)
    lon_min = float(lon_min)
    lat_max = float(lat_max)
    lat_min = float(lat_min)
    tot_dx = lon_max - lon_min
    tot_dy = lat_max - lat_min
    volc_id = int(volc_id)
    n_processes = int(n_processes)
    run_duration = int(run_duration)
    if Iceland_scenario == 'True':
        Iceland_scenario = True
    elif Iceland_scenario == 'False':
        Iceland_scenario = False
    else:
        print('Wrong value for variable --i')
    return volc_id, n_processes, Iceland_scenario, lon_min, lon_max, lat_min, lat_max, tot_dx, tot_dy, run_duration

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

def run_foxi():
    def read_esps_database():
        import pandas as pd

        with open(volcano_list_file, 'r', encoding="utf-8", errors="surrogateescape") as volcano_list:
            for line in volcano_list:
                try:
                    if int(line.split('\t')[0]) == volc_id:
                        volc_lat = line.split('\t')[1]
                        volc_lon = line.split('\t')[2]
                except:
                    continue
        try:
            database = pd.read_excel('http://www.bgs.ac.uk/research/volcanoes/esp/volcanoExport.xlsx',
                                 sheetname='volcanoes')
        except:
            database = pd.read_excel('http://www.bgs.ac.uk/research/volcanoes/esp/volcanoExport.xlsx',
                                     sheet_name='volcanoes')
        nrows = database.shape[0]
        row = 0
        while True:
            if database['SMITHSONIAN_ID'][row] == volc_id:
                summit = database['ELEVATION_m'][row]
                esps_dur = database['DURATION_hour'][row]
                esps_plh = database['HEIGHT_ABOVE_VENT_km'][row] * 1000
                esps_plh += summit

                break
            else:
                row += 1
                if row >= nrows:
                    print('ID not found')
                    break
        return esps_dur, esps_plh, summit, volc_lat, volc_lon

    shutil.copy(os.path.join(ROOT, 'fix_config.txt'), os.path.join(REFIR, 'fix_config.txt'))
    fix_config_file = os.path.join(REFIR, 'fix_config.txt')
    volcano_list_file = os.path.join(REFIR, 'refir_config', 'volcano_list.ini')
    fix_config_records = []

    with open(fix_config_file, 'r', encoding="utf-8", errors="surrogateescape") as fix_config:
        for line in fix_config:
            fix_config_records.append(line.split('\n')[0])

    esps_dur, esps_plh, summit, volc_lat, volc_lon = read_esps_database()
    if esps_dur > 24:
        esps_dur = 24

    if short_simulation:
        time_end = time_now + datetime.timedelta(minutes=5)
    else:
        time_end = time_now + datetime.timedelta(hours=esps_dur)

    start_time = datetime.datetime.strftime(time_now, "%Y-%m-%d %H:%M:%S")
    stop_time = datetime.datetime.strftime(time_end, "%Y-%m-%d %H:%M:%S")

    if Iceland_scenario:
        if volc_id == 372020:
            volc_number = 0
            tgsd = 'eyja'
        elif volc_id == 372030:
            volc_number = 1
            tgsd = 'katla'
        elif volc_id == 372070:
            volc_number = 2
            tgsd = 'hekla_2000'
        elif volc_id == 373010:
            volc_number = 3
            tgsd = 'grimsvotn'
        elif volc_id == 372010:
            volc_number = 4
            tgsd = 'heimeay'
        elif volc_id == 373050:
            volc_number = 7
            tgsd = 'askja_8km'
        elif volc_id == 374010:
            volc_number = 8
            tgsd = 'askja_8km'
        elif volc_id == 371020:
            volc_number = 9
            tgsd = 'reykjanes'
        else:
            tgsd = 'user_defined'
    else:
        volc_number = 0
        tgsd = 'user_defined'

    with open(fix_config_file, 'w', encoding="utf-8", errors="surrogateescape") as fix_config:
        for i in range(0, len(fix_config_records)):
            if i == 0:
                fix_config.write(str(volc_number) + '\n')
            elif i == 163:
                fix_config.write('2\n')
            elif i == 164:
                fix_config.write('1\n')
            elif i == 166:
                fix_config.write(start_time + '\n')
            elif i == 167:
                fix_config.write(stop_time + '\n')
            elif i == 169:
                fix_config.write('60\n')
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
    foxi_command = 'srun -J REFIR_FOXI python FOXI.py background operational'
    os.system(foxi_command)
    os.chdir(ROOT)
    return esps_dur, esps_plh, summit, volc_lat, volc_lon, tgsd

def run_refir():
    REFIR_CONFIG = os.path.join(REFIR,'refir_config')
    volcano_list_file = os.path.join(REFIR_CONFIG,'volcano_list.ini')
    os.system('source activate refir')
    os.chdir(REFIR_CONFIG)
    foxset_command = 'srun -J REFIR_FoxSet python FoxSet.py'
    os.system(foxset_command)
    os.chdir(REFIR)
    fix_command = 'srun -J REFIR_FIX python FIX.py &'
    foxi_command = 'srun -J REFIR_FOXI python FOXI.py &'
    os.system(fix_command)
    os.system(foxi_command)
    with open(volcano_list_file,'r',encoding="utf-8", errors="surrogateescape") as volcano_list:
        for line in volcano_list:
            try:
                if int(line.split('\t')[0]) == volc_id:
                    volc_lat = line.split('\t')[1]
                    volc_lon = line.split('\t')[2]
                    summit = float(line.split('\t')[3])
                    #tgsd = line.split('\t')[5]
                    #tgsd = tgsd.split('\n')[0]
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
    er_dur = lines[173]
    er_dur = float(er_dur.split('\n')[0])
    if er_dur > 24:
        er_dur = 24
    tgsd = 'user_defined'
    return er_dur, summit, volc_lat, volc_lon, tgsd

def run_models(short_simulation):
    def read_refir_outputs(short_simulation):
        files = os.listdir(REFIR)
        paths = []
        tavg_mer_file = ''
        tavg_plh_file = ''
        mer_file = ''
        plh_file = ''
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
                refir_run_name = file.split('_')[0] #Get REFIR run name
        for file in files:
            if file.endswith('tavg_FMER.txt'):
                tavg_mer_file = os.path.join(refir_run,file)
            elif file.endswith('tavg_PLH.txt'):
                tavg_plh_file = os.path.join(refir_run,file)
            elif mode == 'manual' and file == refir_run_name + '_FMER.txt':
                mer_file = os.path.join(refir_run,file)
            elif mode == 'manual' and file == refir_run_name + '_PLH.txt':
                plh_file = os.path.join(refir_run,file)
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
                short_simulation = True # always convert to a short simulation if REFIR has been run manually for one time step only
            mer_file_r.close()
        if short_simulation:
            with open(mer_file, 'r', encoding="utf-8", errors="surrogateescape") as mer_file_r:
                mer_min = ''
                mer_avg = ''
                mer_max = ''
                for line in mer_file_r:
                    try:
                        minute = int(line.split('\t')[1])
                        if minute == 5:
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
                        if minute == 5:
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
            try:
                mer_file = open(tavg_mer_file, 'r', encoding="utf-8", errors="surrogateescape")
                for line in mer_file:
                    minute_dummy = int(line.split('\t')[1])
            except:
                mer_file = open(mer_file, 'r', encoding="utf-8", errors="surrogateescape")
            try:
                plh_file = open(tavg_plh_file, 'r', encoding="utf-8", errors="surrogateescape")
                for line in mer_file:
                    minute_dummy = int(line.split('\t')[1])
            except:
                plh_file = open(plh_file, 'r', encoding="utf-8", errors="surrogateescape")

            mer_min = ''
            mer_avg = ''
            mer_max = ''
            for line in mer_file:
                try:
                    minute = int(line.split('\t')[1])
                    if minute % 60 == 0:
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
            plh_min = ''
            plh_avg = ''
            plh_max = ''
            for line in plh_file:
                try:
                    minute = int(line.split('\t')[1])
                    if minute % 60 == 0:
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
        return mer_avg, mer_max, mer_min, plh_avg, plh_max, plh_min, short_simulation

    def controller(program):
        def run_fall3d():
            GFSGRIB = os.path.join(ROOT, 'weather', 'data', mode)
            FALL3D = '/home/vulcanomod/FALL3D/fall3d-8.0.1/bin/Fall3d.r8.x'
            FALL3D_RUNS = os.path.join(RUNS, 'FALL3D')
            try:
                os.mkdir(FALL3D_RUNS)
            except FileExistsError:
                print('Folder ' + FALL3D_RUNS + ' exists')
            WTDATA = os.path.join(GFSGRIB, syr + smo + sda, shr_wt_st, mode + '.nc')
            RUNS_DAY = os.path.join(FALL3D_RUNS, syr + smo + sda)
            try:
                os.mkdir(RUNS_DAY)
            except FileExistsError:
                print('Folder ' + RUNS_DAY + ' exists')
            RUNS_TIME = os.path.join(RUNS_DAY,shr_wt_st)
            try:
                os.mkdir(RUNS_TIME)
            except FileExistsError:
                print('Folder ' + RUNS_TIME + ' exists')
            OP_INPUT = os.path.join(FALL3D_RUNS, mode + '_fall3d.inp')

            def update_input_files(mer, plh, solution):
                def distribute_processes(n):
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

                RUN = os.path.join(RUNS_TIME,solution)
                try:
                    os.mkdir(RUN)
                except FileExistsError:
                    print('Folder ' + RUN + ' exists')
                INPUT = os.path.join(RUN, mode + '_' + solution + '.inp')
                shutil.copyfile(OP_INPUT,INPUT)
                TGSD_FILE = os.path.join(RUN, mode + '_' + solution + '.tgsd.tephra')
                shutil.copyfile(os.path.join(TGSDS,tgsd),TGSD_FILE)
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
                plh_abv_vector = []
                plh_abv = ''
                max_altitude = 0
                for i in range(0,len(plh_vector)):
                    if float(plh_vector[i]) > max_altitude:
                        max_altitude = float(plh_vector[i])
                    plh_abv_vector.append(float(plh_vector[i]) - summit)
                    plh_abv += str(float(plh_vector[i]) - summit) + ' '
                    mer_string += mer_vector[i] + ' '
                max_altitude += 8000
                max_altitude = round(max_altitude, -3)
                dz = 1000
                n_levels = int(max_altitude / dz + 1)
                shr_er_end = float(shr) + eruption_dur
                source_start_string = ''
                source_end_string = ''
                max_altitude = round(max_altitude, -3)
                dz = 1000
                n_levels = int(max_altitude / dz + 1)
                levels = '0'
                altitude = 0
                while altitude < max_altitude:
                    altitude += dz
                    levels += ' ' + str(int(altitude))
                if not short_simulation:
                    time = 0
                    time_emission = time_now
                    time_end_emission = time_emission + datetime.timedelta(hours=1)
                    source_start_string += datetime.datetime.strftime(time_emission, "%H") + ' '
                    source_end_string += datetime.datetime.strftime(time_end_emission, "%H") + ' '
                    time += 1
                    while time <= int(eruption_dur) - 1:
                        time_emission += datetime.timedelta(hours=1)
                        time_end_emission = time_emission + datetime.timedelta(hours=1)
                        source_start_string += datetime.datetime.strftime(time_emission, "%H") + ' '
                        source_end_string += datetime.datetime.strftime(time_end_emission, "%H") + ' '
                        time += 1
                else:
                    source_start_string = shr
                    source_end_string = '{:.0f}'.format(shr_er_end)
                np, npx, npy, npz = distribute_processes(n_processes)
                lines = []
                with open(INPUT,'r',encoding="utf-8", errors="surrogateescape") as fall3d_input:
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

            np, npx, npy, npz = update_input_files(mer_avg, plh_avg, 'avg')
            np, npx, npy, npz = update_input_files(mer_max, plh_max, 'max')
            np, npx, npy, npz = update_input_files(mer_min, plh_min, 'min')

            def run_scripts(solution):
                RUN = os.path.join(RUNS_TIME, solution)
                INPUT = os.path.join(RUN, mode + '_' + solution + '.inp')
                command_setdbs = 'salloc -n ' + str(np) + ' -J FALL3D_SetDbs -t 01:00:00 mpirun -n ' + str(np) + ' ' + FALL3D + ' SetDbs ' + INPUT + ' ' + str(npx) + ' ' + str(npy) + ' ' + str(npz)
                command_setsrc = 'salloc -n 1 -J FALL3D_SetSrc -t 01:00:00 ' + FALL3D + ' SetSrc ' + INPUT
                command_fall3d = 'salloc -n ' + str(np) + ' -J FALL3D -t 01:00:00 mpirun -n ' + str(np) + ' ' + FALL3D + ' Fall3D ' + INPUT + ' ' + str(npx) + ' ' + str(npy) + ' ' + str(npz)
                os.system(command_setdbs)
                os.system(command_setsrc)
                os.system(command_fall3d)
            try:
                solutions = ['avg','max','min']
                pool_fall3d = ThreadingPool(3)
                pool_fall3d.map(run_scripts,solutions)
                #pool_fall3d.join()
            except:
                print('Error processing FALL3D in parallel')

        def run_hysplit():
            ARL = os.path.join(ROOT, 'weather', 'data', mode)
            HYSPLIT = '/home/vulcanomod/HYSPLIT/hysplit.v4.2.0/exec'
            HYSPLIT_RUNS = os.path.join(RUNS, 'HYSPLIT')
            try:
                os.mkdir(HYSPLIT_RUNS)
            except FileExistsError:
                print('Folder ' + HYSPLIT_RUNS + ' exists')
            ASCDATA = os.path.join(HYSPLIT_RUNS, 'ASCDATA.CFG')
            SETUP = os.path.join(HYSPLIT_RUNS, 'SETUP.CFG')
            WTDATA = os.path.join(ARL, syr + smo + sda, shr_wt_st)
            SIM = os.path.join(HYSPLIT_RUNS, syr + smo + sda, shr_wt_st)

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

                return n_bins, diam, rho, shape, wt_fraction, pollutants, diam_strings, rho_strings, shape_strings, wt_fraction_strings, pollutants_strings

            def update_control_files(mer, plh, solution):
                EMFILE = os.path.join(HYSPLIT_RUNS, 'EMITIMES_' + solution.upper() + '_poll')
                SIM_solution = os.path.join(SIM,solution)
                met = mode + '.arl'
                ADD_WTDATA = ARL
                metdata = 'oct1618.BIN'
                try:
                    os.mkdir(os.path.join(HYSPLIT_RUNS,syr+smo+sda))
                except FileExistsError:
                    print('Folder ' + os.path.join(HYSPLIT_RUNS,syr+smo+sda) + ' exists')
                try:
                    os.mkdir(SIM)
                except:
                    print('Folder ' + SIM + ' exists')
                try:
                    os.mkdir(SIM_solution)
                except:
                    print('Folder ' + SIM_solution + ' exists')
                os.chdir(SIM_solution)
                OUT = os.path.join(SIM_solution,'output')
                try:
                    os.mkdir(OUT)
                except FileExistsError:
                    print('Folder ' + OUT + ' exists')
                RUN = os.path.join(SIM_solution,'runs')
                try:
                    os.mkdir(RUN)
                except FileExistsError:
                    print('Folder ' + RUN + ' exists')
                os.chdir(RUN)
                for i in range(1,int(n_bins) + 1):
                    try:
                        os.mkdir('poll'+str(i))
                    except:
                        print('Folder ' + 'poll'+str(i) + ' exists in ' + RUN)
                    os.chdir('poll'+str(i))
                    try:
                        os.mkdir('output')
                    except FileExistsError:
                        print('Folder output exists in ' + os.path.join(RUN,'poll'+str(i)))
                    try:
                        os.mkdir('run')
                    except FileExistsError:
                        print('Folder run exists in ' + os.path.join(RUN, 'poll' + str(i)))
                    os.chdir(RUN)
                os.chdir(RUN)
                syr_2ch = syr[0:2]
                tot_particle_rate = 1000000
                particle_rate_proc = tot_particle_rate / float(n_bins)
                tot_particles = particle_rate_proc * eruption_dur
                ncpu_per_pollutant = n_processes / int(n_bins)
                if ncpu_per_pollutant > 10:
                    ncpu_per_pollutant = 10
                em_rates = []
                em_rates_strings = []
                if not short_simulation:
                    plh_vector = plh.split(' ')
                    plh_vector = plh_vector[1:]
                else:
                    plh_vector = []
                    plh_vector.append(plh)
                if short_simulation == False: # HYSPLIT will use EMITIMES
                    for i in range(0, len(plh_vector)):
                        plh_vector[i] = float(plh_vector[i])
                    max_altitude = max(plh_vector) + 8000
                    efile = 'EMITIMES'
                    for i in range(0, len(wt_fraction)):
                        em_rates.append(0.0)  # Here divide per the number of processes
                        em_rates_strings.append('em_rate[' + str(i + 1) + ']')
                else:
                    plh = float(plh_vector[0])
                    mer = float(mer) * 3600.0 * 1000 #Convert in g/h for HYSPLIT
                    max_altitude = plh + 8000
                    efile = ''
                    for i in range(0, len(wt_fraction)):
                        em_rates.append(mer * float(wt_fraction[i]) / float(n_processes))  # Here divide per the number of processes
                        em_rates_strings.append('em_rate[' + str(i+1) + ']')
                n_source_locations = 2 * len(plh_vector)
                max_altitude = round(max_altitude, -3)
                dz = 1000
                n_levels = int(max_altitude / dz + 1)
                levels = '0'
                altitude = 0
                while altitude < max_altitude:
                    altitude += dz
                    levels += ' ' + str(int(altitude))
                for i in range(1,int(n_bins)+1):
                    os.chdir(os.path.join(RUN,'poll'+str(i),'run'))
                    with open('CONTROL', 'w', encoding="utf-8", errors="surrogateescape") as control_file:
                        diam_micron = float(diam[i-1]) * 1000.0
                        rho_gcc = float(rho[i-1]) / 1000.0
                        control_file.write(syr_2ch + ' ' + smo + ' ' + sda + ' ' + shr + '\n')
                        control_file.write(str(n_source_locations) + '\n')
                        for j in range(0, len(plh_vector)):
                            control_file.write('{:.2f}'.format(float(volc_lat)) + ' ' + '{:.2f}'.format(float(volc_lon)) + ' ' + str(summit) + '\n')
                            control_file.write('{:.2f}'.format(float(volc_lat)) + ' ' + '{:.2f}'.format(float(volc_lon)) + ' ' + '{:.2f}'.format(float(plh_vector[j])) + '\n')
                        control_file.write('96\n')
                        control_file.write('0\n')
                        control_file.write(str(max_altitude) + '\n')
                        control_file.write('2\n')
                        control_file.write(WTDATA + '/\n')
                        control_file.write(met + '\n')
                        control_file.write(ADD_WTDATA + '/\n')
                        control_file.write(metdata + '\n')
                        control_file.write('1\n')
                        control_file.write(pollutants[i-1] + '\n')
                        control_file.write('{:.1f}'.format(em_rates[i-1]) + '\n')
                        control_file.write(str(eruption_dur) + '\n')
                        control_file.write(syr_2ch + ' ' + smo + ' ' + sda + ' ' + shr + ' 00\n')
                        control_file.write('1\n')
                        control_file.write('{:.1f}'.format(grid_centre_lat) + ' ' + '{:.1f}'.format(grid_centre_lon) + '\n')
                        control_file.write('0.05 0.05\n')
                        control_file.write(str(tot_dy) + ' ' + str(tot_dx) + '\n')
                        control_file.write('../output/\n')
                        control_file.write('cdump' + str(i) + '\n')
                        control_file.write(str(n_levels) + '\n')
                        control_file.write(levels + '\n')
                        control_file.write(syr_2ch + ' ' + smo + ' ' + sda + ' ' + shr + ' 00\n')
                        control_file.write('99 12 31 24 60\n')
                        control_file.write('00 01 00\n')
                        control_file.write('1\n')
                        control_file.write('{:.2f}'.format(diam_micron) + ' ' + '{:.1f}'.format(rho_gcc) + ' ' + shape[i-1] + '\n')
                        control_file.write('0.0 0.0 0.0 0.0 0.0\n')
                        control_file.write('0.0 0.0 0.0\n')
                        control_file.write('0.0\n')
                        control_file.write('0.0\n')
                    shutil.copyfile(SETUP,os.path.join(os.getcwd(),'SETUP.CFG'))
                    lines = []
                    with open('SETUP.CFG', 'r', encoding="utf-8", errors="surrogateescape") as setup_file:
                        for line in setup_file:
                            record = line.split(' = ')
                            if record[0] == ' numpar':
                                line = record[0] + ' = ' + str(int(particle_rate_proc)) + ',\n'
                            elif record[0] == ' maxpar':
                                line = record[0] + ' = ' + str(int(tot_particles)) + ',\n'
                            elif record[0] == ' efile':
                                line = record[0] + ' = \'' + efile  + '\',\n'
                            lines.append(line)
                    with open('SETUP.CFG', 'w', encoding="utf-8", errors="surrogateescape") as setup_file:
                        setup_file.writelines(lines)
                    if not short_simulation:
                        shutil.copyfile(EMFILE + str(i),os.path.join(os.getcwd(),'EMITIMES'))
                    shutil.copyfile(ASCDATA,os.path.join(os.getcwd(),'ASCDATA.CFG'))
                return ncpu_per_pollutant

            def create_emission_file(mer,plh,wt,emfile_name):
                emission_file = os.path.join(HYSPLIT_RUNS, emfile_name)
                mer_vector = mer.split(' ')
                mer_vector = mer_vector[1:]
                plh_vector = plh.split(' ')
                plh_vector = plh_vector[1:]
                n_records = int(eruption_dur * 2)
                time = 0
                em_file_records = []
                em_file_records.append('YYYY MM DD HH DURATION(hhhh) #RECORDS\n')
                em_file_records.append('YYYY MM DD HH MM DURATION(hhmm) LAT LON HGT(m) RATE(/h) AREA(m2) HEAT(w)\n')
                start_time_short = datetime.datetime.strftime(time_now, "%Y %m %d %H")
                time_emission = time_now
                time_emission_s = datetime.datetime.strftime(time_emission, "%Y %m %d %H %M")
                if eruption_dur < 10:
                    eruption_dur_s = '000' + str(int(eruption_dur))
                else:
                    eruption_dur_s = '00' + str(int(eruption_dur))
                em_file_records.append(start_time_short + ' ' + eruption_dur_s + ' ' + str(n_records) + '\n')
                while time <= eruption_dur - 1:
                    mer_bin = float(mer_vector[time]) * 3600 * 1000 * float(wt) / float(n_processes)
                    em_file_records.append(time_emission_s + ' 0100 ' + volc_lat + ' ' + volc_lon + ' ' + str(summit) + ' ' + '{:.5E}'.format(mer_bin) + ' 0.0 0.0\n')
                    em_file_records.append(time_emission_s + ' 0100 ' + volc_lat + ' ' + volc_lon + ' ' + plh_vector[time] + ' ' + '{:.5E}'.format(mer_bin) + ' 0.0 0.0\n')
                    time += 1
                    time_emission += datetime.timedelta(hours=1)
                    time_emission_s = datetime.datetime.strftime(time_emission, "%Y %m %d %H %M")
                with open(emission_file, 'w', encoding="utf-8", errors="surrogateescape") as em_file:
                    for record in em_file_records:
                        em_file.write(record)
            try:
                n_bins, diam, rho, shape, wt_fraction, pollutants, diam_strings, rho_strings, shape_strings, wt_fraction_strings, pollutants_strings = read_tgsd_file(tgsd)
            except:
                print('Unable to process file ' + tgsd)
                exit()
            if short_simulation == False:
                for i in range(0,len(wt_fraction)):
                    create_emission_file(mer_avg, plh_avg, wt_fraction[i], 'EMITIMES_AVG_poll' + str(i+1))
                    create_emission_file(mer_max, plh_max, wt_fraction[i], 'EMITIMES_MAX_poll' + str(i+1))
                    create_emission_file(mer_min, plh_min, wt_fraction[i], 'EMITIMES_MIN_poll' + str(i+1))
            ncpu_per_pollutant = update_control_files(mer_avg, plh_avg,'avg')
            ncpu_per_pollutant = update_control_files(mer_max, plh_max, 'max')
            ncpu_per_pollutant = update_control_files(mer_min, plh_min, 'min')

            def run_hysplit_mpi(path):
                os.chdir(path)
                #logger.write(os.getcwd())
                command = 'srun -J HYSPLIT_mpi sh ' + os.path.join(HYSPLIT, 'run_mpi.sh') + ' ' + '{:.0f}'.format(ncpu_per_pollutant) + ' hycm_std'
                os.system(command)

            def post_processing_hysplit(solution):
                SIM_solution = os.path.join(SIM, solution)
                OUT = os.path.join(SIM_solution,'output')
                RUN = os.path.join(SIM_solution, 'runs')
                for i in range(1, int(n_bins) + 1):
                    CDUMP_POLL = os.path.join(RUN, 'poll' + str(i), 'output', 'cdump' + str(i))
                    shutil.copyfile(CDUMP_POLL, os.path.join(OUT, 'cdump' + str(i)))
                if int(n_bins) == 1:
                    os.rename(os.path.join(OUT,'cdump1'), os.path.join(OUT,'cdump'))
                else:
                    os.rename(os.path.join(OUT,'cdump1'), os.path.join(OUT,'cdump_base'))
                    for i in range(2, int(n_bins) + 1):
                        os.system('srun -J HYSPLIT_concadd ' + os.path.join(HYSPLIT, 'concadd') + ' -i' + os.path.join(OUT,'cdump') + str(
                                i) + ' -b' + os.path.join(OUT,'cdump_base') + ' -o' + os.path.join(OUT,'cdump_temp'))
                        os.rename(os.path.join(OUT,'cdump_temp'), os.path.join(OUT,'cdump_base'))
                try:
                    os.rename(os.path.join(OUT,'cdump_base'), os.path.join(OUT,'cdump'))
                except:
                    print('File ' + os.path.join(OUT,'cdump_base') + ' not found')
                os.system('srun -J HYSPLIT_con2cdf4 ' + os.path.join(HYSPLIT, 'con2cdf4') + ' ' + os.path.join(OUT,'cdump') + ' ' + os.path.join(OUT,'cdump.nc'))
                for i in range(2, int(n_bins) + 1):
                    try:
                        os.remove(os.path.join(OUT, 'cdump' + str(i)))
                    except:
                        print('File ' + os.path.join(OUT, 'cdump' + str(i)) + ' not found')

            solutions = ['avg', 'max', 'min']
            #logger = open(os.path.join(ROOT,'logger.txt'),'a')
            paths = []
            for solution in solutions:
                SIM_solution = os.path.join(SIM, solution)
                RUN = os.path.join(SIM_solution, 'runs')
                for i in range(1, int(n_bins) + 1):
                    path = os.path.join(RUN, 'poll' + str(i), 'run')
                    paths.append(path)
            try:
                pool_hysplit = ThreadingPool(len(paths))
                pool_hysplit.map(run_hysplit_mpi,paths)
            except:
                print('Error processing HYSPLIT in parallel')

            try:
                pool_hysplit_post = ThreadingPool(3)
                pool_hysplit_post.map(post_processing_hysplit, solutions)
            except:
                print('Error processing HYSPLIT outputs in parallel')

        if program == 'fall3d':
            run_fall3d()
        elif program == 'hysplit':
            run_hysplit()

    mer_avg, mer_max, mer_min, plh_avg, plh_max, plh_min, short_simulation = read_refir_outputs(short_simulation)
    programs = ['fall3d','hysplit']
    pool_programs = ThreadingPool(2)
    pool_programs.map(controller, programs)
    pool_programs.join()

time_now = datetime.datetime.utcnow()
syr,smo,sda,shr,shr_wt_st,shr_wt_end,twodaysago = get_times(time_now)

if settings_file:
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
            elif line.split('=')[0] == 'DURATION':
                run_duration = int(line.split('=')[1])
            elif line.split('=')[0] == 'SHORT_SIMULATION':
                short_simulation = line.split('=')[1]
                try:
                    short_simulation = short_simulation.split('\n')[0]
                except:
                    None
                if short_simulation == 'True':
                    short_simulation = True
                elif short_simulation == 'False':
                    short_simulation = False
    tot_dx = lon_max - lon_min
    tot_dy = lat_max - lat_min
else:
    volc_id, n_processes, Iceland_scenario, lon_min, lon_max, lat_min, lat_max, tot_dx, tot_dy, run_duration = convert_args(
        volc_id, n_processes,  Iceland_scenario, lon_min, lon_max, lat_min, lat_max, run_duration)
dx = tot_dx / 2
dy = tot_dy / 2
grid_centre_lat = lat_min + dy
grid_centre_lon = lon_min + dx

if mode == 'operational':
    eruption_dur, eruption_plh, summit, volc_lat, volc_lon, tgsd = run_foxi()
else:
    eruption_dur, summit, volc_lat, volc_lon, tgsd = run_refir()
    # now download weather data
    os.system('python ' + os.path.join(ROOT,'weather_new.py') + ' --mode=manual --set=False --latmin=' + '{:.1f}'.format(lat_min) + ' --latmax=' + '{:.1f}'.format(lat_max) + ' --lonmin=' + '{:.1f}'.format(lon_min) + ' --lonmax=' + '{:.1f}'.format(lon_max))
# Check the tgsd file is available in TGSDs
tgsd_file = os.path.join(TGSDS,tgsd)
if not os.path.exists(tgsd_file):
    print('Unable to read file ' + tgsd + ' in ' + TGSDS)
    print('Please provide a readable TGSD file in ' + TGSDS + ' named ' + tgsd)
    s_input = input('Press Enter when the file is available')
    if s_input != '':
        print('Wrong input. Simulation aborting')
        exit()

def clean_folders():
    for file in os.listdir(REFIR):
        if file.startswith('run_' + twodaysago):
            shutil.rmtree(os.path.join(REFIR,file))
    for file in os.listdir(os.path.join(RUNS,'FALL3D')):
        if file == twodaysago:
            shutil.rmtree(os.path.join(RUNS,'FALL3D',file))
    for file in os.listdir(os.path.join(RUNS,'HYSPLIT')):
        if file == twodaysago:
            shutil.rmtree(os.path.join(RUNS,'HYSPLIT',file))
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

run_models(short_simulation)
clean_folders()

