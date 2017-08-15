import numpy as np

def image_16bit_to_8bit(img_16bit, autoscale=False):
    """
    Algorithm to convert a 16bit image to an 8bit image with optional
        autoscaling.

    Args:
        img_16bit (numpy.ndarray): 2d image to convert.
        autoscale (bool): whether to automatically scale the image contrast

    Returns:
        numpy.ndarray: an 8bit image.

    """
    img_32 = np.array(img_16bit, dtype=np.uint32)

    if autoscale:
        min_intensity = np.min(img_32)
        img_32 -= min_intensity
        max_intensity = np.max(img_32)
    else:
        max_intensity = 65535
    return (img_32*255.0/max_intensity).astype(np.uint8)

def make_thumbnail(img, bin=2, autoscale=True):
    """ Makes a thumbnail from an image by subsampling.

    args:
        img (numpy.ndarray): image data
        bin (Optional[int]): binning, default is 2

    returns:
        numpy.ndarray: thumbnail img data

    """
    if bin > 1:
        img = img[::bin,::bin]
    if img.dtype == np.uint16:
        img = image_16bit_to_8bit(img, autoscale=autoscale)
    return img