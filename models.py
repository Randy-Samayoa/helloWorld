from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()


class Client(db.Model):
  __tablename__ = "client"

  workrequest_ID = db.Column(db.Integer, primary_key=True)
  work_phonenumber = db.Column(db.VARCHAR(20), nullable=False)
  personal_phonenumber = db.Column(db.VARCHAR(20), nullable=False)
  business_name = db.Column(db.String(100), nullable=False)
  address = db.Column(db.VARCHAR(100), nullable=False)
  state = db.Column(db.String(2), nullable=False)
  city = db.Column(db.String(100), nullable=False)
  zipcode = db.Column(db.Integer, nullable=False)
  special_request = db.Column(db.Text, nullable=True)
  date_and_time = db.Column(db.DateTime, nullable=False)
  confirmed_start_date = db.Column(db.DateTime, nullable=True)  # New field for confirmed start date
  quote = db.Column(db.Text, nullable=True)
  quoted = db.Column(db.Boolean, default=False, nullable=False)
  is_approved = db.Column(db.Boolean, default=None, nullable=True)  # Track approval status
  square_footage = db.Column(db.Integer, nullable=True)
  service_id = db.Column(db.Integer, db.ForeignKey('service.service_id'), nullable=False) # Connects service table
  user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))  # Connects user table

  user = db.relationship('User', backref='clients')  # This will allow access to User via Client.user

  def __init__(self, work_phonenumber, personal_phonenumber, business_name, address,
               state, city, zipcode, special_request, date_and_time, quote, quoted, service_id, user_id, square_footage= None):  # Add user_id here
      self.work_phonenumber = work_phonenumber
      self.personal_phonenumber = personal_phonenumber
      self.business_name = business_name
      self.address = address
      self.state = state
      self.city = city
      self.zipcode = zipcode
      self.special_request = special_request
      self.date_and_time = date_and_time
      self.quote = quote
      self.quoted = quoted
      self.square_footage = square_footage
      self.service_id = service_id
      self.user_id = user_id  # Set the user_id

  def __repr__(self):
      return f"{self.business_name}"




class Project(db.Model):
  __tablename__ = 'projects'

  project_id = db.Column(db.Integer, primary_key=True)
  date_and_time = db.Column(db.DateTime, nullable=False)
  address = db.Column(db.VARCHAR(100), nullable=False)
  zipcode = db.Column(db.Integer, nullable=False)
  is_assigned = db.Column(db.Boolean, default=False, nullable=True)
  is_completed = db.Column(db.Boolean, default=False, nullable=True)
  work_phonenumber = db.Column(db.Integer, nullable=False)
  quote = db.Column(db.Integer, nullable=False)
  business_name = db.Column(db.String(100), nullable=False)
  service_id = db.Column(db.Integer, db.ForeignKey('service.service_id'),nullable=False)# Linking to Service table
  user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))
  # project_quote = db.Column(db.Float)  # Assuming Quote History has a relationship to this
  workrequest_ID = db.Column(db.Integer, db.ForeignKey('client.workrequest_ID'),nullable=False)  # Linking to Client table

# Relationships
  client = db.relationship('Client', backref='projects')
  service = db.relationship('Service', backref='projects')
  user = db.relationship('User', backref='projects')
  assignments = db.relationship('ProjectAssignment', backref='project', lazy='dynamic')




#Removed project_quote from the function in the parenthesis and in the parameter self until the table is mad

def __init__(self, date_and_time, address, zipcode, service_id, user_id, workrequest_ID):
    self.date_and_time = date_and_time
    self.address = address
    self.zipcode = zipcode
    self.service_id = service_id
    self.user_id = user_id
    self.workrequest_ID = workrequest_ID

def __repr__(self):
    return f'<Project {self.project_id}, Client {self.client_id}, Service {self.service_id}>'


class EmployeeSchedule(db.Model):
  __tablename__ = 'employee_schedule'

  project_id = db.Column(db.Integer, db.ForeignKey('projects.project_id'), primary_key=True)
  employee_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), primary_key=True)
  # Assuming the existence of a Project table with 'project_id' as a primary key
  # and a User table with 'user_id' as a primary key that represents an employee.

  # Assuming 'scheduled_at' is a datetime column that represents when the employee is scheduled for the projects
  scheduled_at = db.Column(db.DateTime, nullable=False)

  # Relationships
  project = db.relationship('Project', backref='employee_schedule')
  employees = db.relationship('User', backref='employee_schedule')

  def __init__(self, project_id, employee_id, scheduled_at):
      self.project_id = project_id
      self.employee_id = employee_id
      self.scheduled_at = scheduled_at

  def __repr__(self):
      return f'<EmployeeSchedule project_id={self.project_id} employee_id={self.employee_id}>'


class Service(db.Model):
  __tablename__ = "service"

  service_id = db.Column(db.Integer, primary_key=True)
  service = db.Column(db.String(30), nullable=False)
  clients = db.relationship("Client", backref="service")

  def __init__(self, service):
      self.service = service

  def __repr__(self):
      return f"{self.service}"


class User(UserMixin, db.Model):
 __tablename__ = "user"

 user_id = db.Column(db.Integer, primary_key=True)
 first_name = db.Column(db.String(30))
 last_name = db.Column(db.String(50))
 email = db.Column(db.String(100), unique=True)
 password = db.Column(db.String(100))
 title = db.Column(db.String(50), nullable=True)
 phone = db.Column(db.String(13), nullable=True)
 role = db.Column(db.String(20))
 business_name = db.Column(db.String(100), nullable=True)

 def __init__(self, first_name, last_name, email, password, title=None, phone=None, role='PUBLIC', business_name=None):
     self.first_name = first_name
     self.last_name = last_name
     self.email = email
     self.password = password
     self.title = title
     self.phone = phone
     self.role = role
     self.business_name = business_name


     # Function for flask_login manager to provider a user ID to know who is logged in
 def get_id(self):
     return (self.user_id)


 def __repr__(self):
     return f"{self.first_name} {self.last_name} ({self.email})"


class ProjectAssignment(db.Model):
    __tablename__ = 'project_assignments'
    project_id = db.Column(db.Integer, db.ForeignKey('projects.project_id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), primary_key=True)  # Changed from employee_id to user_id

    # Relationship
    user = db.relationship(User, backref=db.backref('project_assignments', cascade="all, delete-orphan"))



class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    message = db.Column(db.String(256), nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)  # Automatically sets to current date/time

    user = db.relationship('User', backref='notifications')
