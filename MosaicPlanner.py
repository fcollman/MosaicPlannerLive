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


if __name__ == "__main__":
    import wx
    import wx.lib.intctrl
    import faulthandler
    from pyqtgraph.Qt import QtCore, QtGui

    from Transform import Transform,ChangeTransform
    from MosaicPanel import MosaicPanel

    from Settings import (MosaicSettings, CameraSettings,SiftSettings,ChangeCameraSettings, ImageSettings,
                       ChangeImageMetadata, SmartSEMSettings, ChangeSEMSettings, ChannelSettings,
                       ChangeChannelSettings, ChangeSiftSettings, CorrSettings,ChangeCorrSettings,
                      ChangeZstackSettings, ZstackSettings,)
    from configobj import ConfigObj
import jsonpickle
from validate import Validator
# import SaveQueue
SETTINGS_FILE = 'MosaicPlannerSettings.cfg'
VALIDATOR_FILE = 'MosaicPlannerSettingsModel.cfg'

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import SQLModels

class ZVISelectFrame(wx.Frame):
    """class extending wx.Frame for highest level handling of GUI components """
    ID_RELATIVEMOTION = wx.NewId()
    ID_EDIT_CAMERA_SETTINGS = wx.NewId()
    ID_EDIT_SMARTSEM_SETTINGS = wx.NewId()
    ID_SORTPOINTS = wx.NewId()
    ID_SHOWNUMBERS = wx.NewId()
    ID_SAVETRANSFORM = wx.NewId()
    ID_EDITTRANSFORM = wx.NewId()
    ID_FLIPVERT = wx.NewId()
    #ID_FULLRES = wx.NewId()
    ID_SAVE_SETTINGS = wx.NewId()
    ID_EDIT_CHANNELS = wx.NewId()
    ID_EDIT_MM_CONFIG = wx.NewId()
    ID_EDIT_SIFT = wx.NewId()
    ID_MM_PROP_BROWSER = wx.NewId()
    ID_EDIT_CORR = wx.NewId()
    ID_EDIT_FOCUS_CORRECTION = wx.NewId()
    ID_USE_FOCUS_CORRECTION = wx.NewId()
    ID_TRANSPOSE_XY = wx.NewId()
    ID_EDIT_ZSTACK = wx.NewId()
    ID_ASIAUTOFOCUS = wx.NewId()

    # ID_Alfred = wx.NewId()

    def __init__(self, parent, title):
        """default init function for a wx.Frame

        keywords:
        parent)parent window to associate it with
        title) title of the

        """
        #default metadata info and image file, remove for release
        #default_meta=""
        #default_image=""

        #recursively call old init function
        wx.Frame.__init__(self, parent, title=title, size=(1550,885),pos=(5,5))
        self.cfg = ConfigObj(SETTINGS_FILE,unrepr=True)
        #val = Validator()
        #test = self.cfg.validate(val)
        #if test == True:
        #    print "config file validated"
        #else:
        #    print "error in validation"

        #self.cfg = wx.Config('settings')
        #setup a mosaic panel
        self.mosaicPanel=MosaicPanel(self, config=self.cfg)

        #setup menu
        menubar = wx.MenuBar()
        options = wx.Menu()
        transformMenu = wx.Menu()
        Platform_Menu = wx.Menu()
        Imaging_Menu = wx.Menu()

        #OPTIONS MENU
        self.relative_motion = options.Append(self.ID_RELATIVEMOTION, 'Relative motion?', 'Move points in the ribbon relative to the apparent curvature, else in absolution coordinates',kind=wx.ITEM_CHECK)
        self.sort_points = options.Append(self.ID_SORTPOINTS,'Sort positions?','Should the program automatically sort the positions by their X coordinate from right to left?',kind=wx.ITEM_CHECK)
        self.show_numbers = options.Append(self.ID_SHOWNUMBERS,'Show numbers?','Display a number next to each position to show the ordering',kind=wx.ITEM_CHECK)
        self.flipvert = options.Append(self.ID_FLIPVERT,'Flip Image Vertically?','Display the image flipped vertically relative to the way it was meant to be displayed',kind=wx.ITEM_CHECK)
        #self.fullResOpt = options.Append(self.ID_FULLRES,'Load full resolution (speed vs memory)','Rather than loading a 10x downsampled ',kind=wx.ITEM_CHECK)
        self.saveSettings = options.Append(self.ID_SAVE_SETTINGS,'Save Settings','Saves current configuration settings to config file that will be loaded automatically',kind=wx.ITEM_NORMAL)
        self.transpose_xy = options.Append(self.ID_TRANSPOSE_XY,'Transpose XY','Flips the x,y display so the vertical ribbons run horizontally',kind=wx.ITEM_CHECK)


        #options.Check(self.ID_FULLRES,self.cfg.ReadBool('fullres',False))

        self.edit_transform_option = options.Append(self.ID_EDIT_CAMERA_SETTINGS,'Edit Camera Properties...','Edit the size of the camera chip and the pixel size',kind=wx.ITEM_NORMAL)

        #SETUP THE CALLBACKS
        self.Bind(wx.EVT_MENU, self.save_settings, id=self.ID_SAVE_SETTINGS)
        self.Bind(wx.EVT_MENU, self.toggle_relative_motion, id=self.ID_RELATIVEMOTION)
        self.Bind(wx.EVT_MENU, self.toggle_sort_option, id=self.ID_SORTPOINTS)
        self.Bind(wx.EVT_MENU, self.toggle_show_numbers,id=self.ID_SHOWNUMBERS)
        self.Bind(wx.EVT_MENU, self.edit_camera_settings, id=self.ID_EDIT_CAMERA_SETTINGS)
        self.Bind(wx.EVT_MENU, self.toggle_transpose_xy, id = self.ID_TRANSPOSE_XY)


        #SET THE INTIAL SETTINGS

        options.Check(self.ID_RELATIVEMOTION,self.cfg['MosaicPlanner']['relativemotion'])
        options.Check(self.ID_SORTPOINTS,True)
        options.Check(self.ID_SHOWNUMBERS,False)
        options.Check(self.ID_FLIPVERT,self.cfg['MosaicPlanner']['flipvert'])
        options.Check(self.ID_TRANSPOSE_XY,self.cfg['MosaicPlanner']['transposexy'])
        self.toggle_transpose_xy()
        #TRANSFORM MENU
        self.save_transformed = transformMenu.Append(self.ID_SAVETRANSFORM,'Save Transformed?',\
        'Rather than save the coordinates in the original space, save a transformed set of coordinates according to transform configured in set_transform...',kind=wx.ITEM_CHECK)
        transformMenu.Check(self.ID_SAVETRANSFORM,self.cfg['MosaicPlanner']['savetransform'])

        self.edit_camera_settings = transformMenu.Append(self.ID_EDITTRANSFORM,'Edit Transform...',\
        'Edit the transform used to save transformed coordinates, by setting corresponding points and fitting a model',kind=wx.ITEM_NORMAL)

        self.Bind(wx.EVT_MENU, self.edit_transform, id=self.ID_EDITTRANSFORM)
        self.Transform = Transform()
        self.Transform.load_settings(self.cfg)

        #PLATFORM MENU
        self.edit_smartsem_settings = Platform_Menu.Append(self.ID_EDIT_SMARTSEM_SETTINGS,'Edit SmartSEMSettings',\
        'Edit the settings used to set the magnification, rotation,tilt, Z position, and working distance of SEM software in position list',kind=wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.edit_smart_SEM_settings, id=self.ID_EDIT_SMARTSEM_SETTINGS)

        #IMAGING SETTINGS MENU
        self.edit_micromanager_config = Imaging_Menu.Append(self.ID_EDIT_MM_CONFIG,'Set MicroManager Configuration',kind=wx.ITEM_NORMAL)
        self.edit_zstack_settings = Imaging_Menu.Append(self.ID_EDIT_ZSTACK,'Edit Zstack settings', kind = wx.ITEM_NORMAL)
        self.edit_channels = Imaging_Menu.Append(self.ID_EDIT_CHANNELS,'Edit Channels',kind=wx.ITEM_NORMAL)
        self.edit_SIFT_settings = Imaging_Menu.Append(self.ID_EDIT_SIFT, 'Edit SIFT settings',kind=wx.ITEM_NORMAL)
        self.edit_CORR_settings = Imaging_Menu.Append(self.ID_EDIT_CORR,'Edit corr_tool settings',kind=wx.ITEM_NORMAL)
        self.launch_MM_PropBrowser = Imaging_Menu.Append(self.ID_MM_PROP_BROWSER,'Open MicroManager Property Browser',kind = wx.ITEM_NORMAL)
        self.focus_correction_plane = Imaging_Menu.Append(self.ID_EDIT_FOCUS_CORRECTION,'Edit Focus Correction Plane',kind = wx.ITEM_NORMAL)
        self.use_focus_correction = Imaging_Menu.Append(self.ID_USE_FOCUS_CORRECTION,'Use Focus Correction?','Use Focus Correction For Mapping',kind=wx.ITEM_CHECK)
        self.launch_ASIControl = Imaging_Menu.Append(self.ID_ASIAUTOFOCUS, 'Allen ASI AutoFocus Control', kind= wx.ITEM_NORMAL)


        self.Bind(wx.EVT_MENU, self.toggle_use_focus_correction,id=self.ID_USE_FOCUS_CORRECTION)
        self.Bind(wx.EVT_MENU, self.mosaicPanel.edit_Zstack_settings, id=self.ID_EDIT_ZSTACK)
        self.Bind(wx.EVT_MENU, self.mosaicPanel.edit_MManager_config, id = self.ID_EDIT_MM_CONFIG)
        self.Bind(wx.EVT_MENU, self.mosaicPanel.edit_channels, id = self.ID_EDIT_CHANNELS)
        self.Bind(wx.EVT_MENU, self.mosaicPanel.edit_SIFT_settings, id = self.ID_EDIT_SIFT)
        self.Bind(wx.EVT_MENU, self.mosaicPanel.edit_corr_settings, id = self.ID_EDIT_CORR)
        self.Bind(wx.EVT_MENU, self.mosaicPanel.launch_MManager_browser, id = self.ID_MM_PROP_BROWSER)
        self.Bind(wx.EVT_MENU, self.mosaicPanel.edit_focus_correction_plane, id = self.ID_EDIT_FOCUS_CORRECTION)
        self.Bind(wx.EVT_MENU, self.mosaicPanel.launch_ASI, id = self.ID_ASIAUTOFOCUS)

        Imaging_Menu.Check(self.ID_USE_FOCUS_CORRECTION,self.cfg['MosaicPlanner']['use_focus_correction'])

        menubar.Append(options, '&Options')
        menubar.Append(transformMenu,'&Transform')
        menubar.Append(Platform_Menu,'&Platform Options')
        menubar.Append(Imaging_Menu,'&Imaging Settings')
        self.SetMenuBar(menubar)

        #setup a file picker for the metadata selector
        #self.meta_label=wx.StaticText(self,id=wx.ID_ANY,label="metadata file")
        #self.meta_filepicker=wx.FilePickerCtrl(self,message='Select a metadata file',\
        #path="",name='metadataFilePickerCtrl1',\
        #style=wx.FLP_USE_TEXTCTRL, size=wx.Size(300,20),wildcard='*.*')
        #self.meta_filepicker.SetPath(self.cfg.Read('default_metadatapath',""))
        #self.meta_formatBox=wx.ComboBox(self,id=wx.ID_ANY,value='ZeissXML',\
        #size=wx.DefaultSize,choices=['ZVI','ZeissXML','SimpleCSV','ZeissCZI'], name='File Format For Meta Data')
        #self.meta_formatBox.SetEditable(False)
        #self.meta_load_button=wx.Button(self,id=wx.ID_ANY,label="Load",name="metadata load")
        #self.meta_enter_button=wx.Button(self,id=wx.ID_ANY,label="Edit",name="manual meta")

        #define the image file picker components
        self.imgCollectLabel=wx.StaticText(self,id=wx.ID_ANY,label="image collection directory")
        self.imgCollectDirPicker=wx.DirPickerCtrl(self,message='Select a directory to store images',\
        path="",name='imgCollectPickerCtrl1',\
        style=wx.FLP_USE_TEXTCTRL, size=wx.Size(300,20))
        self.imgCollectDirPicker.SetPath(self.cfg['MosaicPlanner']['default_imagepath'])
        self.imgCollect_load_button=wx.Button(self,id=wx.ID_ANY,label="Load",name="imgCollect load")

        #wire up the button to the "on_load" button
        self.Bind(wx.EVT_BUTTON, self.on_image_collect_load,self.imgCollect_load_button)
        #self.Bind(wx.EVT_BUTTON, self.OnMetaLoad,self.meta_load_button)
        #self.Bind(wx.EVT_BUTTON, self.OnEditImageMetadata,self.meta_enter_button)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        #define the array picker components
        self.array_label=wx.StaticText(self,id=wx.ID_ANY,label="array file")
        self.array_filepicker=wx.FilePickerCtrl(self,message='Select an array file',\
        path="",name='arrayFilePickerCtrl1',\
        style=wx.FLP_USE_TEXTCTRL, size=wx.Size(300,20),wildcard='*.*')
        self.array_filepicker.SetPath(self.cfg['MosaicPlanner']['default_arraypath'])

        self.array_load_button=wx.Button(self,id=wx.ID_ANY,label="Load",name="load button")
        self.array_formatBox=wx.ComboBox(self,id=wx.ID_ANY,value='AxioVision',\
        size=wx.DefaultSize,choices=['uManager','AxioVision','SmartSEM','OMX','ZEN'], name='File Format For Position List')
        self.array_formatBox.SetEditable(False)
        self.array_save_button=wx.Button(self,id=wx.ID_ANY,label="Save",name="save button")
        self.array_saveframes_button=wx.Button(self,id=wx.ID_ANY,label="Save Frames",name="save-frames button")

        #wire up the button to the "on_load" button
        self.Bind(wx.EVT_BUTTON, self.on_array_load,self.array_load_button)
        self.Bind(wx.EVT_BUTTON, self.on_array_save,self.array_save_button)
        self.Bind(wx.EVT_BUTTON, self.on_array_save_frames,self.array_saveframes_button)

        #define a horizontal sizer for them and place the file picker components in there
        #self.meta_filepickersizer=wx.BoxSizer(wx.HORIZONTAL)
        #self.meta_filepickersizer.Add(self.meta_label,0,wx.EXPAND)
        #self.meta_filepickersizer.Add(self.meta_filepicker,1,wx.EXPAND)
        #self.meta_filepickersizer.Add(wx.StaticText(self,id=wx.ID_ANY,label="Metadata Format:"))
        #self.meta_filepickersizer.Add(self.meta_formatBox,0,wx.EXPAND)
        #self.meta_filepickersizer.Add(self.meta_load_button,0,wx.EXPAND)
        #self.meta_filepickersizer.Add(self.meta_enter_button,0,wx.EXPAND)

        #define a horizontal sizer for them and place the file picker components in there
        self.imgCollect_filepickersizer=wx.BoxSizer(wx.HORIZONTAL)
        self.imgCollect_filepickersizer.Add(self.imgCollectLabel,0,wx.EXPAND)
        self.imgCollect_filepickersizer.Add(self.imgCollectDirPicker,1,wx.EXPAND)
        self.imgCollect_filepickersizer.Add(self.imgCollect_load_button,0,wx.EXPAND)

        #define a horizontal sizer for them and place the file picker components in there
        self.array_filepickersizer=wx.BoxSizer(wx.HORIZONTAL)
        self.array_filepickersizer.Add(self.array_label,0,wx.EXPAND)
        self.array_filepickersizer.Add(self.array_filepicker,1,wx.EXPAND)
        self.array_filepickersizer.Add(wx.StaticText(self,id=wx.ID_ANY,label="Format:"))
        self.array_filepickersizer.Add(self.array_formatBox,0,wx.EXPAND)
        self.array_filepickersizer.Add(self.array_load_button,0,wx.EXPAND)
        self.array_filepickersizer.Add(self.array_save_button,0,wx.EXPAND)
        self.array_filepickersizer.Add(self.array_saveframes_button,0,wx.EXPAND)

        #define the overall vertical sizer for the frame
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        #place the filepickersizer into the vertical arrangement
        self.sizer.Add(self.imgCollect_filepickersizer,0,wx.EXPAND)
        #self.sizer.Add(self.meta_filepickersizer,0,wx.EXPAND)
        self.sizer.Add(self.array_filepickersizer,0,wx.EXPAND)
        self.sizer.Add(self.mosaicPanel.get_toolbar(), 0, wx.LEFT | wx.EXPAND)
        self.sizer.Add(self.mosaicPanel, 0, wx.EXPAND)

        #self.poslist_set=False
        #set the overall sizer and autofit everything
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_press)

        #self.sizer.Fit(self)
        self.Show(True)

        self.SmartSEMSettings=SmartSEMSettings()
        self.app = QtGui.QApplication([])
        #self.app.exec_()
        self.connect_database()
        new_experiment = SQLModels.Experiment(name="testing")

        session = self.Session()
        session.add(new_experiment)
        session.flush()
        session.commit()

        self.find_experiments()

    def find_experiments(self):

        session = self.Session()
        exps=session.query(SQLModels.Experiment)


    def connect_database(self):



        self.sql_engine = create_engine(self.cfg['SqlAlchemy']['database_path'])
        SQLModels.Base.metadata.create_all(self.sql_engine)

        self.Session = sessionmaker(bind=self.sql_engine)


        #self.OnImageLoad()
        #self.on_array_load()
        #self.mosaicCanvas.draw()
    def toggle_transpose_xy(self,evt=None):
        print "toggle called",self.transpose_xy.IsChecked()

        self.mosaicPanel.imgSrc.transpose_xy = self.transpose_xy.IsChecked()


    def save_settings(self,event="none"):
        #save the transform parameters



        self.Transform.save_settings(self.cfg)

        #save the menu options
        self.cfg['MosaicPlanner']['relativemotion']=self.relative_motion.IsChecked()
        #self.cfg.WriteBool('flipvert',self.flipvert.IsChecked())
        #self.cfg.WriteBool('fullres',self.fullResOpt.IsChecked())
        self.cfg['MosaicPlanner']['savetransform']=self.save_transformed.IsChecked()
        self.cfg['MosaicPlanner']['transposexy']=self.transpose_xy.IsChecked()
        #save the camera settings
        self.mosaicPanel.posList.camera_settings.save_settings(self.cfg)

        #save the mosaic options
        self.mosaicPanel.posList.mosaic_settings.save_settings(self.cfg)

        #save the SEMSettings
        self.SmartSEMSettings.save_settings(self.cfg)

        self.cfg['MosaicPlanner']['default_imagepath']=self.imgCollectDirPicker.GetPath()

        self.cfg['MosaicPlanner']['default_arraypath']=self.array_filepicker.GetPath()

        focal_pos_lis_string = self.mosaicPanel.focusCorrectionList.to_json()
        #jsonpickle.encode(self.mosaicPanel.focusCorrectionList)
        self.cfg['MosaicPlanner']["focal_pos_list_pickle"]=focal_pos_lis_string
        self.cfg.write()
        #with open(SETTINGS_FILE,'wb') as configfile:
        #    self.cfg.write(configfile)

    def on_key_press(self,event="none"):
        """forward the key press event to the mosaicCanvas handler"""
        mpos=wx.GetMousePosition()
        mcrect=self.mosaicPanel.GetScreenRect()
        if mcrect.Contains(mpos):
            self.mosaicPanel.on_key_press(event)
        else:
            event.Skip()

    def on_array_load(self,event="none"):
        """event handler for the array load button"""
        if self.array_formatBox.GetValue()=='AxioVision':
            self.mosaicPanel.posList.add_from_file(self.array_filepicker.GetPath())
        elif self.array_formatBox.GetValue()=='OMX':
            print "not yet implemented"
        elif self.array_formatBox.GetValue()=='SmartSEM':
            SEMsetting=self.mosaicPanel.posList.add_from_file_SmartSEM(self.array_filepicker.GetPath())
            self.SmartSEMSettings=SEMsetting
        elif self.array_formatBox.GetValue()=='ZEN':
            self.mosaicPanel.posList.add_from_file_ZEN(self.array_filepicker.GetPath())

        self.mosaicPanel.draw()

    def on_array_save(self,event):
        """event handler for the array save button"""
        if self.array_formatBox.GetValue()=='AxioVision':
            if self.save_transformed.IsChecked():
                self.mosaicPanel.posList.save_position_list(self.array_filepicker.GetPath(), trans=self.Transform)
            else:
                self.mosaicPanel.posList.save_position_list(self.array_filepicker.GetPath())
        elif self.array_formatBox.GetValue()=='OMX':
            if self.save_transformed.IsChecked():
                self.mosaicPanel.posList.save_position_list_OMX(self.array_filepicker.GetPath(), trans=self.Transform);
            else:
                self.mosaicPanel.posList.save_position_list_OMX(self.array_filepicker.GetPath(), trans=None);
        elif self.array_formatBox.GetValue()=='SmartSEM':
            if self.save_transformed.IsChecked():
                self.mosaicPanel.posList.save_position_list_SmartSEM(self.array_filepicker.GetPath(), SEMS=self.SmartSEMSettings, trans=self.Transform)
            else:
                self.mosaicPanel.posList.save_position_list_SmartSEM(self.array_filepicker.GetPath(), SEMS=self.SmartSEMSettings, trans=None)
        elif self.array_formatBox.GetValue()=='ZEN':
            if self.save_transformed.IsChecked():
                self.mosaicPanel.posList.save_position_list_ZENczsh(self.array_filepicker.GetPath(), trans=self.Transform, planePoints=self.planePoints)
            else:
                self.mosaicPanel.posList.save_position_list_ZENczsh(self.array_filepicker.GetPath(), trans=None, planePoints=self.planePoints)
        elif self.array_formatBox.GetValue()=='uManager':
            if self.save_transformed.IsChecked():
                self.mosaicPanel.posList.save_position_list_uM(self.array_filepicker.GetPath(), trans=self.Transform)
            else:
                self.mosaicPanel.posList.save_position_list_uM(self.array_filepicker.GetPath(), trans=None)

    def on_image_collect_load(self,event):
        path=self.imgCollectDirPicker.GetPath()
        self.mosaicPanel.on_load(path)

    def on_array_save_frames(self,event):
        if self.array_formatBox.GetValue()=='AxioVision':
            if self.save_transformed.IsChecked():
                self.mosaicPanel.posList.save_frame_list(self.array_filepicker.GetPath(), trans=self.Transform)
            else:
                self.mosaicPanel.posList.save_frame_list(self.array_filepicker.GetPath())
        elif self.array_formatBox.GetValue()=='OMX':
            if self.save_transformed.IsChecked():
                self.mosaicPanel.posList.save_frame_list_OMX(self.array_filepicker.GetPath(), trans=self.Transform);
            else:
                self.mosaicPanel.posList.save_frame_list_OMX(self.array_filepicker.GetPath(), trans=None);
        elif self.array_formatBox.GetValue()=='SmartSEM':
            if self.save_transformed.IsChecked():
                self.mosaicPanel.posList.save_frame_list_SmartSEM(self.array_filepicker.GetPath(), SEMS=self.SmartSEMSettings, trans=self.Transform)
            else:
                self.mosaicPanel.posList.save_frame_list_SmartSEM(self.array_filepicker.GetPath(), SEMS=self.SmartSEMSettings, trans=None)

    def toggle_relative_motion(self,event):
        """event handler for handling the toggling of the relative motion"""
        if self.relative_motion.IsChecked():
            self.mosaicPanel.relative_motion=(True)
        else:
            self.mosaicPanel.relative_motion=(False)

    def toggle_sort_option(self,event):
        """event handler for handling the toggling of the relative motion"""
        if self.sort_points.IsChecked():
            self.mosaicPanel.posList.dosort=(True)
        else:
            self.mosaicPanel.posList.dosort=(False)

    def toggle_use_focus_correction(self,event):
        """event handler for handling the toggling of using focus correction plane"""
        if self.use_focus_correction.IsChecked():
            "print use focus correction"
            self.mosaicPanel.imgSrc.use_focus_plane = True
        else:
            "print do not use focus correction"
            self.mosaicPanel.imgSrc.use_focus_plane = False

    def toggle_show_numbers(self,event):
        if self.show_numbers.IsChecked():
            self.mosaicPanel.posList.setNumberVisibility(True)
        else:
            self.mosaicPanel.posList.setNumberVisibility(False)
        self.mosaicPanel.draw()

    def edit_camera_settings(self,event):
        """event handler for clicking the camera setting menu button"""
        dlg = ChangeCameraSettings(None, -1,
                                   title="Camera Settings",
                                   settings=self.mosaicPanel.camera_settings)
        dlg.ShowModal()
        #del self.posList.camera_settings
        #passes the settings to the position list
        self.mosaicPanel.camera_settings=dlg.GetSettings()
        self.mosaicPanel.posList.set_camera_settings(dlg.GetSettings())
        dlg.Destroy()

    def edit_smart_SEM_settings(self,event):
        dlg = ChangeSEMSettings(None, -1,
                                   title="Smart SEM Settings",
                                   settings=self.SmartSEMSettings)
        dlg.ShowModal()
        del self.SmartSEMSettings
        #passes the settings to the position list
        self.SmartSEMSettings=dlg.GetSettings()
        dlg.Destroy()

    def edit_transform(self,event):
        """event handler for clicking the edit transform menu button"""
        dlg = ChangeTransform(None, -1,title="Adjust Transform")
        dlg.ShowModal()
        #passes the settings to the position list
        #(pts_from,pts_to,transformType,flipVert,flipHoriz)=dlg.GetTransformInfo()
        #print transformType

        self.Transform=dlg.getTransform()
        #for index,pt in enumerate(pts_from):
        #    (xp,yp)=self.Transform.transform(pt.x,pt.y)
        #    print("%5.5f,%5.5f -> %5.5f,%5.5f (%5.5f, %5.5f)"%(pt.x,pt.y,xp,yp,pts_to[index].x,pts_to[index].y))
        dlg.Destroy()

    def on_close(self,event):
        print "closing"

        self.mosaicPanel.handle_close()
        self.Destroy()

if __name__ == '__main__':
    #dirname=sys.argv[1]
    #print dirname
    faulthandler.enable()
    app = wx.App(False)
    # Create a new app, don't redirect stdout/stderr to a window.
    frame = ZVISelectFrame(None,"Mosaic Planner")
    # A Frame is a top-level window.
    app.MainLoop()
    QtGui.QApplication.quit()
