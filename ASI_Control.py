#Rob Serafin
#August 6th 2015
#Current Status: Program displays window design from QT designer. Program Capabilities include: live feed, single image display, live stage position updates, adjustable exposure settings, and 4 laser illuminations 
import sys
import MMCorePy
import matplotlib as mpl
import numpy as np
import matplotlib.pyplot as plt
from PyQt4 import QtCore, QtGui, uic
from pyqtgraph.Qt import QtCore, QtGui #newly added check for bugs
import functools #newly added check for bugs
from MMPropertyBrowser import MMPropertyBrowser
import time 
import csv
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages
import tifffile as tif
import os
# from PySide import QtUiTools


class Freakout(Exception): pass

# qtCreatorFile = "Scope_Interface4_0.ui" #current file from qt design

# mmc = MMCorePy.CMMCore() #sets mmc as shortcut to micro core
# configFile = 'C:\Users\Administrator\Documents\ASI_Zyla_Laser.cfg'
# mmc.loadSystemConfiguration(configFile)
# mmc.enableDebugLog(True)
# mmc.setPrimaryLogFile('C:\Users\Administrator\Documents\ScopeInterfaceCoreLog.txt')
# Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


class ASI_AutoFocus(QtGui.QMainWindow):

    def __init__(self,mmc):
        #QtGui.QWidget.__init__(self)
        super(ASI_AutoFocus,self).__init__()
        currpath=os.path.split(os.path.realpath(__file__))[0]
        filename = os.path.join(currpath,'ASI_Interface.ui')
        uic.loadUi(filename,self)
        self.show()
        # loader = QtUiTools.QUiLoader()
        #file = QtCore.QFile(filename)
        #file.open(QtCore.QFile.ReadOnly)
        # self.Alfred = loader.load(file,self)
        #file.close()

        #QtGui.QWidget.__init__(self)
        # Ui_MainWindow.__init__(self)
        self.mmc= mmc


        self.XY_label = 'XYStage:XY:31'
        self.Z_label = 'ZStage:Z:32'
        self.PIEZO_label = 'PiezoStage:P:34'
        self.CRISP_label = 'CRISPAFocus:P:34'
        self.TIGER_label = 'TigerCommHub'
        self.TIGER_port =self.mmc.getProperty(self.TIGER_label,'SerialComPort')

        # self.setupUi(self)
        self.cam = self.mmc.getCameraDevice()
        #self.get_position.clicked.connect(self.UpdatePos) #connects to the position button named GetPos
        self.take_picture.clicked.connect(self.TakePic) #connects to the camera button
        self.start_vid.clicked.connect(self.StartVideo)
        self.stop_vid.clicked.connect(self.StopVideo)
        self.get_focus.clicked.connect(self.GetFocus)
        self.get_exposure.clicked.connect(self.GetExposure)
        self.inc_exposure.clicked.connect(self.IncExposure)
        self.dec_exposure.clicked.connect(self.DecExposure)
        self.prop_browser.clicked.connect(self.GetProperties)
        self.idle_button.clicked.connect(self.Idle)
        self.dither_button.clicked.connect(self.Dither)
        self.lock_button.clicked.connect(self.Lock)
        self.unlock_button.clicked.connect(self.Unlock)
        self.reset_offset_button.clicked.connect(self.ResetOffset)
        self.log_cal_button.clicked.connect(self.LogCal)
        self.obj_NA.returnPressed.connect(self.GetObjNA)
        self.LED_spinbox.editingFinished.connect(self.SetLEDIntensity)
        self.set_gain_button.clicked.connect(self.SetGain)
        self.home_button.clicked.connect(self.GoHome)
        self.map_surface_button.clicked.connect(self.MapSurface2_0)
        self.reset_piezo.clicked.connect(self.ResetPiezo)
        self.center_xy.clicked.connect(self.CenterXY)
        self.define_home.clicked.connect(self.DefineHome)
        self.Z_stack.clicked.connect(self.TakeZstack)
        self.z_map.clicked.connect(self.ZMap)
        self.start_pos_timer.clicked.connect(self.startPosTimer)
        self.hw_center_x.clicked.connect(self.CenterX)
        self.hw_center_y.clicked.connect(self.CenterY)
        self.array_map.clicked.connect(self.ArrayMap)

        self.get_xy_speed.clicked.connect(self.GetXYSpeed)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.PosTimer = QtCore.QTimer(self)
        self.connect(self.PosTimer, QtCore.SIGNAL("timeout()"), self.UpdatePos)
        self.PosTimer.start(200)

        self.VideoTimer = QtCore.QTimer(self)
        self.connect(self.VideoTimer, QtCore.SIGNAL("timeout()"), self.UpdateVideo)
        self.ChannelsComboBox.addItems(self.mmc.getAvailableConfigs('Channels'))
        self.ChannelsComboBox.currentIndexChanged[str].connect(self.changeChannel)



        self.ended = False
    def closeEvent(self, event):
        print "Goodbye Master Wayne"
        self.StopVideo()

    def changeChannel(self,chan):
        print 'channel is', chan
        self.mmc.setConfig('Channels',str(chan))

    def startPosTimer(self,evt):
        self.PosTimer.start(200)

    def UpdatePos(self):
        #remcount = self.mmc.getRemainingImageCount()
        # time.sleep(.1)
        X_Pos = self.mmc.getXPosition(self.XY_label) #sets variable X_pos as the result of mmc getXPosition 
        Y_Pos = self.mmc.getYPosition(self.XY_label) 
        PIEZO = self.mmc.getPosition(self.PIEZO_label)
        Z_Pos = self.mmc.getPosition(self.Z_label)
        self.current_Xpos.setText(str(X_Pos))
        self.current_Ypos.setText(str(Y_Pos))
        self.current_Zpos.setText(str(Z_Pos))
        self.current_Piezo.setText(str(PIEZO))
        self.lock_status.setText(self.mmc.getProperty(self.CRISP_label,'CRISP State'))

  
    def TakePic(self):

        for attempt in range(5):
            try:
                # do thing
                self.mmc.snapImage()
            except:
                # perhaps reconnect, etc.
                print "snap failed.. cleaning up buffer"
                data=self.mmc.getImage()
            else:
              break
        else:
            # we failed all the attempts - deal with the consequences.
            print "we failed on 5 attempts to snap properly... freakout!"
            return None

        pic = self.mmc.getImage()
        self.Current_Image.setImage(pic) #sets graphics display widget to the current image
        return pic
    def GetFocus(self):
       # self.ended = False
       # if 1 > 0:
        Focus = str(self.mmc.getCurrentFocusScore()) #gets focus value from camera, converts to string
        self.current_focus.setText(Focus) #imputs string into text box adjacent to focus label
       # if not self.ended:
            #self.timer = QtCore.QTimer.singleShot(self.mmc.getExposure(), self.GetFocus)
    def GetExposure(self):
        Expo = str(self.mmc.getExposure()) #displays current exposure in milliseconds in adjacent text box
        self.current_exposure.setText(Expo)
    def IncExposure(self):
        current = self.mmc.getExposure() #increases exposure time by 1 millisecond
        new = current + 10 
        self.mmc.setExposure(new)
        self.current_exposure.setText(str(new))
    def DecExposure(self):
        current = self.mmc.getExposure()  #decreases exposure time by 1 millisecond
        if current >= 11:
            new = current - 10
        else:
            new = current    
        self.mmc.setExposure(new)
        self.current_exposure.setText(str(new))
    def StartVideo(self):
        if not self.mmc.isSequenceRunning():
            self.mmc.startContinuousSequenceAcquisition(1)
            self.VideoTimer.start(self.mmc.getExposure())

    def StopVideo(self):
        if self.mmc.isSequenceRunning():
            self.mmc.stopSequenceAcquisition()
            self.VideoTimer.stop()

    def UpdateVideo(self):
        remcount = self.mmc.getRemainingImageCount()
         #print 'remcount',remcount
        if remcount > 0:
            data =  self.mmc.getLastImage()
            self.Current_Image.setImage(data,autoLevels=True)
       
    def GetProperties(self, event = None):
        global prop_win
        prop_win = MMPropertyBrowser(self.mmc)
        prop_win.show()
    def Idle(self):
        self.mmc.waitForDevice(self.CRISP_label)
        self.mmc.setProperty(self.CRISP_label, 'CRISP State', 'Idle')
        self.crisp_status.setText('Idle')
    def Dither(self):
        self.mmc.waitForDevice(self.CRISP_label)
        self.mmc.setProperty(self.CRISP_label, 'CRISP State', 'Dither')
        self.crisp_status.setText('Dither')
    def Lock(self):
        self.PosTimer.stop()
        time.sleep(.01)
        self.mmc.enableContinuousFocus(True)
        self.PosTimer.start(200)
        #self.lock_status.setText('Locked')
    def Unlock(self):
        self.mmc.enableContinuousFocus(False)
        #self.lock_status.setText('Unlocked')
    def ResetOffset(self):
        self.mmc.setProperty(self.CRISP_label, 'CRISP State', 'Reset Focus Offset')
    def LogCal(self):
        self.mmc.setProperty(self.CRISP_label, 'CRISP State', 'loG_cal')
        if self.mmc.deviceBusy(self.CRISP_label) == True:
            self.crisp_status.setText('Calibrating')
        else:
            self.crisp_status.setText('Calibrated')
    def GetObjNA(self):
        NA = float(self.obj_NA.text())
        self.mmc.setProperty(self.CRISP_label, 'Objective NA', NA)
    def SetLEDIntensity(self):
        LED = self.LED_spinbox.value()
        self.mmc.setProperty(self.CRISP_label, 'LED Intensity', LED)
    def SetGain(self):
        self.mmc.setProperty(self.CRISP_label, 'CRISP State', 'gain_Cal')
        if self.mmc.deviceBusy(self.CRISP_label) == False:
            self.crisp_status.setText('Gain Set')
        self.GetSignal()
    def GetSignal(self):
        S_N = self.mmc.getProperty(self.CRISP_label, 'Signal Noise Ratio')
        self.signal_noise_ratio.setText(str(S_N))
    def GoHome(self):

        self.mmc.setXYPosition(self.XY_label, 0 , 0)
    def DefineHome(self,evt=None):
        self.mmc.setOriginXY(self.XY_label)
    def CenterAxis(self,axis='X'):
      
        old_timeout = self.mmc.getTimeoutMs()

        self.mmc.setTimeoutMs(90000)
        cmd = "SI %s=0\r\n"%axis
        print "sending command",cmd
        self.mmc.writeToSerialPort(self.TIGER_port,cmd)
        time.sleep(2)
        print "waiting for device"
        self.mmc.waitForDevice(self.XY_label)
        print "waiting 2"
        self.mmc.waitForDevice(self.XY_label)
        print "done waiting"
        self.mmc.setTimeoutMs(old_timeout)
        
    def CenterX(self):     
        self.CenterAxis(axis='X')

    def CenterY(self): 
        self.CenterAxis(axis='Y')

    def CenterXY(self):
        print "centering xy"

       
        self.DefineHome()
        self.CenterAxis('X')
        self.CenterAxis('Y')
        print "done centering, moving to center"
        self.mmc.setXYPosition(self.XY_label,0.0,2000.0)
        time.sleep(.1)
        print "waiting for move"
        self.mmc.waitForDevice(self.XY_label)
        print "done waiting for move"
        self.DefineHome()

    def GetXYSpeed(self):
        cmd = "SPEED X? Y?"
        self.mmc.setSerialPortCommand(self.TIGER_port,cmd,'\r\n')
        ans = self.mmc.getSerialPortAnswer(self.TIGER_port,'\r\n')
        print "get xy speed",ans
        print len(ans)
        #:A X=5.745920 Y=5.745920
        newans = ans.translate(None, 'XY=')
        parts =newans.split(' ')
        xspeed = float(parts[1])
        yspeed = float(parts[2])
        return xspeed, yspeed
        # yspeed = 
    def SetXYSpeed(self,xspeed,yspeed):
        cmd = "SPEED X=%f Y=%f\r\t"%(xspeed,yspeed)
        self.mmc.writeToSerialPort(self.TIGER_port,cmd)

    # def MapSurface(self):

    #     X_Range = self.max_x_array_val.value()
    #     Y_Range = self.max_y_array_val.value()
    #     XPosition_list = []
    #     YPosition_list = []
    #     ZPosition_list = []
    #     X_step = self.x_step_val.value()
    #     Y_step = self.y_step_val.value()
    #     a = np.arange(0, X_Range, X_step)
    #     b = np.arange(0, Y_Range, Y_step)
    #     for x, y in np.nditer([a,b]):
    #         self.mmc.setXYPosition(self.XY_label,float(x), float(y))
    #         XPosition_list.append(float(x))
    #         YPosition_list.append(float(y))
    #         z = self.mmc.getPosition(self.Z_label)
    #         ZPosition_list.append(z)
    #     Position = np.dstack((XPosition_list, YPosition_list))
    #     Position = np.dstack((Position, ZPosition_list))
    #     f = open('PositionOutput.csv', 'w')
    #     for item in Position:
    #         item = str(item)
    #         item = item.translate(None, '[]')
    #         f.write(item + '\n')
    #     f.close()
    def MapSurface2_0(self):
        savename = QtGui.QFileDialog.getSaveFileName(self, 'Save File', '.')
        X_max = self.max_x_array_val.value()
        Y_max = self.max_y_array_val.value()
        X_min = self.min_x_array_val.value()
        Y_min = self.min_y_array_val.value()
        X_step = self.x_step_val.value()
        Y_step = self.y_step_val.value()
        X_cor = np.arange(X_min, X_max, X_step)
        Y_cor = np.arange(Y_min, Y_max, Y_step)
        x_now=self.mmc.getXPosition(self.XY_label)
        y_now=self.mmc.getYPosition(self.XY_label)
        dx = X_cor[0]-x_now
        dy = Y_cor[0]-y_now
        while (abs(dx)+abs(dy))>2000:
            dxm = np.sign(dx)*min(abs(dx),2000)
            dym = np.sign(dy)*min(abs(dy),2000)
            self.mmc.setRelativeXYPosition(self.XY_label,dxm,dym)
            self.mmc.waitForDevice(self.XY_label)
            self.WaitTillLocked()
            piezo = self.mmc.getPosition(self.PIEZO_label)
            if abs(piezo) >= 60:
                self.ResetPiezo()

            x_now=self.mmc.getXPosition(self.XY_label)
            y_now=self.mmc.getYPosition(self.XY_label)
            dx = X_cor[0]-x_now
            dy = Y_cor[0]-y_now

        self.SetXYSpeed(5.7,5.7)

        df = pd.DataFrame()

        xv, yv = np.meshgrid(X_cor, Y_cor, indexing='ij')
        A,B = xv.shape
        dz_counter = 0.0

        self.PosTimer.stop()
        time.sleep(.3)

        try:
            for i in range(A):
                for j in range(B): 
                    self.mmc.setXYPosition(self.XY_label, xv[i,j], yv[i,j])
                    self.mmc.waitForDevice(self.XY_label)
                    self.WaitTillLocked()
                    entry = {}
                    entry['x'] =  self.mmc.getXPosition(self.XY_label)
                    entry['y'] =  self.mmc.getYPosition(self.XY_label)
                    z = self.mmc.getPosition(self.Z_label)
                    entry['z_step'] = z
                    p = self.mmc.getPosition(self.PIEZO_label)
                    entry['piezo'] = p
                    entry['dz_counter']= dz_counter
                    focus = self.mmc.getCurrentFocusScore()
                    entry['focus'] = focus
                    entry['i']=i
                    entry['j']=j
                    df=df.append(entry,ignore_index=True)
                    piezo = self.mmc.getPosition(self.PIEZO_label)
                    if abs(piezo) >= 60:

                        self.ResetPiezo()
                        pnew = self.mmc.getPosition(self.PIEZO_label)
                        dz_counter += (p - pnew)
                        # self.mmc.sleep(0.1)
                    #XPosition_list.append(x)
                    #YPosition_list.append(y)
                    #ZPosition_list.append(z)
                    #PIEZOPosition_list.append(piezo)
                    #Absolute_Z_list.append(absolute_z)
        except Freakout:
            print "Sir I have a message from Robin: Holy Smokes Batman"
            print "We have lost lock!"
        df.to_csv(savename)
        self.PosTimer.start(200)
        print "Alfred: Endure, Master Wayne. Take it. They'll hate you for it, but that's the point of Batman, he can be the outcast. He can make the choice that no one else can make, the right choice."
    def SetOrigin(self):

        self.mmc.setOriginXY(self.XY_label)

    def WaitTillLocked(self,dt = .1):
       is_locked = self.mmc.isContinuousFocusLocked()
       while not is_locked:
           print "locking..."
           self.mmc.sleep(dt)
           #focal_score = self.mmc.getCurrentFocusScore()
           is_locked = self.mmc.isContinuousFocusLocked()
           crisp_state = self.mmc.getProperty(self.CRISP_label,"CRISP State")
           if crisp_state != "In Focus":
               if crisp_state != "Lock":
                   raise Freakout

    def ResetPiezo(self):

        piezo = self.mmc.getPosition(self.PIEZO_label)
        z = self.mmc.getPosition(self.Z_label)
        islocked = self.mmc.isContinuousFocusLocked()

        if islocked:
            self.mmc.enableContinuousFocus(False)

        self.mmc.setPosition(self.Z_label,z-piezo)
        self.mmc.setPosition(self.PIEZO_label,0)

        if islocked:
            self.mmc.enableContinuousFocus(True)

            try:
                self.WaitTillLocked()
            except Freakout:
                print "oh no Batman we lost lock on Piezo Reset"

        # else:
        #     print "am locked "
        #     step = piezo/50.0
        #     self.mmc.setRelativePosition(self.Z_label, -step)
        #     # for i in range(20): 
        #     #     self.mmc.setRelativePosition(self.Z_label, -step)
        #     #     time.sleep(.25)
        #     self.mmc.setPosition(self.PIEZO_label, 0)

    def TakeZstack(self, evt,filename,zrange = 1.8, dz = .1):
        # filename = QtGui.QFileDialog.getSaveFileName(self, 'Save File', '.')
        self.PosTimer.stop()
        z = self.mmc.getPosition(self.Z_label)
        x = self.mmc.getXPosition(self.XY_label)
        islocked = self.mmc.isContinuousFocusLocked()
        pstep = 0.1
        start = self.mmc.getPosition(self.PIEZO_label)
        print islocked
        if islocked:
            self.Unlock()
            self.mmc.waitForDevice(self.PIEZO_label)
        if self.mmc.isSequenceRunning():
            self.mmc.stopSequenceAcquisition()
        self.mmc.waitForDevice(self.PIEZO_label)
        time.sleep(0.01)
        zlist = np.arange(start-zrange,start+zrange,dz)
        print zlist,start,start-zrange,start+zrange,dz,zrange,type(start),type(zrange)
        time.sleep(0.1)
        self.mmc.waitForDevice(self.PIEZO_label)
        self.mmc.setPosition(self.PIEZO_label, zlist[0])
        M = self.mmc.getImageWidth()
        N = self.mmc.getImageHeight()

        if self.mmc.getBytesPerPixel()==2:
            dtype = np.uint16
        else:
            dtype = np.uint8

        stack = np.zeros((len(zlist),N,M),dtype)

        for n,z in enumerate(zlist):
            self.mmc.setPosition(self.PIEZO_label, z)
            self.mmc.waitForDevice(self.PIEZO_label)
            print z
            stack[n,:,:] = self.TakePic()
               
        self.mmc.setPosition(self.PIEZO_label, start)
        time.sleep(0.1)
        try:
            tif.imsave(filename,stack)
        except IOError:
            pass 
        if islocked:
            self.mmc.enableContinuousFocus(True)
            self.PosTimer.start(200)
            try:
                self.WaitTillLocked()
            except Freakout:
                print 'Well rats, we\'ve lost lock'
        # if not self.mmc.isSequenceRunning():
        #     self.StartVideo()
        print 'Anything else Master Bruce?'
        

    def ArrayMap(self):
        savename = QtGui.QFileDialog.getSaveFileName(self, 'Save File', '.')
        print savename, type(savename)
        (savedir, savefile) = os.path.split(str(savename))
        (savebase,saveext)=os.path.splitext(savefile)
        if self.mmc.isSequenceRunning():
            self.mmc.stopSequenceAcquisition()
        X_max = self.max_x_array_val.value()
        Y_max = self.max_y_array_val.value()
        X_min = self.min_x_array_val.value()
        Y_min = self.min_y_array_val.value()
        print X_max,X_min,Y_max,Y_min
        X_step = self.x_step_val.value()
        Y_step = self.y_step_val.value()
        X_cor = np.arange(X_min, X_max, X_step)
        Y_cor = np.arange(Y_min, Y_max, Y_step)
        x_now = self.mmc.getXPosition(self.XY_label)
        y_now = self.mmc.getYPosition(self.XY_label)
        dx = X_cor[0]-x_now
        dy = Y_cor[0]-y_now
        picnumber = int((abs(Y_max) + abs(Y_min))/Y_step)
        print picnumber

        while (abs(dx) + abs(dy)) > 2000:
            dxm = np.sign(dx)*min(abs(dx),2000)
            dym = np.sign(dy)*min(abs(dy),2000)
            self.mmc.setRelativeXYPosition(self.XY_label,dxm,dym)  #sets relative position of xystage from current position to + dxm,dym
            self.mmc.waitForDevice(self.XY_label)
            piezo = self.mmc.getPosition(self.PIEZO_label)
            if abs(piezo) >= 60:
                self.ResetPiezo()

            x_now = self.mmc.getXPosition(self.XY_label)
            y_now - self.mmc.getYPosition(self.XY_label)
            dx = X_cor[0] - x_now
            dy = Y_cor[0] - y_now

        self.SetXYSpeed(5.7,5.7)
        df = pd.DataFrame()
        xv, yv = np.meshgrid(X_cor, Y_cor, indexing='ij')
        A,B = xv.shape
        dz_counter = 0.0

        self.PosTimer.stop()
        time.sleep(.3)
        M = self.mmc.getImageWidth()
        N = self.mmc.getImageHeight()
        if self.mmc.getBytesPerPixel()==2:
            dtype = np.uint16
        else:
            dtype = np.uint8

        stack = np.zeros((picnumber,N,M),dtype)

        try:
            for i in range(A):
                for j in range(B):
                    self.mmc.setXYPosition(self.XY_label,xv[i,j],yv[i,j])
                    self.mmc.waitForDevice(self.XY_label)
                    self.WaitTillLocked()

                    # filename = "%s_i%03d_j%03d.tif"%(savebase,i,j)
                    filename = "%s_i%03d.tif"%(savebase,i)
                    filename = os.path.join(savedir,filename)
                    # self.mmc.snapImage(None,filename)
                    stack[j,:,:]= self.TakePic()


                    entry = {} 
                    entry['x']= self.mmc.getXPosition(self.XY_label)
                    entry['y'] = self.mmc.getYPosition(self.XY_label)
                    z = self.mmc.getPosition(self.Z_label)
                    entry['z_step'] = z
                    p = self.mmc.getPosition(self.PIEZO_label)
                    entry['peizo'] = p
                    entry['dz_counter']= dz_counter
                    focus = self.mmc.getCurrentFocusScore()
                    entry['focus'] = focus
                    entry['i'] = i
                    entry['j'] = j
                    df.append(entry, ignore_index = True)
                    # for n in range(1):
                    #     stack[n,:,:] = self.TakePic()
                    
                    piezo = self.mmc.getPosition(self.PIEZO_label)
                    if abs(piezo) >= 60:
                        self.ResetPiezo()
                        pnew = self.mmc.getPosition(self.PIEZO_label)
                        dz_counter += (p - pnew)
                try:
                    tif.imsave(filename,stack)
                except IOError:
                        pass 
                print "stack saved"
        except Freakout:
               print 'Holy Rusted Metal Batman: We have lost lock!'
        try:
            df.to_csv(savename)
        except:
            pass
        self.PosTimer.start(200)
        print "Alfred: Endure, Master Wayne. Take it. They'll hate you for it, but that's the point of Batman, he can be the outcast. He can make the choice that no one else can make, the right choice."





    def ZMap(self):
        savename = QtGui.QFileDialog.getSaveFileName(self, 'Save File', '.')
        print savename, type(savename)
        (savedir,savefile)=os.path.split(str(savename))
        (savebase,saveext)=os.path.splitext(savefile)

        X_max = self.max_x_array_val.value()
        Y_max = self.max_y_array_val.value()
        X_min = self.min_x_array_val.value()
        Y_min = self.min_y_array_val.value()
        X_step = self.x_step_val.value()
        Y_step = self.y_step_val.value()
        X_cor = np.arange(X_min, X_max, X_step)
        Y_cor = np.arange(Y_min, Y_max, Y_step)
        x_now=self.mmc.getXPosition(self.XY_label)
        y_now=self.mmc.getYPosition(self.XY_label)
        dx = X_cor[0]-x_now
        dy = Y_cor[0]-y_now
        while (abs(dx)+abs(dy))>2000:
            dxm = np.sign(dx)*min(abs(dx),2000)
            dym = np.sign(dy)*min(abs(dy),2000)
            self.mmc.setRelativeXYPosition(self.XY_label,dxm,dym)
            self.mmc.waitForDevice(self.XY_label)
            piezo = self.mmc.getPosition(self.PIEZO_label)
            if abs(piezo) >= 60:
                self.ResetPiezo()

            x_now=self.mmc.getXPosition(self.XY_label)
            y_now=self.mmc.getYPosition(self.XY_label)
            dx = X_cor[0]-x_now
            dy = Y_cor[0]-y_now
            

        self.SetXYSpeed(5.7,5.7)

        df = pd.DataFrame()

        xv, yv = np.meshgrid(X_cor, Y_cor, indexing='ij')
        A,B = xv.shape
        dz_counter = 0.0

        self.PosTimer.stop()
        time.sleep(.3)

        try:
            for j in range(B):
                for i in range(A):

                    self.mmc.setXYPosition(self.XY_label, xv[i,j], yv[i,j])
                    self.mmc.waitForDevice(self.XY_label)
                    self.WaitTillLocked()
                    
                    filename = "%s_i%03d_j%03d.tif"%(savebase,i,j)
                    filename = os.path.join(savedir,filename)
                    self.TakeZstack(None,filename)
                    # self.WaitTillLocked()
                    entry = {}
                    entry['x'] =  self.mmc.getXPosition(self.XY_label)
                    entry['y'] =  self.mmc.getYPosition(self.XY_label)
                    z = self.mmc.getPosition(self.Z_label)
                    entry['z_step'] = z
                    p = self.mmc.getPosition(self.PIEZO_label)
                    entry['piezo'] = p
                    entry['dz_counter']= dz_counter
                    focus = self.mmc.getCurrentFocusScore()
                    entry['focus'] = focus
                    entry['i']=i
                    entry['j']=j
                    df=df.append(entry,ignore_index=True)
                    piezo = self.mmc.getPosition(self.PIEZO_label)
                    if abs(piezo) >= 60:
                        self.ResetPiezo()
                        pnew = self.mmc.getPosition(self.PIEZO_label)
                        dz_counter += (p - pnew)
        except Freakout:
            print "Sir I have a message from Robin: Holy Smokes Batman"
            print "We have lost lock!"
        df.to_csv(savename)
        self.PosTimer.start(200)
        print "Alfred: Endure, Master Wayne. Take it. They'll hate you for it, but that's the point of Batman, he can be the outcast. He can make the choice that no one else can make, the right choice."





if __name__ == "__main__":
    print "Hello world, I am Alfred. I have just achieved conciousness"
    mmc = MMCorePy.CMMCore()
    configFile = 'C:\Users\Administrator\Documents\ASI_Zyla_Laser.cfg'
    mmc.loadSystemConfiguration(configFile)
    app = QtGui.QApplication(sys.argv) #opens window

    print mmc.getLoadedDevices()
    # print mmc.getDevicePropertyNames('CRISPAFocus:P:34')
    # print mmc.getAllowedPropertyValues('CRISPAFocus:P:34','CRISP State')
    # print mmc.getProperty('CRISPAFocus:P:34', 'Objective NA')
    window = ASI_AutoFocus(mmc)
    window.show()
    window.StopVideo()

    app.exec_()
    mmc.unloadAllDevices()
    mmc.reset()
    sys.exit()



    #sys.exit(app.exec_())


    #mmc.reset()

    #app = QApplication(sys.argv)
    #app.lastWindowClosed.connect(app.quit)