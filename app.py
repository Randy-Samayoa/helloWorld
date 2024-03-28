from flask import Flask, render_template, request

app = Flask(__name__)


@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World! Randy Samayoa from Robert H. Smith. I am adding my first code change'

@app.route('/hello')
def hello():
    return render_template('hello.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/about-css')
def about_css():
    return render_template('about-css.html')

@app.route('/favorite-course')
def favorite_course():
    subject = request.args.get('subject', '')
    course_number = request.args.get('course_number', '')
    print('subject entered: ' + subject)
    print('course number entered: ' + course_number)
    return render_template('favorite-course.html', subject=subject, course_number=course_number)

@app.route('/contact',methods = ['GET', 'POST'])
def contact():
    if request.method == 'POST':
        return render_template('contact.html', form_submitted = True)
    else:
        return render_template('contact.html')

if __name__ == '__main__':
    app.run()
