"""
    Plopateer
    ~~~~~~~~~

    A minimal photo- and project-based microblog/website builder.

    Draws heavily from the ``Flaskr'' example for Flask:
    https://github.com/pallets/flask/tree/master/examples/flaskr

    :copyright: (c) 2016 by Logan Moore.
    :license: BSDv3, see LICENSE for more details.
"""
import os
from flask import Flask, request, g, render_template
from sqlite3 import dbapi2 as sqlite3

# Load Flask
app = Flask(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'plop.db'),
    DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
))
app.config.from_envvar('PLOP_SETTINGS', silent=True)


@app.route('/')
def home():
    db = get_db()
    cur = db.execute('select title, text from entries order by id desc')
    entries = cur.fetchall()
    return render_template('entries.html', entries=entries)


def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def init_db():
    """Initializes the database."""
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


@app.cli.command('initdb')
def initdb_command():
    """Creates the database tables."""
    init_db()
    print('Initialized the database.')


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        pass  # login
    else:
        pass  # login form


@app.route('/logout')
def logout():
    pass


@app.route('/post/<int:post_id>')
def post_by_id(post_id):
    return 'Post #{}'.format(post_id)


@app.route('/post/<post_name>')
def post_by_name(post_name):
    # NOTE: prefix posts with number-only titles
    return 'Post {}'.format(post_name)


@app.route('/user/<int:user_id>')
def profile_by_id(user_id):
    return 'User #{}'.format(user_id)


@app.route('/user/<username>')
def profile(username):
    return 'User {}'.format(username)


if __name__ == '__main__':
    app.run()
