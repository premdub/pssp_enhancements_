from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort, session, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager 

from base64 import b64encode
import base64
from io import BytesIO #Converts data from Database into bytes

from dotenv import load_dotenv
import os
import datetime
import uuid



db = SQLAlchemy()

load_dotenv()

mysql_user = os.getenv("MYSQL_USER")
mysql_password = os.getenv("MYSQL_PASSWORD")
mysql_hostname = os.getenv("MYSQL_HOSTNAME")

db = SQLAlchemy()
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqldb://' + mysql_user + ':' + mysql_password + '@' + mysql_hostname + ':3306/patient_portal'
# function to keep track of database changes within python environment and then save it to special file.
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# random characters/numbers for connection that will be forming to mysql. 
app.secret_key = 'sdf#$#dfjkhdf0SDJH0df9fd98343fdfu34rf'

db.init_app(app)

### Models ###
class Users(db.Model):
    __tablename__ = 'production_accounts'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    account_type = db.Column(db.String(80), nullable=False)
    mrn = db.Column(db.String(80), unique=True, nullable=False)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    last_login = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    def __init__(self, username, password, email, account_type, mrn, date_created, last_login):
        self.username = username
        self.password = password
        self.email = email
        self.account_type = account_type
        self.mrn = mrn
        self.date_created = date_created
        self.last_login = last_login


    def to_json(self):
        return {
            'id': self.id,
            'username': self.username,
            'password': self.password,
            'email': self.email,
            'account_type': self.account_type,
            'mrn': self.mrn,
            'date_created': self.date_created,
            'last_login': self.last_login
        }

class Patients(db.Model):
    __tablename__ = 'patients'

    id = db.Column(db.Integer, primary_key=True)
    mrn = db.Column(db.String(255))
    first_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
    zip_code = db.Column(db.String(255), nullable=True)
    dob = db.Column(db.String(255), nullable=True)
    gender = db.Column(db.String(255), nullable=True)
    contact_mobile = db.Column(db.String(255), nullable=True)
    contact_home = db.Column(db.String(255), nullable=True)

    # this first function __init__ is to establish the class for python GUI
    def __init__(self, mrn, first_name, last_name, zip_code, dob, gender, contact_mobile, contact_home):
        self.mrn = mrn
        self.first_name = first_name
        self.last_name = last_name
        self.zip_code = zip_code
        self.dob = dob
        self.gender = gender
        self.contact_mobile = contact_mobile
        self.contact_home = contact_home


    # this second function is for the API endpoints to return JSON 
    def to_json(self):
        return {
            'id': self.id,
            'mrn': self.mrn,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'zip_code': self.zip_code,
            'dob': self.dob,
            'gender': self.gender,
            'contact_mobile': self.contact_mobile,
            'contact_home': self.contact_home
        }

class Conditions_patient(db.Model):
    __tablename__ = 'patient_conditions'

    id = db.Column(db.Integer, primary_key=True)
    mrn = db.Column(db.String(255), db.ForeignKey('patients.mrn'))
    icd10_code = db.Column(db.String(255), db.ForeignKey('conditions.icd10_code'))

    # this first function __init__ is to establish the class for python GUI
    def __init__(self, mrn, icd10_code):
        self.mrn = mrn
        self.icd10_code = icd10_code

    # this second function is for the API endpoints to return JSON
    def to_json(self):
        return {
            'id': self.id,
            'mrn': self.mrn,
            'icd10_code': self.icd10_code
        }

class Conditions(db.Model):
    __tablename__ = 'conditions'

    id = db.Column(db.Integer, primary_key=True)
    icd10_code = db.Column(db.String(255))
    icd10_description = db.Column(db.String(255))

    # this first function __init__ is to establish the class for python GUI
    def __init__(self, icd10_code, icd10_description):
        self.icd10_code = icd10_code
        self.icd10_description = icd10_description

    # this second function is for the API endpoints to return JSON
    def to_json(self):
        return {
            'id': self.id,
            'icd10_code': self.icd10_code,
            'icd10_description': self.icd10_description
        }

class Medications_patient(db.Model):
    __tablename__ = 'patient_medications'

    id = db.Column(db.Integer, primary_key=True)
    mrn = db.Column(db.String(255), db.ForeignKey('patients.mrn'))
    med_ndc = db.Column(db.String(255), db.ForeignKey('medications.med_ndc'))

    # this first function __init__ is to establish the class for python GUI
    def __init__(self, mrn, med_ndc):
        self.mrn = mrn
        self.med_ndc = med_ndc

    # this second function is for the API endpoints to return JSON
    def to_json(self):
        return {
            'id': self.id,
            'mrn': self.mrn,
            'med_ndc': self.med_ndc
        }
    
class Medications(db.Model):
    __tablename__ = 'medications'

    id = db.Column(db.Integer, primary_key=True)
    med_ndc = db.Column(db.String(255))
    med_human_name = db.Column(db.String(255))

    # this first function __init__ is to establish the class for python GUI
    def __init__(self, med_ndc, med_human_name):
        self.med_ndc = med_ndc
        self.med_human_name = med_human_name

    # this second function is for the API endpoints to return JSON
    def to_json(self):
        return {
            'id': self.id,
            'med_ndc': self.med_ndc,
            'med_human_name': self.med_human_name
        }

#--------------------------------------
class Procedures(db.Model):
    __tablename__ = 'treatments_procedures'

    id = db.Column(db.Integer, primary_key=True)
    cpt_code = db.Column(db.String(255))
    cpt_description = db.Column(db.String(255))

    # this first function __init__ is to establish the class for python GUI
    def __init__(self, proc_cpt, proc_desc):
        self.cpt_code = cpt_code
        self.cpt_description = cpt_description

    # this second function is for the API endpoints to return JSON
    def to_json(self):
        return {
            'id': self.id,
            'cpt_code': self.cpt_code,
            'cpt_description': self.cpt_description
        }


class Procedures_Patient(db.Model):
    __tablename__ = ': patient_treatments_procedures'

    id = db.Column(db.Integer, primary_key=True)
    mrn = db.Column(db.String(255), db.ForeignKey('patients.mrn'))
    cpt_code = db.Column(db.String(255), db.ForeignKey(
        'procedure.cpt_code'))

    # this first function __init__ is to establish the class for python GUI
    def __init__(self, mrn, cpt_code):
        self.mrn = mrn
        self.cpt_code = cpt_code

    # this second function is for the API endpoints to return JSON
    def to_json(self):
        return {
            'id': self.id,
            'mrn': self.mrn,
            'cpt_code': self.cpt_code
        }


class Patients_Photos(db.Model):
    __tablename__ = 'patient_photos'

    id = db.Column(db.Integer, primary_key=True)
    mrn = db.Column(db.String(255))
    photo_data = db.Column(db.LargeBinary, nullable=False)
    photo_data_rendered = db.Column(db.String(255), nullable=True)

    # this first function __init__ is to establish the class for python GUI
    def __init__(self, mrn, photo_data, photo_data_rendered):
        self.mrn = mrn
        self.photo_data = photo_data
        self.photo_data_rendered = photo_data_rendered

    # this second function is for the API endpoints to return JSON
    def to_json(self):
        return {
            'id': self.id,
            'photo_data': self.photo_data,
            'photo_data_rendered': self.photo_data_rendered
        }

