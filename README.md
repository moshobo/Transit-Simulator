# Transit-Simulator
Python code for simulating transit lines based on GTFS data

![SNDR_EV_SNDR_TL_100479_2LINE_2024-08-07](https://github.com/user-attachments/assets/e9a8b57f-2f1a-46e3-aa8a-e1ac84f31454)

## Inspiration
This project is inspired by @QuadMet on Twitter/X who [created an animation of Portland, OR transit vehicles](https://twitter.com/quadmet/status/1768852830012805455?s=12&t=UdCSxpmnsn74xbyL8_LL1A) based off of GTFS data. They used the ['GTFS Map Generator'](https://gist.github.com/dfsnow/6cef8184ed0dbccadc0cd56a0d22b8be) from Dan Snow (checkout some [simulations](https://sno.ws/writing/2021/03/03/creating-moving-transit-maps-with-r-and-gtfs-feeds/) of their the Chicago L Trains). However, that code was in R, and I don't know R, so I decided to redo it all in Python.

# Usage

## Command Line Arguments
The following flags can be passed when using the command line:

`--file` - Specify a GTFS ZIP file to use.<br />
`--url` - Specify a URL to get a GTFS ZIP file.<br />
`--date` - Specify the start date of the simulation in YYYY-MM-DD format.<br />
`--start-time` - Specify the start time of the simulation in hh:mm:ss format. The timezone used is that of the transit agency specified in the GTFS feed.<br />
`--end-time` - Specify the end time of the simulation in hh:mm:ss format. The timezone used is that of the transit agency specified in the GTFS feed.<br />
`--routes` - Declare which Route IDs should be displayed in the simulation.<br />
`--title` - The name to be used on the output GIF file.

# FAQs

## How does it work?
Most of the heavy lifting is being done by [gtfs_kit](https://github.com/mrcagney/gtfs_kit), which take in GTFS feed data and allows you to query it in a number of ways. The most important part of this is `feed.locate_trips()`, which is able to figure out where transit vehicles are at a given point in time.

Matplotlib's `FuncAnimation` is then used to animate the vehicles over an array of times

## Where do I get GTFS data?
Most transit agencies will make their GTFS data availble for public download, so just try searching for "<city name> GTFS data". As an example, Sound Transit provides GTFS data for most transit agencies in the Seattle area [on their website](https://www.soundtransit.org/help-contacts/business-information/open-transit-data-otd/otd-downloads)
