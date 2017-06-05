import serial
import io
import numpy as np

class LeicaDMI(object):
    def __init__(self,serial_port):
        self.ser = serial.Serial(serial_port, 115200, timeout=3)
        self.sio = io.TextIOWrapper(io.BufferedRWPair(self.ser, self.ser,1),newline='\r',line_buffering=True)

    def sendCmd(self,cmd,debug = False):    
        if debug:
            print "sending: "+cmd
        self.sio.write(unicode(cmd+'\r'))
        self.sio.flush()
        answer = self.sio.readline()
        if debug:
            print "received: "+ answer
        return answer

    def get_AFC_image(self):
        self.sendCmd("48066 -1")
        Nloops = 323
        my_array = np.zeros(Nloops*8)
        for index in np.arange(0,2584,8):
            vals=self.sendCmd("48066 " + str(index))
            temp = np.array(map(int,vals.split()))
            my_array[index:index+8]=temp[2:]
        return my_array
    
    def get_AFC_score(self):
        ans = self.sendCmd("48030")
        score = ans.split()[-2]
        return float(score)
    
    def get_AFC_intensity(self):
        ans = self.sendCmd("48036")
        return int(ans.split()[1])

    def get_AFC_offset(self):
        ans = self.sendCmd("48025")
        return int(ans.split()[1])

    def set_AFC_intensity(self,intensity):
        assert (intensity<255)
        assert (intensity>0)
        return self.sendCmd('48035 %d'%int(intensity))
         
    def shutdown(self):
        self.ser.close()
        


