
# -*- coding: utf-8 -*-
# based on pyqtgraph\examples\ImageItem.py
from PyQt4 import QtCore, QtGui, uic
import numpy as np
import pyqtgraph as pg
import os.path
from imageSourceMM import imageSource
import pandas as pd
# class myHistographLUTItem(pg.HistogramLUTItem):
#     def __init__(self,*kargs,**kwargs):
#         super(myHistographLUTItem, self).__init__(*kargs,**kwargs)
#         self.plot.rotate(-90)
#         self.gradient.setOrientation('bottom')

class RetakeView(QtGui.QWidget):

    def __init__(self,mp,channel):
        super(RetakeView,self).__init__()

        self.mp = mp
        self.initUI()
        #setup dummy variables of blanks for live and review data
        self.live_data = np.zeros(5,5)
        self.review_data = np.zeros(5,5)

        #initialize section,frame, ch and  initialization state
        self.section = 0
        self.frame = 0
        self.ch = self.mp.channel_settings.channels[0]
        self.initial_offset = self.mp.imgSrc.get_autofocus_offset()
        #get the outdirectory from mosaicplanner settings
        for key,value in self.mp.outdirdict.iteritems():
            self.outdir = self.outdirdict[key]
        #load the focus score data
        self.loadFocusScoreData()

    
    def initUI(self):
        #load the UI from layout file
        currpath=os.path.split(os.path.realpath(__file__))[0]
        filename = os.path.join(currpath,'Retake.ui')
        uic.loadUi(filename,self)

        #add a pyqtgraph image to graphics view
        self.img = pg.ImageItem()
        p1 = self.image_graphicsLayoutWidget.addPlot()
        p1.addItem(self.img)
        self.hist = pg.HistogramLUTItem()
        self.hist.setImageItem(self.img)
        self.graphicsLayoutWidget.addItem(self.hist,0,1)
        self.img.setLevels(o,self.mp.imgSrc.get_max_pixel_value())
        self.hist.setLevels(0,self.mp.imgSrc.get_max_pixel_value())

        #setup the channel buttons 
        self.chnButtons=[]
        for i,ch in enumerate(self.mp.channel_settings.channels):
            btn=QtGui.QRadioButton(ch)
            self.chnButtons.append(btn)
            self.channel_verticalLayout.addWidget(btn)
            btn.clicked.connect(lambda: self.changeChannel(ch))

        #initialize AFCoffset UI, and connect valueChanged to setting it
        self.AFCoffset_doubleSpinBox.setValue(self.initial_offset)
        self.AFCoffset_doubleSpinBox.valueChanged[float].connect(self.mp.imgSrc.set_autofocus_offset)

        #connect various UI slots to their change functions
        self.section_spinBox.valueChanged[int].connect(self.changeSection)
        
        self.frame_spinBox.valueChanged[int].connect(self.changeFrame)
        
        self.move_pushButton.clicked.connect(self.moveToFrame)
        
        self.review_pushButton.clicked.connect(self.reviewFrame)
        
        self.softwareaf_pushButton.clicked.connect(self.mp.on_software_af_tool)

        self.livereview_pushButton.clicked[bool].connect(self.changeLiveReview)
        
        self.exit_pushButton.clicked.connect(self.exitClicked)

    def loadFocusScoreData(self):
        score_ch=self.mp.cfg['ChannelSettings']['focusscore_chan']
        protName = self.mp.channel_settings.prot_names[score_ch]
        ch_dir = os.path.join(self.outdir,protName)
        data_files = [os.path.join(data_directory,f) for f in os.listdir(data_directory) if f.endswith('.csv') ]
        df = pd.DataFrame()
        data_files.sort()
        for data_file in data_files:
            dft = pd.read_csv(data_file)
            df = df.append(dft,ignore_index=True)
        
        frame1 = df[df['section']==0]
        frame_medians = df.groupby('frame')['score1_median'].median()
        frame_stds = df.groupby('frame')['score1_median'].std()

        for i,row in df.iterrows():
            df.loc[i,'score1_norm'] = (row.score1_median - frame_medians[row.frame])/frame_std[row.frame]
        
        self.focus_df = df

    def reviewFrame(self,evt=None):
        self.changeReviewData()
        self.changeLiveReview(isLive=False)

    def moveToFrame(self,evt=None):
        pos = self.mp.posList.slicePositions[self.section]
        fpos = pos.frameList.slicePositions[self.frame]
        self.mp.imgSrc.move_stage(fpos.x,fpos.y)

    def changeLiveReview(self,isLive):
        self.review_pushButton.setDown(isLive)
        if isLive:
            self.review_pushButton.setText("Showing Live")
            self.loadLiveData()
        else:
            self.review_pushButton.setText("Showing Review")
            self.loadReviewData()

    def changeReviewData(self,evt=None):
        ch_dir = os.path.join(self.outdir,self.mp.channel_settings.prot_names[ch])
        tif_filepath = os.path.join(ch_dir, prot_name + "_S%04d_F%04d_Z%02d.tif" % (slice_index, frame_index, 0))
        data = tiffile.imread(tif_filepath)
        self.review_data = data

    def changeChannel(self,ch):
        self.ch = ch

    def changeSection(self,section):
        self.section = section

    def changeFrame(self,frame):
        self.frame = frame

    def exitClicked(self,evt):
        print "exiting"
        self.hide()
 
    def loadLiveData(self,evt=None):
        self.img.setImage(self.live_data)
        
    def loadReviewData(self,evt=None):
        self.img.setImage(self.review_data)

    def doSnap(self,evt=None):
        self.mp.imgSrc.set_channel(self.ch)
        self.mp.imgSrc.set_exposure(self.mp.channel_settings.exposure_times[self.ch])
        data=self.mp.imgSrc.snap_image()
        self.live_data = data
        self.changeLiveReview(isLive=True)
