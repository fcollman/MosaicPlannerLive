from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from config import cfg
from flask_sqlalchemy import SQLAlchemy

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from SQLModels import *

class BaseView(ModelView):
    form_excluded_columns = ('objecttype')

class VolumeView(BaseView):
    # Show only name and email columns in list view
    column_list = ('name','status','created','modified')

    # Enable search functionality - it will search for terms in
    # name and email fields
    column_searchable_list = ('name', 'status')

    # Add filters for name and email columns
    column_filters = ('name', 'status')


app = Flask(__name__)
app.debug = True
app.secret_key = 'prettybluesky'
app.config['SQLALCHEMY_DATABASE_URI']=cfg['SqlAlchemy']['database_path']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

admin = Admin(app, name='ATdbservice', template_mode='bootstrap3')
# Add administrative views here
Base.metadata.drop_all(bind=db.engine)
Base.metadata.create_all(bind=db.engine)

admin.add_view(ModelView(ATObject,db.session,category='model'))
admin.add_view(VolumeView(Volume, db.session,category='Imaging'))
admin.add_view(BaseView(Ribbon, db.session,category='Imaging'))
admin.add_view(BaseView(MicroscopeRound, db.session,category='Imaging'))

app.run()

