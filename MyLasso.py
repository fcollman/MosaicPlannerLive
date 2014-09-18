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
 
from matplotlib.widgets import Lasso
from matplotlib.lines import Line2D

class MyLasso(Lasso):
    """a simple extension of the Lasso widget that allows you to specify the color of the line draw"""
    def __init__(self, ax, xy, callback=None, useblit=True,linecolor='black'):
        """a simple extension of the Lasso widget that allows you to specify the color of the line draw
        
        keywords)
        ax=axis to draw the lasso on
        xy=an x,y tuple with the location of the start
        callback=callback function to call on release of the lasso
        useblit=boolean i don't understand and am just passing through
        linecolor=a string denoting the matplotlib color designation of the lasso
        
        """
        Lasso.__init__(self,ax,xy,callback,useblit)
        #these lines are basic rewrites of lines that existed in the original Lasso init function
        #which ultimately set self.line and make sure that self.line has been added to self.axis via add_line
        x, y = xy
        self.line = Line2D([x],[y],linestyle='-', color=linecolor, lw=2)  
        self.axes.add_line(self.line)