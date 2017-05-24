
# -*- coding: utf-8 -*-
# based on pyqtgraph\examples\ImageItem.py
from PyQt4 import QtCore, QtGui, uic
import os.path


class SetupAlertDialog(QtGui.QDialog):
    def __init__(self,settings):
        super(SetupAlertDialog,self).__init__()

        self.settings = settings
        self.initUI()

    def getSettings(self):
        mysettings = dict([])
        for key in self.settings.keys():
            mysettings[key]=self.settings[key]
        mysettings['username']=str(self.usernameField.text())
        mysettings['password']=str(self.passwordField.text())
        toText = str(self.toField.toPlainText())
        print(toText)
        tolist = toText.split('\n')
        tolist = [n for n in tolist if len(n)>0]
        print(tolist)
        mysettings['to']=tolist
        mysettings['session']=str(self.sessionField.text())
        return mysettings

    def initUI(self):

        currpath=os.path.split(os.path.realpath(__file__))[0]
        filename = os.path.join(currpath,'SetupAlertDialog.ui')
        uic.loadUi(filename,self)

        self.serverLabel.setText(settings['server'])
        self.portLabel.setText(str(settings['port']))


    def closeEvent(self,evt):

        return QtGui.QWidget.closeEvent(self,evt)


def launchDialog(settings):
    import sys

    dlg = SetupAlertDialog(settings)

    dlg.setWindowTitle('Setup Alerts')
    dlg.show()

    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
    thesettings = dlg.getSettings()
    print(thesettings)

    import smtplib
    from email.mime.text import MIMEText

    toaddr = "forrest.collman@gmail.com"
    smtpserver = smtplib.SMTP(thesettings['server'],thesettings['port'])
    smtpserver.ehlo()
    smtpserver.starttls()
    smtpserver.ehlo()
    smtpserver.login(thesettings['username'],thesettings['password'])

    msg = MIMEText('This is a test email')
    msg['Subject']=thesettings['session']
    msg['From']=thesettings['username']
    msg['To']=toaddr
    smtpserver.sendmail(thesettings['username'],toaddr,msg.as_string())
    smtpserver.close()

    return thesettings

if __name__ == '__main__':

    import sys
    import faulthandler
    from configobj import ConfigObj
    from MosaicPlanner import SETTINGS_FILE

    app = QtGui.QApplication(sys.argv)
    faulthandler.enable()
    cfg = ConfigObj(SETTINGS_FILE,unrepr=True)

    #defaultMMpath = "C:\Program Files\Micro-Manager-1.4"
    #configFile = QtGui.QFileDialog.getOpenFileName(
    #    None, "pick a uManager cfg file", defaultMMpath, "*.cfg")
    #configFile = str(configFile.replace("/", "\\"))
    settings = cfg['smtp']
    print settings

    launchDialog(settings)

    sys.exit()
