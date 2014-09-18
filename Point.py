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
 
from numpy import sin, cos

class Point():
    """a simple class for 2d geometric points/vectors
    
    keywords
    x) the x position 
    y) the y position
    
    """
    def __init__(self,x,y):
        """a simple class for 2d geometric points/vectors

        keywords
        x) the x position 
        y) the y position
        
        """
        self.x=x
        self.y=y
        
    def __add__(self, other):
        """Add two Points geometrically"""
        if isinstance(other, Point):
            return Point(self.x+other.x,self.y+other.y)
    def __sub__(self, other):
        """Subtract two Points geometrically"""
        if isinstance(other, Point):
            return Point(self.x-other.x,self.y-other.y)
    def rotate_around(self,other,angle=0):
        """Rotate this point around another point
        
        Keywords:
        other)the point to rotate this point around
        angle)the angle in radians to rotate it
        
        """
        if isinstance(other,Point):
            dv=self-other
            dv.rotate(angle)
            return other+dv
        
    def rotate(self,angle):
        """rotate this point around 0,0 by angle degrees
        
        Keywords:
        angle)the angle to rotate this point in radians
        
        """
        nx=self.x*cos(angle)-self.y*sin(angle)
        ny=self.x*sin(angle)+self.y*cos(angle)
        self.x=nx
        self.y=ny
        return Point(nx,ny)
    