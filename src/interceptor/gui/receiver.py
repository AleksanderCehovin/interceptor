from __future__ import absolute_import, division, print_function

"""
Author      : Lyubimov, A.Y.
Created     : 03/31/2020
Last Changed: 03/31/2020
Description : ZMQ receiver module for Interceptor GUI
"""

import time
from threading import Thread
import zmq
import numpy as np
import wx
import copy

MONITOR_TOPIC_TOKEN = "gui"
# TODO: Use the config files to switch between ZMQ patterns
USE_PULL_PUSH = False

#Preallocate data dictionaries and avoid dynamic allocations
#Maybe this is exaggerated, but for now better safe than sorry on
#memory leaks.
SIZE_DATA_CACHE = 5000
RESET_SIZE = SIZE_DATA_CACHE - 1000


class Receiver(Thread):
    def __init__(self, parent):
        Thread.__init__(self)
        self.parent = parent
        self.stop = False
        #List of dictionaries acting as data cache. We preallocate
        #an array of data entries to avoid running this through
        #garbage collection.
        self.all_info = []
        #Cursor keeps track of where the most recent datapoint is in
        #self.all_info.
        self.all_info_cursor = 0
        #Bookmark keeps track of what part of the cache is yet to be
        #forwarded to the GUI.        
        self.bookmark = 0

        #Pre-allocation of data cache at object creation.
        for i in range(0,SIZE_DATA_CACHE):
            self.all_info.append({
            "run_no": "100",
            "frame_idx": "10000",
            "n_spots": "10000",
            "hres": "1.88",
            "quality": "33",
            "sample_string": "sample-prefix",
            "indexed": np.nan
            })

    def connect(self, host="localhost", port=7000):
        # Create socket and bind to same port as ZMQ Readers
        context = zmq.Context()
        url = "tcp://{}:{}".format(host, port)
        print("*** INTERCEPTOR CONNECTED TO {}".format(url))
        if USE_PULL_PUSH:
            self.collector = context.socket(zmq.PULL)
            self.collector.bind("tcp://*:{}".format(port))
        else:
            self.collector = context.socket(zmq.SUB)
            self.collector.connect(url)
            topic_token = MONITOR_TOPIC_TOKEN
            self.collector.setsockopt(zmq.SUBSCRIBE,topic_token.encode('utf-8'))


    def run(self):
        self.read_data()

    """
    This is the program main loop, to the best of my knowledge so far.
    The rest of the applications is executed by events, where the UI timer is the
    base clock, and trigger the onUITimer() callback.
    """
    def read_data(self):
        while self.stop is False:
            try:
                data_string = self.collector.recv_string(flags=zmq.NOBLOCK)
                if not USE_PULL_PUSH:
                    data_string = data_string[(len(MONITOR_TOPIC_TOKEN)+1):]
            except Exception as exp:
                time.sleep(1)
            else:
                run_no = data_string.split('run ')[1].split(' frame')[0]
                frame_idx = data_string.split('frame ')[1].split(' result')[0]
                result_string = data_string.split('result ')[1].split(' mapping')[0]
                results = result_string[1:-1].split()
                sample_string = data_string.split('result ')[1].split(' mapping')[1]

                data = {
                    "run_no": run_no,
                    "frame_idx": frame_idx,
                    "n_spots": results[0],
                    "hres": results[3],
                    "quality": results[2],
                    "sample_string": sample_string,
                    "indexed": np.nan
                }
                # mark frame if indexed
                sg = results[6]
                data["indexed"] = data["n_spots"] if sg != "NA" else np.nan
                if data:
                    for key in data.keys():
                        self.all_info[self.all_info_cursor][key]=data[key]
                    if self.all_info_cursor < SIZE_DATA_CACHE - 1:
                        self.all_info_cursor += 1
                    else:
                        self.all_info_cursor = 0

        # Once loop exits, disconnect socket
        print("DISCONNECTING...")
        self.collector.close()


    """
    Timer triggered callback function. Collects the data received by the typically much
    faster loop in read_data.
    """
    def onUITimer(self, e):
        start = self.bookmark
        #end = len(self.all_info) - 1 Old implementation
        end = self.all_info_cursor 

        if start < end:
            # doing it this way because self.all_info is being appended at up to
            # 100Hz, or faster. Thus, setting a hard end so that no information is
            # plotted twice or missed
            info = self.all_info[start:end]
            self.send_to_gui(info=info)
            self.bookmark = end

            if end > RESET_SIZE:
                #Re-use or release memory
                #print("Re-use memory, start {}, end {}".format(start,end))
                #Mark old data just in case old points enter by accident. 
                for i in range(0,start-1):
                    self.all_info[i]['run_no'] = "100"
                #self.all_info = [] Old implementation
                self.all_info_cursor = 0
                self.bookmark = 0

    def send_to_gui(self, info):
        evt = SpotFinderOneDone(tp_EVT_SPFDONE, -1, info=info)
        wx.PostEvent(self.parent, evt)

    def close_socket(self):
        self.stop = True


tp_EVT_SPFDONE = wx.NewEventType()
EVT_SPFDONE = wx.PyEventBinder(tp_EVT_SPFDONE, 1)


class SpotFinderOneDone(wx.PyCommandEvent):
    """ Send event when finished all cycles  """

    def __init__(self, etype, eid, info=None):
        wx.PyCommandEvent.__init__(self, etype, eid)
        self.info = info

    def GetValue(self):
        return self.info
