from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from .db_utils import user_exists, add_user_to_db, get_user_by_email, get_all_courses_from_db, get_all_courses_from_db_fro_prereq, update_user_courses, get_all_user_courses
import json
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return redirect(url_for('main.login'))


@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')

        # Примитивная проверка заполнения полей
        if not username or not email or not password or not name:
            flash('Please fill in all fields.', 'error')
            return redirect(url_for('main.register'))

        # Проверяем, существует ли пользователь с таким email
        if user_exists(email):
            flash('This email already exists.', 'error')
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
            flash("Invalid email or password.", "error")
            return redirect(url_for('main.login'))

        user = get_user_by_email(email)
        if user and check_password_hash(user['password_hash'], password):
            # Успешная аутентификация
            session['user_email'] = user['email']
            session['user_name'] = user['user_name']
            flash("You are logged in", "success")
            return redirect(url_for('main.main_page'))
        else:
            flash("Wrong email or pasword", "error")
            return redirect(url_for('main.login'))

    # Если GET запрос, отображаем форму
    return render_template('login.html')

@main_bp.route('/main')
def main_page():
    if 'user_email' not in session:
        flash("You need to login first", "error")
        return redirect(url_for('main.login'))
    return render_template('main.html', user_name=session.get('user_name'), active_page='main')


    # Если вошёл, показываем главную страницу
    return render_template('main.html', user_name=session.get('user_name'))

@main_bp.route('/logout')
def logout():
    session.clear()
    flash("You are logged out", "info")
    return redirect(url_for('main.login'))

@main_bp.route('/prereq_tree', methods=['GET', 'POST'])
def prereq_tree():
    selected_course = None
    full_tree = False

    if request.method == 'POST':
        selected_course = request.form.get('course_code')
        full_tree = 'full_tree' in request.form
        
        from .tree_logic import build_tree_data
        tree_data = build_tree_data(selected_course, full_tree_mode=full_tree)
        tree_data_json = json.dumps(tree_data, ensure_ascii=False)

        return render_template(
            'prereq_tree.html', 
            active_page='prereq_tree', 
            tree_data_json=tree_data_json, 
            courses=get_all_courses_from_db_fro_prereq(),
            selected_course=selected_course,
            full_tree=full_tree
        )

    # GET Request - No form submission
    return render_template(
        'prereq_tree.html', 
        active_page='prereq_tree', 
        courses=get_all_courses_from_db_fro_prereq()
    )


@main_bp.route('/add_classes', methods=['GET', 'POST'])
def add_classes():
    if 'user_name' not in session:
        flash("Please log in first", "error")
        return redirect(url_for('main.login'))

    user_name = session['user_name']

    if request.method == 'POST':
        # Обрабатываем POST запрос при нажатии SAVE
        # данные о курсах и сложностях придут из формы или AJAX
        updated_courses = request.form.get('updated_courses')
        # Ожидаем, что updated_courses - JSON строка с массивом курсов: [{"class_taken": "MATH 100", "difficulty":7, "deleted":false}, ...]

        import json
        courses_data = json.loads(updated_courses)
        update_user_courses(user_name, courses_data)

        flash("Courses updated successfully", "success")
        return redirect(url_for('main.add_classes'))

    # Если GET запрос: отображаем страницу
    all_courses = get_all_courses_from_db()  # Список всех доступных курсов, например [{"code":"CPSC 121", "title":"Intro to CS"}]
    user_courses = get_all_user_courses(user_name) # [{"class_taken":"MATH 100","difficulty":7}, ...]
    return render_template('add_classes.html', active_page='add_classes', all_courses=all_courses, user_courses=user_courses)

@main_bp.route('/degree_eval')
def degree_eval():
    return render_template('degree_eval.html')

@main_bp.route('/profile')
def profile():
    return render_template('profile.html')
