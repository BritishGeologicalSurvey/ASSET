import os
import argparse
import sys
from shutil import which


def read_args():
    parser = argparse.ArgumentParser(description='Input data for the post_processing script')
    parser.add_argument('-M', '--mode', default='operational',
                        help='operational: routine simulation mode controlled via '
                             'operational_settings.txt\nmanual: run with user '
                             'specific inputs')
    parser.add_argument('-SET', '--set', default='True',
                        help='Read simulation parameters from operational_settings.txt')
    parser.add_argument('-LATMIN', '--latmin', default=999, help='Domain minimum latitude')
    parser.add_argument('-LATMAX', '--latmax', default=999, help='Domain maximum latitude')
    parser.add_argument('-LONMIN', '--lonmin', default=999, help='Domain minimum longitude')
    parser.add_argument('-LONMAX', '--lonmax', default=999, help='Domain maximum longitude')
    parser.add_argument('-MOD', '--model', default='all', help='Dispersion model to use. Options are: hysplit, fall3d, '
                                                               'all (both hysplit and fall3d)')
    parser.add_argument('-NR', '--no_refir', default='False',
                        help='True: avoid running REFIR for ESPs. False: run REFIR '
                             'for ESPs')
    args = parser.parse_args()
    mode_input = args.mode
    models_input = args.model
    no_refir_input = args.no_refir
    if mode_input != 'manual' and mode_input != 'operational':
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
    if no_refir_input.lower() == 'true':
        no_refir_input = True
    elif no_refir_input.lower() == 'false':
        no_refir_input = False
    else:
        print('WARNING. Wrong input for argument -NR --no_refir')
        no_refir_input = False

    if settings_file:
        with open('operational_settings.txt', 'r', encoding="utf-8", errors="surrogateescape") as settings:
            for line in settings:
                if line.split('=')[0] == 'LAT_MIN_[deg]':
                    lat_min_input = line.split('=')[1]
                    lat_min_input = lat_min_input.split('\n')[0]
                elif line.split('=')[0] == 'LAT_MAX_[deg]':
                    lat_max_input = line.split('=')[1]
                    lat_max_input = lat_max_input.split('\n')[0]
                elif line.split('=')[0] == 'LON_MIN_[deg]':
                    lon_min_input = line.split('=')[1]
                    lon_min_input = lon_min_input.split('\n')[0]
                elif line.split('=')[0] == 'LON_MAX_[deg]':
                    lon_max_input = line.split('=')[1]
                    lon_max_input = lon_max_input.split('\n')[0]
                elif line.split('=')[0] == 'NO_REFIR':
                    no_refir_input = line.split('=')[1]
                    no_refir_input = no_refir_input.split('\n')[0]
                    if no_refir_input.lower() == 'true':
                        no_refir_input = True
                    elif no_refir_input.lower() == 'false':
                        no_refir_input = False
                    else:
                        no_refir_input = False
                elif line.split('=')[0] == 'MODELS':
                    try:
                        models_input = line.split('=')[1]
                        models_input = models_input.split('\n')[0]
                    except IndexError:
                        models_input = 'all'
    else:
        if args.latmin == 999 or args.latmax == 999 or args.lonmin == 999 or args.lonmax == 999:
            print('Error. Wrong coordinate specification')
            print('Execution stopped')
            sys.exit()
        else:
            lon_min_input = args.lonmin
            lon_max_input = args.lonmax
            lat_min_input = args.latmin
            lat_max_input = args.latmax
    if models_input == 'all':
        models_input = ['FALL3D', 'HYSPLIT']
    elif models_input == 'hysplit':
        models_input = ['HYSPLIT']
    elif models_input == 'fall3d':
        models_input = ['FALL3D']
    else:
        print('Wrong model selection')
        sys.exit()
    return models_input, no_refir_input, lon_min_input, lon_max_input, lat_min_input, lat_max_input, mode_input


def post_process_model():
    def preprocess_models(model):

        def preprocess_hysplit_outputs(solution_file):
            folder_hysplit = os.path.dirname(solution_file)
            pre_process_hysplit_scheduler_file_path = os.path.join(folder_hysplit, 'pre_process.sh')
            with open(pre_process_hysplit_scheduler_file_path, 'w') as preprocess_hysplit_scheduler_file:
                preprocess_hysplit_scheduler_file.write('#!/bin/bash\n')
                if which('sbatch') is None:
                    preprocess_hysplit_scheduler_file.write('cd ' + folder_hysplit + '\n')
                else:
                    preprocess_hysplit_scheduler_file.write('#SBATCH --job-name=pre_hysplit\n')
                    preprocess_hysplit_scheduler_file.write('#SBATCH -o ' + os.path.join(folder_hysplit,
                                                                                         'pre_hysplit.out') + '\n')
                    preprocess_hysplit_scheduler_file.write('#SBATCH -e ' + os.path.join(folder_hysplit,
                                                                                         'pre_hysplit.err') + '\n')
                    preprocess_hysplit_scheduler_file.write('#SBATCH -n 1\n')
                    preprocess_hysplit_scheduler_file.write('source ~/.bashrc\n')
                    preprocess_hysplit_scheduler_file.write('cd ' + folder_hysplit + '\n')
            pollutants = ''
            with open(os.path.join(folder_hysplit, 'CONTROL'), 'r') as control_file:
                for line in control_file:
                    if 'AS' in line:
                        pollutants += line.strip('\n') + '+'
            pollutants = pollutants[:-1]
            pollutants = "'" + 'sum=' + pollutants + "'"
            try:
                cdump_nc_file = os.path.join(folder_hysplit, 'cdump.nc')
                cdump_sum_file = os.path.join(folder_hysplit, 'cdump_sum.nc')
                cdump_temp_file = os.path.join(folder_hysplit, 'cdump_temp.nc')
                with open(pre_process_hysplit_scheduler_file_path, 'a') as preprocess_hysplit_scheduler_file:
                    preprocess_hysplit_scheduler_file.write(os.path.join(HYSPLIT, 'con2cdf4') + ' ' + solution_file +
                                                            ' ' + cdump_nc_file + '\n')
                    preprocess_hysplit_scheduler_file.write('ncap2 -s ' + pollutants + ' ' + cdump_nc_file + ' ' +
                                                            cdump_sum_file + '\n')
                    preprocess_hysplit_scheduler_file.write('ncks -v sum ' + cdump_sum_file + ' ' + cdump_temp_file
                                                            + '\n')
                    preprocess_hysplit_scheduler_file.write('cp ' + cdump_temp_file + ' ' + cdump_nc_file + '\n')
                    preprocess_hysplit_scheduler_file.write('rm ' + cdump_sum_file + '\n')
                    preprocess_hysplit_scheduler_file.write('rm ' + cdump_temp_file + '\n')
                with open(scheduler_file_path, 'a') as scheduler_file:
                    if which('sbatch') is None:
                        scheduler_file.write('sh ' + pre_process_hysplit_scheduler_file_path + ' &\n')
                    else:
                        scheduler_file.write('sbatch -W ' + pre_process_hysplit_scheduler_file_path + ' &\n')
            except BaseException:
                print('Unable to process ' + cdump_nc_file + ' with ncap2 and ncks')
                files_to_remove.append(cdump_nc_file)
                folders_to_remove.append(folder_hysplit)

        def preprocess_fall3d_outputs(solution_file):
            folder_fall3d = os.path.dirname(solution_file)
            pre_process_fall3d_scheduler_file_path = os.path.join(folder_fall3d, 'pre_process.sh')
            with open(pre_process_fall3d_scheduler_file_path, 'w') as preprocess_fall3d_scheduler_file:
                preprocess_fall3d_scheduler_file.write('#!/bin/bash\n')
                if which('sbatch') is None:
                    preprocess_fall3d_scheduler_file.write('cd ' + folder_fall3d + '\n')
                else:
                    preprocess_fall3d_scheduler_file.write('#SBATCH --job-name=pre_fall3d\n')
                    preprocess_fall3d_scheduler_file.write('#SBATCH -o ' + os.path.join(folder_fall3d,
                                                                                         'pre_fall3d.out') + '\n')
                    preprocess_fall3d_scheduler_file.write('#SBATCH -e ' + os.path.join(folder_fall3d,
                                                                                         'pre_fall3d.err') + '\n')
                    preprocess_fall3d_scheduler_file.write('#SBATCH -n 1\n')
                    preprocess_fall3d_scheduler_file.write('source ~/.bashrc\n')
                    preprocess_fall3d_scheduler_file.write('cd ' + folder_fall3d + '\n')
            try:
                temp_cdo_file = str(solution_file) + '_cdo'
                with open(pre_process_fall3d_scheduler_file_path, 'a') as preprocess_fall3d_scheduler_file:
                    preprocess_fall3d_scheduler_file.write('cdo -selyear,2020/2999 ' + solution_file + ' ' +
                                                           temp_cdo_file + ' &> cdo.txt\n')
                    preprocess_fall3d_scheduler_file.write('mv ' + temp_cdo_file + ' ' + solution_file + '\n')
                with open(scheduler_file_path, 'a') as scheduler_file:
                    if which('sbatch') is None:
                        scheduler_file.write('sh ' + pre_process_fall3d_scheduler_file_path + ' &\n')
                    else:
                        scheduler_file.write('sbatch -W ' + pre_process_fall3d_scheduler_file_path + ' &\n')
            except BaseException:
                print('Unable to process ' + solution_file + ' with CDO')
                files_to_remove.append(solution_file)
                folders_to_remove.append(folder_fall3d)

        if model == 'FALL3D':
            for solution_file in solution_files_fall3d:
                preprocess_fall3d_outputs(solution_file)
        else:
            for solution_file in solution_files_hysplit:
                preprocess_hysplit_outputs(solution_file)


    def post_process_solution(output_folder, output_file):
        post_process_scheduler_file_path = os.path.join(output_folder, 'post_process.sh')
        if 'HYSPLIT' in str(output_file):
            model = 'hysplit'
        else:
            model = 'fall3d'
        try:
            output_dir = os.path.join(output_folder, 'iris_outputs')
            try:
                os.mkdir(output_dir)
            except FileExistsError:
                print('Folder ' + output_dir + ' already exists')
            with open(post_process_scheduler_file_path, 'w') as post_process_scheduler_file:
                post_process_scheduler_file.write('#!/bin/bash\n')
                if which('sbatch') is None:
                    post_process_scheduler_file.write('cd ' + output_folder + '\n')
                else:
                    post_process_scheduler_file.write('#SBATCH --job-name=plot_results\n')
                    post_process_scheduler_file.write('#SBATCH -o ' + os.path.join(output_folder, 'plot_results.out') +
                                                      '\n')
                    post_process_scheduler_file.write('#SBATCH -e ' + os.path.join(output_folder, 'plot_results.err') +
                                                      '\n')
                    post_process_scheduler_file.write('#SBATCH -n 16\n')
                    post_process_scheduler_file.write('#SBATCH -N 1\n')
                    post_process_scheduler_file.write('source ~/.bashrc\n')
                    post_process_scheduler_file.write('conda activate ash_model_plotting\n')
                    post_process_scheduler_file.write('cd ' + output_folder + '\n')
                    post_process_scheduler_file.write('plot_ash_model_results ' + output_file + ' --output_dir ' +
                                                      output_dir + ' --limits ' + lon_min + ' ' + lat_min + ' ' +
                                                      lon_max + ' ' + lat_max + ' --model_type ' + model + '\n')
            with open(scheduler_file_path, 'a') as scheduler_file:
                scheduler_file.write('sbatch ' + post_process_scheduler_file_path + ' &\n')
        except BaseException:
            print('Unable to process ' + output_file)

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
            elif 'HYSPLIT' in str(file_full_name) and 'cdump' in str(file_full_name) and '.nc' not in \
                    str(file_full_name):
                solution_files_hysplit.append(os.path.join(folder, file_full_name))

    for model in models:
        preprocess_models(model)

    with open(scheduler_file_path, 'a') as scheduler_file:
        scheduler_file.write('wait\n')

    for i in range(0, len(solution_files_hysplit)):
        solution_files_hysplit[i] += '.nc'
    solution_files = solution_files_fall3d + solution_files_hysplit
    s = set(folders_to_remove)
    solution_folders = [x for x in solution_folders if x not in s]
    s = set(files_to_remove)
    solution_files = [x for x in solution_files if x not in s]
    for i in range(0, len(solution_folders)):
        post_process_solution(solution_folders[i], solution_files[i])


ROOT = os.getcwd()
RUNS = os.path.join(ROOT, 'Runs')
HYSPLIT = os.environ.get('HYSPLIT')

scheduler_file_path = os.path.join(ROOT, 'scheduler_postprocessing.sh')
with open(scheduler_file_path, 'w') as scheduler_file:
    scheduler_file.write('#!/bin/bash\n')
    scheduler_file.write('cd ' + ROOT + '\n')

models, no_refir, lon_min, lon_max, lat_min, lat_max, mode = read_args()

RUNS_mode = os.path.join(RUNS, mode)
post_process_model()
os.system('sh ' + scheduler_file_path)
os.remove(scheduler_file_path)
