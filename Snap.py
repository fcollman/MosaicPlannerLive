
# -*- coding: utf-8 -*-
# based on pyqtgraph\examples\ImageItem.py
from PyQt4 import QtCore, QtGui, uic
import numpy as np
import pyqtgraph as pg
import os.path
from imageSourceMM import imageSource

# class myHistographLUTItem(pg.HistogramLUTItem):
#     def __init__(self,*kargs,**kwargs):
#         super(myHistographLUTItem, self).__init__(*kargs,**kwargs)
#         self.plot.rotate(-90)
#         self.gradient.setOrientation('bottom')

class SnapView(QtGui.QWidget):
    changedExposureTimes = QtCore.Signal()

    def __init__(self,imgSrc,exposure_times=dict([]),channelGroup="Channels"):
        super(SnapView,self).__init__()

        self.channelGroup=channelGroup
        self.exposure_times=exposure_times
        #self.setContentsMargins(0,0,0,0)
        self.mmc = imgSrc.mmc
        self.imgSrc = imgSrc
        self.channels=self.mmc.getAvailableConfigs(self.channelGroup)
        #self.init_mmc()
        self.initUI()
        
        
        self.i = 0
        self.ended = False

       
    # def init_mmc(self):
    #     #filename="C:\Users\Smithlab\Documents\ASI_LUM_RETIGA_CRISP.cfg"
    #     #self.mmc.loadSystemConfiguration(filename)
    #     #self.mmc.enableStderrLog(False)
    #     #self.mmc.enableDebugLog(False)
    #     # # mmc.setCircularBufferMemoryFootprint(100)
    #     #self.cam=self.mmc.getCameraDevice()
    #     #self.mmc.setExposure(50)
    #     #self.mmc.setProperty(self.cam, 'Gain', 1)
    #     Nch=len(self.channels)
    #     startChan=self.channels[Nch-1]

    
    def initUI(self):

        currpath=os.path.split(os.path.realpath(__file__))[0]
        filename = os.path.join(currpath,'Snap.ui')
        uic.loadUi(filename,self)


        self.chnButtons=[]
        self.expSpnBoxes=[]

        self.img = pg.ImageItem()
        p1 = self.graphicsLayoutWidget.addPlot()

        #self.gv.setCentralItem(self.img)
        #self.vb.addItem(self.img)
        #self.layout.setContentsMargins(0,0,0,0)
        #self.graphicsLayoutWidget.addItem(self.img,0,0)
        p1.addItem(self.img)
        self.hist = pg.HistogramLUTItem()
        self.hist.setImageItem(self.img)
        #self.hist.setRotation(-90)

        self.graphicsLayoutWidget.addItem(self.hist,0,1)




        #self.layout.addWidget(self.img)
     
        #self.setLayout(self.layout)
        #self.setAutoFillBackground(True)
        #p = self.palette()
        #p.setColor(self.backgroundRole(), QtCore.Qt.black)
        #self.setPalette(p)
        
        
        keys = self.exposure_times.keys()
        
        #gridlay=QtGui.QGridLayout(margin=0,spacing=-1)
        camera = self.mmc.getCameraDevice()
        self.mmc.setProperty(camera,'Binning','1x1')
        print 'Binning is:', self.mmc.getProperty(camera,'Binning')
        for i,ch in enumerate(self.channels):
            btn=QtGui.QPushButton(ch,self)
            self.chnButtons.append(btn)
            
            self.gridlay.addWidget(btn,i,0)
            
            spnBox=QtGui.QSpinBox(self)
            spnBox.setRange(1,10000)
            spnBox.setSingleStep(25)
            if ch in keys:
                spnBox.setValue(self.exposure_times[ch])
            else:
                spnBox.setValue(self.mmc.getExposure())
            spnBox.setSuffix(" ms")
            btn.clicked.connect(self.make_channelButtonClicked(ch,spnBox))
            self.expSpnBoxes.append(spnBox)
            self.gridlay.addWidget(spnBox,i,1)
        
        Nch=len(self.channels)
        self.exitButton.clicked.connect(self.exitClicked)

        #auto_exposure button
        # snapExpBtn = QtGui.QPushButton('Snap exposures',self)
        # snapExpBtn.clicked.connect(self.snapExposure)
        # self.gridlay.addWidget(snapExpBtn,Nch,0)
        
        #reset focus offset button
        # focResetBtn = QtGui.QPushButton('Reset Focus Position',self)
        # focResetBtn.clicked.connect(self.imgSrc.reset_focus_offset)
        # self.gridlay.addWidget(focResetBtn,Nch+1,0)
        
        #focus lock button
        # self.isLockedBtn = QtGui.QPushButton('Focus Locked',self)
        # self.isLockedBtn.setCheckable(True)
        # self.isLockedBtn.clicked[bool].connect(self.toggleLock)
        # isLocked=self.imgSrc.get_hardware_autofocus_state()
        # if isLocked:
        #     self.isLockedBtn.setText('Focus Locked')
        #     self.isLockedBtn.setDown(True)
        # else:
        #     self.isLockedBtn.setText('Focus UnLocked')
        #     self.isLockedBtn.setDown(False)
        # self.gridlay.addWidget(self.isLockedBtn,Nch+2,0)

    def exitClicked(self,evt):
        self.hide()
        self.changedExposureTimes.emit()

    def getExposureTimes(self):
        exposure_times=dict([])
        for i,ch in enumerate(self.channels):
            spnBox=self.expSpnBoxes[i]
            exposure_times[ch]=spnBox.value()
        return exposure_times

    def snapExposure(self,evt):

        self.ended = True
        data = None
        Nch = len(self.channels)

        for i,ch in enumerate(self.channels):
            if 'Dark' not in ch:
                print ch
                self.mmc.setConfig(self.channelGroup,ch)
                self.mmc.waitForConfig(self.channelGroup,ch)
                spnBox=self.expSpnBoxes[i]
                curr_exposure=spnBox.value()
                self.mmc.setExposure(curr_exposure)
                self.mmc.snapImage()
                img=self.mmc.getImage()
                if data is None:
                    data = np.zeros((Nch,img.shape[0],img.shape[1]))
                data[i,:,:]=img
                print(np.max(img))
        self.img.setImage(data,xvals = np.array(range(Nch)))
        self.img.setLevels(0,2**self.mmc.getImageBitDepth())
        self.hist.setLevels(0,2**self.mmc.getImageBitDepth())

    # def autoExposure(self,evt):
    #
    #     self.mmc.stopSequenceAcquisition()
    #
    #     perc=95; #the goal is to make the X percentile value equal to Y percent of the maximum value
    #     #perc is X
    #     desired_frac=.7 #desired_frac is Y
    #     max_exposure = 3000 #exposure times shall not end up more than this
    #     close_frac = .2 #fractional change in exposure for which we will just trust the math
    #     bit_depth=self.mmc.getImageBitDepth()
    #     max_val=np.power(2,bit_depth)
    #     #loop over the channels
    #     for i,ch in enumerate(self.channels):
    #         img_counter =0 #counter to count how many snaps it takes us
    #         if 'Dark' not in ch: #don't set the 'Dark' channel for obvious reasons
    #             print ch
    #             #setup to use the channel
    #             self.mmc.setConfig(self.channelGroup,ch)
    #             self.mmc.waitForConfig(self.channelGroup,ch)
    #
    #
    #             #get current exposure
    #             spnBox=self.expSpnBoxes[i]
    #             curr_exposure=spnBox.value()
    #             curr_frac=0 #initially set to 0
    #
    #             #follow loop till we get it right
    #             while 1:
    #
    #                 self.mmc.setExposure(curr_exposure)
    #                 self.mmc.snapImage()
    #                 img_counter+=1
    #                 img=self.mmc.getImage()
    #                 vec=img.flatten()
    #
    #                 #the value which is at the perc percentile
    #                 perc_val=np.percentile(vec,perc)
    #                 #the maximum value it could have
    #
    #
    #                 #what fraction of saturation we are at
    #                 curr_frac=perc_val/max_val
    #
    #                 #save the old exposure
    #                 old_exposure=curr_exposure
    #
    #                 #what fraction we should change the exposure assuming linearity of response
    #                 #to achieve the desired percentage
    #                 frac_change=desired_frac/curr_frac
    #
    #                 if curr_frac > .9999: #if the image is saturated, our calculation doesn't work
    #                     curr_exposure=int(.5*curr_exposure) #so cut the exposure time in half
    #                 if frac_change > 10: #don't make the exposure more than 10 times different
    #                     curr_exposure=int(10*curr_exposure)
    #                 else: #otherwise go ahead and change the exposure time accordingly
    #                     curr_exposure=int(curr_exposure*frac_change)
    #
    #                 #just don't make the exposure times more than 3 seconds
    #                 if curr_exposure>max_exposure:
    #                     curr_exposure=max_exposure
    #                 print ("old:%d , new:%d"%(old_exposure,curr_exposure))
    #                 if curr_exposure == max_exposure:
    #                     break
    #                 #if we haven't changed the exposure
    #                 if curr_exposure==old_exposure:
    #                     break
    #                 #if exposure time is within 20% of where it was
    #                 if abs(curr_exposure-old_exposure)/old_exposure<.2:
    #                     break #just trust it will work out and leave loop
    #
    #             print "img_counter:%d"%img_counter
    #             #update the spnBox with the new exposure time
    #             spnBox.setValue(curr_exposure)
    #
                
    # def toggleLock(self,pressed):
    #
    #     if pressed:
    #         self.isLockedBtn.setText('Focus Locked')
    #         self.imgSrc.set_hardware_autofocus_state(True)
    #
    #     else:
    #         self.imgSrc.set_hardware_autofocus_state(False)
    #         self.isLockedBtn.setText('Focus UnLocked')
    #
    #
            
    def make_channelButtonClicked(self,ch,spnBox):
        def channelButtonClicked():
            #print ch
            #print spnBox.value()

            # self.mmc.stopSequenceAcquisition()
            # self.mmc.clearCircularBuffer()
            self.mmc.setConfig(self.channelGroup,ch)
            expTime=spnBox.value()
            self.mmc.setExposure(expTime)
            self.mmc.waitForConfig(self.channelGroup,ch)
            self.mmc.snapImage()
            data= self.mmc.getImage()
            self.img.setImage(data)
            # self.mmc.startContinuousSequenceAcquisition(expTime)
        return channelButtonClicked
        
    def closeEvent(self,evt):
        camera = self.mmc.getCameraDevice()
        self.mmc.setProperty(camera,'Binning','2x2')
        print 'Binning is:', self.mmc.getProperty(camera,'Binning')
        self.changedExposureTimes.emit()
        return QtGui.QWidget.closeEvent(self,evt)
        #evt.accept()

def launchSnap(imgSrc,exposure_times):
    import sys  
    imgSrc.set_binning(1)
    dlg = SnapView(imgSrc,exposure_times)
    dlg.setWindowTitle('snap view')
    #vidview.setGeometry(250,50,1100,1000)
    dlg.setModal(True)
    dlg.show()


    
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
    imgSrc.set_binning(2)
    exp= dlg.getExposureTimes()
    print(exp)
    return exp

if __name__ == '__main__':

    import sys
    import faulthandler
    from configobj import ConfigObj
    from MosaicPlanner import SETTINGS_FILE
    import datetime
    app = QtGui.QApplication(sys.argv)
    faulthandler.enable()
    cfg = ConfigObj(SETTINGS_FILE,unrepr=True)

    #mmc = MMCorePy.CMMCore()
    #defaultMMpath = "C:\Program Files\Micro-Manager-1.4"
    #configFile = QtGui.QFileDialog.getOpenFileName(
    #    None, "pick a uManager cfg file", defaultMMpath, "*.cfg")
    #configFile = str(configFile.replace("/", "\\"))
    configFile = cfg['MosaicPlanner']['MM_config_file']
    print configFile
    dt=datetime.datetime.now()
    logname=dt.strftime('SnapLog_%Y%m%d_%H%M.txt')
    imgSrc = imageSource(configFile,logfile=logname)

    #mmc.loadSystemConfiguration(configFile)
    print "loaded configuration file"
    imgSrc.set_binning(1)

    launchSnap(imgSrc,dict([]))
    #app.exec_()
    print "got out of the event loop"
    imgSrc.mmc.reset()
    print "reset micromanager core"
    sys.exit()
