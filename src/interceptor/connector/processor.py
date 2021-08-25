from __future__ import absolute_import, division, print_function

"""
Author      : Lyubimov, A.Y.
Created     : 03/31/2020
Last Changed: 05/15/2020
Description : Streaming stills processor for live data analysis
"""

import copy
import time  # noqa: F401; keep around for testing

import numpy as np
"""
from cctbx import sgtbx
from iotbx import phil as ip

from dials.command_line.stills_process import Processor, phil_scope as dials_scope
from dials.command_line.refine_bravais_settings import (
    phil_scope as sg_scope,
    bravais_lattice_to_space_group_table,
)
from dials.algorithms.indexing.bravais_settings import (
    refined_settings_from_refined_triclinic,
)
from dials.algorithms.spot_finding import per_image_analysis
from dials.array_family import flex
from dxtbx.model.experiment_list import ExperimentListFactory

from cctbx import uctbx
from cctbx.miller import index_generator

from interceptor import packagefinder, read_config_file
from interceptor.format import FormatEigerStreamSSRL
from iota.components.iota_utils import Capturing
"""


class Processor:
    def __init__(self, params, composite_tag=None, rank=0):
        self.params = params
        self.composite_tag = composite_tag

        # The convention is to put %s in the phil parameter to add a tag to
        # each output datafile. Save the initial templates here.
        self.experiments_filename_template = params.output.experiments_filename
        self.strong_filename_template = params.output.strong_filename
        self.indexed_filename_template = params.output.indexed_filename
        self.refined_experiments_filename_template = (
            params.output.refined_experiments_filename
        )
        self.integrated_filename_template = params.output.integrated_filename
        self.integrated_experiments_filename_template = (
            params.output.integrated_experiments_filename
        )
        if params.dispatch.coset:
            self.coset_filename_template = params.output.coset_filename
            self.coset_experiments_filename_template = (
                params.output.coset_experiments_filename
            )

        debug_dir = os.path.join(params.output.output_dir, "debug")
        if not os.path.exists(debug_dir):
            try:
                os.makedirs(debug_dir)
            except OSError:
                pass  # due to multiprocessing, makedirs can sometimes fail
        assert os.path.exists(debug_dir)
        self.debug_file_path = os.path.join(debug_dir, "debug_%d.txt" % rank)
        write_newline = os.path.exists(self.debug_file_path)
        if write_newline:  # needed if the there was a crash
            self.debug_write("")


    def setup_filenames(self, tag):
        # before processing, set output paths according to the templates


    def debug_start(self, tag):
        pass

    def debug_write(self, string, state=None):
        pass

    def process_experiments(self, tag, experiments):
        pass

    def pre_process(self, experiments):
        """Add any pre-processing steps here"""
        pass

    def find_spots(self, experiments):
        pass

    def index(self, experiments, reflections):
        experiments = None
        indexed = None
        return experiments, indexed

    def refine(self, experiments, centroids):
        experiments = None
        centroids = None
        return experiments, centroids

    def integrate(self, experiments, indexed):
        intergrated = None
        return integrated

    def write_integration_pickles(self, integrated, experiments, callback=None):
        """
        Write a serialized python dictionary with integrated intensities and other information
        suitible for use by cxi.merge or prime.postrefine.
        @param integrated Reflection table with integrated intensities
        @param experiments Experiment list. One integration pickle for each experiment will be created.
        @param callback Deriving classes can use callback to make further modifications to the dictionary
        before it is serialized. Callback should be a function with this signature:
        def functionname(params, outfile, frame), where params is the phil scope, outfile is the path
        to the pickle that will be saved, and frame is the python dictionary to be serialized.
        """
        pass

    def process_reference(self, reference):
        """Load the reference spots."""
        reference = None
        rubbish = None
        return reference, rubbish

    def save_reflections(self, reflections, filename):
        """Save the reflections to file."""
        pass

    def finalize(self):
        """Perform any final operations"""
        pass



class FastProcessor(Processor):
    def __init__(
            self,
            run_mode='DEFAULT',
            configfile=None,
            test=False,
    ):
        self.processing_mode = 'spotfinding'
        self.test = test
        self.run_mode = run_mode



    def generate_params(self):
        return 0 , 0

    def print_params(self):
        print("\nParameters for this run: ")
        print("\n")

    def refine_bravais_settings(self, reflections, experiments):
        return 0

    def reindex(self, reflections, experiments, solution):
        return 0, 0

    def pg_and_reindex(self, indexed, experiments):
        return 0, 0

    def process(self, data, filename, info):
        return 0

    def run(self, data, filename, info):
        return self.process(data, filename, info)






def calculate_score(experiments, observed):
    pass



if __name__ == "__main__":
    proc = FastProcessor()
    proc.dials_phil.show()

# -- end
