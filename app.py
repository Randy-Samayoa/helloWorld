from flask import Flask, render_template

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

@app.route('/aboutcss')
def about2():
    return render_template('about-css.html')

if __name__ == '__main__':
    app.run()
