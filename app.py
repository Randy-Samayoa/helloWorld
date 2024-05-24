import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from sqlalchemy import func
from werkzeug.security import check_password_hash, generate_password_hash
from authorize import role_required
from models import *
import pandas as pd
import plotly.express as px
from datetime import datetime

basedir = os.path.abspath(os.path.dirname(__file__))


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'XandClients.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_really_secret_key_here'
db.init_app(app)


login_manager = LoginManager()
login_manager.login_view = 'login_page'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
   return User.query.get(int(user_id))


@app.route('/')
def home_page():
   return render_template('about.html')


@app.route('/login-page', methods =['GET','POST'])
def login_page():
  default_customer_route_function = 'customer_dashboard'
  default_employee_route_function = 'employee_dashboard'
  default_route_function = 'manager_dashboard'

  if request.method == 'GET':
      # Determine where to redirect user if they are already logged in
      if current_user and current_user.is_authenticated:
          if current_user.role in ['MANAGER', 'ADMIN']:
              return redirect(url_for(default_route_function))
          elif current_user.role == 'CUSTOMER':
              return redirect(url_for(default_customer_route_function))
          elif current_user.role == 'EMPLOYEE':
              return redirect(url_for(default_employee_route_function))
      else:
          redirect_route = request.args.get('next')
          return render_template('login_page.html', redirect_route=redirect_route)


  elif request.method == 'POST':
      email = request.form.get('email')
      password = request.form.get('password')
      redirect_route = request.form.get('redirect_route')

      user = User.query.filter_by(email=email).first()

      # Validate user credentials and redirect them to initial destination
      if user and check_password_hash(user.password, password):
          login_user(user)


          if current_user.role in ['MANAGER', 'ADMIN']:
              return redirect(redirect_route if redirect_route else url_for(default_route_function))
          elif current_user.role == 'CUSTOMER':
              return redirect(redirect_route if redirect_route else url_for(default_customer_route_function))
          elif current_user.role == 'EMPLOYEE':
              return redirect(redirect_route if redirect_route else url_for(default_employee_route_function))
      else:
          flash(f'Your login information was not correct. Please try again.', 'error')


      return redirect(url_for('login_page'))

  return redirect(url_for('login_page'))

@app.route('/logout')
@login_required
def logout():
   logout_user()
   flash(f'You have been logged out.', 'success')
   return redirect(url_for('login_page'))

@app.route('/create-account', methods=['GET', 'POST'])
def create_account():
  if request.method == 'POST':
      # Collect the data from form
      email = request.form['email']
      first_name = request.form['first_name']
      last_name = request.form['last_name']
      business_name = request.form['business_name']
      phone = request.form['phone']
      password = request.form['password']

      # Code that queries the user table to ensure the user attempted to be created does not already exist.
      existing_user = User.query.filter_by(email=email).first()
      if existing_user:
          flash('Username already exists')
          return redirect(url_for('create_account'))

      # Create new user and add to database
      new_user = User(
          email=email,
          first_name=first_name,
          last_name=last_name,
          business_name=business_name,
          phone=phone,
          password=generate_password_hash(password, method='pbkdf2:sha256'),
          role='CUSTOMER'  # Default role for new users
      )
      db.session.add(new_user)
      db.session.commit()
      flash(f'Account created successfully! Please login.', 'success')
      return redirect(url_for('login_page'))

  # If it's not a POST request, just display the registration form
  return render_template('create_account.html')


@app.route('/manager-dashboard')
@login_required
@role_required(['MANAGER', 'ADMIN'])
def manager_dashboard():
   pending_requests = Client.query.filter(
        Client.is_approved == None,
        Client.quote == None
    ).all()
   users = User.query.all()
   upcoming_projects = Project.query.all()
   total_employees = sum(1 for user in users if user.role == 'EMPLOYEE')
   total_customers = User.query.filter_by(role='CUSTOMER').count()
   if current_user.role not in ['MANAGER', 'ADMIN']:
       flash('Access denied: Insufficient permissions')
       return redirect(url_for('home_page'))

   return render_template('manager_dashboard.html', pending_requests=pending_requests, users=users, upcoming_projects=upcoming_projects, total_employees=total_employees, total_customers=total_customers)


@app.route('/customer-dashboard')
@login_required
@role_required(['CUSTOMER'])
def customer_dashboard():
   pending_requests = Client.query.filter_by(user_id=current_user.user_id).all()
   notification_count = Notification.query.filter_by(user_id=current_user.user_id, is_read=False).count()
   return render_template('customer_dashboard.html', pending_requests=pending_requests, user_name=f"{current_user.first_name} {current_user.last_name}",
                          notification_count=notification_count)



@app.route('/employee-dashboard')
@login_required
@role_required(['EMPLOYEE'])
def employee_dashboard():
    # Fetching only the first three upcoming assignments for the dashboard display
    assignments = ProjectAssignment.query.join(Project).filter(
        ProjectAssignment.user_id == current_user.user_id
    ).order_by(Project.date_and_time.asc()).limit(3).all()  # Ordering by date and limiting to three entries

    return render_template('employee-dashboard.html', assignments=assignments, user_name=current_user.first_name)





@app.route('/workrequest', methods=['GET', 'POST'])
@login_required
@role_required(['CUSTOMER'])
def work_request_form():
    if request.method == 'GET':
        services = Service.query.order_by(Service.service).all()
        return render_template('workrequest.html', services=services)

    elif request.method == 'POST':
        # Check for missing required fields
        required_fields = ['service_id']
        missing_fields = [field for field in required_fields if not request.form.get(field)]

        if missing_fields:
            flash(f"Please fill in the required fields: {', '.join(missing_fields)}.", 'error')
            return redirect(url_for('work_request_form'))

        # Parse the date and time string to a datetime object
        date_and_time_str = request.form['date_and_time']
        # The format string '%Y-%m-%dT%H:%M' matches the input format '2024-04-20T21:47'
        try:
            date_and_time_obj = datetime.strptime(date_and_time_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Invalid date and time format. Please use the correct format.', 'error')
            return redirect(url_for('work_request_form'))

        # Create a new client in the database with the user ID of the currently logged-in user
        new_client = Client(
            user_id=current_user.user_id,  # Attach the user's ID to the work request
            work_phonenumber=request.form['work_phonenumber'],
            personal_phonenumber=request.form['personal_phonenumber'],
            business_name=request.form['business_name'],
            address=request.form['address'],
            state=request.form['state'],
            city=request.form['city'],
            zipcode=request.form['zipcode'],
            special_request=request.form['special_request'],
            date_and_time=date_and_time_obj,  # Use the parsed datetime object
            quote=None,  # Initially, there is no quote
            quoted=False,  # Initially, not quoted
            service_id=request.form['service_id'],  # Assuming service_id is a single select field
        )

        db.session.add(new_client)
        db.session.commit()

        submitted_data = {
            'work_phonenumber': request.form['work_phonenumber'],
            'personal_phonenumber': request.form['personal_phonenumber'],
            'business_name': request.form['business_name'],
            'address': request.form['address'],
            'state': request.form['state'],
            'city': request.form['city'],
            'zipcode': request.form['zipcode'],
            'special_request': request.form['special_request'],
            'date_and_time': request.form['date_and_time']
        }

        flash('Work request submitted successfully!', 'success')
        return render_template('workrequest.html', form_submitted=True, submitted_data=submitted_data)

    else:
        flash('Invalid request method.', 'error')
        return redirect(url_for('work_request_form'))


@app.route('/previous-requests')
@login_required
@role_required(['CUSTOMER'])
def prev_requests():
   # Query only the work requests that belong to the currently logged-in user
   user_clients = Client.query.filter_by(user_id=current_user.user_id).all()  # corrected attribute reference
   return render_template('previous_work_requests.html', clients=user_clients)


#This is a test route for the database
@app.route('/test')
def test_page():
   clients = Client.query.all()
   return render_template('test.html', clients=clients)


@app.route('/edit-client/<int:client_id>', methods=['GET'])
@login_required
def edit_client(client_id):
   client = Client.query.get_or_404(client_id)
   # Gathering services so they can also be edited along with the rest of the data
   services = Service.query.all()
   return render_template('edit_client.html', client=client, services=services)



@app.route('/update-client/<int:client_id>', methods=['POST'])
@login_required
def update_client(client_id):
   client = Client.query.get_or_404(client_id)

   # Parse the date and time string to a datetime object
   date_and_time_str = request.form['date_and_time']
   # Adjust the format string to match the input
   date_and_time_obj = datetime.strptime(date_and_time_str, "%Y-%m-%dT%H:%M")

   # Update client details based on form submission
   client.work_phonenumber = request.form['work_phonenumber']
   client.personal_phonenumber = request.form['personal_phonenumber']
   client.business_name = request.form['business_name']
   client.address = request.form['address']
   client.state = request.form['state']
   client.city = request.form['city']
   client.zipcode = request.form['zipcode']
   client.special_request = request.form['special_request']
   client.date_and_time = date_and_time_obj
   client.service_id = request.form['service_id']

   db.session.commit()
   flash('Client updated successfully.', 'success')
   return redirect(url_for('prev_requests'))


@app.route('/delete-client/<int:client_id>', methods=['POST'])
@login_required
def delete_client(client_id):
   client = Client.query.get_or_404(client_id)
   db.session.delete(client)
   db.session.commit()
   flash('Client deleted successfully.', 'success')
   return redirect(url_for('prev_requests'))


@app.route('/about-company')
@login_required
def about_company():
   return render_template('about.html')


@app.route('/client-info')
@login_required
@role_required(['ADMIN', 'MANAGER'])
def client_info():

    client_list = User.query.filter_by(role='CUSTOMER').all()

    return render_template('client_info.html', client_list=client_list)

@app.route('/workrequest-receipt')
@login_required
@role_required(['MANAGER', 'ADMIN'])
def workrequest_receipt():
    # Queries the database to look for all work requests where quoted = false.
    unquoted_requests = Client.query.filter_by(quoted=False).all()
    return render_template('work_request_receipt.html', requests=unquoted_requests)

@app.route('/submit-quote/<int:client_id>', methods=['POST'])
@login_required
@role_required(['MANAGER', 'ADMIN'])
def submit_quote(client_id):
    client = Client.query.get_or_404(client_id)
    client.quote = request.form['quote']
    client.square_footage = request.form.get('square_footage', type=int)

    # Parse and set the confirmed start date

    confirmed_date_str = request.form['confirmed_start_date']
    client.confirmed_start_date = datetime.strptime(confirmed_date_str, '%Y-%m-%dT%H:%M')

    client.quoted = True
    db.session.commit()

    # Create a notification for the customer
    notification = Notification(
        message="You have received a quote!",
        user_id=client.user_id
    )
    db.session.add(notification)
    db.session.commit()

    flash('Quote and start date submitted successfully.', 'success')
    return redirect(url_for('workrequest_receipt'))



@app.route('/project-history')
@login_required
@role_required(['MANAGER', 'ADMIN'])
def project_history():
    # Queries the database to look for all work requests.
    all_requests = Project.query.filter_by(is_completed=True).all()
    return render_template('project_history.html', requests=all_requests)


@app.route('/employees', methods=['GET'])
@login_required
@role_required(['ADMIN', 'MANAGER'])
def employees():
    employees_list = User.query.filter_by(role='EMPLOYEE').all()
    return render_template('employee_test.html', employees_list=employees_list)

@app.route('/employee/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@role_required(['MANAGER', 'ADMIN'])
def edit_employee(user_id):
    employee = User.query.get_or_404(user_id)
    if request.method == 'POST':
        employee.first_name = request.form['first_name']
        employee.last_name = request.form['last_name']
        employee.title = request.form['title']
        employee.email = request.form['email']
        employee.phone = request.form['phone']
        db.session.commit()
        flash('Employee succesfully updated!', 'success')
        return redirect(url_for('employees'))
    return render_template('edit_employee.html', employee=employee)


@app.route('/employees/delete/<int:user_id>')
@login_required
@role_required(['MANAGER','ADMIN'])
def employee_delete(user_id):
    employee = User.query.filter_by(user_id=user_id).first()
    print(user_id)
    if employee:
        db.session.delete(employee)
        db.session.commit()
        flash(f'{employee} was successfully deleted!', 'success')
    else:
        flash(f'Delete failed! Employee could not be found.', 'error')

    return redirect(url_for('employees'))

@app.route('/employee-account-creation', methods=['GET', 'POST'])
@login_required
@role_required(['MANAGER','ADMIN'])
def create_employee_account():
   if request.method == 'POST':
       # Collect the data from form
       email = request.form['email']
       first_name = request.form['first_name']
       last_name = request.form['last_name']
       title = request.form['title']
       phone = request.form['phone']
       password = request.form['password']


       # Code that queries the user table to ensure the user attempted to be created does not already exist.
       existing_user = User.query.filter_by(email=email).first()
       if existing_user:
           flash('Account already exists')
           return redirect(url_for('create_employee_account'))


       # Create new user and add to database
       new_user = User(
           email=email,
           first_name=first_name,
           last_name=last_name,
           title=title,
           phone=phone,
           password=generate_password_hash(password, method='pbkdf2:sha256'),
           role='EMPLOYEE'
       )
       db.session.add(new_user)
       db.session.commit()
       flash(f'Account successfully created.', 'success')
       return redirect(url_for('employees'))

   return render_template('create_employee_account.html')


@app.route('/upcoming-appointments')
@login_required
@role_required(['CUSTOMER'])
def upcoming_appointments():
    # Gathering requests that have received a quote from the manager, making quoted true. Only showing info for logged in user
    approved_requests = Client.query.filter_by(user_id=current_user.user_id, quoted=True).all()
    return render_template('upcoming_appointments.html', requests=approved_requests)


@app.route('/approve-request/<int:request_id>', methods=['POST'])
@login_required
@role_required(['CUSTOMER'])
# when approved is pressed on the upcoming_appointments screen, is_approved becomes true --
# -- alloiwng it to pop up on upcoming projects manager side
def approve_request(request_id):
    client_request = Client.query.get_or_404(request_id)
    action = request.form.get('action')  # Get action from form submit

    if action == 'approve':
        client_request.is_approved = True
        date_and_time_obj = datetime.strptime(client_request.confirmed_start_date.strftime("%Y-%m-%dT%H:%M"), "%Y-%m-%dT%H:%M")
        new_project = Project(
            date_and_time=date_and_time_obj,
            work_phonenumber=client_request.work_phonenumber,
            quote=client_request.quote,
            address=client_request.address,
            business_name=client_request.business_name,
            zipcode=client_request.zipcode,
            service_id=client_request.service_id,
            user_id=client_request.user_id,
            workrequest_ID=client_request.workrequest_ID
        )

        db.session.add(new_project)
        db.session.commit()

    elif action == 'deny':
        client_request.is_approved = False
        db.session.commit()

    if action == 'approve':
        flash('Request approved successfully!', 'success')
    else:
        flash('Request denied!', 'error')
    return redirect(url_for('upcoming_appointments'))



@app.route('/upcoming-projects')
@login_required
@role_required(['MANAGER', 'ADMIN'])
def upcoming_projects():
    # Fetching projects that have been approved
    approved_requests = Client.query.filter_by(is_approved=True).all()
    projects = Project.query.all()
    employees = User.query.filter_by(role='EMPLOYEE').all()  # Only fetch users with 'EMPLOYEE' role
    return render_template('upcoming_projects.html', requests=approved_requests, employees=employees, projects=projects)


@app.route('/work-schedule')
@login_required
@role_required(['EMPLOYEE'])
def work_schedule():

    assignments = ProjectAssignment.query.join(Project).filter(ProjectAssignment.user_id == current_user.user_id).all()
    return render_template('work_schedule.html', assignments=assignments)



@app.route('/client-base')
@login_required
def client_base():
   return render_template('client_base.html')


@app.route('/customer-notifications')
@login_required
@role_required(['CUSTOMER'])
def customer_notif():
    # Fetch notifications for the logged-in user
    notifications = Notification.query.filter_by(user_id=current_user.user_id, is_read=False).all()
    return render_template('customer_notif-page.html', notifications=notifications)


@app.route('/handle-notification/<int:notification_id>', methods=['POST'])
@login_required
def handle_notification(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    action = request.form['action']

    if action == 'dismiss':
        db.session.delete(notification)
    else:
        notification.is_read = True

    db.session.commit()
    return redirect(url_for('upcoming_appointments'))



@app.route('/reports')
@login_required
@role_required(['MANAGER', 'ADMIN'])
def reports():
    # chart to show how many projects each employee completed
    top_employees = (db.session.query(
        User.first_name.label('first_name'),
        User.last_name.label('last_name'),
        func.count(Project.project_id).label('project_count')  # counting the number of completed projects
    ).join(ProjectAssignment,
           User.user_id == ProjectAssignment.user_id)  # joining project assignments with user id to that project
        .join(Project, ProjectAssignment.project_id == Project.project_id)
        .filter(User.role == 'EMPLOYEE', Project.is_completed == True) #filtering through employees with completed project status
        .group_by(User.user_id)
        .order_by(func.count(Project.project_id).desc())
        .all())

    # Convert the query result to a DataFrame
    df_top_employees = pd.DataFrame(top_employees, columns=['first_name', 'last_name', 'project_count'])
    #creating a column which combines the employees first and last name, and then concatenating them, if there
    #is no name then the placeholder is "Employee"
    df_top_employees['display_name'] = df_top_employees.apply(
        lambda x: f"{x['first_name']} {x['last_name']}" if x['first_name'] and x['last_name'] else "Employee", axis=1)


    # Create the bar chart
    top_employees_figure = px.bar(
        data_frame=df_top_employees,
        x='display_name',
        y='project_count',
        title='Top Employees by Assigned Projects',
        labels={'display_name': 'Employee', 'project_count': 'Count'},
        color_continuous_scale=['green'],
        text_auto=True
    )

    # Customize the layout
    top_employees_figure.update_layout(
        yaxis={'tickmode': 'linear', 'dtick': 1},
        title={'x': 0.5},
        xaxis_tickangle=-45
    )

        # Convert the figure to JSON for rendering in the template
    top_employees_json = top_employees_figure.to_json()

    # chart to show the number of Work Requests by Service Type
    work_requests_by_service = db.session.query(
        Service.service.label('service_name'),
        func.count(Client.workrequest_ID).label('work_request_count')
    ).join(Service, Client.service_id == Service.service_id) \
        .group_by(Client.service_id) \
        .order_by(Service.service) \
        .all()

    df_work_requests_by_service = pd.DataFrame(work_requests_by_service,
                                               columns=['service_name', 'work_request_count'])

    work_requests_by_service_figure = px.bar(
        data_frame=df_work_requests_by_service,
        x='service_name',
        y='work_request_count',
        title='Number of Work Requests by Service Type',
        labels={'service_name': 'Service Name', 'work_request_count': 'Count'},
        color_discrete_sequence=['blue'],
        text_auto=True
    )

    work_requests_by_service_figure.update_layout(
        yaxis={'tickmode': 'linear', 'dtick': 1},
        title={'x': 0.5},
        xaxis_tickangle=-45
    )

    work_requests_by_service_json = work_requests_by_service_figure.to_json()

    # chart to show average quote amount by service
    average_quote_by_service = db.session.query(
        Service.service.label('service_name'),
        func.avg(Client.quote).label('average_quote')
    ).join(Client, Service.service_id == Client.service_id) \
        .group_by(Service.service_id) \
        .order_by(Service.service) \
        .all()

    df_average_quote_by_service = pd.DataFrame(average_quote_by_service, columns=['service_name', 'average_quote'])

    # creation of chart
    average_quote_figure = px.bar(
        data_frame=df_average_quote_by_service,
        x='service_name',
        y='average_quote',
        title='Average Quote Amount by Service',
        labels={'service_name': 'Service', 'average_quote': 'Quote Amount ($)'},
        color_discrete_sequence=['green'],
        text_auto=True
    )
    # customization
    average_quote_figure.update_layout(
        yaxis={
            'tickprefix': '$',
            'tickmode': 'linear',
            'dtick': 100
        },
        title={'x': 0.5},
        xaxis_tickangle=-45
    )

    average_quote_json = average_quote_figure.to_json()

    return render_template('reports.html', top_employees_graph=top_employees_json,
                           work_requests_by_service_graph=work_requests_by_service_json,
                           average_quote_graph=average_quote_json)


@app.route('/assign-employees/<int:project_id>', methods=['POST'])
@login_required
@role_required(['MANAGER', 'ADMIN'])
def assign_employees(project_id):
    project = Project.query.get_or_404(project_id)

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update':
            # Resetting is_assigned to allow new assignments
            ProjectAssignment.query.filter_by(project_id=project.project_id).delete()  # Clear existing assignments
            project.is_assigned = False
        else:
            selected_user_ids = request.form.getlist('employee_ids[]')
            ProjectAssignment.query.filter_by(project_id=project.project_id).delete()  # Clear existing assignments

            for user_id in selected_user_ids:
                user = User.query.get(int(user_id))
                if user and user.role == 'EMPLOYEE':
                    new_assignment = ProjectAssignment(project_id=project.project_id, user_id=user.user_id)
                    db.session.add(new_assignment)

            project.is_assigned = True  # Mark as assigned

        db.session.commit()
        flash('Employee assignments updated successfully!', 'success')
        return redirect(url_for('upcoming_projects', project=project_id))
    else:
        flash('Invalid method', 'error')
        return redirect(url_for('upcoming_projects', project=project, employees=employees))

@app.route('/complete-project/<int:project_id>', methods=['POST'])
@login_required
@role_required(['MANAGER', 'ADMIN'])
def complete_project(project_id):
    project = Project.query.get_or_404(project_id)
    project.is_completed = not project.is_completed
    db.session.commit()

    if project.is_completed == True:
        flash('Project marked as completed.', 'success')

    else:
        flash('Project marked as incomplete.', 'success')
    return redirect(url_for('upcoming_projects'))
