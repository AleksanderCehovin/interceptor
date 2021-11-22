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

class Receiver(Thread):
    def __init__(self, parent):
        Thread.__init__(self)
        self.parent = parent
        self.stop = False
        self.all_info = []
        self.bookmark = 0

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

                data = {
                    "run_no": run_no,
                    "frame_idx": frame_idx,
                    "n_spots": results[0],
                    "hres": results[3],
                    "quality": results[2],
                }
                # mark frame if indexed
                sg = results[6]
                data["indexed"] = data["n_spots"] if sg != "NA" else np.nan
                if data:
                    self.all_info.append(data)

        # Once loop exits, disconnect socket
        print("DISCONNECTING...")
        self.collector.close()

    def onUITimer(self, e):
        start = self.bookmark
        end = len(self.all_info) - 1

        if start < end:
            # doing it this way because self.all_info is being appended at up to
            # 100Hz, or faster. Thus, setting a hard end so that no information is
            # plotted twice or missed
            info = copy.deepcopy(self.all_info[start:end])
            self.send_to_gui(info=info)
            self.bookmark = end

            if end > 5000:
                #Release memory
                print("Release memory")
                self.all_info = []
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
