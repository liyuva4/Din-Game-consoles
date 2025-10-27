from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
import os

app = Flask(__name__)
app.secret_key = 'secret-key'  # חובה שיהיה מפתח session
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ---------- ניהול משתמש ----------
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

class User(UserMixin):
    id = 1
    username = "admin"
    password = "Dd0532299500"

    @property
    def is_admin(self):
        return self.username == "admin"


@login_manager.user_loader
def load_user(user_id):
    return User()

# ---------- עוזרים ----------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# ---------- עמוד התחברות ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == 'Dd0532299500':
            login_user(User())
            return redirect('/')
        else:
            return "<h3>שם משתמש או סיסמה שגויים</h3>"
    return '''
        <form method="POST">
            <input type="text" name="username" placeholder="שם משתמש">
            <input type="password" name="password" placeholder="סיסמה">
            <button type="submit">התחבר</button>
        </form>
    '''

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

# ---------- דף הגלריה הראשי ----------
@app.route('/')
def index():
    images = sorted(os.listdir(app.config['UPLOAD_FOLDER']))
    numbered_images = [(i + 1, img) for i, img in enumerate(images)]
    return render_template('index.html', images=numbered_images)

# ---------- העלאת תמונה ----------
@app.route('/upload', methods=['POST'])
@login_required  # <-- הגנה למנהל בלבד
def upload():
    # כאן נכנס הקוד מהגרסה הקודמת שלך
    file = request.files.get('file')
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return redirect(url_for('index'))

# ---------- מחיקת תמונה ----------
@app.route('/delete/<filename>', methods=['POST'])
@login_required  # <-- גם כאן רק למנהל
def delete(filename):
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(path):
        os.remove(path)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
