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
 
import numpy as np
from numpy import sin, pi, cos, arctan, sin, tan, sqrt
from Point import Point
import wx.lib.intctrl
import wx.lib.agw.floatspin    
import csv
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
import PositionList
from matplotlib.lines import Line2D
import matplotlib.ticker as mticker 
import matplotlib.transforms as mtransforms 

class LooseMaxNLocator(mticker.MaxNLocator): 
    """ 
    Select no more than N intervals at nice locations with view 
    limits loosely fitted to the data.  Unlike MaxNLocator, the 
    view limits do not necessarily coincide with tick locations. 
    """ 

    def __init__(self, margin = 0.0, **kwargs): 
        """ 
        Keyword arguments: 
        *margin* 
            Specifies the minimum size of both the lower and upper 
            margins (between the view limits and the data limits) as 
            a fraction of the data range.  Must be non-negative. 
        Remaining keyword arguments are passed to MaxNLocator. 
        """ 
        mticker.MaxNLocator.__init__(self, **kwargs) 
        if margin < 0: 
            raise ValueError('The margin must be non-negative.') 
        self._margin = margin 

    def view_limits(self, dmin, dmax): 
        # begin partial duplication of MaxNLocator.view_limits 
        if self._symmetric: 
            maxabs = max(abs(dmin), abs(dmax)) 
            dmin = -maxabs 
            dmax = maxabs 
        dmin, dmax = mtransforms.nonsingular(dmin, dmax, expander=0.05) 
        # end duplication 
        margin = self._margin * (dmax - dmin)  # fraction of data range 
        vmin = dmin - margin  # expand the view 
        vmax = dmax + margin 
        bin_boundaries = self.bin_boundaries(vmin, vmax) 
            # locate ticks with MaxNLocator 
        # Note: If the lines below change vmin or vmax, the bin boundaries 
        # later calculated by MaxNLocator.__call__ may differ from those 
        # calculated here. 
        vmin = min(vmin, max(bin_boundaries[bin_boundaries <= dmin])) 
            # expand view to the highest tick below or touching the data 
        vmax = max(vmax, min(bin_boundaries[bin_boundaries >= dmax])) 
            # expand view to the lowest tick above or touching the data 
        return np.array([vmin, vmax]) 
        
class Transform():
    """class for storing, applying and fitting linear transformations of 2d points"""
    def __init__(self,matrix=None,disp_vector=None,flipVert=False,flipHoriz=False):

        if not matrix == None:
            self.T=matrix
        else:
            self.T=np.array([[1,0],[0,1]])
        
        if not disp_vector == None:
            self.D=disp_vector
        else:
            self.D=np.array([0,0])
        
        self.flipVert=flipVert;
        self.flipHoriz=flipHoriz;
        
    def transform(self,x,y):
        if self.flipVert:
            y=-y
        if self.flipHoriz:
            x=-x
        vec=np.array([x,y])
        vec_t=np.dot(self.T,vec);
        vec_t=vec_t+self.D;
        # print "point from:"
        # print (x,y)
        # print "point to:"
        # print (vec_t[0],vec_t[1])
        return (vec_t[0],vec_t[1])
    
    def save_settings(self,cfg):
        print "saving_transformation"
        print self.T
        print self.D
        cfg.WriteFloat('trans_M00',self.T[0][0])
        cfg.WriteFloat('trans_M01',self.T[0][1])
        cfg.WriteFloat('trans_M10',self.T[1][0])
        cfg.WriteFloat('trans_M11',self.T[1][1])
        
        cfg.WriteFloat('trans_D0',self.D[0])
        cfg.WriteFloat('trans_D1',self.D[1])
        cfg.WriteBool('trans_flipvert',self.flipVert)
        cfg.WriteBool('trans_fliphoriz',self.flipHoriz)
      
    def load_settings(self,cfg):
        print "loading transform"
        print self.T
        print self.D
        self.T[0,0]=cfg.ReadFloat('trans_M00',1.0)
        self.T[0,1]=cfg.ReadFloat('trans_M01',0.0)
        self.T[1,0]=cfg.ReadFloat('trans_M10',0.0)
        self.T[1,1]=cfg.ReadFloat('trans_M11',1.0)       
        self.D[0]=cfg.ReadFloat('trans_D0',0.0)
        self.D[1]=cfg.ReadFloat('trans_D1',0.0)
        self.flipVert=cfg.ReadBool('trans_flipvert',False)
        self.flipHoriz=cfg.ReadBool('trans_fliphoriz',False)
        print self.T
        print self.D
           
    def set_transform_by_fit(self,from_pts,to_pts,mode='similarity',flipVert=False,flipHoriz=False):
        """set_transform_by_fit(x1,y1,x2,y2,mode='similarity')
        keywords:
        from_pts) a list of Point objects from the original space that correspond in a 1-1 way with the Points in to_pts
        to_pts) a list of Point objects from the new space that correspond in a 1-1 way with the Points in from_pts
        mode) whether these corresponding points should be fit using a 'translation','rigid','similarity' or 'affine' transformation
        'translation' only shifts them in x and y
        'rigid' does translation plus rotation
        'similarity' does rigid plus a scaling factor which is equal in x and y
        'affine' does a fully linear transformation
        default is similarity
        """
        self.flipVert=flipVert
        self.flipHoriz=flipHoriz
        
        if mode=='similarity':
            # Fill the matrices
            A_data = []
            for pt in from_pts:
              if flipVert:
                y=-pt.y
              else:
                y=pt.y
              
              if flipHoriz:
                x=-pt.x
              else:
                x=pt.x
              A_data.append( [-y, x, 1, 0] )
              A_data.append( [ x, y, 0, 1] )

            b_data = []
            for pt in to_pts:
              b_data.append(pt.x)
              b_data.append(pt.y)

            # Solve
            A = np.matrix( A_data )
            b = np.matrix( b_data ).T
            c = np.linalg.lstsq(A, b)[0].T
            c = np.array(c)[0]

            print("Solved coefficients:")
            print(c)

            self.T=[[c[1],-c[0]],[c[0],c[1]]]
            self.D=[c[2],c[3]]
            
        if mode=='translation':
            A_data = []
            for pt in from_pts:
                if flipVert:
                    y=-pt.y
                else:
                    y=pt.y
              
                if flipHoriz:
                    x=-pt.x
                else:
                    x=pt.x
                
                A_data.append( [1, 0] )
                A_data.append( [0, 1] )
            
            b_data = []
            for index,pt in enumerate(to_pts):
                if flipVert:
                    y=-from_pts[index].y
                else:
                    y=from_pts[index].y
              
                if flipHoriz:
                    x=-from_pts[index].x
                else:
                    x=from_pts[index].x
                b_data.append(pt.x-x)
                b_data.append(pt.y-y)    
            
            A = np.matrix( A_data )
            b = np.matrix( b_data ).T
            c = np.linalg.lstsq(A, b)[0].T
            c = np.array(c)[0]
            
            self.T=[[1,0],[0,1]]
            self.D=[c[0],c[1]]
            
    

class TransformCanvasPanel(FigureCanvas):
    """A panel that extends the matplotlib class FigureCanvas for plotting the corresponding points from the two coordinate systems, and their transforms"""
    def __init__(self, parent, **kwargs):
        """keyword the same as standard init function for a FigureCanvas"""
        self.figure = Figure(figsize=(6,4))
        FigureCanvas.__init__(self, parent, -1, self.figure, **kwargs)
        self.canvas = self.figure.canvas
        #format the appearance
        self.figure.set_facecolor((1,1,1))
        self.figure.set_edgecolor((1,1,1))
        self.canvas.SetBackgroundColour('black')   
        
        #add subplots for various things
        self.fromplot = self.figure.add_axes([.05,.05,.45,.92])
        self.toplot = self.figure.add_axes([.55,.05,.45,.92])
        self.fromplot.set_axis_bgcolor('black')
        self.toplot.set_axis_bgcolor('black')
        self.fromplot.yaxis.set_major_locator(LooseMaxNLocator(nbins=5,margin=.125))
        self.fromplot.xaxis.set_major_locator(LooseMaxNLocator(nbins=5,margin=.125))
        #self.toplot.yaxis.set_major_locator(LooseMaxNLocator(nbins=5,margin=.0125))
        #self.toplot.xaxis.set_major_locator(LooseMaxNLocator(nbins=5,margin=.0125))
        
    def plot_points_in_from(self,xx,yy,color='black'):
        self.from_points=Line2D(xx,yy,marker='x',markersize=7,markeredgewidth=1.5,markeredgecolor=color)
        self.fromplot.add_line(self.pointLine2D)
    
    def plot_trans_points(self,xx,yy,color='black'):
        self.trans_points=Line2D(xx,yy,marker='x',markersize=7,markeredgewidth=1.5,markeredgecolor=color)
        self.toplot.add_line(self.trans_points)
        for i in range(len(xx)):
            numTxt = self.toplot.text(xx[i],yy[i],str(i)+"  ",color='g',weight='bold') 
            numTxt.set_visible(True)
            numTxt.set_horizontalalignment('left')
        self.toplot.relim()
        self.toplot.autoscale_view()
        self.draw()
   
    
class ChangeTransform(wx.Dialog):
    """simple dialog for changing the camera settings"""
    
    def initold(self, parent, id, title, transform=None):
        wx.Dialog.__init__(self, parent, id, title, size=(600, 120))
        panel = wx.Panel(self, -1)
        vbox = wx.BoxSizer(wx.VERTICAL)  
        
        self.corresp_label=wx.StaticText(self,id=wx.ID_ANY,label="Correspondance file")
        self.corresp_filepicker=wx.FilePickerCtrl(self,message='Select file with corresponding points list (xf0,yf0,xt0,yt0 \\n xf1,yf1,xt1,yt1\n ...)',\
        path="",name='correspondancePicker',\
        style=wx.FLP_USE_TEXTCTRL, size=wx.Size(200,20),wildcard='*.csv')
        self.corresp_load_button=wx.Button(self,id=wx.ID_ANY,label="Load",name="load correspondance files")
             
        
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.corresp_label,1)
        hbox.Add(self.corresp_filepicker,4, wx.EXPAND)
        hbox.Add(self.corresp_load_button, 1, wx.EXPAND)
      
        self.transtypeBox=wx.ComboBox(self,id=wx.ID_ANY,value='similarity', size=wx.DefaultSize,
           choices=['similarity','rigid','translation','affine'], name='Transformation Type Name')
        self.transtypeBox.SetEditable(False)
        self.flipHoriz = wx.CheckBox(self)
        self.flipVert = wx.CheckBox(self)
        self.flipHoriz.SetValue(False)
        self.flipVert.SetValue(False)
        
        
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)

        hbox2.Add(wx.StaticText(self,id=wx.ID_ANY,label="Transformation Type:"))
        hbox2.Add(self.transtypeBox,border=5);
        hbox2.Add(wx.StaticText(self,id=wx.ID_ANY,label="Vertical flip:"))
        hbox2.Add(self.flipVert)
        hbox2.Add(wx.StaticText(self,id=wx.ID_ANY,label="Horizontal flip:"))
        hbox2.Add(self.flipHoriz)
        #vbox.Add(hbox,1,wx.EXPAND)
        
       
         
        vbox.Add(hbox, 1, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 10)
        vbox.Add(hbox2,1, wx.ALIGN_RIGHT,5)
        self.SetSizer(vbox)

        self.Bind(wx.EVT_BUTTON, self.OnCorrespLoad,self.corresp_load_button)

    def __init__(self, parent, id, title, transform=None):
 
        
        wx.Dialog.__init__(self, parent, id, title, size=(640, 490))
        panel = wx.Panel(self, -1)
        vbox = wx.BoxSizer(wx.VERTICAL)       
        
        #define the array picker components for the from array
        self.fromarray_label=wx.StaticText(self,id=wx.ID_ANY,label="posList from:")
        self.fromarray_filepicker=wx.FilePickerCtrl(self,message='Select an position list containing points in the original coordinate space',\
                                                path="",name='arrayFilePickerCtrl1',\
                                                style=wx.FLP_USE_TEXTCTRL, size=wx.Size(300,100),wildcard='*.*')
        self.fromarray_load_button=wx.Button(self,id=wx.ID_ANY,label="Load",name="load button")
        self.fromarray_formatBox=wx.ComboBox(self,id=wx.ID_ANY,value='AxioVision',\
        size=wx.DefaultSize,choices=['AxioVision','SmartSEM','OMX'], name='File Format For Position List')
        self.fromarray_formatBox.SetEditable(False)
       
        #define a horizontal sizer for them and place the file picker components in there
        self.hbox1=wx.BoxSizer(wx.HORIZONTAL)
        self.hbox1.Add(self.fromarray_label,0)   
        self.hbox1.Add(self.fromarray_filepicker,1) 
        self.hbox1.Add(wx.StaticText(self,id=wx.ID_ANY,label="Format:"))
        self.hbox1.Add(self.fromarray_formatBox,0)
        self.hbox1.Add(self.fromarray_load_button,0)
        
        #define the array picker components for the to array
        self.toarray_label=wx.StaticText(self,id=wx.ID_ANY,label="posList to:")
        self.toarray_filepicker=wx.FilePickerCtrl(self,message='Select an position list containing points in the new coordinate space',\
                                                path="",name='arrayFilePickerCtrl1',\
                                                style=wx.FLP_USE_TEXTCTRL, size=wx.Size(300,100),wildcard='*.*')
        self.toarray_load_button=wx.Button(self,id=wx.ID_ANY,label="Load",name="load button")
        self.toarray_formatBox=wx.ComboBox(self,id=wx.ID_ANY,value='AxioVision',\
        size=wx.DefaultSize,choices=['AxioVision','SmartSEM','OMX'], name='File Format For Position List')
        self.toarray_formatBox.SetEditable(False)
       
        #define a horizontal sizer for them and place the file picker components in there
        self.hbox2=wx.BoxSizer(wx.HORIZONTAL)
        self.hbox2.Add(self.toarray_label,0)   
        self.hbox2.Add(self.toarray_filepicker,1) 
        self.hbox2.Add(wx.StaticText(self,id=wx.ID_ANY,label="Format:"))
        self.hbox2.Add(self.toarray_formatBox,0)
        self.hbox2.Add(self.toarray_load_button,0)
      
        #options for the transformation
        self.fit_transform_button=wx.Button(self,id=wx.ID_ANY,label="FitTransform",name="Fit correspondances to transform")
        self.transtypeBox=wx.ComboBox(self,id=wx.ID_ANY,value='similarity', size=wx.DefaultSize, choices=['similarity','rigid','translation','affine'], name='Transformation Type Name')
        self.transtypeBox.SetEditable(False)
        self.flipHoriz = wx.CheckBox(self)
        self.flipVert = wx.CheckBox(self)
        self.flipHoriz.SetValue(False)
        self.flipVert.SetValue(False)

        self.hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox3.Add(wx.StaticText(self,id=wx.ID_ANY,label="Transformation Type:"))
        self.hbox3.Add(self.transtypeBox,border=5);
        self.hbox3.Add(wx.StaticText(self,id=wx.ID_ANY,label="Vertical flip:"))
        self.hbox3.Add(self.flipVert)
        self.hbox3.Add(wx.StaticText(self,id=wx.ID_ANY,label="Horizontal flip:"))
        self.hbox3.Add(self.flipHoriz)
        self.hbox3.Add(self.fit_transform_button)
        #vbox.Add(hbox,1,wx.EXPAND)
        self.transformCanvas=TransformCanvasPanel(self)  
         
        vbox = wx.BoxSizer(wx.VERTICAL) 
        vbox.Add(self.hbox1, 0, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 5)
        vbox.Add(self.hbox2, 0, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 5)
        vbox.Add(self.hbox3,0, wx.ALIGN_RIGHT,5)
        vbox.Add(self.transformCanvas,1,wx.EXPAND,10)
        self.SetSizer(vbox)

        self.Bind(wx.EVT_BUTTON, self.OnFitTransform,self.fit_transform_button)
        self.Bind(wx.EVT_BUTTON, self.OnFromLoad,self.fromarray_load_button)
        self.Bind(wx.EVT_BUTTON, self.OnToLoad,self.toarray_load_button)

        self.posListFrom=PositionList.posList(self.transformCanvas.fromplot,shownumbers=True)
        self.posListTo=PositionList.posList(self.transformCanvas.toplot,shownumbers=True)
        self.transform=Transform()
        
    def OnFitTransform(self,evt):            
        fromPts=self.posListFrom.getXYpoints()
        toPts=self.posListTo.getXYpoints()
        transType=self.transtypeBox.GetValue()
        flipVert=self.flipVert.GetValue()
        flipHoriz=self.flipHoriz.GetValue()
        self.transform.set_transform_by_fit(fromPts,toPts,mode=transType,flipVert=flipVert,flipHoriz=flipHoriz)
        
        xxt=[]
        yyt=[]
        
        #self.posListTrans=PositionList.posList(self.transformCanvas.toplot,shownumbers=True)
        for index,pt in enumerate(fromPts):
            (xt,yt)=self.transform.transform(pt.x,pt.y)
            xxt.append(xt)
            yyt.append(yt)
            #self.posListTrans.add_position(xt,yt,edgecolor='g',withpoint=True,selected=True)
            print "to points:"
            print (toPts[index].x,toPts[index].y)
            print "trans points:"
            print (xt,yt)
            print "from points:"
            print (pt.x,pt.y)
        
        self.transformCanvas.plot_trans_points(xxt,yyt,color='g')
        
        
    # def OnCorrespLoad(self,evt):
        # filename=self.corresp_filepicker.GetPath()
        # coorespReader = csv.reader(open(filename, 'rb'), delimiter=',', quotechar='#')
        # headerline = coorespReader.next()
        # pts_from=[]
        # pts_to=[]
        # for row in coorespReader:
            # if len(row)==4:
                # (xf,yf,xt,yt)=row
                # print row
                # pts_from.append(Point(float(xf),float(yf)))
                # pts_to.append(Point(float(xt),float(yt)))
                
        # self.pts_from=pts_from
        # self.pts_to=pts_to
    
    def OnFromLoad(self,evt):
        """event handler for the array load button"""
        format=self.fromarray_formatBox.GetValue()
        file=self.fromarray_filepicker.GetPath()
        self.posListFrom.LoadFromFile(file,format)
        self.transformCanvas.fromplot.relim()
        self.transformCanvas.fromplot.autoscale_view()
        self.transformCanvas.draw()
        
    def OnToLoad(self,evt):
        """event handler for the array load button"""
        format=self.toarray_formatBox.GetValue()
        file=self.toarray_filepicker.GetPath()
        self.posListTo.LoadFromFile(file,format)
        self.transformCanvas.toplot.relim()
        self.transformCanvas.toplot.autoscale_view()
        self.transformCanvas.draw()
        
    def getTransform(self):
        return self.transform
