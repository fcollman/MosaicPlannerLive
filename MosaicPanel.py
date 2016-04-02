from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from Settings import (MosaicSettings, CameraSettings,SiftSettings,ChangeCameraSettings, ImageSettings,
                       ChangeImageMetadata, SmartSEMSettings, ChangeSEMSettings, ChannelSettings,
                       ChangeChannelSettings, ChangeSiftSettings, CorrSettings,ChangeCorrSettings,
                      ChangeZstackSettings, ZstackSettings)
from sqlalchemy import create_engine
from imageSourceMM import imageSource
from matplotlib.figure import Figure
import traceback
import wx
import sys
from PositionList import posList
import os
import multiprocessing as mp
from tifffile import imsave
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from MMPropertyBrowser import MMPropertyBrowser
from ASI_Control import ASI_AutoFocus
from FocusCorrectionPlaneWindow import FocusCorrectionPlaneWindow
from NavigationToolBarImproved import NavigationToolbar2Wx_improved as NavBarImproved
import jsonpickle
from PIL import Image
import SaveQueue
from MosaicToolbar import MosaicToolbar
import LiveMode
import numpy as np
from MyLasso import MyLasso
from MosaicImage import MosaicImage

class MosaicPanel(FigureCanvas):
    """A panel that extends the matplotlib class FigureCanvas for plotting all the plots, and handling all the GUI interface events
    """
    def __init__(self, parent, config, **kwargs):
        """keyword the same as standard init function for a FigureCanvas"""
        self.figure = Figure(figsize=(5, 9))
        FigureCanvas.__init__(self, parent, -1, self.figure, **kwargs)
        self.canvas = self.figure.canvas

        #format the appearance
        self.figure.set_facecolor((1, 1, 1))
        self.figure.set_edgecolor((1, 1, 1))
        self.canvas.SetBackgroundColour('white')

        #add subplots for various things
        self.subplot     = self.figure.add_axes([.05, .5, .92, .5])
        self.posone_plot = self.figure.add_axes([.1, .05, .2, .4])
        self.postwo_plot = self.figure.add_axes([.37, .05, .2, .4])
        self.corrplot    = self.figure.add_axes([.65, .05, .25, .4])

        #initialize the camera settings and mosaic settings
        self.cfg = config
        self.camera_settings = CameraSettings()
        self.camera_settings.load_settings(config)
        mosaic_settings = MosaicSettings()
        mosaic_settings.load_settings(config)
        self.MM_config_file = self.cfg['MosaicPlanner']['MM_config_file']
        print self.MM_config_file

        #setup the image source
        self.imgSrc=None
        while self.imgSrc is None:
            try:
                self.imgSrc=imageSource(self.MM_config_file)
            except:
                traceback.print_exc(file=sys.stdout)
                dlg = wx.MessageBox("Error Loading Micromanager\n check scope and re-select config file","MM Error")
                self.edit_MManager_config()

        self.MM_database_path = str(self.cfg.get("MosaicPlanner","MM_database_path"))



        channels=self.imgSrc.get_channels()
        self.channel_settings=ChannelSettings(self.imgSrc.get_channels())
        self.channel_settings.load_settings(config)
        self.imgSrc.set_channel(self.channel_settings.map_chan)
        map_chan=self.channel_settings.map_chan
        if map_chan not in channels: #if the saved settings don't match, call up dialog
            self.edit_channels()
            map_chan=self.channel_settings.map_chan
        self.imgSrc.set_channel(map_chan)
        self.imgSrc.set_exposure(self.channel_settings.exposure_times[map_chan])

        #load the SIFT settings

        self.SiftSettings = SiftSettings()
        self.SiftSettings.load_settings(config)

        self.CorrSettings = CorrSettings()
        self.CorrSettings.load_settings(config)

        # load Zstack settings
        self.zstack_settings = ZstackSettings()
        self.zstack_settings.load_settings(config)

        #setup a blank position list
        self.posList=posList(self.subplot,mosaic_settings,self.camera_settings)
        #start with no MosaicImage
        self.mosaicImage=None
        #start with relative_motion on, so that keypress calls shift_selected_curved() of posList
        self.relative_motion = True

        self.focusCorrectionList = posList(self.subplot)

        #read saved position list from configuration file
        pos_list_string = self.cfg['MosaicPlanner']['focal_pos_list_pickle']
        #if the saved list is not default blank.. add it to current list
        #print "pos_list",pos_list_string
        #if len(pos_list_string)>0:
        #    print "loading saved position list"
        #    pl = jsonpickle.decode(pos_list_string)
        #    self.focusCorrectionList.add_from_posList(pl)
        #x,y,z = self.focusCorrectionList.getXYZ()
        #if len(x)>2:
        #    XYZ = np.column_stack((x,y,z))
        #    self.imgSrc.define_focal_plane(np.transpose(XYZ))


        #start with no toolbar and no lasso tool
        self.navtoolbar = None
        self.lasso = None
        self.lassoLock=False

        self.canvas.mpl_connect('button_press_event', self.on_press)
        self.canvas.mpl_connect('button_release_event', self.on_release)
        self.canvas.mpl_connect('key_press_event', self.on_key)

    def handle_close(self,evt=None):
        print "handling close"
        #if not self.mosaicImage == None:
        #    self.mosaicImage.cursor_timer.cancel()
        self.imgSrc.mmc.unloadAllDevices()

    def on_load(self,rootPath):
        self.rootPath=rootPath
        print "transpose toggle state",self.imgSrc.transpose_xy
        self.mosaicImage=MosaicImage(self.subplot,self.posone_plot,self.postwo_plot,self.corrplot,self.imgSrc,rootPath,figure=self.figure)
        self.on_crop_tool()
        self.draw()


    def write_session_metadata(self,outdir):
        filename=os.path.join(outdir,'session_metadata.txt')
        f = open(filename, 'w')

        (height,width)=self.imgSrc.get_sensor_size()
        Nch=0
        for k,ch in enumerate(self.channel_settings.channels):
            if self.channel_settings.usechannels[ch]:
                Nch+=1

        f.write("Width\tHeight\t#chan\tMosaicX\tMosaicY\tScaleX\tScaleY\n")
        f.write("%d\t%d\t%d\t%d\t%d\t%f\t%f\n" % (width,height, Nch,self.posList.mosaic_settings.mx, self.posList.mosaic_settings.my, self.imgSrc.get_pixel_size(), self.imgSrc.get_pixel_size()))
        f.write("Channel\tExposure Times (msec)\tRLPosition\n")
        for k,ch in enumerate(self.channel_settings.channels):
            if self.channel_settings.usechannels[ch]:
                f.write(self.channel_settings.prot_names[ch] + "\t" + "%f\t%s\n" % (self.channel_settings.exposure_times[ch],ch))

    def multiDacq(self,outdir,x,y,slice_index,frame_index=0):

        #print datetime.datetime.now().time()," starting multiDAcq, autofocus on"
        self.imgSrc.set_hardware_autofocus_state(True)
        #print datetime.datetime.now().time()," starting stage move"
        self.imgSrc.move_stage(x,y)
        wx.Yield()
        attempts=0
        #print datetime.datetime.now().time()," starting autofocus"
        if self.imgSrc.has_hardware_autofocus():
            #wait till autofocus settles
            while not self.imgSrc.is_hardware_autofocus_done():
                #time.sleep(.05)
                attempts+=1
                if attempts>100:
                    print "not auto-focusing correctly.. giving up after 10 seconds"
                    break


            self.imgSrc.set_hardware_autofocus_state(False) #turn off autofocus

        else:
            score=self.imgSrc.image_based_autofocus(chan=self.channel_settings.map_chan)
            print score

        #print datetime.datetime.now().time()," starting multichannel acq"
        currZ=self.imgSrc.get_z()
        presentZ = currZ
        #print 'flag is,',self.zstack_settings.zstack_flag

        if self.zstack_settings.zstack_flag:
            furthest_distance = self.zstack_settings.zstack_delta * (self.zstack_settings.zstack_number-1)/2
            zplanes_to_visit = [(currZ-furthest_distance) + i*self.zstack_settings.zstack_delta for i in range(self.zstack_settings.zstack_number)]
        else:
            zplanes_to_visit = [currZ]
        #print 'zplanes_to_visit : ',zplanes_to_visit

        for z_index, zplane in enumerate(zplanes_to_visit):
            for k,ch in enumerate(self.channel_settings.channels):
                #print datetime.datetime.now().time()," start channel",ch, " zplane", zplane
                prot_name=self.channel_settings.prot_names[ch]
                path=os.path.join(outdir,prot_name)
                if self.channel_settings.usechannels[ch]:
                    #ti = time.clock()*1000
                    #print time.clock(),'start'
                    z = zplane + self.channel_settings.zoffsets[ch]
                    if not z == presentZ:
                        self.imgSrc.set_z(z)
                        presentZ = z
                    self.imgSrc.set_exposure(self.channel_settings.exposure_times[ch])
                    self.imgSrc.set_channel(ch)
                    #t2 = time.clock()*1000
                    #print time.clock(),t2-ti, 'ms to get to snap image from start'

                    data=self.imgSrc.snap_image()
                    #t3 = time.clock()*1000
                    #print time.clock(),t3-t2, 'ms to snap image'
                    self.dataQueue.put((slice_index,frame_index, z_index, prot_name,path,data,ch,x,y,z,))



    def on_run_acq(self,event="none"):
        print "running"
        #self.channel_settings
        #self.pos_list
        #self.imgSrc


        #get an output directory
        dlg=wx.DirDialog(self,message="Pick output directory",defaultPath= os.path.split(self.rootPath)[0])
        button_pressed = dlg.ShowModal()
        if button_pressed == wx.ID_CANCEL:
            wx.MessageBox("You didn't enter a save directory... \n Aborting aquisition")
            return None

        outdir=dlg.GetPath()
        dlg.Destroy()



        metadata_dictionary = {
        'channelname'    : self.channel_settings.prot_names,
        '(height,width)' : self.imgSrc.get_sensor_size(),
        'ScaleFactorX'   : self.imgSrc.get_pixel_size(),
        'ScaleFactorY'   : self.imgSrc.get_pixel_size(),
        'exp_time'       : self.channel_settings.exposure_times,
        }

        #setup output directories
        for k,ch in enumerate(self.channel_settings.channels):
            if self.channel_settings.usechannels[ch]:
                thedir=os.path.join(outdir,self.channel_settings.prot_names[ch])
                if not os.path.isdir(thedir):
                    os.makedirs(thedir)

        self.write_session_metadata(outdir)

        #step the stage back to the first position, position by position
        #so as to not lose the immersion oil
        (x,y)=self.imgSrc.get_xy()
        currpos=self.posList.get_position_nearest(x,y)
        while currpos is not None:
            #turn on autofocus
            self.imgSrc.set_hardware_autofocus_state(True)
            self.imgSrc.move_stage(currpos.x,currpos.y)
            currpos=self.posList.get_prev_pos(currpos)
            wx.Yield()


        self.dataQueue = mp.Queue()
        self.saveProcess =  mp.Process(target=SaveQueue.file_save_process,args=(self.dataQueue,SaveQueue.STOP_TOKEN, metadata_dictionary))
        self.saveProcess.start()

        hasFrameList = self.posList.slicePositions[0].frameList is not None
        numSections = len(self.posList.slicePositions)
        if hasFrameList:
            numFrames = len(self.posList.slicePositions[0].frameList.slicePositions)
        else:
            numFrames = 1
        maxProgress = numSections*numFrames

        self.progress = wx.ProgressDialog("A progress box", "Time remaining", maxProgress ,
        style=wx.PD_CAN_ABORT | wx.PD_ELAPSED_TIME | wx.PD_REMAINING_TIME)



        goahead = True
        #loop over positions
        for i,pos in enumerate(self.posList.slicePositions):
            if not goahead:
                break
            (goahead, skip) = self.progress.Update(i*numFrames,'section %d of %d'%(i+1,numSections))
            #turn on autofocus
            if pos.frameList is None:
                self.multiDacq(outdir,pos.x,pos.y,i)
                #write a frame end token here
            else:
                for j,fpos in enumerate(pos.frameList.slicePositions):
                    if not goahead:
                        print "breaking out!"
                        break
                    self.multiDacq(outdir,fpos.x,fpos.y,i,j)
                    #write a frame end token here

                    (goahead, skip)=self.progress.Update((i*numFrames) + j+1,'section %d of %d, frame %d'%(i+1,numSections,j))
            #write a section end token here

            wx.Yield()
        if not goahead:
            print "user cancelled the acquisition "
            print "section %d"%(i)
            if pos.frameList is not None:
                print "frame %d"%(j)
        if goahead:
        #write a session json file here

        #update/create ribbon json file to include new session

            self.dataQueue.put((SaveQueue.STOP_TOKEN,True))
        if not goahead:
            self.dataQueue.put((SaveQueue.STOP_TOKEN,False))

        self.saveProcess.join()
        print "save process ended"
        self.progress.Destroy()


    def edit_channels(self,event="none"):
        dlg = ChangeChannelSettings(None, -1, title = "Channel Settings", settings = self.channel_settings,style=wx.OK)
        ret=dlg.ShowModal()
        if ret == wx.ID_OK:
            self.channel_settings=dlg.GetSettings()
            self.channel_settings.save_settings(self.cfg)
            map_chan=self.channel_settings.map_chan
            self.imgSrc.set_channel(map_chan)
            self.imgSrc.set_exposure(self.channel_settings.exposure_times[map_chan])
            print "should be changed"

        dlg.Destroy()

    def on_live_mode(self,evt="none"):
        expTimes=LiveMode.launchLive(self.imgSrc,exposure_times=self.channel_settings.exposure_times)
        self.channel_settings.exposure_times=expTimes
        self.channel_settings.save_settings(self.cfg)
        #reset the current channel to the mapping channel, and it's exposure
        map_chan=self.channel_settings.map_chan
        self.imgSrc.set_channel(map_chan)
        self.imgSrc.set_exposure(self.channel_settings.exposure_times[map_chan])

    def edit_SIFT_settings(self, event="none"):
        dlg = ChangeSiftSettings(None, -1, title= "Edit SIFT Settings", settings = self.SiftSettings, style = wx.OK)
        ret=dlg.ShowModal()
        if ret == wx.ID_OK:
            self.SiftSettings = dlg.GetSettings()
            self.SiftSettings.save_settings(self.cfg)
        dlg.Destroy()

    def edit_corr_settings(self, event="none"):
        dlg = ChangeCorrSettings(None, -1, title= "Edit Corr Settings", settings = self.CorrSettings, style = wx.OK)
        ret=dlg.ShowModal()
        if ret == wx.ID_OK:
            self.CorrSettings = dlg.GetSettings()
            self.CorrSettings.save_settings(self.cfg)
        dlg.Destroy()

    def edit_MManager_config(self, event = "none"):

        fullpath=self.MM_config_file
        if fullpath is None:
            fullpath = ""

        (dir,file)=os.path.split(fullpath)
        dlg = wx.FileDialog(self,"select configuration file",dir,file,"*.cfg")

        dlg.ShowModal()
        self.MM_config_file = str(dlg.GetPath())
        self.cfg['MosaicPlanner']['MM_config_file'] = self.MM_config_file
        self.cfg.write()

        dlg.Destroy()

    def edit_Zstack_settings(self,event = "none"):
        dlg = ChangeZstackSettings(None, -1, title= "Edit Ztack Settings", settings = self.zstack_settings, style = wx.OK)
        ret=dlg.ShowModal()
        if ret == wx.ID_OK:
            self.zstack_settings = dlg.GetSettings()
            self.zstack_settings.save_settings(self.cfg)
        dlg.Destroy()

    def edit_focus_correction_plane(self, event=None):
        global win
        win = FocusCorrectionPlaneWindow(self.focusCorrectionList,self.imgSrc)
        win.show()

    def launch_MManager_browser(self, event=None):
        global win
        win = MMPropertyBrowser(self.imgSrc.mmc)
        win.show()

    def launch_ASI(self, event=None):
         global win
         win = ASI_AutoFocus(self.imgSrc.mmc)
         win.show()

    def repaint_image(self, evt):
        """event handler used when the slider bar changes and you want to repaint the MosaicImage with a different color scale"""
        if not self.mosaicImage==None:
            self.mosaicImage.repaint()
            self.draw()

    def lasso_callback(self, verts):
        """callback function for handling the lasso event, called from on_release"""
        #select the points inside the vertices listed
        self.posList.select_points_inside(verts)
        #redraw the plot
        self.canvas.draw_idle()
        #release the widgetlock and remove the lasso
        self.canvas.widgetlock.release(self.lasso)
        self.lassoLock=False
        del self.lasso

    def on_key(self,evt):
        if (evt.inaxes == self.mosaicImage.axis):
            if (evt.key == 'a'):
                self.posList.select_all()
                self.draw()
            if (evt.key == 'd'):
                self.posList.delete_selected()

    def on_press(self, evt):
        """canvas mousedown handler
        """
        #on a left click
        if evt.button == 1:
            #if something hasn't locked the widget
            if self.canvas.widgetlock.locked():
                return
            #if the click is inside the axis
            if evt.inaxes is None:
                return
            #if we have a toolbar
            if (self.navtoolbar):
                #figure out which of the mutually exclusive toolbar buttons are active
                mode = self.navtoolbar.get_mode()
                #call the appropriate function
                if (evt.inaxes == self.mosaicImage.one_axis):
                    self.posList.pos1.setPosition(evt.xdata,evt.ydata)
                    self.mosaicImage.paintPointsOneTwo(self.posList.pos1.getPosition(),self.posList.pos2.getPosition())
                elif (evt.inaxes == self.mosaicImage.two_axis):
                    self.posList.pos2.setPosition(evt.xdata,evt.ydata)
                    self.mosaicImage.paintPointsOneTwo(self.posList.pos1.getPosition(),self.posList.pos2.getPosition())
                else:
                    if (mode == 'movehere'):
                        self.imgSrc.set_xy(evt.xdata,evt.ydata,self.imgSrc.use_focus_plane)
                    if (mode == 'selectone'):
                        self.posList.set_pos1_near(evt.xdata,evt.ydata)
                        if not (self.posList.pos2 == None):
                            self.mosaicImage.paintPointsOneTwo(self.posList.pos1.getPosition(),self.posList.pos2.getPosition())
                    if (mode == 'selecttwo'):
                        self.posList.set_pos2_near(evt.xdata,evt.ydata)
                        if not (self.posList.pos1 == None):
                            self.mosaicImage.paintPointsOneTwo(self.posList.pos1.getPosition(),self.posList.pos2.getPosition())
                    if (mode == 'selectnear'):
                        pos=self.posList.get_position_nearest(evt.xdata,evt.ydata)
                        if not evt.key=='shift':
                            self.posList.set_select_all(False)
                        pos.set_selected(True)
                    elif (mode == 'add'):
                        print ('add point at',evt.xdata,evt.ydata)
                        self.posList.add_position(evt.xdata,evt.ydata)
                        self.mosaicImage.imgCollection.add_covered_point(evt.xdata,evt.ydata)

                    elif (mode  == 'select' ):
                        self.lasso = MyLasso(evt.inaxes, (evt.xdata, evt.ydata), self.lasso_callback,linecolor='white')
                        self.lassoLock=True
                        self.canvas.widgetlock(self.lasso)
                    elif (mode == 'snappic' ):
                        (fw,fh)=self.mosaicImage.imgCollection.get_image_size_um()
                        for i in range(-1,2):
                            for j in range(-1,2):
                                self.mosaicImage.imgCollection.add_image_at(evt.xdata+(j*fw),evt.ydata+(i*fh))
                                self.draw()
                                self.on_crop_tool()
                                wx.Yield()
                    elif (mode == 'snaphere'):
                        self.mosaicImage.imgCollection.add_image_at(evt.xdata,evt.ydata)

                self.draw()

    def on_release(self, evt):
        """canvas mouseup handler
        """
        # Note: lasso_callback is not called on click without drag so we release
        #   the lock here to handle this case as well.
        if evt.button == 1:
            if self.lassoLock:
                self.canvas.widgetlock.release(self.lasso)
                self.lassoLock=False
        else:
            #this would be for handling right click release, and call up a popup menu, this is not implemented so it gives an error
            self.show_popup_menu((evt.x, self.canvas.GetSize()[1]-evt.y), None)

    def get_toolbar(self):
        """"return the toolbar, make one if neccessary"""
        if not self.navtoolbar:
            self.navtoolbar = MosaicToolbar(self.canvas)
            self.navtoolbar.Realize()
        return self.navtoolbar

    def on_slider_change(self, evt):
        """handler for when the maximum value slider changes"""
        if not self.mosaicImage==None:
            self.mosaicImage.set_maxval(self.get_toolbar().slider.GetValue())
            self.draw()

    def on_grid_tool(self, evt):
        """handler for when the grid tool is toggled"""
        #returns whether the toggle is True or False
        visible=self.navtoolbar.GetToolState(self.navtoolbar.ON_GRID)
        #make the frames grid visible/invisible accordingly
        self.posList.set_frames_visible(visible)
        self.draw()

    def on_delete_points(self,event="none"):
        """handlier for handling the Delete tool press"""
        self.posList.delete_selected()
        self.draw()

    def on_rotate_tool(self,evt):
        """handler for handling when the Rotate tool is toggled"""
        if self.navtoolbar.GetToolState(self.navtoolbar.ON_ROTATE):
            self.posList.rotate_boxes()
        else:
            self.posList.unrotate_boxes()
        self.draw()

    def on_step_tool(self,evt=""):
        """handler for when the step_tool is pressed"""
        #we call another steptool function so that the fast forward tool can use the same function
        goahead=self.step_tool()
        self.on_crop_tool()
        self.draw()

    def on_corr_tool(self,evt=""):
        """handler for when the corr_tool is pressed"""
        #we call another function so the step tool can use the same function
        passed=self.corr_tool()
        #inliers=self.sift_corr_tool(window=70)
        self.draw()

    def on_snap_tool(self,evt=""):
        #takes snap straight away
        self.mosaicImage.imgCollection.oh_snap()
        if self.mosaicImage.imgCollection.imgCount == 1:
            self.on_crop_tool()
        self.draw()

    def on_home_tool(self):
        """handler which overrides the usual behavior of the home button, just resets the zoom on the main subplot for the mosaicImage"""
        self.mosaicImage.set_view_home()
        self.draw()

    def on_crop_tool(self,evt=""):
        self.mosaicImage.crop_to_images(evt)
        self.draw()

    def on_fine_tune_tool(self,evt=""):
        print "fine tune tool not yet implemented, should do something to make fine adjustments to current position list"
        #this is a list of positions which we forbid from being point 1, our anchor points
        badpositions = []
        badstreak=0
        if ((self.posList.pos1 != None) & (self.posList.pos2 != None)):
            #start with point 1 where it is, and make point 2 the next point
            #self.posList.set_pos2(self.posList.get_next_pos(self.posList.pos1))
            #we are going to loop through until point 2 reaches the end
            #while (self.posList.pos2 != None):
            if badstreak>2:
                return
            #adjust the position of point 2 using a fine scale alignment with a small search radius
            corrval=self.corr_tool()
            #each time through the loop we are going to move point 2 but not point 1, but after awhile
            #we expect the correlation to fall off, at which point we will move point 1 to be closer
            # so first lets try moving point 1 to be the closest point to pos2 that we have fixed (which hasn't been marked "bad")
            if (corrval<.3):
                #lets make point 1 the point just before this one which is still a "good one"
                newp1=self.posList.get_prev_pos(self.posList.pos2)
                #if its marked bad, lets try the one before it
                while (newp1 in badpositions):
                    newp1=self.posList.get_prev_pos(newp1)
                self.posList.set_pos1(newp1)
                #try again
                corrval2=self.corr_tool()
                if (corrval2<.3):
                    badstreak=badstreak+1
                    #if this fails a second time, lets assume that this point 2 is a messed up one and skip it
                    #we just want to make sure that we don't use it as a point 1 in the future
                    badpositions.append(self.posList.pos2)
            else:
                badstreak=0
            #select pos2 as the next point in line
            self.posList.set_pos2(self.posList.get_next_pos(self.posList.pos2))
            self.draw()

    #===========================================================================
    # def PreviewTool(self,evt):
    #    """handler for handling the make preview stack tool.... not fully implemented"""
    #    (h_um,w_um)=self.calcMosaicSize()
    #    mypf=pointFinder(self.positionarray,self.tif_filename,self.extent,self.originalfactor)
    #    mypf.make_preview_stack(w_um, h_um)
    #===========================================================================
    def on_redraw(self,evt=""):
        self.mosaicImage.paintPointsOneTwo((self.posList.pos1.x,self.posList.pos1.y),
                                           (self.posList.pos2.x,self.posList.pos2.y),
                                                               100)
        self.draw()

    def on_fastforward_tool(self,event):

        goahead=True
        #keep doing this till the step_tool says it shouldn't go forward anymore
        while (goahead):
            wx.Yield()
            goahead=self.step_tool()
            self.on_crop_tool()
            self.draw()

        #call up a box and make a beep alerting the user for help
        wx.MessageBox('Fast Forward Aborted, Help me','Info')

    def step_tool(self):
        """function for performing a step, assuming point1 and point2 have been selected

        keywords:
        window)size of the patch to cut out
        delta)size of shifts in +/- x,y to look for correlation
        skip)the number of positions in pixels to skip over when sampling shifts

        """
        newpos=self.posList.new_position_after_step()
        #if the new postiion was not created, or if it wasn't on the array stop and return False
        if newpos == None:
            return False
        #if not self.is_pos_on_array(newpos):
        #    return False
        #if things were fine, fine adjust the position
        #corrval=self.corr_tool(window,delta,skip)
        #return self.sift_corr_tool(window)
        return self.corr_tool()

    def sift_corr_tool(self,window=70):
        """function for performing the correction of moving point2 to match the image shown around point1

        keywords)
        window)radious of the patch to cut out in microns
        return inliers
        inliers is the number of inliers in the best transformation obtained by this operation

        """
        (dxy_um,inliers)=self.mosaicImage.align_by_sift((self.posList.pos1.x,self.posList.pos1.y),(self.posList.pos2.x,self.posList.pos2.y),window = window,SiftSettings=self.SiftSettings)
        (dx_um,dy_um)=dxy_um
        self.posList.pos2.shiftPosition(-dx_um,-dy_um)
        return len(inliers)>self.SiftSettings.inlier_thresh

    def corr_tool(self):
        """function for performing the correlation correction of two points, identified as point1 and point2

        keywords)
        window)size of the patch to cut out
        delta)size of shifts in +/- x,y to look for correlation
        skip)the number of positions in pixels to skip over when sampling shifts

        """

        (corrval,dxy_um)=self.mosaicImage.align_by_correlation((self.posList.pos1.x,self.posList.pos1.y),(self.posList.pos2.x,self.posList.pos2.y),CorrSettings=self.CorrSettings)

        (dx_um,dy_um)=dxy_um
        self.posList.pos2.shiftPosition(-dx_um,-dy_um)
        #self.draw()
        return corrval>self.CorrSettings.corr_thresh

    def on_key_press(self,event="none"):
        """function for handling key press events"""

        #pull out the current bounds
        #(minx,maxx)=self.subplot.get_xbound()
        (miny,maxy)=self.subplot.get_ybound()

        #make the jump a size dependant on the y extent of the bounds, and depending on whether you are holding down shift
        if event.ShiftDown():
            jump=(maxy-miny)/20
        else:
            jump=(maxy-miny)/100
        #initialize the jump to be zero
        dx=dy=0


        keycode=event.GetKeyCode()

        #if keycode in (wx.WXK_DELETE,wx.WXK_BACK,wx.WXK_NUMPAD_DELETE):
        #    self.posList.delete_selected()
        #    self.draw()
        #    return
        #handle arrow key presses
        if keycode == wx.WXK_DOWN:
            dy=jump
        elif keycode == wx.WXK_UP:
            dy=-jump
        elif keycode == wx.WXK_LEFT:
            dx=-jump
        elif keycode == wx.WXK_RIGHT:
            dx=jump
        #skip the event if not handled above
        else:
            event.Skip()
        #if we have a jump move accomplish it depending on whether you have relative_motion on/off
        if not (dx==0 and dy==0):
            if self.relative_motion:
                self.posList.shift_selected_curve(dx, dy)
            else:
                self.posList.shift_selected(dx,dy)
            self.draw()
