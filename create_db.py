from app import app, db
from models import *
from datetime import datetime
from werkzeug.security import generate_password_hash

with app.app_context():
  db.drop_all()
  db.create_all()


  # Initial loading of services to be picked
  services = ['Carpet Cleaning', 'Water Damage', 'Stone Damage', 'Destruction Cleaning']
  for each_service in services:
      print(each_service)
      a_service = Service(service=each_service)
      db.session.add(a_service)
  db.session.commit()

  # Initial loading of users
  users = [
      {'email': 'admin@example.com', 'first_name': 'Admin', 'last_name': 'User',
       'password': generate_password_hash('securepassword', method='pbkdf2:sha256'), 'role': 'ADMIN'},
      {'email': 'manager@example.com', 'first_name': 'Manager', 'last_name': 'User',
       'password': generate_password_hash('securepassword', method='pbkdf2:sha256'), 'role': 'MANAGER'},
      {'email': 'customer@example.com', 'first_name': 'Customer', 'last_name': 'User',
       'password': generate_password_hash('securepassword', method='pbkdf2:sha256'), 'role': 'CUSTOMER'},
      {'email': 'employee@example.com', 'first_name': 'Employee', 'last_name': 'User', 'title': 'cleaner',
       'phone': '301',
       'password': generate_password_hash('securepassword', method='pbkdf2:sha256'), 'role': 'EMPLOYEE'}
  ]

  for each_user in users:
      print(f'{each_user["email"]} inserted into user')
      a_user = User(email=each_user["email"], first_name=each_user["first_name"],
                    last_name=each_user["last_name"], password=each_user["password"],
                    title=each_user.get("title", "default-title"),
                    phone=each_user.get("phone", "default-phone"), role=each_user["role"])
      db.session.add(a_user)
  db.session.commit()

  # Adding the code that populates data for clients
  clients = [
        {"work_phonenumber": "240-300-8583",
          "personal_phonenumber": "301-010-8493",
          "business_name": "Robert H. Smith Business School",
          "address": "7500 Mowatt Lane",
          "state": "MD",
          "city": "College Park",
          "zipcode": 20740,
          "special_request": "Please avoid the kitchen area",
          "date_and_time": datetime.strptime("2023-04-05 10:00:00", "%Y-%m-%d %H:%M:%S"),
          "quote": None,  # Assuming no quote is provided initially
          "quoted": False,  # Initially no quote has been sent
         "square_footage": None,
          "service_id": 1,
          "user_id": 1},]

  for each_client in clients:
      print(f'{each_client["business_name"]} inserted into Client')
      a_Client = Client(
          work_phonenumber=each_client["work_phonenumber"], personal_phonenumber=each_client["personal_phonenumber"],
          business_name=each_client["business_name"],
          address=each_client["address"], state=each_client["state"],
          city=each_client["city"], zipcode=each_client["zipcode"],
          special_request=each_client["special_request"], date_and_time=each_client["date_and_time"],
          quote=each_client["quote"], quoted=each_client["quoted"], square_footage=each_client["square_footage"],
          service_id=each_client["service_id"], user_id=each_client["user_id"]
      )
      db.session.add(a_Client)
  db.session.commit()





