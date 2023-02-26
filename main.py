from flask import Flask, render_template, url_for, request, redirect, flash, abort
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = '12345'
manager = LoginManager(app)
db = SQLAlchemy(app)
admin = Admin(app)


class CustomModelView(ModelView):
    def is_accessible(self):
        if current_user.is_authenticated:
            return current_user.is_admin
        else:
            return abort(401)

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login_page'))


# Models
class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    calories = db.Column(db.Integer, nullable=False)
    proteins = db.Column(db.Float, nullable=False)
    fats = db.Column(db.Float, nullable=False)
    carbs = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return '<Article %r>' % self.id


admin.add_view(CustomModelView(Article, db.session))

with app.app_context():
    db.create_all()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(128), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)



admin.add_view(CustomModelView(User, db.session))


class ImtResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(128), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    result = db.Column(db.Float, nullable=False)


admin.add_view(CustomModelView(ImtResult, db.session))


class UserWeight(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(128), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    weight = db.Column(db.Float, nullable=False)


admin.add_view(CustomModelView(UserWeight, db.session))


@manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


# Functions
def get_value_by_index(index_imt):
    if index_imt < 16:
        return "Выраженный дефицит массы тела"
    elif 16 <= index_imt < 18.5:
        return "Недостаточная масса тела"
    elif 18.5 <= index_imt < 25:
        return "Нормальная масса тела"
    elif 25 <= index_imt < 30:
        return "Избыточная масса тела (предожирение)"
    elif 30 <= index_imt < 35:
        return "Ожирение 1-ой степени"
    elif 35 <= index_imt < 40:
        return "Ожирение 2-ой степени"
    elif index_imt >= 40:
        return "Ожирение 3-ой степени"
    else:
        return "Error"


# Routes
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/imt_calc', methods=['POST', 'GET'])
def imt():
    if request.method == 'POST':

        weight = request.form['weight']
        height = request.form['height']
        if weight == '' or height == '':
            flash("Заполните все поля данных")
            return render_template('imt.html')
        imt_index = int(weight) / (int(height)/100)**2
        imt_index = round(imt_index, 2)
        if current_user.is_authenticated:
            imt_result = ImtResult(user=current_user.login, result=imt_index)
            db.session.add(imt_result)
            db.session.commit()
        return render_template('imt_result.html',
                               height=height, weight=weight, index=imt_index, result=get_value_by_index(imt_index))
    else:
        return render_template('imt.html')


@app.route('/kcal_calc', methods=['POST', 'GET'])
def kcal_calc():
    articles = Article.query.all()
    if request.method == 'POST':
        product = request.form['product']
        weight = request.form['weight']
        if weight == '':
            flash('Заполните все поля данных')
            return render_template('kcal_calc.html', articles=articles)
        for el in articles:
            if el.name == product:
                return render_template('kcal_calc_result.html', product=product, weight=weight,
                                       kcal=round(el.calories*(int(weight)/100), 2),
                                       proteins=round(el.proteins*(int(weight)/100), 2),
                                       fats=round(el.fats*(int(weight)/100), 2),
                                       carbs=round(el.carbs*(int(weight)/100),2))
    else:
        return render_template('kcal_calc.html', articles=articles)


@app.route('/norm_kcal', methods=['POST', 'GET'])
def norm_kcal():
    if request.method == 'POST':
        sex = request.form['sex']
        age = request.form['age']
        height = request.form['height']
        weight = request.form['weight']
        activity = request.form['activity']
        if sex == '' or age == '' or height == '' or weight == '' or activity == '':
            flash('Заполните все поля данных')
            return render_template('norm_kcal.html')
        if sex == 'm':
            result = ((9.99*int(weight))+(6.25*int(height)) - (4.92*int(age))+5)*float(activity)
        else:
            result = ((9.99 * int(weight)) + (6.25 * int(height)) - (4.92 * int(age)) - 161) * float(activity)
        return render_template('norm_kcal_result.html', result=int(round(result, 0)))
    else:
        return render_template('norm_kcal.html')


@app.route('/login', methods=['POST', 'GET'])
def login_page():
    login = request.form.get('login')
    password = request.form.get('password')

    if login and password:
        user = User.query.filter_by(login=login).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('imt'))
        else:
            flash('Неверный логин или пароль')
    else:
        flash('Пожалуйста, заполните поля логина и пароля')

    return render_template('login.html')


@app.route('/logout', methods=['POST', 'GET'])
def logout_page():
    logout_user()
    return redirect(url_for('imt'))


@app.route('/register', methods=['POST', 'GET'])
def register_page():
    login = request.form.get('login')
    password = request.form.get('password')
    password2 = request.form.get('password2')

    if request.method == 'POST':
        if not (login or password or password2):
            flash('Пожалуйста, заполните все поля')
        elif password != password2:
            flash('Введенные пароли не совпадают')
        else:
            hash_password = generate_password_hash(password)
            new_user = User(login=login, password=hash_password)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login_page'))
    return render_template('register.html')


@app.route('/imt_prev')
@login_required
def prev():
    imt_results = ImtResult.query.order_by(ImtResult.date).filter(ImtResult.user == current_user.login).all()
    return render_template('imt_prev.html', imt_results=imt_results)


@app.route('/ideal_weight', methods=['POST', 'GET'])
def ideal_weight():
    if request.method == 'POST':
        height = request.form['height']
        gr_kl = request.form['gr_kl']
        if height == '' or gr_kl == '':
            flash('Заполните все поля данных')
            return render_template('ideal_weight.html')
        else:
            weight = (int(height)*int(gr_kl))/240
            return render_template('ideal_weight_result.html', weight=round(weight, 1))
    return render_template('ideal_weight.html')


@app.route('/weight_control')
@login_required
def weight_control():
    if len(UserWeight.query.order_by(UserWeight.date).filter(UserWeight.user == current_user.login).all()) != 0:
        labels = [str(i.date.date()) for i in UserWeight.query.order_by(UserWeight.date).filter(UserWeight.user == current_user.login).all()]
        values = [int(i.weight) for i in UserWeight.query.order_by(UserWeight.date).filter(UserWeight.user == current_user.login).all()]

        return render_template('weight_control.html',
                               weight_now=UserWeight.query.order_by(UserWeight.date.desc()).filter(
                                   UserWeight.user == current_user.login).first().weight,
                               weight_all=UserWeight.query.order_by(UserWeight.date).filter(
                                   UserWeight.user == current_user.login).all(),
                               labels=labels,
                               values=values
                               )
    else:
        return render_template('weight_control.html')


@app.route('/new_weight', methods=['POST', 'GET'])
@login_required
def new_weight():
    if request.method == 'POST':
        if request.form['weight'] != '':
            weight = UserWeight(user=current_user.login, weight=request.form['weight'])
            db.session.add(weight)
            db.session.commit()
            return redirect(url_for('weight_control'))
        else:
            flash('Заполните поле ввода веса')
            return render_template('new_weight.html')
    else:
        return render_template('new_weight.html')


@app.after_request
def redirect_to_login_page(response):
    if response.status_code == 401:
        return redirect(url_for('login_page'))
    else:
        return response


if __name__ == '__main__':
    article = Article(name='Курица', calories=190, proteins=16.0, fats=14.0, carbs=0.0)

    app.run()