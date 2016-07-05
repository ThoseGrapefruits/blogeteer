"""
    Plopateer
    ~~~~~~~~~

    A minimal photo- and project-based microblog/website builder.

    Draws heavily from the ``Flaskr'' example for Flask:
    https://github.com/pallets/flask/tree/master/examples/flaskr

    :copyright: (c) 2016 by Logan Moore.
    :license: BSDv3, see LICENSE for more details.
"""
from sqlite3 import dbapi2 as sqlite

import os
from flask import Flask, request, g, session, redirect, flash, abort, url_for, render_template
from wtforms import StringField, PasswordField, FileField, validators, RadioField, TextAreaField
from flask_wtf import Form

# noinspection PyUnresolvedReferences
from passlib.hash import pbkdf2_sha256
from werkzeug.utils import secure_filename
import datetime
from PIL import Image
import re

# Load Flask
app = Flask(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'plop.db'),
    DEBUG=True,
    SECRET_KEY='development key',
    REGISTRATION=True,
    ALLOWED_EXTENSIONS={'png', 'jpg', 'jpeg', 'gif'},
    UPLOAD_DIR=os.path.join(app.root_path, 'media'),
    REGEXP={'username': re.compile(r'^([A-Za-z\d]+)$'),
            'filename': re.compile(r'^[^/\\]+\.jpg$')}
))
app.config.from_envvar('PLOP_SETTINGS', silent=True)


# ------------------------------------------------------------------------------------------------

# DATABASES
def connect_db():
    """Connects to the specific database."""
    rv = sqlite.connect(app.config['DATABASE'])
    rv.row_factory = sqlite.Row
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


# ------------------------------------------------------------------------------------------------

# ROUTING

@app.route('/')
def home():
    db = get_db()
    cur = db.execute('select title, author, body, media from entries order by id desc')
    entries = cur.fetchall()
    return render_template('entries.html', entries=entries)


@app.route('/new', methods=['GET', 'POST'])
def new():
    if not session.get('logged_in'):
        abort(401)
    form = EntryForm(request.form)
    if request.method == 'POST' and form.validate():
        db = get_db()
        db.execute('insert into entries (title, body) values (?, ?)',
                   (request.form['title'], request.form['body']))
        db.commit()
        flash('New entry was successfully posted')
        return redirect(url_for('home'))
    return render_template('new.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        db = get_db()
        cur = db.execute('select id, username, passhash from users where username=?',
                         (request.form['username'],))
        entry = cur.fetchone()

        if entry is None:
            error = 'Invalid username'
        elif not pbkdf2_sha256.verify(request.form['password'], entry['passhash']):
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You are logged in')
            return redirect(url_for('home'))
    return render_template('login.html', error=error, dest='login', val='Login', form=form)


@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    pass  # TODO


@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        db = get_db()
        db.execute('insert into users (username, email, passhash) values (?, ?, ?)',
                   (form.username.data, form.email.data,
                    pbkdf2_sha256.encrypt(form.password.data, rounds=200000, salt_size=16)))
        db.commit()
        session['logged_in'] = True
        flash('Thanks for registering')
        return redirect(url_for('home'))
    return render_template('login.html', error=error, dest='register', val='Register', form=form)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('home'))


@app.route('/post/<int:post_id>')
def entry_by_id(post_id):
    db = get_db()
    entry = db.execute('select title, author, body, media from entries where id=?', str(post_id)) \
        .fetchone()
    return render_template('entry.html', title=entry['title'], body=entry['body'])


@app.route('/post/<post_name>')
def entry_by_name(post_name):
    # NOTE: prefix posts with number-only titles
    return 'Post {}'.format(post_name)  # TODO


@app.route('/user/<int:user_id>')
def profile_by_id(user_id):
    db = get_db()
    entry = db.execute('select username, fullname, bio from users where id=?', str(user_id)) \
        .fetchone()
    name = '{} ({})'.format(entry['fullname'], entry['username']) if entry['fullname'] \
        else entry['username']
    return render_template('entry.html', title=name, body=entry['bio'])


@app.route('/user/<username>')
def profile(username):
    db = get_db()
    entry = db.execute('select username, fullname, bio from users where username=?', username) \
        .fetchone()
    name = '{} ({})'.format(entry['fullname'], entry['username']) \
        if entry['fullname'] else entry['username']
    return render_template('entry.html', title=name, body=entry['bio'])


# ------------------------------------------------------------------------------------------------

# FORMS

class LoginForm(Form):
    username = StringField('Username', (validators.Length(min=1, max=32),
                                        validators.regexp(r'^([A-Za-z0-9]+)$')))
    password = PasswordField('Password', (validators.Length(min=8, max=128),))


class RegistrationForm(LoginForm):
    email = StringField('Email Address', (validators.Email(), validators.Length(min=6, max=128)))


class EntryForm(Form):
    """Base form for entries of all kinds"""
    title = StringField('Title', (validators.InputRequired(), validators.Length(max=128)))
    radio = RadioField('Label', choices=[('value', 'description'), ('value_two', 'whatever')])
    files = FileField(u'Image File(s)', (validators.regexp(app.config['REGEXP']['filename']),),
                      render_kw={'multiple': True})
    body = TextAreaField('Body', (validators.Length(max=1000000),),
                         render_kw={'cols': 35, 'rows': 20})


class MediaEntryForm(EntryForm):
    """Form for entries containing media (media galleries, pictures, etc)"""


class TextEntryForm(EntryForm):
    """Form for text-only entries"""


def canonicalize(username):
    """
    Canonicalize the given username. Given the requirements on usernames to be alphanumeric, this
    will only put the username to lowercase in practice.

    :param username:
    :type   username: str
    :return:
    """
    if re.match(app.config['REGEXP']['username'], username):
        return username.lower()


# ------------------------------------------------------------------------------------------------

# FILE PROCESSING


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']


def save_dir():
    timetuple = datetime.datetime.now().utctimetuple()

    path = os.path.join(app.config['UPLOAD_DIR'], timetuple[0:3])

    os.makedirs(path, mode=0o770, exist_ok=True)

    return path


def save_paths(*filenames):
    base_dir = save_dir()
    for filename in filenames:
        yield os.path.join(base_dir, secure_filename(filename))


class SubImage:
    size = 2048, 2048
    suffix = 'small'

    def get_sub_path(self, file_path):
        splitext = os.path.splitext(file_path)
        return '{}{}.{}x{}.{}'.format(os.path.dirname(), splitext[0],
                                      self.size[0], self.size[1], splitext[1])

    def resize(self, file_path):
        out_file = self.get_sub_path(file_path)
        if file_path != out_file:
            try:
                image = Image.open(file_path)
                image.thumbnail(self.size)
                image.save(out_file)
            except IOError:
                message = "Cannot create thumbnail for {}".format(os.path.basename(file_path))
                flash(message)
                print(message)


class SubSubImage(SubImage):
    size = 1024, 1024
    suffix = 'verysmall'


class TinyImage(SubImage):
    size = 512, 512
    suffix = 'tiny'


class TinyTinyImage(SubImage):
    size = 256, 256
    suffix = 'verytiny'


class ThumbnailImage(SubImage):
    size = 128, 128
    suffix = 'thumb'


# ------------------------------------------------------------------------------------------------

# MAIN


if __name__ == '__main__':
    app.run()
