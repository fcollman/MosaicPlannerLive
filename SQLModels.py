
from sqlalchemy.ext.declarative import declarative_base,declared_attr
from sqlalchemy import Column, Integer, String, Sequence,ForeignKey,Float
from sqlalchemy.orm import relationship
Base = declarative_base()

import numpy as np
class MyMixin(object):
    #@declared_attr
    #def __tablename__(cls):
    #    return cls.__name__.lower()
    #@declared_attr
    #def object_id(cls):
    #    return Column('object_id', ForeignKey('objects.id'))
    #@declared_attr
    #def object(cls):
    #    return relationship("Object")
    id=Column(Integer,primary_key=True)
    #@declared_attr
    #def object_id(cls):
    #    return Column(Integer, ForeignKey('objects.id'),primary_key=True)
    #test = Column(Integer)

class ATObject(Base):
    __tablename__ = 'objects'
    object_id = Column(Integer,primary_key=True)
    objecttype = Column(String(100))
    status = Column(Integer)
    __mapper_args__ = {'polymorphic_on': objecttype}
    #json_filename = Column(String(100))
    #def __init__(self, **kwargs):
    #    if 'status' not in kwargs:
    #        kwargs['status'] = 0
    #    super(Object, self).__init__(**kwargs)

    def __repr__(self):
        return "ATObject(objecttype=%s)"%(self.objecttype)


class Experiment(ATObject,MyMixin):
    __tablename__ = 'experiments'
    __mapper_args__={'polymorphic_identity': 'experiment'}
    object_id = Column(Integer, ForeignKey('objects.object_id'),primary_key=True)

    name = Column(String(50))
    ribbons = relationship("Ribbon",back_populates='experiment',primaryjoin="Experiment.id==Ribbon.experiment_id")

    def __repr__(self):
        return "Experiment(name='%s')"%(self.name)

    def as_dict(self):
        dict = {'name':self.name,'ribbons':[r.object_id for r in ribbons]}
        json_string = json.dumps(dict)
        return json_string



class Ribbon(ATObject,MyMixin):
    __tablename__ = 'ribbons'
    __mapper_args__={'polymorphic_identity': 'ribbon'}
    object_id = Column(Integer, ForeignKey('objects.object_id'),primary_key=True)

    experiment_id = Column(Integer,ForeignKey('experiments.id'))
    experiment = relationship("Experiment",back_populates='ribbons',foreign_keys=[experiment_id])

    imagingsessions = relationship("ImagingSession",back_populates='ribbon',primaryjoin="Ribbon.id==ImagingSession.ribbon_id")
    order = Column(Integer)

    sections = relationship("Section",back_populates='ribbon',primaryjoin = "Ribbon.id==Section.ribbon_id")
    def __repr__(self):
        return "Ribbon(order=%d,experiment='%s')"%(self.order,self.experiment.name)

class ImagingSession(ATObject,MyMixin):
    __tablename__ = 'imagingsessions'
    __mapper_args__={'polymorphic_identity': 'imagingsession'}
    object_id = Column(Integer, ForeignKey('objects.object_id'),primary_key=True)

    ribbon_id = Column(Integer,ForeignKey('ribbons.id'))
    ribbon = relationship("Ribbon",back_populates='imagingsessions',foreign_keys=[ribbon_id])
    order = Column(Integer)

    channel_settings = relationship("ChannelSetting",back_populates='imagingsession',
                                   primaryjoin='ImagingSession.id==ChannelSetting.imagingsession_id')
    poslist_transform = relationship("LinearTransform",uselist=False,back_populates='imagingsession',
                                     primaryjoin='ImagingSession.id==LinearTransform.imagingsession_id')


class LinearTransform(ATObject,MyMixin):
    __tablename__ = 'lineartransforms'
    __mapper_args__={'polymorphic_identity': 'lineartransforms'}
    object_id = Column(Integer, ForeignKey('objects.object_id'),primary_key=True)

    imagingsession_id = Column(Integer,ForeignKey('imagingsessions.id'))
    imagingsession = relationship("ImagingSession",back_populates='poslist_transform',foreign_keys=[imagingsession_id])

    a00 = Column(Float)
    a10 = Column(Float)
    a11 = Column(Float)
    a12 = Column(Float)
    b0 = Column(Float)
    b1 = Column(Float)

    def get_transform(self):
        A=np.array([[self.a00,self.a01],[self.a10,self.a11]])
        B=np.array([self.b0,self.b1])
        return A,B

    def set_transform(self,A,B):
        self.a00=A[0,0]
        self.a01=A[0,1]
        self.a10=A[1,0]
        self.a11=A[0,1]
        self.b0=B[0]
        self.b1=B[1]


# # class RigidTransform(LinearTransform,Base):

# #      def get_angle():
# #          pass
# #      def set_angle():
# #          pass
# #      def get_offset():
# #          pass
# #      def set_offset():
# #          pass
class ChannelSetting(ATObject,MyMixin):
    __tablename__ = 'channelsettings'
    __mapper_args__={'polymorphic_identity': 'channelsetting'}
    object_id = Column(Integer, ForeignKey('objects.object_id'),primary_key=True)

    imagingsession_id = Column(Integer,ForeignKey('imagingsessions.id'))
    imagingsession = relationship("ImagingSession",back_populates='channel_settings',foreign_keys=[imagingsession_id])
    channel_id = Column(Integer,ForeignKey('channels.id'))
    channel = relationship("Channel",foreign_keys=[channel_id])

    protein_name = Column(String(50))
    exposure_time = Column(Integer)
    z_offset = Column(Float)

    def __repr__(self):
        return "ChannelSetting(protein_name = '%s', exposure= %d, z_offset = %f)"%(self.protein_name,self.exposure_time,self.z_offset)
class Channel(ATObject,MyMixin):
    __tablename__ = 'channels'
    __mapper_args__={'polymorphic_identity': 'channel'}
    object_id = Column(Integer, ForeignKey('objects.object_id'),primary_key=True)

    name = Column(String(50))
    wavelength = Column(String(50))

class Section(ATObject,MyMixin):
    __tablename__ = 'sections'
    __mapper_args__={'polymorphic_identity': 'section'}
    object_id = Column(Integer, ForeignKey('objects.object_id'),primary_key=True)
    ribbon_id = Column(Integer,ForeignKey('ribbons.id'))
    ribbon = relationship("Ribbon",back_populates='sections',foreign_keys=[ribbon_id])
    order = Column(Integer)
    pos_x = Column(Float)
    pos_y = Column(Float)
    angle = Column(Float)

class SectionImagePlan(ATObject,MyMixin):
    __tablename__ = 'sectionimageplans'
    __mapper_args__={'polymorphic_identity': 'sectionimageplans'}
    object_id = Column(Integer, ForeignKey('objects.object_id'),primary_key=True)

    imagingsession_id = Column(Integer,ForeignKey('imagingsessions.id'))
    imagingsession = relationship("ImagingSession",foreign_keys=[imagingsession_id])
    section_id = Column(Integer,ForeignKey('sections.id'))
    section = relationship("Section",foreign_keys=[section_id])
    frames = relationship("Frame",back_populates='sectionimageplan',
                         primaryjoin='SectionImagePlan.id==Frame.sectionimageplan_id')

class Frame(ATObject,MyMixin):
    __tablename__ = 'frames'
    __mapper_args__={'polymorphic_identity': 'frame'}
    object_id = Column(Integer,ForeignKey('objects.object_id'),primary_key=True)

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
    object_id = Column(Integer,ForeignKey('objects.object_id'),primary_key=True)

    imagepath = Column(String(100))
    channel_setting_id = Column(Integer,ForeignKey('channelsettings.id'))
    #channel_setting = relationship("ChannelSetting")
    z_order = Column(Integer)
    z_pos = Column(Float)
    frame_id = Column(Integer,ForeignKey('frames.id'))
    frame = relationship("Frame",back_populates='images',foreign_keys=[frame_id])
