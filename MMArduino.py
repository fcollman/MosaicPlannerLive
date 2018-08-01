import serial
import struct
import time
import numpy as np

class MMArduino(object):
    def __init__(self,port = 'COM8',baudrate = '57600'):
        self.ser = serial.Serial()
        self.ser.port = port
        self.ser.baudrate = baudrate
        self.ser.STOPBITS = 1
        self.ser.timeout =.5
        self.ser.open()
        time.sleep(2)
        self.ser.readlines()
        self.sendCmd(chr(27))
        self.sendCmd(chr(27))
        self.sendCmd(chr(27))
        self.sendCmd(chr(27))
    def sendMessage(self,message,debug=False):
        cmd = bytearray(message)
        answer = self.sendDirect(message,len(message))
        if debug:
            values = struct.unpack('B'*len(message),answer)
            print message,values
        return cmd == answer

    def sendDirect(self,cmd,bytesback=1):
        self.ser.write(cmd)
        return self.ser.read(bytesback)

    def sendCmd(self,cmd):
        self.ser.write(cmd)
        answer = self.ser.readline()
        #print 'answer:',answer[:-2]
        return answer[:-2]
    def getIdentity(self):
        return self.sendCmd(chr(30))
    def getVersion(self):
        return self.sendCmd(bytearray([31]))
    def setPattern(self,pattern=[0,0,0,0,0,0,0,1]):
        num = np.packbits(pattern)[0]
        cmd = bytearray([1,num])
        answer=self.sendDirect(cmd,1)

        return answer == bytearray([1])
    def getPattern(self):
        answer = self.sendDirect(chr(2),2)
        values = struct.unpack('BB',answer)
        pattern = np.unpackbits(bytearray([values[1]]))
        return pattern
    def setStoredPattern(self,patternNum,pattern=[0,0,0,0,0,0,0,1]):
        num =  np.packbits(pattern)[0]
        return self.sendMessage([5,patternNum,num])

    def setNumberOfPatterns(self,numPatterns):
        return self.sendMessage([6,numPatterns])

    def skipTrigger(self,numEvents):
        return self.sendMessage([7,numEvents])

    def startTriggerMode(self):
        return self.sendMessage([8])

    def stopTriggerMode(self):
        return self.sendMessage([9])
    def setPatternTimeInterval(self,patternNum,interval):
        interval=struct.pack('>H', interval)
        precmd = bytearray([10,patternNum])
        cmd = precmd+interval
        answer = self.sendDirect(cmd,2)
        return answer == precmd
    def setTimedPattern(self,patternNum,pattern,interval):
        ans1=self.setStoredPattern(patternNum,pattern)
        ans2=self.setPatternTimeInterval(patternNum,interval)
        return ans1 and ans2
    def setTimedPatternRepeats(self,numRepeats):
        return self.sendMessage([11,numRepeats])
    def startTimedPattern(self):
        return self.sendMessage([12])
    def startBlankingMode(self):
        return self.sendMessage([20])
    def stopBlankingMode(self):
        return self.sendMessage([21])
    def setBlankingDirection(self,blankHigh=True):
        if blankHigh:
            answer = self.sendDirect([22,0])
        else:
            answer = self.sendDirect([22,1])
        return answer == bytearray([22])
    def setTriggerPolarity(self,triggerHigh = True):
        if triggerHigh:
            return self.sendMessage([23,0])
        else:
            return self.sendMessage([23,1])
    
    def setupExposure(self,exposures,interframe=10,exp_pattern=[0,0,0,0,0,0,0,1]):
        i =0
        for exp in exposures:
            self.setTimedPattern(i,exp_pattern,exp)
            i+=1
            self.setTimedPattern(i,[0,0,0,0,0,0,0,0],2)
            i+=1
            self.setTimedPattern(i,[0,0,0,0,0,0,1,0],interframe)
            i+=1
        self.setTimedPatternRepeats(1)
        self.setNumberOfPatterns(3*len(exposures))

    def MoveFilter(self,interframe=10, move_pattern=[0,0,0,0,0,0,1,0]):
        self.setNumberOfPatterns(1)
        self.setPattern(move_pattern)
        self.startTimedPattern()

    def shutdown(self):
        self.ser.close()