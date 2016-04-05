
from sqlalchemy.ext.declarative import declarative_base,declared_attr
from sqlalchemy import Column, Integer, String, Sequence,ForeignKey,Float,DateTime,Table
from sqlalchemy.orm import relationship
Base = declarative_base()
from sqlalchemy import Sequence

import numpy as np
from sqlalchemy import event
from datetime import datetime



class MyMixin(object):
    @declared_attr
    def __table_args__(cls):
        return {'sqlite_autoincrement':True}
    #@declared_attr
    #def object_id(cls):
    #    return Column('object_id', ForeignKey('objects.id'))
    #@declared_attr
    #def object(cls):
    #    return relationship("Object")

    #@declared_attr
    #def object_id(cls):
    #    return Column(Integer, ForeignKey('objects.id'),primary_key=True)
    #test = Column(Integer)
    id=Column(Integer,primary_key=True)

class ATObject(Base):
    __tablename__ = 'objects'
    __table_args__= {'sqlite_autoincrement':True}
    object_id = Column(Integer,primary_key=True)
    objecttype = Column(String(100))
    status = Column(Integer)
    created = Column(DateTime)
    modified = Column(DateTime)

    __mapper_args__ = {
        'polymorphic_on': objecttype
    }
    #json_filename = Column(String(100))
    #def __init__(self, **kwargs):
    #    if 'status' not in kwargs:
    #        kwargs['status'] = 0
    #    super(Object, self).__init__(**kwargs)

    def __repr__(self):
        return "ATObject(objecttype=%s)"%(self.objecttype)


def update_created_modified_on_create_listener(mapper, connection, target):
  """ Event listener that runs before a record is updated, and sets the create/modified field accordingly."""
  target.created = datetime.utcnow()
  target.modified = datetime.utcnow()

def update_modified_on_update_listener(mapper, connection, target):
  """ Event listener that runs before a record is updated, and sets the modified field accordingly."""
  # it's okay if this field doesn't exist - SQLAlchemy will silently ignore it.
  target.modified = datetime.utcnow()


ribbon_stainround_association = Table('ribbon_stainround_association', Base.metadata,
                                  Column('ribbon_id', Integer, ForeignKey('ribbon.id')),
                                  Column('stainround_id', Integer, ForeignKey('stainround.id')))

ribbon_microscoperound_association = Table('ribbon_microscoperound_association', Base.metadata,
                                      Column('ribbon_id', Integer, ForeignKey('ribbon.id')),
                                      Column('microscoperound_id', Integer, ForeignKey('microscoperound.id')))

# class Block(ATObject,MyMixin):
#     __tablename__ = 'block'
#     __mapper_args__={'polymorphic_identity': 'block'}
#     object_id = Column(Integer, ForeignKey('objects.object_id'))
#
#     ribbons = relationship("Ribbon",back_populates='block',primaryjoin="Block.id==Ribbon.block_id")
#
#     #map of ribbons in this block

volumeribbon_association = Table('volumeribbon_association', Base.metadata,
                                  Column('volume_id', Integer, ForeignKey('volume.id')),
                                  Column('ribobn_id', Integer, ForeignKey('ribbon.id')))

class Volume(ATObject, MyMixin):
    __tablename__ = 'volume'
    __mapper_args__={'polymorphic_identity': 'volume'}
    object_id = Column(Integer, ForeignKey('objects.object_id'))

    name = Column(String(50))
    ribbons = relationship("Ribbon",secondary=volumeribbon_association)

    notes = Column(String(512))

    def __repr__(self):
        return "Volume(name='%s')"%(self.name)

class Ribbon(ATObject,MyMixin):
    __tablename__ = 'ribbon'
    __mapper_args__={'polymorphic_identity': 'ribbon'}
    object_id = Column(Integer, ForeignKey('objects.object_id'))

    # block_id = Column(Integer,ForeignKey('block.id'))
    # block = relationship("Block",back_populates='ribbons',foreign_keys=[block_id])

    #volume_id = Column(Integer,ForeignKey('volume.id'))
    #volume = relationship("Volume",back_populates='ribbons',foreign_keys=[volume_id])

    #imagingsessions = relationship("ImagingSession",back_populates='ribbon',primaryjoin="Ribbon.id==ImagingSession.ribbon_id")
    order = Column(Integer)
    stainrounds = relationship("StainRound",secondary=ribbon_stainround_association)
    microscoperounds = relationship("MicroscopeRound",secondary=ribbon_microscoperound_association)

    sections = relationship("Section",back_populates='ribbon',primaryjoin = "Ribbon.id==Section.ribbon_id")
    notes = Column(String(512))
    def __repr__(self):
        return "Ribbon(order=%d,volume='%s')"%(self.order,self.volume.name)

class MicroscopeRound(ATObject,MyMixin):
    __tablename__ = 'microscoperound'
    __mapper_args__={'polymorphic_identity': 'microscoperound'}
    object_id = Column(Integer, ForeignKey('objects.object_id'))

    channelsettings = relationship("ChannelSetting",primaryjoin="MicroscopeRound.id==ChannelSetting.microscoperound_id")


class ChannelSetting(ATObject,MyMixin):
    __tablename__ = 'channelsettings'
    __mapper_args__={'polymorphic_identity': 'channelsetting'}
    object_id = Column(Integer, ForeignKey('objects.object_id'))

    microscoperound_id = Column(Integer,ForeignKey('microscoperound.id'))
    microscoperound = relationship("MicroscopeRound",back_populates='channelsettings',foreign_keys=[microscoperound_id])

    channelconfig_id = Column(Integer,ForeignKey('channelconfig.id'))
    channelconfig = relationship("ChannelConfig",foreign_keys=[channelconfig_id])

    stain_id = Column(Integer,ForeignKey('stain.id'))
    stain = relationship("Stain",foreign_keys=[stain_id])

    exposure_time = Column(Integer)
    z_offset = Column(Float)

    def __repr__(self):
        return "ChannelSetting(exposure= %d, z_offset = %f)"%(self.exposure_time,self.z_offset)


channelconfig_association = Table('channelconfig_association', Base.metadata,
                                Column('channelconfig_id', Integer, ForeignKey('channelconfig.id')),
                                Column('fluorophore_id', Integer, ForeignKey('fluorophore.id')))


class ChannelConfig(ATObject,MyMixin):
    __tablename__ = 'channelconfig'
    __mapper_args__={'polymorphic_identity': 'channelconfig'}
    object_id = Column(Integer, ForeignKey('objects.object_id'),primary_key=True)

    name = Column(String(50)) #name of the channel config group in micromanager (Channels,X)

    #the set of fluorophores for which this channel config is appropriate
    fluorophores = relationship("Fluorophore", secondary=channelconfig_association)

stain_association_table = Table('stain_association', Base.metadata,
                                Column('stainround_id', Integer, ForeignKey('stainround.id')),
                                Column('stain_id', Integer, ForeignKey('stain.id')))

class StainRound(ATObject,MyMixin):
    __tablename__ = 'stainround'
    __mapper_args__ = {'polymorphic_identity':'stainround'}
    object_id = Column(Integer,ForeignKey('objects.object_id'))

    immunoprotocol_id = Column(Integer,ForeignKey('immunoprotocol.id'))
    protocol = relationship("ImmunoProtocol",foreign_keys = [immunoprotocol_id])

    stains = relationship("Stain", secondary = stain_association_table)


class Stain(ATObject,MyMixin):
    __tablename__ = "stain"
    __mapper_args__ = {'polymorphic_identity':'stain'}
    object_id = Column(Integer,ForeignKey('objects.object_id'))

    primary_antibody_id = Column(Integer,ForeignKey('primaryantibody.id'))
    primary_antibody = relationship("PrimaryAntibody",foreign_keys=[primary_antibody_id])
    primary_dilution = Column(Integer)

    secondary_antibody_id = Column(Integer,ForeignKey('secondaryantibody.id'))
    secondary_antibody = relationship("SecondaryAntibody",foreign_keys=[secondary_antibody_id])
    secondary_dilution = Column(Integer)

    directfluorophore_id = Column(Integer,ForeignKey('fluorophore.id'))
    directfluorophore = relationship("Fluorophore",foreign_keys=[directfluorophore_id])

class ImmunoProtocol(ATObject,MyMixin):
    __tablename__ = 'immunoprotocol'
    __mapper_args__ = {'polymorphic_identity':'immunoprotocol'}
    object_id = Column(Integer, ForeignKey('objects.object_id'))

    name = Column(String(100))
    notes = Column(String(1024))

class PrimaryAntibody(ATObject,MyMixin):
    __tablename__ = 'primaryantibody'
    __mapper_args__ = {'polymorphic_identity':'primaryantibody'}
    object_id = Column(Integer,ForeignKey('objects.object_id'))

    species_id = Column(Integer,ForeignKey('species.id'))
    species = relationship("Species",foreign_keys=[species_id])

    protein_name = Column(String(200))
    protein_asc_id = Column(String(200))
    manufacturer = Column(String(200))
    lot_number = Column(String(200))
    location = Column(String(200))
    recieved = Column(DateTime)
    notes = Column(String(512))
    tube_label = Column(String(512))

class SecondaryAntibody(ATObject,MyMixin):
    __tablename__ = 'secondaryantibody'
    __mapper_args__ = {'polymorphic_identity':'secondaryantibody'}
    object_id = Column(Integer,ForeignKey('objects.object_id'))
    #attributes


    hostspecies_id = Column(Integer,ForeignKey('species.id'))
    hostspecies = relationship("Species", foreign_keys=[hostspecies_id])
    species_id = Column(Integer,ForeignKey('species.id'))
    species = relationship("Species",foreign_keys=[species_id])

    fluorophore_id = Column(Integer,ForeignKey('fluorophore.id'))
    fluorophore = relationship("Fluorophore",foreign_keys=[fluorophore_id])

    manufacturer = Column(String(200))
    lot_number = Column(String(200))
    location = Column(String(200))
    recieved = Column(DateTime)
    notes = Column(String(512))
    tube_label = Column(String(512))

class Species(ATObject,MyMixin):
    __tablename__ = 'species'
    __mapper_args__ = {'polymorphic_identity':'species'}
    object_id = Column(Integer,ForeignKey('objects.object_id'))

    name = Column(String(200))


class Fluorophore(ATObject,MyMixin):
    __tablename__ = 'fluorophore'
    __mapper_args__ = {'polymorphic_identity': 'fluorophore'}
    object_id = Column(Integer, ForeignKey('objects.object_id'))

    name = Column(String(200))
    excitation_max = Column(Integer)
    emission_max = Column(Integer)

# class ImagingSession(ATObject,MyMixin):
#     __tablename__ = 'imagingsessions'
#     __mapper_args__={'polymorphic_identity': 'imagingsession'}
#     object_id = Column(Integer, ForeignKey('objects.object_id'))
#
#     ribbon_id = Column(Integer,ForeignKey('ribbons.id'))
#     ribbon = relationship("Ribbon",back_populates='imagingsessions',foreign_keys=[ribbon_id])
#     order = Column(Integer)
#
#     channel_settings = relationship("ChannelSetting",back_populates='imagingsession',
#                                    primaryjoin='ImagingSession.id==ChannelSetting.imagingsession_id')
#     poslist_transform = relationship("LinearTransform",uselist=False,back_populates='imagingsession',
#                                      primaryjoin='ImagingSession.id==LinearTransform.imagingsession_id')
#

# class LinearTransform(ATObject,MyMixin):
#     __tablename__ = 'lineartransforms'
#     __mapper_args__={'polymorphic_identity': 'lineartransforms'}
#     object_id = Column(Integer, ForeignKey('objects.object_id'))
#
#     imagingsession_id = Column(Integer,ForeignKey('imagingsessions.id'))
#     imagingsession = relationship("ImagingSession",back_populates='poslist_transform',foreign_keys=[imagingsession_id])
#
#     a00 = Column(Float)
#     a10 = Column(Float)
#     a11 = Column(Float)
#     a12 = Column(Float)
#     b0 = Column(Float)
#     b1 = Column(Float)
#
#     def get_transform(self):
#         A=np.array([[self.a00,self.a01],[self.a10,self.a11]])
#         B=np.array([self.b0,self.b1])
#         return A,B
#
#     def set_transform(self,A,B):
#         self.a00=A[0,0]
#         self.a01=A[0,1]
#         self.a10=A[1,0]
#         self.a11=A[0,1]
#         self.b0=B[0]
#         self.b1=B[1]


# # class RigidTransform(LinearTransform,Base):

# #      def get_angle():
# #          pass
# #      def set_angle():
# #          pass
# #      def get_offset():
# #          pass
# #      def set_offset():
# #          pass



class Section(ATObject,MyMixin):
    __tablename__ = 'sections'
    __mapper_args__={'polymorphic_identity': 'section'}
    object_id = Column(Integer, ForeignKey('objects.object_id'))

    ribbon_id = Column(Integer,ForeignKey('ribbon.id'))
    ribbon = relationship("Ribbon",back_populates='sections',foreign_keys=[ribbon_id])
    order = Column(Integer)
    pos_x = Column(Float)
    pos_y = Column(Float)
    angle = Column(Float)
    notes = Column(String(512))


class SectionImagePlan(ATObject,MyMixin):
    __tablename__ = 'sectionimageplans'
    __mapper_args__={'polymorphic_identity': 'sectionimageplans'}

    object_id = Column(Integer, ForeignKey('objects.object_id'),primary_key=True)

    microscoperound_id = Column(Integer,ForeignKey('microscoperound.id'))
    microscoperound = relationship("MicroscopeRound",foreign_keys=[microscoperound_id])
    section_id = Column(Integer,ForeignKey('sections.id'))
    section = relationship("Section",foreign_keys=[section_id])
    frames = relationship("Frame",back_populates='sectionimageplan',
                         primaryjoin='SectionImagePlan.id==Frame.sectionimageplan_id')

class Frame(ATObject,MyMixin):
    __tablename__ = 'frames'
    __mapper_args__={'polymorphic_identity': 'frame'}

    object_id = Column(Integer,ForeignKey('objects.object_id'))

    order = Column(Integer)
    sectionimageplan_id = Column(Integer,ForeignKey('sectionimageplans.id'))
    sectionimageplan = relationship("SectionImagePlan",back_populates='frames',foreign_keys=[sectionimageplan_id])

    pos_x = Column(Float)
    pos_y = Column(Float)
    pos_i = Column(Integer)
    pos_j = Column(Integer)
    images = relationship("Image",back_populates='frame',
                         primaryjoin='Frame.id==Image.frame_id')

#     def to_json():
#         return json.dumps([dict(r) for r in res], default=alchemyencoder)



class Image(ATObject,MyMixin):
    __tablename__ = 'images'
    __mapper_args__={'polymorphic_identity': 'image'}

    object_id = Column(Integer,ForeignKey('objects.object_id'))

    imagepath = Column(String(100))
    channel_setting_id = Column(Integer,ForeignKey('channelsettings.id'))
    #channel_setting = relationship("ChannelSetting")
    z_order = Column(Integer)
    z_pos = Column(Float)
    frame_id = Column(Integer,ForeignKey('frames.id'))
    frame = relationship("Frame",back_populates='images',foreign_keys=[frame_id])

event.listen(Ribbon, 'before_insert',update_created_modified_on_create_listener)
event.listen(Ribbon, 'before_update',update_modified_on_update_listener)
event.listen(Volume, 'before_insert',update_created_modified_on_create_listener)
event.listen(Volume, 'before_update',update_modified_on_update_listener)
event.listen(ATObject, 'before_insert',update_created_modified_on_create_listener)
event.listen(ATObject, 'before_update',update_modified_on_update_listener)
