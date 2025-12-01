# Transit-Simulator
Python code for simulating transit lines based on [General Transit Feed Specification (GTFS)](https://gtfs.org/) data.

![100479_2LINE_2024-12-25](https://github.com/user-attachments/assets/805ca97f-7af6-4cbd-8e2f-ce5bd6a3e9f9)

## Inspiration
This project is inspired by @QuadMet on Twitter/X who [created an animation of Portland, OR transit vehicles](https://twitter.com/quadmet/status/1768852830012805455?s=12&t=UdCSxpmnsn74xbyL8_LL1A) based off of GTFS data. They used the ['GTFS Map Generator'](https://gist.github.com/dfsnow/6cef8184ed0dbccadc0cd56a0d22b8be) from Dan Snow (checkout some [simulations](https://sno.ws/writing/2021/03/03/creating-moving-transit-maps-with-r-and-gtfs-feeds/) of their the Chicago L Trains). However, that code was in R, and I don't know R, so I decided to redo it all in Python.

# Usage

## Example Usage
Here is an example of how to generate a transit simulation for Sound Transit's 1 Line at 8am on Dec 25, 2024.

`python3 main.py -u https://www.soundtransit.org/GTFS-rail/40_gtfs.zip -d 2024-12-25 -s 08:00:00 -r 100479 2LINE -t Foobar`

## Command Line Arguments
The following flags can be passed when using the command line:

`-f`, `--file` - Specify a GTFS ZIP file to use. File should be in the `/data/gtfs-data` folder<br />
`-u`, `--url` - Specify a URL to get a GTFS ZIP file.<br />
`-d`, `--date` - Specify the start date of the simulation in YYYY-MM-DD format.<br />
`-s`, `--start-time` - Specify the start time of the simulation in hh:mm:ss format. The timezone used is that of the transit agency specified in the GTFS feed.<br />
`-e`, `--end-time` - Specify the end time of the simulation in hh:mm:ss format. The timezone used is that of the transit agency specified in the GTFS feed.<br />
`-r`, `--routes` - Declare which Route IDs should be displayed in the simulation.<br />
`t`, `--title` - The name to be used on the output GIF file.
`--station-labels` - When specificed, shows station labels for all stations.

# Examples

## MBTA Red Line - Boston, MA
![Red_2024-09-30](https://github.com/user-attachments/assets/02a0bd4b-2328-4cb9-9a01-4482330557e8)

## LA Metro A, C, and K Lines - Los Angeles, CA
`python3 main.py -u https://gitlab.com/LACMTA/gtfs_rail/raw/master/gtfs_rail.zip -d 2024-12-25 -s 08:00:00 -r 807 803 801 -t LA Metro`
![807_803_801_2024-12-25](https://github.com/user-attachments/assets/f4bc3f24-7256-40ba-b385-4f74ccaab53b)

# FAQs

## How does it work?
Most of the heavy lifting is being done by [gtfs_kit](https://github.com/mrcagney/gtfs_kit), which take in GTFS feed data and allows you to query it in a number of ways. The most important part of this is `feed.locate_trips()`, which is able to figure out where transit vehicles are at a given point in time.

Matplotlib's `FuncAnimation` is then used to animate the vehicles over an array of times

## Where can I get GTFS data?
Most transit agencies will make their GTFS data availble for public download, so just try searching for "<city name> GTFS data". As an example, Sound Transit provides GTFS data for most transit agencies in the Seattle area [on their website](https://www.soundtransit.org/help-contacts/business-information/open-transit-data-otd/otd-downloads)
