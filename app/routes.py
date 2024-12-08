from flask import Blueprint, render_template, request, redirect, url_for

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # Главная страница с формой входа/регистрации
    return render_template('index.html')

@main_bp.route('/login', methods=['POST'])
def login():
    # Логика обработки входа
    # Если успех: redirect на main page
    return redirect(url_for('main.main_page'))

@main_bp.route('/register', methods=['POST'])
def register():
    # Логика регистрации
    # После успешной регистрации можно перевести на main page
    return redirect(url_for('main.main_page'))

@main_bp.route('/main')
def main_page():
    # Основная страница после входа
    return render_template('main.html')

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
