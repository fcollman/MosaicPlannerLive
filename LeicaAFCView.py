from PyQt4 import QtCore, QtGui, uic
import numpy as np
import pyqtgraph as pg
import os
from LeicaDMI import LeicaDMI

class LeicaAFCView(QtGui.QWidget):

    def __init__(self,imgSrc,port):
        super(LeicaAFCView,self).__init__()
        self.initUI()
        self.dmi = LeicaDMI(port=port)
        self.imgSrc = imgSrc

    def initUI(self):
        # load the UI from layout file
        currpath = os.path.split(os.path.realpath(__file__))[0]
        filename = os.path.join(currpath, 'LeicaAFCView.ui')
        uic.loadUi(filename, self)

        # add a pyqtgraph image to graphics view
        self.img1 = pg.ImageItem()
        self.imageplot1 = self.imageGraphicsLayout.addPlot()
        self.imageplot1.setAspectLocked(True, ratio=1)
        self.imageplot1.addItem(self.img1)
        self.hist1 = pg.HistogramLUTItem()
        self.hist1.setImageItem(self.img1)
        self.image1_graphicsLayoutWidget.addItem(self.hist1, 0, 1)
        self.img1.setLevels(0, self.imgSrc.get_max_pixel_value())
        self.hist1.setLevels(0, self.imgSrc.get_max_pixel_value())

        self.dataplot = self.afcGraphicsLayout.addPlot()

    def takeAFCImage(self,evt):
        data=self.dmi.get_AFC_image()
        self.dataplot.clear()
        self.dataplot.plot(data)

    def onHoldHere(self,evt):
        self.dmi.holdHere()

    def holdOn(self,evt):
        self.dmi.set_AFC_hold(True)

    def getLEDIntensity(self,evt):
        intensity = self.dmi.get_AFC_intensity()
        self.LEDspinBox.blockSignals(True)
        self.LEDspinBox.set_value(intensity)
        self.LEDspinBox.blockSignals(False)

    def getAFCOffset(self,evt):
        offset = self.dmi.get_AFC_setpoint()
        self.afcSetpointDoubleSpinBox.blockSignals(True)
        self.afcSetpointDoubleSpinBox.set_value(offset)
        self.afcSetpointDoubleSpinBox.blockSignals(False)

    def setAFCOffset(self,offset):
        self.dmi.set_AFC_setpoint(offset)

    def setAFCIntensity(self,intensity):
        self.dmi.set_AFC_intensity(intensity)

    def getAFCScore(self,evt):
        score = self.dmi.get_AFC_score()
        self.afcScoredoubleSpinBox.set_value(score)

    def snap(self,evt):
        print "not yet implemented"