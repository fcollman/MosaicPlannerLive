from PyQt4 import QtCore, QtGui, uic
import os

class StageResetSettings():
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


class ChangeStageResetSettings(QtGui.QWidget):
    def __init__(self,mmc,settings=StageResetSettings()):

        #QtGui.QWidget.__init__(self)
        super(ChangeStageResetSettings,self).__init__()
        currpath=os.path.split(os.path.realpath(__file__))[0]
        filename = os.path.join(currpath,'StageReset.ui')
        uic.loadUi(filename,self)
        self.show()

    def getSettings(self):


        """extracts the Camera Settings from the controls"""
        return SmartSEMSettings(mag=self.magCtrl.GetValue(),
                                     tilt=self.tiltCtrl.GetValue(),
                                     rot=self.rotCtrl.GetValue(),
                                     Z=self.ZCtrl.GetValue(),
                                     WD=self.WDCtrl)

