# app.py  –  Kamar AI Mode  –  نسخة جاهزة للرفع على Render
import os, requests, json, textwrap, re
from collections import Counter
from urllib.parse import urlparse
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_babel import Babel, gettext as _

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kamar.db'
app.config['BABEL_DEFAULT_LOCALE'] = 'ar'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
babel = Babel(app)

# ==================== المفتاح مدمج جاهز ====================
API_BASE = "https://api.openwebninja.com/google-ai-mode/ai-mode"
API_KEY  = "ak_is7pbn7gl4g8mbaupwynpkfbr6lm9yfh8iurpdpuk4noou1"
# =========================================================

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    keyword = db.Column(db.String(200))
    lang = db.Column(db.String(5))
    data = db.Column(db.Text)

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@babel.localeselector
def get_locale():
    return session.get('lang', 'ar')

# --------------------------------------------------
#  صفحات المستخدم
# --------------------------------------------------
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if User.query.filter_by(email=email).first():
            flash(_('Email already registered'))
            return redirect(url_for('register'))
        user = User(email=email, password=password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('dashboard'))
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email, password=password).first()
        if user:
            login_user(user)
            return redirect(url_for('dashboard'))
        flash(_('Invalid credentials'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

# --------------------------------------------------
#  تحليل من السيرفر (Proxy) – لا CORS
# --------------------------------------------------
@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    data    = request.get_json(silent=True) or {}
    keyword = data.get('keyword','').strip()
    lang    = data.get('lang','ar')
    gl      = data.get('gl','sa')

    if not keyword:
        return jsonify({'error':'أدخل كلمة مفتاحية'}), 400

    params = {'prompt':keyword, 'hl':lang, 'gl':gl, 'x-api-key':API_KEY}
    try:
        r = requests.get(API_BASE, params=params, timeout=15)
    except Exception as e:
        return jsonify({'error':'فشل الاتصال بالخادم الخارجي'}), 502

    if r.status_code != 200:
        return jsonify({'error':'خطأ في الاستجابة من الـ API'}), 502

    ans  = r.json().get('answer','')
    refs = r.json().get('references',[])

    # نفس دوال المعالجة السابقة
    stop = {"تعرف","تعلم","اكتشف","احصل","لا تفوّت","سرّ","خدعة","مذهل","رائع","أفضل 10","best","discover","amazing","top 10","secret","trick"}
    def clean(t): return ' '.join(w for w in t.split() if w.lower() not in stop)
    def build_meta(t): return textwrap.shorten(clean(t), 155, placeholder='...')
    def build_snip(t): return textwrap.shorten(clean(t.split(/[.؟!]/)[0]), 155, placeholder='...')
    def nlp_kw(t):
        bi = re.findall(r'\b\w+\s\w+\b', t.lower())
        freq = Counter(bi)
        return '، '.join([w for w,_ in freq.most_common(12)])
    def outline(t):
        sents = [s.strip() for s in re.split(r'[.؟!]', t) if len(s.strip())>20][:6]
        return [{'tag':'h3','text':s[:70]} for s in sents]
    def title(t):
        w = t.split()
        top = Counter(w).most_common(3)
        return f"{top[0][0]} {top[1][0]} {top[2][0]}: اختيارك حسب الاختبار والتجربة"

    result = {
        'suggested_title'   : clean(title(ans)),
        'meta_description'  : build_meta(ans),
        'snippet_text'      : build_snip(ans),
        'nlp_keywords'      : nlp_kw(ans),
        'featured_snippets' : list({urlparse(u).hostname for u in refs}),
        'outline'           : outline(ans)
    }
    return jsonify(result)

# --------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True)