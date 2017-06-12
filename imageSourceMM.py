import numpy as np
import MMCorePy
from PIL import Image
import time
from Rectangle import Rectangle
import wx
import datetime
import os
from MMArduino import MMArduino

class imageSource():
    
    def __init__(self,configFile,channelGroupName='Channels',
                 use_focus_plane  = False, focus_points=None,
                 transpose_xy = False, logfile='MP_MM.txt',
                 MasterArduinoPort = None, interframe_time= 10, filtswitch = None):
      #NEED TO IMPLEMENT IF NOT MICROMANAGER
     
        self.configFile=configFile
        self.mmc = MMCorePy.CMMCore() 
        self.mmc.enableStderrLog(False)
        self.mmc.enableDebugLog(True)
        now=datetime.datetime.now()
        #logfile=now.strftime('%Y-%m-%d_%H:%M:%S_log.txt')

        currpath=os.path.split(os.path.realpath(__file__))[0]
        self.mmc.setPrimaryLogFile(os.path.join(currpath,logfile))
        self.mmc.loadSystemConfiguration(self.configFile)
       
        self.channelGroupName=channelGroupName
        self.transpose_xy = transpose_xy
        auto_dev = self.mmc.getAutoFocusDevice()
        assert(auto_dev is not None)

        dev_name = self.mmc.getDeviceName(auto_dev)
        print "dev_name",dev_name

        if 'SimpleAutofocus' == dev_name:
            self.has_continuous_focus = False
        else:
            self.has_continuous_focus = True
       
        print "has_continuous_focus",self.has_continuous_focus

        self.focus_points = focus_points
        self.plane_tuple = None
        self.use_focus_plane = use_focus_plane
        if use_focus_plane:
            assert (focus_points is not None)
            self.define_focal_plane(focus_points)

        if MasterArduinoPort is not None:
            self.masterArduino = MMArduino(port=MasterArduinoPort)
        else:
            self.masterArduino = None
        self.interframe_time = interframe_time
        self.filtswitch = filtswitch

        if self.filtswitch is not None:
            #sets filterwheel to empty slot during setup/mapping if wheel is present
            self.mmc.setConfig('Triggering','Hardware')
            self.mmc.waitForConfig('Triggering','Hardware')
            self.mmc.setConfig('Triggering','Hardware')
            # self.mmc.setProperty(filtswitch,'State','5')

            self.mmc.loadPropertySequence(filtswitch,'State','5')
            self.mmc.startPropertySequence(filtswitch,'State')
            self.masterArduino.MoveFilter()
            self.mmc.stopPropertySequence(filtswitch,'State')
            self.mmc.setConfig('Triggering','Software')
            self.mmc.setConfig('Triggering','Software')
        #set the exposure to use

    def reset_piezo(self,cfg):

        do_stage_reset=cfg['enableStageReset']
        if do_stage_reset:
            z_label = cfg['compensationStage']
            piezo_label = cfg['resetStage']
            min_threshold = cfg['minThreshold']
            max_threshold = cfg['maxThreshold']
            reset_position = cfg['resetPosition']
            invert_compensation = cfg['invertCompensation']

            piezo = self.mmc.getPosition(piezo_label)
            if (piezo<min_threshold) or (piezo>max_threshold):
                z = self.mmc.getPosition(z_label)
                islocked = self.mmc.isContinuousFocusEnabled()

                if islocked:
                    self.mmc.enableContinuousFocus(False)

                if invert_compensation:
                    self.mmc.setPosition(z_label,z+(piezo-reset_position))
                else:
                    self.mmc.setPosition(z_label,z-(piezo-reset_position))
                self.mmc.setPosition(piezo_label,reset_position)

                if islocked:
                    self.mmc.enableContinuousFocus(True)

    def define_focal_plane(self,points):
        if points.shape[1]>3:
            self.plane_tuple = self.planeFit(points)

    def get_focal_z(self,x,y):
        if self.plane_tuple is not None:
            ax,ay,b = self.plane_tuple
            return ax*x + ay*y + b
        else:
            return self.get_z()

    def planeFit(self,points):
        """
        p, n = planeFit(points)

        Fit an n-dimensional plane to the points.
        Return a point on the plane and the normal.
        """
        from numpy.linalg import svd
        points = np.reshape(points, (points.shape[0], -1))
        assert points.shape[0] < points.shape[1]
        ctr = points.mean(axis=1)
        x = points - ctr[:,None]
        M = np.dot(x, x.T)
        pt_on_plane = ctr
        norm =  svd(M)[0][:,-1]
        d=norm[0]*pt_on_plane[0]+norm[1]*pt_on_plane[1]+norm[2]*pt_on_plane[2]
        ax=-norm[0]/norm[2]
        ay=-norm[1]/norm[2]
        b = -d/norm[2]
        return ax,ay,b

    def stop_hardware_triggering(self):
        self.mmc.stopSequenceAcquisition()
        self.mmc.setConfig('Triggering','Software')
        self.mmc.setConfig('Triggering','Software')

    def setup_hardware_triggering(self,channels,exposure_times):

        #set up triggering to "Hardware" to load all the
        self.mmc.setConfig('Triggering','Hardware')
        #do it twice to work around bug in Andor Zyla camera's, can't really hurt
        self.mmc.setConfig('Triggering','Hardware')
        self.mmc.waitForConfig('Triggering','Hardware')

        #get the first channel config
        cfg = self.mmc.getConfigData(self.channelGroupName,channels[0])
        #loop over the properties in this channel
        for i in range(cfg.size()):
            #pull out the device and property
            setting=cfg.getSetting(i)
            dev = setting.getDeviceLabel()
            prop = setting.getPropertyName()

            #if its sequencable, then load the sequence
            if self.mmc.isPropertySequenceable(dev,prop):
                #set it up for hardware triggering
                propseq = [self.mmc.getConfigData(self.channelGroupName,channels[k]).getSetting(i).getPropertyValue() for k in range(len(channels))]
                self.mmc.loadPropertySequence(dev,prop,propseq)
                self.mmc.startPropertySequence(dev,prop)

            #otherwise then we need it to be constant
            else:
                #check that it is constant across channels
                valuefirst = setting.getPropertyValue()
                for channel in channels:
                    thisconfig = self.mmc.getConfigData(self.channelGroupName,channel)
                    thissetting = thisconfig.getSetting(i)
                    thisvalue = thissetting.getPropertyValue()
                    #if its not constant, then we can't hardware trigger this
                    if thisvalue != valuefirst:
                        self.mmc.setConfig('Triggering','Software')
                        self.mmc.waitForConfig('Triggering','Software')
                        return False

                #set it to that constant state
                self.mmc.setProperty(dev,prop,valuefirst)
                self.mmc.waitForDevice(dev)
        self.masterArduino.setupExposure(exposure_times,self.interframe_time)
        self.numberHardwareChannels = len(exposure_times)
        self.mmc.startContinuousSequenceAcquisition(0)

    def stopSequenceAcquisition(self):
        self.mmc.stopSequenceAcquisition()
        self.mmc.clearCircularBuffer()
        
    def startContinuousSequenceAcquisition(self,val):
        self.mmc.startContinuousSequenceAcquisition(val)

    def startHardwareSequence(self):
        assert(self.masterArduino is not None)
        self.masterArduino.startTimedPattern()

    def set_binning(self,bin=1):
        cam = self.mmc.getCameraDevice()
        binstring = "%dx%d"%(bin,bin)
        self.mmc.setProperty(cam,'Binning',binstring)

    def get_binning(self):
        cam = self.mmc.getCameraDevice()
        binstring = self.mmc.getProperty(cam,'Binning')
        (bx,by)=binstring.split('x')
        return int(bx)

    def image_based_autofocus(self,chan=None):
        if chan is not None:
            self.set_channel(chan)
        self.mmc.fullFocus()
        return self.mmc.getLastFocusScore()

    def get_max_pixel_value(self):
        bit_depth=self.mmc.getImageBitDepth()
        return np.power(2,bit_depth)-1

    def get_exposure(self):
        return self.mmc.getExposure()

    def set_exposure(self,exp_msec):
      #NEED TO IMPLEMENT IF NOT MICROMANAGER
        self.mmc.setExposure(exp_msec)
    

    def reset_focus_offset(self):
        if self.has_hardware_autofocus():
            focusDevice=self.mmc.getAutoFocusDevice()
            self.mmc.setProperty(focusDevice,"CRISP State","Reset Focus Offset")
  
    def get_hardware_autofocus_state(self):
        if self.has_hardware_autofocus():
            return self.mmc.isContinuousFocusEnabled()
           
    def set_hardware_autofocus_state(self,state,dowait=True):
        if self.has_hardware_autofocus():
            self.mmc.enableContinuousFocus(state)
            if dowait:
                self.mmc.waitForDevice(self.mmc.getAutoFocusDevice())
        
    def has_hardware_autofocus(self):
        #NEED TO IMPLEMENT IF NOT MICROMANAGER
        return self.has_continuous_focus
        
        
    def is_hardware_autofocus_done(self):
      #NEED TO IMPLEMENT IF NOT MICROMANAGER
        #hardware autofocus assumes the focus score is <1 when focused
        #score=self.mmc.getCurrentFocusScore()
        #if abs(score)<1:
        #    print "locked on"
        #    return True
        #else:
        #    print "score %f not locked on"%score
        #    return False
        return self.mmc.isContinuousFocusLocked()
        

    def take_hardware_snap(self):

        self.mmc.startSequenceAcquisition(self.numberHardwareChannels,0,True)
        images = []
        while self.mmc.isSequenceRunning():
            if self.mmc.getRemainingImageCount()>0:
                images.append(self.mmc.popNextImage())
        for i in range(self.numberHardwareChannels-len(images)):
            images.append(self.mmc.popNextImage())
        return images


    def take_image(self,x,y):
        #do not need to re-implement
        #moves scope to x,y - focus scope - snap picture
        #using the configured exposure time

        #print "is continuous focus enabled",self.mmc.isContinuousFocusEnabled()
        #print "is continuous focus locked",self.mmc.isContinuousFocusLocked()

        if not self.mmc.isContinuousFocusEnabled():
            print 'autofocus not enabled'
            wx.MessageBox('autofocus not enabled, Help me',)
            return


        #move stage to x,y
        self.set_xy(x,y)
        if self.use_focus_plane:
            z = self.get_focal_z(x,y)
            self.set_z(z)
        else:
            if not self.has_hardware_autofocus():
                self.image_based_autofocus()
            else:
                #make sure hardware autofocus worked
                attempts=0
                failure=False
                while not self.is_hardware_autofocus_done():
                    attempts+=1
                    time.sleep(.1)
                    if attempts>100:
                        failure=True
                        print("focus score is ",self.mmc.getCurrentFocusScore(),'breaking out')
                        break
                        print "not autofocusing correctly.. giving up after 10 seconds"
                if failure:
                    return None

        #get the image data       
        data=self.snap_image()
       
        #check whether it is in focus 
        #if not self.meets_focus_spec(data):
        #if not, attempt image based autofocus
        #self.image_based_autofocus()
        #data=self.snap_image()
            
        #check whether it is in focus
        #if not self.meets_focus_spec(data):
        #if not take a small stack around current point
        #and return most in focus image of that
        #data=self.take_best_of_stack()
        
        #calculate bounding box for data
        bbox=self.calc_bbox(x,y)
        
        print "todo get some real metadata"
        metadata=None
        return data,bbox
    def set_xy(self,x,y,use_focus_plane=False):
        flipx,flipy = self.get_xy_flip()

        if use_focus_plane:
            z  = self.get_focal_z(x,y)
            self.set_z(z)
        if self.transpose_xy:
            xt = x
            x = y
            y = xt
        #if flipx==1:
        #    x = -x
        #if flipy == 1:
        #    y = -y
        
        stg=self.mmc.getXYStageDevice()
        self.mmc.setXYPosition(stg,x,y)
        self.mmc.waitForDevice(stg)
        #print self.get_xy()
        


    def get_xy_flip(self):
        xystg=self.mmc.getXYStageDevice()
        flipx=int(self.mmc.getProperty(xystg,"TransposeMirrorX"))==1
        flipy=int(self.mmc.getProperty(xystg,"TransposeMirrorY"))==1

        return flipx,flipy
    def get_xy(self):
        #NEED TO IMPLEMENT IF NOT MICROMANAGER
        xystg=self.mmc.getXYStageDevice()
        
        flipx,flipy = self.get_xy_flip()

        x=self.mmc.getXPosition(xystg)
        y=self.mmc.getYPosition(xystg)

        if self.transpose_xy:
            xt = x
            x = y
            y = xt

        #if flipx:
        #    x = -x
        #if flipy:
        #    y = -y

        return (x,y)
    def get_z(self):
        focus_stage=self.mmc.getFocusDevice()
        return self.mmc.getPosition(focus_stage)
    def set_z(self,z):
        focus_stage=self.mmc.getFocusDevice()
        self.mmc.setPosition (focus_stage,z)
        self.mmc.waitForDevice(focus_stage)
        
    def get_pixel_size(self):
        #NEED TO IMPLEMENT IF NOT MICROMANAGER
        return self.mmc.getPixelSizeUm()

    def get_image(self,wait=True):
        rem = self.mmc.getRemainingImageCount()
        if wait:
            while (rem ==0):
                time.sleep(.01)
                rem = self.mmc.getRemainingImageCount()
        if rem>0:
            data = self.mmc.popNextImage()
            return self.flip_image(data)
        else:
            return None

    def get_frame_size_um(self):
        (sensor_width,sensor_height)=self.get_sensor_size()
        pixsize = self.get_pixel_size()
        flipx,flipy,trans = self.get_image_flip()
        if trans:
            temp = sensor_width
            sensor_width = sensor_height
            sensor_height = temp

        return (sensor_width*pixsize,sensor_height*pixsize)
        
        
    def calc_bbox(self,x,y):
        #do not need to implement
        (fw,fh)=self.get_frame_size_um()
        
        #we are going to follow the convention of upper left being 0,0 
        #and lower right being X,X where X is positive
        left = x - fw/2;
        right = x + fw/2;
        
        top = y - fh/2;
        bottom = y + fh/2;
        print "fw,fh",fw,fh
       
        return Rectangle(left,right,top,bottom)
        
    #@retry(tries= 5)
    def snap_image(self):
        #NEED TO IMPLEMENT IF NOT MICROMANAGER
        #with microscope in current configuration
        #snap a picture, and return the data as a numpy 2d array

        for attempt in range(5):
            try:
                # do thing
                self.mmc.snapImage()
            except:
                # perhaps reconnect, etc.
                print "snap failed.. cleaning up buffer"
                data=self.mmc.getImage()
            else:
              break
        else:
            # we failed all the attempts - deal with the consequences.
            print "we failed on 5 attempts to snap properly... freakout!"
            return None
        data = self.mmc.getImage()
        data = self.flip_image(data)
        return data


    def flip_image(self,data):

        (flipx,flipy,trans) = self.get_image_flip()
        if trans:
            data = np.transpose(data)
        if flipx:
            data=np.fliplr(data)
        if flipy:
            data=np.flipud(data)
        return data

    
    
    def get_sensor_size(self):
        #NEED TO IMPLEMENT IF NOT MICROMANAGER
        #get the sensor size in pixels
        height = self.mmc.getImageHeight()
        width = self.mmc.getImageWidth()
    
        #return the height and width in pixels
        return (width,height)
        
    def move_stage(self,x,y):
        #need to implement if not MICROMANAGER
        #move the stage to position x,y

        self.set_xy(x,y)
        
        
    def set_channel(self,channel):
        if channel not in self.get_channels():
            print "no such channel:" + channel
            return False
        
        self.mmc.setConfig(self.channelGroupName,channel)
        self.mmc.waitForConfig(self.channelGroupName,channel)
        self.mmc.setShutterOpen(False)
        
    def get_channels(self):
        return self.mmc.getAvailableConfigs(self.channelGroupName)
        
    def take_best_of_stack(self):
        print "need to implement take best of stack"
        return self.snap_image()  
    def meets_focus_spec(data):
        print "need to implement focus spec check"
        return True
    def get_image_flip(self):
        #when take_image returns an image
        #which way is up?
        
        cam=self.mmc.getCameraDevice()
        flip_x = int(self.mmc.getProperty(cam,"TransposeMirrorX"))==1
        flip_y = int(self.mmc.getProperty(cam,"TransposeMirrorY"))==1
        trans = int(self.mmc.getProperty(cam,"TransposeXY"))==1

        return (flip_x,flip_y,trans)

    def move_safe_and_focus(self,x,y): #MultiRibbons
        #lower objective, move the stage to position x,y
        focus_stage=self.mmc.getFocusDevice()
        #self.mmc.setRelativePosition(focus_stage,-3000.0)
        for j in range(300): #use small z steps to lower objective slowly
            self.mmc.setRelativePosition(-10.0)
            self.mmc.waitForDevice(focus_stage)
            time.sleep(0.2)
        self.mmc.waitForDevice(focus_stage)
        time.sleep(1)
        self.set_xy_new(x,y)
        time.sleep(40)
        stg=self.mmc.getXYStageDevice()
        self.mmc.waitForDevice(stg)
        #self.mmc.setRelativePosition(focus_stage,2700.0)
        for j in range(310): #use small z steps to raise objective slowly
            self.mmc.setRelativePosition(10.0)
            self.mmc.waitForDevice(focus_stage)
            time.sleep(0.2)
        self.mmc.setRelativePosition(-200.0)
        self.mmc.waitForDevice(focus_stage)
        i = 0
        while not self.mmc.isContinuousFocusLocked():
            self.mmc.setRelativePosition(focus_stage,20.0)
            self.mmc.waitForDevice(focus_stage)
            self.mmc.enableContinuousFocus(True)
            self.mmc.waitForDevice(self.mmc.getAutoFocusDevice())
            time.sleep(1)
            i = i+1
            if i==20:
                break

    def set_xy_new(self,x,y,use_focus_plane=False): #MultiRibbons
        # modified version of set_xy to be called by move_safe_and_focus with removed self.mmc.waitForDevice(stg)
        # to avoid error when waiting time exceeds 5s
        flipx,flipy = self.get_xy_flip()

        if use_focus_plane:
            z  = self.get_focal_z(x,y)
            self.set_z(z)
        if self.transpose_xy:
            xt = x
            x = y
            y = xt
        #if flipx==1:
        #    x = -x
        #if flipy == 1:
        #    y = -y

        stg=self.mmc.getXYStageDevice()
        self.mmc.setXYPosition(stg,x,y)
        #self.mmc.waitForDevice(stg)

    def set_autofocus_offset(self,offset): #MultiRibbons
        if self.has_hardware_autofocus():
            self.mmc.setAutoFocusOffset(offset)
            self.mmc.waitForDevice(self.mmc.getAutoFocusDevice())

    def get_autofocus_offset(self): #MultiRibbons
        if self.has_hardware_autofocus():
            return self.mmc.getAutoFocusOffset()
    
    def shutdown(self):
        self.mmc.unloadAllDevices()