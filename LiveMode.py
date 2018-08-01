
# -*- coding: utf-8 -*-
# based on pyqtgraph\examples\ImageItem.py
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np
import pyqtgraph as pg
import pyqtgraph.ptime as ptime



class VideoView(QtGui.QWidget):
    def __init__(self,imgSrc,exposure_times=dict([]),channelGroup="Channels"):
        super(VideoView,self).__init__()

        self.channelGroup=channelGroup
        self.exposure_times=exposure_times
        #self.setContentsMargins(0,0,0,0)
  
        self.imgSrc = imgSrc
        self.channels=self.imgSrc.get_channels()
        self.init_mmc()
        self.initUI()
        
        self.i = 0
        self.updateTime = ptime.time()
        self.fps = 0
        self.ended = False
        self.updateData()
       
    def init_mmc(self):   
        #filename="C:\Users\Smithlab\Documents\ASI_LUM_RETIGA_CRISP.cfg"
       
        
        self.imgSrc.set_exposure(50)

        Nch=len(self.channels)
        startChan=self.channels[Nch-1]
        for ch in self.channels:
            if 'dapi' in ch.lower():
                self.imgSrc.set_channel(ch)
        self.imgSrc.set_binning(1)
        print 'Binning is:', self.imgSrc.get_binning()
        self.imgSrc.startContinuousSequenceAcquisition(100)
    
    def initUI(self):

        self.chnButtons=[]
        self.expSpnBoxes=[]
        #print channels
        self.layout = QtGui.QHBoxLayout()
        #self.layout=QtGui.QGridLayout(margin=0,spacing=-1)

        self.layout.setSpacing(0)

      
            
        self.gv = pg.GraphicsView(background = 'k')
        self.gv.setContentsMargins(0,0,0,0)

        self.vb = pg.ViewBox()
        self.gv.setCentralItem(self.vb)
        self.vb.setAspectLocked()
        self.vb.setContentsMargins(0,0,0,0)

        self.img = pg.ImageItem()
        
        self.vb.addItem(self.img)
        self.layout.setContentsMargins(0,0,0,0)

        self.layout.addWidget(self.gv)
     
        self.setLayout(self.layout)
        self.setAutoFillBackground(True)  
        p = self.palette()
        p.setColor(self.backgroundRole(), QtCore.Qt.black)
        self.setPalette(p)
        
        
        keys = self.exposure_times.keys()
        
        gridlay=QtGui.QGridLayout(margin=0,spacing=-1)
        for i,ch in enumerate(self.channels):
            btn=QtGui.QPushButton(ch,self)
            self.chnButtons.append(btn)
            
            gridlay.addWidget(btn,i,0)

            spnBox=QtGui.QSpinBox(self)
            spnBox.setRange(1,10000)
            spnBox.setSingleStep(25)
            if ch in keys:
                spnBox.setValue(self.exposure_times[ch])
            else:
                spnBox.setValue(self.imgSrc.get_exposure())
            spnBox.setSuffix(" ms")
            btn.clicked.connect(self.make_channelButtonClicked(ch,spnBox))
            self.expSpnBoxes.append(spnBox)
            gridlay.addWidget(spnBox,i,1)
        
        Nch=len(self.channels)
        #auto_exposure button
        autoExpBtn = QtGui.QPushButton('Auto set exposure',self)
        autoExpBtn.clicked.connect(self.setExposureAuto)
        gridlay.addWidget(autoExpBtn,Nch,0)
        
        #reset focus offset button
        focResetBtn = QtGui.QPushButton('Reset Focus Position',self)
        focResetBtn.clicked.connect(self.imgSrc.reset_focus_offset)
        gridlay.addWidget(focResetBtn,Nch+1,0)
        
        #focus lock button
        self.isLockedBtn = QtGui.QPushButton('Focus Locked',self)
        self.isLockedBtn.setCheckable(True)
        self.isLockedBtn.clicked[bool].connect(self.toggleLock)
        isLocked=self.imgSrc.get_hardware_autofocus_state()
        if isLocked:
            self.isLockedBtn.setText('Focus Locked')
            self.isLockedBtn.setDown(True)
        else:
            self.isLockedBtn.setText('Focus UnLocked')
            self.isLockedBtn.setDown(False)
        gridlay.addWidget(self.isLockedBtn,Nch+2,0)


        self.layout.addLayout(gridlay)
        

    def getExposureTimes(self):
        exposure_times=dict([])
        for i,ch in enumerate(self.channels):
            spnBox=self.expSpnBoxes[i]
            exposure_times[ch]=spnBox.value()
        return exposure_times
        
    def setExposureAuto(self,evt):
        
        self.imgSrc.stopSequenceAcquisition() 
        perc=95; #the goal is to make the X percentile value equal to Y percent of the maximum value
        #perc is X
        desired_frac=.7 #desired_frac is Y
        max_exposure = 3000 #exposure times shall not end up more than this
        close_frac = .2 #fractional change in exposure for which we will just trust the math
        max_val=self.imgSrc.get_max_pixel_value()
  
        #loop over the channels
        for i,ch in enumerate(self.channels):
            img_counter =0 #counter to count how many snaps it takes us
            if 'Dark' not in ch: #don't set the 'Dark' channel for obvious reasons
                print ch
                #setup to use the channel
                self.imgSrc.set_channel(ch)
                
                
                #get current exposure
                spnBox=self.expSpnBoxes[i]
                curr_exposure=spnBox.value()
                curr_frac=0 #initially set to 0
                
                #follow loop till we get it right
                while 1:
                
                    self.imgSrc.set_exposure(curr_exposure)
                    img=self.imgSrc.snap_image()
                    img_counter+=1
                    
                    vec=img.flatten()
                    
                    #the value which is at the perc percentile
                    perc_val=np.percentile(vec,perc)
                    #the maximum value it could have
                    
                    
                    #what fraction of saturation we are at
                    curr_frac=perc_val/max_val
                    
                    #save the old exposure
                    old_exposure=curr_exposure
                    
                    #what fraction we should change the exposure assuming linearity of response
                    #to achieve the desired percentage                  
                    frac_change=desired_frac/curr_frac
                    
                    if curr_frac > .9999: #if the image is saturated, our calculation doesn't work
                        curr_exposure=int(.5*curr_exposure) #so cut the exposure time in half
                    if frac_change > 10: #don't make the exposure more than 10 times different
                        curr_exposure=int(10*curr_exposure)
                    else: #otherwise go ahead and change the exposure time accordingly
                        curr_exposure=int(curr_exposure*frac_change)
                        
                    #just don't make the exposure times more than 3 seconds               
                    if curr_exposure>max_exposure:
                        curr_exposure=max_exposure
                    print ("old:%d , new:%d"%(old_exposure,curr_exposure))   
                    if curr_exposure == max_exposure:
                        break
                    #if we haven't changed the exposure
                    if curr_exposure==old_exposure:
                        break
                    #if exposure time is within 20% of where it was 
                    if abs(curr_exposure-old_exposure)/old_exposure<.2:
                        break #just trust it will work out and leave loop
                
                print "img_counter:%d"%img_counter
                #update the spnBox with the new exposure time    
                spnBox.setValue(curr_exposure)
                   
                
    def toggleLock(self,pressed):
        
        if pressed:
            self.isLockedBtn.setText('Focus Locked')
            self.imgSrc.set_hardware_autofocus_state(True)
          
        else:
            self.imgSrc.set_hardware_autofocus_state(False)
            self.isLockedBtn.setText('Focus UnLocked')
           
            
            
    def make_channelButtonClicked(self,ch,spnBox):
        def channelButtonClicked():
            #print ch
            #print spnBox.value()
            self.imgSrc.stopSequenceAcquisition() 
            self.imgSrc.set_channel(ch)
            expTime=spnBox.value()
            self.imgSrc.set_exposure(expTime)
            self.imgSrc.startContinuousSequenceAcquisition(expTime)
        return channelButtonClicked
        
    def closeEvent(self,evt):
        self.imgSrc.stopSequenceAcquisition()
        self.imgSrc.set_binning(2)
        print 'Binning is:', self.imgSrc.get_binning()
        print "stopped acquisition"
        #if self.timer is not None:
        #    print "cancelling timer if it exists"
        #    self.timer.cancel()
        self.ended = True
        #self.destroy()
        return QtGui.QWidget.closeEvent(self,evt)
        #evt.accept()
        

    def display8bit(self,image, display_min, display_max): 
        image = np.array(image, copy=True)
        image2=image.clip(display_min, display_max)
        image2 -= display_min
        image2 //= (display_max - display_min + 1) / 256.
        return image2.astype(np.uint8)

    def lut_convert16as8bit(self,image, display_min, display_max) :
        lut = np.arange(2**16, dtype='uint16')

        newlut = self.display8bit(lut, display_min, display_max)
        print "min to max",np.min(newlut),np.max(newlut)
        newimage = np.take(newlut, image)
        print "new image shape",newimage.shape
        return newimage

    def updateData(self):
    
       
        data =  self.imgSrc.get_image(wait=False)
        if data is not None:
            data = np.rot90(data, k=3)
            self.img.setImage(data,autoLevels=True)

        if not self.ended:
            self.timer = QtCore.QTimer.singleShot(self.imgSrc.get_exposure(), self.updateData)
        now = ptime.time()
        fps1 = 1.0 / (now-self.updateTime)
        self.updateTime = now
        self.fps = self.fps * 0.6 + fps1 * 0.4
        if self.i == 0:
            print "%0.1f fps" % self.fps
        self.update()
            

def launchLive(imgSrc,exposure_times):  
    import sys  
  
    vidview = VideoView(imgSrc,exposure_times)
    vidview.setGeometry(250,50,1100,1000)
    vidview.show()

    vidview.updateData()
    vidview.setWindowTitle('live view')
    
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()

    return vidview.getExposureTimes()

if __name__ == '__main__':

    import sys
    import faulthandler

    from imageSourceMM import imageSource
    app = QtGui.QApplication(sys.argv)
    faulthandler.enable()


    defaultMMpath = "C:\Program Files\Micro-Manager-1.4"
    configFile = QtGui.QFileDialog.getOpenFileName(
        None, "pick a uManager cfg file", defaultMMpath, "*.cfg")
    configFile = str(configFile.replace("/", "\\"))
    print configFile
    imgSrc = imageSource(configFile)

    print "loaded configuration file"
    launchLive(imgSrc,dict([]))
    #app.exec_()
    print "got out of the event loop"
    imgSrc.shutdown()
    print "reset micromanager core"
    sys.exit()
