#!/usr/bin/python
import numpy as np
from PositionList import posList

import Tkinter, Tkconstants, tkFileDialog
import csv
import os

#class Tk_Tform_PosList(Tkinter.Frame):
#
#  def __init__(self, root):
#
#    Tkinter.Frame.__init__(self, root)
#
#    # options for buttons
#    button_opt = {'fill': Tkconstants.BOTH, 'padx': 5, 'pady': 5}
#
#    # define buttons
#    Tkinter.Button(self, text='askopenfile', command=self.askopenfile).pack(**button_opt)
#    Tkinter.Button(self, text='askopenfilename', command=self.askopenfilename).pack(**button_opt)
#    Tkinter.Button(self, text='asksaveasfile', command=self.asksaveasfile).pack(**button_opt)
#    Tkinter.Button(self, text='asksaveasfilename', command=self.asksaveasfilename).pack(**button_opt)
#    Tkinter.Button(self, text='askdirectory', command=self.askdirectory).pack(**button_opt)
#
#    # define options for opening or saving a file
#    self.file_opt = options = {}
#    options['defaultextension'] = '' # couldn't figure out how this works
#    options['filetypes'] = [('all files', '.*'), ('text files', '.txt')]
#    options['initialdir'] = 'C:\\'
#    options['initialfile'] = 'myfile.txt'
#    options['parent'] = root
#    options['title'] = 'This is a title'
#
#    # This is only available on the Macintosh, and only when Navigation Services are installed.
#    #options['message'] = 'message'
#
#    # if you use the multiple file version of the module functions this option is set automatically.
#    #options['multiple'] = 1
#
#    # defining options for opening a directory
#    self.dir_opt = options = {}
#    options['initialdir'] = 'C:\\'
#    options['mustexist'] = False
#    options['parent'] = root
#    options['title'] = 'This is a title'
#
#  def askopenfile(self):
#
#    """Returns an opened file in read mode."""
#
#    return tkFileDialog.askopenfile(mode='r', **self.file_opt)
#
#  def askopenfilename(self):
#
#    """Returns an opened file in read mode.
#    This time the dialog just returns a filename and the file is opened by your own code.
#    """
#
#    # get filename
#    filename = tkFileDialog.askopenfilename(**self.file_opt)
#
#    # open file on your own
#    if filename:
#      return open(filename, 'r')
#
#  def asksaveasfile(self):
#
#    """Returns an opened file in write mode."""
#
#    return tkFileDialog.asksaveasfile(mode='w', **self.file_opt)
#
#  def asksaveasfilename(self):
#
#    """Returns an opened file in write mode.
#    This time the dialog just returns a filename and the file is opened by your own code.
#    """
#
#    # get filename
#    filename = tkFileDialog.asksaveasfilename(**self.file_opt)
#
#    # open file on your own
#    if filename:
#      return open(filename, 'w')
#
#  def askdirectory(self):
#
#    """Returns a selected directoryname."""
#
#    return tkFileDialog.askdirectory(**self.dir_opt)
#

def rstTransform(from_pt, to_pt):
    # adapted from http://elonen.iki.fi/code/misc-notes/2d-rigid-fit/index.html
    # Input points: lists of x/y coordinates as: [[x1,y1],[x2,y2],...]
    # must be at least 2 points in each list
    # returns 'c': coefficients matrix
    
    assert len(from_pt) >= 2
    assert len(to_pt) >= 2
    
    # Fill the matrices
    A_data = []
    # only use as many points from template list as exist in target list
    for pt in from_pt(range(len(to_pt))):
      A_data.append( [-pt[1], pt[0], 1, 0] )
      A_data.append( [ pt[0], pt[1], 0, 1] )
    
    b_data = []
    for pt in to_pt:
      b_data.append(pt[0])
      b_data.append(pt[1])
    
    # Solve
    A = np.matrix( A_data )
    b = np.matrix( b_data ).T
    c = np.linalg.lstsq(A, b)[0].T
    c = np.array(c)[0]
    
    print("Solved coefficients:")
    print(c)
    
    return c

def rstTransform_posList(from_pL, to_pL):
    # adapted from http://elonen.iki.fi/code/misc-notes/2d-rigid-fit/index.html
    # Input points: lists of x/y coordinates as: [[x1,y1],[x2,y2],...]
    # must be at least 2 points in each list
    # returns 'c': coefficients matrix
    
    assert len(from_pL.slicePositions) >= 2
    assert len(to_pL.slicePositions) >= 2
    
    # Fill the matrices
    A_data = []
    # only use as many points from template list as exist in target list
    print "template positions:"
    for index,pos in enumerate(from_pL.slicePositions):
      if index >= len(to_pL.slicePositions): break
      print "%s (x, y): (%f, %f)" %(index, pos.x, pos.y)
      A_data.append( [-pos.y, pos.x, 1, 0] )
      A_data.append( [ pos.x, pos.y, 0, 1] )
    
    b_data = []
    print "target positions:"
    for index,pos in enumerate(to_pL.slicePositions):
      print "%s (x, y): (%f, %f)" %(index, pos.x, pos.y)
      b_data.append(pos.x)
      b_data.append(pos.y)
    
    assert len(A_data) == len(b_data)
    
    # Solve
    A = np.matrix( A_data )
    b = np.matrix( b_data ).T
    c = np.linalg.lstsq(A, b)[0].T
    c = np.array(c)[0]
    
    print("Solved coefficients:")
    print(c)
    
    return c

def getPoints(file):
    # read posList file & get datapoints
    # return list of points as [[x1,y1],[x2,y2],...]
    
    pL = posList(axis = None)
    pL.add_from_file(file)
    
    pt_list = []
    
    for index,pos in enumerate(pL.slicePositions):
        pt_list.append([pos.x,pos.y])
        print ('%d\t[%f,%f]' %(index, pos.x, pos.y))
    
    return pt_list

def savePoints(tform_pt, file):
    pL = posList(axis = None)
    pL.save_position_list()

def applyTform(from_pt, c):
    
    print("Translated 'from_pt':")
    
    tform_pt = []
    
    for pt in from_pt:
        tform_pt_tmp = [c[1]*pt[0] - c[0]*pt[1] + c[2], c[1]*pt[1] + c[0]*pt[0] + c[3]]
        print ("%f, %f" % (tform_pt_tmp[0], tform_pt_tmp[1]))
        tform_pt.append(tform_pt_tmp)
        
    return tform_pt

def applyTform_posList(from_pL, c):
    
    tform_pL = posList(axis = None)
    
    for index,pos in enumerate(from_pL.slicePositions):
        #print index, pos
        tform_x = c[1]*pos.x - c[0]*pos.y + c[2] 
        tform_y = c[1]*pos.y + c[0]*pos.x + c[3]
        #print tform_x, tform_y
        print "%d (x, y):  (%f, %f) --> (%f, %f)" %(index, pos.x, pos.y, tform_x, tform_y)
        tform_pL.add_position(tform_x,tform_y)
        
    return tform_pL
    

#script
if __name__=='__main__':
    #root = Tkinter.Tk()
    #TkFileDialogExample(root).pack()
    #root.mainloop()
    
    options = {}
    options['defaultextension'] = '' # couldn't figure out how this works
    options['filetypes'] = [('csv files', '.csv')]
    options['initialdir'] = '/Users/SJSmith/Documents/Nick Local/data/ISI-Barrels/Ct1-ISI/R55/Imaging-Sessions'
    options['initialfile'] = 'posList.csv'
    #options['parent'] = root
    
    #get input pList (ie. original template to be transformed from)
    options['title'] = 'Select template PositionList file'
    template_csv = tkFileDialog.askopenfilename(**options)
    #template_pt = getPoints(template_csv)

    template_pL = posList(axis = None)
    template_pL.add_from_file(template_csv)
    
    #get target pList (ie. new points from which to calculate transformation)
    options['title'] = 'Select target PositionList file'
    options['initialdir'] = os.path.split(template_csv)[0]
    target_csv = tkFileDialog.askopenfilename(**options)
    #target_pt = getPoints(target_csv)
    
    target_pL = posList(axis = None)
    target_pL.add_from_file(target_csv)
    
    print "Calculating transformation of %s to %s" %(template_csv, target_csv)
    
    #calculate coefficients
    #c = rstTransform(template_pt, target_pt)
    c = rstTransform_posList(template_pL, target_pL)
    #print "Transformation calculated:\n",c
    
    #apply transformation
    #tform_pL = posList(axis = None)
    tform_pL = applyTform_posList(template_pL, c)
    #tform_pt = applyTform(template_pt, c)
    print "Transformation applied to %s" %(template_csv)
    
    #save output pList (ie. template transformed to match target pList)
    options['title'] = 'Select transformed PositionList file'
    options['initialdir'] = os.path.split(target_csv)[0]
    tform_csv = tkFileDialog.asksaveasfilename(**options)
    tform_pL.save_position_list(tform_csv)
    
    print "Transformed plist saved to %s" %(tform_csv)