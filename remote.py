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
"""
remote.py

Remote Interface for Mosaic Planner.

Here we expose any Mosaic Planner functionality that we'd like to be able to access from other
    software.  Any function or attribute added to RemoteInterface will be automatically callable
    using:

    >>> from zro import Proxy
    >>> mp = Proxy("<host_computer_name>:<rep_port>")

    For example:
    >>> pos = mp.get_stage_pos()
    >>> pos
    (3000, 4000)

It should be possible to re-use this code with other remote object systems like Pyro4.
"""
import os
import time
import logging

from zro import RemoteObject, Publisher

from imgprocessing import make_thumbnail

class RemoteInterface(Publisher):
    """ Allows remote control of certain Mosaic Planner features.

        All public attributes and methods of this class can be called
            remotely by connecting:

        >>> from zro import Proxy
        >>> mp = Proxy("<host_computer_name>:<rep_port>")
        >>> pos = mp.get_stage_pos()

        Args:
            rep_port (int): reply socket
            parent (MosaicPlanner): reference to MosaicPlanner

    """
    def __init__(self, rep_port, pub_port, parent):
        super(RemoteInterface, self).__init__(rep_port=rep_port, pub_port=pub_port)
        logging.info("Opening Remote Interface on port:{}".format(rep_port))
        self.parent = parent
        self._pause = False

    @property
    def pause(self):
        return self._pause

    @pause.setter
    def pause(self, value):
        self._pause = value

    def _check_rep(self):
        """ Checks replay socket.  Mosaic Planner calls this periodically to process
            requests.
        """
        super(RemoteInterface, self)._check_rep()

    def get_stage_pos(self):
        """ Returns the current xy stage position.

            Returns:
                tuple: current (x, y) stage position.
        """
        stagePosition = self.parent.getStagePosition()
        return stagePosition

    def set_stage_pos(self, pos):
        """ Sets the current xy stage position.

            Args:
                pos (iterable): x and y position for stage
        """
        self.parent.setStagePosition(*pos)
        logging.info("Set new stage position to x:{}, y:{}".format(*pos))

    def get_objective_z(self):
        """ Returns the current Z height of objective.

        """
        pos_z = self.parent.getZPosition()
        return pos_z

    def set_objective_z(self, pos_z, speed=None):
        if speed:
            old_speed = self.get_objective_property("Speed")
            self.set_objective_property("Speed", speed)
        t0 = time.clock()
        self.parent.setZPosition(pos_z)
        # make sure it got there
        timeout = self.parent.imgSrc.mmc.getTimeoutMs() / 1000.0
        while time.clock()-t0 < timeout:
            if not (pos_z-0.5 < self.get_objective_z() < pos_z+0.5):
                time.sleep(0.1)
            else:
                break
        else:
            raise Exception("Failed to reach target position before timeout.")

        logging.info("Set Z Position to z: {}".format(pos_z))
        if speed:
            self.set_objective_property("Speed", old_speed)

    def get_objective_property_names(self):
        # check that it has that property
        objective = self.parent.imgSrc.objective
        return self.parent.imgSrc.mmc.getDevicePropertyNames(objective)

    def get_objective_property(self, property):
        objective = self.parent.imgSrc.objective
        return self.parent.imgSrc.mmc.getProperty(objective, property)

    def set_objective_property(self, property, value):
        objective = self.parent.imgSrc.objective
        return self.parent.imgSrc.mmc.setProperty(objective, property, value)

    def set_objective_vel(self, vel):
        """ Sets objective move speed
        """

    def get_objective_vel(self):
        """ Get objective speed
        """

    def set_mm_timeout(self, ms):
        """ Sets MicroManager timeout
        """
        self.parent.imgSrc.mmc.setTimeoutMs(ms)
        logging.info("MicroManager timeout set to: {} ms".format(ms))

    def get_remaining_time(self):
        """ Returns remaining acquisition time.
        """
        remainingTime = self.parent.getRemainingImagingTime()
        return remainingTime

    def get_current_session(self):
        """ Gets the current imaging session metadata.

        Returns:
            dict: session data
        """
        return {}

    def set_current_session(self, session_data):
        """ Sets the current imaging session metadata from a session file.

        Args:
            session_data (dict): session data
        """

    def load_session(self, session_file):
        """ Reads a session from a yaml file and loads it.

        Args:
            session_file (str): path to session file

        """
        import yaml
        with open(session_file, 'r') as f:
            data = yaml.load(f)
        self.set_current_session(data)

    def on_run_multi(self):
        logging.info('preparing to image multiple ribbons')
        outdirlist = self.get_directory_settings()
        # ToImageList = len(outdirlist)*[True]

        poslistpath, ToImageList = self.get_position_list_settings()
        self.parent.on_run_multi_acq(poslistpath,outdirlist,ToImageList)

    def get_directory_settings(self):
        outdirdict = self.parent.outdirdict
        outdirlist =[]
        keys = sorted(outdirdict)
        for key in keys:
            outdirlist.append(outdirdict[key])
        return outdirlist

    def get_position_list_settings(self):
        pass
        # #will return a list of position lists to load into on run multi
        # keys = sorted(self.parent.outdirdict)
        # dlg = MultiRibbonSettings(None, -1, self.parent.Ribbon_Num, keys, title = "Multiribbon Settings",style=wx.OK)
        # ret=dlg.ShowModal()
        # if ret == wx.ID_OK:
        #     poslistpath, ToImageList =dlg.GetSettings()
        # dlg.Destroy()
        # return poslistpath, ToImageList

    def sample_nearby(self, pos=None, folder="", size=3):
        """ Samples a grid of images and saves them to a specified folder.

        args:
            pos (tuple): position of center image, defaults to current position
            folder (str): folder to save images to
            size (int): rows and columns in each direction (total images are (2*size+1)^2)
        """
        self.parent.grabGrid(pos, folder, size)
        logging.info("Grid grabbed @ {}".format(folder))

    def grab_image(self):
        """ Returns the current image from the camera.

        Returns:
            numpy.ndarray: the current image data
        """
        data = self.parent.imgSrc.snap_image()
        thumb = make_thumbnail(data, autoscale=True)
        self.publish(thumb)
        return data


    def connect_objective(self, pos_z, speed=None):
        approach_offset = 4000.0 # configurable?
        # go to approach offset first
        self.set_objective_z(approach_offset)
        # then go to objective slowly if desired
        self.set_objective_z(pos_z, speed=speed)


    def disconnect_objective(self, pos_z=None, speed=None):
        approach_offset = 4000.0 #configurable?
        if pos_z is None:
            pos_z = approach_offset
        self.set_objective_z(approach_offset, speed)
        self.set_objective_z(pos_z)


    def autofocus(self, search_range=320, step=20, settle_time=1.0, attempts=3):
        """ Triggers autofocus.
        """
        # best_offset = self.parent.software_autofocus(False, False)
        # logging.info("Autofocus finished."
        # return best_offset
        #self.parent.imgSrc.set_hardware_autofocus_state(True)
        z_pos = self.parent.imgSrc.focus_search(search_range=search_range,
                                                step=step,
                                                settle_time=settle_time,
                                                attempts=attempts)
        logging.info("Autofocus completed @ objective height: {}".format(z_pos))
        return z_pos

    def change_channel_settings(self):
        """ ROB: what is this?

        """
        self.parent.edit_channels()

    @property
    def is_acquiring(self):
        """ Returns whether or not MP is acquiring
        """
        #return self.parent.acquiring
        return False

    def check_bubbles(self, img_folder):
        """ Checks for bubbles in the images in specified folder.

        args:
            folder (str): folder of images

        Returns:
            list: list of images containing detected bubbles
        """
        import cv2
        import numpy as np
        import tifffile
        data_files = []
        for file in os.listdir(img_folder):
            data_files.append(os.path.join(img_folder, file))

        params = cv2.SimpleBlobDetector_Params()

        # Change thresholds
        params.minThreshold = 0
        params.maxThreshold = 15
        params.thresholdStep = 1

        # Filter by Area.
        params.filterByArea = True
        params.maxArea = 1e7
        params.minArea = 5e4 #5e4

        # Filter by Circularity
        params.filterByCircularity = False
        params.minCircularity = 0.5

        # Filter by Convexity
        params.filterByConvexity = True
        params.minConvexity = 0.97

        # Filter by Inertia
        params.filterByInertia = False
        params.minInertiaRatio = 0.4

        # Find bubbles
        score = np.zeros((len(data_files),),dtype='uint8')
        x = np.zeros((len(data_files),))
        y = np.zeros((len(data_files),))
        s = np.zeros((len(data_files),))

        blobReport = []

        for i, filename in enumerate(data_files):
            img = tifffile.imread(filename)
            img = cv2.blur(img, (50,50))
            a = 255.0/(np.max(img) - np.min(img))
            b = np.min(img)*(-255.0)/(np.max(img)-np.min(img))
            img = cv2.convertScaleAbs(img,alpha=a,beta=b)
            params.maxThreshold = int(round(np.min(img) + (np.min(img) + np.median(img))/4))
            img[0:2,:]=img[-2:,:]=img[:,0:2]=img[:,-2:]=np.median(img)

            # Create a detector with the parameters
            detector = cv2.SimpleBlobDetector(params)

            keypoints = detector.detect(img)
            if keypoints:
                score[i] = 1
                x[i] = keypoints[0].pt[0]
                y[i] = keypoints[0].pt[1]
                s[i] = keypoints[0].size
                logging.info("found %d blobs" % len(keypoints))
                blobReport.append(filename)
            else:
                score[i] = 0

        logging.info("blobReport:{}".format(blobReport))
        return blobReport
