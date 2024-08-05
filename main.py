import warnings
# Suppress FutureWarning messages
warnings.filterwarnings("ignore", "\nPyarrow", DeprecationWarning)

import argparse
import sys
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from mpl_toolkits.basemap import Basemap
from pathlib import Path
from datetime import datetime, timedelta
import gtfs_kit as gk

parser = argparse.ArgumentParser()
data_group = parser.add_mutually_exclusive_group(required=True)
data_group.add_argument(
    "-f",
    "--file",
    help="Specify a GTFS feed ZIP file. File should be located in /data/gtfs-data"
)

data_group.add_argument(
    "-u",
    "--url",
    help="Specify a GTFS feed URL"
)

parser.add_argument(
    "-d",
    "--date",
    help = "Start date of the simulation in YYYY-MM-DD format."
)

parser.add_argument(
    "-s",
    "--start-time",
    help = "Start time of the simulation in hh:mm:ss format."
)

parser.add_argument(
    "-e",
    "--end-time",
    help = "End time of the simulation in hh:mm:ss format."
)

parser.add_argument(
    "-r",
    "--routes",
    nargs='+',
    help = "Routes to display in the output GIF file"
)

parser.add_argument(
    "-t",
    "--title",
    help = "Title to be used for the output GIF file"
)

DIR = Path('')
sys.path.append(str(DIR))
DATA_DIR = DIR/'data/gtfs-data'

args = parser.parse_args()
if args.url:
    path = args.url
else:
    path = DATA_DIR/args.file
    print(f"Path is a file: {path}")

if args.date:
    simulation_date = args.date
else:
    current_date = datetime.now().date()
    simulation_date = current_date.strftime("%Y-%m-%d")

if args.start_time:
    simulation_start_time = args.start_time
else:
    current_time = datetime.now().time()
    simulation_start_time = current_time.strftime("%H:%M:%S")

if args.end_time:
    simulation_end_time = args.date
else:
    start_time_datetime = datetime.strptime(simulation_start_time, "%H:%M:%S")
    new_time_datetime = start_time_datetime + timedelta(hours=1)
    simulation_end_time = new_time_datetime.strftime("%H:%M:%S")

feed = gk.read_feed(path, dist_units='mi')
moving_feed = feed.append_dist_to_stop_times()
all_routes = [r for r in feed.get_routes()["route_id"]]

if args.routes:
    route_ids = args.routes
    valid_routes = []
    for route in args.routes:
        if route in all_routes:
            valid_routes.append(route)
    
    if not valid_routes:
        raise ValueError(f"No valid routes provided")
    else:
        route_ids = valid_routes
else:
    route_ids = [all_routes[0]]

# Create a Basemap instance with the desired projection
plt.figure(figsize=(8,8))

# Use resolutions of 'h' or 'f' for greater detail
my_map = Basemap(llcrnrlon=-122.6, llcrnrlat=47.4, urcrnrlon=-122.0, urcrnrlat=47.9,
            projection='lcc', resolution='f', lat_0=47.5, lon_0=-122.3)

# Draw geographic features
my_map.drawmapboundary(fill_color='lightcyan')
my_map.fillcontinents(lake_color='lightcyan')
my_map.drawcoastlines(color='cadetblue')

# Plot route shapes and stops
route_geo_json_array = feed.routes_to_geojson(include_stops=True)
route_names = []
plotted_stations = []

for route in route_geo_json_array["features"]:
    x_route = []
    y_route = []
    x_stop = []
    y_stop = []

    try:
        route_color = "#" + str(route["properties"]["route_color"])
        if route_color == "#None":
            route_color = "#96182e"
    except KeyError:
        route_color = "#96182e"
    
    # Identify station coordinates
    if route["geometry"]["type"] == "Point":
        station_id = route["properties"]["parent_station"] or route["properties"]["stop_code"] or route["properties"]["stop_id"]
        if station_id.startswith(("C", "S", "N", "E")) and not station_id.startswith(("SN", "SS")): # Only 1 Line (C/N/S) or 2 Line (E), but not "SS" for Sounder North/South
            s_x, s_y = route["geometry"]["coordinates"]
            projs_x, projs_y = my_map(s_x, s_y)  # Convert lat/lon to map coords
            x_stop.append(projs_x)
            y_stop.append(projs_y)

    else: # Line coordinates
        route_id = route["properties"]["route_id"]
        if route_id not in route_ids:
            continue
        else:
            route_names.append(route["properties"]["route_short_name"])
        
        route_points = route["geometry"]["coordinates"]
        if route["geometry"]["type"] == "LineString":
            route_coords = route_points
        else:
            route_coords = route_points[0]

        for coord in route_coords:
            projc_x, projc_y = my_map(coord[0], coord[1]) # Convert lat/lon to map coords
            x_route.append(projc_x)
            y_route.append(projc_y)

    my_map.plot(x_route, y_route, marker='', color=route_color, linestyle='-', linewidth=2) # Plot route shape
    my_map.plot(x_stop,y_stop, marker='o', color='white', markeredgecolor='black') # Plot route stops

# Get location of trips between specified times
date_string = ''.join(simulation_date.split('-'))
start_time = simulation_date + ' ' + simulation_start_time
end_time = simulation_date + ' ' + simulation_end_time

rng = pd.date_range(start=start_time, end=end_time, freq='30s')
times = [t.strftime('%H:%M:%S') for t in rng]
loc = moving_feed.locate_trips(date_string, times)
filtered_route_loc = loc[loc['route_id'].isin(route_ids)].sort_values('time', ascending=True).copy()

# Check that there will be route information to animate
if len(filtered_route_loc) == 0:
    raise Exception("No frames to animate. Length of target_route is zero.")

x_trip = []
y_trip = []

# Get coordinates for trips within the simulation time range
for time in times:
    matching_rows = filtered_route_loc[filtered_route_loc['time'] == time]
    
    if not matching_rows.empty:
        lon_values = matching_rows['lon'].tolist()
        lat_values = matching_rows['lat'].tolist()

        x_trip.append(lon_values)
        y_trip.append(lat_values)

# Plot trip animation
if args.title:
    plot_title = args.title
else:
    plot_title = "Transit Simulator"

plt.title(plot_title, fontsize=18, loc='left', color='royalblue', style='italic')
plt.title('                    created by moshobo', fontsize=10, loc='center', color="k")

animated_plot, = my_map.plot(
    [],
    [],
    latlon=True,
    color='k',
    marker='s',
    linestyle='None',
    zorder=8
)

def update_data(frame):
    x0, y0 = my_map(x_trip[frame], y_trip[frame])
    animated_plot.set_data(x0, y0)
    vehicle_count = len(x_trip[frame])
    plt.title(
        f"{simulation_date} {times[frame]} \n{vehicle_count} active vehicles ",
        loc='right',
        color='dimgray',
        y=0.92
    )

    return animated_plot

ani = animation.FuncAnimation(
    fig=plt.gcf(),
    func=update_data,
    frames=len(x_trip),
    interval=100,
    repeat=True,
    repeat_delay=1000
)

title_routes = '_'.join(route_ids)
ani.save(f"{title_routes}_{simulation_date}.gif") # Save animation as a gif
plt.show()