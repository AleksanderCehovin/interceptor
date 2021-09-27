from __future__ import absolute_import, division, print_function

"""
Author      : Lyubimov, A.Y.
Created     : 07/08/2016
Last Changed: 12/02/2019
Description : IOTA GUI controls
"""

import os
from glob import glob

import wx
import wx.lib.agw.floatspin as fs


# Platform-specific stuff
# TODO: Will need to test this on Windows at some point
if wx.Platform == "__WXGTK__":
    plot_font_size = 10
    norm_font_size = 10
    button_font_size = 12
    LABEL_SIZE = 14
    CAPTION_SIZE = 12
    python = "python"
elif wx.Platform == "__WXMAC__":
    plot_font_size = 9
    norm_font_size = 12
    button_font_size = 14
    LABEL_SIZE = 14
    CAPTION_SIZE = 12
    python = "Python"
elif wx.Platform == "__WXMSW__":
    plot_font_size = 9
    norm_font_size = 9
    button_font_size = 11
    LABEL_SIZE = 11
    CAPTION_SIZE = 9
    python = "Python"  # TODO: make sure it's right!



# --------------------------------- Controls --------------------------------- #


class CtrlBase(wx.Panel):
    """Control panel base class.

    @DynamicAttrs
    """

    def __init__(
        self,
        parent,
        label_style="normal",
        label_font_size=norm_font_size,
        content_style="normal",
        content_font_size=norm_font_size,
        size=wx.DefaultSize,
    ):

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY, size=size)

        self.window = self.GetTopLevelParent()

        # TODO: streamline this
        # Set control attributes
        self.expert_level = 0
        self.font = wx.Font(
            norm_font_size,
            wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_NORMAL,
        )
        self.cfont = wx.Font(
            norm_font_size,
            wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_NORMAL,
        )

        # Set font attributes for label
        if "bold" in label_style:
            self.font.SetWeight(wx.FONTWEIGHT_BOLD)
        if "italic" in label_style:
            self.font.SetStyle(wx.FONTSTYLE_ITALIC)
        if "teletype" in label_style:
            self.font.SetFamily(wx.FONTFAMILY_TELETYPE)

        # Set font attributes for content
        if "bold" in content_style:
            self.cfont.SetWeight(wx.FONTWEIGHT_BOLD)
        if "italic" in content_style:
            self.cfont.SetStyle(wx.FONTSTYLE_ITALIC)
        if "teletype" in content_style:
            self.cfont.SetFamily(wx.FONTFAMILY_TELETYPE)

        self.font.SetPointSize(label_font_size)
        self.cfont.SetPointSize(content_font_size)


class SpinCtrl(CtrlBase):
    """Generic panel will place a spin control w/ label."""

    def __init__(
        self,
        parent,
        label="",
        label_size=wx.DefaultSize,
        label_style="normal",
        checkbox=False,
        checkbox_state=False,
        checkbox_label="",
        ctrl_size=wx.DefaultSize,
        ctrl_value="3",
        ctrl_max=999999,
        ctrl_min=0,
        ctrl_step=1,
        ctrl_digits=0,
    ):

        CtrlBase.__init__(self, parent=parent, label_style=label_style)

        self.value = ctrl_value
        self.checkbox_state = checkbox_state
        self.toggle = None
        cols = 3

        if checkbox:
            assert checkbox_label != ""
            label = ""
            cols += 1
            self.toggle = wx.CheckBox(self, label=checkbox_label, size=label_size)
            self.toggle.SetValue(self.checkbox_state)

        ctr_box = wx.FlexGridSizer(1, cols, 0, 5)

        if hasattr(label, "decode"):
            label = label.decode("utf-8")
        self.txt = wx.StaticText(self, label=label, size=label_size)
        self.txt.SetFont(self.font)
        self.ctr = fs.FloatSpin(
            self,
            value=ctrl_value,
            max_val=(ctrl_max),
            min_val=(ctrl_min),
            increment=ctrl_step,
            digits=ctrl_digits,
            size=ctrl_size,
        )

        if checkbox:
            ctr_box.Add(self.toggle, flag=wx.ALIGN_CENTER_VERTICAL)
            self.toggle_boxes(flag_on=self.checkbox_state)
            self.Bind(wx.EVT_CHECKBOX, self.onToggle, self.toggle)

        ctr_box.Add(self.txt, flag=wx.ALIGN_CENTER_VERTICAL)
        ctr_box.Add(
            self.ctr, flag= wx.ALIGN_RIGHT | wx.EXPAND
        )

        self.SetSizer(ctr_box)

    def onToggle(self, e):
        self.toggle_boxes(flag_on=self.toggle.GetValue())
        e.Skip()

    def toggle_boxes(self, flag_on=True):
        self.toggle.SetValue(flag_on)
        if flag_on:
            self.ctr.Enable()
            self.ctr.SetValue(int(self.value))
        else:
            self.value = self.ctr.GetValue()
            self.ctr.Disable()

    def reset_default(self):
        self.ctr.SetValue(int(self.value))


# ---end
