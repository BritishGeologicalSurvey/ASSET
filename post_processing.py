import os
import argparse
from pathos.multiprocessing import ThreadingPool
import sys
from shutil import which

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
    def post_process_solution(output_folder, output_file, model_in):
        try:
            output_dir = os.path.join(output_folder,'iris_outputs')
            try:
                os.mkdir(output_dir)
            except:
                print('Folder ' + output_dir + ' already exists')
            if which('srun') is None:
                os.system('plot_ash_model_results ' + output_file + ' --output_dir ' + output_dir +
                          ' --limits ' + lon_min + ' ' + lat_min + ' ' + lon_max + ' ' + lat_max + ' --model_type ' +
                          model_in)
            else:
                os.system('salloc -n 16 plot_ash_model_results ' + output_file + ' --output_dir ' + output_dir +
                      ' --limits ' + lon_min + ' ' + lat_min + ' ' + lon_max + ' ' + lat_max + ' --model_type ' +
                      model_in)
        except:
            print('Unable to process ' + output_file)

    model_type = []
    solution_folders = []
    solution_files = []
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
    folders_to_remove = []
    for folder in solution_folders:
        if 'FALL3D' in str(folder):
            model_type.append('fall3d')
            files = os.listdir(folder)
            file_check = False
            for file in files:
                if str(file).endswith('.res.nc'):
                    solution_files.append(os.path.join(folder, file))
                    file_check = True
                    try:
                        temp_cdo_file = str(file) + '_cdo'
                        if which('srun') is None:
                            os.system('cdo -selyear,2020/2999 ' + os.path.join(folder, file) + ' ' +
                                  os.path.join(folder, temp_cdo_file) + ' &> cdo.txt')
                        else:
                            os.system('srun -J CDO cdo -selyear,2020/2999 ' + os.path.join(folder, file) + ' ' +
                                      os.path.join(folder, temp_cdo_file) + ' &> cdo.txt')
                        os.rename(os.path.join(folder, temp_cdo_file), os.path.join(folder, file))
                    except:
                        file_check = False
                        print('Unable to process ' + solution_files[-1] + ' with CDO')
            if file_check == False:
                folders_to_remove.append(folder)
                del model_type[-1]
        else:
            model_type.append('hysplit')
            files = os.listdir(folder)
            file_check = False  # If no res.nc file found, it remains False
            for file in files:
                if file.endswith('.nc'):
                    file_check = True
                    solution_files.append(os.path.join(folder, file))
            if file_check == False:
                folders_to_remove.append(folder)
                del model_type[-1]
        s = set(folders_to_remove)
        solution_folders = [x for x in solution_folders if x not in s]
    try:
        pool_solution_post = ThreadingPool(len(solution_folders))
        pool_solution_post.map(post_process_solution, solution_folders, solution_files, model_type)
    except:
        print('Error processing outputs in parallel')

post_process_model()


