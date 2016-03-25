import os
import json
STOP_TOKEN = 'STOP!!!'
FRAME_TOKEN = 'Frame_Acquired'
SECTION_TOKEN = 'Section_Acquired'
TILE_TOKEN = 'Tile_Acquired'
SESSION_TOKEN = 'Session_Acquired'

EXPERIMENT_FILENAME = 'exp.json'

def get_data_from_json(directory,filename):
    filepath = os.path.join(directory,filename)
    if os.path.isfile(filepath):
        with open(filepath) as data_file:
            experiment_dict = json.load(data_file)
    else:
        return None

def get_experiment_from_json(directory):
    return get_data_from_json(directory,EXPERIMENT_FILENAME)

def get_ribbon_from_json(directory,ribbonkey):
    filepath = os.path.join(directory,ribbonkey)
    if os.path.isfile(filepath):
        with open(filepath) as data_file:
            ribbon_dict = json.load(data_file)
    else:
        return None


def add_ribbon_to_json(directory,ribbonid):
    pass

def add_session_to_json():
    print "hi"


def file_save_process(queue,stop_token, metadata_dictionary):
    pass
    # while True:
    #     token = queue.get()
    #     token_type = token[0]
    #     if token_type == stop_token:
    #         return
    #     else:
    #         if token_type==FRAME_TOKEN:
    #
    #         elif token_type==SECTION_TOKEN:
    #             process_
    #         elif token_type==TILE_TOKEN:
    #             process_tile_token(token,metadata_dictionary)
    #         elif token_type==SESSION_TOKEN:
    #             process_session_token(token)
    #
    #         (slice_index,frame_index, z_index, prot_name, path, data, ch, x, y, z) = token
    #
    #
    #         tif_filepath = os.path.join(path, prot_name + "_S%04d_F%04d_Z%02d.tif" % (slice_index, frame_index, z_index))
    #         metadata_filepath = os.path.join(path, prot_name + "_S%04d_F%04d_Z%02d_metadata.txt"%(slice_index, frame_index, z_index))
    #         imsave(tif_filepath,data)
    #         write_slice_metadata(metadata_filepath, ch, x, y, z, metadata_dictionary)


def process_session_token(token):
    (token_type,experiment_id,ribbon_id,session_id,section_ids)=token
    session_json = create_session_json(session_id,section_ids)

def process_section_token(token):
    (token_type,section_id,frame_ids)=token

def process_frame_token(token):
    (token_type,frame_id,tile_ids,frame_index)=token

def create_session_json(session_id,section_ids):
    pass
def write_slice_metadata(filename, ch, xpos, ypos, zpos, meta_dict):
    channelname    = meta_dict['channelname'][ch]
    (height,width) = meta_dict['(height,width)']
    ScaleFactorX   = meta_dict['ScaleFactorX']
    ScaleFactorY   = meta_dict['ScaleFactorY']
    exp_time       = meta_dict['exp_time'][ch]

    f = open(filename, 'w')
    f.write("Channel\tWidth\tHeight\tMosaicX\tMosaicY\tScaleX\tScaleY\tExposureTime\n")
    f.write("%s\t%d\t%d\t%d\t%d\t%f\t%f\t%f\n" % \
    (channelname, width, height, 1, 1, ScaleFactorX, ScaleFactorY, exp_time))
    f.write("XPositions\tYPositions\tFocusPositions\n")
    f.write("%s\t%s\t%s\n" %(xpos, ypos, zpos))


class MP_json_node():
    def __init__(self,name,rootdir):
        self.mydict = {}
        self.rootdir = rootdir

    def save(self):
        self.dump()
    def load(self):
        pass
    def queue_to_s3(self):
        pass
class Experiment_json_node(MP_json_node):

    def get_ribbons(self):
        return self.mydict['ribbons']
    def set_ribbons(self,ribbons):
        self.mydict['ribbons']=ribbons

