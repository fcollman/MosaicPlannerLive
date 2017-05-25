from PyQt4 import QtCore, QtGui, uic
import os



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


class ChannelSettings():
    """simple struct for containing the parameters for the microscope"""
    def __init__(self,channels,exposure_times=dict([]),zoffsets=dict([]),
                 usechannels=dict([]),prot_names=dict([]),map_chan=None,
                 def_exposure=100,def_offset=0.0,):
        #def_exposure is default exposure time in msec


        self.channels= channels
        self.def_exposure=def_exposure
        self.def_offset=def_offset

        self.exposure_times=exposure_times
        self.zoffsets=zoffsets
        self.usechannels=usechannels
        self.prot_names=prot_names

        if map_chan is None:
            for ch in self.channels:
                if 'dapi' in ch.lower():
                    map_chan = ch
        if map_chan is None:
            map_chan = channels[0]

        self.map_chan = map_chan

    def save_settings(self,cfg):

        cfg['ChannelSettings']['map_chan']=self.map_chan
        for ch in self.channels:
            cfg['ChannelSettings']['Exposure_'+ch]=self.exposure_times[ch]
            cfg['ChannelSettings']['ZOffsets_'+ch]=self.zoffsets[ch]
            cfg['ChannelSettings']['UseChannel_'+ch]=self.usechannels[ch]
            cfg['ChannelSettings']['ProteinNames_'+ch]=self.prot_names[ch]
        cfg.write()

    def load_settings(self,cfg):
        for ch in self.channels:
            self.exposure_times[ch]=cfg['ChannelSettings'].get('Exposures_'+ch,self.def_exposure)
            self.zoffsets[ch]=cfg['ChannelSettings'].get('ZOffsets_'+ch,self.def_offset)
            self.usechannels[ch]=cfg['ChannelSettings'].get('UseChannel_'+ch,True)
            self.prot_names[ch]=cfg['ChannelSettings'].get('ProteinNames_'+ch,ch)

        self.map_chan=str(cfg['ChannelSettings']['map_chan'])


class ChangeChannelSettings(wx.Dialog):
    """simple dialog for changing the channel settings"""
    def __init__(self, parent, id, title, settings,style):
        wx.Dialog.__init__(self, parent, id, title,style=wx.DEFAULT_DIALOG_STYLE, size=(420, 600))

        self.settings=settings
        vbox = wx.BoxSizer(wx.VERTICAL)
        Nch=len(settings.channels)
        print Nch

        gridSizer=wx.FlexGridSizer(rows=Nch+3,cols=6,vgap=5,hgap=5)


        gridSizer.Add(wx.StaticText(self,id=wx.ID_ANY,label="chan"),border=5)
        gridSizer.Add(wx.StaticText(self,id=wx.ID_ANY,label="protein"),border=5)
        gridSizer.Add(wx.StaticText(self,id=wx.ID_ANY,label="use?"),border=5)
        gridSizer.Add(wx.StaticText(self,id=wx.ID_ANY,label="exposure"),border=5)
        gridSizer.Add(wx.StaticText(self,id=wx.ID_ANY,label="map?"),border=5)
        gridSizer.Add(wx.StaticText(self,id=wx.ID_ANY,label="zoffset     "),border=5)

        self.ProtNameCtrls=[]
        self.UseCtrls=[]
        self.ExposureCtrls=[]
        self.MapRadCtrls=[]
        self.ZOffCtrls=[]

        for ch in settings.channels:
            hbox =wx.BoxSizer(wx.HORIZONTAL)
            Txt=wx.StaticText(self,label=ch)
            ProtText=wx.TextCtrl(self,value=settings.prot_names[ch])
            ChBox = wx.CheckBox(self)
            ChBox.SetValue(settings.usechannels[ch])
            IntCtrl=wx.lib.intctrl.IntCtrl( self, value=settings.exposure_times[ch],size=(50,-1))
            FloatCtrl=wx.lib.agw.floatspin.FloatSpin(self,
                                       value=settings.zoffsets[ch],
                                       min_val=-3.0,
                                       max_val=3.0,
                                       increment=.1,
                                       digits=2,
                                       name='',
                                       size=(95,-1))

            if ch is settings.channels[0]:
                RadBut = wx.RadioButton(self,-1,'',style=wx.RB_GROUP)
            else:
                RadBut = wx.RadioButton(self,-1,'')
            if ch == settings.map_chan:
                RadBut.SetValue(True)

            gridSizer.Add(Txt,0,flag=wx.ALL|wx.EXPAND,border=5)
            gridSizer.Add(ProtText,1,flag=wx.ALL|wx.EXPAND,border=5)
            gridSizer.Add(ChBox,0,flag=wx.ALL|wx.EXPAND,border=5)
            gridSizer.Add(IntCtrl,0,border=5)
            gridSizer.Add(RadBut,0,flag=wx.ALL|wx.EXPAND,border=5)
            gridSizer.Add(FloatCtrl,0,flag=wx.ALL|wx.EXPAND,border=5)

            self.ProtNameCtrls.append(ProtText)
            self.UseCtrls.append(ChBox)
            self.ExposureCtrls.append(IntCtrl)
            self.MapRadCtrls.append(RadBut)
            self.ZOffCtrls.append(FloatCtrl)


        hbox = wx.BoxSizer(wx.HORIZONTAL)
        ok_button = wx.Button(self,wx.ID_OK,'OK')
        cancel_button = wx.Button(self,wx.ID_CANCEL,'Cancel')
        hbox.Add(ok_button)
        hbox.Add(cancel_button)

        vbox.Add(gridSizer)
        vbox.Add(hbox)

        self.SetSizer(vbox)


    def GetSettings(self):
        prot_names=dict([])
        usechannels=dict([])
        exposure_times=dict([])
        zoffsets=dict([])

        for i,ch in enumerate(self.settings.channels):
            prot_names[ch]=self.ProtNameCtrls[i].GetValue()
            usechannels[ch]=self.UseCtrls[i].GetValue()
            exposure_times[ch]=self.ExposureCtrls[i].GetValue()
            if self.MapRadCtrls[i].GetValue():
                map_chan=ch
            zoffsets[ch]=self.ZOffCtrls[i].GetValue()
        return ChannelSettings(self.settings.channels,exposure_times=exposure_times,zoffsets=zoffsets,usechannels=usechannels,prot_names=prot_names,map_chan=map_chan)

if __name__ == '__main__':
    import sys
    import MMCorePy
    app = QtGui.QApplication(sys.argv)

    print "loaded configuration file"
    #settings = StageResetSettings()
    #resetSettings=ChangeStageResetSettings(mmc,settings)
    #resetSettings.setModal(True)
    #resetSettings.show()
    exposure_times={'a':100,'b':100,'c':100,'d':100}
    zoffsets={'a':0,'b':0,'c':0,'d':0}
    usechannels={'a':True,'b':True,'c':True,'d':True}
    prot_names={'a':'prota','b':'protb','c':'propc','d':'protd'}
    map_chan='c'
    def_exposure=100
    def_offset=0.0

    settings = ChannelSettings(channels=['a','b','c','d'],)

    app.exec_()
    settings=resetSettings.getSettings()
    print(settings)

    sys.exit()