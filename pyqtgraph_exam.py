
# -*- coding: utf-8 -*-
# based on pyqtgraph\examples\ImageItem.py
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np
import pyqtgraph as pg
import pyqtgraph.ptime as ptime
import MMCorePy
import cv2
from pyqtgraph.widgets.RawImageWidget import RawImageGLWidget, RawImageWidget

class VideoView(QtGui.QWidget):
    def __init__(self,mmc,channelGroup="Channels"):
        super(VideoView,self).__init__()

        self.channelGroup=channelGroup
        
        self.mmc = mmc
        self.init_mmc()
        self.initUI()
        
        self.i = 0
        self.updateTime = ptime.time()
        self.fps = 0
        
        self.updateData()
       
    def init_mmc(self):   
        filename="C:\Users\Smithlab\Documents\ASI_LUM_RETIGA_CRISP.cfg"
        self.mmc.loadSystemConfiguration(filename)
        self.mmc.enableStderrLog(False)
        self.mmc.enableDebugLog(False)
        # # mmc.setCircularBufferMemoryFootprint(100)
        self.cam=self.mmc.getCameraDevice()
        self.mmc.setExposure(100)
        self.mmc.setProperty(self.cam, 'Gain', 10)
        self.mmc.setConfig(self.channelGroup,'Violet')
        self.mmc.waitForConfig(self.channelGroup,'Violet')
        self.mmc.startContinuousSequenceAcquisition(1)
    
    def initUI(self):
        #channels=mmc.getAvailableConfigs(self.channelGroup)
        channels=('ch1','ch2','ch3','ch4','ch5')
        self.chnButtons=[]
        self.expSpnBoxes=[]
        #print channels
        self.layout = QtGui.QGridLayout()
        for i,ch in enumerate(channels):
            btn=QtGui.QPushButton(ch,self)
            self.chnButtons.append(btn)
            
            self.layout.addWidget(btn,i,1)
            
            spnBox=QtGui.QSpinBox(self)
            spnBox.setRange(1,10000)
            spnBox.setSingleStep(50)
            spnBox.setValue(300)
            spnBox.setSuffix("ms")
            btn.clicked.connect(self.make_channelButtonClicked(ch,spnBox))
            self.expSpnBoxes.append(spnBox)
            self.layout.addWidget(spnBox,i,2)
            
        self.glw=pg.GraphicsLayoutWidget()
        self.p1=self.glw.addPlot()
        self.img = pg.ImageItem()
        self.p1.addItem(self.img)
        
        self.layout.addWidget(self.glw,0,0,len(channels),1)
   
        self.setLayout(self.layout)
              
        
        self.setGeometry(200,200,1000,700)
        self.setWindowTitle('message me')
        self.show()
    
    def make_channelButtonClicked(self,ch,spnBox):
        def channelButtonClicked():
            print ch
            print spnBox.value()
            self.mmc.stopSequenceAcquisition() 
            self.mmc.setConfig(self.channelGroup,ch)
            self.mmc.setExposure(spnBox.value())
            self.mmc.waitForConfig(self.channelGroup,ch)
            self.mmc.startContinuousSequenceAcquisition(1)
        return channelButtonClicked
        
    def closeEvent(self,evt):
        self.mmc.stopSequenceAcquisition() 
        print "close"
        
    def updateData(self):
    
        remcount = self.mmc.getRemainingImageCount()
        #remcount=0
        if remcount > 0:
            # rgb32 = mmc.popNextImage()
            rgb32 =  self.mmc.getLastImage()
            gray = rgb32.view(dtype=np.uint8).transpose()
            #gray=cv2.equalizeHist(gray)
            self.img.setImage(gray,autoLevels=True)
            #cv2.imshow('Video', gray)
        else:
            print('No frame')
        

        QtCore.QTimer.singleShot(10, self.updateData)
        now = ptime.time()
        fps1 = 1.0 / (now-self.updateTime)
        self.updateTime = now
        self.fps = self.fps * 0.9 + fps1 * 0.1
        if self.i == 0:
            print "%0.1f fps" % self.fps
            
        
app = QtGui.QApplication([])
mmc = MMCorePy.CMMCore()

win = VideoView(mmc)
#win.show() 
#win.updateData()

win.setWindowTitle('multi-video display')


## Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
        
        