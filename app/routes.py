from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from .db_utils import user_exists, add_user_to_db, get_user_by_email, get_all_courses_from_db, get_all_courses_from_db_fro_prereq, update_user_courses, get_all_user_courses, get_all_majors
import json
from .db_utils import get_connection
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
        major_id = request.form.get('major_id')

        if not username or not email or not password or not name or not major_id:
            flash('Please fill in all fields.', 'error')
            return redirect(url_for('main.register'))

        if user_exists(email):
            flash('This email already exists.', 'error')
            return redirect(url_for('main.register'))

        password_hash = generate_password_hash(password)
        add_user_to_db(username, email, password_hash, name, major_id)

        flash('Registration successful!', 'success')
        return redirect(url_for('main.login'))

    # Fetch majors for the dropdown
    majors = get_all_majors()
    return render_template('register.html', majors=majors)


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
    if 'user_name' not in session:
        flash("Please log in first.", "error")
        return redirect(url_for('main.login'))

    user_name = session['user_name']
    conn = get_connection()
    cur = conn.cursor()

    # Fetch user's major from the program table
    cur.execute("""
        SELECT p.name
        FROM users u
        JOIN program p ON u.major_id = p.id
        WHERE u.user_name = %s
    """, (user_name,))
    result = cur.fetchone()

    if not result:
        flash("Major not found for user.", "error")
        return redirect(url_for('main.profile'))

    program_name = result[0]
    session['major_name'] = program_name

    # Fetch completed courses by the user
    cur.execute("""
        SELECT class_taken 
        FROM user_courses 
        WHERE user_name = %s
    """, (user_name,))
    completed_courses = {row[0] for row in cur.fetchall()}

    # Fetch required courses based on program and requirements
    cur.execute("""
        SELECT 
            rg.name AS requirement_group_name,
            rg.required_credits,
            array_agg(DISTINCT c.code) AS course_codes,
            array_agg(DISTINCT c.title) AS course_titles
        FROM program p
        JOIN requirement_group rg ON rg.program_id = p.id
        LEFT JOIN requirement_course_link rcl ON rcl.requirement_group_id = rg.id
        LEFT JOIN course c ON c.code = rcl.course_code
        WHERE p.name = %s
          AND rg.id NOT IN (SELECT requirement_group_id FROM concentration_requirement_link)
        GROUP BY rg.name, rg.required_credits
        ORDER BY rg.name;
    """, (program_name,))
    all_requirements = cur.fetchall()

    # Process remaining courses by requirement group
    remaining_courses = []
    for req in all_requirements:
        group_name, required_credits, course_codes, course_titles = req

        # Handle "ALL" case
        if required_credits == 'ALL':
            remaining_courses.append({
                "group_name": group_name,
                "required_credits": "ALL",
                "courses": [
                    {"code": code, "title": title} 
                    for code, title in zip(course_codes, course_titles)
                ]
            })
        else:
            # Filter out completed courses
            remaining_in_group = [
                {"code": code, "title": title} 
                for code, title in zip(course_codes, course_titles) 
                if code not in completed_courses
            ]

            if remaining_in_group:
                remaining_courses.append({
                    "group_name": group_name,
                    "required_credits": required_credits,
                    "courses": remaining_in_group
                })

    conn.close()

    return render_template(
        'degree_eval.html', 
        completed_courses=completed_courses, 
        remaining_courses=remaining_courses, 
        active_page='degree_eval'
    )




from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from .db_utils import get_connection

@main_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_name' not in session:
        flash("Please log in first.", "error")
        return redirect(url_for('main.login'))

    user_name = session['user_name']

    if request.method == 'POST':
        action = request.form.get('action')

        # Update Password
        if action == 'update_password':
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')

            if not current_password or not new_password or not confirm_password:
                flash("Please fill all fields.", "error")
                return redirect(url_for('main.profile'))

            if new_password != confirm_password:
                flash("New passwords do not match.", "error")
                return redirect(url_for('main.profile'))

            conn = get_connection()
            cur = conn.cursor()

            # Validate current password
            cur.execute("SELECT password FROM users WHERE user_name = %s", (user_name,))
            result = cur.fetchone()

            if not result or not check_password_hash(result[0], current_password):
                flash("Incorrect current password.", "error")
                conn.close()
                return redirect(url_for('main.profile'))

            # Update password
            new_password_hash = generate_password_hash(new_password)
            cur.execute("UPDATE users SET password = %s WHERE user_name = %s",
                        (new_password_hash, user_name))
            conn.commit()
            conn.close()

            flash("Password updated successfully.", "success")
            return redirect(url_for('main.profile'))

        # Delete Account
        elif action == 'delete_account':
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM users WHERE user_name = %s", (user_name,))
            conn.commit()
            conn.close()

            # Clear session and redirect to login
            session.clear()
            flash("Account deleted successfully.", "success")
            return redirect(url_for('main.login'))

    return render_template('profile.html', user_name=user_name)

