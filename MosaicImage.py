#===============================================================================
# 
#  License: GPL
# 
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License 2
#  as published by the Free Software Foundation.
# 
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
# 
#   You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
# 
#===============================================================================
 
 
from PIL import Image
#import ImageEnhance
import numpy as np
import threading
import os
import Queue
from CenterRectangle import CenterRectangle
from matplotlib.lines import Line2D
from ImageCollection import ImageCollection
from Settings import SiftSettings,CorrSettings
from Rectangle import Rectangle
import cv2 
import ransac
from skimage.measure import block_reduce
import norm_xcorr
from skimage.feature import register_translation
from skimage.feature.register_translation import _upsampled_dft
#implicity this relies upon matplotlib.axis matplotlib.AxisImage matplotlib.bar

import time
from bisect import bisect_right

#my custom 2d correlation function for numpy 2d matrices.. 
def mycorrelate2d(fixed,moved,skip=1):
    """a 2d correlation function for numpy 2d matrices
    
    arguments
    fixed) is the larger matrix which should stay still 
    moved) is the smaller matrix which should move left/right up/down and sample the correlation
    skip) is the number of positions to skip over when sampling, 
    so if skip =3 it will sample at shift 0,0 skip,0 2*skip,0... skip,0 skip,skip...
    
    returns
    corrmat) the 2d matrix with the corresponding correlation coefficents of the data at that offset
    note the 0,0 entry of corrmat corresponds to moved(0,0) corresponding to fixed(0,0)
    and the 1,1 entry of corrmat corresponds to moved(0,0) corresponding to fixed(skip,skip)
    NOTE) the height of corrmat is given by corrmat.height=ceil((fixed.height-moved.height)/skip)
    and the width in a corresonding manner.
    NOTE)the standard deviation is measured over the entire dataset, so particular c values can be above 1.0
    if the variance in the subsampled region of fixed is lower than the variance of the entire matrix
    
    """
    if skip>1:
        fixed = block_reduce(fixed,block_size = (int(skip),int(skip)),func = np.mean,cval=np.mean(fixed))
        moved = block_reduce(moved,block_size = (int(skip),int(skip)),func = np.mean,cval=np.mean(moved))

    (fh,fw)=fixed.shape
    (mh,mw)=moved.shape
    deltah=(fh-mh)
    deltaw=(fw-mw)
    #if (deltah<1 or deltaw<1):
    #    return
    #fixed=fixed-fixed.mean()
    #fixed=fixed/fixed.std()
    #moved=moved-moved.mean()
    #moved=moved/moved.std()
    # ch=np.ceil(deltah*1.0/skip)
    # cw=np.ceil(deltaw*1.0/skip)
    
    # corrmat=np.zeros((ch,cw))
    
    # #print (fh,fw,mh,mw,ch,cw,skip,deltah,deltaw)
    # for shiftx in range(0,deltaw,skip):
    #     for shifty in range(0,deltah,skip):
    #         fixcut=fixed[shifty:shifty+mh,shiftx:shiftx+mw]
    #         corrmat[shifty/skip,shiftx/skip]=(fixcut*moved).sum()
           
    # corrmat=corrmat/(mh*mw)
    

    corrmatt = norm_xcorr.norm_xcorr(moved,fixed, trim=True, method='fourier')

    print 'corrmatt',corrmatt.shape
    print 'moved',moved.shape
    print 'fixed',fixed.shape

    #image_product = np.fft.fft2(fixed) * np.fft.fft2(moved).conj()
    #corrmat = np.fft.fftshift(np.fft.ifft2(image_product))

    return corrmatt


#thread for making a cropped version of the big image... not very efficent    
class ImageCutThread(threading.Thread):
        def __init__(self, queue):
            threading.Thread.__init__(self)
            self.queue = queue        
        def run(self):
            while True:
                #grabs host from queue
                (filename,rect,i) = self.queue.get()
                image=Image.open(filename)
                image=image.crop(rect)
                (path,file)=os.path.split(filename)
                path=os.path.join(path,"previewstack")
                if not os.path.exists(path):
                    os.path.os.mkdir(path)
                cutfile=os.path.splitext(file)[0]+"stack%3d.tif"%i        
                cutfile=os.path.join(path,cutfile)
                image.save(cutfile)
                #signals to queue job is done
                self.queue.task_done()
                     
class MosaicImage():
    """A class for storing the a large mosaic imagein a matplotlib axis. Also contains functions for finding corresponding points
    in the larger mosaic image, and plotting informative graphs about that process in different axis"""
    def __init__(self,axis,one_axis,two_axis,corr_axis,imgSrc,rootPath,figure=None):
        """initialization function which will plot the imagematrix passed in and set the bounds according the bounds specified by extent
        
        keywords)
        axis)the matplotlib axis to plot the image into
        one_axis) the matplotlib axis to plot the cutout of the fixed point when using the corresponding point functionality
        two_axis) the matplotlib axis to plot the cutout of the point that should be moved when using the corresponding point functionality
        corr_axis) the matplotlib axis to plot out the matrix of correlation values found when using the corresponding point functionality
        imagefile) a string with the path of the file which contains the full resolution image that should be used when calculating the corresponding point funcationality
         currently the reading of the image is using PIL so the path specified must be an image which is PIL readable
        imagematrix) a numpy 2d matrix containing a low resolution varsion of the full resolution image, for the purposes of faster plotting/memory management
        extent) a list [minx,maxx,miny,maxy] of the corners of the image.  This will specify the scale of the image, and allow the corresponding point functionality
        to specify how much the movable point should be shifted in the units given by this extent.  If omitted the units will be in pixels and extent will default to
        [0,width,height,0].
       
        """
        #define the attributes of this class
        self.axis=axis
        self.one_axis=one_axis
        self.two_axis=two_axis
        self.corr_axis=corr_axis
            
        #initialize the images for the various subplots as None
        self.oneImage=None
        self.twoImage=None
        self.corrImage=None
        self.imgSrc = imgSrc
        self.imgCollection=ImageCollection(rootpath=rootPath,imageSource=imgSrc,axis=self.axis)
        
        (x,y)=imgSrc.get_xy()
        bbox=imgSrc.calc_bbox(x,y)
        self.imgCollection.set_view_home()
        self.imgCollection.load_image_collection()
        
        self.maxvalue=512
        self.currentPosLine2D=Line2D([x],[y],marker='o',markersize=7,markeredgewidth=1.5,markeredgecolor='r',zorder=100)
        self.axis.add_line(self.currentPosLine2D) 
        self.axis.set_title('Mosaic Image')
        self.fig = figure
        self.update_pos_cursor()
        
    # def paintImage(self):
        # """plots self.imagematrix in self.axis using self.extent to define the boundaries"""
        # self.Image=self.axis.imshow(self.imagematrix,cmap='gray',extent=self.extent)
        # (minval,maxval)=self.Image.get_clim()
        # self.maxvalue=maxval
        # #self.axis.canvas.get_toolbar().slider.SetSelection(minval,self.maxvalue)
        # self.axis.autoscale(False)
        # self.axis.set_xlabel('X Position (pixels)')
        # self.axis.set_ylabel('Y Position (pixels)')
        # self.Image.set_clim(0,25000)

    def update_pos_cursor(self):
        x,y = self.imgSrc.get_xy()
        self.currentPosLine2D.set_xdata([x])
        self.currentPosLine2D.set_ydata([y])
        self.axis.draw_artist(self.currentPosLine2D)
        self.fig.canvas.draw()
        #self.cursor_timer = threading.Timer(1, self.update_pos_cursor)
        #self.cursor_timer.start()

    def set_maxval(self,maxvalue):
        """set the maximum value in the image colormap"""
        self.maxvalue=maxvalue;
        self.repaint()
    
    def set_view_home(self):
        self.imgCollection.set_view_home()

    def crop_to_images(self,evt):
        self.imgCollection.crop_to_images(evt)
        
    def repaint(self):
        """sets the new clim for the Image using self.maxvalue as the new maximum value"""
        #(minval,maxval)=self.Image.get_clim()
        self.imgCollection.update_clim(max=self.maxvalue)
        
        if self.oneImage!=None:
            self.oneImage.set_clim(0,self.maxvalue)
        if self.twoImage!=None:
            self.twoImage.set_clim(0,self.maxvalue)
    
    def paintImageCenter(self,cut,theaxis,xc=0,yc=0,skip=1,cmap='gray',scale=1,interpolation='nearest'):
        """paints an image and redefines the coordinates such that 0,0 is at the center
        
        keywords
        cut)the 2d numpy matrix with the image data
        the axis)the matplotlib axis to plot it in
        skip)the factor to rescale the axis by so that 1 entry in the cut, is equal to skip units on the axis (default=1)
        cmap)the colormap designation to use for the plot (default 'gray')
        
        """
        theaxis.cla()
        (h,w)=cut.shape
        dh=skip*1.0*(h-1)/2       
        dw=skip*1.0*(w-1)/2
        dh=dh*scale;
        dw=dw*scale;
        
        left=xc-dw
        right=xc+dw
        top=yc-dh
        bot=yc+dh
            
        ext=[left,right,bot,top]

        image=theaxis.imshow(cut,cmap=cmap,extent=ext,interpolation=interpolation)
        
        theaxis.set_xlim(left=xc-dw,right=xc+dw)
        theaxis.set_ylim(bottom=yc+dh,top=yc-dh)
            
        theaxis.hold(True)

        return image 
    
    def updateImageCenter(self,cut,theimage,theaxis,xc=0,yc=0,skip=1,scale=1):
        """updates an image with a new image
        
        keywords
        cut) the 2d numpy matrix with the image data 
        theimage) the image to update
        theaxis) the axis that the image is in
        skip)the factor to rescale the axis by so that 1 entry in the cut, is equal to skip units on the axis (default=1)

        """
        (h,w)=cut.shape[0:2]
        dh=skip*1.0*(h-1)/2       
        dw=skip*1.0*(w-1)/2
        dh=dh*scale;
        dw=dw*scale;
        theimage.set_array(cut)
      
        left=xc-dw
        right=xc+dw
        theaxis.set_xlim(left=xc-dw,right=xc+dw)

        top=yc-dh
        bot=yc+dh
        theaxis.set_ylim(top=yc-dh,bottom=yc+dh)

        ext=[left,right,bot,top]
        theimage.set_extent(ext)
         
         
    def paintImageOne(self,cut,xy=(0,0),dxy_pix=(0,0),window=0):
        """paints an image in the self.one_axis axis, plotting a box of size 2*window+1 around that point
        
        keywords
        cut) the 2d numpy matrix with the image data
        dxy_pix) the center of the box to be drawn given as an (x,y) tuple
        window)the size of the box, where the height is 2*window+1
        
        """ 
        (xc,yc)=xy  
        (dx,dy)=dxy_pix
        
        pixsize=self.imgCollection.get_pixel_size()
        
        dx=dx*pixsize;
        dy=dy*pixsize;
        #the size of the cutout box in microns
        boxsize_um=(2*window+1)*pixsize;
        
        #if there is no image yet, create one and a box
        if self.oneImage==None:
            self.oneImage=self.paintImageCenter(cut, self.one_axis,xc=xc,yc=yc,scale=pixsize)
            self.oneBox=CenterRectangle((xc+dx,yc+dy),width=50,height=50,edgecolor='r',linewidth=1.5,fill=False)
            self.one_axis.add_patch(self.oneBox)
            self.one_axis_center=Line2D([xc],[yc],marker='+',markersize=7,markeredgewidth=1.5,markeredgecolor='r')
            self.one_axis.add_line(self.one_axis_center) 
            self.one_axis.set_title('Point 1')
            self.one_axis.set_ylabel('Microns')
            self.one_axis.autoscale(False)
            self.oneImage.set_clim(0,self.maxvalue)     
        #if there is an image update it and the self.oneBox
        else:
            self.updateImageCenter(cut, self.oneImage, self.one_axis,xc=xc,yc=yc,scale=pixsize)
            self.oneBox.set_center((dx+xc,dy+yc))
            self.oneBox.set_height(boxsize_um)
            self.oneBox.set_width(boxsize_um)
            self.one_axis_center.set_xdata([xc])
            self.one_axis_center.set_ydata([yc])
    
        
    def paintImageTwo(self,cut,xy=(0,0),xyp=None,pointcolor='r'):
        """paints an image in the self.two_axis, with 0,0 at the center cut=the 2d numpy"""
        #create or update appropriately
        pixsize=self.imgCollection.get_pixel_size()
       
        
        (xc,yc)=xy
        if xyp is not None:
            (xp,yp)=xyp
        else:
            (xp,yp)=xy
            
        if self.twoImage==None:
            self.twoImage=self.paintImageCenter(cut, self.two_axis,xc=xc,yc=yc,scale=pixsize)
            self.two_axis_center=Line2D([xp],[yp],marker='+',markersize=7,markeredgewidth=1.5,markeredgecolor=pointcolor)
            self.two_axis.add_line(self.two_axis_center) 
            self.two_axis.set_title('Point 2')
            self.two_axis.set_ylabel('Pixels from point 2')
            self.two_axis.autoscale(False)
            self.twoImage.set_clim(0,self.maxvalue)
 
        else:
            self.updateImageCenter(cut, self.twoImage, self.two_axis,xc=xc,yc=yc,scale=pixsize)
            self.two_axis_center.set_xdata([xp])
            self.two_axis_center.set_ydata([yp])
    
    def paintCorrImage(self,corrmat,dxy_pix,skip=1):
        """paints an image in the self.corr_axis, with 0,0 at the center and rescaled by skip, plotting a point at dxy_pix
        
        keywords)
        corrmat) the 2d numpy matrix with the image data
        dxy_pix) the offset in pixels from the center of the image to plot the point
        skip) the factor to rescale the axis by, so that when corrmat was produced by mycorrelate2d with a certain skip value, 
        the axis will be in units of pixels
        
        """
        #unpack the values
        (dx,dy)=dxy_pix
        #update or create new
        if self.corrImage==None:
            self.corrImage=self.paintImageCenter(corrmat, self.corr_axis,skip=skip,cmap='jet')             
            self.maxcorrPoint,=self.corr_axis.plot(dx,dy,'ro')

            self.colorbar=self.corr_axis.figure.colorbar(self.corrImage,shrink=.9, ticks = [0.2,0.4,0.6,0.8,1.0])
            self.corrImage.set_clim(vmin = 0.0, vmax = 1.0)
            self.corr_axis.set_title('Cross Correlation')
            self.corr_axis.set_ylabel('Pixels shifted')
          
        else:
            self.updateImageCenter(corrmat, self.corrImage, self.corr_axis,skip=skip)
            self.maxcorrPoint.set_data(dx,dy)   
        #hard code the correlation maximum at .5
        #self.corrImage.set_clim(0,.5)
    
    def cutout_window(self,x,y,window):
        """returns a cutout of the original image at a certain location and size
        
        keywords)
        x)x position in microns
        y)y position in microns
        window) size of the patch to cutout (microns), will cutout +/- window in both vertical and horizontal dimensions
        note.. behavior not well specified at edges, may crash
        
        function uses PIL to read in image and crop it appropriately
        returns) cut: a 2d numpy matrix containing the removed patch
        
        """
        box=Rectangle(x-window,x+window,y-window,y+window)
        return self.imgCollection.get_cutout(box)
        
    def cross_correlate_two_to_one(self,xy1,xy2,window=60,delta=40,skip=3):
        """take two points in the image, and calculate the 2d cross correlation function of the image around those two points
        
        keywords)
        xy1) a (x,y) tuple specifying point 1, the point that should be fixed
        xy2) a (x,y) tuple specifiying point 2, the point that should be moved
        window) the size of the patch to cutout (+/- window around the points) for calculating the correlation (default = 100 um)
        delta) the size of the maximal shift +/- delta from no shift to calculate
        skip) the number of integer pixels to skip over when calculating the correlation
        
        returns (one_cut,two_cut,corrmat)
        one_cut) the patch cutout around point 1
        two_cut) the patch cutout around point 2
        corrmat) the matrix of correlation values measured with 0,0 being a shift of -delta,-delta
        
        """
        (x1,y1)=xy1
        (x2,y2)=xy2
        one_cut=self.cutout_window(x1,y1,window+delta)
        two_cut=self.cutout_window(x2,y2,window)
        #return (target_cut,source_cut,mycorrelate2d(target_cut,source_cut,mode='valid'))
        return (one_cut,two_cut,mycorrelate2d(one_cut,two_cut,skip))

    def _cross_correlation_shift(self, fixed_cutout, to_shift_cutout):
        '''
        :param one_cut: cutout around point 1
        :param two_cut: cutout around point 2
        :return: corrmatt, corval, dx_pix, dy_pix
        '''
        src_image = np.array(fixed_cutout, dtype=np.complex128, copy=False)
        target_image = np.array(to_shift_cutout, dtype=np.complex128, copy=False)
        f1 = np.std(fixed_cutout)
        f2 = np.std(to_shift_cutout)
        normfactor = f1*f2*fixed_cutout.size
        src_freq = np.fft.fftn(src_image)
        target_freq = np.fft.fftn(target_image)
        shape = src_freq.shape
        image_product = src_freq * target_freq.conj()
        corrmat = np.fft.ifftn(image_product)
        corrmat = np.fft.fftshift(corrmat.real/normfactor)
        #find the peak of the matrix
        maxind=corrmat.argmax()
        (h,w)=corrmat.shape
        #determine the indices of that peak
        (max_i,max_j)=np.unravel_index(maxind,corrmat.shape)

        #calculate the shift for that index in pixels
        dy_pix=int((max_i-(h/2)))
        dx_pix=int((max_j-(w/2)))

        #calculate what the maximal correlation was
        corrval=corrmat.max()

        return corrmat, corrval, dx_pix, dy_pix

    def _get_faster_pixel_dimension(self,current_dimension):
        '''
        Uses a list of pre-calculated dimensions to cut the image size down
        to one that is faster for np.fft.fftn(). Dimensions are all integers of the form
        k*2^n for small k.
        :param current_dimension:
        :return: new dimension
        '''
        better_dimensions = [80,   84,   88,   92,   96,  104,  110,  112,  120,  128,  130,
        132,  136,  140,  152,  156,  160,  168,  176,  184,  192,  208,
        220,  224,  240,  256,  260,  264,  272,  280,  304,  312,  320,
        336,  352,  368,  384,  416,  440,  448,  480,  512,  520,  528,
        544,  560,  608,  624,  640,  672,  704,  736,  768,  832,  880,
        896,  960, 1024, 1040, 1056, 1088, 1120, 1216, 1248, 1280, 1344,
        1408, 1472, 1536, 1664, 1760, 1792, 1920, 2048]

        pos = bisect_right(better_dimensions, current_dimension)-1
        print 'pos',pos
        return better_dimensions[pos]

    def get_central_region(self,cutout,dim):
        '''

        :param cutout: a 2d numpy array, could be non square
        :param dim: an integer dimensional
        :return: cutout_central, the central dim x dim region of cutout
        '''
        cut_height = cutout.shape[0]-dim
        cut_width = cutout.shape[1]-dim
        top_pix = np.int(np.floor(cut_height/2.0))
        left_pix = np.int(np.floor(cut_width/2.0))
        cutout_central = cutout[top_pix:top_pix+dim,left_pix:left_pix+dim]
        return  cutout_central

    def fix_cutout_size(self,cutout1,cutout2):
        '''

        :param cutout1,2: two 2d numpy array representing a windowed cutouts around a point of interest,
        should be in the range of 100-2048 pixels in height/width
        :return: cutout1_fix,cutout2_fix: the a 2d numpy arrays that are square, and have been cropped to be of a size
        that will be relatively fast to calculate a 2d FFT of.
        '''
        min_dim = min(cutout1.shape[0],cutout1.shape[1],cutout2.shape[0],cutout2.shape[1])
        new_dim = self._get_faster_pixel_dimension(min_dim)

        cutout1_fix = self.get_central_region(cutout1,new_dim)
        cutout2_fix = self.get_central_region(cutout2,new_dim)

        return (cutout1_fix,cutout2_fix)

    def align_by_correlation(self,xy1,xy2,CorrSettings = CorrSettings()):
        """take two points in the image, and calculate the 2d cross correlation function of the image around those two points
        plots the results in the appropriate axis, and returns the shift which aligns the two points given in microns
        
        keywords)
        xy1) a (x,y) tuple specifying point 1, the point that should be fixed
        xy2) a (x,y) tuple specifiying point 2, the point that should be moved
        window) the size of the patch to cutout (+/- window around the points) for calculating the correlation (default = 100 pixels)
        delta) the size of the maximal shift +/- delta from no shift to calculate
        skip) the number of integer pixels to skip over when calculating the correlation
        
        returns) (maxC,dxy_um)
        maxC)the maximal correlation measured
        dxy_um) the (x,y) tuple which contains the shift in microns necessary to align point xy2 with point xy1
        
        """
        start_time = time.time()

        window = CorrSettings.window
        delta = CorrSettings.delta
        skip = CorrSettings.skip

        pixsize=self.imgCollection.get_pixel_size()
        #calculate the cutout patches and the correlation matrix
        #(one_cut,two_cut,corrmat)=self.cross_correlate_two_to_one(xy1,xy2,window,delta,skip)
        (x1,y1)=xy1
        (x2,y2)=xy2
        one_cut=self.cutout_window(x1,y1,window)
        two_cut=self.cutout_window(x2,y2,window)


        print("---cutout a . %s seconds  ---" % (time.time() - start_time))
        print 'one_shape,two_shape ',one_cut.shape,two_cut.shape
        one_cut,two_cut = self.fix_cutout_size(one_cut,two_cut)

        one_cut = one_cut - np.mean(one_cut)
        two_cut = two_cut - np.mean(two_cut)
        print 'new dimensions ',one_cut.shape,two_cut.shape
        print("---cutout ended. %s seconds  ---" % (time.time() - start_time))

        corrmat, corrval, dx_pix, dy_pix = self._cross_correlation_shift(one_cut,two_cut)

        #convert dy_pix and dx_pix into microns
        dy_um=dy_pix*pixsize
        dx_um=dx_pix*pixsize
        #pack up the shifts into tuples
        dxy_pix=(dx_pix,dy_pix)
        dxy_um=(dx_um,dy_um)

        print("---correlation ended. %s seconds  ---" % (time.time() - start_time))
        print "(correlation,(dx,dy))=  ",
        print (corrval,dxy_pix)

        #paint the patch around the first point in its axis, with a box of size of the two_cut centered around where we found it
        self.paintImageOne(one_cut,xy=xy1,dxy_pix=dxy_pix)
        #paint the patch around the second point in its axis
        self.paintImageTwo(two_cut,xy=xy2,xyp=(xy2[0]-dx_um,xy2[1]-dy_um))
        #paint the correlation matrix in its axis
        self.paintCorrImage(corrmat, dxy_pix)

        print("---painting ended %s seconds ---" % (time.time() - start_time))
        return (corrval,dxy_um)
        
    def explore_match(self,img1, kp1,img2,kp2, status = None, H = None):
        h1, w1 = img1.shape[:2]
        h2, w2 = img2.shape[:2]
        vis = np.zeros((max(h1, h2), w1+w2), np.uint8)
        vis[:h1, :w1] = img1
        vis[:h2, w1:w1+w2] = img2
        vis = cv2.cvtColor(vis, cv2.COLOR_GRAY2BGR)

        if H is not None:
            corners = np.float32([[0, 0], [w1, 0], [w1, h1], [0, h1]])
            corners = np.int32( cv2.perspectiveTransform(corners.reshape(1, -1, 2), H).reshape(-1, 2) + (w1, 0) )
            cv2.polylines(vis, [corners], True, (255, 255, 255))

        if status is None:
            status = np.ones(len(kp1), np.bool_)
        p1 = np.int32([kpp.pt for kpp in kp1])
        p2 = np.int32([kpp.pt for kpp in kp2]) + (w1, 0)

        green = (0, 255, 0)
        red = (0, 0, 255)
        white = (255, 255, 255)
        kp_color = (51, 103, 236)
        for (x1, y1), (x2, y2), inlier in zip(p1, p2, status):
            if inlier:
                col = green
                cv2.circle(vis, (x1, y1), 2, col, -1)
                cv2.circle(vis, (x2, y2), 2, col, -1)
            else:
                col = red
                r = 2
                thickness = 3
                cv2.line(vis, (x1-r, y1-r), (x1+r, y1+r), col, thickness)
                cv2.line(vis, (x1-r, y1+r), (x1+r, y1-r), col, thickness)
                cv2.line(vis, (x2-r, y2-r), (x2+r, y2+r), col, thickness)
                cv2.line(vis, (x2-r, y2+r), (x2+r, y2-r), col, thickness)
        vis0 = vis.copy()
        for (x1, y1), (x2, y2), inlier in zip(p1, p2, status):
            if inlier:
                cv2.line(vis, (x1, y1), (x2, y2), green)
            else:
                cv2.line(vis, (x1, y1), (x2, y2), red)
        return vis
        
            
    def align_by_sift(self,xy1,xy2,window=70,SiftSettings=SiftSettings()):
        """take two points in the image, and calculate SIFT features image around those two points
        cutting out size window

        keywords)
        xy1) a (x,y) tuple specifying point 1, the point that should be fixed
        xy2) a (x,y) tuple specifiying point 2, the point that should be moved
        window) the size of the patch to cutout (+/- window around the points) for calculating the correlation (default = 70 um)


        returns) (maxC,dxy_um)
        maxC)the maximal correlation measured
        dxy_um) the (x,y) tuple which contains the shift in microns necessary to align point xy2 with point xy1

        """
        print "starting align by sift"
        pixsize=self.imgCollection.get_pixel_size()
        #cutout the images around the two points
        (x1,y1)=xy1
        (x2,y2)=xy2
        one_cut=self.cutout_window(x1,y1,window)
        two_cut=self.cutout_window(x2,y2,window)


        #one_cuta=np.minimum(one_cut*256.0/self.maxvalue,255.0).astype(np.uint8)
        #two_cuta=np.minimum(two_cut*256.0/self.maxvalue,255.0).astype(np.uint8)
        one_cuta = np.copy(one_cut)
        two_cuta = np.copy(two_cut)
        
        one_cuta=cv2.equalizeHist(one_cuta)
        two_cuta=cv2.equalizeHist(two_cuta)
        
        
        sift = cv2.SIFT(nfeatures=SiftSettings.numFeatures,contrastThreshold=SiftSettings.contrastThreshold)
        kp1, des1 = sift.detectAndCompute(one_cuta,None)
        kp2, des2 = sift.detectAndCompute(two_cuta,None)
        print "features1:%d"%len(kp1)
        print "features2:%d"%len(kp2)
        

        
        #img_one = cv2.drawKeypoints(one_cut,kp1)
        #img_two = cv2.drawKeypoints(two_cut,kp2)
        
  
        #image2=self.two_axis.imshow(img_two)
        
        # FLANN parameters
        FLANN_INDEX_KDTREE = 0
        index_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 5)
        search_params = dict(checks=50)   # or pass empty dictionary

        flann = cv2.FlannBasedMatcher(index_params,search_params)

        matches = flann.knnMatch(des1,des2,k=2)

        # Need to draw only good matches, so create a mask
        matchesMask = np.zeros(len(matches))
        
        kp1matchIdx=[]
        kp2matchIdx=[]
        # ratio test as per Lowe's paper
        for i,(m,n) in enumerate(matches):
            if m.distance < 0.9*n.distance:
                kp1matchIdx.append(m.queryIdx)
                kp2matchIdx.append(m.trainIdx)
               

      
        p1 = np.array([kp1[i].pt for i in kp1matchIdx])
        p2 = np.array([kp2[i].pt for i in kp2matchIdx]) 
       # p1c = [pt-np.array[window,window] for pt in p1]
       # p2c = [pt-np.array[window,window] for pt in p2]
        kp1m = [kp1[i] for i in kp1matchIdx]
        kp2m = [kp2[i] for i in kp2matchIdx]
        #print "kp1matchshape"
        #print matchesMask
        #print len(kp1match)
        #print len(kp2match)
        
        #draw_params = dict(matchColor = (0,255,0),
        #                   singlePointColor = (255,0,0),
        #                   matchesMask = matchesMask,
        #                   flags = 0)

        #img3 = cv2.drawMatches(one_cut,kp1,two_cut,kp2,matches,None,**draw_params)
        
        
        transModel=ransac.RigidModel()
        bestModel,bestInlierIdx=ransac.ransac(p1,p2,transModel,2,300,20.0,3,debug=True,return_all=True)
        
        if bestModel is not None:
            
            the_center = np.array([[one_cut.shape[0]/2,one_cut.shape[1]/2]])
            trans_center=transModel.transform_points(the_center,bestModel)
            offset=the_center-trans_center
            xc=x2+offset[0,0]*pixsize
            yc=y2-offset[0,1]*pixsize
          
            #newcenter=Line2D([trans_center[0,0]+one_cut.shape[1]],[trans_center[0,1]],marker='+',markersize=7,markeredgewidth=1.5,markeredgecolor='r')
            #oldcenter=Line2D([the_center[0,0]],[the_center[0,1]],marker='+',markersize=7,markeredgewidth=1.5,markeredgecolor='r')
            
            
            dx_um=-bestModel.t[0]*pixsize
            dy_um=-bestModel.t[1]*pixsize
           
                
      
            print "matches:%d"%len(kp1matchIdx)
            print "inliers:%d"%len(bestInlierIdx)
            print ('translation',bestModel.t)
            print ('rotation',bestModel.R)
            
            mask = np.zeros(len(p1), np.bool_)
            mask[bestInlierIdx]=1
            
                 
            #img3 = self.explore_match(one_cuta,kp1m,two_cuta,kp2m,mask)
            #self.corr_axis.cla()
            #self.corr_axis.imshow(img3)
            #self.corr_axis.add_line(newcenter)
            #self.corr_axis.add_line(oldcenter)
            #self.repaint()

         
            #self.paintImageOne(img_one,xy=xy1)
            #paint the patch around the second point in its axis
            #self.paintImageTwo(img_two,xy=xy2)
            #paint the correlation matrix in its axis
            #self.paintCorrImage(corrmat, dxy_pix,skip)
            
          
          
            print (dx_um,dy_um)

            
            self.paintImageOne(one_cut,xy=xy1)
            self.paintImageTwo(two_cut,xy=xy2,xyp=(x2-dx_um,y2-dy_um))
            
            return ((dx_um,dy_um),len(bestInlierIdx))
        else:
            print "no model found"
            self.paintImageOne(one_cut,xy=xy1)
            self.paintImageTwo(two_cut,xy=xy2)
            
            return ((0.0,0.0),0)
        
    def paintPointsOneTwo(self,xy1,xy2,window=None):
        (x1,y1)=xy1
        (x2,y2)=xy2
        print "getting p1 window at ",x1,y1
        print "getting p2 window at ",x2,y2
        fw,fh=self.imgCollection.get_image_size_um()
        if window is None:
            min_dim = min(fw,fh)
            window = min_dim*.8/2

        one_cut=self.cutout_window(x1,y1,window)
        two_cut=self.cutout_window(x2,y2,window)
        self.paintImageOne(one_cut,xy1)
        #paint the patch around the second point in its axis
        self.paintImageTwo(two_cut,xy2)
        
    def make_preview_stack(self,xpos,ypos,width,height,directory):
        print "make a preview stack"
   
        hw_pix=int(round(width*.5/self.orig_um_per_pix))
        hh_pix=int(round(height*.5/self.orig_um_per_pix))
        queue = Queue.Queue()
          
        #spawn a pool of threads, and pass them queue instance 
        for i in range(4):
            t = ImageCutThread(queue)
            t.setDaemon(True)
            t.start()
              
        for i in range(len(self.mosaicArray.xpos)):
            (cx_pix,cy_pix)=self.convert_pos_to_ind(xpos[i],ypos[i])
            rect=[cx_pix-hw_pix,cy_pix-hh_pix,cx_pix+hw_pix,cy_pix+hh_pix]
            queue.put((self.imagefile,rect,i))
        queue.join()