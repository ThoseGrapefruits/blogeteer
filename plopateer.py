from flask import Flask, request, render_template

app = Flask(__name__)


@app.route('/')
def home():
    return 'Hello World!'


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
def posts(post_id):
    return "Post #{}".format(post_id)


@app.route('/user/<username>')
def profile(username):
    return "User {}".format(username)


if __name__ == '__main__':
    app.run()
