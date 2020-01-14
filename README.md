# CHANCE Water Distribution Network Web App

[![Build Status](https://travis-ci.com/alan-turing-institute/chance-water-distribution.svg?branch=master)](https://travis-ci.com/alan-turing-institute/chance-water-distribution)

A web app to visualise the spread of pollution through water networks.

This work is part of the [Coupled human and natural critical ecosystems (CHANCE) project](https://www.turing.ac.uk/research/research-projects/coupled-human-and-natural-critical-ecosystems-chance)

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
