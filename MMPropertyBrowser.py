
# -*- coding: utf-8 -*-
# based on pyqtgraph\examples\ImageItem.py
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np
import pyqtgraph as pg
import pyqtgraph.ptime as ptime
import time

import MMCorePy

import functools

UnknownType=0
AnyType=1
CameraDevice=2
ShutterDevice=3
StateDevice=4
StageDevice=5
XYStageDevice=6
SerialDevice=7
GenericDevice=8
AutoFocusDevice=9
CoreDevice=10
ImageProcessorDevice=11
SignalIODevice=12
MagnifierDevice=13
SLMDevice=14
HubDevice=15
GalvoDevice=16

class MMPropertyBrowser(QtGui.QWidget):
    def __init__(self,mmc):
        QtGui.QWidget.__init__(self)
        self.layout = QtGui.QVBoxLayout() 
        self.mmc = mmc
        self.devices=self.mmc.getLoadedDevices() 
        self.devicepulldown = QtGui.QComboBox(self)
        self.devicepulldown.addItems(self.devices)
        self.devicepulldown.currentIndexChanged.connect(self.deviceChanged)

        self.propTable = QtGui.QTableWidget(self)
        device0 = self.devices[0]
        self.fillPropTable(device0)
        #button = QtGui.QPushButton('Open Dialog', self)

        #button.clicked.connect(self.handleOpenDialog)
        self.layout.addWidget(self.devicepulldown)
        self.layout.addWidget(self.propTable)

        self.setLayout(self.layout)
        self.resize(300, 500)
        self._dialog = None

    def fillPropTable(self,device):
        self.propTable.clear()
        props=self.mmc.getDevicePropertyNames(device)
        self.propTable.setRowCount(len(props)+1)
        self.propTable.setColumnCount(2)
        self.propTable.setHorizontalHeaderLabels(["property","value"])
        for i,prop in enumerate(props):
            propNameItem = QtGui.QTableWidgetItem(prop)
            propNameItem.setFlags(QtCore.Qt.ItemIsEnabled)
            self.propTable.setItem(i,0,propNameItem)                      
            value = self.mmc.getProperty(device,prop)
            readOnly = self.mmc.isPropertyReadOnly(device,prop)
            allowedValues = self.mmc.getAllowedPropertyValues(device,prop)
            if len(allowedValues)>0  and not readOnly:
                propValueItem = QtGui.QComboBox(self)
                propValueItem.addItems(allowedValues)
                #self.connect(propValueItem, QtCore.SIGNAL('currentIndexChanged(QString)'), self.setProperty,device)
                propValueItem.currentIndexChanged[str].connect(functools.partial (self.setProperty,device,prop))
                self.propTable.setCellWidget(i,1,propValueItem)
            elif not readOnly:  
                propType=self.mmc.getPropertyType(device,prop)
                if propType == 1:
                    #then this is a string
                    print "need to fix"
                elif propType == 2:
                    #then this is a float
                    propFloatSpin = QtGui.QDoubleSpinBox(self)
                    propFloatSpin.setDecimals(3)
                    if self.mmc.hasPropertyLimits(device,prop):
                        maxval=self.mmc.getPropertyUpperLimit(device,prop)
                        minval=self.mmc.getPropertyLowerLimit(device,prop)
                        
                    else:
                        maxval=9999999.99
                        minval=-9999999.99

                    propFloatSpin.setMaximum(maxval)
                    propFloatSpin.setMinimum(minval)
                    print (device,prop,"min-max",minval,maxval)    

                    self.propTable.setCellWidget(i,1,propFloatSpin)
                    propFloatSpin.setKeyboardTracking(False)
                    propFloatSpin.valueChanged[str].connect(functools.partial(self.setProperty,device,prop))
                elif propType == 3:
                    #then this is an integer
                    propIntSpin = QtGui.QSpinBox(self)
                    if self.mmc.hasPropertyLimits(device,prop):
                        maxval=self.mmc.getPropertyUpperLimit(device,prop)
                        minval=self.mmc.getPropertyLowerLimit(device,prop)
                    else:
                        minval=-9999999
                        maxval=9999999

                    propIntSpin.setMaximum(int(maxval))
                    propIntSpin.setMinimum(int(minval))
                    print (device,prop,"min-max",int(minval),int(maxval))
                    self.propTable.setCellWidget(i,1,propIntSpin)
                    propIntSpin.setKeyboardTracking(False)
                    propIntSpin.valueChanged[str].connect(functools.partial(self.setProperty,device,prop))

                
            else:
           


                propValueItem = QtGui.QTableWidgetItem(value)
                self.propTable.setItem(i,1,propValueItem)
                propValueItem.setBackground(QtCore.Qt.lightGray)
                propValueItem.setFlags(QtCore.Qt.ItemIsEnabled)
                nameItem = self.propTable.item(i,0)
                nameItem.setBackground(QtCore.Qt.lightGray)
                
        i=len(props)
        propNameItem = QtGui.QTableWidgetItem("Device Type")
        propNameItem.setFlags(QtCore.Qt.ItemIsEnabled)
        propNameItem.setBackground(QtCore.Qt.lightGray)
        self.propTable.setItem(i,0,propNameItem)   

        device_type = self.mmc.getDeviceType(device)
        propValueText = QtGui.QTableWidgetItem(self.mmc.getDeviceName(device))
        propValueText.setFlags(QtCore.Qt.ItemIsEnabled)
        propValueText.setBackground(QtCore.Qt.lightGray)
        self.propTable.setItem(i,1,propValueText)

        #self.propTable.itemChanged.connect(self.cellChanged)
    


    def setProperty(self,device,prop,value):  
        print device,prop,value 
        self.mmc.setProperty(device,prop,str(value))
        
    def handleOpenDialog(self):
        if self._dialog is None:
            self._dialog = QtGui.QDialog(self)
            self._dialog.resize(200, 100)
        self._dialog.show()

    def deviceChanged(self,index):
        device = self.devices[index]
        self.fillPropTable(device)

   
if __name__ == '__main__':

    import sys
    app = QtGui.QApplication(sys.argv)
    
    mmc = MMCorePy.CMMCore() 
    configFile = QtGui.QFileDialog.getOpenFileName(None,"pick a uManager cfg file","C:\Program Files\Micro-Manager-1.4","*.cfg")
    configFile= str(configFile.replace("/","\\"))
    print configFile

    #configFile='C:\Program Files\Micro-Manager-1.4\MMZyla.cfg'
    mmc.loadSystemConfiguration(configFile)
    print "loaded configuration file"
    win = MMPropertyBrowser(mmc)
    win.show()
    app.exec_()
    mmc.reset()
    sys.exit()