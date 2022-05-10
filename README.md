# Interceptor: Experimental Fork

[![PyPI release](https://img.shields.io/pypi/v/intxr.svg)](https://pypi.org/project/intxr/)
![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)


## Fork Description

This is an Interceptor,  https://github.com/ssrl-px/interceptor,  fork for experimental modifications. The purpose is to adapt the code for Max IV,  www.maxiv.lu.se, purposes. 

It would be interesting to

- Keep the original functionality intact
- Modify the package for the possiblility  stand-alone installation
- Add possibility to use Dozor spotfinding. The Dozor source is not completely public, but the python bindings to a compiled binary should be ok to publish. For evaluation purposes one could use a mockup Dozor binary to demonstrate the concept. 
- Modify the test GUI for presentation of Dozor image quality indicators. 
- Test if it is feasible to forward collected spot coordinates to the ADXV viewer, https://www.scripps.edu/tainer/arvai/adxv/adxv_1.9.10/AdxvUserManual_v1.1.pdf . The manual describes a socket interface, which could be a way to integrate a viewer already well-known to users.

aleksander.cehovin@maxiv.lu.se


# Installing the decoupled GUI

Preliminary notes on simplified install of decoupled GUI

- Install miniconda with python 3.
- Create a conda environment, "interceptor_gui", for the install
> conda create --name interceptor_gui python=3.8
- Activate the clean environment
> conda activate interceptor_gui
- To speed-up the installation install the following packages with conda:
> conda install ipython

> conda install wxpython

> conda install matplotlib

- I believe these can be installed with pip too, but downloading conda binaries is faster.
- Finish by installing the decoupled interceptor GUI in the environment with

> python -m pip install ./interceptor

Here we assume the current directory is the root folder above the interceptor checkout one.

The interceptor GUI is now available as "intxr.gui"


## Simulator

There is a simulation folder where two simple scripts can be used to generate the data-stream
the interceptor GUI relies upon as data input.

