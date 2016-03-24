from Settings import (MosaicSettings, CameraSettings,SiftSettings,ChangeCameraSettings, ImageSettings,
                       ChangeImageMetadata, SmartSEMSettings, ChangeSEMSettings, ChannelSettings,
                       ChangeChannelSettings, ChangeSiftSettings, CorrSettings,ChangeCorrSettings,
                      ChangeZstackSettings, ZstackSettings,)
from NavigationToolBarImproved import NavigationToolbar2Wx_improved as NavBarImproved
import wx

class MosaicToolbar(NavBarImproved):
    """A custom toolbar which adds buttons and to interact with a MosaicPanel

    current installed buttons which, along with zoom/pan
    are in "at most one of group can be selected mode":
    selectnear: a cursor point
    select: a lasso like icon
    add: a cursor with a plus sign
    selectone: a cursor with a number 1
    selecttwo: a cursor with a number 2

    installed Simple tool buttons:
    deleteTool) calls self.canvas.OnDeleteSelected ID=ON_DELETE_SELECTED
    corrTool: a button that calls self.canvas.on_corr_tool ID=ON_CORR
    stepTool: a button that calls self.canvas.on_step_tool ID=ON_STEP
    ffTool: a button that calls on_fastforward_tool ID=ON_FF

    installed Toggle tool buttons:
    gridTool: a toggled button that calls self.canvas.on_grid_tool with the ID=ON_GRID
    rotateTool: a toggled button that calls self.canvas.on_rotate_tool with the ID=ON_ROTATE
    THESE SHOULD PROBABLY BE CHANGED TO BE MORE MODULAR IN ITS EFFECT AND NOT ASSUME SOMETHING
    ABOUT THE STRUCTURE OF self.canvas

    a set of controls for setting the parameters of a mosaic (see class MosaicSettings)
    the function getMosaicSettings will return an instance of MosaicSettings with the current settings from the controls
    the function self.canvas.posList.set_mosaic_settings(self.getMosaicSettings) will be called when the mosaic settings are changed
    the function self.canvas.posList.set_mosaic_visible(visible) will be called when the show? checkmark is click/unclick
    THIS SHOULD BE CHANGED TO BE MORE MODULAR IN ITS EFFECT

    note this will also call self.canvas.on_home_tool when the home button is pressed
    """
    # Set up class attributes
    ON_FIND = wx.NewId()
    ON_SELECT  = wx.NewId()
    ON_NEWPOINT = wx.NewId()
    ON_DELETE_SELECTED = wx.NewId()
    #ON_CORR_LEFT = wx.NewId()
    ON_STEP = wx.NewId()
    ON_FF = wx.NewId()
    ON_CORR = wx.NewId()
    ON_FINETUNE = wx.NewId()
    ON_GRID = wx.NewId()
    ON_ROTATE = wx.NewId()
    ON_REDRAW = wx.NewId()
    ON_LIVE_MODE = wx.NewId()
    MAGCHOICE = wx.NewId()
    SHOWMAG = wx.NewId()
    ON_ACQGRID = wx.NewId()
    ON_RUN = wx.NewId()
    ON_SNAP = wx.NewId()
    ON_CROP = wx.NewId()

    def __init__(self, plotCanvas):
        """
        plotCanvas: an instance of MosaicPanel which has the correct features (see class doc)

        """
        # call the init function of the class we inheriting from
        NavBarImproved.__init__(self, plotCanvas)
        wx.Log.SetLogLevel(0) # batman?

        #import the icons
        leftcorrBmp   = wx.ArtProvider.GetBitmap(wx.ART_GO_BACK, wx.ART_TOOLBAR)
        selectBmp     = wx.Image('icons/lasso-icon.png',   wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        addpointBmp   = wx.Image('icons/add-icon.bmp',     wx.BITMAP_TYPE_BMP).ConvertToBitmap()
        trashBmp      = wx.Image('icons/delete-icon.png',  wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        selectnearBmp = wx.Image('icons/cursor2-icon.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        oneBmp        = wx.Image('icons/one-icon.bmp',     wx.BITMAP_TYPE_BMP).ConvertToBitmap()
        twoBmp        = wx.Image('icons/two-icon.bmp',     wx.BITMAP_TYPE_BMP).ConvertToBitmap()
        stepBmp       = wx.Image('icons/step-icon.png',    wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        corrBmp       = wx.Image('icons/target-icon.png',  wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        ffBmp         = wx.Image('icons/ff-icon.png',      wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        rotateBmp     = wx.Image('icons/rotate-icon.png',  wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        gridBmp       = wx.Image('icons/grid-icon.png',    wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        cameraBmp     = wx.Image('icons/camera-icon.png',  wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        mosaicBmp     = wx.Image('icons/mosaic-icon.png',  wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        carBmp        = wx.Image('icons/car-icon.png',     wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        cropBmp       = wx.Image('icons/new/crop.png',     wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        snapBmp       = wx.Image('icons/new/snap.png',     wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        cameraBmp     = wx.Image('icons/new/camera.png',   wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        liveBmp       = wx.Image('icons/new/livemode.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        batmanBmp     = wx.Image('icons/new/batman.png',   wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        #mosaicBmp     = wx.Image('icons/new/mosaic_camera.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap()


        self.DeleteTool(self.wx_ids['Subplots']) # batman - what is this? add comment above it?

        #add the mutually exclusive/toggleable tools to the toolbar, see superclass for details on how function works
        self.moveHereTool    = self.add_user_tool('movehere',6,carBmp,True,'move scope here')
        self.snapHereTool    = self.add_user_tool('snaphere',7,cameraBmp,True,'move scope and snap image here')
        self.snapPictureTool = self.add_user_tool('snappic',8,mosaicBmp,True,'take 3x3 mosaic on click')
        self.selectNear      = self.add_user_tool('selectnear',9,selectnearBmp,True,'Add Nearest Point to selection')
        self.addTool         = self.add_user_tool('add', 10, addpointBmp, True, 'Add a Point')
        self.oneTool         = self.add_user_tool('selectone', 11, oneBmp, True, 'Choose pointLine2D 1')
        self.twoTool         = self.add_user_tool('selecttwo', 12, twoBmp, True, 'Choose pointLine2D 2')

        self.AddSeparator()
        self.AddSeparator() # batman - why called twice, why called at all!, maybe add comment?

        #add the simple button click tools
        self.liveModeTool = self.AddSimpleTool(self.ON_LIVE_MODE,liveBmp,'Enter Live Mode','liveMode')
        self.deleteTool   = self.AddSimpleTool(self.ON_DELETE_SELECTED,trashBmp,'Delete selected points','delete points')
        self.corrTool     = self.AddSimpleTool(self.ON_CORR,corrBmp,'Ajdust pointLine2D 2 with correlation','corrTool')
        self.stepTool     = self.AddSimpleTool(self.ON_STEP,stepBmp,'Take one step using points 1+2','stepTool')
        self.ffTool       = self.AddSimpleTool(self.ON_FF,ffBmp,'Auto-take steps till C<.3 or off image','fastforwardTool')
        self.snapNowTool  = self.AddSimpleTool(self.ON_SNAP,snapBmp,'Take a snap now','snapHereTool')
        self.onCropTool   = self.AddSimpleTool(self.ON_CROP,cropBmp,'Crop field of view','cropTool')

        #add the toggleable tools
        self.gridTool=self.AddCheckTool(self.ON_GRID,gridBmp,wx.NullBitmap,'toggle rotate boxes')
        self.rotateTool=self.AddCheckTool(self.ON_ROTATE,rotateBmp,wx.NullBitmap,'toggle rotate boxes')
        self.runAcqTool=self.AddSimpleTool(self.ON_RUN,batmanBmp,'Acquire AT Data','run_tool')

        #setup the controls for the mosaic
        self.showmagCheck = wx.CheckBox(self)
        self.showmagCheck.SetValue(False)
        self.magChoiceCtrl = wx.lib.agw.floatspin.FloatSpin(self,
                                                            size=(65, -1 ),
                                                            value=self.canvas.posList.mosaic_settings.mag,
                                                            min_val=0,
                                                            increment=.1,
                                                            digits=2,
                                                            name='magnification')
        self.mosaicXCtrl = wx.lib.intctrl.IntCtrl(self, value=1, size=(20, -1))
        self.mosaicYCtrl = wx.lib.intctrl.IntCtrl(self, value=1, size=(20, -1))
        self.overlapCtrl = wx.lib.intctrl.IntCtrl(self, value=10, size=(25, -1))

        #setup the controls for the min/max slider
        minstart=0
        maxstart=500
        self.slider = wx.Slider(self,value=250,minValue=minstart,maxValue=maxstart,size=( 180, -1),style = wx.SL_SELRANGE)
        self.sliderMaxCtrl = wx.lib.intctrl.IntCtrl( self, value=maxstart,size=( 60, -1 ))

        #add the control for the mosaic
        self.AddControl(wx.StaticText(self,label="Show Mosaic"))
        self.AddControl(self.showmagCheck)
        self.AddControl(wx.StaticText(self,label="Mag"))
        self.AddControl( self.magChoiceCtrl)
        self.AddControl(wx.StaticText(self,label="MosaicX"))
        self.AddControl(self.mosaicXCtrl)
        self.AddControl(wx.StaticText(self,label="MosaicY"))
        self.AddControl(self.mosaicYCtrl)
        self.AddControl(wx.StaticText(self,label="%Overlap"))
        self.AddControl(self.overlapCtrl)
        self.AddSeparator()
        self.AddControl(self.slider)
        self.AddControl(self.sliderMaxCtrl)

        #bind event handles for the various tools
        #this one i think is inherited... the zoom_tool function (- batman, resolution to thinking?)
        self.Bind(wx.EVT_TOOL, self.on_toggle_pan_zoom, self.zoom_tool)
        self.Bind(wx.EVT_CHECKBOX,self.toggle_mosaic_visible,self.showmagCheck)
        self.Bind( wx.lib.agw.floatspin.EVT_FLOATSPIN,self.update_mosaic_settings, self.magChoiceCtrl)
        self.Bind(wx.lib.intctrl.EVT_INT,self.update_mosaic_settings, self.mosaicXCtrl)
        self.Bind(wx.lib.intctrl.EVT_INT,self.update_mosaic_settings, self.mosaicYCtrl)
        self.Bind(wx.lib.intctrl.EVT_INT,self.update_mosaic_settings, self.overlapCtrl)

        #event binding for slider
        self.Bind(wx.EVT_SCROLL_THUMBRELEASE,self.canvas.on_slider_change,self.slider)
        self.Bind(wx.lib.intctrl.EVT_INT,self.updateSliderRange, self.sliderMaxCtrl)

        wx.EVT_TOOL(self, self.ON_LIVE_MODE, self.canvas.on_live_mode)
        wx.EVT_TOOL(self, self.ON_DELETE_SELECTED, self.canvas.on_delete_points)
        wx.EVT_TOOL(self, self.ON_CORR, self.canvas.on_corr_tool)
        wx.EVT_TOOL(self, self.ON_STEP, self.canvas.on_step_tool)
        wx.EVT_TOOL(self, self.ON_RUN, self.canvas.on_run_acq)
        wx.EVT_TOOL(self, self.ON_FF, self.canvas.on_fastforward_tool)
        wx.EVT_TOOL(self, self.ON_GRID, self.canvas.on_grid_tool)
        wx.EVT_TOOL(self, self.ON_ROTATE, self.canvas.on_rotate_tool)
        wx.EVT_TOOL(self, self.ON_SNAP, self.canvas.on_snap_tool)
        wx.EVT_TOOL(self, self.ON_CROP, self.canvas.on_crop_tool)

        self.Realize()

    def update_mosaic_settings(self, evt=""):
        """"update the mosaic_settings variables of the canvas and the posList of the canvas and redraw
        set_mosaic_settings should take care of what is necessary to replot the mosaic"""
        self.canvas.posList.set_mosaic_settings(self.get_mosaic_parameters())
        self.canvas.mosaic_settings = self.get_mosaic_parameters()
        self.canvas.draw()

    def updateSliderRange(self, evt=""):
        #self.set_slider_min(self.sliderMinCtrl.GetValue())
        self.set_slider_max(self.sliderMaxCtrl.GetValue())

    def toggle_mosaic_visible(self, evt=""):
        """call the set_mosaic_visible function of self.canvas.posList to initiate what is necessary to hide the mosaic box"""
        self.canvas.posList.set_mosaic_visible(self.showmagCheck.IsChecked())
        self.canvas.draw()

    def get_mosaic_parameters(self):
        """extract out an instance of MosaicSettings from the current controls with the proper values"""
        return MosaicSettings(mag=self.magChoiceCtrl.GetValue(),
                              show_box=self.showmagCheck.IsChecked(),
                              mx=self.mosaicXCtrl.GetValue(),
                              my=self.mosaicYCtrl.GetValue(),
                              overlap=self.overlapCtrl.GetValue())
    #unused # batman - should we kill it if unused?
    def cross_cursor(self, event):
        self.canvas.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))

    #overrides the default
    def home(self, event):
        """calls self.canvas.on_home_tool(), should be triggered by the hometool press.. overrides default behavior"""
        self.canvas.on_home_tool()

    def set_slider_min(self, min=0):
        self.slider.SetMin(min)

    def set_slider_max(self, max=500):
        self.slider.SetMax(max)