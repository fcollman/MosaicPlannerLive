import numpy as np
from scipy.ndimage import convolve

# Try and use the faster Fourier transform functions from the anfft module if
# available
try:
	from pyfftw.interfaces.scipy_fftpack import fftn, ifftn
# Otherwise use the normal scipy fftpack ones instead (~2-3x slower!)
except ImportError:
	print \
	"Module 'pyfftw' (FFTW Python bindings) could not be imported.\n"\
	"To install it, try running 'pip install pyfftw' from the terminal.\n"\
	"Falling back on the slower 'fftpack' module for ND Fourier transforms."
	from scipy.fftpack import fftn, ifftn

class TemplateMatch(object):
	"""
	N-dimensional template search by normalized cross-correlation or sum of
	squared differences.

	Arguments:
	------------------------
		template 	The template to search for
		method 		The search method. Can be "ncc", "ssd" or 
				"both". See documentation for norm_xcorr and 
				fast_ssd for more details.

	Example use:
	------------------------
	from scipy.misc import lena
	from matplotlib.pyplot import subplots

	image = lena()
	template = image[240:281,240:281]
	TM = TemplateMatch(template,method='both')
	ncc,ssd = TM(image)
	nccloc = np.nonzero(ncc == ncc.max())
	ssdloc = np.nonzero(ssd == ssd.min())

	fig,[[ax1,ax2],[ax3,ax4]] = subplots(2,2,num='ND Template Search')
	ax1.imshow(image,interpolation='nearest')
	ax1.set_title('Search image')
	ax2.imshow(template,interpolation='nearest')
	ax2.set_title('Template')
	ax3.hold(True)
	ax3.imshow(ncc,interpolation='nearest')
	ax3.plot(nccloc[1],nccloc[0],'w+')
	ax3.set_title('Normalized cross-correlation')
	ax4.hold(True)
	ax4.imshow(ssd,interpolation='nearest')
	ax4.plot(ssdloc[1],ssdloc[0],'w+')
	ax4.set_title('Sum of squared differences')
	fig.tight_layout()
	fig.canvas.draw()
	"""
	def __init__(self,template,method='ssd'):

		if method not in ['ncc','ssd','both']:
			raise Exception('Invalid method "%s". '\
					'Valid methods are "ncc", "ssd" or "both"'
					%method)

		self.template = template
		self.method = method

	def __call__(self,a):

		if a.ndim != self.template.ndim:
			raise Exception('Input array must have the same number '\
					'of dimensions as the template (%i)'
					%self.template.ndim)

		if self.method == 'ssd':
			return self.fast_ssd(self.template,a,trim=True)
		elif self.method == 'ncc':
			return norm_xcorr(self.template,a,trim=True)
		elif self.method == 'both':
			return norm_xcorr(self.template,a,trim=True,do_ssd=True)

def norm_xcorr(t,a,method=None,trim=True,do_ssd=False):
	"""
	Fast normalized cross-correlation for n-dimensional arrays

	Inputs:
	----------------
		t 	The template. Must have at least 2 elements, which 
			cannot all be equal.

		a 	The search space. Its dimensionality must match that of 
			the template.

		method 	The convolution method to use when computing the 
			cross-correlation. Can be either 'direct', 'fourier' or
			None. If method == None (default), the convolution time 
			is estimated for both methods and the best one is chosen
			for the given input array sizes.

		trim 	If True (default), the output array is trimmed down to  
			the size of the search space. Otherwise, its size will  
			be (f.shape[dd] + t.shape[dd] -1) for dimension dd.

		do_ssd 	If True, the sum of squared differences between the 
			template and the search image will also be calculated.
			It is very efficient to calculate normalized 
			cross-correlation and the SSD simultaneously, since they
			require many of the same quantities.

	Output:
	----------------
		nxcorr 	An array of cross-correlation coefficients, which may  
			vary from -1.0 to 1.0.
		[ssd] 	[Returned if do_ssd == True. See fast_ssd for details.]

	Wherever the search space has zero  variance under the template,
	normalized  cross-correlation is undefined. In such regions, the
	correlation coefficients are set to zero.

	References:
		Hermosillo et al 2002: Variational Methods for Multimodal Image
		Matching, International Journal of Computer Vision 50(3),
		329-343, 2002
		<http://www.springerlink.com/content/u4007p8871w10645/>

		Lewis 1995: Fast Template Matching, Vision Interface, 
		p.120-123, 1995
		<http://www.idiom.com/~zilla/Papers/nvisionInterface/nip.html>

		<http://en.wikipedia.org/wiki/Cross-correlation#Normalized_cross-correlation>

	Alistair Muldal
	Department of Pharmacology
	University of Oxford
	<alistair.muldal@pharm.ox.ac.uk>

	Sept 2012

	"""

	if t.size < 2:
		raise Exception('Invalid template')
	if t.size > a.size:
		raise Exception('The input array must be smaller than the template')

	std_t,mean_t = np.std(t),np.mean(t)

	if std_t == 0:
		raise Exception('The values of the template must not all be equal')

	t = np.float64(t)
	a = np.float64(a)

	# output dimensions of xcorr need to match those of local_sum
	outdims = np.array([a.shape[dd]+t.shape[dd]-1 for dd in xrange(a.ndim)])

	# would it be quicker to convolve in the spatial or frequency domain? NB
	# this is not very accurate since the speed of the Fourier transform
	# varies quite a lot with the output dimensions (e.g. 2-radix case)
	if method == None:
		spatialtime, ffttime = get_times(t,a,outdims)
		if spatialtime < ffttime:
			method = 'spatial'
		else:
			method = 'fourier'

	if method == 'fourier':
		# # in many cases, padding the dimensions to a power of 2
		# # *dramatically* improves the speed of the Fourier transforms
		# # since it allows using radix-2 FFTs
		# fftshape = [nextpow2(ss) for ss in a.shape]

		# Fourier transform of the input array and the inverted template

		# af = fftn(a,shape=fftshape)
		# tf = fftn(ndflip(t),shape=fftshape)

		af = fftn(a,shape=outdims)
		tf = fftn(ndflip(t),shape=outdims)

		# 'non-normalized' cross-correlation
		xcorr = np.real(ifftn(tf*af))

	else:
		xcorr = convolve(a,t,mode='constant',cval=0)

	# local linear and quadratic sums of input array in the region of the
	# template
	ls_a = local_sum(a,t.shape)
	ls2_a = local_sum(a**2,t.shape)

	# now we need to make sure xcorr is the same size as ls_a
	xcorr = procrustes(xcorr,ls_a.shape,side='both')

	# local standard deviation of the input array
	ls_diff = ls2_a - (ls_a**2)/t.size
	ls_diff = np.where(ls_diff < 0,0,ls_diff)
	sigma_a = np.sqrt(ls_diff)

	# standard deviation of the template
	sigma_t = np.sqrt(t.size-1.)*std_t

	# denominator: product of standard deviations
	denom = sigma_t*sigma_a

	# numerator: local mean corrected cross-correlation
	numer = (xcorr - ls_a*mean_t)

	# sigma_t cannot be zero, so wherever the denominator is zero, this must
	# be because sigma_a is zero (and therefore the normalized cross-
	# correlation is undefined), so set nxcorr to zero in these regions
	tol = np.sqrt(np.finfo(denom.dtype).eps)
	nxcorr = np.where(denom < tol,0,numer/denom)

	# if any of the coefficients are outside the range [-1 1], they will be
	# unstable to small variance in a or t, so set them to zero to reflect
	# the undefined 0/0 condition
	nxcorr = np.where(np.abs(nxcorr-1.) > np.sqrt(np.finfo(nxcorr.dtype).eps),nxcorr,0)

	# calculate the SSD if requested
	if do_ssd:
		# quadratic sum of the template
		tsum2 = np.sum(t**2.)

		# SSD between template and image
		ssd = ls2_a + tsum2 - 2.*xcorr

		# normalise to between 0 and 1
		ssd -= ssd.min()
		ssd /= ssd.max()

		if trim:
			nxcorr = procrustes(nxcorr,a.shape,side='both')
			ssd = procrustes(ssd,a.shape,side='both')
		return nxcorr,ssd

	else:
		if trim:
			nxcorr = procrustes(nxcorr,a.shape,side='both')
		return nxcorr

def fast_ssd(t,a,method=None,trim=True):
	"""

	Fast sum of squared differences (SSD block matching) for n-dimensional
	arrays

	Inputs:
	----------------
		t 	The template. Must have at least 2 elements, which 
			cannot all be equal.

		a 	The search space. Its dimensionality must match that of 
			the template.

		method 	The convolution method to use when computing the 
			cross-correlation. Can be either 'direct', 'fourier' or
			None. If method == None (default), the convolution time 
			is estimated for both methods and the best one is chosen
			for the given input array sizes.

		trim 	If True (default), the output array is trimmed down to  
			the size of the search space. Otherwise, its size will  
			be (f.shape[dd] + t.shape[dd] -1) for dimension dd.

	Output:
	----------------
		ssd 	An array containing the sum of squared differences 
			between the image and the template, with the values
			normalized in the range -1.0 to 1.0.

	Wherever the search space has zero  variance under the template,
	normalized  cross-correlation is undefined. In such regions, the
	correlation coefficients are set to zero.

	References:
		Hermosillo et al 2002: Variational Methods for Multimodal Image
		Matching, International Journal of Computer Vision 50(3),
		329-343, 2002
		<http://www.springerlink.com/content/u4007p8871w10645/>

		Lewis 1995: Fast Template Matching, Vision Interface, 
		p.120-123, 1995
		<http://www.idiom.com/~zilla/Papers/nvisionInterface/nip.html>


	Alistair Muldal
	Department of Pharmacology
	University of Oxford
	<alistair.muldal@pharm.ox.ac.uk>

	Sept 2012

	"""

	if t.size < 2:
		raise Exception('Invalid template')
	if t.size > a.size:
		raise Exception('The input array must be smaller than the template')

	std_t,mean_t = np.std(t),np.mean(t)

	if std_t == 0:
		raise Exception('The values of the template must not all be equal')

	# output dimensions of xcorr need to match those of local_sum
	outdims = np.array([a.shape[dd]+t.shape[dd]-1 for dd in xrange(a.ndim)])

	# would it be quicker to convolve in the spatial or frequency domain? NB
	# this is not very accurate since the speed of the Fourier transform
	# varies quite a lot with the output dimensions (e.g. 2-radix case)
	if method == None:
		spatialtime, ffttime = get_times(t,a,outdims)
		if spatialtime < ffttime:
			method = 'spatial'
		else:
			method = 'fourier'

	if method == 'fourier':
		# # in many cases, padding the dimensions to a power of 2
		# # *dramatically* improves the speed of the Fourier transforms
		# # since it allows using radix-2 FFTs
		# fftshape = [nextpow2(ss) for ss in a.shape]

		# Fourier transform of the input array and the inverted template

		# af = fftn(a,shape=fftshape)
		# tf = fftn(ndflip(t),shape=fftshape)

		af = fftn(a,shape=outdims)
		tf = fftn(ndflip(t),shape=outdims)

		# 'non-normalized' cross-correlation
		xcorr = np.real(ifftn(tf*af))

	else:
		xcorr = convolve(a,t,mode='constant',cval=0)

	# quadratic sum of the template
	tsum2 = np.sum(t**2.)

	# local quadratic sum of input array in the region of the template
	ls2_a = local_sum(a**2,t.shape)

	# now we need to make sure xcorr is the same size as ls2_a
	xcorr = procrustes(xcorr,ls2_a.shape,side='both')

	# SSD between template and image
	ssd = ls2_a + tsum2 - 2.*xcorr

	# normalise to between 0 and 1
	ssd -= ssd.min()
	ssd /= ssd.max()

	if trim:
		ssd = procrustes(ssd,a.shape,side='both')

	return ssd


def local_sum(a,tshape):
	"""For each element in an n-dimensional input array, calculate
	the sum of the elements within a surrounding region the size of
	the template"""

	# zero-padding
	a = ndpad(a,tshape)

	# difference between shifted copies of an array along a given dimension
	def shiftdiff(a,tshape,shiftdim):
		ind1 = [slice(None,None),]*a.ndim
		ind2 = [slice(None,None),]*a.ndim
		ind1[shiftdim] = slice(tshape[shiftdim],a.shape[shiftdim]-1)
		ind2[shiftdim] = slice(0,a.shape[shiftdim]-tshape[shiftdim]-1)
		return a[ind1] - a[ind2]

	# take the cumsum along each dimension and subtracting a shifted version
	# from itself. this reduces the number of computations to 2*N additions
	# and 2*N subtractions for an N-dimensional array, independent of its
	# size.
	#
	# See:
	# <http://www.idiom.com/~zilla/Papers/nvisionInterface/nip.html>
	for dd in xrange(a.ndim):
		a = np.cumsum(a,dd)
		a = shiftdiff(a,tshape,dd)
	return a

# # for debugging purposes, ~10x slower than local_sum for a (512,512) array
# def slow_2D_local_sum(a,tshape):
# 	out = np.zeros_like(a)
# 	for ii in xrange(a.shape[0]):
# 		istart = np.max((0,ii-tshape[0]//2))
# 		istop = np.min((a.shape[0],ii+tshape[0]//2+1))
# 		for jj in xrange(a.shape[1]):
# 			jstart = np.max((0,jj-tshape[1]//2))
# 			jstop = np.min((a.shape[1],jj+tshape[0]//2+1))
# 			out[ii,jj] = np.sum(a[istart:istop,jstart:jstop])
# 	return out

def get_times(t,a,outdims):

	k_conv = 1.21667E-09
	k_fft = 2.65125E-08

	# # uncomment these lines to measure timing constants
	# k_conv,k_fft,convreps,fftreps = benchmark(t,a,outdims,maxtime=60)
	# print "-------------------------------------"
	# print "Template size:\t\t%s" %str(t.shape)
	# print "Search space size:\t%s" %str(a.shape)
	# print "k_conv:\t%.6G\treps:\t%s" %(k_conv,str(convreps))
	# print "k_fft:\t%.6G\treps:\t%s" %(k_fft,str(fftreps))
	# print "-------------------------------------"

	# spatial convolution time scales with the total number of elements
	convtime = k_conv*(t.size*a.size)

	# Fourier convolution time scales with N*log(N), cross-correlation
	# requires 2x FFTs and 1x iFFT. ND FFT time scales with
	# prod(dimensions)*log(prod(dimensions))
	ffttime = 3*k_fft*(np.prod(outdims)*np.log(np.prod(outdims)))

	# print 	"Predicted spatial:\t%.6G\nPredicted fourier:\t%.6G" %(convtime,ffttime)
	return convtime,ffttime

def benchmark(t,a,outdims,maxtime=60):
	import resource

	# benchmark spatial convolutions
	# ---------------------------------
	convreps = 0
	tic = resource.getrusage(resource.RUSAGE_SELF).ru_utime
	toc = tic
	while (toc-tic) < maxtime:
		convolve(a,t,mode='constant',cval=0)
		# xcorr = convolve(a,t,mode='full')
		convreps += 1
		toc = resource.getrusage(resource.RUSAGE_SELF).ru_utime
	convtime = (toc-tic)/convreps

	# convtime == k(N1+N2)
	N = t.size*a.size
	k_conv = convtime/N

	# benchmark 1D Fourier transforms
	# ---------------------------------
	veclist = [np.random.randn(ss) for ss in outdims]
	fft1times = []
	fftreps = []
	for vec in veclist:
		reps = 0
		tic = resource.getrusage(resource.RUSAGE_SELF).ru_utime
		toc = tic
		while (toc-tic) < maxtime:
			fftn(vec)
			toc = resource.getrusage(resource.RUSAGE_SELF).ru_utime
			reps += 1
		fft1times.append((toc-tic)/reps)
		fftreps.append(reps)
	fft1times = np.asarray(fft1times)

	# fft1_time == k*N*log(N)
	N = np.asarray([vec.size for vec in veclist])
	k_fft = np.mean(fft1times/(N*np.log(N)))

	# # benchmark ND Fourier transforms
	# # ---------------------------------
	# arraylist = [t,a]
	# fftntimes = []
	# fftreps = []
	# for array in arraylist:
	# 	reps = 0
	# 	tic = resource.getrusage(resource.RUSAGE_SELF).ru_utime
	# 	toc = tic
	# 	while (toc-tic) < maxtime:
	# 		fftn(array,shape=a.shape)
	# 		reps += 1
	# 		toc = resource.getrusage(resource.RUSAGE_SELF).ru_utime
	# 	fftntimes.append((toc-tic)/reps)
	# 	fftreps.append(reps)
	# fftntimes = np.asarray(fftntimes)

	# # fftn_time == k*prod(dimensions)*log(prod(dimensions)) for an M-dimensional array
	# nlogn = np.array([aa.size*np.log(aa.size) for aa in arraylist])
	# k_fft = np.mean(fftntimes/nlogn)

	return k_conv,k_fft,convreps,fftreps
	# return k_conv,k_fft1,k_fftn


def ndpad(a,npad=None,padval=0):
	"""
	Pads the edges of an n-dimensional input array with a constant value
	across all of its dimensions.

	Inputs:
	----------------
		a 	The array to pad

		npad* 	The pad width. Can either be array-like, with one 
			element per dimension, or a scalar, in which case the 
			same pad width is applied to all dimensions.

		padval	The value to pad with. Must be a scalar (default is 0).

	Output:
	----------------
		b 	The padded array

	*If npad is not a whole number, padding will be applied so that the
	'left' edge of the output is padded less than the 'right', e.g.:

		a 		== np.array([1,2,3,4,5,6])
		ndpad(a,1.5) 	== np.array([0,1,2,3,4,5,6,0,0])

	In this case, the average pad width is equal to npad (but if npad was
	not a multiple of 0.5 this would not still hold). This is so that ndpad
	can be used to pad an array out to odd final dimensions.
	"""

	if npad == None:
		npad = np.ones(a.ndim)
	elif np.isscalar(npad):
		npad = (npad,)*a.ndim
	elif len(npad) != a.ndim:
		raise Exception('Length of npad (%i) does not match the '\
				'dimensionality of the input array (%i)' 
				%(len(npad),a.ndim))

	# initialise padded output
	padsize = [a.shape[dd]+2*npad[dd] for dd in xrange(a.ndim)]
	b = np.ones(padsize,a.dtype)*padval

	# construct an N-dimensional list of slice objects
	ind = [slice(np.floor(npad[dd]),a.shape[dd]+np.floor(npad[dd])) for dd in xrange(a.ndim)]

	# fill in the non-pad part of the array
	b[ind] = a
	return b

# def ndunpad(b,npad=None):
# 	"""
# 	Removes padding from each dimension of an n-dimensional array (the
# 	reverse of ndpad)

# 	Inputs:
# 	----------------
# 		b 	The array to unpad

# 		npad* 	The pad width. Can either be array-like, with one 
# 			element per dimension, or a scalar, in which case the 
# 			same pad width is applied to all dimensions.

# 	Output:
# 	----------------
# 		a 	The unpadded array

#         *If npad is not a whole number, padding will be removed assuming that
# 	the 'left' edge of the output is padded less than the 'right', e.g.:

# 		b 		== np.array([0,1,2,3,4,5,6,0,0])
# 		ndpad(b,1.5) 	== np.array([1,2,3,4,5,6])

# 	This is consistent with the behaviour of ndpad.
# 	"""
# 	if npad == None:
# 		npad = np.ones(b.ndim)
# 	elif np.isscalar(npad):
# 		npad = (npad,)*b.ndim
# 	elif len(npad) != b.ndim:
# 		raise Exception('Length of npad (%i) does not match the '\
# 				'dimensionality of the input array (%i)' 
# 				%(len(npad),b.ndim))
# 	ind = [slice(np.floor(npad[dd]),b.shape[dd]-np.ceil(npad[dd])) for dd in xrange(b.ndim)]
# 	return b[ind]

def procrustes(a,target,side='both',padval=0):
	"""
	Forces an array to a target size by either padding it with a constant or
	truncating it

	Arguments:
		a 	Input array of any type or shape
		target 	Dimensions to pad/trim to, must be a list or tuple
	"""

	try:
		if len(target) != a.ndim:
			raise TypeError('Target shape must have the same number of dimensions as the input')
	except TypeError:
		raise TypeError('Target must be array-like')

	try:
		b = np.ones(target,a.dtype)*padval
	except TypeError:
		raise TypeError('Pad value must be numeric')
	except ValueError:
		raise ValueError('Pad value must be scalar')

	aind = [slice(None,None)]*a.ndim
	bind = [slice(None,None)]*a.ndim

	# pad/trim comes after the array in each dimension
	if side == 'after':
		for dd in xrange(a.ndim):
			if a.shape[dd] > target[dd]:
				aind[dd] = slice(None,target[dd])
			elif a.shape[dd] < target[dd]:
				bind[dd] = slice(None,a.shape[dd])

	# pad/trim comes before the array in each dimension
	elif side == 'before':
		for dd in xrange(a.ndim):
			if a.shape[dd] > target[dd]:
				aind[dd] = slice(a.shape[dd]-target[dd],None)
			elif a.shape[dd] < target[dd]:
				bind[dd] = slice(target[dd]-a.shape[dd],None)

	# pad/trim both sides of the array in each dimension
	elif side == 'both':
		for dd in xrange(a.ndim):
			if a.shape[dd] > target[dd]:
				diff = (a.shape[dd]-target[dd])/2.
				aind[dd] = slice(np.floor(diff),a.shape[dd]-np.ceil(diff))
			elif a.shape[dd] < target[dd]:
				diff = (target[dd]-a.shape[dd])/2.
				bind[dd] = slice(np.floor(diff),target[dd]-np.ceil(diff))
	
	else:
		raise Exception('Invalid choice of pad type: %s' %side)

	b[bind] = a[aind]

	return b

def ndflip(a):
	"""Inverts an n-dimensional array along each of its axes"""
	ind = (slice(None,None,-1),)*a.ndim
	return a[ind]

# def nextpow2(n):
# 	"""get the next power of 2 that's greater than n"""
# 	m_f = np.log2(n)
# 	m_i = np.ceil(m_f)
# 	return 2**m_i