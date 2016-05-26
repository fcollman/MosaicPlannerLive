from PyQt4 import QtCore, QtGui, uic
import os
import MMCorePy


class StageResetSettings:

    def __init__(self,enableStageReset=False,focusStage=None,resetStage=None,compensationStage=None,minThreshold=-60,
                 maxThreshold=60,resetPosition=0,invertCompensation=False):
        self.enableStageReset=enableStageReset
        self.focusStage=focusStage
        self.resetStage=resetStage
        self.compensationStage=compensationStage
        self.minThreshold=minThreshold
        self.maxThreshold=maxThreshold
        self.resetPosition=resetPosition
        self.invertCompensation=invertCompensation

    def __str__(self):
        total_string = "enableStageReset:"+str(self.enableStageReset) +" \n"
        total_string += "focusStage: " + self.focusStage + "\n"
        total_string += "resetStage: " + self.resetStage + "\n"
        total_string += "compensationStage: " + self.compensationStage + "\n"
        total_string += "minThreshold: " + str(self.minThreshold) + "\n"
        total_string += "maxThreshold: " + str(self.maxThreshold) + "\n"
        total_string += "resetPosition: " + str(self.resetPosition) + "\n"
        total_string += "invertCompensation: " + str(self.invertCompensation) + "\n"
        return total_string

    def savesettings(self,cfg):
        cfg.WriteBool('enableStageReset',self.enableStageReset)
        cfg.Write('focusStage',self.focusStage)
        cfg.Write('resetStage',self.resetStage)
        cfg.Write('compensationStage',self.compensationStage)
        cfg.WriteFloat('minThreshold',self.minThreshold)
        cfg.WriteFloat('maxThreshold',self.maxThreshold)
        cfg.WriteFloat('resetPosition',self.resetPosition)
        cfg.WriteBool('invertCompensation',self.invertCompensation)

    def loadsettings(self,cfg):
        self.enableStageReset=cfg.ReadBool('enableStageReset',False)
        self.focusStage=cfg.Read('focusStage',None)
        self.resetStage=cfg.Read('resetStage',None)
        self.compensationStage=cfg.Read('compensationStage',None)
        self.minThreshold=cfg.ReadFloat('minThreshold',-60.0)
        self.maxThreshold=cfg.ReadFloat('maxThreshold',60.0)
        self.resetPosition=cfg.ReadFloat('resetPosition',0.0)
        self.invertCompensation=cfg.ReadBool('invertCompensation',False)


class ChangeStageResetSettings(QtGui.QDialog):
    def __init__(self, mmc, input_settings=StageResetSettings()):

        #QtGui.QWidget.__init__(self)
        super(ChangeStageResetSettings,self).__init__()
        currpath=os.path.split(os.path.realpath(__file__))[0]
        filename = os.path.join(currpath,'StageReset.ui')
        self.input_settings = input_settings
        uic.loadUi(filename,self)

        stages = mmc.getLoadedDevicesOfType(MMCorePy.StageDevice)
        #load up the focusStage_combobox
        self.enableReset_checkBox.setCheckState(input_settings.enableStageReset)

        self.focusStage_comboBox.addItems(stages)
        self.resetStage_comboBox.addItems(stages)
        self.compensationStage_comboBox.addItems(stages)

        def setComboByText(combobox,text):
            index = combobox.findText(text, flags=QtCore.Qt.MatchExactly)
            if(index>-1):
                combobox.setCurrentIndex(index)

        if settings.focusStage is not None:
            setComboByText(self.focusStage_comboBox,settings.focusStage)

        if settings.resetStage is not None:
            setComboByText(self.resetStage_comboxBox,settings.resetStage)

        if settings.compensationStage is not None:
            setComboByText(self.compensationStage_comboBox,settings.compensationStage)


        #self.show()

    def getSettings(self):


        """extracts the Camera Settings from the controls"""
        return StageResetSettings(enableStageReset=self.enableReset_checkBox.isChecked(),
                                  focusStage=str(self.focusStage_comboBox.currentText()),
                                  resetStage=str(self.resetStage_comboBox.currentText()),
                                  compensationStage=str(self.compensationStage_comboBox.currentText()),
                                  minThreshold=self.minThreshold_SpinBox.value(),
                                  maxThreshold=self.maxThreshold_SpinBox.value(),
                                  resetPosition=self.resetPosition_SpinBox.value(),
                                  invertCompensation=self.invertCompensation_checkBox.isChecked())

if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    defaultMMpath = "C:\Users\Administrator\Documents"
    configFile = QtGui.QFileDialog.getOpenFileName(
        None, "pick a uManager cfg file", defaultMMpath, "*.cfg")
    configFile = str(configFile.replace("/", "\\"))

    mmc = MMCorePy.CMMCore()
    mmc.loadSystemConfiguration(configFile)
    print "loaded configuration file"
    settings = StageResetSettings()
    resetSettings=ChangeStageResetSettings(mmc,settings)
    #resetSettings.setModal(True)
    resetSettings.show()
    app.exec_()
    settings=resetSettings.getSettings()
    print(settings)
    mmc.reset()
    print "reset micromanager core"
    sys.exit()