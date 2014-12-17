#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""
Created on 23 March 2014.
@author: Eugene Dvoretsky

Live video acquisition with Micro-Manager adapter and opencv.
Another example with exposure and gain control.
"""

import numpy as np
import cv2
import MMCorePy
import matplotlib.pyplot as plt

WIDTH, HEIGHT = 320, 240
DEVICE = ['Camera', 'DemoCamera', 'DCam']
# DEVICE = ['Camera', 'OpenCVgrabber', 'OpenCVgrabber']
# DEVICE = ['Camera', "BaumerOptronic", "BaumerOptronic"]


def set_mmc_resolution(mmc, width, height):
    """Select rectangular ROI in center of the frame.
    """
    x = (mmc.getImageWidth() - width) / 2
    y = (mmc.getImageHeight() - height) / 2
    #mmc.setROI(x, y, width, height)


def main():
    """Looping in function should be faster then in global scope.
    """
    mmc = MMCorePy.CMMCore()
    filename="C:\Users\Smithlab\Documents\ASI_LUM_RETIGA_CRISP.cfg"
    mmc.loadSystemConfiguration(filename)
    mmc.enableStderrLog(False)
    mmc.enableDebugLog(False)
    # mmc.setCircularBufferMemoryFootprint(100)
    cam=mmc.getCameraDevice()
    
    mmc.setConfig('Channels','DAPI')
    mmc.waitForConfig('Channels','DAPI')
    #self.mmc.setShutterOpen(False)
    
    #cv2.namedWindow('MM controls')
    #if mmc.hasProperty(cam, 'Gain'):
    #    cv2.createTrackbar(
    #        'Gain', 'MM controls',
    #        int(float(mmc.getProperty(cam, 'Gain'))),
    #        int(mmc.getPropertyUpperLimit(cam, 'Gain')),
    #        lambda value: mmc.setProperty(cam, 'Gain', value))
    #if mmc.hasProperty(cam, 'Exposure'):
    #    cv2.createTrackbar(
    #       'Exposure', 'MM controls',
    #      int(float(mmc.getProperty(cam, 'Exposure'))),
    #     100,  # int(mmc.getPropertyUpperLimit(DEVICE[0], 'Exposure')),
    #        lambda value: mmc.setProperty(cam, 'Exposure', int(value)))

    set_mmc_resolution(mmc, WIDTH, HEIGHT)
    mmc.setProperty(cam, 'Gain', 20)
    mmc.snapImage()  # Baumer workaround
    data=mmc.getImage()
    gray = data.view(dtype=np.uint8)
    fig=plt.figure(1)
    ax1 = fig.add_subplot(1, 1, 1)
    theimg=ax1.imshow(gray,cmap='gray')
    plt.ion()
    plt.show(False)
   # cv2.namedWindow('Video',flags=cv2.WINDOW_NORMAL )
    mmc.startContinuousSequenceAcquisition(1)
    while True:
        remcount = mmc.getRemainingImageCount()
        print('Images in circular buffer: %s') % remcount
        if remcount > 0:
            # rgb32 = mmc.popNextImage()
            rgb32 = mmc.getLastImage()
            gray = rgb32.view(dtype=np.uint8)
            gray=cv2.equalizeHist(gray)
            theimg.set_array(gray)
            plt.draw()
            #cv2.imshow('Video', gray)
        else:
            print('No frame')
        if cv2.waitKey(5) >= 0:
            break
    cv2.destroyAllWindows()
    mmc.stopSequenceAcquisition()
    mmc.reset()


if __name__ == '__main__':
    main()