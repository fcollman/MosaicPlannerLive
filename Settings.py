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
import wx

class CameraSettings():
    """simple struct for containing the parameters for the camera"""
    def __init__(self,sensor_height=1040,sensor_width=1388,pix_width=6.5,pix_height=6.5):
        #in pixels        
        self.sensor_height=sensor_height
        self.sensor_width=sensor_width
        #in microns
        self.pix_width=pix_width
        self.pix_height=pix_height
    def save_settings(self,cfg):
        cfg.WriteInt('sensor_height',self.sensor_height)
        cfg.WriteInt('sensor_width',self.sensor_width)
        cfg.WriteFloat('pix_width',self.pix_width)
        cfg.WriteFloat('pix_height',self.pix_height)
    def load_settings(self,cfg):
        self.sensor_height=cfg.ReadInt('sensor_height',1040)
        self.sensor_width=cfg.ReadInt('sensor_width',1388)
        self.pix_width=cfg.ReadFloat('pix_width',6.5)
        self.pix_height=cfg.ReadFloat('pix_height',6.5)
        
class MosaicSettings:
    def __init__(self,mag=65.486,mx=1,my=1,overlap=10,show_box=False,show_frames=False):
        """a simple struct class for encoding settings about mosaics
        
        keywords)
        mag=magnification of objective
        mx=integer number of columns in a rectangular mosaic
        my=integer number of rows in a rectangular mosaic
        overlap=percentage overlap of individual frames (0-100)
        show_box=boolean as to whether to display the box
        show_frames=Boolean as to whether to display the individual frames
        
        """
        self.mx=mx
        self.my=my
        self.overlap=overlap
        self.show_box=show_box
        self.show_frames=show_frames
        self.mag=mag
    def save_settings(self,cfg):
        cfg.WriteFloat('mosaic_mag',self.mag)
        cfg.WriteInt('mosaic_mx',self.mx)
        cfg.WriteInt('mosaic_my',self.my)
        cfg.WriteInt('mosaic_overlap',self.overlap)
        cfg.WriteBool('mosaic_show_box',self.show_box)
        cfg.WriteBool('mosaic_show_frames',self.show_frames)
        
    def load_settings(self,cfg):
        self.mag=cfg.ReadFloat('mosaic_mag',65.486)
        self.mx=cfg.ReadInt('mosaic_mx',1)
        self.my=cfg.ReadInt('mosaic_my',1)
        self.overlap=cfg.ReadInt('mosaic_overlap',10)
        self.show_box=cfg.WriteBool('mosaic_show_box',False)
        self.show_frames=cfg.WriteBool('mosaic_show_frames',False)
        
  
class ChangeCameraSettings(wx.Dialog):
    """simple dialog for changing the camera settings"""
    def __init__(self, parent, id, title, settings):
        wx.Dialog.__init__(self, parent, id, title, size=(230, 210))
        panel = wx.Panel(self, -1)
        vbox = wx.BoxSizer(wx.VERTICAL)       
        self.widthIntCtrl=wx.lib.intctrl.IntCtrl( panel, value=settings.sensor_width,pos=(95,5),size=( 90, -1 ) )
        self.heightIntCtrl=wx.lib.intctrl.IntCtrl( panel, value=settings.sensor_height,pos=(95,35),size=( 90, -1 ) )
        self.pixwidthFloatCtrl=wx.lib.agw.floatspin.FloatSpin(panel, pos=(95,65),size=( 90, -1 ),
                                       value=settings.pix_width,
                                       min_val=0.1,
                                       max_val=100,
                                       increment=.1,
                                       digits=2,
                                       name='pix_width')
        self.pixheightFloatCtrl=wx.lib.agw.floatspin.FloatSpin(panel, pos=(95,95),size=( 90, -1 ),
                                       value=settings.pix_height,
                                       min_val=0.1,
                                       max_val=100,
                                       increment=.1,
                                       digits=2,
                                       name='pix_height')                             
                                         
        wx.StaticText(panel,id=wx.ID_ANY,label="Width (pixels)",pos=(5,8))
        wx.StaticText(panel,id=wx.ID_ANY,label="Height (pixels)",pos=(5,38))  
        wx.StaticText(panel,id=wx.ID_ANY,label="Pixel Width (um)",pos=(5,68))  
        wx.StaticText(panel,id=wx.ID_ANY,label="Pixel Height (um)",pos=(5,98)) 
                                         
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        okButton = wx.Button(self, wx.ID_OK, 'Ok', size=(70, 30))
       # closeButton = wx.Button(self, wx.ID_CLOSE, 'Close', size=(70, 30))
        hbox.Add(okButton, 1)
        #hbox.Add(closeButton, 1, wx.LEFT, 5)
        vbox.Add(panel)
        vbox.Add(hbox, 1, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 10)
        self.SetSizer(vbox)
    def GetSettings(self):
        """extracts the Camera Settings from the controls"""
        return CameraSettings(sensor_width=self.widthIntCtrl.GetValue(),
                              sensor_height=self.heightIntCtrl.GetValue(),
                              pix_width=self.pixwidthFloatCtrl.GetValue(),
                              pix_height=self.pixheightFloatCtrl.GetValue())
        
class ImageSettings():
    def __init__(self,extent=[0,10,10,0]):
        self.extent=extent
        
class ChangeImageMetadata(wx.Dialog):
    """simple dialog for edchanging the camera settings"""
    def __init__(self, parent, id, title, settings=ImageSettings()):
        wx.Dialog.__init__(self, parent, id, title, size=(230, 210))
        panel = wx.Panel(self, -1)
        vbox = wx.BoxSizer(wx.VERTICAL)       
        self.minXIntCtrl=wx.lib.agw.floatspin.FloatSpin( panel, value=settings.extent[0],pos=(125,5),size=( 90, -1 ),increment=1,digits=2 )
        self.maxXIntCtrl=wx.lib.agw.floatspin.FloatSpin( panel, value=settings.extent[1],pos=(125,35),size=( 90, -1 ),increment=1,digits=2 )
        self.minYIntCtrl=wx.lib.agw.floatspin.FloatSpin( panel, value=settings.extent[3],pos=(125,65),size=( 90, -1 ),increment=1,digits=2 )
        self.maxYIntCtrl=wx.lib.agw.floatspin.FloatSpin( panel, value=settings.extent[2],pos=(125,95),size=( 90, -1 ),increment=1,digits=2 )
                                                           
        wx.StaticText(panel,id=wx.ID_ANY,label="Minimum X (um)",pos=(5,8))
        wx.StaticText(panel,id=wx.ID_ANY,label="Maximum X (um)",pos=(5,38))  
        wx.StaticText(panel,id=wx.ID_ANY,label="Minimum Y (um) (bottom)",pos=(5,68))  
        wx.StaticText(panel,id=wx.ID_ANY,label="Maximum Y (um) (top)",pos=(5,98)) 
                                         
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        okButton = wx.Button(self, wx.ID_OK, 'Ok', size=(70, 30))
       # closeButton = wx.Button(self, wx.ID_CLOSE, 'Close', size=(70, 30))
        hbox.Add(okButton, 1)
        #hbox.Add(closeButton, 1, wx.LEFT, 5)
        vbox.Add(panel)
        vbox.Add(hbox, 1, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 10)
        self.SetSizer(vbox)
    def GetSettings(self):
        """extracts the Camera Settings from the controls"""
        return ImageSettings(extent=[self.minXIntCtrl.GetValue(),
                                     self.maxXIntCtrl.GetValue(),
                                     self.maxYIntCtrl.GetValue(),
                                     self.minYIntCtrl.GetValue()])
        

class SmartSEMSettings():
    def __init__(self,mag=1200,tilt=0.33,rot=0,Z=0.0125,WD=0.00632568):
        self.mag=mag
        self.tilt=tilt
        self.rot=rot
        self.Z=Z
        self.WD=WD
    def save_settings(self,cfg):
        cfg.WriteInt('SEM_mag',self.mag)
        cfg.WriteFloat('SEM_tilt',self.tilt)
        cfg.WriteFloat('SEM_rot',self.rot)
        cfg.WriteFloat('SEM_Z',self.Z)
        cfg.WriteFloat('SEM_WD',self.WD)
    def load_settings(self,cfg):
        self.mag=cfg.ReadInt('SEM_mag',1200)
        self.tilt=cfg.ReadFloat('SEM_tilt',0.33)
        self.rot=cfg.ReadFloat('SEM_rot',0)
        self.Z=cfg.ReadFloat('SEM_Z',0.0125)
        self.WD=cfg.ReadFloat('SEM_WD',0.00632568)
        
class ChangeSEMSettings(wx.Dialog):
    """simple dialog for edchanging the camera settings"""
    def __init__(self, parent, id, title, settings=SmartSEMSettings()):
        wx.Dialog.__init__(self, parent, id, title, size=(230, 210))
        panel = wx.Panel(self, -1)
        vbox = wx.BoxSizer(wx.VERTICAL)       
        self.magCtrl=wx.lib.agw.floatspin.FloatSpin( panel, value=settings.mag,pos=(125,5),size=( 90, -1 ),increment=100,digits=2 )
        self.tiltCtrl=wx.lib.agw.floatspin.FloatSpin( panel, value=settings.tilt,pos=(125,35),size=( 90, -1 ),increment=1,digits=4 )
        self.rotCtrl=wx.lib.agw.floatspin.FloatSpin( panel, value=settings.rot,pos=(125,65),size=( 90, -1 ),increment=1,digits=4 )
        self.ZCtrl=wx.lib.agw.floatspin.FloatSpin( panel, value=settings.Z,pos=(125,95),size=( 90, -1 ),increment=1,digits=4 )
        self.WDCtrl=wx.lib.agw.floatspin.FloatSpin( panel, value=settings.WD,pos=(125,125),size=( 90, -1 ),increment=1,digits=4 )
        
        wx.StaticText(panel,id=wx.ID_ANY,label="magnification (prop. area)",pos=(5,8))
        wx.StaticText(panel,id=wx.ID_ANY,label="tilt (radians)",pos=(5,38))  
        wx.StaticText(panel,id=wx.ID_ANY,label="rotation (radians)",pos=(5,68))  
        wx.StaticText(panel,id=wx.ID_ANY,label="Z location (mm)",pos=(5,98))
        wx.StaticText(panel,id=wx.ID_ANY,label="WD working distance? (mm)",pos=(5,128))
                                         
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        okButton = wx.Button(self, wx.ID_OK, 'Ok', size=(70, 30))
       # closeButton = wx.Button(self, wx.ID_CLOSE, 'Close', size=(70, 30))
        hbox.Add(okButton, 1)
        #hbox.Add(closeButton, 1, wx.LEFT, 5)
        vbox.Add(panel)
        vbox.Add(hbox, 1, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 10)
        self.SetSizer(vbox)
    def GetSettings(self):
        """extracts the Camera Settings from the controls"""
        return SmartSEMSettings(mag=self.magCtrl.GetValue(),
                                     tilt=self.tiltCtrl.GetValue(),
                                     rot=self.rotCtrl.GetValue(),
                                     Z=self.ZCtrl.GetValue(),
                                     WD=self.WDCtrl)
                                     