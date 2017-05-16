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

class ZstackSettings():

    def __init__(self,zstack_delta = 1.0, zstack_number = 3.0, zstack_flag = True):
        self.zstack_flag = zstack_flag
        self.zstack_delta = zstack_delta
        self.zstack_number = int(zstack_number + (1 - zstack_number % 2))

    def save_settings(self,cfg):
        cfg['ZStackSettings']['zstack_delta']=self.zstack_delta
        cfg['ZStackSettings']['zstack_flag']=self.zstack_flag
        cfg['ZStackSettings']['zstack_number']=self.zstack_number

    def load_settings(self,cfg):
        self.zstack_delta = cfg['ZStackSettings']['zstack_delta']
        self.zstack_flag = cfg['ZStackSettings']['zstack_flag']
        self.zstack_number = cfg['ZStackSettings']['zstack_number']
        print self.zstack_number,type(self.zstack_number)
        self.zstack_number = int(self.zstack_number + (1 - self.zstack_number % 2))

class ChangeZstackSettings(wx.Dialog):
    def __init__(self, parent, id, title, settings,style):
        wx.Dialog.__init__(self, parent, id, title,style=wx.DEFAULT_DIALOG_STYLE, size=(420, -1))
        vbox =wx.BoxSizer(wx.VERTICAL)

        self.settings = settings
        self.zflagtxt = wx.StaticText(self,label="Take Z stacks?")
        self.checkBox = wx.CheckBox(self)
        self.checkBox.SetValue(settings.zstack_flag)
        self.znumberTxt = wx.StaticText(self,label="number of images to take (forced to be odd for middle=current)")
        self.znumberIntCtrl = wx.lib.intctrl.IntCtrl( self, value=settings.zstack_number,size=(50,-1))
        self.zdeltaTxt = wx.StaticText(self,label="z step between images (microns)")
        self.zdeltaFloatCtrl = wx.lib.agw.floatspin.FloatSpin(self,
                                       value=settings.zstack_delta,
                                       min_val=0,
                                       max_val=10.0,
                                       increment=.01,
                                       digits=2,
                                       name='',
                                       size=(95,-1))
        ok_button = wx.Button(self,wx.ID_OK,'OK')
        cancel_button = wx.Button(self,wx.ID_CANCEL,'Cancel')
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        hbox4 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(self.zflagtxt)
        hbox1.Add(self.checkBox)
        hbox2.Add(self.znumberIntCtrl)
        hbox2.Add(self.znumberTxt)
        hbox3.Add(self.zdeltaFloatCtrl)
        hbox3.Add(self.zdeltaTxt)
        hbox4.Add(ok_button)
        hbox4.Add(cancel_button)
        vbox.Add(hbox1)
        vbox.Add(hbox2)
        vbox.Add(hbox3)
        vbox.Add(hbox4)
        self.SetSizer(vbox)

    def GetSettings(self):
        flag        = self.checkBox.GetValue()
        stacksize   = self.znumberIntCtrl.GetValue()
        delta       = self.zdeltaFloatCtrl.GetValue()
        return ZstackSettings(zstack_delta = delta,zstack_number = stacksize,zstack_flag = flag)

class CorrSettings():

    def __init__(self,window=100,delta=75,skip = 3,corr_thresh = .3):
    
        self.window = window
        self.delta = delta
        self.skip = skip
        self.corr_thresh  = corr_thresh
        
    def save_settings(self,cfg):
        cfg['CorrSettings']['CorrTool_window']=self.window
        cfg['CorrSettings']['CorrTool_delta']=self.delta
        cfg['CorrSettings']['CorrTool_skip']=self.skip
        cfg['CorrSettings']['CorrTool_corr_thresh']=self.corr_thresh
    
    def load_settings(self,cfg):
        self.window=cfg['CorrSettings']['CorrTool_window']
        self.delta=cfg['CorrSettings']['CorrTool_delta']
        self.skip = cfg['CorrSettings']['CorrTool_skip']
        self.corr_thresh = cfg['CorrSettings']['CorrTool_corr_thresh']

class ChangeCorrSettings(wx.Dialog):
    def __init__(self, parent, id, title, settings,style):
        wx.Dialog.__init__(self, parent, id, title,style=wx.DEFAULT_DIALOG_STYLE, size=(420, -1))
        vbox =wx.BoxSizer(wx.VERTICAL)
        
        self.settings = settings
        self.windowTxt = wx.StaticText(self,label="window in microns to cutout")
        self.windowIntCtrl = wx.lib.intctrl.IntCtrl( self, value=settings.window,size=(50,-1))
        #self.deltaTxt = wx.StaticText(self,label="delta (in pixels) to search for maximum")
        #self.deltaIntCtrl = wx.lib.intctrl.IntCtrl( self, value=settings.delta,size=(50,-1))
        #self.skipTxt = wx.StaticText(self,label="number of pixels to skip when searching")
        #self.skipIntCtrl = wx.lib.intctrl.IntCtrl( self, value=settings.skip,size=(50,-1))
        

        self.corr_threshThresholdTxt = wx.StaticText(self,label="correlation threshold to accept match (0.0-1.0)")
        self.corr_threshThresholdFloatCtrl = wx.lib.agw.floatspin.FloatSpin(self, 
                                       value=settings.corr_thresh,
                                       min_val=0,
                                       max_val=1.0,
                                       increment=.01,
                                       digits=2,
                                       name='',
                                       size=(95,-1)) 
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        
        hbox1.Add(self.windowIntCtrl)
        hbox1.Add(self.windowTxt)
        #hbox1.Add(self.deltaIntCtrl)
        #hbox1.Add(self.skipIntCtrl)

        #hbox2.Add(self.deltaTxt)
        #hbox2.Add(self.skipTxt)
        hbox2.Add(self.corr_threshThresholdFloatCtrl)
        hbox2.Add(self.corr_threshThresholdTxt)   

        hbox3 = wx.BoxSizer(wx.HORIZONTAL)      
        ok_button = wx.Button(self,wx.ID_OK,'OK')
        cancel_button = wx.Button(self,wx.ID_CANCEL,'Cancel')
        hbox3.Add(ok_button)
        hbox3.Add(cancel_button)
        
        vbox.Add(hbox1)
        vbox.Add(hbox2)
        vbox.Add(hbox3)

        self.SetSizer(vbox)
        
    def GetSettings(self):
        window=self.windowIntCtrl.GetValue()
        #delta=self.deltaIntCtrl.GetValue()
        #skip=self.skipIntCtrl.GetValue()
        corr_thresh=self.corr_threshThresholdFloatCtrl.GetValue()

        return CorrSettings(window=window,corr_thresh=corr_thresh)

class SiftSettings():

    def __init__(self,contrastThreshold=.05,numFeatures=1000,inlier_thresh = 12):
    
        self.contrastThreshold=contrastThreshold
        self.numFeatures=numFeatures
        self.inlier_thresh = inlier_thresh
        
    def save_settings(self,cfg):
        cfg['SiftSettings','numFeatures']=self.numFeatures
        cfg['SiftSettings','inlier_thresh']=self.inlier_thresh
        cfg['SiftSettings','contrastThreshold']=self.contrastThreshold
    
    def load_settings(self,cfg):
        self.numFeatures=cfg['SiftSettings']['numFeatures']
        self.contrastThreshold=cfg['SiftSettings']['contrastThreshold']
        self.inlier_thresh = cfg['SiftSettings']['inlier_thresh']
        
class ChangeSiftSettings(wx.Dialog):
    def __init__(self, parent, id, title, settings,style):
        wx.Dialog.__init__(self, parent, id, title,style=wx.DEFAULT_DIALOG_STYLE, size=(420, -1))   
        vbox =wx.BoxSizer(wx.VERTICAL)
        
        self.settings=settings
        self.numFeatureTxt=wx.StaticText(self,label="max features")
        self.numFeatureIntCtrl = wx.lib.intctrl.IntCtrl( self, value=settings.numFeatures,size=(50,-1))
        self.inlierThreshTxt=wx.StaticText(self,label="minimum inliers for match")
        self.inlierThreshIntCtrl = wx.lib.intctrl.IntCtrl( self, value=settings.inlier_thresh,size=(50,-1))

        self.contrastThresholdTxt = wx.StaticText(self,label="contrast threshold")
        self.contrastThresholdFloatCtrl = wx.lib.agw.floatspin.FloatSpin(self, 
                                       value=settings.contrastThreshold,
                                       min_val=0,
                                       max_val=12.0,
                                       increment=.01,
                                       digits=2,
                                       name='',
                                       size=(95,-1)) 
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        
        hbox1.Add(self.numFeatureTxt)
        hbox1.Add(self.numFeatureIntCtrl)
        hbox1.Add(self.inlierThreshIntCtrl)
        
        hbox2.Add(self.contrastThresholdTxt)
        hbox2.Add(self.contrastThresholdFloatCtrl)
        hbox2.Add(self.inlierThreshTxt)

        
       

        hbox3 = wx.BoxSizer(wx.HORIZONTAL)      
        ok_button = wx.Button(self,wx.ID_OK,'OK')
        cancel_button = wx.Button(self,wx.ID_CANCEL,'Cancel')
        hbox3.Add(ok_button)
        hbox3.Add(cancel_button)
        
        vbox.Add(hbox1)
        vbox.Add(hbox2)
        vbox.Add(hbox3)

        self.SetSizer(vbox)
        
    def GetSettings(self):
        numFeatures = self.numFeatureIntCtrl.GetValue()
        contrastThreshold = self.contrastThresholdFloatCtrl.GetValue()
        inlier_thresh = self.inlierThreshIntCtrl.GetValue()
        return SiftSettings(contrastThreshold,numFeatures,inlier_thresh)
        
        
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
        cfg['Camera_Settings']['sensor_height']=self.sensor_height
        cfg['Camera_Settings']['sensor_width']=self.sensor_width
        cfg['Camera_Settings']['pix_width']=self.pix_width
        cfg['Camera_Settings']['pix_height']=self.pix_height
    def load_settings(self,cfg):
        self.sensor_height=cfg['Camera_Settings']['sensor_height']
        self.sensor_width=cfg['Camera_Settings']['sensor_width']
        self.pix_width=cfg['Camera_Settings']['pix_width']
        self.pix_height=cfg['Camera_Settings']['pix_height']

class ChannelSettings():
    """simple struct for containing the parameters for the microscope"""
    def __init__(self,channels,exposure_times=dict([]),zoffsets=dict([]),
                 usechannels=dict([]),prot_names=dict([]),map_chan=None,
                 def_exposure=100,def_offset=0.0,):
        #def_exposure is default exposure time in msec
       
        
        self.channels= channels
        self.def_exposure=def_exposure
        self.def_offset=def_offset
        
        self.exposure_times=exposure_times
        self.zoffsets=zoffsets
        self.usechannels=usechannels
        self.prot_names=prot_names

        if map_chan is None:
            for ch in self.channels:
                if 'dapi' in ch.lower():
                    map_chan = ch
        if map_chan is None:
            map_chan = channels[0]
            
        self.map_chan = map_chan
        
    def save_settings(self,cfg):    
        
        cfg['ChannelSettings']['map_chan']=self.map_chan
        for ch in self.channels:
            cfg['ChannelSettings']['Exposure_'+ch]=self.exposure_times[ch]
            cfg['ChannelSettings']['ZOffsets_'+ch]=self.zoffsets[ch]
            cfg['ChannelSettings']['UseChannel_'+ch]=self.usechannels[ch]
            cfg['ChannelSettings']['ProteinNames_'+ch]=self.prot_names[ch]

    def load_settings(self,cfg):
        for ch in self.channels:
            self.exposure_times[ch]=cfg['ChannelSettings'].get('Exposures_'+ch,self.def_exposure)
            self.zoffsets[ch]=cfg['ChannelSettings'].get('ZOffsets_'+ch,self.def_offset)
            self.usechannels[ch]=cfg['ChannelSettings'].get('UseChannel_'+ch,True)
            self.prot_names[ch]=cfg['ChannelSettings'].get('ProteinNames_'+ch,ch)

        self.map_chan=str(cfg['ChannelSettings']['map_chan'])

class ChangeChannelSettings(wx.Dialog):
    """simple dialog for changing the channel settings"""
    def __init__(self, parent, id, title, settings,style):
        wx.Dialog.__init__(self, parent, id, title,style=wx.DEFAULT_DIALOG_STYLE, size=(420, -1))
        
        self.settings=settings
        vbox = wx.BoxSizer(wx.VERTICAL)   
        Nch=len(settings.channels)
        print Nch
        
        gridSizer=wx.FlexGridSizer(rows=Nch+3,cols=6,vgap=5,hgap=5)
        
      
        gridSizer.Add(wx.StaticText(self,id=wx.ID_ANY,label="chan"),border=5)
        gridSizer.Add(wx.StaticText(self,id=wx.ID_ANY,label="protein"),border=5)     
        gridSizer.Add(wx.StaticText(self,id=wx.ID_ANY,label="use?"),border=5)
        gridSizer.Add(wx.StaticText(self,id=wx.ID_ANY,label="exposure"),border=5)
        gridSizer.Add(wx.StaticText(self,id=wx.ID_ANY,label="map?"),border=5)
        gridSizer.Add(wx.StaticText(self,id=wx.ID_ANY,label="zoffset     "),border=5)

        self.ProtNameCtrls=[]
        self.UseCtrls=[]
        self.ExposureCtrls=[]
        self.MapRadCtrls=[]
        self.ZOffCtrls=[]
        
        for ch in settings.channels:
            hbox =wx.BoxSizer(wx.HORIZONTAL)
            Txt=wx.StaticText(self,label=ch)
            ProtText=wx.TextCtrl(self,value=settings.prot_names[ch])
            ChBox = wx.CheckBox(self)
            ChBox.SetValue(settings.usechannels[ch])
            IntCtrl=wx.lib.intctrl.IntCtrl( self, value=settings.exposure_times[ch],size=(50,-1))
            FloatCtrl=wx.lib.agw.floatspin.FloatSpin(self, 
                                       value=settings.zoffsets[ch],
                                       min_val=-3.0,
                                       max_val=3.0,
                                       increment=.1,
                                       digits=2,
                                       name='',
                                       size=(95,-1)) 
               
            if ch is settings.channels[0]:
                RadBut = wx.RadioButton(self,-1,'',style=wx.RB_GROUP)
            else:
                RadBut = wx.RadioButton(self,-1,'')
            if ch == settings.map_chan:
                RadBut.SetValue(True)
                
            gridSizer.Add(Txt,0,flag=wx.ALL|wx.EXPAND,border=5)
            gridSizer.Add(ProtText,1,flag=wx.ALL|wx.EXPAND,border=5)
            gridSizer.Add(ChBox,0,flag=wx.ALL|wx.EXPAND,border=5)
            gridSizer.Add(IntCtrl,0,border=5)
            gridSizer.Add(RadBut,0,flag=wx.ALL|wx.EXPAND,border=5)
            gridSizer.Add(FloatCtrl,0,flag=wx.ALL|wx.EXPAND,border=5)
            
            self.ProtNameCtrls.append(ProtText)
            self.UseCtrls.append(ChBox)
            self.ExposureCtrls.append(IntCtrl)
            self.MapRadCtrls.append(RadBut)
            self.ZOffCtrls.append(FloatCtrl)
        
           
        hbox = wx.BoxSizer(wx.HORIZONTAL)      
        ok_button = wx.Button(self,wx.ID_OK,'OK')
        cancel_button = wx.Button(self,wx.ID_CANCEL,'Cancel')
        hbox.Add(ok_button)
        hbox.Add(cancel_button)
        
        vbox.Add(gridSizer)
        vbox.Add(hbox)
        
        self.SetSizer(vbox)
    
        
    def GetSettings(self):
        prot_names=dict([])
        usechannels=dict([])
        exposure_times=dict([])
        zoffsets=dict([])
        
        for i,ch in enumerate(self.settings.channels):
            prot_names[ch]=self.ProtNameCtrls[i].GetValue()
            usechannels[ch]=self.UseCtrls[i].GetValue()
            exposure_times[ch]=self.ExposureCtrls[i].GetValue()
            if self.MapRadCtrls[i].GetValue():
                map_chan=ch
            zoffsets[ch]=self.ZOffCtrls[i].GetValue()
        return ChannelSettings(self.settings.channels,exposure_times=exposure_times,zoffsets=zoffsets,usechannels=usechannels,prot_names=prot_names,map_chan=map_chan)
        
 
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
        cfg['MosaicSettings']['mosaic_mag']=self.mag
        cfg['MosaicSettings']['mosaic_mx']=self.mx
        cfg['MosaicSettings']['mosaic_my']=self.my
        cfg['MosaicSettings']['mosaic_overlap']=self.overlap
        cfg['MosaicSettings']['mosaic_show_box']=self.show_box
        cfg['MosaicSettings']['mosaic_show_frames']=self.show_frames
        
    def load_settings(self,cfg):
        self.mag=cfg['MosaicSettings']['mosaic_mag']
        self.mx=cfg['MosaicSettings']['mosaic_mx']
        self.my=cfg['MosaicSettings']['mosaic_my']
        self.overlap=cfg['MosaicSettings']['mosaic_overlap']
        self.show_box=cfg['MosaicSettings']['mosaic_show_box']
        self.show_frames=cfg['MosaicSettings']['mosaic_show_frames']
        
  
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
        cfg['SmartSEMSettings']['SEM_mag']=self.mag
        cfg['SmartSEMSettings']['SEM_tilt']=self.tilt
        cfg['SmartSEMSettings']['SEM_rot']=self.rot
        cfg['SmartSEMSettings']['SEM_Z']=self.Z
        cfg['SmartSEMSettings']['SEM_WD']=self.WD
    def load_settings(self,cfg):
        self.mag=cfg['SmartSEMSettings']['SEM_mag']
        self.tilt=cfg['SmartSEMSettings']['SEM_tilt']
        self.rot=cfg['SmartSEMSettings']['SEM_rot']
        self.Z=cfg['SmartSEMSettings']['SEM_Z']
        self.WD=cfg['SmartSEMSettings']['SEM_WD']

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
                                     