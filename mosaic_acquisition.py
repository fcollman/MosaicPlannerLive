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

import multiprocessing as mp
import wx
import os

from imageSourceMM import imageSource

STOP_TOKEN = 'STOP!!!'

def acquisition_process(MM_config_file,metadata_dictionary,coordinates,config,outdir):
    '''
    Handler function for setting up the process to run the mosaic aquisition.
    '''
    MosaicAquisition(MM_config_file,metadata_dictionary, coordinates, config,outdir)



class MosaicAquisition()

    def __init__(self, MM_config_file, metadata_dictionary, coordinates,config,outdir):
        '''
        :param MM_config_file:
        :param metadata_dictionary:
        :param coordinates: if framelist D = 4, else D= 3
        (x,y,i,j) or (x,y,i)
        :param config:
        :param outdir:
        :return:
        '''

        try:
            self.imgSrc=imageSource(MM_config_file)
        except:
            print('Could not set up acquisition image source, aborting...')
            return None

        self.dataQueue = mp.Queue()
        self.saveProcess =  mp.Process(target=file_save_process,args=(self.dataQueue,STOP_TOKEN, metadata_dictionary))
        self.saveProcess.daemon = True # Set so saveprocess will be killed if the run process is terminated
        self.saveProcess.start()

        if len(coordinates[0]) == 3: # No framelist, just single positions
            for xyi in coordinates:
                self.multiDAcq(xyi[0], xyi[1], xyi[2], frameindex=0)

        elif len(coordinates[0]) == 4: # Framelist exists
            for xyij in coordinates:
                self.multiDAcq(xyij[0], xyij[1], xyij[2], xyij[3])

        else:
            print('Acquisition coordinates unexpected dimensions, aborting')
            return None


        self.config = wx.Config('settings') # ? or just config
        self.channel_settings=ChannelSettings(self.imgSrc.get_channels())
        self.channel_settings.load_settings(self.config)
        self.imgSrc.set_channel(self.channel_settings.map_chan)

        self.dataQueue.put(STOP_TOKEN)
        self.saveProcess.join()
        print "save process ended"

    def multiDAcq(self,outdir,x,y,slice_index,frame_index=0):

        self.imgSrc.set_hardware_autofocus_state(True)
        self.imgSrc.move_stage(x,y)

        attempts=0
        if self.imgSrc.has_hardware_autofocus():
            while not self.imgSrc.is_hardware_autofocus_done():
                attempts+=1
                if attempts>100:
                    print "CRISP not auto-focusing correctly.. giving up after 10 seconds"
                    break
            self.imgSrc.set_hardware_autofocus_state(False)

        else:
            score=self.imgSrc.image_based_autofocus(chan=self.channel_settings.map_chan)
            print score

        currZ=self.imgSrc.get_z()

        #if self.zstack_settings.zstack_flag:
        #    furthest_distance = self.zstack_settings.zstack_delta * (self.zstack_settings.zstack_number-1)/2
        #    zplanes_to_visit = [(currZ-furthest_distance) + i*self.zstack_settings.zstack_delta for i in range(self.zstack_settings.zstack_number)]
        #else:
        zplanes_to_visit = [currZ]

        for z_index, zplane in enumerate(zplanes_to_visit):
            for k,ch in enumerate(self.channel_settings.channels):
                prot_name=self.channel_settings.prot_names[ch]
                path=os.path.join(outdir,prot_name)
                if self.channel_settings.usechannels[ch]:

                    z = zplane + self.channel_settings.zoffsets[ch]
                    self.imgSrc.set_z(z)
                    self.imgSrc.set_exposure(self.channel_settings.exposure_times[ch])
                    self.imgSrc.set_channel(ch)

                    data=self.imgSrc.snap_image()
                    self.dataQueue.put((slice_index,frame_index, z_index, prot_name,path,data,ch,x,y,z,))

def file_save_process(queue,stop_token, metadata_dictionary):
    while True:
        token=queue.get()
        if token == stop_token:
            return
        else:
            (slice_index,frame_index, z_index, prot_name,path,data,ch,x,y,z)=token
            tif_filepath=os.path.join(path,prot_name+"_S%04d_F%04d_Z%02d.tif"%(slice_index,frame_index,z_index))
            metadata_filepath=os.path.join(path,prot_name+"_S%04d_F%04d_Z%02d_metadata.txt"%(slice_index,frame_index,z_index))
            imsave(tif_filepath,data)
            write_slice_metadata(metadata_filepath,ch,x,y,z,metadata_dictionary)


def write_slice_metadata(filename,ch,xpos,ypos,zpos, meta_dict):
    f = open(filename, 'w')
    channelname   = meta_dict['channelname'][ch]
    (height,width)= meta_dict['(height,width)']
    ScaleFactorX  = meta_dict['ScaleFactorX']
    ScaleFactorY  = meta_dict['ScaleFactorY']
    exp_time      = meta_dict['exp_time'][ch]

    f.write("Channel\tWidth\tHeight\tMosaicX\tMosaicY\tScaleX\tScaleY\tExposureTime\n")
    f.write("%s\t%d\t%d\t%d\t%d\t%f\t%f\t%f\n" % \
    (channelname, width, height, 1, 1, ScaleFactorX, ScaleFactorY, exp_time))
    f.write("XPositions\tYPositions\tFocusPositions\n")
    f.write("%s\t%s\t%s\n" %(xpos, ypos, zpos))