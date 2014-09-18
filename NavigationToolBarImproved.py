#===============================================================================
# 
#  License: GPL
# 
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License 2
#  as published by the Free Software Foundation.
# 
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
# 
#   You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
# 
#===============================================================================
 
from matplotlib.backends.backend_wx import NavigationToolbar2Wx           
import wx

class NavigationToolbar2Wx_improved(NavigationToolbar2Wx):
    """wx/mpl NavToolbar hack with an additional tools user interaction.
    This class is necessary because simply adding a new togglable tool to the
    toolbar won't (1) radio-toggle between the new tool and the pan/zoom tools.
    (2) disable the pan/zoom tool modes in the associated subplot(s).
    """
    def __init__(self, canvas):
        NavigationToolbar2Wx.__init__(self,canvas)
        self.pan_tool  = self.FindById(self.wx_ids['Pan'])
        self.zoom_tool = self.FindById(self.wx_ids['Zoom'])
        #self.home_tool = self.FindById(self._NTB2_HOME)
        
        self.Bind(wx.EVT_TOOL, self.on_toggle_pan_zoom, self.zoom_tool)
        self.Bind(wx.EVT_TOOL, self.on_toggle_pan_zoom, self.pan_tool)

        self.user_tools = {}   # user_tools['tool_mode'] : wx.ToolBarToolBase

        self.InsertSeparator(5)
       

    def add_user_tool(self, mode, pos, bmp, istoggle=True, shortHelp=''):
        """Adds a new user-defined tool to the toolbar.
        mode -- the value that MyNavToolbar.get_mode() will return if this tool 
                is toggled on
        pos -- the position in the toolbar to add the icon
        bmp -- a wx.Bitmap of the icon to use in the toolbar
        isToggle -- whether or not the new tool toggles on/off with the other 
                    togglable tools
        shortHelp -- the tooltip shown to the user for the new tool
        """
        tool_id = wx.NewId()
        self.user_tools[mode] = self.InsertSimpleTool(pos, tool_id, bmp,
                            isToggle=istoggle, shortHelpString=shortHelp)
        self.Bind(wx.EVT_TOOL, self.on_toggle_user_tool, self.user_tools[mode])

    def get_mode(self):
        """Use this rather than navtoolbar.mode
        """
        for mode, tool in self.user_tools.items():
            if tool.IsToggled():
                return mode
        return self.mode

    def untoggle_mpl_tools(self):
        """Hack city: Since I can't figure out how to change the way the 
        associated subplot(s) handles mouse events: I generate events to turn
        off whichever tool mode is enabled (if any). 
        This function needs to be called whenever any user-defined tool 
        (eg: lasso) is clicked.
        """
        if self.pan_tool.IsToggled():
            wx.PostEvent(
                self.GetEventHandler(), 
                wx.CommandEvent(wx.EVT_TOOL.typeId, self.wx_ids['Pan'])
            )
            self.ToggleTool(self.wx_ids['Pan'], False)
        elif self.zoom_tool.IsToggled():
            wx.PostEvent(
                self.GetEventHandler(),
                wx.CommandEvent(wx.EVT_TOOL.typeId, self.wx_ids['Zoom'])
            )
            self.ToggleTool(self.wx_ids['Zoom'], False)

    def on_toggle_user_tool(self, evt):
        """user tool click handler.
        """
        if evt.Checked():
            self.untoggle_mpl_tools()
            #untoggle other user tools
            for tool in self.user_tools.values():
                if tool.Id != evt.Id:
                    self.ToggleTool(tool.Id, False)

    def on_toggle_pan_zoom(self, evt):
        """Called when pan or zoom is toggled. 
        We need to manually untoggle user-defined tools.
        """
        if evt.Checked():
            for tool in self.user_tools.values():
                self.ToggleTool(tool.Id, False)
        # Make sure the regular pan/zoom handlers get the event
        evt.Skip()

    def reset_history(self):
        """More hacky junk to clear/reset the toolbar history.
        """
        self._views.clear()
        self._positions.clear()
        self.push_current()