from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from .db_utils import user_exists, add_user_to_db, get_user_by_email

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')

        # Примитивная проверка заполнения полей
        if not username or not email or not password or not name:
            flash('Fill all fields', 'error')
            return redirect(url_for('main.register'))

        # Проверяем, существует ли пользователь с таким email
        if user_exists(email):
            flash('this eamil already exists', 'error')
            return redirect(url_for('main.register'))

        # Хэшируем пароль
        password_hash = generate_password_hash(password)

        # Добавляем пользователя в базу данных
        add_user_to_db(username, email, password_hash, name)

        flash('Registration completed', 'success')
        return redirect(url_for('main.index'))

    return render_template('register.html')



@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash("Введите email и пароль", "error")
            return redirect(url_for('main.login'))

        user = get_user_by_email(email)
        if user and check_password_hash(user['password_hash'], password):
            # Успешная аутентификация
            session['user_email'] = user['email']
            session['user_name'] = user['user_name']
            flash("Вы успешно вошли!", "success")
            return redirect(url_for('main.main_page'))
        else:
            flash("Неверный email или пароль", "error")
            return redirect(url_for('main.login'))

    # Если GET запрос, отображаем форму
    return render_template('login.html')

@main_bp.route('/main')
def main_page():
    # Проверим, вошёл ли пользователь
    if 'user_email' not in session:
        flash("Сначала войдите", "error")
        return redirect(url_for('main.login'))

    # Если вошёл, показываем главную страницу
    return render_template('main.html', user_name=session.get('user_name'))

@main_bp.route('/logout')
def logout():
    session.clear()
    flash("Вы вышли из системы", "info")
    return redirect(url_for('main.login'))


@main_bp.route('/prereq_tree')
def prereq_tree():
    return render_template('prereq_tree.html')

@main_bp.route('/add_classes')
def add_classes():
    # Страница, как в Фото №3
    return render_template('add_classes.html')

@main_bp.route('/degree_eval')
def degree_eval():
    return render_template('degree_eval.html')

@main_bp.route('/profile')
def profile():
    return render_template('profile.html')
