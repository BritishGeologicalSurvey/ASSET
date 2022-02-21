import os
import argparse
from pathos.multiprocessing import ThreadingPool
import sys
from shutil import which, copy

ROOT = os.getcwd()
RUNS = os.path.join(ROOT,'Runs')
#NP = int(os.environ["SLURM_JOB_CPUS_PER_NODE"])

parser = argparse.ArgumentParser(description='Input data for the post_processing script')
parser.add_argument('-M','--mode',default='operational',help='operational: routine simulation mode controlled via '
                                                             'operational_settings.txt\nmanual: run with user specific inputs')
parser.add_argument('-SET','--set',default='True',help='Read simulation parameters from operational_settings.txt')
parser.add_argument('-LATMIN','--latmin',default=999,help='Domain minimum latitude')
parser.add_argument('-LATMAX','--latmax',default=999,help='Domain maximum latitude')
parser.add_argument('-LONMIN','--lonmin',default=999,help='Domain minimum longitude')
parser.add_argument('-LONMAX','--lonmax',default=999,help='Domain maximum longitude')
parser.add_argument('-MOD','--model',default='all',help='Dispersion model to use. Options are: hysplit, fall3d, all '
                                                        '(both hysplit and fall3d)')
parser.add_argument('-NR', '--no_refir',default='False',help='True: avoid running REFIR for ESPs. False: run REFIR '
                                                             'for ESPs')
args = parser.parse_args()
mode = args.mode
models_in = args.model
no_refir = args.no_refir
if mode != 'manual' and mode != 'operational':
    print('Wrong value for variable --mode')
    print('Execution stopped')
    sys.exit()
if args.set == 'True':
    settings_file = True
elif args.set == 'False':
    settings_file = False
else:
    print('Wrong value for variable --set')
    print('Execution stopped')
    sys.exit()
if no_refir.lower() == 'true':
    no_refir = True
elif no_refir.lower() == 'false':
    no_refir = False
else:
    print('WARNING. Wrong input for argument -NR --no_refir')
    no_refir = False
RUNS_mode = os.path.join(RUNS, mode)

if settings_file:
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
            elif line.split('=')[0] == 'NO_REFIR':
                no_refir = line.split('=')[1]
                no_refir = no_refir.split('\n')[0]
                if no_refir.lower() == 'true':
                    no_refir = True
                elif no_refir.lower() == 'false':
                    no_refir = False
                else:
                    no_refir = False
            elif line.split('=')[0] == 'MODELS':
                try:
                    models_in = line.split('=')[1]
                    models_in = models_in.split('\n')[0]
                except:
                    models_in = 'all'
else:
    if args.latmin == 999 or args.latmax == 999 or args.lonmin == 999 or args.lonmax == 999:
        print('Error. Wrong coordinate specification')
        print('Execution stopped')
        sys.exit()
    else:
        lon_min = args.lonmin
        lon_max = args.lonmax
        lat_min = args.latmin
        lat_max = args.latmax
if models_in == 'all':
    models = ['FALL3D', 'HYSPLIT']
elif models_in == 'hysplit':
    models = ['HYSPLIT']
elif models_in == 'fall3d':
    models = ['FALL3D']
else:
    print('Wrong model selection')
    sys.exit()

def post_process_model():
    def post_process_solution(output_folder, output_file):
        if 'HYSPLIT' in str(output_file):
            model = 'hysplit'
        else:
            model = 'fall3d'
        try:
            output_dir = os.path.join(output_folder, 'iris_outputs')
            try:
                os.mkdir(output_dir)
            except:
                print('Folder ' + output_dir + ' already exists')
            os.system('plot_ash_model_results ' + output_file + ' --output_dir ' + output_dir +
                      ' --limits ' + lon_min + ' ' + lat_min + ' ' + lon_max + ' ' + lat_max + ' --model_type ' +
                      model)
        except:
            print('Unable to process ' + output_file)

    def preprocess_models(model):

        def preprocess_hysplit_outputs(solution_file):
            folder_hysplit = os.path.dirname(solution_file)
            pollutants = ''
            with open(os.path.join(folder_hysplit, 'CONTROL'), 'r') as control_file:
                for line in control_file:
                    if 'AS' in line:
                        pollutants += line.strip('\n') + '+'
            pollutants = pollutants[:-1]
            pollutants = "'" + 'sum=' + pollutants + "'"
            try:
                cdump_sum_file = os.path.join(folder_hysplit, 'cdump_sum.nc')
                cdump_temp_file = os.path.join(folder_hysplit, 'cdump_temp.nc')
                os.system('ncap2 -s ' + pollutants + ' ' + solution_file + ' ' + cdump_sum_file)
                os.system('ncks -v sum ' + cdump_sum_file + ' ' + cdump_temp_file)
                copy(cdump_temp_file, solution_file)
            except:
                print('Unable to process ' + solution_file + ' with ncap2 and ncks')
                files_to_remove.append(solution_file)
                folders_to_remove.append(folder_hysplit)


        def preprocess_fall3d_outputs(solution_file):
            folder_fall3d = os.path.dirname(solution_file)
            try:
                temp_cdo_file = str(solution_file) + '_cdo'
                os.system('cdo -selyear,2020/2999 ' + solution_file + ' ' + temp_cdo_file + ' &> cdo.txt')
                os.rename(temp_cdo_file, solution_file)
            except:
                print('Unable to process ' + solution_file + ' with CDO')
                files_to_remove.append(solution_file)
                folders_to_remove.append(folder_fall3d)

        if model == 'FALL3D':
            try:
                pool_pre_fall3d = ThreadingPool(len(solution_files_fall3d))
                pool_pre_fall3d.map(preprocess_fall3d_outputs, solution_files_fall3d)
            except:
                print('Error pre-processing FALL3D outputs')
        else:
            try:
                pool_pre_hysplit = ThreadingPool(len(solution_files_hysplit))
                pool_pre_hysplit.map(preprocess_hysplit_outputs, solution_files_hysplit)
            except:
                print('Error pre-processing HYSPLIT outputs')
        return folders_to_remove, files_to_remove


    folders_to_remove = []
    files_to_remove = []
    solution_folders = []
    solution_files_fall3d = []
    solution_files_hysplit = []
    for model in models:
        MODEL_RUNS = os.path.join(RUNS_mode, model)
        files = os.listdir(MODEL_RUNS)
        paths = []
        for file in files:
            paths.append(os.path.join(MODEL_RUNS, file))
        latest_path = max(paths, key=os.path.getmtime)
        latest_run_day = os.path.join(latest_path, latest_path)
        files = os.listdir(latest_run_day)
        paths = []
        for file in files:
            paths.append(os.path.join(latest_run_day, file))
        latest_path = max(paths, key=os.path.getmtime)
        latest_run_time = os.path.join(latest_run_day, latest_path)
        for folder in os.listdir(latest_run_time):
            solution_folder = os.path.join(latest_run_time, folder)
            if os.path.isdir(solution_folder):
                solution_folders.append(solution_folder)
    for folder in solution_folders:
        files = os.listdir(folder)
        for file in files:
            file_full_name = os.path.join(folder, file)
            if 'FALL3D' in str(file_full_name) and file.endswith('res.nc'):
                solution_files_fall3d.append(file_full_name)
            elif 'HYSPLIT' in str(file_full_name) and file.endswith('.nc'):
                solution_files_hysplit.append(os.path.join(folder, file_full_name))
    try:
        pool_preprocess = ThreadingPool(len(models))
        pool_preprocess.map(preprocess_models, models)
    except:
        print('Error pre-processing outputs in parallel')

    solution_files = solution_files_fall3d + solution_files_hysplit
    s = set(folders_to_remove)
    solution_folders = [x for x in solution_folders if x not in s]
    s = set(files_to_remove)
    solution_files = [x for x in solution_files if x not in s]
    try:
        pool_solution_post = ThreadingPool(len(solution_folders))
        pool_solution_post.map(post_process_solution, solution_folders, solution_files)
    except:
        print('Error processing outputs in parallel')

post_process_model()


