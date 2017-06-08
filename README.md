# MosaicPlannerLive 

MosaicPlannerLive is a python based GUI program for acquiring array tomography data using MicroManager as an interface.

MosaicPlannerLive is based upon MosaicPlanner, a program that was developed for analyzing large mosaic images,
in order to set up position list files to be used in other automated microscopy software, such as AxioVision (Zeiss), Zen (Zeiss),
OMX (GE Healthcare), SmartSEM (Zeiss), MicroManager Studio (HHMI), etc.

MosaicPlannerLive has some of the same GUI interface elements, but uses the Micromanager API, to also execute the acquisition of data.
It's development is ongoing, but it's goal is to streamline the acquisition of Array Tomography datasets using the diversity of microscope components that MicroManager supports.


#Instructions


## Navigating around the image
You can use the first 4 buttons of the toolbar to navigate around the large mosaic.

The home button: Will return the main plot to its default zoom position where the entire image is visible.

The back/forward button: Will change the zoom to the previous/next view that you were using

The pan button (4 arrows): Allows you to click and drag the center of the plot around your screen.

The zoom button (magnifying glass): Clicking and dragging will define a rectangle to zoom the plot to.

## Creating a position list
You can create and edit a position list from scratch if you do not have one preloaded.

To do so, start by adding a point to you list with the add tool (The pointer with a plus arrow).  You can zoom in to position it precisely on a section.  Add a second point in an adjacent section at approximately the same position.

Select the first point as point 1 by clicking the tool with the pointer with the 1 next to it, and then clicking near the first point.

Select the second point as point 2 by clicking the tool with the pointer with the 2 next to it, and then clicking near the second point.

Now use the Correlation Correction (CorrTool) for short, to fine tune the position of point 2 to make it closer to where you placed point 1, based upon the correlations in the image.  The program at this point goes back to the original image file and loads up smaller cutouts of the image at the full resolution around point 1 and point 2.  Those cutouts are plotted in the first two subplots below the main plot.  The units of the axis both being pixels relative the location of the point.  The 2 dimensional cross correlation between the two cutouts is plotted in the third subplot with units of Pearson's correlation (-1-1), but the colorrange has been restricted to 0-.5.  A red dot is placed on top of the shift which produces the maximal correlation.  Also, over the cutout of the first point for which the correlation appears to have found the position which corresponds to the cutout of point 2 there is a red box.  One can visually assess the quality of the fit by looking at the point 2 cutout relative to the red box in the point 1 cutout, or by looking at the intensity of the correlation.

Next, use the step tool (The green play button) to find the next section.  The step tool will first make a guess as to where the section is based upon adding the vector from 1 to 2 to point 2.  Then it will automatically redefine point 1 and point 2 and call the CorrTool to fine tune the position of point 2.

You can also use use the fast forward tool (the blue double arrow to the right) which will continually run the step tool over and over, and only stop when the correlation of the maximal shift drops below .3. At that point the program will popup a dialog and make a bing, prompting the user to help.  You can look at the fit by eye, and decided to continue by clicking the fast forward button again, or reposition some of the points before trying to continue.  We will discuss the ways to do this below.

## Moving and editing positions
The program has a few functions for repositioning points.  

The most common thing you might want to do is manually reposition a point, based upon what you see in the Point1/Point2 preview boxes during the correlation analysis.  If you simply left click in the Point1 or Point2 preview boxes, the position of that point will be moved to where you clicked.  This makes it easy to manually fine tune the location of points if the correlation tool makes a mistake for some reason.  Note each time you select a new point as point 1 or 2, it will update that preview box, allowing you to do this adjustment.

If you want to move multiple points around by the same amount, you first need to select them.  

You can select points in one of two ways, either with the direct select tool (The big blue arrow pointer) or the lasso tool (the rope icon).

To use the lasso tool, simply click the lasso tool on, then click and drag a freeform area around the main plot.  All the points inside the shape you drew will be selected, and all those outside will not be selected.

The direct select tool will simply select the point closest to the point on the plot that you click (and unselect the rest).  Holding down the shift key while you click will simply add the point to your selection.

Also, if you want to select all the points, while your cursor is hovering over the plot, if you hit the 'a' key, all the points will become selected. 

Once points are selected you can either delete them, by clicking on the trash icon tool, or move them using the arrow keys on your keyboard.

Note, the arrow keys will move the points a small amount based upon the current zoom level.  So if you zoom in, the absolute movement of the points will be smaller.   Note also that by default the points do not move in absolute coordinates, but rather the program uses the current selection to estimate the curvature of the ribbon, and moves the points in such a way that "up" is actually perpendicular to the tangent of the curvature of the ribbon.  You can deselect this option in the Options menu, by unchecking "Relative motion?" in which case the points will all move the same relative amount in absolute coordinates.

## Previewing a mosaic
The Mosaic Planner provides visual feedback on planning the acquisition of a mosaic centered around the current set of positions.  The program needs to know both the size of your camera, the magnification of your objective, the size of the grid you wish to acquire (in x and y), and the amount of overlap you want to have between individual frames of your mosaic.

To enter the information about your camera, click the Options menu, and click "edit camera settings".  This will prompt you to enter information about the number and size of the pixels on your camera.

Then on the toolbar, enter information about the magnification you will be using, as well as the size of the mosaic and the overlap.

When you click the Show checkbox, a green rectangle will be drawn around each point, showing the borders of the mosaic that will be acquired.  If you wish, you can click the Grid tool (the icon with the 3x3 grid), in which case the individual frames will also be shown in cyan.  

With the Mosaic boxes visible, you can then zoom in on an individual section to estimate where the borders will fall on your sections.

Also, if you wish you can click the rotate button, which rotates the green box to reflect the angle of the ribbon at each point.  It even also reposition the individual frames in such as way as to continue to have their edges vertical and horizontal, but rearrange their positions to best cover the rotated green box.  This mosaic will thus better cover the same corresponding regions of tissue as the curved ribbon rotates relative to the coordinate system of the microscope.

Now you might want to select all the points on your ribbon, and then zoom in on a representative section, then use the arrow keys to nudge the point around until you have optimized the area you are going to image.  You probably want to do this with the Relative Motion? option checked so that your points remain at least roughly aligned.

You can of course go back and use the CorrTool to align the points more finely.  Future versions will contain a tool to automate this fine tune alignment. 

## Saving position lists
When you are done and happy with your position list, enter a filename for the position list (the program will suggest one based upon the name and location of the image you loaded) and click the Save button to the right of the "array file" field.  (Note not the disk icon on the toolbar, which will simply save an image of the current workspace).
You can now also choose which kind of file format you want to save the position list in.  It should be fairly straight forward for someone to add a new file format to these options if they were interested, feel free to contact Forrest Collman in the Smith Lab if you want help in doing this.

You can also save a position list of individual frames.  This will produce a line in the position list for each of the individual frame positions needed to implement the mosaic you have entered into the toolbar.  Note, in order for this option to work perfectly, the size of the camera pixels and the relative zoom of the optical microscope must be empirically exact. If they are not exact, the amount of overlap may differ from the specified amount, and might affect your ability to stitch the images.

We have a Beta version of some software which allows semi-automated checking of the focus of individual ZVI files called ReFocus, so that when a single frame of a mosaic is out of focus, one can go more easily find that frame and go back and retake only that frame.  You can find it in the SVN.  This program is designed to work with mosaics in which were created using this "freeframe" option.  We also have python scripts in FIJI for exporting and stitching these types of "freeframe" mosaics. 

## *BETA* Saving transformed position lists===
The software now contains a primitive ability to save transformed position lists that we are currently developing.  This allows you to tell the software about sets of corresponding points between the coordinate system that the 10X image was acquired in, and the coordinate system of the microscope that you want the position list to be saved into.  With those points, the software can fit a transformation to the correspondences, and thus be able to transform the position list you setup in the original coordinate system into the new coordinate system.

To setup and edit this transform, currently you need to have a .csv file which contains the corresponding points formatted as follow.

{{{
#Header line, i don't care what you put here i'll ignore it
x_from1,y_from1,x_to1,y_to1
x_from2,y_from2,x_to2,y_to2
x_from3,y_from3,x_to3,y_to2
.
.
.
x_fromN,y_fromN,x_toN,y_toN
}}}

In the Transform Menu at the top of the program, you can click Edit Transform... which will take you to a dialog which will allow you to specify this csv file, as well as the type of transformation you want it to fit the corresponding points to.  Currently I have only implemented 'translation' and 'similarity' (uniform scaling, rotation, and translation).  In addition, if the directionality of the horizontal or vertical axis has to be flipped in order to make the transformation work, you can check the flip vertical or flip horizontal tick marks.  This will change the coordinates of the from points from x->-x for horizontal flip, and y->-y for vertical flip, before fitting the transformation. 

Specify the csv file using the file picker and hit load, choose the transform type you want and then close the dialog.  After you close the dialog in python terminal, you will see a text output that shows how the transform mapped each of the individual from points, as well as their specified locations in parentheses, so you can evaluate the precision of the fit.

# Development Plan
## Partially done features

  * Create a preview image stack)  I have some code written, but the Python Imaging Library is not that efficent at cropping large images and so its slow.  I think I might want to move over to another Imaging Library that is smarter at allocating memory and reading just the pixels necessary to produce the cropped image.

  * Some kind of refinement tool which will readjust by cross correlation all of the points, but make an assumption that all of the points are basically close to correct.  For instance if you use the arrow keys to fine tune the placement of the mosaic, the exact locations might no longer be optimal.  Also, currently the program does not sample every offset on a integer pixel level, but rather samples offsets skipping every X pixels.  This saves computational time, but when moving from 10x to 63x a single pixel can be significant, so one should do a coarse alignment first using skipping in order to efficiently search a large area, but then follow that up with a smaller more precise alignment.

## Known/suspected bugs
  * Only 16-bit tiff images have been used in testing this program

## Requirements
To run this program you must have python installed (http://www.python.org/) I have developed this on both 2.6 and 2.7 and had no issues with compatibility, but I am unsure as to either forward or backward compatibility from there.

You also need your python instance to have the following python packages installed

  * matplotlib (for making the pretty dynamic plots) http://matplotlib.sourceforge.net/
  * numpy (for making mathematical operations on data sane) http://numpy.scipy.org/
  * Python Imaging Library (for reading/cropping/resizing/writing images) http://www.pythonware.com/products/pil/
  * wxpython (for the GUI interface) http://www.wxpython.org/
  
If starting from scratch with python I'd recommend the following

for 32-bit machines

  * Windows, i'd recommend you installed Python(x,y) http://www.pythonxy.com/ and then wxpython from wxpython.org
  * Mac, use macports http://www.macports.org/ to install everything
    (see MosaicPlannerLion for my walk through in installing it on Mac OS Lion)
  * Linux/Unix See your package management software

for 64-bit machines
  * Windows You need to install python from python.org and then this link has some useful binaries http://www.lfd.uci.edu/~gohlke/pythonlibs/
  * Mac, use macports http://www.macports.org/ to install everything
  * Linux/Unix see your package management software

I have tried a little bit to get py2exe working with this package but haven't made it very far.  If someone wanted to help out with that it make it easier for many people to use as we could just link to a download button.

## Configuration Instructions
The Micromanager installation directory should be added to the pythonpath environment variable, so that MosaicPlanner can access the Micro-Manager C++ Core. (To do this on Windows go to System Properties, Advanced, System Variables and add or edit the PYTHONPATH directory)

You should setup a Micromanager configuration file that has all your devices loaded, and you should make a few Configu groups.

### Group: System
### Preset: Startup
This should contain all the settings you want your devices to have set when you start your program.  Importantly, this includes Camera flips/transpose, stage flips and transposes, so that the stage coordinates read out in a way that is consistent with the way the camera lays out it's pixels, and follows the matrix access convention... meaning positive Y is down, and positive X is to the right, and images have their first pixel at 0,0 in the upper left.

### Group: Channels
### Presets: All the different channels you want to snap images in
This should contain all the settings that are needed to make the microscope snap a picture in a specific channel
They should have names that reflect the fluorophore they are designed to excite and the state of the scope.

### Group: Triggering
### Preset: Software
These are settings of various devices that are needed to make normal software triggering work. Most importantly, the triggering properity of your camrea, but maybe also the sequencing mode of Arduino's, etc etc.

### Preset: Hardware
These are the settings for devices that are needed to make hardware triggering work.  Note hardware triggering will only run successfully if for all the properties in the Channel Groups you select to image the properties are either "sequencable" after these hardware triggering properties are applied OR they are constant across all the channels.

You can find many more configuration properties in the MosaicPlannerSettings.cfg	file which should be created the first time you run MosaicPlanner.  It will ask you the first time what Microamanger configuration file you would like to access the first time you run the program and this will be stored in the configuration.


