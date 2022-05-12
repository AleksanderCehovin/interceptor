from __future__ import absolute_import, division, print_function

"""
Author      : Lyubimov, A.Y.
Created     : 03/31/2020
Last Changed: 03/31/2020
Description : Interceptor tracking module (GUI elements)
"""

import numpy as np
import wx
import copy
import time

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.widgets import SpanSelector

#from iota.components.gui import controls as ct
from interceptor.gui import controls as ct
from interceptor.gui import receiver as rcv, find_icon
from interceptor import packagefinder

blconfig = packagefinder('beamlines.cfg', 'connector', read_config=True)
uiconfig = packagefinder('ui.cfg', 'connector', read_config=True)

icon_cache = {}

itx_EVT_ZOOM = wx.NewEventType()
EVT_ZOOM = wx.PyEventBinder(itx_EVT_ZOOM, 1)

#For very long measurements, a single run can collect hundreds of
#thousands frames. In this case, the GUI will show a moving window
#of data determined by RESIZE_WINDOW. The data window will move in
#steps of MOVING_WINDOW_STEP_SIZE
RESIZE_WINDOW = 30000
MOVING_WINDOW_STEP_SIZE = 5000

#Maximum length of tab string name.
MAX_TAB_TEXT_LENGTH = 30

#UI Timer Period [ms]
#Determines the maximum update frequency of the UI. This must always
#be larger than the update execution time. If not, I think event are
#starting to stack up, the GUI slows down, and eventually there is a
#stack overflow.
UI_TIMER_PERIOD_MS = 1000


class EvtChartZoom(wx.PyCommandEvent):
    """ Send event when any zoom event happens  """

    def __init__(self, etype, eid, info):
        wx.PyCommandEvent.__init__(self, etype, eid)
        self.info = info

    def GetInfo(self):
        return self.info


class ZoomCtrl(ct.CtrlBase):
    def __init__(self, parent, main_window):
        self.parent = parent
        self.main_window = main_window
        self.tracker_panel = self.parent.GetParent()
        super(ZoomCtrl, self).__init__(parent)

        # Attributes
        self.move = 0
        self.chart_range = 100
        self.plot_zoom = False
        self.max_lock = False

        main_sizer = wx.GridBagSizer(5, 5)

        # Zoom checkbox
        btn_size = (32, 32)
        zoom_bmp = find_icon("zoom", size=24)
        self.btn_zoom = wx.BitmapToggleButton(self, label=zoom_bmp, size=btn_size)
        self.spn_zoom = ct.SpinCtrl(
            self, ctrl_size=(100, -1), ctrl_value=100, ctrl_min=10, ctrl_step=10
        )
        back_bmp = find_icon("back", size=24)
        self.btn_back = wx.BitmapButton(self, bitmap=back_bmp, size=btn_size)
        frwd_bmp = find_icon("forward", size=24)
        self.btn_frwd = wx.BitmapButton(self, bitmap=frwd_bmp, size=btn_size)
        xmax_bmp = find_icon("max", size=24)
        self.btn_lock = wx.BitmapToggleButton(self, label=xmax_bmp, size=btn_size)

        main_sizer.Add(self.btn_zoom, pos=(0, 0))
        main_sizer.Add(self.spn_zoom, flag=wx.ALIGN_CENTER_VERTICAL, pos=(0, 1))
        main_sizer.Add(self.btn_back, pos=(0, 2))
        main_sizer.Add(self.btn_frwd, pos=(0, 3))
        main_sizer.Add(self.btn_lock, pos=(0, 4))

        self.SetSizer(main_sizer)
        self.set_control()

        # button bindings
        self.btn_zoom.Bind(
            wx.EVT_TOGGLEBUTTON, self.onZoom,
        )
        self.spn_zoom.Bind(wx.EVT_SPINCTRL, self.onZoom)
        self.btn_back.Bind(wx.EVT_BUTTON, self.onBack)
        self.btn_frwd.Bind(wx.EVT_BUTTON, self.onFrwd)
        self.btn_lock.Bind(wx.EVT_TOGGLEBUTTON, self.onLock)

    def onZoom(self, e):
        self.plot_zoom = self.btn_zoom.GetValue()
        self.chart_range = self.spn_zoom.ctr.GetValue()
        self.max_lock = self.plot_zoom
        self.btn_lock.SetValue(self.plot_zoom)
        self.set_and_signal()

    def onBack(self, e):
        self.max_lock = False
        self.move = -(self.chart_range / 10)
        self.set_and_signal()

    def onFrwd(self, e):
        self.move = self.chart_range / 10
        self.set_and_signal()

    def onLock(self, e):
        self.max_lock = self.btn_lock.GetValue()
        self.move = -1
        self.set_and_signal()

    def set_zoom(self, plot_zoom=False, chart_range=None):
        self.btn_zoom.SetValue(state=plot_zoom)
        if chart_range:
            self.spn_zoom.ctr.SetValue(value=chart_range)

    def set_control(self, max_lock=None, plot_zoom=None, chart_range=None):
        for arg, value in locals().items():
            if arg != "self" and value is not None:
                setattr(self, arg, value)

        # change control settings depending on situation
        self.btn_lock.SetValue(self.max_lock)
        self.btn_zoom.SetValue(self.plot_zoom)
        self.btn_lock.Enable(enable=self.plot_zoom)
        self.btn_back.Enable(enable=self.plot_zoom)
        self.spn_zoom.Enable(enable=self.plot_zoom)
        self.spn_zoom.ctr.SetValue(self.chart_range)
        if self.plot_zoom:
            self.btn_frwd.Enable(enable=not self.max_lock)
        else:
            self.btn_frwd.Enable(False)

    def set_and_signal(self):
        self.set_control()
        info = {
            "move": self.move,
            "max_lock": self.max_lock,
            "chart_range": self.chart_range,
            "plot_zoom": self.plot_zoom,
        }
        evt = EvtChartZoom(itx_EVT_ZOOM, -1, info)
        wx.PostEvent(self.tracker_panel.chart, evt)
        self.move_cache = []


class TrackStatusBar(wx.StatusBar):
    def __init__(self, parent):
        wx.StatusBar.__init__(self, parent)

        self.SetFieldsCount(2)
        self.sizeChanged = False
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_IDLE, self.OnIdle)

        bmp = find_icon("disconnected", library="custom")
        self.conn_icon = wx.StaticBitmap(self, bitmap=bmp)

        icon_width = self.conn_icon.GetSize()[0] + 10
        self.SetStatusWidths([icon_width, -1])
        self.SetStatusBitmap()

    def OnSize(self, e):
        e.Skip()
        self.position_icon()
        self.sizeChanged = True

    def OnIdle(self, e):
        if self.sizeChanged:
            self.position_icon()

    def SetStatusBitmap(self, connected=False):
        if connected:
            bmp = find_icon("connected", library="custom")
        else:
            bmp = find_icon("disconnected", library="custom")
        self.conn_icon.SetBitmap(bmp)
        self.position_icon()

    def position_icon(self):
        rect1 = self.GetFieldRect(0)
        rect1.x += 1
        rect1.y += 1
        self.conn_icon.SetRect(rect1)
        self.sizeChanged = False

#Utility
def set_subplot_labels(subplot_instance,xlabel,ylabel,doClear=False):
    if doClear:
        subplot_instance.clear()
    subplot_instance.set_ylabel(ylabel)
    if xlabel is not None:
        subplot_instance.set_xlabel(xlabel)

#Utility
def clear_subplots(subplot_instance):
    subplot_instance.clear()
    subplot_instance.patch.set_visible(False)

class TrackChart(wx.Panel):
    def __init__(self, parent, main_window, use_resolution=False):
        wx.Panel.__init__(self, parent, size=(100, 100))
        self.main_window = main_window
        self.parent = parent
        self.zoom_ctrl = self.parent.GetParent().chart_zoom
        self.use_resolution = use_resolution

        #Keep track of first time draw event        
        self.first_time_draw = True

        self.main_box = wx.StaticBox(self, label="Dozor Spotfinding Chart")
        self.main_fig_sizer = wx.StaticBoxSizer(self.main_box, wx.VERTICAL)
        self.SetSizer(self.main_fig_sizer)

        self.resize_counter = 0 # ALEK
        self.track_figure = Figure()
        self.track_axes = {}

        #Presentation depends on whether thresholding and hitrate is based 
        #on Dozor quality metric or resolution
        if self.use_resolution:
            self.track_axes['resolution'] = self.track_figure.add_subplot(311)                        
            self.track_axes['quality'] = self.track_figure.add_subplot(312)        
            self.track_axes['spots'] = self.track_figure.add_subplot(313)
            set_subplot_labels(self.track_axes['resolution'],None,"Resolution [Å]")        
            set_subplot_labels(self.track_axes['spots'],"Frame","Found Spots")
        else:
            self.track_axes['quality'] = self.track_figure.add_subplot(311)            
            self.track_axes['spots'] = self.track_figure.add_subplot(312)
            self.track_axes['resolution'] = self.track_figure.add_subplot(313)        
            set_subplot_labels(self.track_axes['resolution'],"Frame","Resolution [Å]")        
            set_subplot_labels(self.track_axes['spots'],None,"Found Spots")                    

        set_subplot_labels(self.track_axes['quality'],None,"Quality")

        self.track_figure.set_tight_layout(True)
        self.track_canvas = FigureCanvas(self, -1, self.track_figure)
        self.track_axes['spots'].patch.set_visible(False)
        self.track_axes['quality'].patch.set_visible(False)
        self.track_axes['resolution'].patch.set_visible(False)

        self.plot_sb = wx.ScrollBar(self)
        self.plot_sb.Hide()

        self.main_fig_sizer.Add(self.track_canvas, 1, wx.EXPAND)
        self.main_fig_sizer.Add(self.plot_sb, flag=wx.EXPAND)

        # Scroll bar binding
        self.Bind(wx.EVT_SCROLL, self.onScroll, self.plot_sb)

        # Zoom control binding
        self.Bind(EVT_ZOOM, self.onZoomControl)

        # Plot bindings
        self.track_figure.canvas.mpl_connect("button_press_event", self.onPress)
        self.track_figure.canvas.mpl_connect("pick_event",self.onPick)

        # initialize chart
        self.reset_chart()

        # Draw initial state
        self._update_canvas(canvas=self.track_canvas)


    def onSelect(self, xmin, xmax):
        """ Called when SpanSelector is used (i.e. click-drag-release) """

        if int(xmax) - int(xmin) >= 5:
            self.x_min = int(xmin)
            self.x_max = int(xmax)
            self.plot_zoom = True
            self.max_lock = False
            self.chart_range = int(self.x_max - self.x_min)
            sb_center = self.x_min + self.chart_range / 2

            self.plot_sb.SetScrollbar(
                position=sb_center,
                thumbSize=self.chart_range,
                range=np.max(self.xdata),
                pageSize=self.chart_range,
            )
            self.plot_sb.Show()
            self.zoom_ctrl.set_control(
                max_lock=False, plot_zoom=True, chart_range=self.chart_range
            )
            self.draw_plot()

    def onZoomControl(self, e):
        zoom_dict = e.GetInfo()
        self.max_lock = zoom_dict["max_lock"]
        self.plot_zoom = zoom_dict["plot_zoom"]
        self.chart_range = zoom_dict["chart_range"]
        self.x_max += zoom_dict["move"]
        self.x_min += zoom_dict["move"]

        try:
            assert self.chart_range == int(self.x_max - self.x_min)
        except AssertionError:
            self.x_min = int(self.x_max - self.chart_range)

        if self.plot_zoom is False:
            self.plot_sb.Hide()
        else:
            self.plot_sb.Show()
            sb_center = self.x_min + self.chart_range / 2
            range = np.max(self.xdata) if self.xdata.size else self.chart_range
            self.plot_sb.SetScrollbar(
                position=sb_center,
                thumbSize=self.chart_range,
                range=range,
                pageSize=self.chart_range,
            )
        self.draw_plot()

    def onScroll(self, e):
        sb_center = self.plot_sb.GetThumbPosition()
        half_span = (self.x_max - self.x_min) / 2
        if sb_center - half_span == 0:
            self.x_min = 0
            self.x_max = half_span * 2
        else:
            self.x_min = sb_center - half_span
            self.x_max = sb_center + half_span

        if (
            self.plot_sb.GetThumbPosition()
            >= self.plot_sb.GetRange() - self.plot_sb.GetThumbSize()
        ):
            self.max_lock = True
        else:
            self.max_lock = False
        self.draw_plot()

    def onPress(self, e):
        """ If left mouse button is pressed, activates the SpanSelector;
    otherwise, makes the span invisible """
        if e.button != 1:
            self.zoom_span.set_visible(False)
            self.bracket_set = False
            self.plot_zoom = False
            self.plot_sb.Hide()
            self.zoom_ctrl.set_control(
                max_lock=False, plot_zoom=False,
            )
            self.draw_plot()
        else:
            self.zoom_span.set_visible(True)

    def onPick(self, e):
        """ Execute action when a point is clicked """
        #TODO: Set up a ZMQ socket to DataHandler and request a plot remotely.
        line = e.artist 
        xdata, ydata = line.get_data()
        ind = e.ind
        print("OnPick: ({},{},{})\n".format(xdata[int(ind)],ydata[int(ind)],ind))

    def reset_chart(self):
        self.track_figure.patch.set_visible(False)
        clear_subplots(self.track_axes['spots'])
        clear_subplots(self.track_axes['quality'])
        clear_subplots(self.track_axes['resolution'])

        if self.use_resolution:
            set_subplot_labels(self.track_axes['resolution'],None,"Resolution [Å]")        
            set_subplot_labels(self.track_axes['quality'],None,"Dozor Quality")
            set_subplot_labels(self.track_axes['spots'],"Frame Number","Nb. of Spots")
        else:
            set_subplot_labels(self.track_axes['spots'],None,"Nb. of Spots")
            set_subplot_labels(self.track_axes['quality'],None,"Dozor Quality")
            set_subplot_labels(self.track_axes['resolution'],"Frame Number","Resolution [Å]")        

        self.xdata = np.array([]).astype(np.double)
        self.ydata = np.array([]).astype(np.double)
        self.idata = np.array([]).astype(np.double)
        self.rdata = []
        self.qdata = []
        self.sdata = []        
        self.x_min = 0
        self.x_max = 1
        self.y_max = 1
        self.bracket_set = False
        self.button_hold = False
        self.plot_zoom = False
        self.chart_range = None
        self.selector = None
        self.max_lock = True
        self.patch_x = 0
        self.patch_x_last = 1
        self.patch_width = 1
        self.start_edge = 0
        self.end_edge = 1

        self.acc_plot = {}
        self.rej_plot = {}
        
        if self.use_resolution:        
            LABEL_ONE = "resolution"
            LABEL_TWO = "quality"
            LABEL_THREE = "spots"
        else:
            LABEL_ONE = "quality"
            LABEL_TWO = "spots"
            LABEL_THREE = "resolution"            

        self.acc_plot[LABEL_ONE] = self.track_axes[LABEL_ONE].plot([], [], "o", color="#4575b4",picker=5)[0]
        self.rej_plot[LABEL_ONE] = self.track_axes[LABEL_ONE].plot([], [], "o", color="#d73027",picker=5)[0]
        self.acc_plot[LABEL_TWO] = self.track_axes[LABEL_TWO].plot([], [], "o", color="#4575b4")[0]
        self.acc_plot[LABEL_THREE] = self.track_axes[LABEL_THREE].plot([], [], "o", color="#4575b4")[0]

        self.idx_plot = self.track_axes[LABEL_ONE].plot([], [], "wo", ms=2)[0]
        self.bragg_line = self.track_axes[LABEL_ONE].axhline(0, c="#4575b4", ls=":", alpha=0)
        self.highlight = self.track_axes[LABEL_ONE].axvspan(
            0.5, 0.5, ls="--", alpha=0, fc="#deebf7", ec="#2171b5"
        )
        self.track_axes[LABEL_ONE].set_autoscaley_on(True)
        self.track_axes[LABEL_TWO].set_autoscaley_on(True)
        self.track_axes[LABEL_THREE].set_autoscaley_on(True)

        self.zoom_span = SpanSelector(
            ax=self.track_axes[LABEL_ONE],
            onselect=self.onSelect,
            direction="horizontal",
            rectprops=dict(alpha=0.5, ls=":", fc="#ffffd4", ec="#8c2d04"),
        )
        self.zoom_span.set_active(True)
        self._update_canvas(canvas=self.track_canvas)

    def draw_bragg_line(self,draw_plot=True):
        min_bragg = self.main_window.tracker_panel.min_bragg.ctr.GetValue()
        if min_bragg > 0:
            self.bragg_line.set_alpha(1)
        else:
            self.bragg_line.set_alpha(0)
        self.bragg_line.set_ydata(min_bragg)
        try:
            #If call is done in connection with a later draw_plot event,
            #there is an option to skip this draw_plot.
            if draw_plot:
                self.draw_plot()
        except AttributeError:
            pass

    def get_chart_data(self):
        #return  copy.deepcopy(list(zip(self.xdata, self.ydata, self.idata, self.rdata, self.qdata)))        
        return  list(zip(self.xdata, self.ydata , self.idata, self.rdata, self.qdata))        

    def draw_plot(
        self, new_data=None, new_res=None, new_x=None, new_y=None, new_i=None
    ):
        """ Draw plot from acquired data; called on every timer event or forced
        when the Bragg spot count cutoff line is moved, or when current run tab
        is clicked on
    :param new_data: a list of tuples containing (frame_idx, no_spots, hres)
    :param new_res: a list of resolutions (hres, deprecated)
    :param new_x: a list of x-values (frame_idx, deprecated)
    :param new_y: a list of y-values (no_spots, deprecated)
    :param new_i: a list of x-values for indexed frames
    """
        new_quality = None
        new_spots = None
        
        # get Bragg spots count cutoff line from UI widget
        min_bragg = self.main_window.tracker_panel.min_bragg.ctr.GetValue()
        if self.use_resolution:
            #Resolution thresholds are inverted
            min_bragg = 1/min_bragg

        # append new data (if available) to data lists
        if new_data:
            #new_x, new_quality, new_i, new_res, new_y = list(zip(*new_data))
            new_frame, new_spots, new_i, new_res, new_quality = list(zip(*new_data))
            if self.use_resolution:
                new_x = new_frame
                new_y = new_res
            else:
                new_x = new_frame
                new_y = new_quality                

        if new_x and new_y:
            new_x_arr = np.array(new_x).astype(np.double)
            nref_x = np.append(self.xdata, new_x_arr)
            self.xdata = nref_x
            new_y_arr = np.array(new_y).astype(np.double)
            if self.use_resolution:
                nref_y = np.append(self.ydata, 1./(0.01+new_y_arr) )
            else:
                nref_y = np.append(self.ydata, new_y_arr)
            self.ydata = nref_y
        else:
            nref_x = self.xdata
            nref_y = self.ydata

        #Needed when resolution is to be thresholded.
        if new_spots:
            new_spots_arr = np.array(new_spots).astype(np.double)
            self.sdata = np.append(self.sdata, new_spots_arr)

        if new_res:
            new_res_arr = np.array(new_res).astype(np.double)
            self.rdata = np.append(self.rdata, new_res_arr)

        if new_quality:
            new_quality_arr = np.array(new_quality).astype(np.double)
            self.qdata = np.append(self.qdata, new_quality_arr)

        if new_i:
            new_i_arr = np.array(new_i).astype(np.double)
            nref_i = np.append(self.idata, new_i_arr)
            self.idata = nref_i
        else:
            nref_i = self.idata

        nref_xy = list(zip(nref_x, nref_y))

        print("No. x-axis points: {}".format(self.xdata.shape[0]))
        if self.xdata.shape[0] > RESIZE_WINDOW:
            self.resize_counter += 1
            self.xdata = self.xdata[MOVING_WINDOW_STEP_SIZE:]
            self.ydata = self.ydata[MOVING_WINDOW_STEP_SIZE:]
            self.rdata = self.rdata[MOVING_WINDOW_STEP_SIZE:]
            self.sdata = self.sdata[MOVING_WINDOW_STEP_SIZE:]
            self.qdata = self.qdata[MOVING_WINDOW_STEP_SIZE:]
            self.idata = self.idata[MOVING_WINDOW_STEP_SIZE:]            
            nref_x = nref_x[MOVING_WINDOW_STEP_SIZE:]            
            nref_y = nref_y[MOVING_WINDOW_STEP_SIZE:]            
            nref_i = nref_i[MOVING_WINDOW_STEP_SIZE:]

            nref_xy = list(zip(nref_x, nref_y))            


        # identify plotted data boundaries
        if nref_x != [] and nref_y != []:
            if self.plot_zoom:
                if self.max_lock:
                    self.x_max = np.max(nref_x)
                    self.x_min = self.x_max - self.chart_range
                else:
                    if self.x_max >= np.max(nref_x):
                        self.x_max = np.max(nref_x)
                        self.max_lock = True
                    else:
                        self.max_lock = False
                    if self.x_min <= 0:
                        self.x_min = 0
            else:
                self.x_min = np.min(nref_x)
                self.x_max = np.max(nref_x) + 1

            if min_bragg > np.max(nref_y):
                self.y_max = min_bragg + int(0.1 * min_bragg)
            else: 
                self.y_max = np.max(nref_y) + int(0.1 * np.max(nref_y))

            self.track_axes['spots'].set_xlim(self.x_min, self.x_max)
            if self.use_resolution:
                self.track_axes['spots'].set_ylim(0, 1.1*self.sdata.max())
            else:
                self.track_axes['spots'].set_xticklabels([])
                self.track_axes['spots'].set_ylim(0, 1.1*self.sdata.max())
                #self.track_axes['spots'].set_ylim(0, self.y_max)

            self.track_axes['quality'].set_xlim(self.x_min,self.x_max)
            self.track_axes['quality'].set_xticklabels([])
            #Keep this way of setting y-limit, since we keep double books on quality data
            self.track_axes['quality'].set_ylim(0, 1.1*self.qdata.max())
            self.track_axes['resolution'].set_xlim(self.x_min,self.x_max)
            yticks = [0,0.1,0.25,0.5,0.8]
            ytick_labels = ["Inf","10","4","2","1.25"]
            self.track_axes['resolution'].set_yticks(yticks)
            self.track_axes['resolution'].set_yticklabels(ytick_labels)
            if self.use_resolution:
                self.track_axes['resolution'].set_xticklabels([])
            #if self.first_time_draw:
            is_y_grid_on = any([l.get_visible() for l in self.track_axes['resolution'].yaxis.get_gridlines()])
            if not is_y_grid_on:
                # Toggles horizontal help lines. Only need one call, but gets reset sometimes.
                self.track_axes['resolution'].yaxis.grid(which="major",color='k',linestyle=':',linewidth=1)             
            #Not clear why this bragg line set needs to be done in the resolution case, but the line is not
            #visible otherwise.
            if self.use_resolution:
                self.bragg_line.set_ydata(min_bragg)
            #self.track_axes['resolution'].set_ylim(0,1)
        else:
            self.x_min = -1
            self.x_max = 1

        # select results that are a) within the plotted boundaries and b) are above
        # (acc) or below (rej) the minimum found Bragg spots cutoff
        acc = [
            i for i in nref_xy if (self.x_min < i[0] < self.x_max and i[1] >= min_bragg)
        ]
        rej = [
            i for i in nref_xy if (self.x_min < i[0] < self.x_max and i[1] <= min_bragg)
        ]
        

        # exit if there's nothing to plot
        if not acc and not rej:
            return
        
        # split acc/rej lists into x and y lists
        """
        acc_x = [int(i[0]) for i in acc]
        acc_y = [int(i[1]) for i in acc]
        rej_x = [int(i[0]) for i in rej]
        rej_y = [int(i[1]) for i in rej]
        """
        acc_x = [int(i[0]) for i in acc]
        acc_y = [float(i[1]) for i in acc]
        rej_x = [int(i[0]) for i in rej]
        rej_y = [float(i[1]) for i in rej]        

        # update plot data
        
        if acc_x:
            if self.use_resolution:
                self.acc_plot['resolution'].set_xdata(acc_x)
                self.acc_plot['resolution'].set_ydata(acc_y)
            else:
                self.acc_plot['quality'].set_xdata(acc_x)
                self.acc_plot['quality'].set_ydata(acc_y)                            
        if rej_x:
            if self.use_resolution:
                self.rej_plot['resolution'].set_xdata(rej_x)
                self.rej_plot['resolution'].set_ydata(rej_y)
            else:
                self.rej_plot['quality'].set_xdata(rej_x)
                self.rej_plot['quality'].set_ydata(rej_y)                
        #Always update the other plots regardless of the 
        #thresholded populations above
        self.acc_plot['spots'].set_xdata(nref_x)
        self.acc_plot['spots'].set_ydata(self.sdata)
        if self.use_resolution:
            self.acc_plot['quality'].set_xdata(nref_x)
            self.acc_plot['quality'].set_ydata(self.qdata)
        else:
            self.acc_plot['resolution'].set_xdata(nref_x)
            #Add a small number in denominator to avoid potential divison by zero
            self.acc_plot['resolution'].set_ydata( 1./(0.01+self.rdata) )


        # plot indexed
        if new_i is not None:
            self.idx_plot.set_xdata(nref_x)
            self.idx_plot.set_ydata(nref_i)
            idx_count = "{}".format(len(nref_i[~np.isnan(nref_i)]))
            self.main_window.tracker_panel.idx_count_txt.SetLabel(idx_count)

        self.Layout()

        # update run stats
        # hit count
        count = "{}".format(len(acc))
        self.main_window.tracker_panel.count_txt.SetLabel(count)
        self.main_window.tracker_panel.info_sizer.Layout()

        # hit rate count
        if len(rej) == 0:
            count_rate = "{:.1f}".format(100)
        else:
            count_rate = "{:.1f}".format(100*len(acc)/(1.0*(len(acc)+len(rej))))        
        self.main_window.tracker_panel.count_rate_txt.SetLabel(count_rate)

        # indexed count
        idx_count = "{}".format(len(nref_i[~np.isnan(nref_i)]))
        self.main_window.tracker_panel.idx_count_txt.SetLabel(idx_count)

        # Median resolution
        median_res = np.median(self.rdata)
        res_label = "{:.2f} Å".format(median_res)
        self.main_window.tracker_panel.res_txt.SetLabel(res_label)

        # Test Sample Name
        sample_id = self.main_window.tracker_panel.sample_id
        run_no = self.main_window.tracker_panel.run_no
        self.main_window.tracker_panel.pg_txt.SetLabel(sample_id)
        self.main_window.tracker_panel.uc_txt.SetLabel(run_no)

        #Avoids bug related to first time draw.
        if self.first_time_draw:
            print("First Time Draw. Pre-updating Canvas.")
            self.first_time_draw = False
            self._update_canvas(self.track_canvas)

        # Draw extended plots
        if self.use_resolution:
            self.track_axes['resolution'].draw_artist(self.acc_plot['resolution'])
            self.track_axes['resolution'].draw_artist(self.rej_plot['resolution'])
            self.track_axes['quality'].draw_artist(self.acc_plot['quality'])
            self.track_axes['spots'].draw_artist(self.acc_plot['spots'])        
        else:
            self.track_axes['quality'].draw_artist(self.acc_plot['quality'])
            self.track_axes['quality'].draw_artist(self.rej_plot['quality'])
            self.track_axes['spots'].draw_artist(self.acc_plot['spots'])
            self.track_axes['resolution'].draw_artist(self.acc_plot['resolution'])            

        # If zoomed update navigation tools
        if self.chart_range:
            # Adjust scrollbar
            rng = np.max(self.xdata)
            pos = rng if self.max_lock else self.plot_sb.GetThumbPosition()
            self.plot_sb.SetScrollbar(
                position=pos,
                thumbSize=self.chart_range,
                range=rng,
                pageSize=self.chart_range,
            )

            # Update Zoom control
            self.zoom_ctrl.set_control(max_lock=self.max_lock,)

        # Redraw canvas
        self._update_canvas(self.track_canvas)
        

    def _update_canvas(self, canvas, draw_idle=True):
        """ Update a canvas (passed as arg)
    :param canvas: A canvas to be updated via draw_idle
    """
        # Draw_idle is useful for regular updating of the chart; straight-up draw
        # without flush_events() will have to be used when buttons are clicked to
        # avoid recursive calling of wxYield
        if draw_idle:
            canvas.draw_idle()
            try:
                canvas.flush_events()
            except (NotImplementedError, AssertionError):
                pass
        else:
            canvas.draw()
        canvas.Refresh()


class TrackerPanel(wx.Panel):
    def __init__(self, parent, main_window, run_number, use_resolution=False):
        wx.Panel.__init__(self, parent=parent)
        self.parent = parent
        self.main_window = main_window
        self.chart_sash_position = 0

        self.all_data = []
        self.new_data = []
        self.run_number = run_number
        self.use_resolution = use_resolution
        #Sample ID
        self.sample_id = "None"
        self.run_no = "1"

        self.main_sizer = wx.GridBagSizer(10, 10)

        # Status box
        self.info_panel = wx.Panel(self)
        self.info_sizer = wx.FlexGridSizer(1, 6, 0, 6)
        self.info_sizer.AddGrowableCol(4)
        self.info_panel.SetSizer(self.info_sizer)

        self.count_box = wx.StaticBox(self.info_panel, label="Hits")
        self.count_box_sizer = wx.StaticBoxSizer(self.count_box, wx.HORIZONTAL)
        self.count_txt = wx.StaticText(self.info_panel, label="")
        self.count_box_sizer.Add(
            self.count_txt, flag=wx.ALL | wx.ALIGN_CENTER, border=10
        )

        self.count_box_rate = wx.StaticBox(self.info_panel, label="Hit Rate [%]")
        self.rate_count_box_sizer = wx.StaticBoxSizer(self.count_box_rate, wx.HORIZONTAL)
        self.count_rate_txt = wx.StaticText(self.info_panel, label="")
        self.rate_count_box_sizer.Add(
            self.count_rate_txt, flag=wx.ALL | wx.ALIGN_CENTER, border=10
        )

        self.idx_count_box = wx.StaticBox(self.info_panel, label="Indexed")
        self.idx_count_box_sizer = wx.StaticBoxSizer(self.idx_count_box, wx.HORIZONTAL)
        self.idx_count_txt = wx.StaticText(self.info_panel, label="")
        self.idx_count_box_sizer.Add(
            self.idx_count_txt, flag=wx.ALL | wx.ALIGN_CENTER, border=10
        )

        self.res_box = wx.StaticBox(self.info_panel, label="Median Resolution")
        self.res_box_sizer = wx.StaticBoxSizer(self.res_box, wx.HORIZONTAL)
        self.res_txt = wx.StaticText(self.info_panel, label="")
        self.res_box_sizer.Add(self.res_txt, flag=wx.ALL | wx.ALIGN_CENTER, border=10)

        self.pg_box = wx.StaticBox(self.info_panel, label="Sample Label")
        self.pg_box_sizer = wx.StaticBoxSizer(self.pg_box, wx.HORIZONTAL)
        self.pg_txt = wx.StaticText(self.info_panel, label="")
        self.pg_box_sizer.Add(self.pg_txt, flag=wx.ALL | wx.ALIGN_CENTER, border=10)

        self.uc_box = wx.StaticBox(self.info_panel, label="Run Number")
        self.uc_box_sizer = wx.StaticBoxSizer(self.uc_box, wx.HORIZONTAL)
        self.uc_txt = wx.StaticText(self.info_panel, label="")
        self.uc_box_sizer.Add(self.uc_txt, flag=wx.ALL | wx.ALIGN_CENTER, border=10)

        font = wx.Font(18, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.count_txt.SetFont(font)
        self.count_rate_txt.SetFont(font)
        self.idx_count_txt.SetFont(font)
        self.res_txt.SetFont(font)
        font = wx.Font(16, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.pg_txt.SetFont(font)
        self.uc_txt.SetFont(font)

        self.info_sizer.Add(self.count_box_sizer, flag=wx.EXPAND)
        self.info_sizer.Add(self.rate_count_box_sizer, flag=wx.EXPAND)        
        self.info_sizer.Add(self.idx_count_box_sizer, flag=wx.EXPAND)
        self.info_sizer.Add(self.res_box_sizer, flag=wx.EXPAND)
        self.info_sizer.Add(self.pg_box_sizer, flag=wx.EXPAND)
        self.info_sizer.Add(self.uc_box_sizer, flag=wx.EXPAND)

        # Put in chart
        self.graph_panel = wx.Panel(self)
        self.graph_sizer = wx.GridBagSizer(5, 5)

        self.chart_zoom = ZoomCtrl(self.graph_panel, main_window)
        self.chart = TrackChart(self.graph_panel, main_window=self.main_window,
                                use_resolution=self.use_resolution)
        
        if self.use_resolution:            
            label_txt="Min. Resolution"            
            ctrl_value_int=4            
        else:
            label_txt="Min. Dzr Quality"
            ctrl_value_int=10                    
        self.min_bragg = ct.SpinCtrl(
            self.graph_panel,
            ctrl_size=(100, -1),
            label=label_txt,            
            ctrl_value=ctrl_value_int,            
        )

        self.graph_sizer.Add(self.chart, flag=wx.EXPAND, pos=(0, 0), span=(1, 3))
        self.graph_sizer.Add(self.min_bragg, flag=wx.ALIGN_LEFT, pos=(1, 0))
        self.graph_sizer.Add(self.chart_zoom, flag=wx.ALIGN_CENTER, pos=(1, 1))

        self.graph_sizer.AddGrowableRow(0)
        self.graph_sizer.AddGrowableCol(1)
        self.graph_panel.SetSizer(self.graph_sizer)

        # Add all to main sizer
        self.main_sizer.Add(
            self.info_panel, pos=(0, 0), flag=wx.EXPAND | wx.ALL, border=5
        )
        self.main_sizer.Add(
            self.graph_panel, pos=(1, 0), flag=wx.EXPAND | wx.ALL, border=5
        )
        self.main_sizer.AddGrowableCol(0)
        self.main_sizer.AddGrowableRow(1)
        self.SetSizer(self.main_sizer)

    #ADDITION
    def set_sample_id(self,sample_string, run_no):
        self.sample_id = sample_string
        self.run_no = run_no
        self.pg_txt.SetLabel(sample_string)
        self.uc_txt.SetLabel(run_no)

    def save_chart_data(self):
        self.all_data = self.chart.get_chart_data()

    def update_plot(self, reset=False):
        if reset:
            self.chart.reset_chart()
            self.chart.draw_bragg_line(False)
            self.chart.draw_plot(new_data=self.all_data)

        #print("update_plot all_data {}".format(len(self.all_data)))
        self.chart.draw_bragg_line(False)
        self.chart.draw_plot(new_data=self.new_data)
        self.all_data.extend(self.new_data)
        self.new_data = []

    def update_data(self, new_data):
        if len(self.all_data) > RESIZE_WINDOW:
            self.save_chart_data()
        #print("new_data before {}".format(new_data))    
        #new_data = [i for i in new_data if i not in self.all_data]
        #print("new_data after {}".format(new_data))
        self.new_data.extend(new_data)


class TrackerWindow(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, size=(1200, 1000))
        self.parent = parent
        #New Runs
        self.is_new_run_ongoing = False
        self.data_cache = []
        #Pick thresholded metric
        self.use_resolution_threshold = True


        # initialize dictionary of tracker panels
        self.track_panels = {}
        #MEMORY LEAK self.all_info = []

        # Status bar
        self.sb = TrackStatusBar(self)
        self.SetStatusBar(self.sb)
        self.sb.SetStatusText("DISCONNECTED", i=1)

        # Setup main sizer
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Setup toolbar
        self.toolbar = self.CreateToolBar(style=wx.TB_TEXT)
        self.toolbar.SetToolPacking(5)
        self.toolbar.SetMargins((5, -1))

        # Beamline selection
        txt_bl = wx.StaticText(self.toolbar, label="Beamline: ")
        txt_spc = wx.StaticText(self.toolbar, label="   ")
        choices = [s for s in blconfig.sections()]
        chc_bl = wx.Choice(self.toolbar, choices=choices)
        self.toolbar.AddControl(txt_bl)
        self.tb_chc_bl = self.toolbar.AddControl(chc_bl)
        self.toolbar.AddControl(txt_spc)

        # URL textboxes
        txt_url = wx.StaticText(self.toolbar, label="Connect to tcp://")
        ctr_host = wx.TextCtrl(
            self.toolbar, id=wx.ID_ANY, size=(200, -1), value="222.22.2.2"
        )
        txt_div = wx.StaticText(self.toolbar, label=" : ")
        ctr_port = wx.SpinCtrl(
            self.toolbar, id=wx.ID_ANY, size=(80, -1), max=99999, min=4000, value="4433"
        )
        self.toolbar.AddControl(txt_url)
        self.tb_ctrl_host = self.toolbar.AddControl(control=ctr_host)
        self.toolbar.AddControl(txt_div)
        self.tb_ctrl_port = self.toolbar.AddControl(control=ctr_port)

        # Connect toggle
        sock_off_bmp = find_icon("network", size=32)
        self.tb_btn_conn = self.toolbar.AddTool(
            toolId=wx.ID_ANY,
            label="Connect",
            bitmap=sock_off_bmp,
            kind=wx.ITEM_CHECK,
            shortHelp="Connect to / Disconnect from beamline",
        )

        # Test Buttton. Currently triggers tab removal.
        stop_bmp = find_icon("stop", size=32)
        self.tb_btn_stop = self.toolbar.AddTool(
            toolId=wx.ID_ANY,
            label="Clear Tabs",
            bitmap=stop_bmp,
            kind=wx.ITEM_NORMAL,
            shortHelp="Clear Tabs Trigger Button",
        )

        # Quit button
        self.toolbar.AddStretchableSpace()
        quit_bmp = find_icon("exit", size=32)
        self.tb_btn_quit = self.toolbar.AddTool(
            toolId=wx.ID_EXIT,
            label="Quit",
            bitmap=quit_bmp,
            shortHelp="Quit Interceptor",
        )
        self.toolbar.Realize()

        self.nb_panel = wx.Panel(self)
        # self.track_nb = AuiNotebook(self.nb_panel, style=wx.aui.AUI_NB_TOP)
        self.track_nb = wx.Notebook(self.nb_panel, style=wx.NB_RIGHT)
        self.nb_sizer = wx.BoxSizer(wx.VERTICAL)
        self.nb_sizer.Add(self.track_nb, 1, flag=wx.EXPAND | wx.ALL, border=3)
        self.nb_panel.SetSizer(self.nb_sizer)

        # Toolbar bindings
        self.Bind(wx.EVT_TOOL, self.onQuit, self.tb_btn_quit)
        self.Bind(wx.EVT_TOOL, self.onConnect, self.tb_btn_conn)
        self.Bind(wx.EVT_CHOICE, self.onBLChoice, self.tb_chc_bl.GetControl())
        #DEBUG Button Event
        self.Bind(wx.EVT_TOOL, self.onStop, self.tb_btn_stop)        

        # Notebook bindings
        self.Bind(
            wx.EVT_NOTEBOOK_PAGE_CHANGED, self.onPageChange, id=self.track_nb.GetId()
        )

        self.tb_chc_bl.GetControl().SetSelection(0)
        self.set_bl_choice()

    def onBLChoice(self, e):
        self.set_bl_choice()

    def set_bl_choice(self):
        ctrl = self.tb_chc_bl.GetControl()
        selstring = ctrl.GetString(ctrl.GetSelection())
        host = blconfig[selstring]['host']
        port = blconfig[selstring]['port']
        self.tb_ctrl_host.GetControl().SetValue(host)
        self.tb_ctrl_port.GetControl().SetValue(port)

        #Pick thresholded metric
        use_resolution_str = blconfig[selstring]['use_resolution_threshold']        
        use_resolution = False
        if use_resolution_str == "True":
            use_resolution = True
        print("Beamline param use_resolution {}, type {}".format(use_resolution,type(use_resolution)))
        self.use_resolution_threshold = use_resolution


    def onMinBragg(self, e):
        print("onMinBragg")
        self.tracker_panel.chart.draw_bragg_line()

    def onChartRange(self, e):
        zoom_ctrl = self.tracker_panel.chart_zoom
        self.tracker_panel.chart.plot_zoom = zoom_ctrl.plot_zoom
        self.tracker_panel.chart.chart_range = zoom_ctrl.chart_range
        self.tracker_panel.chart.max_lock = zoom_ctrl.max_lock
        self.tracker_panel.chart.x_min = zoom_ctrl.x_min
        self.tracker_panel.chart.x_max = zoom_ctrl.x_max
        if zoom_ctrl.plot_zoom:
            self.tracker_panel.chart.plot_sb.Show()
        else:
            self.tracker_panel.chart.plot_sb.Hide()
        self.tracker_panel.chart.draw_plot()

    def onConnect(self, e):
        connect_id = self.tb_btn_conn.GetId()
        if self.toolbar.GetToolState(connect_id):
            self.create_collector()
            self.start_zmq_collector()
        else:
            self.stop_run()

    def onPageChange(self, e):
        print("Event: onPageChange:")
        self.set_current_chart_panel()
        #Avoid re-drawing page on tab change. Assuming all but the one latest tab
        #is active 
        #self.tracker_panel.update_plot(reset=True)

    def set_current_chart_panel(self):
        # Settings bindings
        self.tracker_panel = self.track_nb.GetCurrentPage()
        self.Bind(wx.EVT_SPINCTRL, self.onMinBragg, self.tracker_panel.min_bragg.ctr)
        # self.Bind(EVT_ZOOM, self.onChartRange)

    def create_new_run(self, run_no=None):
        if run_no is None:
            if not self.track_panels:
                run_no = "1"
            else:
                extant_runs = [int(r) for r in self.track_panels.keys()]
                run_no = max(extant_runs) + 1

        panel_title = "Run {}".format(run_no)
        try:
            self.tracker_panel.save_chart_data()
        except:
            print("Exception: TrackerWindow: self.tracker_panel.save_chart_data() failed")
            pass
        self.tracker_panel = TrackerPanel(
            self.track_nb, main_window=self, run_number=run_no, use_resolution=self.use_resolution_threshold
        )
        self.track_panels[run_no] = self.tracker_panel
        self.track_nb.AddPage(self.tracker_panel, panel_title, select=True)

        self.Bind(wx.EVT_SPINCTRL, self.onMinBragg, self.tracker_panel.min_bragg.ctr)
        # self.Bind(EVT_ZOOM, self.onChartRange)


    def reset_tabs(self):

        #self.track_nb.DeleteAllPages()
        current_panel = self.track_nb.GetCurrentPage()
        print("current_panel {}".format(current_panel))
        print("self.track_panels() {}".format(self.track_panels))
        tabs_to_remove = []
        for tab_label in self.track_panels.keys():
            print("tab_label {}".format(tab_label))
            if current_panel != self.track_panels[tab_label]:
                print("Remove tab {}".format(tab_label))
                tabs_to_remove.append(tab_label)

        for tab in tabs_to_remove:
            page = self.track_nb.FindPage(self.track_panels[tab])
            #self.track_nb.DeletePage(page)
            self.track_nb.RemovePage(page)                
            self.track_panels.pop(tab)
            print("AFTER DELETE: self.track_panels() {}".format(self.track_panels))
            post_panel = self.track_nb.GetCurrentPage()
            print("post_panel {}".format(post_panel))

    def create_collector(self):
        self.ui_timer = wx.Timer(self)
        self.collector = rcv.Receiver(self)
        self.Bind(rcv.EVT_SPFDONE, self.onCollectorInfo)
        self.Bind(wx.EVT_TIMER, self.collector.onUITimer, id=self.ui_timer.GetId())

    def start_zmq_collector(self):
        # clear screen / restart runs

        host = self.tb_ctrl_host.GetControl().GetValue()
        port = self.tb_ctrl_port.GetControl().GetValue()
        sb_msg = "CONNECTED TO tcp://{}:{}".format(host, port)
        self.sb.SetStatusText(sb_msg, i=1)
        self.sb.SetStatusBitmap(connected=True)
        self.ui_timer.Start(UI_TIMER_PERIOD_MS) 
        self.collector.connect(host=host, port=port)
        self.collector.start()

    def stop_run(self):
        if hasattr(self, "collector"):
            self.collector.close_socket()
            self.ui_timer.Stop()

            self.sb.SetStatusText("DISCONNECTED", i=1)
            self.sb.SetStatusBitmap(connected=False)

            # remove collector and timer
            del self.collector
            del self.ui_timer

    def getTabString(self,sample_string,run_no_string, 
                    max_sample_string_length=MAX_TAB_TEXT_LENGTH):
        sample_label = sample_string
        N = max(1,(MAX_TAB_TEXT_LENGTH-1)//2) 
        if len(sample_string) > max_sample_string_length:
            sample_label = str(sample_string[:N])+"..."+str(sample_string[-N:])
        return sample_label+"_"+str(run_no_string)


    def onCollectorInfo(self, e):
        """ Occurs on every wx.PostEvent instance; updates lists of images with
    spotfinding results """

        info_list = e.GetValue()
        # MEMORY LEAK self.all_info.extend(info_list)
        new_data_dict = {}
        run_no_dict = {}
        sample_id_dict = {}
        
        print("onCollectorInfo\n")

        #The GUI can be overrun by data during tab switches. This should save incoming
        #data until the new tab/run is created. Not a problem after some tuning and
        #fixes, but can still happen.
        if self.is_new_run_ongoing:
            print("CREATE TAB ONGOING: len(info_list) {}, type {}".format(len(info_list),type(info_list)))
            if info_list:
                self.data_cache = self.data_cache + info_list
            return

        if info_list:

            if len(self.data_cache) > 0:
                for i in range(0,len(self.data_cache)):
                    info_list.append(self.data_cache[i])
                self.data_cache=[]

            for info in info_list:
                run_no = info["run_no"]
                sample_id = info["sample_string"]
                tab_id = self.getTabString(info["sample_string"],info["run_no"])
                run_no_dict[tab_id]=run_no
                sample_id_dict[tab_id]=sample_id

                if tab_id not in self.track_panels:
                    print("debug: creating new run # {}, type {}".format(tab_id,type(tab_id)))
                    self.is_new_run_ongoing = True
                    start_time = time.time()
                    self.create_new_run(run_no=tab_id)
                    self.is_new_run_ongoing = False
                    end_time = time.time()
                    print("debug: create_new_run time: {:.2f}s".format(end_time-start_time))
                    

                if tab_id in new_data_dict:
                    new_data_dict[tab_id].append(
                        (
                            info["frame_idx"],
                            info["n_spots"],
                            info["indexed"],
                            info["hres"],
                            info["quality"],
                        )
                    )
                else:
                    new_data_dict[tab_id] = [
                        (
                            info["frame_idx"],
                            info["n_spots"],
                            info["indexed"],
                            info["hres"],
                            info["quality"],
                        )
                    ]

            # update track panel data
            for tab_id in new_data_dict:
                if tab_id in self.track_panels:
                    #print("run_no {}, new_data_dict[run_no] {}".format(run_no,new_data_dict[run_no]))
                    self.track_panels[tab_id].update_data(new_data=new_data_dict[tab_id])
                    self.track_panels[tab_id].set_sample_id( sample_id_dict[tab_id],run_no_dict[tab_id])
                    # update current plot
                    #self.track_panels[tab_id].update_plot()
                else:
                    print("ERROR, track_panels changed")

        # update current plot
        self.tracker_panel.update_plot()

    def onQuit(self, e):
        self.Close()

        # TODO: CLEANUP ON EXIT!
        self.stop_run()


    def onStop(self, e):
        print("Clear Button Event!!")
        #Debug button removes all but the active tab.
        self.reset_tabs()

class MainTESTApp(wx.App):
    """ App for the main GUI window  """

    def OnInit(self):
        from interceptor import __version__ as intxr_version

        self.frame = TrackerWindow(
            None, -1, title="MAXIV DOZOR INTERCEPTOR v.{}" "".format(intxr_version)
        )
        self.frame.SetMinSize(self.frame.GetEffectiveMinSize())
        self.frame.SetPosition((150, 150))
        self.frame.Show(True)

        self.frame.create_new_run()

        self.frame.Layout()
        self.SetTopWindow(self.frame)
        return True


if __name__ == "__main__":
    app = MainTESTApp(0)
    app.MainLoop()
