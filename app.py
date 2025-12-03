from flask import Flask, render_template, request, redirect, url_for, abort
from werkzeug.utils import secure_filename
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
import os
import json  # לטיפול בקובצי JSON
import shutil  # נשאר לייבוא אך לא נשתמש בו למחיקת קונסולות

app = Flask(__name__)
app.secret_key = 'secret-key'

# קובץ השמירה של הקונסולות
CONSOLES_FILE = 'consoles.json'
UPLOAD_BASE_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_BASE_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}


# ---------- פונקציות ניהול קונסולות וקבצים ----------

def load_consoles():
    """טוען את רשימת הקונסולות מקובץ JSON."""
    default_consoles = ['Nintendo', 'PlayStation', 'Xbox', 'PC']

    if not os.path.exists(CONSOLES_FILE):
        return default_consoles

    try:
        with open(CONSOLES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return [c for c in data if c]
            else:
                return default_consoles
    except Exception as e:
        print(f"שגיאה בטעינת קובץ הקונסולות: {e}. מאפס את הרשימה.")
        return default_consoles


def save_consoles(consoles_list):
    """שומר את רשימת הקונסולות לקובץ JSON."""
    with open(CONSOLES_FILE, 'w', encoding='utf-8') as f:
        # ensure_ascii=False מאפשר שמירה תקינה של עברית
        json.dump(consoles_list, f, indent=4, ensure_ascii=False)


# טוענים את הקונסולות בעת הפעלת האפליקציה
CONSOLES = load_consoles()

# יצירת תיקיות הקבצים עבור הקונסולות שנטענו (השם הפיזי הוא תמיד בטוח)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
for console_name in CONSOLES:
    # שמירת הקובץ הפיזי תמיד משתמשת בשם בטוח (case insensitive במערכת הקבצים)
    safe_name = secure_filename(console_name)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], safe_name), exist_ok=True)

# ---------- ניהול משתמש ופונקציות עזר ----------
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


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == 'Dd0532299500':
            login_user(User())
            next_page = request.args.get('next')
            return redirect(next_page or '/')
        else:
            return "<h3>שם משתמש או סיסמה שגויים</h3>"
    return '''
        <form method="POST" dir="rtl">
            <h2>התחברות מנהל</h2>
            <input type="text" name="username" placeholder="שם משתמש" required><br><br>
            <input type="password" name="password" placeholder="סיסמה" required><br><br>
            <button type="submit">התחבר</button>
        </form>
        <p style="margin-top: 15px;"><a href="/">חזרה לגלריה</a></p>
    '''


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')


# ---------- דף הגלריה הראשי + עמוד ספציפי לקונסולה ----------
@app.route('/')
@app.route('/<console_name>')
def index(console_name=None):
    global CONSOLES

    if console_name and console_name not in CONSOLES:
        abort(404)

    # השם הפיזי של התיקייה במערכת הקבצים (תמיד בטוח)
    physical_folder_name = secure_filename(console_name) if console_name else None

    if console_name:
        current_folder = os.path.join(app.config['UPLOAD_FOLDER'], physical_folder_name)
    else:
        return render_template('index.html', consoles=CONSOLES, images=None, selected_console=None)

    try:
        images = sorted(os.listdir(current_folder))
    except FileNotFoundError:
        images = []

    # הנתיב ל-URL משתמש בשם הפיזי הבטוח (physical_folder_name)
    numbered_images = [
        (i + 1, os.path.join(physical_folder_name, img).replace(os.path.sep, '/'))
        for i, img in enumerate(images)
    ]

    return render_template('index.html',
                           consoles=CONSOLES,
                           images=numbered_images,
                           selected_console=console_name)


# ---------- העלאת תמונה ----------
@app.route('/upload', methods=['POST'])
@login_required
def upload():
    global CONSOLES
    file = request.files.get('file')
    console = request.form.get('console')

    # בדיקת רגישות לאותיות רישיות
    if not console or console not in CONSOLES:
        return "<h3>שגיאה: יש לבחור קונסולה חוקית.</h3>", 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # שמירת הקובץ בתיקייה עם השם הפיזי הבטוח
        safe_console_name = secure_filename(console)
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_console_name, filename)
        file.save(upload_path)

    return redirect(url_for('index', console_name=console))


# ---------- מחיקת תמונה ----------
@app.route('/delete/<path:filepath>', methods=['POST'])
@login_required
def delete(filepath):
    # filepath יכיל את הנתיב הפיזי הבטוח (למשל: Nintendo/my_game.png)
    path = os.path.join(app.config['UPLOAD_FOLDER'], filepath)

    if os.path.exists(path):
        os.remove(path)
        # מפיק את שם הקונסולה הפיזי מתוך הנתיב (Nintendo)
        physical_folder_name = filepath.split('/')[0]

        # מוצא את השם המקורי (Case Sensitive) של הקונסולה כדי לחזור ל-URL הנכון
        original_console_name = None
        for console in CONSOLES:
            if secure_filename(console) == physical_folder_name:
                original_console_name = console
                break

        return redirect(url_for('index', console_name=original_console_name))

    return "<h3>שגיאה: הקובץ לא נמצא למחיקה.</h3>", 404


# ---------- ניהול קונסולות (חדש) ----------
@app.route('/manage_consoles', methods=['POST'])
@login_required
def manage_consoles():
    """מסלול חדש לניהול הוספה ומחיקה של קונסולות."""
    global CONSOLES
    action = request.form.get('action')
    console_name = request.form.get('console_name')  # השם המקורי ששלח המשתמש

    # 1. יצירת השם הבטוח לתיקייה הפיזית
    safe_console_name_for_folder = secure_filename(console_name)

    if not console_name or not safe_console_name_for_folder:
        return "<h3>שגיאה: שם קונסולה לא חוקי.</h3>", 400

    if action == 'add':
        # בדיקה Case Sensitive (האם השם המקורי קיים ברשימה)
        if console_name not in CONSOLES:
            # 1. עדכון הרשימה בזיכרון (שומרים את השם המקורי - Case Sensitive)
            CONSOLES.append(console_name)

            # 2. שמירת הרשימה לקובץ JSON
            save_consoles(CONSOLES)

            # 3. יצירת התיקייה הפיזית (משתמשים בשם הבטוח)
            os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], safe_console_name_for_folder), exist_ok=True)

        return redirect(url_for('index', console_name=console_name))

    elif action == 'delete':
        # בדיקה Case Sensitive (האם השם המקורי קיים ברשימה)
        if console_name in CONSOLES:
            # שינוי לוגיקה: מחיקה מהרשימה בלבד, השארת התיקייה הפיזית.

            # 1. הסרת הפריט מהרשימה בזיכרון
            CONSOLES.remove(console_name)

            # 2. שמירת הרשימה המעודכנת לקובץ JSON
            save_consoles(CONSOLES)

        return redirect(url_for('index'))

    return redirect(url_for('index'))


if __name__ == '__main__':
    # ודא שהרשימה הראשונית נשמרת אם הקובץ לא קיים
    if not os.path.exists(CONSOLES_FILE):
        save_consoles(CONSOLES)

    app.run(debug=True)