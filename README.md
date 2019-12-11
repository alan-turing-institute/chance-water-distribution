# CHANCE project REG contribution

Hut23 Project issue: https://github.com/alan-turing-institute/Hut23/issues/34

## Water Distribution Network Web App

Task is to develop a web app that can load a water distribution network and simulate the spread of contamination/pollution through the network over time.

The purpose of the app is engagement and the information displayed should satisfy stakeholders including:

- Water operators
- Pollution sensor companies
- The national infrastructure commission

It should strike a balance between providing some useful information about contamination and maximising engagement through looking nice!

### Data

The data for contamination spread scenarios is pre-computed and coupled with information on (water) demand for network nodes (reservoirs, tanks and junctions), as well as diameter and lengths of the edges (pipes).

### Primary Features

1. Visual representation of the water network(s)
2. Animation of contamination spread through the network with visual cues for things like water demand and contamination concentration as they change in the nodes and edges
3. Ability to trigger a contamination spread via clicking a given node

### Secondary Features

1. Visualization of Weisi/Alessio's Neural Network's decision making process for reducing a water network to a set of critical nodes
2. A version of the app that water networks can input their own water networks and contamination scenario data to, by uploading files in a format specified by the app

## Run the App Locally

*Tested with Python 3.6 and 3.7*

1. Clone the repository: `git clone https://github.com/alan-turing-institute/chance-water-distribution`
2. Install the python requirements: `pip install -r requirements.txt`
3. Download data modules: `git submodule update --init --recursive`
4. Run bokeh server from top dir of the repo: `bokeh serve --show water`
5. The app should open in a browser window, otherwise navigate to http://localhost:5006

## Docker Container

1. Pull from Docker Hub: `docker pull turinginst/chance-water:no-flask`
2. Run the container `docker run -p 5006:5006 turinginst/chance-water:no-flask`
3. Open http://localhost:5006 in a browser

The image is [hosted on DockerHub](https://hub.docker.com/repository/docker/turinginst/chance-water/general) and is set to build from pushes to the master branch of this repo.

## [Adding custom water networks](water/data)

## [Deploying the App](ansible/)
