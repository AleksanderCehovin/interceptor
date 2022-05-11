# Interceptor: Experimental Fork

[![PyPI release](https://img.shields.io/pypi/v/intxr.svg)](https://pypi.org/project/intxr/)
![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)


## Fork Description

This is an Interceptor,  https://github.com/ssrl-px/interceptor,  fork for experimental modifications. The purpose is to adapt the code for Max IV,  www.maxiv.lu.se, purposes. 

In this project, the GUI part has been isolated and adapted to present Dozor spotfinding quality metrics. Much has been
removed from the original code, and this repository is much easier to install in a Conda environment. There are no more depencies on DIALS.
The simulator/ directory contains python scripts that can be used to feed the GUI with fake test data for standalone
evaluation and debugging. 

Some notes on the code:

- GUI modified for Dozor spotfinding metrics (number of spots, quality, and resolution)
- The update frequency of the graphics is intentionally set at 1 Hz (configurable). From what I undertand the ZMQ data collection loop and the GUI shares the same thread, so it is important to avoid starving the execution with excessive GUI updates. To improve refresh rates, probably a dual process design with an inter-process queue is a relatively simple solution. 
- If a run tab collects large amount of points, the plot will only show the last 25k points in a moving windows. This is configurable.
- The hitrate and thresholding can be done on either quality or resolution metrics. Use the "hve (resolution)" and "hve (quality)" beamline tabs to evaluate this.
- There is a callback function implemented triggered by clicking a point in the first subplot. This could be used to view image details in an external program. The ADXV viewer, https://www.scripps.edu/tainer/arvai/adxv/adxv_1.9.10/AdxvUserManual_v1.1.pdf , fits this use-case. The manual describes a socket interface, which is a way to integrate a viewer already well-known to users.
- In some scenarios many tabs can be created. The "Clear Tabs" button removes all but the active tab.

aleksander.cehovin@maxiv.lu.se

# Example Images

Example from datacollection at Biomax Max IV by Monika Bjelcic

![Example of real datacollection](doc/images/fig_1.png)



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

### Simulation Data Examples

Test data with GUI using quality for hit rate calculations

![Simulation with quality threshold](doc/images/test_gui_quality.png)


Test data with GUI using resolution for hit rate calculations

![Simulation with resolutin threshold](doc/images/test_gui_resolution.png)