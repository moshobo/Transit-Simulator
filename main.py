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

def update_data(frame):
    """Update animated plot for each frame"""
    
    frame_data = trip_positions[frame]

    total_vehicles = 0

    for route_id, plot in animated_plots.items():
        if route_id in frame_data:
            lons, lats = frame_data[route_id]
            x, y = transit_map(lons, lats)
            plot.set_data(x, y)
            total_vehicles += len(lons)
        else:
            plot.set_data([], [])

    plt.title(
        f"{simulation_date} {times[frame]}\n{total_vehicles} active vehicles",
        loc='right',
        color='dimgray',
        y=0.92
    )

    return list(animated_plots.values())

def validate_args_to_feed(feed, simulation_date):
    """Validate command line arguments are valid for the feed"""
    
    # Validate feed contains calendar for target simulation date
    target_date = simulation_date.replace("-","")
    feed_dates = feed.get_dates()

    if target_date not in feed_dates:
        raise ValueError(f"Simulation date {target_date} not found in feed dates. Valid dates from {feed_dates[0]} to {feed_dates[-1]}")

parser = argparse.ArgumentParser()
data_group = parser.add_mutually_exclusive_group(required=True)
data_group.add_argument(
    "-f",
    "--file",
    help="Specify a GTFS feed ZIP file. File should be located in /data/gtfs-data."
)

data_group.add_argument(
    "-u",
    "--url",
    help="Specify a GTFS feed URL."
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
    help = "Routes to display in the output GIF file. Use 'all' to select every route in the GTFS feed."
)

parser.add_argument(
    "-t",
    "--title",
    nargs='+',
    help = "Title to be used on the outputted plot."
)

parser.add_argument(
    "--station-labels",
    nargs='*',
    help = "Display station names as labels on the plot."
)

DIR = Path('')
sys.path.append(str(DIR))
DATA_DIR = DIR/'data/gtfs-data'

args = parser.parse_args()
if args.url:
    path = args.url
else:
    path = DATA_DIR/args.file

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
    simulation_end_time = args.end_time
else:
    start_time_datetime = datetime.strptime(simulation_start_time, "%H:%M:%S")
    new_time_datetime = start_time_datetime + timedelta(hours=1)
    simulation_end_time = new_time_datetime.strftime("%H:%M:%S")

feed = gk.read_feed(path, dist_units='mi')
validate_args_to_feed(feed, simulation_date)
moving_feed = feed.append_dist_to_stop_times()
all_routes = [r for r in feed.get_routes()["route_id"]]

if args.routes:
    if args.routes[0] == "all":
        route_ids = all_routes
    else:
        route_ids = args.routes
        valid_routes = []
        for user_route in args.routes:
            if user_route in all_routes:
                valid_routes.append(user_route)
        
        if not valid_routes:
            raise ValueError(f"No valid routes provided")
        else:
            route_ids = valid_routes
else:
    route_ids = [all_routes[0]]

# Plot route shapes and stops
route_geo_json_array = feed.routes_to_geojson(include_stops=True)
route_names = [] # Currently unused
all_stops = feed.get_stops()

llcrnrlon_0 = 0.0
llcrnrlat_0 = 0.0
urcrnrlon_0 = 0.0
urcrnrlat_0 = 0.0
routes = {}

# Export route and its accompanying stations in lon/lat format
for route in route_geo_json_array["features"]: 
    if route["geometry"]["type"] in ["LineString", "MultiLineString"]: # TODO: Could this if statement be removed by doing more filtering in the For loop?
        route_id = route["properties"]["route_id"]
        if route_id not in route_ids:
            continue

        # Update route_color if one is provided by the feed
        try:
            route_color = "#" + str(route["properties"]["route_color"])
            if route_color == "#None":
                route_color = "#FFFFFF"
        except KeyError:
            route_color = "#FFFFFF"
        
        # Attempt to use stations (location_type == 1) where possible to simplify visuals
        route_stops = feed.get_stops(route_ids=[route_id])
        route_stations = {}
        for index, stop in route_stops.iterrows():
            if stop["location_type"] == 1: # Station
                route_stations[stop["stop_id"]] = {
                    'lat': stop["stop_lat"],
                    "lon": stop["stop_lon"],
                    "name": stop["stop_name"]
                }
            elif stop["location_type"] == 0 or pd.isna(stop["location_type"]): # Stop or platform   
                parent_station_stop_id = stop["parent_station"]
                if pd.isna(parent_station_stop_id):
                    route_stations[stop["stop_id"]] = {
                        'lat': stop["stop_lat"],
                        "lon": stop["stop_lon"],
                        "name": stop["stop_name"]
                    }
                # Use the station since it is available
                else:
                    if parent_station_stop_id not in route_stations.keys():
                        parent_lat = float(
                            all_stops[all_stops["stop_id"] == parent_station_stop_id]["stop_lat"].iloc[0]
                        )
                        parent_lon = float(
                            all_stops[all_stops["stop_id"] == parent_station_stop_id]["stop_lon"].iloc[0]
                        )
                        route_stations[parent_station_stop_id] = {
                            "lat": parent_lat,
                            "lon": parent_lon,
                            "name": stop["stop_name"]
                        }
            else:
                raise TypeError(f"Unsupported location_type of {stop['location_type']}")

        route_points = route["geometry"]["coordinates"]
        if route["geometry"]["type"] == "LineString":
            route_coords = [route_points]
        else:
            route_coords = route_points

        route_station_lon_array = [route_stations[station]["lon"] for station in route_stations.keys()]
        route_station_lat_array = [route_stations[station]["lat"] for station in route_stations.keys()]

        # Find the upper and lower bounds of the filtered stations
        # TODO: Simplify if/else statements
        if urcrnrlon_0 == 0.0:
            urcrnrlon_0 = max(route_station_lon_array)
        else:
            if max(route_station_lon_array) > urcrnrlon_0:
                urcrnrlon_0 = max(route_station_lon_array)

        if llcrnrlon_0 == 0.0:
            llcrnrlon_0 = min(route_station_lon_array)
        else:
            if min(route_station_lon_array) < llcrnrlon_0:
                llcrnrlon_0 = min(route_station_lon_array)

        if urcrnrlat_0 == 0.0:
            urcrnrlat_0 = max(route_station_lat_array)
        else:
            if max(route_station_lat_array) > urcrnrlat_0:
                urcrnrlat_0 = max(route_station_lat_array)

        if llcrnrlat_0 == 0.0:
            llcrnrlat_0 = min(route_station_lat_array)
        else:
            if min(route_station_lat_array) < llcrnrlat_0:
                llcrnrlat_0 = min(route_station_lat_array)

        routes[route_id] = {"route_color": route_color, "route_coords": route_coords, "route_stations": route_stations}

# TODO: Make the zoom factor dynamic for the lat / lon so that its something like 10% more than the max-min
zoom_factor = 0.02 # Add padding around station coordinates 
plt.figure(figsize=(8,8))
transit_map = Basemap(
    llcrnrlon=llcrnrlon_0-(zoom_factor),
    llcrnrlat=llcrnrlat_0-(zoom_factor),
    urcrnrlon=urcrnrlon_0+(zoom_factor),
    urcrnrlat=urcrnrlat_0+(zoom_factor),
    projection='lcc',
    resolution='f',
    lat_0=urcrnrlat_0 - (urcrnrlat_0 - llcrnrlat_0),
    lon_0=urcrnrlon_0 - (urcrnrlon_0 - llcrnrlon_0)
)

# Draw geographic features
transit_map.fillcontinents(lake_color='white', color=(.9, .9, .9))

# Plot routes and their stops on map
target_station_names = args.station_labels if args.station_labels else []

for route in routes:

    route_color = routes[route]["route_color"]
    route_coords = routes[route]["route_coords"]
    route_stations = routes[route]["route_stations"]

    x_route_proj = []
    y_route_proj = []
    x_stop_proj = []
    y_stop_proj = []
    route_station_names = []

    # Convert the x/y for the route's stations to map coord system
    for station in route_stations: 
        s_x, s_y = route_stations[station]["lon"], route_stations[station]["lat"]
        projs_x, projs_y = transit_map(s_x, s_y)
        x_stop_proj.append(projs_x)
        y_stop_proj.append(projs_y)
        route_station_names.append(route_stations[station]['name'])
    
    # Convert the x/y for the route's line to map coord system
    for route in route_coords:
        x_route_proj = []
        y_route_proj = []
        for coord in route:
            projc_x, projc_y = transit_map(coord[0], coord[1])
            x_route_proj.append(projc_x)
            y_route_proj.append(projc_y)
        
        transit_map.plot(x_route_proj, y_route_proj, marker='', color=route_color, linestyle='-', linewidth=2)
    
    transit_map.scatter(x_stop_proj, y_stop_proj, color='white', edgecolor=route_color, zorder=2)

    # Add station labels
    if len(target_station_names) > 0:
        for x_stop_proj, y_stop_proj, name in zip(x_stop_proj, y_stop_proj, route_station_names):
            if name in target_station_names:
                plt.annotate(
                    name,
                    (x_stop_proj, y_stop_proj),
                    xytext=(5, 3),
                    textcoords='offset points',
                    fontsize=7
                )
    elif args.station_labels is not None:
        print("No station labels specified.")
        for x_stop_proj, y_stop_proj, name in zip(x_stop_proj, y_stop_proj, route_station_names):
            plt.annotate(
                name,
                (x_stop_proj, y_stop_proj),
                xytext=(5, 3),
                textcoords='offset points',
                fontsize=7
            )

# Get location of trips between specified times
date_string = ''.join(simulation_date.split('-'))
start_datetime = simulation_date + ' ' + simulation_start_time
end_datetime = simulation_date + ' ' + simulation_end_time
rng = pd.date_range(start=start_datetime, end=end_datetime, freq='30s')
times = [t.strftime('%H:%M:%S') for t in rng]

loc = moving_feed.locate_trips(date_string, times)
filtered_route_loc = loc[loc['route_id'].isin(route_ids)].sort_values('time', ascending=True).copy()

# Check that there will be route information to animate
if len(filtered_route_loc) == 0:
    raise Exception("No frames to animate. Length of filtered_route_loc is zero.")

trip_positions = [] # list of dicts: {route_id: (lons, lats)}

# Get coordinates for trips within the simulation time range
for time in times:
    matching_rows = filtered_route_loc[filtered_route_loc['time'] == time]
    
    if not matching_rows.empty:
        frame_data = {}
        for route_id, group in matching_rows.groupby("route_id"):
            frame_data[route_id] = (
                group["lon"].tolist(),
                group["lat"].tolist()
            )

        trip_positions.append(frame_data)
    else:
        # TODO: Insert a placeholder value if there is no trip info for that time
        continue

if args.title:
    plot_title = ' '.join(args.title)
else:
    plot_title = "Transit Simulator"

plt.title(plot_title, fontsize=18, loc='left', color='royalblue', style='italic')
plt.title('                    created by moshobo', fontsize=10, loc='center', color="k")

# TODO: Keep this near where GTFS is loaded.
route_colors = {
    route.route_id: f"#{route.route_color}"
    for route in feed.routes.itertuples()
}

animated_plots = {}

for route_id in route_ids:
    animated_plots[route_id], = transit_map.plot(
        [],
        [],
        latlon=True,
        marker='s',
        linestyle='None',
        color=routes[route_id]["route_color"],
        zorder=8,
        label=route_id
    )

ani = animation.FuncAnimation(
    fig=plt.gcf(),
    func=update_data,
    frames=len(trip_positions),
    interval=100,
    repeat=True,
    repeat_delay=1000
)

title_routes = '_'.join(route_ids)
ani.save(f"output/{title_routes}_{simulation_date}.gif") # Save animation as a gif
plt.show()