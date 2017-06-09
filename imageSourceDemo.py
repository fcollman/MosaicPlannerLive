import numpy as np
import time
from Rectangle import Rectangle
import wx

class imageSource():
    
    def __init__(self,configFile,channelGroupName='Channels',
                 use_focus_plane  = False, focus_points=None,
                 transpose_xy = False, logfile='MP_MM.txt',
                 MasterArduinoPort = None, interframe_time= 10, filtswitch = None):
      #NEED TO IMPLEMENT IF NOT MICROMANAGER
     
      self.x = 0
      self.y = 0
      self.z = 0
      self.binning = 1
      self.exposure = 100
      self.hardware_autofocus_state = True
      self.channels = []
      self.exposure_times = []
      self.offset = 0
      self.use_focus_plane = False

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

    def reset_piezo(self,cfg):
        pass

    def stop_hardware_triggering(self):
        pass

    def setup_hardware_triggering(self,channels,exposure_times):
        self.channels = channels
        self.exposure_times = exposure_times
        
    def startHardwareSequence(self):
        pass

    def set_binning(self,bin=1):
        self.binning = bin

    def get_binning(self):     
        return self.binning

    def image_based_autofocus(self,chan=None):
        return 0.0

    def get_max_pixel_value(self):  
        return np.power(2,16)-1

    def get_exposure(self):
        return self.exposure

    def set_exposure(self,exp_msec):
        self.exposure = exp_msec
    
    def reset_focus_offset(self):
        pass
  
    def get_hardware_autofocus_state(self):
        return self.hardware_autofocus_state
           
    def set_hardware_autofocus_state(self,state):
        self.hardware_autofocus_state = state
        
    def has_hardware_autofocus(self):
        #NEED TO IMPLEMENT IF NOT MICROMANAGER
        return True
        
    def stopSequenceAcquisition(self):
        pass
        
    def startContinuousSequenceAcquisition(self,val):
        pass

    def is_hardware_autofocus_done(self):
        return self.hardware_autofocus_state
        

    def take_hardware_snap(self):     
        images = []
        for ch in self.channels:
            images.append(np.random(self.get_sensor_size()))
        return images


    def take_image(self,x,y):
        #do not need to re-implement
        #moves scope to x,y - focus scope - snap picture
        #using the configured exposure time

        #print "is continuous focus enabled",self.mmc.isContinuousFocusEnabled()
        #print "is continuous focus locked",self.mmc.isContinuousFocusLocked()

        if not self.get_hardware_autofocus_state():
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
                        print("focus score is ",0.0,'breaking out')
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
        
        self.x = x
        self.y = y
        #print self.get_xy()
        


    def get_xy_flip(self):
        return False,False
    def get_xy(self):
        #NEED TO IMPLEMENT IF NOT MICROMANAGER

        
        flipx,flipy = self.get_xy_flip()

        x=self.x
        y=self.y

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
        return self.z
    def set_z(self,z):
        self.z = z
        
    def get_pixel_size(self):
        #NEED TO IMPLEMENT IF NOT MICROMANAGER
        return .1

    def make_random_image(self):
        #return np.random.random(self.get_sensor_size())
        return np.random.randint(0,2**16 - 1,self.get_sensor_size(),np.uint16)
    def get_image(self,wait=True):
        return self.make_random_image()

    def get_frame_size_um(self):
        (sensor_width,sensor_height)=(self.get_sensor_size())
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
        data = self.make_random_image()
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
        #return the height and width in pixels
        return (2048,2048)
        
    def move_stage(self,x,y):
        #need to implement if not MICROMANAGER
        #move the stage to position x,y

        self.set_xy(x,y)
        
        
    def set_channel(self,channel):
        self.channel = channel
        
    def get_channels(self):
        return ['QuadBand1DAPI','QuadBand1Alexa488','QuadBand1Alexa594','QuadBand1Alexa647']
        
    def take_best_of_stack(self):
        print "need to implement take best of stack"
        return self.snap_image()  
    def meets_focus_spec(data):
        print "need to implement focus spec check"
        return True
    def get_image_flip(self):
        return (False,False,True)

    def move_safe_and_focus(self,x,y): #MultiRibbons
        #lower objective, move the stage to position x,y
        focus_stage=self.mmc.getFocusDevice()
        #self.mmc.setRelativePosition(focus_stage,-3000.0)
        for j in range(300): #use small z steps to lower objective slowly
            self.z -= 10
            time.sleep(0.2)

        time.sleep(1)
        self.set_xy_new(x,y)
        time.sleep(40)

        #self.mmc.setRelativePosition(focus_stage,2700.0)
        for j in range(310): #use small z steps to raise objective slowly
            self.z += 10 
            time.sleep(0.2)
        self.z -= 200 
        i = 0
        for i in range(5):
            self.z += 20 
            time.sleep(1)
        self.set_hardware_autofocus_state(True)

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

        self.set_xy(x,y)

    def set_autofocus_offset(self,offset): #MultiRibbons
        self.offset = offset

    def get_autofocus_offset(self): #MultiRibbons
        return self.offset
        
    def shutdown(self):
        pass