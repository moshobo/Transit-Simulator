# Transit-Simulator
Python code for simulating transit lines based on GTFS data

![lightrail_2024-04-27](https://github.com/moshobo/Transit-Simulator/assets/52591849/4c9e79bf-a73a-46db-9883-ecd77703e6da)

## Inspiration
This project is inspired by @QuadMet on Twitter/X who [created an animation of Portland, OR transit vehicles](https://twitter.com/quadmet/status/1768852830012805455?s=12&t=UdCSxpmnsn74xbyL8_LL1A) based off of GTFS data. However, their code was in R, and I don't know R, so I decided to redo it all in Python.

## How it works
Most of the heavy lifting is being done by [gtfs_kit](https://github.com/mrcagney/gtfs_kit), which take in GTFS feed data and allows you to query it in a number of ways. The most important part of this is `feed.locate_trips()`, which is able to figure out where transit vehicles are at a given point in time.

Matplotlib's `FuncAnimation` is then used to animate the vehicles over an array of times

## Where do I get GTFS data?
Most transite agencies will make their GTFS data availble for public download, so just try searching for "<city name> GTFS data". As an example, Sound Transit provides GTFS data for most transit agencies in the Seattle area [on their website](https://www.soundtransit.org/help-contacts/business-information/open-transit-data-otd/otd-downloads)
