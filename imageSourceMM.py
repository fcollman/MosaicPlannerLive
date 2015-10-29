import numpy as np
import MMCorePy
from PIL import Image
import time
from Rectangle import Rectangle

class imageSource():
    
    def __init__(self,configFile,channelGroupName='Channels',use_focus_plane  = False,focus_points=None):
      #NEED TO IMPLEMENT IF NOT MICROMANAGER
     
        self.configFile=configFile
        self.mmc = MMCorePy.CMMCore() 
        self.mmc.enableStderrLog(True)
        self.mmc.enableDebugLog(True)
        self.mmc.loadSystemConfiguration(self.configFile)
       
        self.channelGroupName=channelGroupName

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
            self.define_focal_plane(points)

        #set the exposure to use
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

    def image_based_autofocus(self,chan=None):
        if chan is not None:
            self.set_channel(chan)
        self.mmc.fullFocus()
        return self.mmc.getLastFocusScore()

    def get_max_pixel_value(self):
        bit_depth=self.mmc.getImageBitDepth()
        return np.power(2,bit_depth)-1
        
    def set_exposure(self,exp_msec):
      #NEED TO IMPLEMENT IF NOT MICROMANAGER
        self.mmc.setExposure(exp_msec)
    
    def reset_focus_offset(self):
        if self.has_hardware_autofocus():
            focusDevice=self.mmc.getAutoFocusDevice()
            self.mmc.setProperty(focusDevice,"CRISP State","Reset Focus Offset")
  
    def get_hardware_autofocus_state(self):
        if self.has_hardware_autofocus():
            return self.mmc.isContinuousFocusLocked()
           
    def set_hardware_autofocus_state(self,state):
        if self.has_hardware_autofocus():
            self.mmc.enableContinuousFocus(state)
        
    def has_hardware_autofocus(self):
        #NEED TO IMPLEMENT IF NOT MICROMANAGER
        return self.has_continuous_focus
        
        
    def is_hardware_autofocus_done(self):
      #NEED TO IMPLEMENT IF NOT MICROMANAGER
        #hardware autofocus assumes the focus score is <1 when focused
        score=self.mmc.getCurrentFocusScore()
        if abs(score)<1:
            print "locked on"
            return True
        else:
            print "score %f not locked on"%score
            return False
        
        

    
    def take_image(self,x,y):
        #do not need to re-implement
        #moves scope to x,y - focus scope - snap picture
        #using the configured exposure time
    
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
                    time.sleep(.1)
                    attempts+=1
                    if attempts>100:
                        failure=True
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
        if flipx==1:
            x = -x
        if flipy == 1:
            y = -y
        
        stg=self.mmc.getXYStageDevice()
        self.mmc.setXYPosition(stg,x,y)
        self.mmc.waitForDevice(stg)
        print self.get_xy()
        


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
        
        if flipx:
            x = -x
        if flipy:
            y = -y

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
        
       
        return Rectangle(left,right,top,bottom)
        
    
    def snap_image(self):
        #NEED TO IMPLEMENT IF NOT MICROMANAGER
        #with microscope in current configuration
        #snap a picture, and return the data as a numpy 2d array
        self.mmc.snapImage()
        data = self.mmc.getImage()
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
        return (height,width)
        
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
        flip_x = int(self.mmc.getProperty(cam,"TransposeMirrorX"))==0
        flip_y = int(self.mmc.getProperty(cam,"TransposeMirrorY"))==0
        trans = int(self.mmc.getProperty(cam,"TransposeXY"))

        return (flip_x,flip_y,trans) 