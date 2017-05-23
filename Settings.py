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
import os
import json
import marshmallow as mm

class DirectorySettings():

    def __init__(self,Sample_ID = None, Ribbon_ID = None, Session_ID = None,Map_num= None,Slot_num = None,default_path = None,meta_experiment_name = None ):

        self.default_path = default_path
        self.Sample_ID = Sample_ID
        self.Ribbon_ID = Ribbon_ID
        self.Session_ID = Session_ID
        self.Slot_num = Slot_num
        self.Map_num = Map_num
        self.meta_experiment_name = meta_experiment_name



    def save_settings(self,cfg):
        cfg['Directories']['Sample_ID'] = self.Sample_ID
        cfg['Directories']['Ribbon_ID'] = self.Ribbon_ID
        cfg['Directories']['Session_ID'] = self.Session_ID
        cfg['Directories']['Map_num'] = self.Map_num
        cfg['Directories']['Default_Path'] = self.default_path
        cfg['Directories']['Slot_num'] = self.Slot_num
        cfg['Directories']['meta_experiment_name'] = self.meta_experiment_name
        cfg.write()

    def load_settings(self,cfg):
        self.default_path = cfg['Directories']['Default_Path']
        self.Sample_ID = cfg['Directories']['Sample_ID']
        self.Ribbon_ID = cfg['Directories']['Ribbon_ID']
        self.Session_ID = cfg['Directories']['Session_ID']
        self.Map_num = cfg['Directories']['Map_num']
        self.Slot_num = cfg['Directories']['Slot_num']
        self.meta_experiment_name = cfg['Directories']['meta_experiment_name']

    def create_directory(self,cfg,kind):
        root = self.default_path
        print 'root:', root
        if kind == 'map':
            map_folder = os.path.join(root,self.Sample_ID,'raw','map','Ribbon%04d'%self.Ribbon_ID,'map%01d'%self.Map_num)
            if not os.path.exists(map_folder):
                os.makedirs(map_folder)
                cfg['MosaicPlanner']['default_imagepath'] = map_folder
                # return map_folder
            else:
                # return map_folder
                cfg['MosaicPlanner']['default_imagepath'] = map_folder
        elif kind == 'data':
            data_folder = os.path.join(root,self.Sample_ID,'raw','data','Ribbon%04d'%self.Ribbon_ID,'session%02d'%self.Session_ID)
            if not os.path.exists(data_folder):
                os.makedirs(data_folder)
                return data_folder
            else:
                dlg = wx.MessageDialog(None,message = "Path already exists! Do you wish to continue?",caption = "Directory Warning",style = wx.YES|wx.NO)
                button_pressed = dlg.ShowModal()
                if button_pressed == wx.ID_YES:
                    return data_folder
                elif button_pressed == wx.ID_NO:
                    box = wx.MessageDialog(None,message = 'Aborting Acquisition')
                    box.ShowModal()
                    box.Destroy()
                    return None
        elif kind == 'multi_map':
            map_folder = os.path.join(root,self.Sample_ID,'raw','map','multi_ribbon_round','map%02d'%self.Map_num)
            if not os.path.exists(map_folder):
                os.makedirs(map_folder)
                cfg['MosaicPlanner']['default_imagepath'] = map_folder
            else:
                cfg['MosaicPlanner']['default_imagepath'] = map_folder
        else:
            dlg = wx.MessageBox(self,caption = 'Error',message = "Directory must be either \'map\' or \'data\' \n Aborting Acquisition")
            return None


class RibbonNumberDialog(wx.Dialog):
    def __init__(self,parent,id,style,title = "Enter Number of Ribbons"):
        wx.Dialog.__init__(self,parent,id,title,style = wx.DEFAULT_DIALOG_STYLE, size = (200,75))
        vbox = wx.BoxSizer(wx.VERTICAL)

        self.RibbonNum_txt = wx.StaticText(self,label = "Number of Ribbons:")
        self.RibbonNum_IntCtrl = wx.lib.intctrl.IntCtrl(self,value = 1, min = 1, max = None, allow_none = False)

        ok_button = wx.Button(self,wx.ID_OK,'OK')
        cancel_button = wx.Button(self,wx.ID_CANCEL,'Cancel')
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(self.RibbonNum_txt)
        hbox1.Add(self.RibbonNum_IntCtrl)
        hbox2.Add(ok_button)
        hbox2.Add(cancel_button)
        vbox.Add(hbox1)
        vbox.Add(hbox2)
        self.SetSizer(vbox)

    def GetValue(self):
        val = self.RibbonNum_IntCtrl.GetValue()
        return val




class ChangeDirectorySettings(wx.Dialog):
    def __init__(self,parent, id,style, title="Enter Sample Information",settings = DirectorySettings()):
        wx.Dialog.__init__(self, parent, id, title, style= wx.DEFAULT_DIALOG_STYLE, size= (440,-1),)
        vbox = wx.BoxSizer(wx.VERTICAL)
        # self.settings = settings

        self.MetaExp_txt = wx.StaticText(self,label = 'Meta Experiment Name:')
        self.MetaExp_Ctrl = wx.TextCtrl(self,value = settings.meta_experiment_name)

        self.RootDir_txt = wx.StaticText(self,label = 'Data Directory:')
        self.RootDir_Ctrl = wx.DirPickerCtrl(self,path=settings.default_path)

        self.SampleID_txt = wx.StaticText(self, label = "Sample ID:")
        self.SampleID_Ctrl = wx.TextCtrl(self,value=settings.Sample_ID)

        self.Ribbon_txt = wx.StaticText(self, label= "Ribbon Number:")
        self.RibbonInt_Ctrl = wx.lib.intctrl.IntCtrl(self,value = settings.Ribbon_ID, min = 0, max = None, allow_none = False)

        self.Session_txt = wx.StaticText(self,label = "Session Number:")
        self.SessionInt_Ctrl = wx.lib.intctrl.IntCtrl(self,value = settings.Session_ID, min=0, max = None, allow_none = False)

        self.Map_txt = wx.StaticText(self,label = "Map Number:")
        self.MapInt_Ctrl = wx.lib.intctrl.IntCtrl(self,value = settings.Map_num, min = 0 , max = None, allow_none = False)

        self.Slot_txt = wx.StaticText(self,label = "Slot Number:")
        self.SlotInt_Ctrl = wx.lib.intctrl.IntCtrl(self, value = settings.Slot_num, min = 0, max = 7, allow_none = False)


        ok_button = wx.Button(self,wx.ID_OK,'OK')
        cancel_button = wx.Button(self,wx.ID_CANCEL,'Cancel')
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        hbox4 = wx.BoxSizer(wx.HORIZONTAL)
        hbox5 = wx.BoxSizer(wx.HORIZONTAL)
        hbox6 = wx.BoxSizer(wx.HORIZONTAL)
        hbox7 = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.MetaExp_txt)
        hbox.Add(self.MetaExp_Ctrl)
        hbox1.Add(self.RootDir_txt)
        hbox1.Add(self.RootDir_Ctrl)
        hbox2.Add(self.SampleID_txt)
        hbox2.Add(self.SampleID_Ctrl)
        hbox3.Add(self.Ribbon_txt)
        hbox3.Add(self.RibbonInt_Ctrl)
        hbox4.Add(self.Session_txt)
        hbox4.Add(self.SessionInt_Ctrl)
        hbox5.Add(self.Map_txt)
        hbox5.Add(self.MapInt_Ctrl)
        hbox6.Add(self.Slot_txt)
        hbox6.Add(self.SlotInt_Ctrl)
        hbox7.Add(ok_button)
        hbox7.Add(cancel_button)
        vbox.Add(hbox)
        vbox.Add(hbox1)
        vbox.Add(hbox2)
        vbox.Add(hbox3)
        vbox.Add(hbox4)
        vbox.Add(hbox5)
        vbox.Add(hbox6)
        vbox.Add(hbox7)
        self.SetSizer(vbox)

    def get_settings(self):

        Ribbon_ID = self.RibbonInt_Ctrl.GetValue() # insures the ribbon ID that is passed is of the form Ribbon0000
        Session_ID = self.SessionInt_Ctrl.GetValue()
        Sample_ID = self.SampleID_Ctrl.GetValue()
        Map_num = self.MapInt_Ctrl.GetValue()
        Slot_num = self.SlotInt_Ctrl.GetValue()
        Default_Path = self.RootDir_Ctrl.GetPath()
        meta_experiment_name = self.MetaExp_Ctrl.GetValue()
        return DirectorySettings(Sample_ID,Ribbon_ID,Session_ID,Map_num,Slot_num,Default_Path,meta_experiment_name)







class ZstackSettings():

    def __init__(self,zstack_delta = 1.0, zstack_number = 3.0, zstack_flag = True):
        self.zstack_flag = zstack_flag
        self.zstack_delta = zstack_delta
        self.zstack_number = int(zstack_number + (1 - zstack_number % 2))

    def save_settings(self,cfg):
        cfg['ZStackSettings']['zstack_delta']=self.zstack_delta
        cfg['ZStackSettings']['zstack_flag']=self.zstack_flag
        cfg['ZStackSettings']['zstack_number']=self.zstack_number
        cfg.write()

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
        cfg.write()
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
        cfg.write()

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
        
class CameraSettingsSchema(mm.Schema):
    sensor_height = mm.fields.Int(required=True)
    sensor_widht = mm.fields.Int(required=True)
    pix_width = mm.fields.Float(required=True)
    pix_height = mm.fields.Float(required=True)

class CameraSettings():
    """simple struct for containing the parameters for the camera"""
    def __init__(self,sensor_height=1040,sensor_width=1388,pix_width=6.5,pix_height=6.5):
        #in pixels        
        self.sensor_height=sensor_height
        self.sensor_width=sensor_width
        #in microns
        self.pix_width=pix_width
        self.pix_height=pix_height
    def to_dict(self):
        d={'sensor_height':self.sensor_height,
           'sensor_width':self.sensor_width,
           'pix_width':self.pix_width,
           'pix_height':self.pix_height
        }
        
    def save_settings(self,cfg):
        cfg['Camera_Settings']['sensor_height']=self.sensor_height
        cfg['Camera_Settings']['sensor_width']=self.sensor_width
        cfg['Camera_Settings']['pix_width']=self.pix_width
        cfg['Camera_Settings']['pix_height']=self.pix_height
        cfg.write()
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
        cfg.write()

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
        wx.Dialog.__init__(self, parent, id, title,style=wx.DEFAULT_DIALOG_STYLE, size=(420, 600))
        
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
        with open('ChannelSettings.json') as protein_file:
            self.ProteinSelection = json.load(protein_file)
        for ch in settings.channels:
            hbox =wx.BoxSizer(wx.HORIZONTAL)
            Txt=wx.StaticText(self,label=ch)
            ChBox = wx.CheckBox(self)
            ChBox.SetValue(settings.usechannels[ch])
            print settings.prot_names[ch]
            if 'dapi' in ch.lower():
                ProtComboBox=wx.ComboBox(self,choices=self.ProteinSelection['QuadBand0DAPI'], style = wx.CB_SORT)
            else:
                ProtComboBox=wx.ComboBox(self,choices=self.ProteinSelection['Proteins'], style = wx.CB_SORT)
            if ChBox.GetValue():
                ProtComboBox.SetValue(settings.prot_names[ch])



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
            gridSizer.Add(ProtComboBox,1,flag=wx.ALL|wx.EXPAND,border=5)
            gridSizer.Add(ChBox,0,flag=wx.ALL|wx.EXPAND,border=5)
            gridSizer.Add(IntCtrl,0,border=5)
            gridSizer.Add(RadBut,0,flag=wx.ALL|wx.EXPAND,border=5)
            gridSizer.Add(FloatCtrl,0,flag=wx.ALL|wx.EXPAND,border=5)
            
            self.ProtNameCtrls.append(ProtComboBox)
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
        print self.settings.channels
        for i,ch in enumerate(self.settings.channels):
            prot_names[ch]=self.ProtNameCtrls[i].GetValue()
            if (prot_names[ch] not in self.ProteinSelection['QuadBand0DAPI']) and (prot_names[ch] not in self.ProteinSelection['Proteins']):
               if 'dapi' in prot_names[ch].lower():
                   self.ProteinSelection['QuadBand0DAPI'].append(prot_names[ch])
               else:
                   self.ProteinSelection['Proteins'].append(prot_names[ch])
               with open('ChannelSettings.json','w') as protein_file:
                   json.dump(self.ProteinSelection, protein_file)
            usechannels[ch]=self.UseCtrls[i].GetValue()
            exposure_times[ch]=self.ExposureCtrls[i].GetValue()
            if self.MapRadCtrls[i].GetValue():
                map_chan=ch
            zoffsets[ch]=self.ZOffCtrls[i].GetValue()
        return ChannelSettings(self.settings.channels,exposure_times=exposure_times,zoffsets=zoffsets,usechannels=usechannels,prot_names=prot_names,map_chan=map_chan)
        
class MosaicSettingsSchema(mm.Schema):
    mx = mm.fields.Int(required=True)
    my = mm.fields.Int(required=True)
    overlap = mm.fields.Int(required=True)
    show_box = mm.fields.Bool(required=True)
    mag = mm.fields.Float(required=True)

class MosaicSettings:
    def __init__(self,mag=65.486,mx=1,my=1,overlap=20,show_box=False,show_frames=False):
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
        cfg.write()

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
        cfg.write()

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

class MultiRibbonSettings(wx.Dialog): #MultiRibbons
    """dialog for setting multiribbon aquisition"""
    def __init__(self, parent, id, ribbon_number,slot_labels, title, settings,style):
        wx.Dialog.__init__(self, parent, id, title,style=wx.DEFAULT_DIALOG_STYLE, size=(1000, 300))

        vbox = wx.BoxSizer(wx.VERTICAL)
        gridSizer=wx.FlexGridSizer(rows=9,cols=3,vgap=5,hgap=5)
        gridSizer.Add(wx.StaticText(self,id=wx.ID_ANY,label="slot#"),border=5)
        gridSizer.Add(wx.StaticText(self,id=wx.ID_ANY,label="array file"),border=5)
        gridSizer.Add(wx.StaticText(self,id=wx.ID_ANY,label=" "),border=5)

        self.ribbon_number = ribbon_number
        self.slot_labels = slot_labels
        self.RibbonFilePath = []
        self.ToImageList = []
        for i in range(self.ribbon_number):
            self.ribbon_label=wx.StaticText(self,id=wx.ID_ANY,label=slot_labels[i])
            self.ribbon_load_button=wx.Button(self,id=wx.ID_ANY,label=" ",name="load button")
            self.ribbon_filepicker=wx.FilePickerCtrl(self,message='Select an array file',\
            path="",name='arrayFilePickerCtrl1',\
            style=wx.FLP_USE_TEXTCTRL, size=wx.Size(800,20),wildcard='*.*')
            gridSizer.Add(self.ribbon_label,0,wx.EXPAND,border=5)
            gridSizer.Add(self.ribbon_filepicker,1,wx.EXPAND,border=5)
            gridSizer.Add(self.ribbon_load_button,0,wx.EXPAND,border=5)
            self.RibbonFilePath.append(self.ribbon_filepicker)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        ok_button = wx.Button(self,wx.ID_OK,'OK')
        cancel_button = wx.Button(self,wx.ID_CANCEL,'Cancel')
        hbox.Add(ok_button)
        hbox.Add(cancel_button)

        vbox.Add(gridSizer)
        vbox.Add(hbox)

        self.SetSizer(vbox)

    def GetSettings(self):
        #pathway=dict([])
        pathway=[]
        for i in range(self.ribbon_number):
            #pathway[i]=self.RibbonFilePath[i].GetPath()
            newpath=self.RibbonFilePath[i].GetPath()
            pathway.append(newpath)
            print 'new path length:', len(newpath)
            if len(newpath) == 0:
                self.ToImageList.append(False)
            else:
                self.ToImageList.append(True)

        return pathway, self.ToImageList
