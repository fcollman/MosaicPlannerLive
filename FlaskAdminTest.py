from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
SETTINGS_FILE = 'MosaicPlannerSettings.cfg'
from configobj import ConfigObj
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from SQLModels import *

class VolumeView(ModelView):
    # Show only name and email columns in list view
    column_list = ('name','status','created','modified')

    # Enable search functionality - it will search for terms in
    # name and email fields
    column_searchable_list = ('name', 'status')

    # Add filters for name and email columns
    column_filters = ('name', 'status')

cfg = ConfigObj(SETTINGS_FILE,unrepr=True)
#sql_engine = create_engine(cfg['SqlAlchemy']['database_path'])
sql_engine = create_engine(cfg['SqlAlchemy']['database_path'])

Base.metadata.create_all(sql_engine)

Session = sessionmaker(bind=sql_engine)

mysess = Session()


app = Flask(__name__)

admin = Admin(app, name='ATdbservice', template_mode='bootstrap3')
# Add administrative views here

admin.add_view(ModelView(ATObject,mysess))
admin.add_view(VolumeView(Volume, mysess))
admin.add_view(ModelView(Ribbon,mysess))
admin.add_view(ModelView(MicroscopeRound,mysess))


app.run()