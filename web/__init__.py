from flask import Flask
from flask_login import LoginManager
from peewee import *
from playhouse.db_url import connect
import os
import logging


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = Flask(__name__, static_folder= 'templates')
app.secret_key = os.environ.get('SECRET_KEY') or 'YQ^gKfWGLL4#y@JqdZxBpkCoiAuGaC97'
login_manager = LoginManager(app)
login_manager.login_view = "login"

# #db = connect(os.environ.get('DATABASE') or 'postgres://yelp:yelp@localhost/yelp')
db = connect(os.environ.get('DATABASE') or 'postgres://postgres:password@localhost:5432/sample')

# Bring in views and models
from web import views
# from web import models

