Water network data
=======

The examples directory contains a set of example water networks with pollution scenarios produced by simulation with [WNTR](https://github.com/USEPA/WNTR).

The example networks are taken from the [Water Distribution System Research Database](http://www.uky.edu/WDST/database.html) and use the same naming convention.

Loading new networks and pollution data
-------

You can follow these modified instructions to load a custom water network with pollution timeseries node data similar to the examples.

1. Clone the repository: `git clone https://github.com/alan-turing-institute/chance-water-distribution`
2. Install the python requirements: `pip install -r requirements.txt`
3. If you want to include the example networks, download the data modules: `git submodule update --init --recursive`
4. **Include a new subdirectory within `chance-water-distribution/water/data` with the files specified below (e.g. called custom_network)**
5. Run flask server from top dir of the repo: `python water/main.py`
6. Open http://localhost:8000 in a browser

### Custom network directory structure

The directory structure must follow those of the examples which is as follows:

```
custom_network
│   custom_network.inp
|   metadata.yml
│
└───custom_network
│   │   J-1.pkl
│   │   J-2.pkl
|   |   ...

```

1. The `.inp` file is an [EPANET INP file, used by the wntr python package to build a water network model](https://wntr.readthedocs.io/en/latest/waternetworkmodel.html).
2. For each node in the network that you want to show pollution spread starting from, add a pollution file with a simulation of pollution spread from that node. The file should be a `.pkl` of a pandas dataframe containing pollution concentration for each node at each timestep for a 24hr period.
3. *Optionally* add a file called `metadata.yml`. This should contain offset values for the graph network node coordinates that convert these to the actual latitude and longitude (see the example `ky2`). When this is included, the network is placed over a map.

You can add multiple subdirectories to `water/data` if you have more than one network to display. They can be switched between with the "Network" widget in the top left corner of the flask/bokeh app.
