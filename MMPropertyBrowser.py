
from pyqtgraph.Qt import QtCore, QtGui
import MMCorePy
import functools

UnknownType = 0
AnyType = 1
CameraDevice = 2
ShutterDevice = 3
StateDevice = 4
StageDevice = 5
XYStageDevice = 6
SerialDevice = 7
GenericDevice = 8
AutoFocusDevice = 9
CoreDevice = 10
ImageProcessorDevice = 11
SignalIODevice = 12
MagnifierDevice = 13
SLMDevice = 14
HubDevice = 15
GalvoDevice = 16

DeviceDict = {0:'UnknownType',
                1: 'AnyType',
                2: 'CameraType',
                3: 'ShutterDevice',
                4: 'StateDevice',
                5: 'StageDevice',
                6: 'XYStageDevice',
                7: 'SerialDevice',
                8: 'GenericDevice',
                9: 'AutoFocusDevice',
                10: 'CoreDevice',
                11: 'ImageProcessorDevice',
                12: 'SignalIODevice',
                13: 'MagnifierDevice',
                14: 'SLMDevice',
                15: 'HubDevice',
                16: 'GalvoDevice'
}
StringProperty = 1
FloatProperty = 2
IntProperty = 3

class MMPropertyBrowser(QtGui.QWidget):

    def __init__(self, mmc,debug=True):
        r"""MMPropertyBrowser(mmc)
        mmc is a micromanager core object"""

        QtGui.QWidget.__init__(self)
        self.layout = QtGui.QVBoxLayout()
        self.mmc = mmc
        if debug:
            self.mmc.enableStderrLog(debug)
            self.mmc.enableDebugLog(debug)
        self.devices = self.mmc.getLoadedDevices()
        self.devicepulldown = QtGui.QComboBox(self)
        self.devicepulldown.addItems(self.devices)
        self.devicepulldown.currentIndexChanged.connect(self.deviceChanged)

        self.propTable = QtGui.QTableWidget(self)
        device0 = self.devices[0]
        self.fillPropTable(device0)

        self.layout.addWidget(self.devicepulldown)
        self.layout.addWidget(self.propTable)

        self.setLayout(self.layout)
        self.resize(300, 500)
        self._dialog = None

    def addNameItem(self,text,i,isReadOnly=True,col=0,greyBack = False):
        NameItem = QtGui.QTableWidgetItem(text)
        if isReadOnly:
            NameItem.setFlags(QtCore.Qt.ItemIsEnabled)
        if greyBack:
            NameItem.setBackground(QtCore.Qt.lightGray)
        self.propTable.setItem(i, col, NameItem) 
        return NameItem

    def getPropertyBounds(self,device,prop):
        propType = self.mmc.getPropertyType(device, prop)
        deviceType = self.mmc.getDeviceType(device)
        if self.mmc.hasPropertyLimits(device, prop):
            maxval = self.mmc.getPropertyUpperLimit(device, prop)
            minval = self.mmc.getPropertyLowerLimit(device, prop)
        elif (deviceType == StateDevice) & (prop == 'State'):
            # if it's a state device, then the state property
            # needs to have its max/min values set from label
            minval = 0
            numLabels = len(
                self.mmc.getAllowedPropertyValues(device, "Label"))
            maxval = numLabels - 1
        else:
            if propType == StringProperty:
                 maxval = None
                 minval = None
            elif propType == FloatProperty:
                 maxval = 9999999.99
                 minval = -9999999.99
            elif propType == IntProperty:
                 minval = -9999999
                 maxval = 9999999   
        return (minval,maxval)

    def addSpinBox(self,type,minval,maxval,i,j,defValue = 0):
        if type == FloatProperty:
            SpinBox = QtGui.QDoubleSpinBox(self)
            defValue = float(defValue)
            SpinBox.setDecimals(8)
        elif type == IntProperty:
            defValue = int(defValue)
            SpinBox = QtGui.QSpinBox(self)
            

        SpinBox.setMaximum(maxval)
        SpinBox.setMinimum(minval)
        SpinBox.setValue(defValue)

        self.propTable.setCellWidget(i, j, SpinBox)
        # make it only fire a valuechanged when done inputing
        SpinBox.setKeyboardTracking(False)

        return SpinBox

    def fillPropTable(self, device):

        # clear the previous table
        self.propTable.clear()
        # get the property names for this device
        props = self.mmc.getDevicePropertyNames(device)

        # setup the table according to the size
        self.propTable.setRowCount(len(props) + 1)
        self.propTable.setColumnCount(2)
        self.propTable.setHorizontalHeaderLabels(["property", "value"])
        device_type = self.mmc.getDeviceType(device)
        # loop over the properties for this device, filling in the table
        for i, prop in enumerate(props):
            # fill in name in the first column with a Qtablewidgetitem
            propNameItem=self.addNameItem(prop,i,True)

            # read in the properties current value from mmc
            value = self.mmc.getProperty(device, prop)
            # find out if its read only, and its allowed values
            readOnly = self.mmc.isPropertyReadOnly(device, prop)
            allowedValues = self.mmc.getAllowedPropertyValues(device, prop)

            # if it has allowed values, use a QComboBox
            if len(allowedValues) > 0 and not readOnly:
                propValueItem = QtGui.QComboBox(self)
                propValueItem.addItems(allowedValues)
                if value in allowedValues:
                    propValueItem.setCurrentIndex(allowedValues.index(value))
                else:
                    self.setProperty(device,prop,propValueItem.currentText())

                temp_func = functools.partial(self.setProperty, device, prop)
                propValueItem.currentIndexChanged[str].connect(temp_func)
                self.propTable.setCellWidget(i, 1, propValueItem)
            # if it is not a read only property
            elif not readOnly:
                # then we need to know what kind it is
                propType = self.mmc.getPropertyType(device, prop)
                minval, maxval = self.getPropertyBounds(device,prop)

                if propType == 1:
                    # then this is a string
                    print "need to fix"
                elif propType == 2:
                    # then this is a float
                    # and we will use a QDoubleSpinBox
                    propFloatSpin = self.addSpinBox(propType,minval,maxval,i,1,defValue = float(value))
                    propFloatSpin.valueChanged[float].connect(
                        functools.partial(
                            self.setProperty, device, prop))
                elif propType == 3:
                    # then this is an integer
                    propIntSpin = self.addSpinBox(propType,minval,maxval,i,1,defValue =int(value))
                    propIntSpin.valueChanged[int].connect(
                        functools.partial(
                            self.setProperty, device, prop))
            else:
                # then it must have been a readonly item and we will display
                # it's value as a grey backgrounded string
                propValueItem = self.addNameItem(value,i,True,1,greyBack = True)
                
                # go get the name item, and change its background too
                nameItem = self.propTable.item(i, 0)
                nameItem.setBackground(QtCore.Qt.lightGray)

        # tack on one more fake property which shows the device type
        # in the final row.
        i = len(props)
        propNameItem = self.addNameItem("Device Type",i,True,0,greyBack = True)
        
        device_type = self.mmc.getDeviceType(device)
        propValueText = self.addNameItem(DeviceDict[device_type],i,True,1,greyBack = True)

        if device_type == XYStageDevice:
            self.propTable.setRowCount(len(props) + 3)

            i = len(props)+1
            propNameItem = self.addNameItem("X Position",i,True,0)
            propNameItem = self.addNameItem("Y Position",i+1,True,0)
            xpos = self.mmc.getXPosition(device)
            ypos = self.mmc.getYPosition(device)
            self.XPosSpinBox = self.addSpinBox(FloatProperty,-999999.99,999999.99,i,1,defValue = xpos)
            self.YPosSpinBox = self.addSpinBox(FloatProperty,-999999.99,999999.99,i+1,1,defValue = ypos)

            self.XPosSpinBox.valueChanged[float].connect(
                        functools.partial(
                            self.setPosition, device,self.XPosSpinBox,self.YPosSpinBox))
            self.YPosSpinBox.valueChanged[float].connect(
                        functools.partial(
                            self.setPosition, device,self.XPosSpinBox,self.YPosSpinBox))


    def setPosition(self, device,XPosSpinBox,YPosSpinBox,value):
        xpos = XPosSpinBox.value()
        ypos = YPosSpinBox.value()
        self.mmc.setXYPosition(device,xpos,ypos)
        self.mmc.waitForDevice(device)
        self.fillPropTable(device)

    def setProperty(self, device, prop, value):
        r'''setProperty(device, prop, value)
        meant for use as a callback function
        device = string for the micromanager device
        prop = string denoting the micromanager propery name
        value = Qstring or string indicating the value,
        must be convertable to a string with str() cast'''
        print device, prop, value
        self.mmc.setProperty(device, prop, str(value))
        self.mmc.waitForDevice(device)
        self.fillPropTable(device)

    #def handleOpenDialog(self):
    #    if self._dialog is None:
    #        self._dialog = QtGui.QDialog(self)
    #        self._dialog.resize(200, 100)
    #    self._dialog.show()

    def deviceChanged(self, index):
        device = self.devices[index]
        self.fillPropTable(device)

if __name__ == '__main__':

    import sys
    app = QtGui.QApplication(sys.argv)

    mmc = MMCorePy.CMMCore()
    defaultMMpath = "C:\Program Files\Micro-Manager-1.4"
    configFile = QtGui.QFileDialog.getOpenFileName(
        None, "pick a uManager cfg file", defaultMMpath, "*.cfg")
    configFile = str(configFile.replace("/", "\\"))
    print configFile

    mmc.loadSystemConfiguration(configFile)
    print "loaded configuration file"
    win = MMPropertyBrowser(mmc)
    win.show()
    app.exec_()
    mmc.reset()
    sys.exit()
