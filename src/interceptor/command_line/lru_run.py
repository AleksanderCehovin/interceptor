from __future__ import absolute_import, division, print_function

"""
Author      : Lyubimov, A.Y.
Created     : 05/06/2020
Last Changed: 05/06/2020
Description : Collector module
"""

from interceptor.connector import broker, reader, collector

def entry_point():
    try:
        from mpi4py import MPI
    except ImportError as ie:
        comm_world = None
        print("DEBUG: MPI NOT LOADED! {}".format(ie))
    else:
        comm_world = MPI.COMM_WORLD
    if comm_world is not None:
        comm_world = MPI.COMM_WORLD
        rank = comm_world.Get_rank()
        if rank == 0:
            script = broker
        elif rank == 1:
            script = collector
        else:
            script = reader
        comm_world.barrier()

        localhost = MPI.Get_processor_name()
        script.entry_point(localhost=localhost)


if __name__ == "__main__":
    entry_point()

# -- end
