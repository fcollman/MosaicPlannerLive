import numpy

## Copyright (c) 2004-2007, Andrew D. Straw. All rights reserved.

## Redistribution and use in source and binary forms, with or without
## modification, are permitted provided that the following conditions are
## met:

##     * Redistributions of source code must retain the above copyright
##       notice, this list of conditions and the following disclaimer.

##     * Redistributions in binary form must reproduce the above
##       copyright notice, this list of conditions and the following
##       disclaimer in the documentation and/or other materials provided
##       with the distribution.

##     * Neither the name of the Andrew D. Straw nor the names of its
##       contributors may be used to endorse or promote products derived
##       from this software without specific prior written permission.

## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
## "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
## LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
## A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
## OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
## SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
## LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
## DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
## THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
## (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
## OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

def ransac(from_points,to_points,model,n,k,t,d,debug=False,return_all=False):
    """fit model parameters to data using the RANSAC algorithm
    
This implementation written from pseudocode found at
http://en.wikipedia.org/w/index.php?title=RANSAC&oldid=116358182

{{{
Given:
    data - a set of observed data points
    model - a model that can be fitted to data points
    n - the minimum number of data values required to fit the model
    k - the maximum number of iterations allowed in the algorithm
    t - a threshold value for determining when a data point fits a model
    d - the number of close data values required to assert that a model fits well to data
Return:
    bestfit - model parameters which best fit the data (or nil if no good model is found)
iterations = 0
bestfit = nil
besterr = something really large
while iterations < k {
    maybeinliers = n randomly selected values from data
    maybemodel = model parameters fitted to maybeinliers
    alsoinliers = empty set
    for every point in data not in maybeinliers {
        if point fits maybemodel with an error smaller than t
             add point to alsoinliers
    }
    if the number of elements in alsoinliers is > d {
        % this implies that we may have found a good model
        % now test how good it is
        bettermodel = model parameters fitted to all points in maybeinliers and alsoinliers
        thiserr = a measure of how well model fits these points
        if thiserr < besterr {
            bestfit = bettermodel
            besterr = thiserr
        }
    }
    increment iterations
}
return bestfit
}}}
"""
    iterations = 0
    bestfit = None
    besterr = numpy.inf
    bestin = 0
    best_inlier_idxs = None
    N=from_points.shape[0]
    
 
    
    while iterations < k:
        maybe_idxs, test_idxs = random_partition(n,N)
    
        maybeinliers_from = from_points[maybe_idxs,:]
        maybeinliers_to = to_points[maybe_idxs,:]
          
        test_points_from = from_points[test_idxs,:]
        test_points_to = to_points[test_idxs,:]
        maybemodel=model.fit(maybeinliers_from,maybeinliers_to)
        maybe_errs = model.get_error(maybeinliers_from,maybeinliers_to,maybemodel)
        good_errs=maybe_errs[maybe_errs < t]
        if len(good_errs)>n-1: # only proceed if each of the test points meets the inlier criteria
            
            test_err = model.get_error( test_points_from,test_points_to, maybemodel)
        
        
       
            also_idxs = test_idxs[test_err < t] # select indices of rows with accepted points
            alsoinliers_from = from_points[also_idxs,:]
            alsoinliers_to = to_points[also_idxs,:]
         
        
            if len(alsoinliers_from) > d:
                if model.is_valid_transform(maybemodel):
                    #print test_err[test_err < t]
                    betterdata_from = numpy.concatenate( (maybeinliers_from, alsoinliers_from) )
                    
                    betterdata_to = numpy.concatenate( (maybeinliers_to, alsoinliers_to) )
                    bettermodel=model.fit(betterdata_from,betterdata_to)
                    better_errs = model.get_error( betterdata_from,betterdata_to, bettermodel)
                    thiserr = numpy.mean( better_errs )
                    thisin = len(also_idxs)
                    if thisin > bestin:
                        if debug:
                            print better_errs[0:3]
                            print maybe_errs
                            print '\nbetter_errs.min()',better_errs.min()
                            print 'better_errs.max()',better_errs.max()
                            print 'numpy.mean(better_errs)',numpy.mean(better_errs)
                            print 'iteration %d:len(alsoinliers) = %d'%(iterations,len(alsoinliers_from))
                        bestfit = bettermodel
                        besterr = thiserr
                        bestin = thisin
                        best_inlier_idxs = numpy.concatenate( (maybe_idxs, also_idxs) )
        iterations+=1
    if bestfit is None:
        return None, []
    if return_all:
        
        return bestfit, best_inlier_idxs
    else:
        return bestfit

def random_partition(n,n_data):
    """return n random rows of data (and also the other len(data)-n rows)"""
    all_idxs = numpy.arange( n_data )
    numpy.random.shuffle(all_idxs)
    idxs1 = all_idxs[:n]
    idxs2 = all_idxs[n:]
    return idxs1, idxs2

class LinModel:
    def __init__(self,t=None,R=None):
        self.t=t
        self.R=R
        
class LinearModel:
    def __init__(self, debug= False):
        self.debug = debug
        

    def fit(self, from_points,to_points):
      
        t = numpy.zeros((1,from_points.shape[1]))
        R = numpy.eye(from_points.shape[1])
        return LinModel(t,R)
        
    def get_error( self, from_points,to_points,model):
    
        transformed_from_points=self.transform_points(from_points,model)
     
        # sum squared error per row
        err_per_point = numpy.sqrt(numpy.sum((transformed_from_points-to_points)**2,axis=1))
        
        return err_per_point
        
    def transform_points(self,from_points,model):
        N=from_points.shape[0]
        
     
        rot_points=(numpy.dot(model.R,from_points.T)).T
        transformed_from_points = rot_points + numpy.tile(model.t, (N, 1))
        return transformed_from_points
        
    def calc_angle(self,model):
        R=model.R;
        print R
        
    def is_valid_transform(self,model):
        return True

class TranslationModel(LinearModel):
    """transform between two N dimensional vector spaces using a simple translation"""
    
    def __init__(self, debug= False):
        LinearModel.__init__(self,debug)
      
        
    def fit(self, from_points,to_points):
        
        t = numpy.mean(to_points-from_points,0);
        R = numpy.eye(from_points.shape[1]) 
        return LinModel(t,R)
        
class RigidModel(LinearModel):
    """transform between two N dimensional vector spaces using a rigid tranformation"""
    
    def __init__(self, debug= False):
        LinearModel.__init__(self,debug)
            
    def fit(self, A,B):
        assert len(A) == len(B)

        N = A.shape[0]; # total points

        centroid_A = numpy.mean(A, axis=0)
        centroid_B = numpy.mean(B, axis=0)
        
        # centre the points
        AA = A - numpy.tile(centroid_A, (N, 1))
        BB = B - numpy.tile(centroid_B, (N, 1))

        # dot is matrix multiplication for array
        H = numpy.dot(numpy.transpose(AA) , BB)

        U, S, Vt = numpy.linalg.svd(H)

        R = numpy.dot( Vt.T , U.T)

        # special reflection case
        if numpy.linalg.det(R) < 0:
           #print "Reflection detected"
           #print Vt.shape
           Vt[-1,:] *= -1
           R = numpy.dot( Vt.T , U.T)

        
        t = -numpy.dot(R,centroid_A.T).T + centroid_B.T
        #print ("centroid_A",centroid_A)       
        #print ("t",t)
        return LinModel(t,R)
        

       
       
class SimilarityModel(LinearModel):
    """transform between two N dimensional vector spaces using a rigid tranformation"""
    
    def __init__(self, debug= False):
        LinearModel.__init__(self,debug)
        
    def fit(self, from_points,to_points):
        
        t=numpy.mean(to_points-from_points,1);
        R = numpy.eye(from_points.shape[1]) 
        return LinModel(t,R)


class AffineModel(LinearModel):


    def __init__(self, max_det_change=.25,debug= False):
        self.max_det_change=max_det_change
        LinearModel.__init__(self,debug)
        
    def fit(self, A,B):
        assert len(A) == len(B)

        N = A.shape[0]; # total points
        
        M= numpy.zeros((2*N,6))
        Y = numpy.zeros((2*N,1))
        for i in range(N):
            M[2*i,:]=[A[i,0],A[i,1],0,0,1,0]
            M[2*i+1,:]=[0,0,A[i,0],A[i,1],0,1]
            Y[2*i]=B[i,0]
            Y[2*i+1]=B[i,1]
            
        (Tvec,residuals,rank,s)=numpy.linalg.lstsq(M,Y)
              
        
        t=numpy.array([Tvec[4,0],Tvec[5,0]])
        R = numpy.array([[Tvec[0,0],Tvec[1,0]],[Tvec[2,0],Tvec[3,0]]])
        
        return LinModel(t,R)
        
    def is_valid_transform(self,model):
        if numpy.abs(numpy.linalg.det(model.R)-1)>self.max_det_change:
            return False
        else:
            return True
        
        
class LinearLeastSquaresModel:
    """linear system solved using linear least squares

    This class serves as an example that fulfills the model interface
    needed by the ransac() function.
    
    """
    def __init__(self,input_columns,output_columns,debug=False):
        self.input_columns = input_columns
        self.output_columns = output_columns
        self.debug = debug
    def fit(self, data):
        A = numpy.vstack([data[:,i] for i in self.input_columns]).T
        B = numpy.vstack([data[:,i] for i in self.output_columns]).T
        x,resids,rank,s = scipy.linalg.lstsq(A,B)
        return x
    def get_error( self, data, model):
        A = numpy.vstack([data[:,i] for i in self.input_columns]).T
        B = numpy.vstack([data[:,i] for i in self.output_columns]).T
        B_fit = scipy.dot(A,model)
        err_per_point = numpy.sum((B-B_fit)**2,axis=1) # sum squared error per row
        return err_per_point

