from tkinter import *

get_inputs = Tk()
out = StringVar()
short_simulation = BooleanVar()
fall3d_on = IntVar()
hysplit_on = IntVar()

def get_input_data():
    get_inputs.title("Input control")
    Label(get_inputs, text="Set computational domain", \
          font="Helvetica 12", fg="blue").grid(row=0, column=0, columnspan=6)
    Label(get_inputs, text="Latitude: ", \
          font="Helvetica 11", fg="green").grid(row=5, column=0, columnspan=2, sticky=W)
    Label(get_inputs, text="Min: ", font="Helvetica 10").grid(row=6, column=0, sticky=W)
    Label(get_inputs, text="Max: ", font="Helvetica 10").grid(row=6, column=1, sticky=W)
    Label(get_inputs, text="Longitude: ", \
          font="Helvetica 11", fg="green").grid(row=8, column=0, columnspan=2, sticky=W)
    Label(get_inputs, text="Min: ", font="Helvetica 10").grid(row=9, column=0, sticky=W)
    Label(get_inputs, text="Max: ", font="Helvetica 10").grid(row=9, column=1, sticky=W)
    Label(get_inputs, text="Set volcano: ", \
          font="Helvetica 11", fg="blue").grid(row=11, column=0, columnspan=6)
    Label(get_inputs, text="SI ID: ", font="Helvetica 10").grid(row=12, column=0, sticky=W)
    Label(get_inputs, text="Other parameters: ", \
          font="Helvetica 11", fg="blue").grid(row=11, column=0, columnspan=6)
    Label(get_inputs, text="N Processors: ", font="Helvetica 10").grid(row=13, column=0, sticky=W)
    Label(get_inputs, text="ADM duration (hrs): ", font="Helvetica 10").grid(row=14, column=0, sticky=W)
    Label(get_inputs, text="Eruption duration (hrs): ", font="Helvetica 10").grid(row=15, column=0, sticky=W)
    Label(get_inputs, text="Source resolution (mins): ", font="Helvetica 10").grid(row=16, column=0, sticky=W)
    Label(get_inputs, text="Particles emission rate (p/hr): ", font="Helvetica 10").grid(row=17, column=0, sticky=W)
    Label(get_inputs, text="Output interval (hrs): ", font="Helvetica 10").grid(row=18, column=0, sticky=W)
    Label(get_inputs, text="Model selection", font="Helvetica 10").grid(row=19, column=0, sticky=W)
    Checkbutton(get_inputs, text='FALL3D', variable=fall3d_on, onvalue=1, offvalue=0).grid(row=19, column=1)
    Checkbutton(get_inputs, text='HYSPLIT', variable=hysplit_on, onvalue=1, offvalue=0).grid(row=19, column=2)
    Label(get_inputs, text="REFIR Short", font="Helvetica 10").grid(row=20, column=0, sticky=W)
    Radiobutton(get_inputs, text="True", variable=short_simulation, value=True).grid(row=20, column=1)
    Radiobutton(get_inputs, text="False", variable=short_simulation, value=False).grid(row=20, column=2)
    lat_min_in = Entry(get_inputs, width=8)
    lat_min_in.grid(row=6, column=0, sticky=E)
    lat_max_in = Entry(get_inputs, width=8)
    lat_max_in.grid(row=6, column=2, sticky=E)
    lon_min_in = Entry(get_inputs, width=8)
    lon_min_in.grid(row=9, column=0, sticky=E)
    lon_max_in = Entry(get_inputs, width=8)
    lon_max_in.grid(row=9, column=2, sticky=E)
    volcano_ID_in = Entry(get_inputs, width=6)
    volcano_ID_in.grid(row=12, column=1, sticky=W)
    np_in = Entry(get_inputs, width=4)
    np_in.grid(row=13, column=1, sticky=W)
    duration_in = Entry(get_inputs, width=4)
    duration_in.grid(row=14, column=1, sticky=W)
    er_duration_in = Entry(get_inputs, width=4)
    er_duration_in.grid(row=15, column=1, sticky=W)
    source_resolution_in = Entry(get_inputs, width=4)
    source_resolution_in.grid(row=16, column=1, sticky=W)
    per_in = Entry(get_inputs, width=10)
    per_in.grid(row=17, column=1, sticky=W)
    output_interval_in = Entry(get_inputs, width=4)
    output_interval_in.grid(row=18, column=1, sticky=W)

    def on_button():
        global lat_max, lat_min, lon_max, lon_min, volcano_ID, np, duration, short_simulation_s, lat_grid_centre, lon_grid_centre, er_duration, source_resolution, per, output_interval, models
        lat_max = str(lat_max_in.get())
        lat_min = str(lat_min_in.get())
        lon_max = str(lon_max_in.get())
        lon_min = str(lon_min_in.get())
        volcano_ID = str(volcano_ID_in.get())
        np = str(np_in.get())
        duration = str(duration_in.get())
        er_duration = str(er_duration_in.get())
        source_resolution = str(source_resolution_in.get())
        per = str(per_in.get())
        short_simulation_s = str(short_simulation.get())
        output_interval = str(output_interval_in.get())
        lat_grid_centre = float(lat_min) + (float(lat_max) - float(lat_min)) / 2
        lon_grid_centre = float(lon_min) + (float(lon_max) - float(lon_min)) / 2
        if fall3d_on.get() == 1:
            if hysplit_on.get() == 1:
                models = 'all'
            else:
                models = 'fall3d'
        else:
            models = 'hysplit'

    Button(get_inputs, text="Confirm inputs", font="Helvetica 11", fg="yellow", bg="red", \
           width=24, height=2, command=on_button).grid(row=21, column=0, columnspan=5)

    get_inputs.mainloop()

get_input_data()

with open('operational_settings.txt','w',encoding="utf-8", errors="surrogateescape") as settings_file:
    settings_file.write('LAT_MIN_[deg]=' + lat_min + '\n')
    settings_file.write('LAT_MAX_[deg]=' + lat_max + '\n')
    settings_file.write('LON_MIN_[deg]=' + lon_min + '\n')
    settings_file.write('LON_MAX_[deg]=' + lon_max + '\n')
    settings_file.write('VOLCANO_ID=' + volcano_ID + '\n')
    settings_file.write('NP=' + np + '\n')
    settings_file.write('DURATION_[hours]=' + duration + '\n')
    settings_file.write('SHORT_SIMULATION=' + short_simulation_s + '\n')
    settings_file.write('ERUPTION_DURATION_[hours]=' + er_duration + '\n')
    settings_file.write('SOURCE_RESOLUTION_[hours]=' + source_resolution + '\n')
    settings_file.write('PARTICLE_EMISSION_RATE_[p/hr]=' + per + '\n')
    settings_file.write('OUTPUT_INTERVAL_[hr]=' + output_interval + '\n')
    settings_file.write('MODELS=' + models)

