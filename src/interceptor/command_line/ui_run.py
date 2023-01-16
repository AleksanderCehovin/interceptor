from __future__ import absolute_import, division, print_function

"""
Author      : Lyubimov, A.Y.
Created     : 03/06/2020
Last Changed: 03/06/2020
Description : Interceptor module
"""

import wx
from interceptor.gui.tracker import TrackerWindow
from interceptor import __version__ as intxr_version
#from iota import iota_version


class MainApp(wx.App):
    """ App for the main GUI window  """
    def __init__(self, use_extended_gui=False):
        #Important to define all needed class attributes before
        #call to App.__init__, which will call OnInit. 
        self.use_extended_gui = use_extended_gui
        wx.App.__init__(self,False)

    def OnInit(self):
        intx_version = "0.000.00"
        self.frame = TrackerWindow(
            None, -1, title="MAXIV MX DOZOR INTERCEPTOR v.{}" "".format(intxr_version), use_extended_gui=self.use_extended_gui
        )
        self.frame.SetMinSize(self.frame.GetEffectiveMinSize())
        self.frame.SetPosition((150, 150))
        self.frame.Show(True)
        self.frame.Layout()
        self.SetTopWindow(self.frame)
        return True


def entry_point(use_extended_gui=False):
    import platform
    from matplotlib import __version__ as mpl_v
    from zmq import zmq_version as zmq_v, pyzmq_version as pyzmq_v

    print("~~~ Interceptor ~~~")
    print("Versions: ")
    print("  Interceptor : ", format(intxr_version))
    #print("  IOTA        : ", format(iota_version))

    print("Python Package Versions:")
    print("  Python      : ", platform.python_version())
    print("  wxPython    : ", wx.__version__)
    print("  MatPlotLib  : ", mpl_v)
    print("  ZMQ         : ", zmq_v())
    print("  PyZMQ       : ", pyzmq_v())

    app = MainApp(use_extended_gui=use_extended_gui)
    app.MainLoop()

def extended_entry_point():
    entry_point(use_extended_gui=True)

if __name__ == "__main__":
    entry_point()

# -- end
