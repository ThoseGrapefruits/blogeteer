"""
    Blogeteer
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
import flask_login
from flask_wtf import Form, CsrfProtect
from wtforms import StringField, PasswordField, FileField, validators, RadioField, TextAreaField

from passlib.hash import pbkdf2_sha256
from werkzeug.utils import secure_filename
import datetime
from PIL import Image
import re

# Load Flask
app = Flask(__name__)
CsrfProtect(app)

# Load default config and override config from an environment variable
app.config.update(dict(
    ALLOWED_EXTENSIONS=('png', 'jpg', 'jpeg', 'gif'),
    DATABASE=os.path.join(app.root_path, 'blogeteer.db'),
    DEBUG=True,
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,
    REGISTRATION=True,
    REGEXP={
        'username': re.compile(r'^([A-Za-z\d]+)$'),
        'filename': re.compile(r'^[^/\\]+\.jpg$'),
        'char_slug': re.compile(r'[-a-zA-Z0-9]'),
        'char_non_slug': re.compile(r'[^-a-zA-Z0-9]'),
        'dashes': re.compile(r'-{2,}')},
    SECRET_KEY='development key',
    UPLOAD_DIR=os.path.join(app.root_path, 'media'),
))
app.config.from_envvar('BLOGETEER_SETTINGS', silent=True)

# ------------------------------------------------------------------------------------------------

# LOGIN & SESSION MANAGEMENT

login_manager = flask_login.LoginManager()
login_manager.init_app(app)


def log_user_in(username):
    user = User()
    user.username = username
    flask_login.login_user(user)
    return user


class User(flask_login.UserMixin):
    def __init__(self):
        self.username = None

    def get_id(self):
        return self.username


def load_user_login(username):
    username = canonicalize(username)
    db = get_db()

    cur = db.execute('select passhash, username from users where username=? or email=?',
                     (username, username))
    entry = cur.fetchone()

    if not entry:
        return None

    return entry


@login_manager.user_loader
def user_loader(username):
    user_entry = load_user_login(username)

    if not user_entry:
        return

    user = User()
    user.username = user_entry['username']

    return user


@login_manager.request_loader
def request_loader(request):
    user_entry = load_user_login(request.form.get('username'))
    if not user_entry:
        return

    user = User()
    user.username = user_entry['username']

    user.is_authenticated = verify_password(request.form['password'], user_entry['passhash'])

    return user


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
    cur = db.execute('select id, title, author, body, media from entries order by date_time desc')
    entries = cur.fetchall()
    return render_template('entries.html', entries=entries)


@flask_login.login_required
@app.route('/new_entry', methods=['GET', 'POST'])
def new_entry():
    form = EntryForm(request.form)
    if request.method == 'POST' and form.validate():
        db = get_db()
        # TODO file upload

        db.execute('insert into entries (slug, title, author, body) values (?,?,?,?)',
                   (slugify(form.title.data), form.title.data, flask_login.current_user.username,
                    form.body.data,))
        db.commit()
        flash('New entry was successfully posted')
        return redirect(url_for('home'))

    return render_template('new_entry.html', form=form)


@app.route('/new_page', methods=['GET', 'POST'])
def new_page():
    # TODO
    pass


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        db = get_db()
        username = canonicalize(request.form['username'])
        cur = db.execute('select passhash from users where username=?',
                         (username,))
        entry = cur.fetchone()

        if entry is None:
            error = 'Invalid username'
        elif not verify_password(request.form['password'], entry['passhash']):
            error = 'Invalid password'
        else:
            log_user_in(username)
            return redirect(url_for('home'))
    return render_template('login.html',
                           error=error, dest='login', val='Login', form=form)


@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    pass  # TODO


@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        db = get_db()
        username = canonicalize(form.username.data)
        possible_current_user = db.execute('select passhash from users where username=?',
                                           (username,)).fetchone()
        if possible_current_user is None:
            db.execute('insert into users (username, email, passhash) values (?, ?, ?)',
                       (username, form.email.data, hash_password(form.password.data)))
            db.commit()
            log_user_in(username)
            flash('Thanks for registering')
            return redirect(url_for('home'))
        elif verify_password(form.password.data, possible_current_user['passhash']):
            flash('You already have an account. You have been logged in.')
            return redirect(url_for('home'))
        else:
            error = u'The username <em>{}</em> is taken.'.format(form.username.data)
    elif request.method == 'POST':
        error = 'Invalid input'
    return render_template('login.html', error=error, dest='register', val='Register', form=form)


@app.route('/logout')
def logout():
    flask_login.logout_user()
    flash('You were logged out')
    return redirect(url_for('home'))


@app.route('/post/<int:entry_id>')
def entry_by_id(entry_id):
    db = get_db()
    entry = db.execute('select id, title, author, body, media from entries where id=?', str(entry_id)) \
        .fetchone()
    return render_template('entry.html', title=entry['title'], body=entry['body'])


@app.route('/post/<post_name>')
def entry_by_name(post_name):
    # NOTE: prefix posts with number-only titles
    return 'Post {}'.format(post_name)  # TODO


@app.route('/404')
def not_found(title, message):
    return render_template('404.html', title=title, message=message)


@app.route('/user/<string:username>')
def user(username):
    username = canonicalize(username)
    db = get_db()
    entry = db.execute('select username, fullname, bio from users where username=?', (username,)) \
        .fetchone()

    if entry is None:
        return render_template('404.html', title='User not found.')

    if username == flask_login.current_user.username:
        return render_template()

    name = entry['fullname'] or entry['username']

    return render_template('entry.html', title=name, body=entry['bio'])


# ------------------------------------------------------------------------------------------------

# FORMS

class LoginForm(Form):
    username = StringField('Username', (validators.Length(min=1, max=32),
                                        validators.regexp(app.config['REGEXP']['username'])))
    password = PasswordField('Password', (validators.Length(min=8, max=128),))


class RegistrationForm(LoginForm):
    full_name = StringField('Full Name')
    email = StringField('Email Address')


class EntryForm(Form):
    """Base form for text entries"""
    title = StringField('Title', (validators.InputRequired(), validators.Length(max=128)))
    body = TextAreaField('Body', (validators.Length(max=1000000),),
                         render_kw={'cols': 35, 'rows': 20})


class MediaEntryForm(EntryForm):
    """Form for entries containing media (media galleries, pictures, etc)"""
    files = FileField(u'Image File(s)', (validators.regexp(app.config['REGEXP']['filename']),
                                         validators.optional()),
                      render_kw={'multiple': True})


class ChoiceEntryForm(EntryForm):
    """Form for entries requiring a variety of options"""

    radio = RadioField('Label', choices=[])

    def ChoiceEntryForm(self, label, choices):
        """
        :param label: String label for the RadioField
        :param choices: dictionary of options and their descriptions
        :return: a new ChoiceEntryForm
        """
        self.radio = RadioField([(key, value) for key, value in choices.items()])


def canonicalize(username):
    """
    Canonicalize the given username. Given the requirements on usernames to be alphanumeric, this
    will only put the username to lowercase in practice.

    :param username:
    :type   username: str
    :return:
    """
    if username and app.config.get('REGEXP')['username'].match(username):
        return username.lower()


def slugify(initial=''):
    """
    Slugify the given string for use in URLs. Will convert capitals to lowercase, then map all non-
    dash and non-alphanumeric characters to dashes, then squash dash series into single dashes.

    :param initial: initial string to slugify
    :return: slug
    """
    return app.config['REGEXP']['dashes'].sub('-', app.config['REGEXP']['char_non_slug'] \
                                              .sub('-', initial.lower()).strip('-'))


# ------------------------------------------------------------------------------------------------

# PASSWORDS

def hash_password(password):
    return pbkdf2_sha256.encrypt(password, rounds=20000, salt_size=16)


def verify_password(password, passhash):
    return pbkdf2_sha256.verify(password, passhash)


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


# ------------------------------------------------------------------------------------------------

# IMAGE PROCESSING

class SubImage:
    size = 2048, 2048
    suffix = 'small'
    square = False

    def get_sub_path(self, file_path):
        splitext = os.path.splitext(file_path)
        return '{}{}.{}x{}.{}'.format(os.path.dirname(), splitext[0],
                                      self.size[0], self.size[1], splitext[1])

    def resize(self, file_path):
        out_file = self.get_sub_path(file_path)
        if file_path != out_file:
            try:
                image = Image.open(file_path)
                try:
                    image.verify()
                except IOError:
                    print('Image could not be read.')

                if self.square:  # Crop image into centred square
                    (width, height) = image.size()
                    (left, upper, right, lower) = (0, height, width, 0)
                    if width < height:
                        diff = (height - width) / 2
                        upper = height - diff
                        lower = diff
                    elif width > height:
                        diff = (width - height) / 2
                        left = diff
                        right = width - diff
                    image.crop(left, upper, right, lower)

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
    square = True


class ThumbnailImage(SubImage):
    size = 128, 128
    suffix = 'thumb'
    square = True


# ------------------------------------------------------------------------------------------------

# MAIN


if __name__ == '__main__':
    app.run(debug=True)
