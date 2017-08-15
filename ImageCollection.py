import numpy as np
import matplotlib.pyplot as plt
import os
from PIL import Image
from tifffile import imsave
import time
import json
from Rectangle import Rectangle
import traceback,sys
#from imageSourceMM import imageSource

        
class MyImage():
    def __init__(self,imagePath=None,boundBox=None):
        
        self.boundBox = boundBox #should be a class Rectangle
        self.imagePath = imagePath
        
        
    def save_metadata(self,filename):
         d = {"boundBox":{"top":self.boundBox.top,"bottom":self.boundBox.bottom,
                          "left":self.boundBox.left,"right":self.boundBox.right},
              "imagePath":{"path":self.imagePath,"format":".tif"}
             }
                 
         meta = json.dumps(d)
         metafile = open(filename,'w')
         metafile.write(meta)
         metafile.close()
         
         
    def load_from_metadata(self,filename):
        #loads this image from a metadata file
        file = open(filename,'r')
        data = file.read()
        file.close()
        
        data = data.replace("false","False")
        data = data.replace("true","True")
        data = data.replace("null","0")
        f = eval(str(data))
        top=f["boundBox"]["top"]
        bottom=f["boundBox"]["bottom"]
        left=f["boundBox"]["left"]
        right=f["boundBox"]["right"]
        
        cx=(left+right)/2;
        cy=(top+bottom)/2;
        
        self.imagePath=f["imagePath"]["path"]
        self.format=f["imagePath"]["format"]
        self.boundBox=Rectangle(left,right,top,bottom)

        
    def set_boundBox(self,left,right,top,bottom):
        self.boundBox=Rectangle(left,right,top,bottom)


    def get_cutout(self,box):
        '''
        Expected that the int() will occasionally produce rounding error -
        making cutout size unstable.
        '''

        if self.boundBox.contains_rect(box):
            #load image from file
            #todo
            img=Image.open(self.imagePath,mode='r')
            (width,height)=img.size

            
            rel_box=self.boundBox.find_relative_bounds(box)
            
            left=int(rel_box.left*width)
            right=int(rel_box.right*width)
            top=int(rel_box.top*height)
            bottom=int(rel_box.bottom*height)
             
            c_img=img.crop([left,top,right,bottom])
            thedata=c_img.getdata()

            (cutwidth,cutheight)=c_img.size
            cut=np.reshape(np.array(thedata,np.dtype('uint8')),(cutheight,cutwidth))
           
            
            return cut
        else:
            Raise_Error("cutout not in image")
            
    def get_ext(self):
        return ".tif"
    
    def file_has_metadata(self,path):
        (base,theext)=os.path.splitext(path)
        print "need a better way to tell if this is a metadata file"
        return 'txt' in theext
                
    def save_data(self,data):
        #img = Image.fromarray(data)
        #img.save(self.imagePath)
        imsave(self.imagePath,data)

        
    def contains_rect(self,box):
        return self.boundBox.contains_rect(box)
    def contains_point(self,x,y):
        return self.boundBox.contains_point(x,y)
        
    def get_data(self):
        img=Image.open(self.imagePath,mode='r')
        thedata=img.getdata()
        
        (width,height)=img.size
        data=np.reshape(np.array(thedata,np.dtype('uint8')),(height,width))
        return data
    
class ImageCollection():
    
    def __init__(self,rootpath,imageClass=MyImage,imageSource=None,axis=None,working_area = Rectangle(left=-30000,right=36000,top=-6100,bottom=16000)):
        
        self.rootpath=rootpath #rootpath to save images
        self.imageClass=imageClass #the class of image that this image collection should be composed of,
                                # must conform to myImage interface
        self.imageSource = imageSource #a source for new data usually a microscope, could be a virtual file
        #needs to implement numpy2darray=imageSource.take_image(x,y)
        self.images = [] #list of image objects
        self.imgCount=0 #counter of number of images in collection
        self.axis=axis #matplotlib.axis to plot images
        self.bigBox = None #bounding box to include all images
        self.matplot_images=[]
        self.minvalue=0
        self.maxvalue=512
        self.working_area = working_area

    def display8bit(self,image, display_min, display_max): 
        image = np.array(image, copy=True)
        image.clip(display_min, display_max, out=image)
        image -= display_min
        image = image / ((display_max - display_min + 1) / 256.)
        return image.astype(np.uint8)

    def lut_convert16as8bit(self,image, display_min, display_max) :
        lut = np.arange(2**16, dtype='uint16')
        lut = self.display8bit(lut, display_min, display_max)
        return np.take(lut, image)


    
    def get_pixel_size(self):
        return self.imageSource.get_pixel_size()
    
    def get_image_size_um(self):
        (fw,fh)=self.imageSource.get_frame_size_um()
        return (fw,fh)
        
    def set_view_home(self,box=None):
        if box==None:
            self.axis.set_xlim(left=self.working_area.left,right=self.working_area.right)
            self.axis.set_ylim(bottom=self.working_area.bottom,top=self.working_area.top)
        else:
            self.axis.set_xlim(left=box.left,right=box.right)
            self.axis.set_ylim(bottom=box.bottom,top=box.top)

    def crop_to_images(self,evt):
        if not self.images:
            self.axis.set_xlim(left=self.working_area.left,right=self.working_area.right)
            self.axis.set_ylim(bottom=self.working_area.bottom,top=self.working_area.top)
        else:

            self.boundary = self.get_image_size_um()[0]
            self.axis.set_xlim(left=self.bigBox.left-self.boundary,right=self.bigBox.right+self.boundary)
            self.axis.set_ylim(bottom=self.bigBox.bottom+self.boundary,top=self.bigBox.top-self.boundary)

            #self.axis.set_xlim(left=self.bigBox.left,right=self.bigBox.right)
            #self.axis.set_ylim(bottom=self.bigBox.bottom,top=self.bigBox.top)

    def get_cutout(self,box):
        #from the collection of images return the pixels contained by the Rectangle box
        #look for an image which contains the desired cutout
        for image in self.images:
            if image.contains_rect(box):
                return image.get_cutout(box)

        #TODO
        #if you don't find the cutout in one image, see if you can get it from two
        
        #TODO
        #can you assemble the cutout from all overlapping images (probably harder than its worth)
        
        #if you can't get it from two, go get a new image from source
        if self.imageSource is not None:
            return self.get_cutout_from_source(box)
            
        return None #we give up as we can't find the cutout for them.. sad
    
    
    
    def add_covered_point(self,x,y):
    
        for image in self.images:
            if image.contains_point(x,y):
                return True
        
        self.add_image_at(x,y)
        return False

    def oh_snap(self):
        (x, y) = self.imageSource.get_xy()
        self.add_image_at(x,y)
        
    def add_image_at(self,x,y):
        #go get an image at x,y
        try:
            (thedata,bbox)=self.imageSource.take_image(x,y)
            if thedata.dtype == np.uint16:
                print "converting"
                #maxval=self.imageSource.get_max_pixel_value()
                thedata=self.lut_convert16as8bit(thedata,0,60000)
            
        except:
            #todo handle this better
            print "ahh no! imageSource failed us"
            traceback.print_exc(file=sys.stdout)
        print "hmm.. bbox is"
        bbox.printRect()
        print "x,y is",x,y
        
        #add this image to the collection
        theimage=self.add_image(thedata,bbox)
        return theimage

    def add_image_to_path(self,x,y,path):
        try:
            (data,bbox) = self.imageSource.take_image(x,y)
            # if data.dtype == np.uint16:
            #     maxval = self.imageSource.get_max_pixel_value()
            #     data = self.lut_convert16as8bit(data,0,60000)
            imsave(path, data)
            return data
        except Exception as e:
            print("Failed to add image to path: {}".format(e))

        
        
    def get_cutout_from_source(self,box):
        print "getting cutout from source"
        if self.imageSource is not None:
            
            #figure out the x,y of the center of the bounding box
            (x,y)=box.get_center()
           
            theimage=self.add_image_at(x,y)
          
            if theimage.contains_rect(box):
                return theimage.get_cutout(box)
            else:
                #todo.. should raise error here... source didn't return 
                print "the source didn't contain the desired cutout"
                print box.printRect()
                
                return None
        else:
            print "there is no image source!"
            return None
        
    def add_image(self,thedata,bbox):
        
        #determine the file path of this image
        thefile=os.path.join(self.rootpath,"%010d"%self.imgCount + ".tif")
        themetafile=os.path.join(self.rootpath,"%010d"%self.imgCount + "_metadata.txt")
        print "imgCount:%d"%self.imgCount
        self.imgCount+=1
        
        #initialize the new image and save the data
        theimage=self.imageClass(thefile,bbox)
        theimage.save_data(thedata)
        theimage.save_metadata(themetafile)
        
        #append this image to the list of images
        self.images.append(theimage)
        
        #update the display
        self.add_image_to_display(thedata,bbox)
        return theimage
        
    
    def update_clim(self,max=512,min=0):
        self.maxvalue=max
        self.minvalue=min
        
        for theimg in self.matplot_images:
            theimg.set_clim(min,max)
            
    def add_image_to_display(self,data,bbox):
        #make the bounding box of the entire image collection include this bounding box
        
        #if there is no big box, make one!
        if self.bigBox is None:
            self.bigBox = Rectangle(0,0,0,0)
            bbox.copyTo(self.bigBox)
        #otherwise make what we have bigger if necessary
        else:
            self.bigBox.expand_to_include(bbox) #use our handy rectangle method to do this
        self.axis.hold(True) #matplotlib axis
        #plot the image
        theimg=self.axis.imshow(data,cmap='gray',extent=[bbox.left,bbox.right,bbox.bottom,bbox.top])
        self.matplot_images.append(theimg)
        #make sure all the other images stay in the field of view
        #self.set_view_home()
        theimg.set_clim(0,self.maxvalue)
        
        self.axis.set_xlabel('X Position (um)')
        self.axis.set_ylabel('Y Position (um)')
            
    def save_image_collection(self):
        #do all the saving
        #todo
        self.save_all_the_things()
    
    def print_bounding_boxes(self):
        print "printing bounding boxes"
        for image in self.images:
            image.boundBox.printRect()
            
    def load_image_collection(self):
        #list all metadata files in rootdir
        testimage=self.imageClass()
        if not os.path.isdir(self.rootpath):
            os.makedirs(self.rootpath)
        
        metafiles=[os.path.join(self.rootpath,f) for f in os.listdir(self.rootpath) if f.endswith('.txt') ]
        
        print "loading metadata"
        #loop over files reading in metadata, and initializing Image objects, reading images to update display
        for file in metafiles:
            print file
            theimage=self.imageClass()
            theimage.load_from_metadata(file)
            self.images.append(theimage)
            data=theimage.get_data()
            self.add_image_to_display(data,theimage.boundBox)
            self.imgCount+=1
     
            
        
        del(testimage)
      
# filename="C:\Users\Smithlab\Documents\ASI_LUM_RETIGA_CRISP.cfg"
# imgsrc=imageSource(filename)
# channels=imgsrc.get_channels()
# imgsrc.set_channel('Violet')
# imgsrc.set_exposure(250)

# plt.axis()
# rootPath='C:\\Users\\Smithlab\\Documents\\ImageCollectTest\\'
# figure = plt.figure(1,figsize=(5,14))
# axes = figure.get_axes()

# ic=ImageCollection(rootpath=rootPath,imageSource=imgsrc,axis=axes[0])
# ic.load_image_collection()
# box=Rectangle(-50,50,-50,50)
# data2=ic.get_cutout(box)

# box=Rectangle(-140,-90,0,50)
# data2=ic.get_cutout(box)

# box=Rectangle(-340,-240,0,50)
# data2=ic.get_cutout(box)

# box=Rectangle(-740,-740,0,50)
# data2=ic.get_cutout(box)

# plt.show()

        