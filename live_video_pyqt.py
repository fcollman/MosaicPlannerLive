#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""
Created on 23 March 2014.
@author: Eugene Dvoretsky

Live video acquisition with Micro-Manager adapter and opencv.
Another example with exposure and gain control.
"""
import numpy as np
import cv2
import MMCorePy
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
import time

WIDTH, HEIGHT = 320, 240
DEVICE = ['Camera', 'DemoCamera', 'DCam']
# DEVICE = ['Camera', 'OpenCVgrabber', 'OpenCVgrabber']
# DEVICE = ['Camera', "BaumerOptronic", "BaumerOptronic"]

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(695, 798)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.rawGLImg = RawImageGLWidget(self.centralwidget)
        MainWindow.setCentralWidget(self.centralwidget)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        
def set_mmc_resolution(mmc, width, height):
    """Select rectangular ROI in center of the frame.
    """
    x = (mmc.getImageWidth() - width) / 2
    y = (mmc.getImageHeight() - height) / 2
    #mmc.setROI(x, y, width, height)




mmc = MMCorePy.CMMCore()
filename="C:\Users\Smithlab\Documents\ASI_LUM_RETIGA_CRISP.cfg"
mmc.loadSystemConfiguration(filename)
mmc.enableStderrLog(False)
mmc.enableDebugLog(False)
# mmc.setCircularBufferMemoryFootprint(100)
cam=mmc.getCameraDevice()
mmc.setExposure(50)
mmc.setConfig('Channels','Violet')
mmc.waitForConfig('Channels','Violet')
#self.mmc.setShutterOpen(False)

#cv2.namedWindow('MM controls')
#if mmc.hasProperty(cam, 'Gain'):
#    cv2.createTrackbar(
#        'Gain', 'MM controls',
#        int(float(mmc.getProperty(cam, 'Gain'))),
#        int(mmc.getPropertyUpperLimit(cam, 'Gain')),
#        lambda value: mmc.setProperty(cam, 'Gain', value))
#if mmc.hasProperty(cam, 'Exposure'):
#    cv2.createTrackbar(
#       'Exposure', 'MM controls',
#      int(float(mmc.getProperty(cam, 'Exposure'))),
#     100,  # int(mmc.getPropertyUpperLimit(DEVICE[0], 'Exposure')),
#        lambda value: mmc.setProperty(cam, 'Exposure', int(value)))
def myExitHandler(): 
    global mmc
    mmc.stopSequenceAcquisition()
    mmc.reset()
    
set_mmc_resolution(mmc, WIDTH, HEIGHT)
mmc.setProperty(cam, 'Gain', 1)
mmc.snapImage()  # Baumer workaround
data=mmc.getImage()
gray = data.view(dtype=np.uint8)
mmc.startContinuousSequenceAcquisition(50)
       
#QtGui.QApplication.setGraphicsSystem('raster')
app = QtGui.QApplication([])
app.aboutToQuit.connect(myExitHandler) 
#mw = QtGui.QMainWindow()
#mw.resize(800,800)

win = QtGui.QMainWindow()
win.setWindowTitle('pyqtgraph example: VideoSpeedTest')
win.resize(800,800)
gv = pg.GraphicsView()
win.setCentralWidget(gv)

vb = pg.ViewBox()
gv.setCentralItem(vb)
vb.setAspectLocked()
img = pg.ImageItem()
img.setImage(gray)
vb.addItem(img)
vb.setRange(QtCore.QRectF(0, 0, 512, 512))

win.show()



def update():
    global img,mmc
    remcount = mmc.getRemainingImageCount()
    #print remcount

    #print('Images in circular buffer: %s') % remcount
  
    if remcount > 0:
        rgb32 = mmc.popNextImage()
        #rgb32 = mmc.getLastImage()
        gray = rgb32.view(dtype=np.uint8)
        gray=cv2.equalizeHist(gray)
        img.setImage(gray)
       
        #cv2.imshow('Video', gray)
    #else:
    #    print('No frame')

viewtimer = QtCore.QTimer()
viewtimer.timeout.connect(update)
viewtimer.start(5)
        

