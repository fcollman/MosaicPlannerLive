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
 
from Settings import MosaicSettings, CameraSettings, SmartSEMSettings,MosaicSettingsSchema, CameraSettingsSchema
import numpy as np
from numpy import sin, pi, cos, arctan, sin, tan, sqrt
import csv
from Point import Point
import matplotlib.patches
import matplotlib.transforms
from matplotlib import path
from matplotlib.lines import Line2D
from matplotlib.quiver import Quiver
#from matplotlib.nxutils import points_inside_poly
from CenterRectangle import CenterRectangle
import os
from scipy.interpolate import griddata
import lxml.etree as ET
import json
import marshmallow as mm

class NumberDisplaySettingsSchema(mm.Schema):
    shownumbers = mm.fields.Bool(required=True)
    color = mm.fields.Str(required=True)
    horizontalAlignment = mm.fields.Str(required=True)
    verticalAlignment = mm.fields.Str(required=True)
    
class NumberDisplaySettings(object):
    def __init__(self,shownumbers=False,color='darkorange',horizontalAlignment='right',verticalAlignment='top'):
        self.shownumbers = shownumbers
        self.color=color
        self.horizontalAlignment = horizontalAlignment
        self.verticalAlignment = verticalAlignment

class slicePositionSchema(mm.Schema):
    x = mm.fields.Float(required=True)
    y = mm.fields.Float(required=True)
    angle = mm.fields.Float(required=True)
    showAngle = mm.fields.Bool(required=False,default=True)
    selected = mm.fields.Bool(required=False,default=False)
    activated = mm.fields.Bool(required=False,default=True)
    withpoint = mm.fields.Bool(required=False,default=True)
    number = mm.fields.Int(required=True)
    numberDisplaySettings = mm.fields.Nested(NumberDisplaySettingsSchema)
    frameList = mm.fields.Nested('posListSchema')

class posListSchema(mm.Schema):
    mosaic_settings = mm.fields.Nested(MosaicSettingsSchema,required=True)
    camera_settings = mm.fields.Nested(CameraSettingsSchema,required=True)
    slicePositions = mm.fields.Nested(slicePositionSchema,many=True)
    dosort = mm.fields.Bool(required=False,default=True)
    numberDisplaySettings = mm.fields.Nested(NumberDisplaySettingsSchema)

class posList():
    """class for holding, altering, and plotting the position list"""
    def __init__(self,axis,mosaic_settings=MosaicSettings(),camera_settings=CameraSettings(),
                 numberDisplaySettings=NumberDisplaySettings(),dosort=True):
        """initialization function
        
        keywords)
        axis:matplotlib axis to plot the position list in
        mosaic_settings:MosaicSettings for initialization purposes, defaults to default for class
        camera_settings:CameraSettins for initialization purposes, defaults to default for class
        
        """
        self.mosaic_settings=mosaic_settings
        self.camera_settings=camera_settings     
        self.slicePositions=[]
        self.axis=axis
        #start with point1 and 2 not defined
        self.pos1=None
        self.pos2=None
        self.dosort=dosort
        self.numberDisplaySettings=numberDisplaySettings
   

    def get_next_pos(self,pos):
        self.__sort_points()
        myindex=self.slicePositions.index(pos)
        if (myindex)==len(self.slicePositions)-1:
            return None     
        return self.slicePositions[myindex+1]
        
    def get_prev_pos(self,pos):
        #self.__sort_points()
        myindex=self.slicePositions.index(pos)
        if (myindex)==0:
            return None 
        return self.slicePositions[myindex-1]
        
    def set_pos1_near(self,x,y):
        """sets point1 to be the position nearest an x,y point
        
        keywords)
        x:x position in microns to select nearest
        y:y position in microns to select nearest
        
        """
        #slicePosition nearest x,y
        near_pos=self.get_position_nearest(x, y)
        
        self.set_pos1(near_pos)
                       
    def set_pos2_near(self,x,y):
        """sets point2 to be the position nearest an x,y point
        
        keywords)
        x:x position in microns to select nearest
        y:y position in microns to select nearest
        
        
        """
        #slicePosition nearest x,y
        near_pos=self.get_position_nearest(x, y)
        self.set_pos2(near_pos)
        
    def set_pos1(self,newpos):
        """makes a position be position 1 if possible"""
        #if the position has a label already do nothing
        if newpos.label == None:
            #if pos1 is defined, remove it
            if self.pos1 != None:
                self.pos1.removeLabel()
            newpos.addLabel(" 1")
            self.pos1=newpos
            
    def set_pos2(self,newpos):
        """makes a position be position 2 if possible"""
        #if the position has a label already do nothing
        if newpos.label == None:
            if self.pos2 != None:
                self.pos2.removeLabel()
            newpos.addLabel(" 2")
            self.pos2=newpos
            
    def new_position_after_step(self):
        """add a new position to the list, by calculate the vector between pos1 and pos2, and adding that vector to pos2
        if pos1 and pos2 are not defined, return None, otherwise return the newly added slicePosition
        also redefines pos1 to be pos2 and pos2 to be the new point"""
        if (self.pos1 == None or self.pos2==None):
            return None
        else:
            dx=self.pos2.x-self.pos1.x
            dy=self.pos2.y-self.pos1.y
            #add the new position using the add_position function
            newpos=self.add_position(self.pos2.x+dx,self.pos2.y+dy)
            #redefine pos1 and pos2 such that the new point is pos2 and the old pos2 is pos1
            oldpos2=self.pos2
            self.set_pos2(newpos)
            self.set_pos1(oldpos2)
            return newpos
      
    def set_select_all(self,selected):
        """set the selected attribute in all the slicePositions to be equal to selected
        and updates the appropriate drawn attributes accordingly via set_selected
        keywords:
        selected)boolean as to whether the selected should be selected or unselected
        
        """
        for pos in self.slicePositions:
            pos.set_selected(selected)
                
    def set_mosaic_settings(self,mosaic_settings):
        """sets the mosaic settings, and updates all the necessary properties of the slice positions using their update_mosaic_settings() function
        
        keywords:
        mosaic_settings)the MosaicSettings class to make be the current mosaic settings"""
        self.mosaic_settings=mosaic_settings
        for pos in self.slicePositions:
            pos.update_mosaic_settings()
            
    def set_camera_settings(self,camera_settings):
        """sets the camera_settings attribute, and updates all the necessary properties of the slice positions using their update_mosaic_settings() function
        
        keywords:
        camera_settings)the CameraSettings class to make be the current camera_settings"""
        self.camera_settings=camera_settings
        for pos in self.slicePositions:
            pos.update_mosaic_settings()
        
    def set_mosaic_visible(self,visible):
        """sets visibility of the mosaic boxes on each of the slicePositions to be equal to visible
        
        keywords:
        visible)Boolean describing whether the rectangular boxes should be visible or not
        
        """
        self.mosaic_settings.show_box=visible
        for pos in self.slicePositions:
            pos.set_box_visible(visible)
     
    def set_frames_visible(self,visible):
        """sets visibility of the frames boxes on each of the slicePositions to be equal to visible
        
        keywords:
        visible)Boolean describing whether the frame boxes should be visible or not
        
        """
        self.mosaic_settings.show_frames=visible
        for pos in self.slicePositions:
            #if no frames exist, and we are trying to make them visible, create them
            if pos.frameList==None and visible:
                pos.paintFrames()
            #if the frames already exist, use the set_mosaic_visible function to make them visible/invisible
            #as frameList is a posList class.. low and behold fancy recursive META logic
            if not pos.frameList==None:
                pos.frameList.set_mosaic_visible(visible)

    
    def select_points_inside(self,verts): 
        """select all the points inside the vertices created by the Lasso widget callback function
        recursively calls the select_if_inside function of all slicePositions in the list"""
        for pos in self.slicePositions:
            pos.select_if_inside(verts)
     
    def select_all(self):
        for pos in self.slicePositions:
            pos.set_selected(True)
            
    def shift_selected(self,dx,dy):
        """shift all the points which are selected by dx,dy
        
        keywords:
        dx,dy) the shift in microns to move each point
        
        """
        for pos in self.slicePositions:
            if pos.selected:
                pos.shiftPosition(dx,dy)
                
    def shift_all(self,dx,dy):
        """shift all the slicePositions in the position list by dx,dy
        
        keywords:
        dx,dy) the shift in microns to move each point
        
        """
        for pos in self.slicePositions:
            pos.shiftPosition(dx,dy)
    
    def unrotate_boxes(self):
        """set the angle attribute on each slicePosition to be 0 and update the drawing properties appropriately"""
        for pos in self.slicePositions:
            pos.setAngle(0)

        
    def rotate_boxes(self):
        """calculate the tangent angle of the ribbon at each point using the calcAngles function and then set the angle
        attribute of each slice position using setAngle"""
        
        theta=self.calcAngles()
        for index, pos in enumerate(self.slicePositions):
            pos.setAngle(theta[index])

    def rotate_boxes_angle(self):
        """use angle from loaded JSON position list and then set the angle
        attribute of each slice position using setAngle"""

        for index, pos in enumerate(self.slicePositions):
            pos.setAngle(pos.angle)

    def rotate_selected(self,dtheta):
        """

        Args:
            dtheta: angle in radians to rotate all selected positions

        Returns:None

        """
        for index, pos in enumerate(self.slicePositions):
            if pos.selected:
                pos.rotateAngle(dtheta)

    def shift_selected_curve(self,dx,dy):
        """shift all the selected points by dx,dy in coordinates that are rotated according the curvature of the ribbon,
         making use of calcAngles to determine the angle
        
        keywords:
        dx,dy) the shift in microns to move each point
        
        """
     
        theta=[pos.angle for pos in self.slicePositions]
        #use a rotation matrix to determine the right dx,dy in absolute coordinates
        dx_rot=dx*cos(theta)+dy*sin(theta)
        dy_rot=(dx*sin(theta)-dy*cos(theta))
        for index, pos in enumerate(self.slicePositions):
            if pos.selected:
                pos.shiftPosition(dx_rot[index],dy_rot[index])

            
    def get_position_nearest(self,x,y):
        """return the slicePosition nearest an x,y point
        
        keywords:
        x)the x coordinate in microns to get the nearest point 
        y)the y coordinate in microns to get the nearest point
        
        returns newpos
        the slicePosition from the list which is closest to the input point
        
        """
        (xpos,ypos,select)=self.__getXYS()
        dx=(xpos-x)
        dy=(ypos-y)
        dist=np.sqrt(dx*dx+dy*dy)
        min_index=dist.argmin()
        return self.slicePositions[min_index]



    def get_nearest_position_index(self,x,y):
        """return the slicePosition index nearest an x,y point

        keywords:
        x)the x coordinate in microns to get the nearest point
        y)the y coordinate in microns to get the nearest point

        returns index
        the slicePosition index from the list which is closest to the input point

        """
        (xpos,ypos,select)=self.__getXYS()
        dx=(xpos-x)
        dy=(ypos-y)
        dist=np.sqrt(dx*dx+dy*dy)
        min_index=dist.argmin()
        return min_index


        
    def calcAngles(self):
        """calculate the angle tangent to each point on the position list
        makes sure to calculate the angle only using points on the ribbon which are selected to deal with breaks in the ribbon"""
        #calculate the delta x and delta y vector along line
        #using pointLine2D to the right, except for the last one, use the pointLine2D to the left
        
        #get the positions and selected attributes as numpy vectors
        #first sort the points to make them in order
        self.__sort_points()
        (xpos,ypos,select)=self.__getXYS()
        if (len(xpos)<2):
            return np.zeros(len(xpos))
   
        delx=np.diff(xpos)
        delx=np.append(delx,delx[len(delx)-1])
        dely=np.diff(ypos)
        dely=np.append(dely,dely[len(dely)-1])
        
        #calculate the angle from this vector, fixing up small changes in x
        theta=arctan(dely/delx)
        theta[np.isnan(theta)]=pi/2
        
        #when we are selecting a subset of points, we want the slope to be
        #defined WITHIN the selection when possible, so fix up the right 
        #most points of streaks of selection to use the slope the left
        #this won't be possible for singulatons, but who cares
        
        #conver the true/false into 1.0/0.0 binary
        #binary=self.selected*1.0
        #the ones to fix are located at the downticks of the diff
        badones,=np.where(np.diff(select)==-1)
        
        #if the first pointLine2D is a downtick, there is no pointLine2D to the left
        #so remove it from the list
        if (len(badones)>0):
            if (badones[0]==0):
                badones=badones[1:]    
            
        #use the slope to the left for these points we are fixing up
        theta[badones]=theta[badones-1]
        #for i,pos in enumerate(self.slicePositions):
        #    pos.setAngle(theta[i])
        return theta

    def getXYZ(self):
        xpos=[]
        ypos=[]
        zpos=[]
        for pos in self.slicePositions:
            xpos.append(pos.x)
            ypos.append(pos.y) 
            zpos.append(pos.z)       
        return (np.array(xpos),np.array(ypos),np.array(zpos))   

    def __getXYS(self):
        """get the current position list as a series of numpy vectors
        
        returns (xpos,ypos,select)
        xpos)a N element long numpy vector of the x coordinate in microns
        ypos)a N element long numpy vector of the y coordinate in microns
        select)a N element long numpy vector where 1.0 means it is selected and 0.0 means it is not selected"""
        xpos=[]
        ypos=[]
        select=[]
        for pos in self.slicePositions:
            xpos.append(pos.x)
            ypos.append(pos.y) 
            if pos.selected:
                select.append(1.0)
            else:
                select.append(0.0)          
        return (np.array(xpos),np.array(ypos),np.array(select))                 
    
    def getXYpoints(self):
        """get the current position list (x,y) as a series of numpy vectors
        
        returns (xpos,ypos,select)
        xpos)a N element long numpy vector of the x coordinate in microns
        ypos)a N element long numpy vector of the y coordinate in microns"""
        points=[]

        for pos in self.slicePositions:
            points.append(Point(pos.x,pos.y));
 
        return points                 
              
    def add_position(self,x,y,edgecolor='g',withpoint=True,selected=False,z=None):
        """add a new position to the position list
        
        keywords:
        x) the x coordinate of the new position in microns
        y) the y coordinate of the new position in microns
        edgecolor) matplotlib color string describing the color of the mosaic box to draw around this position (default='g')
        withpoint) boolean whether to draw the point as a blue X where this point is (default=True)

        
        """
        newPosition=slicePosition(axis=self.axis,pos_list=self,x=x,y=y,z=z,edgecolor=edgecolor,withpoint=withpoint,
                                  numberDisplaySettings = self.numberDisplaySettings,selected=selected)
        self.slicePositions.append(newPosition)  
        if self.dosort:
            self.__sort_points()
        self.updateNumbers()
        return newPosition
    
    def delete_position(self,i):
        assert (i>=0)
        assert (i<len(self.slicePositions))

        pos=self.slicePositions.pop(i)
        pos.destroy()
        del pos

    def delete_selected(self):
        """delete all the points from the position list that are currently selected"""
        #accomplish this by making a new list, and copying over the points you are saving from the old list, then replacing the old attribute
        newPositions=[]
        if not self.pos1==None:
            if self.pos1.selected:
                self.pos1=None
        if not self.pos2==None:
            if self.pos2.selected:
                self.pos2=None
            
        for pos in self.slicePositions:
            if pos.selected:
                pos.destroy()
                del pos
            else:
                newPositions.append(pos)
        self.slicePositions=newPositions
        self.updateNumbers()
        
    def LoadFromFile(self,file,format):
        if format=='AxioVision':
            self.add_from_file(file)          
        elif format=='OMX':
            self.add_from_file_OMX(file) 
        elif format=='SmartSEM':
            SEMsetting=self.add_from_file_SmartSEM(file)
            self.SmartSEMSettings=SEMsetting
        elif format=='JSON':  #MultiRibbons
            self.add_from_file_JSON(file)

    def add_from_posList(self,posList):
        for pos in posList.slicePositions:
            newPosition=slicePosition(axis=self.axis,pos_list=self,x=pos.x,y=pos.y,z=pos.z,
                numberDisplaySettings=self.numberDisplaySettings,edgecolor=pos.edgecolor,withpoint=pos.withpoint,
                selected=pos.selected,number=pos.number)
            self.slicePositions.append(newPosition)  

    def add_from_file(self,filename):
        """add points to the position list from a file, currently only implementing axiovision positionlist format
        
        keywords:
        filename)a string containing the path of the file to load
        
        """
        print "adding from file"
        ifile  = open(filename, "rb")         
        reader = csv.reader(open(filename, 'rb'), delimiter=',')      
        rownum = 0                 
        row_count = sum(1 for row in csv.reader(open(filename, 'rb'), delimiter=',') )          
        headerrows=7   
        self.xpos=np.zeros(row_count-headerrows)
        self.ypos=np.zeros(row_count-headerrows)
        self.selected=np.zeros(row_count-headerrows,dtype=bool)
        self.p1=-1
        self.p2=-1
        for row in reader:         
            if rownum >headerrows-1:
                if len(row)>0:
                    z=row[3]
                    if len(z)==0:
                        z=None
                    else:
                        z=float(z)
                    newPosition=slicePosition(axis=self.axis,pos_list=self,x=float(row[1]),y=float(row[2]),
                                              z=z,numberDisplaySettings=self.numberDisplaySettings)
                    self.slicePositions.append(newPosition)          
            rownum += 1          
        ifile.close() 
        self.updateNumbers()
    def add_from_file_OMX(self,filename):
        """add points to the position list from an OMX position list file
        
        keywords:
        filename)a string containing the path of the file to load
        
        """
        print "adding from file"
        ifile  = open(filename, "rb")         
        reader = csv.reader(open(filename, 'rb'), delimiter=',')      
        rownum = 0                 
        row_count = sum(1 for row in csv.reader(open(filename, 'rb'), delimiter=',') )          
        headerrows=0   
        self.xpos=np.zeros(row_count-headerrows)
        self.ypos=np.zeros(row_count-headerrows)
        self.selected=np.zeros(row_count-headerrows,dtype=bool)
        self.p1=-1
        self.p2=-1
        for row in reader:         
            if rownum >headerrows-1:
                if len(row)>0:
                    (label_and_x,Y,Z)=row
                    (label,X)=label_and_x.split(': ')
                    newPosition=slicePosition(axis=self.axis,pos_list=self,x=float(X),y=float(Y),
                                              numberDisplaySettings=self.numberDisplaySettings)
                    self.slicePositions.append(newPosition)          
            rownum += 1          
        ifile.close() 
        self.updateNumbers()
    
    def add_from_file_ZEN(self,filename):
        """add points to the position list from an OMX position list file
        
        keywords:
        filename)a string containing the path of the file to load
        
        """
        print "adding from file"
        ifile  = open(filename, "rb")         
        reader = csv.reader(open(filename, 'rb'), delimiter=',')      
        rownum = 0                 
        row_count = sum(1 for row in csv.reader(open(filename, 'rb'), delimiter=',') )          
        headerrows=1   
        self.xpos=np.zeros(row_count-headerrows)
        self.ypos=np.zeros(row_count-headerrows)
        self.selected=np.zeros(row_count-headerrows,dtype=bool)
        self.p1=-1
        self.p2=-1
        for row in reader:         
            if rownum >headerrows-1:
                if len(row)>0:
                    newPosition=slicePosition(axis=self.axis,pos_list=self,x=float(row[1]),y=float(row[2]),
                                              numberDisplaySettings= self.numberDisplaySettings,z=float(row[3]))
                    self.slicePositions.append(newPosition)           
            rownum += 1          
        ifile.close() 
        self.updateNumbers()
        
    def add_from_file_SmartSEM(self,filename):
        """add points to the position list from a Smart SEM position list file
        
        keywords:
        filename)a string containing the path of the file to load
        
        """
        ifile  = open(filename, "rb")         
        reader = csv.reader(open(filename, 'rb'), delimiter=',')      
        rownum = 0                 
        row_count = sum(1 for row in csv.reader(open(filename, 'rb'), delimiter=',') )          
        headerrows=4  
        self.xpos=np.zeros(row_count-headerrows)
        self.ypos=np.zeros(row_count-headerrows)
        self.selected=np.zeros(row_count-headerrows,dtype=bool)
        self.p1=-1
        self.p2=-1
        for row in reader:         
            if rownum >headerrows-1:
                (Label,X,Y,Z,T,R,M,Mag,WD)=row
                newPosition=slicePosition(axis=self.axis,pos_list=self,x=float(X),y=float(Y),
                                          numberDisplaySettings=self.numberDisplaySettings)
                self.slicePositions.append(newPosition)          
            rownum += 1          
        ifile.close() 
        SEMSetting=SmartSEMSettings(mag=float(Mag),tilt=float(T),rot=float(R),Z=float(Z),WD=float(WD))
        self.updateNumbers()
        return SEMSetting

    def add_from_file_JSON(self,filename): #MultiRibbons
        """add points to the position list from a JSON file

        keywords:
        filename)a string containing the path of the file to load

        """
        print "adding from file"
        ifile  = open(filename, "rb")
        thestring = ifile.read()
        thedict = json.JSONDecoder().decode(thestring)
        print thedict
        self.xpos=np.zeros(len(thedict["POSITIONS"]))
        self.ypos=np.zeros(len(thedict["POSITIONS"]))
        self.selected=np.zeros(len(thedict["POSITIONS"]),dtype=bool)
        self.p1=-1
        self.p2=-1
        for i in range(len(thedict["POSITIONS"])):
            newPosition=slicePosition(axis=self.axis,pos_list=self,x=thedict["POSITIONS"][i]["X"],\
            y=thedict["POSITIONS"][i]["Y"],z=None,angle=thedict["POSITIONS"][i]["ANGLE"],numberDisplaySettings=self.numberDisplaySettings)
            self.slicePositions.append(newPosition)
        self.mosaic_settings.mx = thedict["MOSAIC"]["MOSAICX"]
        self.mosaic_settings.my = thedict["MOSAIC"]["MOSAICY"]
        self.mosaic_settings.overlap = thedict["MOSAIC"]["OVERLAP"]
        self.set_mosaic_settings(self.mosaic_settings)
        ifile.close()
        self.updateNumbers()

    def load_frame_state_table(self,filename):
        filename, formattype = filename.split('.')
        filename = filename + 'frame_state_table.json'


        if os.path.exists(filename):
            ifile = open(filename,'rb')
            thedict = json.load(ifile)
            for i,item in enumerate(sorted(thedict)):
                self.slicePositions[i].update_framestates(thedict[item])
        else:
            pass



    def save_position_list(self,filename,trans=None):
        """save the positionlist to a axiovision position list format, csv format
        
        keywords:
        filename)a string containing the path of the file to save list into
        trans)an optional transform object which will cause the points to be saved to the file, not with their original
        coordinates, but with the coordinates run through the trans.transform(x,y) method
        """  
        self.__sort_points()
        writer = csv.writer(open(filename, 'wb'), delimiter=',',quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(["Slide","","","","",""])
        writer.writerow(["Name","Width","Height","Description",'',''])
        writer.writerow(["Slide 1A Ribbon 1 Site 1",76000.000000,24000.000000,"Slide - 76 mm x 24 mm (3 x 1)",'',''])
        writer.writerow(['','','','','',''])
        writer.writerow(['','','','','',''])
        writer.writerow(["Positions",'','','','',''])
        writer.writerow(["Comments","PositionX","PositionY","PositionZ","Color","Classification"])
   
        for index,pos in enumerate(self.slicePositions):
            #"Comments","PositionX","PositionY","PositionZ","Color","Classification"
            #"1000000",-29541.755,6144.1,0.000000," blue "," blue"
            if trans == None:
                writer.writerow(["%d"%(100000+index),pos.x,pos.y,pos.z," blue "," blue "])
            else:
                (xt,yt)=trans.transform(pos.x,pos.y)
                writer.writerow(["%d"%(100000+index),xt,yt,pos.z," blue "," blue "])
    
    
    def save_position_list_uM(self,filename,trans=None):
        self.__sort_points()
        
        points=np.array([[pos.x,pos.y] for pos in self.slicePositions])

        poslist=[]
        for index,pos in enumerate(self.slicePositions):
            #"Comments","PositionX","PositionY","PositionZ","Color","Classification"
            #"1000000",-29541.755,6144.1,0.000000," blue "," blue"
                
            if trans == None:
                posdict={"GRID_COL": 0,"DEVICES": [{"DEVICE": "XYStage","AXES": 2,"Y": pos.y,"X": -pos.x,"Z": 0}],"PROPERTIES": {},"DEFAULT_Z_STAGE": "ZStage","LABEL": "p%03.3d"%(index),"GRID_ROW": 0,"DEFAULT_XY_STAGE": "XYStage"}
              
            else:
                (xt,yt)=trans.transform(pos.x,pos.y)
                posdict={"GRID_COL": 0,"DEVICES": [{"DEVICE": "XYStage","AXES": 2,"Y": yt,"X": -xt,"Z": 0}],"PROPERTIES": {},"DEFAULT_Z_STAGE": "ZStage","LABEL": "p%03.3d"%(index),"GRID_ROW": 0,"DEFAULT_XY_STAGE": "XYStage"}   
        
            poslist.append(posdict)
            
        dict={"VERSION": 3,
        "ID": "Micro-Manager XY-position list",
        "POSITIONS":poslist}
        
        thestring=json.JSONEncoder().encode(dict)
        file = open(filename,'w')
        file.write(thestring)
        file.close()
        
    def save_position_list_SmartSEM(self,filename,SEMS=SmartSEMSettings(),trans=None):     
        self.__sort_points()
        writer = csv.writer(open(filename, 'wb'), delimiter=',')
        writer.writerow(["Leo Points List"])
        writer.writerow(["Absolute"])
        writer.writerow(["Label","X","Y","Z","T","R","M","Mag","WD"])
        writer.writerow(["%d"%len(self.slicePositions)])
        for index,pos in enumerate(self.slicePositions):
            #"Comments","PositionX","PositionY","PositionZ","Color","Classification"
            #"1000000",-29541.755,6144.1,0.000000," blue "," blue"
            if trans == None:
                writer.writerow(["%03d"%(index),pos.x,pos.y,SEMS.Z,SEMS.tilt,SEMS.rot,0.00,SEMS.mag,SEMS.WD])
            else:
                (xt,yt)=trans.transform(pos.x,pos.y)
                writer.writerow(["%03d"%(index),xt,yt,SEMS.Z,SEMS.tilt,SEMS.rot,0.00,SEMS.mag,SEMS.WD])
     
    def save_position_list_ZEN(self,filename,trans=None,planePoints=None,zoffset=47.33-34.79):     
        self.__sort_points()
        writer = csv.writer(open(filename, 'wb'), delimiter=',')
       
        writer.writerow(["Name","X","Y","Z","Width","Height","ContourType"])
        
        points=np.array([[pos.x,pos.y] for pos in self.slicePositions])
        print points.shape
        print points
        if planePoints is not None:
            newZ=griddata(planePoints[:,0:2],planePoints[:,2],points,'nearest')
        else:
            newZ=np.zeros(len(self.slicePositions));
            for index,pos in enumerate(self.slicePositions):
                if pos.Z is not None:
                    newZ[index]=pos.Z-zoffset
                    
        for index,pos in enumerate(self.slicePositions):
            #"Comments","PositionX","PositionY","PositionZ","Color","Classification"
            #"1000000",-29541.755,6144.1,0.000000," blue "," blue"
            
            if trans == None:
                writer.writerow(["p%03.3d"%(index),pos.x,pos.y,newZ[index]+zoffset,'','',''])
              
            else:
                (xt,yt)=trans.transform(pos.x,pos.y)
                writer.writerow(["p%03.3d"%(index),xt,yt,newZ[index]+zoffset,'','',''])
    
    def write_position_ZENczsh(self,SingleTileRegions,index,x,y,z):

        SingleTileRegion=ET.SubElement(SingleTileRegions,"SingleTileRegion")
        SingleTileRegion.set("Name","p%03d"%index)
        SingleTileRegion.set("Id","%d"%(1000000+index))
        X=ET.SubElement(SingleTileRegion,"X")
        Y=ET.SubElement(SingleTileRegion,"Y")
        Z=ET.SubElement(SingleTileRegion,"Z")
        X.text = "%5.3f"%x
        Y.text = "%5.3f"%y
        Z.text = "%5.3f"%z
        
        IsUsedForAcquisition=ET.SubElement(SingleTileRegion,"IsUsedForAcquisition")
        IsUsedForAcquisition.text = "true"
        
        return SingleTileRegions
                  
    def save_position_list_ZENczsh(self,filename,trans=None,planePoints=None,zoffset=47.33-34.79):     
        self.__sort_points()
        
        root = ET.Element("SampleHolder")
        #overlap=ET.SubElement(root,"Overlap")
        #overlap.text = 0.05
        #ScanMode=ET.SubElement(root,"ScanMode")
        #ScanMode.text = "Comb"
        #IsConstantTiles=ET.SubElement(root,"IsConstantTiles")
        #IsConstantTiles.text = "false"
        #TileRegionAnchorMode=ET.SubElement(root,"TileRegionAnchorMode")
        #TileRegionAnchorMode.text = "BottomRight"
        TileRegions=ET.SubElement(root,"TileRegions")
        #overlap.text = 0.05
        #writer.writerow(["  <TileRegions />"])
        #writer.writerow(["<SingleTileRegions>"])
        TileRegions=ET.SubElement(root,"TileRegions")
        SingleTileRegions=ET.SubElement(root,"SingleTileRegions")
        
        
        points=np.array([[pos.x,pos.y] for pos in self.slicePositions])
        print points.shape
        print points
        if planePoints is not None:
            newZ=griddata(planePoints[:,0:2],planePoints[:,2],points,'nearest')
        else:
            newZ=np.zeros(len(self.slicePositions));
            for index,pos in enumerate(self.slicePositions):
                if pos.Z is not None:
                    newZ[index]=pos.Z-zoffset
                    
        for index,pos in enumerate(self.slicePositions):
            #"Comments","PositionX","PositionY","PositionZ","Color","Classification"
            #"1000000",-29541.755,6144.1,0.000000," blue "," blue"
            
            if trans == None:
                self.write_position_ZENczsh(SingleTileRegions,index,pos.x,pos.y,newZ[index]+zoffset)
              
            else:
                (xt,yt)=trans.transform(pos.x,pos.y)
                self.write_position_ZENczsh(SingleTileRegions,index,xt,yt,newZ[index]+zoffset)
              
        tree = ET.ElementTree(root)
        
        tree.write(filename,pretty_print=True,xml_declaration=True)
        
                            
    def save_position_list_OMX(self,filename,trans=None,Z=13235.0):
        self.__sort_points()
        writer = csv.writer(open(filename, 'wb'), delimiter=',')
        count=0;
        for index,pos in enumerate(self.slicePositions):
            count=count+1;
            if trans==None:
                writer.writerow(['%03d: %f'%(index,pos.x),pos.y,Z])    
            else:
                (xt,yt)=trans.transform(pos.x,pos.y)
                writer.writerow(['%03d: %f'%(index,xt),yt,Z])  

    def save_position_list_JSON(self,filename,trans=None): #MultiRibbons
        #save the positionlist to JSON format, include position x, y, angle, mosaic settings, channel settings
        self.__sort_points()

        poslist=[]
        for index,pos in enumerate(self.slicePositions):

            if trans == None:
                posdict={"SECTION": "%d"%(100000+index),"X": pos.x,"Y": pos.y,"ANGLE": pos.angle}

            else:
                (xt,yt)=trans.transform(pos.x,pos.y)
                posdict={"SECTION": "%d"%(100000+index),"X": xt,"Y": yt,"ANGLE": pos.angle}

            poslist.append(posdict)

        dict={"MOSAIC": {"MOSAICX": self.mosaic_settings.mx,"MOSAICY": self.mosaic_settings.my,"OVERLAP": self.mosaic_settings.overlap},
        "CHANNELS": {},
        "POSITIONS":poslist}

        thestring=json.JSONEncoder().encode(dict)
        file = open(filename,'w')
        file.write(thestring)
        file.close()


    def on_save_frame_state_table(self,filepath):

        filename, formattype = filepath.split('.')
        filename = filename + 'frame_state_table.json'
        statetable_dict = {}

        for i in range(len(self.slicePositions)):
            section_num, frame_statelist = self.slicePositions[i].create_frame_state_list()
            statetable_dict[section_num] = frame_statelist
        thestring = json.JSONEncoder().encode(statetable_dict)
        with open(filename,'w') as file:
            file.write(thestring)
        file.close()




    def save_frame_list_OMX(self,filename,trans=None,Z=13235.0):
        """save the positionlist to a SmartSEM position list csv format, where each frame of the mosaic is its own position
        keywords:
        filename)a string containing the path of the file to save list into
        trans)an optional transform object which will cause the points to be saved to the file, not with their original
        coordinates, but with the coordinates run through the trans.transform(x,y) method
        """  
        if self.dosort:
            self.__sort_points()
        writer = csv.writer(open(filename, 'wb'), delimiter=',')
        count=0;
        for index,pos in enumerate(self.slicePositions):

            #pos.frameList.__sort_points(vertsort=True)
            for frameindex,framepos in enumerate(pos.frameList.slicePositions):
                count=count+1;
                if trans==None:
                    writer.writerow(["S%03d_F%03d: %f"%(index,frameindex,framepos.x),framepos.y,Z])    
                else:
                    (xt,yt)=trans.transform(framepos.x,framepos.y)
                    writer.writerow(["S%03d_F%03d: %f"%(index,frameindex,xt),yt,Z])  
                    
    def save_frame_list_SmartSEM(self,filename,SEMS=SmartSEMSettings(),trans=None):
        """save the positionlist to a SmartSEM position list csv format, where each frame of the mosaic is its own position
        keywords:
        filename)a string containing the path of the file to save list into
        trans)an optional transform object which will cause the points to be saved to the file, not with their original
        coordinates, but with the coordinates run through the trans.transform(x,y) method
        """  

        self.__sort_points()
        writer = csv.writer(open(filename, 'wb'), delimiter=',')
        writer.writerow(["Leo Points List"])
        writer.writerow(["Absolute"])
        writer.writerow(["Label","X","Y","Z","T","R","M","Mag","WD"])
        count=0
        for index,pos in enumerate(self.slicePositions):
            for frameindex,framepos in enumerate(pos.frameList.slicePositions):
                count=count+1
        writer.writerow(["%d"%count])

        for index,pos in enumerate(self.slicePositions):
            pos.frameList.__sort_points(vertsort=True)
            for frameindex,framepos in enumerate(pos.frameList.slicePositions):
                if trans==None:
                    writer.writerow(["S%03d_F%03d"%(index,frameindex),framepos.x,framepos.y,SEMS.Z,SEMS.tilt,SEMS.rot,0.00,SEMS.mag,SEMS.WD])    
                else:
                    (xt,yt)=trans.transform(framepos.x,framepos.y)
                    writer.writerow(["S%03d_F%03d"%(index,frameindex),xt,yt,SEMS.Z,SEMS.tilt,SEMS.rot,0.00,SEMS.mag,SEMS.WD])
    
    def save_frame_list(self,filename,trans=None):
        """save the positionlist to a axiovision position list format, csv format, where each frame of the mosaic is its own position
        
        keywords:
        filename)a string containing the path of the file to save list into
        trans)an optional transform object which will cause the points to be saved to the file, not with their original
        coordinates, but with the coordinates run through the trans.transform(x,y) method
        """  
        if self.dosort:
            self.__sort_points()
        writer = csv.writer(open(filename, 'wb'), delimiter=',',quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(["Slide","","","","",""])
        writer.writerow(["Name","Width","Height","Description",'',''])
        writer.writerow(["Slide 1A Ribbon 1 Site 1",76000.000000,24000.000000,"Slide - 76 mm x 24 mm (3 x 1)",'',''])
        writer.writerow(['','','','','',''])
        writer.writerow(['','','','','',''])
        writer.writerow(["Positions",'','','','',''])
        writer.writerow(["Comments","PositionX","PositionY","PositionZ","Color","Classification"])
        
        for index,pos in enumerate(self.slicePositions):
            #pos.frameList.__sort_points(vertsort=True)
            for frameindex,framepos in enumerate(pos.frameList.slicePositions):
                if trans==None:
                    writer.writerow(["S%03d_F%03d"%(index,frameindex),framepos.x,framepos.y,0," blue "," blue "])    
                else:
                    (xt,yt)=trans.transform(framepos.x,framepos.y)
                    writer.writerow(["S%03d_F%03d"%(index,frameindex),xt,yt,0," blue "," blue "]) 
                    
    def __sort_points(self,vertsort=False):
        """sort the slicePositions in the list according to their x value"""
        if self.dosort:
            if vertsort:
                self.slicePositions.sort(key=lambda pos: pos.y, reverse=False)
            else:
				self.slicePositions.sort(key=lambda pos: pos.x, reverse=False)  
            
    def updateNumbers(self):
        for index,pos in enumerate(self.slicePositions):
            pos.setNumber(index)
            
    def setNumberVisibility(self,isvisible):
        self.shownumbers=isvisible
        for index,pos in enumerate(self.slicePositions):
            pos.set_number_visible(isvisible)
            
    def calcFrameSize(self):
        """calculate the size of a single frame of the camera given the current camera_settings and magnification from mosaic_settings
        
        returns (frameheight,framewidth)
        the size of the frame in microns
        
        """
        framewidth=self.camera_settings.sensor_width*self.camera_settings.pix_width/self.mosaic_settings.mag
        frameheight=self.camera_settings.sensor_height*self.camera_settings.pix_height/self.mosaic_settings.mag  
        return (frameheight,framewidth)
    
    def calcMosaicSize(self):   
        """calculates the size of the mosaic given the current camera_settings and mosaic settings
        
        returns (mosaicheight,mosaicwidth)
        the size of the mosaic in microns
        
        """
        mx=self.mosaic_settings.mx
        my=self.mosaic_settings.my
        overlap=self.mosaic_settings.overlap   
        (frameheight,framewidth)=self.calcFrameSize()   
        totalwidth=framewidth*mx-((overlap*1.0)/100)*framewidth*(mx-1)
        totalheight=frameheight*my-((overlap*1.0)/100)*frameheight*(my-1)     
        return (totalheight,totalwidth)
    
    def destroy(self):
        """destroys all the positions in this position list by calling their destroy functions"""
        for pos in self.slicePositions:
            pos.destroy()
            del pos



class slicePosition():
    """class which contains information about a single position in the position list, and is responsible for keeping 
    its matplotlib representation up to date via function calls which are mostly managed by its posList"""
    def __init__(self,axis,pos_list,x,y,withpoint=True,selected=False, activated = True, autofocus_trigger = False, initial_trigger = False,
                 edgecolor='g',number=-1,numberDisplaySettings=NumberDisplaySettings(),z=None,angle = 0,showAngle=True, framestatetable = None):
        """constructor function
        
        keywords:
        axis)what matplotlib axis to plot this points graphical representation
        pos_list)the position list this point is associated with
        x)the x coordinate of this position (in microns)
        y)the y coordinate of this position (in microns)
        withpoint)whether to plot this position with a blue X point (default=True)
        selected)whether this position should be selected upon creation (default=False)
        edgecolor)string containing the matplotlib color designation of the mosaic box for this point (default='g')
        
        """
        self.axis=axis
        self.pos_list=pos_list
        self.x=x
        self.y=y 
        self.z=z
        self.angle = angle
        self.selected=selected
        self.activated=activated
        self.autofocus_trigger = autofocus_trigger
        self.initial_trigger = initial_trigger
        self.framestatetable = framestatetable
        self.withpoint=withpoint
        self.number = number
        self.numberDisplaySettings = numberDisplaySettings
        self.showAngle = showAngle
        self.quiverLength = .15
        self.quiverLine = None
        if self.withpoint:
            self.__paintPoint()
        self.__paintMosaicBox(edgecolor)
        self.frameList= None
        self.label = None



        if self.axis:
            self.numTxt = self.axis.text(self.x,self.y,str(self.number),color=self.numberDisplaySettings.color,weight='bold') 
            self.numTxt.set_visible(self.numberDisplaySettings.shownumbers)
            self.numTxt.set_horizontalalignment(self.numberDisplaySettings.horizontalAlignment)
            self.numTxt.set_verticalalignment(self.numberDisplaySettings.verticalAlignment)
        else:
            self.numTxt = None
 
        self.setAngle(angle)
    
        
    def __paintPoint(self):
        """paint the point for this position, initializing the pointLine2d attribute and adding it to the axis"""
        if not self.axis:
            return None
        print self.axis
        if self.activated:
            marker = 'o'
        else:
            marker = 'x'
        if self.selected:
            color='r'
        else:
            color='b'
        self.pointLine2D=Line2D([self.x],[self.y],marker=marker,markersize=7,markeredgewidth=1.5,markeredgecolor=color,)

        self.axis.add_line(self.pointLine2D)
        if self.showAngle:
            u = self.quiverLength*np.sin(self.angle)
            v = self.quiverLength*np.cos(self.angle)
            self.quiverLine = Quiver(self.axis,self.x,self.y,u,v,units='inches',scale=.5,headlength=3,headwidth=3,
                                     width=.02,scale_units='inches',color='y')
            self.axis.add_artist(self.quiverLine)

    def __paintMosaicBox(self,edgecolor='g'):
        """paint the box to represent the size of the mosaic for this position
        
        keywords:
        edgecolor) string containing the matplotlib color designation for the box (default='g')
        
        """ 
        if not self.axis:
            return None
        (h,w)=self.pos_list.calcMosaicSize()    
        #use the CenterRectangle class to plot the rectangle in a straight forward way
        self.box = CenterRectangle( (self.x,self.y), width=w, height=h,edgecolor=edgecolor,fill=False,linewidth=2,visible=self.pos_list.mosaic_settings.show_box)
        self.axis.add_patch(self.box)
    
    def paintFrames(self):
        if not self.axis: return None
        """paint the individual frames for this position, using either a straight grid, or a tilted algorithm depending if the current angle attribute
        is larger or smaller than 2 degrees (2*pi/180 radians)"""
        if abs(self.angle)>(2*pi/180):
            self.__paintFramesTilted()
        else:
            self.__paintFramesGrid()
        if self.framestatetable != None:
            self.update_framestates(self.framestatetable)
            
    def __paintFramesGrid(self):
        if not self.axis: return None
        """paint the individual frames for this position using a standard grid algorithm according to the current mosaic_settings for the associated position list"""
        #only do this if the current list is empty
        if self.frameList==None:
            frameNumberSettings = NumberDisplaySettings(shownumbers=self.numberDisplaySettings.shownumbers,
                                            color='m',
                                            horizontalAlignment='center',
                                            verticalAlignment='center')
            #the frame list will be another posList with the same camera_settings, but the default MosaicSettings (i.e. a 1x1)
            self.frameList=posList(self.axis,mosaic_settings=MosaicSettings(mag=self.pos_list.mosaic_settings.mag),
                                   camera_settings=self.pos_list.camera_settings,dosort=False,numberDisplaySettings=frameNumberSettings)
            (fh,fw)=self.pos_list.calcFrameSize()
            (h,w)=self.pos_list.calcMosaicSize()
            mx = self.pos_list.mosaic_settings.mx
            my = self.pos_list.mosaic_settings.my
            #fill in an array with x and y coordinates
            xx=np.zeros((my,mx),dtype=np.double)
            yy=np.zeros((my,mx),dtype=np.double)


            #use the point class to add the offsets from the upper left necessary to make the grid
            UL= Point(self.x,self.y)-Point(w/2,h/2)
            alpha=(self.pos_list.mosaic_settings.overlap*1.0)/100
            evenodd = True
            for x in range(mx):
                delX=Point((x*fw+(fw/2)-x*alpha*fw),0)
                for y in range(my):
                    delY=Point(0,y*fh+(fh/2)-y*alpha*fh)
                    #calculates the position for this frame
                    thispoint=UL+delX+delY
                    xx[y,x]=thispoint.x
                    yy[y,x]=thispoint.y

                    #make the frameList boxes be cyan in color
                    #self.frameList.add_position(thispoint.x,thispoint.y,withpoint=False,edgecolor='c')
                    #evenodd *= -1

            for y in range(my):
                if y%2==0:
                    xrange = range(mx)
                else:
                    xrange = range(mx-1,-1,-1)
                for x in xrange:
                    self.frameList.add_position(xx[y,x],yy[y,x],withpoint=False,edgecolor='c')

            self.frameList.set_mosaic_visible(True)  

    def __paintFramesTilted(self):
        if not self.axis: return None
        """paint the individual frames for this position using an algorithm which should take into account the angle of the slice's tilt"""
        if self.frameList==None:
            frameNumberSettings = NumberDisplaySettings(shownumbers=self.numberDisplaySettings.shownumbers,
                                                        color='m',
                                                        horizontalAlignment='center',
                                                        verticalAlignment='center')
            self.frameList=posList(self.axis,mosaic_settings=MosaicSettings(mag=self.pos_list.mosaic_settings.mag),
                                   camera_settings=self.pos_list.camera_settings,
                                   dosort=False,numberDisplaySettings=frameNumberSettings)
            (fh,fw)=self.pos_list.calcFrameSize()
            (h,w)=self.pos_list.calcMosaicSize() 
            alpha=(self.pos_list.mosaic_settings.overlap*1.0)/100
            mx = self.pos_list.mosaic_settings.mx
            my = self.pos_list.mosaic_settings.my
            #fill in an array with x and y coordinates
            xx=np.zeros((my,mx),dtype=np.double)
            yy=np.zeros((my,mx),dtype=np.double)
            #cent_line_rot=UL.rotate_around(Point(self.x,self.y),self.angle)
            if my==1:
                v=.5*(mx-1)*fw*(1-alpha)
                frame1=Point(self.x,self.y)-Point(v*cos(self.angle),v*sin(self.angle));
            else:
                cent_line=Point(self.x,self.y)-Point(0,h/2-(fh/2)) 
                cent_line_shift=cent_line+Point((h/2-(fh/2))*tan(self.angle),0)
                frame1=cent_line_shift+Point(-.5*(mx-1)*fw*(1-alpha),0);
            #frame1=UL
			#frame1=self.__shiftdown_andslide_first(ULr,fh/2,self.angle,0)
            
            # self.frameList.add_position(frame1.x,frame1.y,withpoint=False,edgecolor='c')
            for y in range(my):
                if y==0:
                    startframe=frame1
                else:
                    startframe=self.__shiftdown_andslide(startframe, fh*(1-alpha), self.angle,0)           
                for x in range(mx):
                    if my==1:
                        v=x*fw*(1-alpha);
                        delX=Point(v*cos(self.angle),v*sin(self.angle))
                    else:
                        delX=Point(x*fw-x*alpha*fw,0)
                    thispoint=startframe+delX
                    #if x==0:
                    #    x=x
                    #    #thispoint=thispoint+Point(-fw*sin(self.angle)*sin(self.angle),-fw*sin(self.angle)*cos(self.angle))
                    xx[y,x]=thispoint.x
                    yy[y,x]=thispoint.y
                    #self.frameList.add_position(thispoint.x,thispoint.y,withpoint=False,edgecolor='c')
                    

            for y in range(my):
                if y%2==0:
                    xrange = range(mx)
                else:
                    xrange = range(mx-1,-1,-1)
                for x in xrange:
                    self.frameList.add_position(xx[y,x],yy[y,x],withpoint=False,edgecolor='c')


            self.frameList.set_mosaic_visible(True)


            #shiftx_rot=.5*(self.pos_list.mosaic_settings.mx-1)*fw*(1-alpha);
            #self.frameList.shift_all(-shiftx_rot*cos(self.angle),-shiftx_rot*sin(self.angle))
     
    def __shiftdown_andslide_first(self,start,drop,theta,over):
        """helper function for paintFramesTilted, which slides the first frame down and over from the upper left
        
        keywords:
        start)the point we are starting at
        drop)how far down to move it
        theta) the angle which is down
        over) how far over to move it
        
        returns newpoint
        the point after the sliding
        """
        if not self.axis: return None
        newpoint=Point(start.x,start.y)+Point(0,drop)
        newpoint=newpoint-Point(2*drop*tan(theta),0)
        newpoint=newpoint+Point(over,0)
        return newpoint
            
    def __shiftdown_andslide(self,start,drop,theta,over):
        """helper function for paintFramesTilted, which slides the subsequent frames down and over from the upper left
        
        keywords:
        start)the point we are starting at
        drop)how far down to move it
        theta) the angle which is down
        over) how far over to move it
        
        returns newpoint
        the point after the sliding
        
        """
        if not self.axis: return None
        newpoint=Point(start.x,start.y)+Point(0,drop)
        newpoint=newpoint-Point(drop*tan(theta),0)
        newpoint=newpoint+Point(over,0)
        return newpoint

  
           
    def __updateMosaicSize(self):
        """reset the properties of the mosaic box due to an updated parameters of the mosaic or camera settings"""
        if not self.axis: return None
        (h,w)=self.pos_list.calcMosaicSize() 
        self.box.set_width(w)
        self.box.set_height(h)
     
    def __updateFramesLayout(self):
        """update the layout of the frames, called when mosaic, camera, or maybe angle settings are changed"""
        if not self.axis: return None
        if not self.frameList==None:
            for frame in self.frameList.slicePositions:
                frame.destroy()
                del frame
            del self.frameList
            self.frameList=None
            self.paintFrames()
 
    def __updateAllPositions(self):
        """private function update the drawing parameters of this position for all the matplotlib elements associated with it"""
        if not self.axis: return None
        self.__updateMosaicPosition()
        if self.withpoint:
            self.__updatePointPosition()
        self.__updateLabelPosition()
        self.__updateNumberPosition()
            
    def __updateMosaicPosition(self):
        """private function to update the position of the matplotlib box representing the mosaic for this position"""
        if not self.axis: return None
        self.box.set_center((self.x,self.y))
        transform = matplotlib.transforms.Affine2D().rotate_around(self.x,self.y,self.angle) + self.axis.transData
        self.box.set_transform(transform)
        
    def __updateNumberPosition(self):
        self.numTxt.set_x(self.x)
        self.numTxt.set_y(self.y)
        
    def __updatePointPosition(self):
        """private function to update the position of the matplotlib Line2d representing this position"""
        self.pointLine2D.set_xdata([self.x])
        self.pointLine2D.set_ydata([self.y])
        self.quiverLine.set_offsets(np.array([self.x,self.y]))


    def __updateQuiverAngle(self):
        if self.quiverLine is not None:
            u=self.quiverLength*np.sin(self.angle)
            v=self.quiverLength*np.cos(self.angle)
            self.quiverLine.set_UVC(u,v,None)

    def __updateLabelPosition(self):
        """private function to update the position of the label representing this position"""
        if not self.axis: return None
        if self.label != None:
            self.label.set_x(self.x)
            self.label.set_y(self.y)
     
    def setNumber(self,number):
        if not self.axis: return None
        self.number=number
        self.numTxt.set_text(str(number)+"  ")
                                 
    def addLabel(self,txt):
        """add a label for this position, if this position doesn't have one
        
        keywords:
        txt)the string to write at this position, should add a space before the txt to have it offset e.g. txt=" #1"
        """
        if not self.axis: return None
        if self.label == None:
            self.label= self.axis.text(self.x,self.y,txt,color='r',weight='bold') 
        
    def removeLabel(self):
        """remove the label for this position if it has one"""
        if not self.axis: return None
        if not self.label == None:
            self.label.remove()
            del self.label
            self.label = None

    def rotateAngle(self,offset):
        """

        :param offset: amount in radians to increase or decrease angle associated with this position
        :return: None
        """
        newangle = self.angle + offset
        self.setAngle(newangle)

    def setAngle(self,angle):
        """set the angle of the ribbon at this position, updating thing accordingly appropriately
        
        keywords:
        angle)the angle in radians of the ribbon, where 0 is flat in X, and negative angle means clockwise rotation
        
        """
        if not self.axis: return None
        self.angle=angle
        transform = matplotlib.transforms.Affine2D().rotate_around(self.x,self.y,angle) + self.axis.transData
        self.box.set_transform(transform)
        self.__updateFramesLayout()
        self.__updateQuiverAngle()

    
    def set_box_visible(self,visible):
        """update the visibility of the mosaic box
        
        keywords:
        visible)boolean as to whether it should be visible or not
        
        """
        if not self.axis: return None
        self.box.set_visible(visible)     
                 
    def shiftPosition(self,dx,dy):
        """shift the coordinates of this position, and update its matplotlib elements accordingly
        
        keywords:
        dx)shift in x (microns)
        dy)shift in y (microns)
        
        """
        self.x=self.x+dx
        self.y=self.y+dy
        if not self.frameList==None:
            self.frameList.shift_all(dx, dy)
        self.__updateAllPositions()
        
    def set_number_visible(self,isvisible):
        if not self.axis: return None
        self.numTxt.set_visible(isvisible)
        if self.frameList is not None:
            self.frameList.setNumberVisibility(isvisible)
        
    def setPosition(self,x,y):
        """set the coordinates for this position, and update its matplotlib elements accordingly
        
        keywords)
        x)the x new x coordiante in microns
        y)the new y coordinate in microns
        
        """
        #accomplish this by calling shiftPosition appropriately to conserve rewriting code
        dx=x-self.x
        dy=y-self.y
        self.shiftPosition(dx, dy)
        
    def getPosition(self):
        return (self.x,self.y)
      
    def update_mosaic_settings(self):
        """update the matplotlib representation of this point's mosaic"""
        if not self.axis: return None
        self.__updateMosaicSize()
        self.__updateFramesLayout()

    def set_activated(self,activated,type = 'slice'):

        self.activated=activated
        self.__updatePointActivated(type)

    def set_selected(self,selected):
        """set this point to be selected or not
        
        keywords:
        selected)boolean describing whether this point is or is not selected
        """
        self.selected=selected
        self.__updatePointSelect()

    def set_autofocus_trigger(self,trigger, type = 'Normal'):
        if type == 'Normal':
            self.initial_trigger = False
            self.autofocus_trigger = trigger
            self.__updatePointActivated('frame')
        if type == 'Initial':
            self.initial_trigger = trigger
            if self.initial_trigger == True:
                self.autofocus_trigger = False
            self.__updatePointActivated('frame')


    def create_frame_state_list(self):
        # filename, format = filename.split('.')
        # filename = filename + 'frame_state_table.' + 'json'

        statedict = {'inactive' : 0,
                    'active' : 1,
                    'initial_frame' : 2,
                    'trigger_autofocus' : 3}
        statelist = []
        if self.frameList == None:
            return None
        else:
            for fpos in self.frameList.slicePositions:
                if not fpos.activated:
                    statelist.append(statedict['inactive'])
                elif fpos.initial_trigger:
                    statelist.append(statedict['initial_frame'])
                elif fpos.autofocus_trigger:
                    statelist.append(statedict['trigger_autofocus'])
                else:
                    statelist.append(statedict['active'])

            return self.number, statelist



    def update_framestates(self,statelist):
        if self.frameList == None:
            self.paintFrames()
            self.framestatetable = statelist
        for i,fpos in enumerate(self.frameList.slicePositions):
            framestate = statelist[i]
            # print 'framestate:', framestate
            if framestate == 0:
                fpos.set_activated(False,type = 'frame')
            elif framestate == 2:
                fpos.set_autofocus_trigger(True,'Initial')
            elif framestate == 3:
                fpos.set_autofocus_trigger(True)
            else:
                fpos.set_activated(True, type = 'frame')

    def select_if_inside(self,verts):
        """select this point if it is inside the list of vertices given (created by Lasso tool)
        as determined by matplotlib.nxutils.points_inside_poly
        
        keywords:
        verts)the list of vertices
        
        """
        thepath=path.Path(verts)
        if not self.axis: return None
        vec=np.array([[self.x],[self.y]])
        #vec=np.vstack((self.x,self.y))
        #isselect = points_inside_poly(vec.transpose(), verts)[0]
        isselect = thepath.contains_point(vec.transpose())
        if not isselect==self.selected:
            self.selected=isselect
            self.__updatePointSelect()
    def __updatePointActivated(self,type = 'slice'):
        if not self.axis: return None
        if type == 'slice':
            if self.activated:
                marker = 'o'
                color = 'b'
            else:
                marker = 'x'
                color = 'm'
            self.pointLine2D.set_marker(marker)
            # self.pointLine2D.set_markercolor(color)
            self.pointLine2D.set_markeredgecolor(color)
        if type == 'frame':
            if (self.initial_trigger):
                self.activated = True
                self.autofocus_trigger = False
                color = 'y'
            elif self.autofocus_trigger:
                self.initial_trigger = False
                self.activated = True
                color = 'b'
            elif not self.activated:
                self.autofocus_trigger = False
                self.initial_trigger = False
                color = 'r'


            elif (self.activated) and not(self.initial_trigger) and not (self.autofocus_trigger):
                color = 'c'
            self.box.set_edgecolor(color)


    def __updatePointSelect(self):
        """private function for updating the color of the point,depending on its selected state"""
        if not self.axis: return None
        if self.selected:
            color='r'
        else:
            color='b'
        self.pointLine2D.set_markeredgecolor(color)
                
    def destroy(self):
        """function for removing and destroying all the matplotlib elements associated with this position"""
        if not self.axis: return None
        if self.withpoint:
            self.pointLine2D.remove()
        self.box.remove()
        if not self.label == None:
            self.label.remove()
        if not self.frameList == None:
            self.frameList.destroy()
        if not self.numTxt == None:
            self.numTxt.remove()
        if self.quiverLine is not None:
            self.quiverLine.remove()