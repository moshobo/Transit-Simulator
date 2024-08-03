import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from mpl_toolkits.basemap import Basemap
import gtfs_kit as gk

DIR = Path('')
sys.path.append(str(DIR))
DATA_DIR = DIR/'data/gtfs-data'
path = DATA_DIR/'example/SoundTransit_072624_40_gtfs.zip' # Example Sound Transit GTFS data
# path = DATA_DIR/'example/KCM_050524_GTFS_google_transit.zip' # Example King County Metro GTFS data

feed = gk.read_feed(path, dist_units='mi')
moving_feed = feed.append_dist_to_stop_times()

# Configurable Paramters
simulation_date = '2024-08-31'
simulation_start_time = '07:00:00'
simulation_end_time = '10:00:00'
plot_title = "Link Light Rail"
route_ids = ["100479", "2LINE"] # Route IDs to plot
# route_ids = ["100512", "102548", "102576", "102581", "102615", "102619", "102736"] # KCM Rapid Ride

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
            route_color == "#96182e"
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

ani.save(f"Line1_{simulation_date}.gif") # Save animation as a gif
plt.show()