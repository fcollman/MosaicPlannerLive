class Rectangle():
    def __init__(self,left,right,top,bottom):
        
       
        if left>right:
            self.right=left
            self.left=right
        else:
            self.left=left
            self.right=right
            
        if top>bottom:
            self.top=bottom
            self.bottom=top
        else:
            self.top=top
            self.bottom=bottom
        
    def printRect(self):
        print (self.left,self.right,self.top,self.bottom)
     

    def copyTo(self,other):
        other.left=self.left
        other.right=self.right
        other.top=self.top
        other.bottom=self.bottom
        
    def shift(self,dx=1,dy=1):
        self.left=self.left+dx
        self.right=self.right+dx
        self.top=self.top+dx
        self.bottom=self.bottom+dx
        
    def contains_leftright(self,other_rect):
        if (other_rect.left>self.left) & (other_rect.right<self.right):
            return True
        else:
            return False
        
    def contains_topbottom(self,other_rect):
        if (other_rect.bottom<self.bottom) & (other_rect.top>self.top):
            return True
        else:
            return False
        
    def contains_rect(self,other_rect):
        
        leftright=self.contains_leftright(other_rect)
        updown = self.contains_topbottom(other_rect)
        
        
        if leftright & updown:
            return True
        else:
            return False
    
    def contains_point(self,x,y):
        
        if (x>self.left) & (x<self.right):
            leftright=True
        else:
            leftright=False
        
        if (y<self.bottom) & (y>self.top):
            updown=True
            
        else:
            updown=False
            
        if leftright & updown:
            return True
        else:
            return False
        
        

            
    def overlaps_rect(self,other_rect):
        leftright=False
        updown=False
        if (other_rect.left>self.left)&(other_rect.left<self.right):
            leftright=True
        if (other_rect.right<self.right)&(other_rect.right>self.left):
            leftright=True 
    
        if (other_rect.bottom<self.bottom)&(other_rect.bottom>self.top):
            updown=True
        if (other_rect.top>self.top)&(other_rect.top<self.bottom):
            updown=True 
    
        if leftright & updown:
            return True
        else:
            return False
        
    def get_center(self):
        x=(self.left+self.right)/2
        y=(self.top+self.bottom)/2
        return (x,y)
        
    def get_height(self):
        return self.bottom-self.top
    
    def get_width(self):
        return self.right-self.left
    
        
    def expand_to_include(self,other):
        self.left=min(other.left,self.left)
        self.right=max(other.right,self.right)
        self.bottom=max(other.bottom,self.bottom)
        self.top=min(other.top,self.top)

    def find_relative_bounds(self,inner_rect):
        #returns a rectangle whose bounds are expressed in terms of what fraction
        #of the way through this rectangle do you have to go to find inner_rect
        #this rectangle is constrained to have its left_bound<right_bound and 
        #top<bottom.  So use appropriately.
        rel_rect=inner_rect
        width=self.right-self.left
        height= self.bottom - self.top
        
        rel_rect.left=(rel_rect.left - self.left)/width
        rel_rect.right=(rel_rect.right - self.left)/width
        rel_rect.bottom=(rel_rect.bottom - self.top)/height
        rel_rect.top = (rel_rect.top - self.top)/height
        
        return rel_rect
        
  