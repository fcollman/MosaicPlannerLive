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
 
import matplotlib.patches

class CenterRectangle(matplotlib.patches.Rectangle):
    """a simple extension of the matplotlib Rectangle class which allows you to specify the center and width/height
    rather than the corner and the width/height of the rectangle"""
    def __init__(self,xy, width, height, **kwargs):
        self.xyc=xy
        (x,y)=xy
        self.l=x-width/2
        self.b=y-height/2
        matplotlib.patches.Rectangle.__init__(self, (self.l,self.b), width, height,**kwargs)   

    def set_center(self,xy):
        """sets a new center point tuple for the rectangle.. do not use set_x and set_y with this class
        as those still specify the corner"""
        self.xyc=xy
        (x,y)=xy
        self.set_x(x-self.get_width()/2)
        self.set_y(y-self.get_height()/2)
    def set_width(self,width):
        """sets the width of this rectangle, and then recalls the setting of the center so that its center stays still"""
        super(type(self), self).set_width(width)
        self.set_center(self.xyc)
    def set_height(self,height):
        """sets the height of this rectangle, and then recalls the set_center so that the center stays still"""
        super(type(self), self).set_height(height)
        self.set_center(self.xyc)  