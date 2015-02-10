
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


class MMPropertyBrowser(QtGui.QWidget):

    def __init__(self, mmc):
        r"""MMPropertyBrowser(mmc)
        mmc is a micromanager core object"""

        QtGui.QWidget.__init__(self)
        self.layout = QtGui.QVBoxLayout()
        self.mmc = mmc
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
            propNameItem = QtGui.QTableWidgetItem(prop)
            # make it read only
            propNameItem.setFlags(QtCore.Qt.ItemIsEnabled)
            self.propTable.setItem(i, 0, propNameItem)

            # read in the properties current value from mmc
            value = self.mmc.getProperty(device, prop)
            # find out if its read only, and its allowed values
            readOnly = self.mmc.isPropertyReadOnly(device, prop)
            allowedValues = self.mmc.getAllowedPropertyValues(device, prop)

            # if it has allowed values, use a QComboBox
            if len(allowedValues) > 0 and not readOnly:
                propValueItem = QtGui.QComboBox(self)
                propValueItem.addItems(allowedValues)
                temp_func = functools.partial(self.setProperty, device, prop)
                propValueItem.currentIndexChanged[str].connect(temp_func)
                self.propTable.setCellWidget(i, 1, propValueItem)
            # if it is not a read only property
            elif not readOnly:
                # then we need to know what kind it is
                propType = self.mmc.getPropertyType(device, prop)
                if propType == 1:
                    # then this is a string
                    print "need to fix"
                elif propType == 2:
                    # then this is a float
                    # and we will use a QDoubleSpinBox
                    propFloatSpin = QtGui.QDoubleSpinBox(self)
                    propFloatSpin.setDecimals(3)
                    if self.mmc.hasPropertyLimits(device, prop):
                        maxval = self.mmc.getPropertyUpperLimit(device, prop)
                        minval = self.mmc.getPropertyLowerLimit(device, prop)
                    else:
                        # default max/min values for floats/doubles
                        maxval = 9999999.99
                        minval = -9999999.99

                    propFloatSpin.setMaximum(maxval)
                    propFloatSpin.setMinimum(minval)
                    print (device, prop, "min-max", minval, maxval)

                    self.propTable.setCellWidget(i, 1, propFloatSpin)
                    # make it only fire a valuechanged when done inputing
                    propFloatSpin.setKeyboardTracking(False)
                    # set call back to set property on value changing
                    propFloatSpin.valueChanged[str].connect(
                        functools.partial(
                            self.setProperty, device, prop))

                elif propType == 3:
                    # then this is an integer
                    propIntSpin = QtGui.QSpinBox(self)
                    if self.mmc.hasPropertyLimits(device, prop):
                        maxval = self.mmc.getPropertyUpperLimit(device, prop)
                        minval = self.mmc.getPropertyLowerLimit(device, prop)
                    elif (device_type == StateDevice) & (prop == 'State'):
                        # if it's a state device, then the state property
                        # needs to have its max/min values set from label
                        minval = 0
                        numLabels = len(
                            self.mmc.getAllowedPropertyValues(device, "Label"))
                        maxval = numLabels - 1
                    else:
                        minval = -9999999
                        maxval = 9999999

                    propIntSpin.setMaximum(int(maxval))
                    propIntSpin.setMinimum(int(minval))
                    print (device, prop, "min-max", int(minval), int(maxval))
                    self.propTable.setCellWidget(i, 1, propIntSpin)
                    propIntSpin.setKeyboardTracking(False)
                    propIntSpin.valueChanged[str].connect(
                        functools.partial(self.setProperty, device, prop))
            else:
                # then it must have been a readonly item and we will display
                # it's value as a grey backgrounded string
                propValueItem = QtGui.QTableWidgetItem(value)
                self.propTable.setItem(i, 1, propValueItem)
                propValueItem.setBackground(QtCore.Qt.lightGray)
                propValueItem.setFlags(QtCore.Qt.ItemIsEnabled)
                # go get the name item, and change its background too
                nameItem = self.propTable.item(i, 0)
                nameItem.setBackground(QtCore.Qt.lightGray)

        # tack on one more fake property which shows the device type
        # in the final row.
        i = len(props)
        propNameItem = QtGui.QTableWidgetItem("Device Type")
        propNameItem.setFlags(QtCore.Qt.ItemIsEnabled)
        propNameItem.setBackground(QtCore.Qt.lightGray)
        self.propTable.setItem(i, 0, propNameItem)

        device_type = self.mmc.getDeviceType(device)
        propValueText = QtGui.QTableWidgetItem(str(device_type))
        propValueText.setFlags(QtCore.Qt.ItemIsEnabled)
        propValueText.setBackground(QtCore.Qt.lightGray)
        self.propTable.setItem(i, 1, propValueText)

    def setProperty(self, device, prop, value):
        r'''setProperty(device, prop, value)
        meant for use as a callback function
        device = string for the micromanager device
        prop = string denoting the micromanager propery name
        value = Qstring or string indicating the value,
        must be convertable to a string with str() cast'''
        print device, prop, value
        self.mmc.setProperty(device, prop, str(value))

    def handleOpenDialog(self):
        if self._dialog is None:
            self._dialog = QtGui.QDialog(self)
            self._dialog.resize(200, 100)
        self._dialog.show()

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
