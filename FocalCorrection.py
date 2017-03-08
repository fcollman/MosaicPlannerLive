import sys
import numpy as np
import time
import csv
import pandas as pd
import os
from scipy import interpolate
import MMCorePy
from PyQt4 import QtCore, QtGui, uic
import pyqtgraph as pg
from matplotlib.mlab import griddata
import itertools
import statsmodels.api as sm


# import matplotlib.pyplot as plt
# import matplotlib.pyplot as plt
# from mpl_toolkits.mplot3d import Axes3D
# from matplotlib.figure import Figure
# from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
# from pyqtgraph.Qt import QtCore, QtGui


#### Currently will only hold pre defined functions that I know I will need to use,
### will add the UI setup later

class FocalCorrectionObject2():
    """Method for fitting approximate focal plane of a given sample using a two
    dimmensional bicubic spline interpolation. For N knots(sample points) on the surface
    the interpolation method fits a function z = f(x,y) of degree n, typically three.
    In order for the interpolation to work propertly one needs N = (n+1)**2 knots"""

    def __init__(self, Knots=None):
        self.Knots = Knots
        # self.FocalDict = {'Linear Regression': self.get_z_LinearRegression(),
        #                   'Polynomial Fit': self.polyFit(),
        #                   'Plane Fit': self.planeFit()}
        self.FocalDict = {'Linear Regression': 0,
                          'Plane Fit': 1,
                          'Polynomial Fit': 2}

    def add_knot(self, x, y, z):
        knot = np.array([x,y,z])
        if self.Knots is None:
            self.Knots = np.array([knot])
        else:
            self.Knots=np.vstack((self.Knots,knot))


    def remove_knot(self):
        print len(self.Knots)
        self.Knots.pop()  # removes last item from list Knots
        print len(self.Knots)

    def polyfit2d(self,x, y, z, order=3):
        ncols = (order + 1)**2
        G = np.zeros((x.size, ncols))
        ij = itertools.product(range(order+1), range(order+1))
        for k, (i,j) in enumerate(ij):
            G[:,k] = x**i * y**j
        m, _, _, _ = np.linalg.lstsq(G, z)
        return m

    def polyval2d(self,x, y, m):
        order = int(np.sqrt(len(m))) - 1
        ij = itertools.product(range(order+1), range(order+1))
        z = np.zeros_like(x)
        for a, (i,j) in zip(m, ij):
            z += a * x**i * y**j
        return z


    def polyFit(self,points,order=2):
        print 'poly fit'
        x = points[:,0]
        y = points[:,1]
        z = points[:,2]
        m = self.polyfit2d(x,y,z,order)
        return m

    def planeFit(self,points):
        print 'plane fit'
        from numpy.linalg import svd
        points = points.T
        assert points.shape[0] < points.shape[1]
        ctr = points.mean(axis=1)
        x = points - ctr[:,None]
        M = np.dot(x, x.T)
        pt_on_plane = ctr
        norm =  svd(M)[0][:,-1]
        d=norm[0]*pt_on_plane[0]+norm[1]*pt_on_plane[1]+norm[2]*pt_on_plane[2]
        ax=-norm[0]/norm[2]
        ay=-norm[1]/norm[2]
        b = d/norm[2]
        return ax,ay,b

    def get_z_LinearRegression(self,xo,yo):
        print 'linear regression'
        dist_sigma = 1000
        xx= self.Knots[:,0]
        yy= self.Knots[:,1]
        dd = np.sqrt((xx-xo)**2 + (yy-yo)**2)
        print "dd",dd
        exponent = -(dd**2)/(2*(dist_sigma**2))
        print "exponent", exponent
        weights = np.exp(exponent)
        print "weights",weights

        X = self.Knots[:,0:2]
        X = sm.add_constant(X)
        y = self.Knots[:,2]

        mod_wls = sm.WLS(y, X, weights=weights)
        res_wls = mod_wls.fit()
        print(res_wls.summary())
        p = np.zeros((2,2),dtype=X.dtype)
        p[0,0] = xo
        p[0,1] = yo
        p[1,0] = xo
        p[1,0] = yo
        p = sm.add_constant(p)
        z = res_wls.predict(p)
        print "zshape",z

        return z[0]



    def get_z(self,x, y, method):
        xs,ys,zs = self.get_xyzs()
        #X = np.vstack((self.Knots[:,0:1],[x,y]))

        #ax,ay,b = self.planeFit(self.Knots)
        #focalZ = ax*x + ay*y + b

        #m = self.polyFit(self.Knots,2)
        #focalZ = self.polyval2d(x,y,m)
        if method == self.FocalDict.get('Linear Regression'):
            focalZ = self.get_z_LinearRegression(x,y)

        if method == self.FocalDict.get('Plane Fit'):

            ax,ay,b = self.planeFit(self.Knots)
            focalZ = ax*x + ay*y + b
        if method == self.FocalDict.get('Polynomial Fit'):
            m = self.polyFit(self.Knots,2)
            focalZ = self.polyval2d(x,y,m)

        # print 'focalz',focalZ

        return focalZ

    def clear_knots(self):
        self.Knots = None

    def get_xyzs(self):
        if self.Knots is None:
            xs,ys,zs = ([],[],[])
        else:
            xs = self.Knots[:,0]
            ys = self.Knots[:,1]
            zs = self.Knots[:,2]
        return xs,ys,zs


class FocalCorrectionObject():
    """Method for fitting approximating the focal plane of a given sample using a two
    dimmensional bicubic spline interpolation. For N knots(sample points) on the surface
    the interpolation method fits a function z = f(x,y) of degree n, typically three.
    In order for the interpolation to work propertly one needs N = (n+1)**2 knots"""

    def __init__(self, Knots=None):
        self.Knots = Knots
        self.__calc_surface_switch()

    def add_knot(self, x, y, z):
        knot = np.array([x,y,z])
        if self.Knots is None:
            self.Knots = np.array([knot])
        else:
            self.Knots=np.vstack((self.Knots,knot))

        self.__calc_surface_switch()

    def remove_knot(self):
        print len(self.Knots)
        self.Knots.pop()  # removes last item from list Knots
        print len(self.Knots)
        self.__calc_surface_switch()

    def get_z(self,x, y):
        if self.tck is not None:
            focalZ = interpolate.bisplev(x, y, self.tck)
        return focalZ

    def __calc_surface_switch(self):
        if self.Knots is not None:
            N,M = self.Knots.shape
        else:
            N=0

        if (N < 6) and (N >= 4):
            self.__calc_surface(1, 1)
        elif (N < 9) and (N >= 6):
            self.__calc_surface(2, 1)
        elif (N < 12) and (N >= 9):
            self.__calc_surface(2, 2)
        elif (N < 16) and (N >= 12):
            self.__calc_surface(3, 2)
        elif N >= 16:
            self.__calc_surface(3, 3)  # kx = ky = 3 is the most efficient interpolation method
        else:
            self.tck = None

    def __calc_surface(self, kx, ky):
        self.tck = interpolate.bisplrep(self.Knots[:,0],self.Knots[:,1],self.Knots[:,2], kx=kx, ky=ky)

    def clear_knots(self):
        self.Knots = None
        self.__calc_surface_switch()

    def get_xyzs(self):
        if self.Knots is None:
            xs,ys,zs = ([],[],[])
        else:
            xs = self.Knots[:,0]
            ys = self.Knots[:,1]
            zs = self.Knots[:,2]
        return xs,ys,zs


#
# class Mpl_Knot_Canvas(FigureCanvas):
# 	def __init__(self):
# 		self.fig = Figure()
# 		self.ax = self.fig.add_subplot(111)
# 		FigureCanvas.__init__(self,sefl.fig)
# 		FigureCanvas.setSizePolicy(self, QtGui.QSizePolicy.Expanding,
# 									self.QtGui.QSizePolicy.Expanding)
# 		FigureCanvas.updateGeometry(self)
#
# class Mpl_Knot_Map(QtGui.QWidget):
# 	def __init__(self, parent= None):
# 		QtGui.QWidget.__init__(self, parent)
# 		self.canvas = Mpl_Knot_Canvas()
# 		self.vbl = QtGui.QVBoxLayout()
# 		self.vbl.addWidget(self.canvas)
# 		self.setLayout(self.vbl)




class myPlotItem(pg.PlotItem):
    def __init__(self,interface,**kwargs):
        super(myPlotItem,self).__init__(**kwargs)
        self.interface = interface

    def mouseClickEvent(self,evt):
        if evt.double():
            print "i double clicked"
            x1,y1 = evt.pos()
            pos=self.vb.mapFromItemToView(self,evt.pos())
            x,y = (pos.x(),pos.y())

            #print evt.scenePos()
            #print evt.pos()

            #

            self.interface.move_with_interpolation(x,y)

class FocalCorrectionInterface(QtGui.QWidget):
    def __init__(self, mmc, myfocalcorrection=FocalCorrectionObject2()):
        super(FocalCorrectionInterface, self).__init__()
        self.myfocalcorrection = myfocalcorrection
        # self.config = config
        currpath = os.path.split(os.path.realpath(__file__))[0]
        filename = os.path.join(currpath, 'Interpolation_Interface.ui')
        uic.loadUi(filename, self)


        self.gv.setContentsMargins(0,0,0,0)
        self.vb = pg.ViewBox(invertY=True) #creates viewbox object
        self.gv.setCentralItem(self.vb) #inserts viewbox into graphics view
        self.vb.setAspectLocked()
        self.vb.setContentsMargins(0,0,0,0)
        self.current_image = pg.ImageItem()
        self.vb.addItem(self.current_image)

        self.knotView.setBackground('w')
        self.knotPlot = myPlotItem(self) #knot plot object inherits class attributes of myplot item, making it a pyqtgraph plot object
        self.knotPlot.invertY()
        self.knotView.setCentralItem(self.knotPlot) #inserts knotplot object into knotview (graphics view)
        #self.knotViewBox.setAspectLocked()
        #self.knotViewBox.setContentsMargins(0,0,0,0)
        self.knotScatter = pg.ScatterPlotItem(size=10, pen=pg.mkPen(None), brush=pg.mkBrush(0, 0, 0, 255))
        self.currPos = pg.ScatterPlotItem(size=5,pen=pg.mkPen(None), brush=pg.mkBrush(255, 0, 0, 255))

        self.knotPlot.addItem(self.knotScatter)
        self.knotPlot.addItem(self.currPos)


        self.mmc = mmc
        self.XY_label = self.mmc.getXYStageDevice()
        self.Z_label = self.mmc.getFocusDevice()
        self.add_knot.clicked.connect(self.addknot)
        self.remove_knot.clicked.connect(self.removeknot)

        self.clear_knots.clicked.connect(self.clearknots)
        # self.plot_knots.clicked.connect(self.plotknots)
        self.PosTimer = QtCore.QTimer(self)
        self.connect(self.PosTimer, QtCore.SIGNAL("timeout()"), self.updateposition)
        self.PosTimer.start(200)
        self.ended = False


        self.FocalDict = self.myfocalcorrection.FocalDict
        self.FocalDictkeys = self.FocalDict.keys()
        print self.FocalDict
        self.InterpMethodComboBox.addItems(self.FocalDictkeys)


        self.cam = self.mmc.getCameraDevice()

        self.XY_label = self.mmc.getXYStageDevice()


        print self.XY_label
        print self.mmc.getXPosition(self.XY_label)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.channelsComboBox.addItems(self.mmc.getAvailableConfigs('Channels'))
        self.objectivesComboBox.addItems(self.mmc.getAvailableConfigs('Objective'))
        self.objectivesComboBox.currentIndexChanged[str].connect(self.changeObjective)


        # self.channels = self.mmc.getChannelGroup()
        # print channels

        # self.channelpulldown = QtGui.QCombobox(self)
        # self.channelpulldown.addItems(self.channels)
        # channelpulldown.activated[str].connect(self.setChannel)
        self.take_pic.clicked.connect(self.takePic)
        self.start_video.clicked.connect(self.startVideo)
        self.stop_video.clicked.connect(self.stopVideo)

        self.VideoTimer = QtCore.QTimer(self)
        self.connect(self.VideoTimer, QtCore.SIGNAL("timeout()"), self.updateVideo)
        self.channelsComboBox.currentIndexChanged[str].connect(self.changeChannel)
        self.inc_exposure.clicked.connect(self.increaseExposure)
        self.dec_exposure.clicked.connect(self.decreaseExposure)
        self.mmc.setExposure(200)
        self.getExposure()

        self.loadknots()
        self.show()

    def changeObjective(self,obj):
        print obj
        self.mmc.setConfig('Objective',str(obj))

    def changeChannel(self,chan):
        print 'channel is ',chan
        self.mmc.setConfig('Channels',str(chan))

    def move_with_interpolation(self,x,y):
        print "move to ", x,y
        self.mmc.setXYPosition(self.XY_label,x,y)
        method = self.InterpMethodComboBox.currentText() #gets current text of combobox
        # print 'method', method
        method = self.FocalDict.get(str(method)) #returns value of entry in focal dictionary
        # print 'method', method
        z = self.myfocalcorrection.get_z(x,y, method) #inputs value into focal correction object to determine interpolation method
        print "z move to ", z
        print "current z",self.mmc.getPosition(self.Z_label)
        self.mmc.setPosition(self.Z_label,float(z))


    def setChannel(self, text):
        self.mmc.setConfig('Channels', text)

    def takePic(self):
        self.mmc.snapImage()
        img = self.mmc.getImage()
        self.current_image.setImage(img.T,autoLevels=True)
        self.vb.autoRange()
        return img

    def startVideo(self):

        if not self.mmc.isSequenceRunning():
            self.mmc.startContinuousSequenceAcquisition(1)
            self.VideoTimer.start(self.mmc.getExposure())

    def stopVideo(self):
        if self.mmc.isSequenceRunning():
            self.mmc.stopSequenceAcquisition()
            self.VideoTimer.stop()

    def updateVideo(self):
        remcount = self.mmc.getRemainingImageCount()
        if remcount > 0:
            data = self.mmc.getLastImage()
            self.current_image.setImage(data.T,autoscale=True)

    def getExposure(self):
        expo = str(self.mmc.getExposure())
        self.current_exposure.setText(expo)

    def increaseExposure(self):
        current = self.mmc.getExposure()
        new = current + 10
        self.mmc.setExposure(new)
        self.current_exposure.setText(str(new))

    def decreaseExposure(self):
        current = self.mmc.getExposure()
        new = current - 10
        self.mmc.setExposure(new)
        self.current_exposure.setText(str(new))

    def addknot(self):
        x = self.mmc.getXPosition(self.XY_label)  ### add labels for stages
        y = self.mmc.getYPosition(self.XY_label)
        z = self.mmc.getPosition(self.Z_label)
        #self.knotScatter.addPoints(spots= [{'pos': (x,y), 'size':5}])
        self.myfocalcorrection.add_knot(x, y, z)
        self.loadknots()

    def removeknot(self):
        # removes last knot from Knots
        self.myfocalcorrection.remove_knot()
        self.loadknots()

    def loadknots(self):
        xs,ys,zs = self.myfocalcorrection.get_xyzs()

        data_dict = [{'pos': (x,y), 'size':5} for x,y in zip(xs,ys)]

        if len(zs)>3:
            znorm = np.array(zs) - np.min(zs)
            range = np.max(znorm) - np.min(znorm)
            if range == 0:
                znorm =10
            else:
                znorm = znorm/range
                znorm = 5+15*znorm
        else:
            znorm = 10

        self.knotScatter.setData(pos=zip(xs,ys),size=znorm,pxMode=True)

    def clearknots(self, Knots):
        self.myfocalcorrection.clear_knots()
        self.knotScatter.clear()

        # def plotknots(self):
        # 	self.fig = Figure(facecolor = 'white')
        # 	self.canvas = FigureCanvas(self.fig)
        # 	self.ax1 = self.fig.add_subplot(111)
        # 	# self.knot_map.addWidget(self.canvas)
        # 	self.canvas.setParent(self.knot_map)
        # 	x,y,z = self.getcorlist()

        # 	cmap = plt.get_cmap('viridis')
        # 	self.ax1.plot(x,y)
        # 	self.canvas.draw()

    def updateposition(self):
        xpos = self.mmc.getXPosition(self.XY_label)
        ypos = self.mmc.getYPosition(self.XY_label)
        zpos = self.mmc.getPosition(self.Z_label)
        self.current_Xpos.setText(str(xpos))
        self.current_Ypos.setText(str(ypos))
        self.current_Zpos.setText(str(zpos))
        self.currPos.setData(spots= [{'pos': (xpos,ypos), 'size':10}])



if __name__ == "__main__":
    print 'hello world'
    app = QtGui.QApplication(sys.argv)  # opens window
    mmc = MMCorePy.CMMCore()
    # config = QtGui.QFileDialog.getOpenFileName(None, "Choose uManager config file")
    # config = str(config)
    config = 'C:\Users\SYNBIO-ZEISS\Desktop\Focal Interpolation\MMZeiss_andor.cfg'

    mmc.loadSystemConfiguration(config)
    print mmc.getLoadedDevices()
    window = FocalCorrectionInterface(mmc)
    window.show()

    app.exec_()

    # mmc.unloadAllDevices()

    # app = QApplication(sys.argv)
    # app.lastWindowClosed.connect(app.quit)
    sys.exit()
