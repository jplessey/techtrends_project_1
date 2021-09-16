import sqlite3
import json
import logging
from datetime import date, datetime
from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort


# Function to get a database connection.
# This function connects to database with the name `database.db`
def count_calls(f):
    def wrapped(*args, **kwargs):
        wrapped.calls += 1
        return f(*args, **kwargs)
    wrapped.calls = 0
    return wrapped


@count_calls
def get_db_connection():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    return connection


# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post


# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'
logging.basicConfig(level=logging.DEBUG)
log_timestamp = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")


# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)


# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
      app.logger.info('{}, Non-existing article accessed. 404 page returned!'.format(log_timestamp))
      return render_template('404.html'), 404
    else:
      title = post['title']
      app.logger.info('{}, Article "{}" retrieved!'.format(log_timestamp, title))
      return render_template('post.html', post=post)


# Define the About Us page
@app.route('/about')
def about():
    app.logger.info('{}, "About Us" page retrieved!'.format(log_timestamp))
    return render_template('about.html')


# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()

            app.logger.info('{}, Article "{}" created!'.format(log_timestamp, title))
            return redirect(url_for('index'))

    return render_template('create.html')


@app.route('/healthz')
def healthz():
    response = app.response_class(
        response=json.dumps({"result":"OK - healthy"}),
        status=200,
        mimetype='application/json'
    )
    return response


@app.route('/metrics')
def metrics():
    connection = get_db_connection()
    num_of_posts = connection.execute('SELECT COUNT(*) FROM posts').fetchone()[0]
    connection.close()
    response = app.response_class(
        response=json.dumps({"db_connection_count": get_db_connection.calls, "post_count": num_of_posts}),
        status=200,
        mimetype='application/json'
    )

    return response


# start the application on port 3111
if __name__ == "__main__":
    app.run(host='0.0.0.0', port='3111')
 