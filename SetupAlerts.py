
# -*- coding: utf-8 -*-
# based on pyqtgraph\examples\ImageItem.py
from PyQt4 import QtCore, QtGui, uic
import numpy as np

class SetupAlertDialog(QtGui.QWidget):
    def __init__(self,settings):
        super(SetupAlertDialog,self).__init__()

        self.settings = settings
        self.initUI()


    def initUI(self):

        currpath=os.path.split(os.path.realpath(__file__))[0]
        filename = os.path.join(currpath,'SetupAlertDialog.ui')
        uic.loadUi(filename,self)

    def closeEvent(self,evt):
        self.mmc.stopSequenceAcquisition()
        print "stopped acquisition"
        #if self.timer is not None:
        #    print "cancelling timer if it exists"
        #    self.timer.cancel()
        self.ended = True
        #self.destroy()
        return QtGui.QWidget.closeEvent(self,evt)
        #evt.accept()

def launchDialog(settings):
    import sys
    imgSrc.set_binning(1)
    dlg = SetupAlertDialog(settings)
    #vidview.setGeometry(250,50,1100,1000)
    dlg.show()

    dlg.setWindowTitle('Setup Alerts')

    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()

    return dlg.getSettings()

if __name__ == '__main__':

    import sys
    import faulthandler
    from configobj import ConfigObj
    from MosaicPlanner import SETTINGS_FILE

    app = QtGui.QApplication(sys.argv)
    faulthandler.enable()
    cfg = ConfigObj(SETTINGS_FILE,unrepr=True)

    #mmc = MMCorePy.CMMCore()
    #defaultMMpath = "C:\Program Files\Micro-Manager-1.4"
    #configFile = QtGui.QFileDialog.getOpenFileName(
    #    None, "pick a uManager cfg file", defaultMMpath, "*.cfg")
    #configFile = str(configFile.replace("/", "\\"))
    settings = cfg['smtp']
    print settings

    launchSnap(imgSrc,dict([]))
    #app.exec_()
    print "got out of the event loop"
    imgSrc.mmc.reset()
    print "reset micromanager core"
    sys.exit()
