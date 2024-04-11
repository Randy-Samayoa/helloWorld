import os
from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, Student, Major
from datetime import datetime as dt

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'university.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'beyond_course_scope'
db.init_app(app)

#This route belongs to the student view page
@app.route('/student/view')
def student_view_all():
    students = Student.query.outerjoin(Major, Student.major_id == Major.major_id) \
        .add_entity(Major) \
        .order_by(Student.last_name, Student.first_name) \
        .all()
    return render_template('student_view_all.html', students=students)

#This code handles the query for student ID. If the student that is attempted to be viewed does not exist, it will return a message
@app.route('/student/view/<int:student_id>')
def student_view(student_id):
    student = Student.query.filter_by(student_id=student_id).first()
    majors = Major.query.order_by(Major.major) \
        .order_by(Major.major) \
        .all()

    if student:
        return render_template('student_entry.html', student=student, majors=majors, action='read')

    else:
        flash(f'Student attempting to be viewed could not be found!', 'error')
        return redirect(url_for('student_view_all'))


#This route handles the function of creating a new entry. The entry includes first name, last name, student email, and major id
@app.route('/student/create', methods=['GET', 'POST'])
def student_create():
    if request.method == 'GET':
        majors = Major.query.order_by(Major.major) \
            .order_by(Major.major) \
            .all()
        return render_template('student_entry.html', majors=majors, action='create')
    elif request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        student_email = request.form['student_email']
        major_id = request.form['major_id']

        birth_date = request.form['birth_date']
        is_honors = True if 'is_honors' in request.form else False

        student = Student(first_name=first_name, last_name=last_name, student_email=student_email, major_id=major_id,
                          birth_date=dt.strptime(birth_date, '%Y-%m-%d'), is_honors=is_honors)
        db.session.add(student)
        db.session.commit()
        flash(f'{first_name} {last_name} was successfully added!', 'success')
        return redirect(url_for('student_view_all'))

    flash('Invalid action. Please try again.', 'error')
    return redirect(url_for('student_view_all'))

#This code deals with updating an existing student entry. A message will apear to confirm the existing student has been updated
#The code will send a message if the student does not exist
@app.route('/student/update/<int:student_id>', methods=['GET', 'POST'])
def student_edit(student_id):
    if request.method == 'GET':
        student = Student.query.filter_by(student_id=student_id).first()
        majors = Major.query.order_by(Major.major) \
            .order_by(Major.major) \
            .all()

        if student:
            return render_template('student_entry.html', student=student, majors=majors, action='update')

        else:
            flash(f'Student attempting to be edited could not be found!', 'error')

    elif request.method == 'POST':
        student = Student.query.filter_by(student_id=student_id).first()

        if student:
            student.first_name = request.form['first_name']
            student.last_name = request.form['last_name']
            student.email = request.form['student_email']
            student.major_id = request.form['major_id']
            student.birthdate = dt.strptime(request.form['birth_date'], '%Y-%m-%d')
            student.num_credits_completed = request.form['num_credits_completed']
            student.gpa = request.form['gpa']
            student.is_honors = True if 'is_honors' in request.form else False

            db.session.commit()
            flash(f'{student.first_name} {student.last_name} was successfully updated!', 'success')
        else:
            flash(f'Student attempting to be edited could not be found!', 'error')

        return redirect(url_for('student_view_all'))

    return redirect(url_for('student_view_all'))

#This code deals with deleting a student entry
@app.route('/student/delete/<int:student_id>')
def student_delete(student_id):
    student = Student.query.filter_by(student_id=student_id).first()

    if student:
        db.session.delete(student)
        db.session.commit()
        flash(f'{student} was successfully deleted!', 'success')
    else:
        flash(f'Delete failed! Student could not be found.', 'error')

    return redirect(url_for('student_view_all'))

@app.route('/')
def home():
    return redirect(url_for('student_view_all'))


if __name__ == '__main__':
    app.run()
