from flask import Flask, render_template, request
import psycopg2
from credentials import *

app = Flask(__name__)

def get_connection():
    # Подключение к БД, адаптируйте под ваши данные
    return psycopg2.connect(
        dbname= DBNAME,
        user=USER,
        password=PASSWORD,
        host=PASSWORD,
        port=PORT
    )

@app.route('/', methods=['GET', 'POST'])
def index():
    conn = get_connection()
    cur = conn.cursor()

    # Получаем список мейджоров
    cur.execute("SELECT id, name FROM program")
    majors = cur.fetchall()

    # Получаем список концентраций (например, для выбранного major)
    # Если вы хотите показать концентрации только при выборе мейджора, можете сначала отобразить только major
    # и затем через AJAX подгружать концентрации. Для простоты сразу всех покажем.
    cur.execute("SELECT c.id, c.name, p.name FROM concentration c JOIN program p ON c.program_id = p.id;")
    concentrations = cur.fetchall()

    conn.close()

    if request.method == 'POST':
        selected_major_id = request.form.get('major')
        selected_concentration_id = request.form.get('concentration')
        taken_courses = request.form.getlist('taken_courses')

        # Переходим на страницу результата, передаем выбранные данные.
        return render_template('result.html',
                               major_id=selected_major_id,
                               concentration_id=selected_concentration_id,
                               taken_courses=taken_courses)

    # Получаем список всех курсов для возможности отметить "пройденные"
    # Предполагаем, что таблица course существует и содержит все курсы.
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT code, title FROM course ORDER BY code;")
    all_courses = cur.fetchall()
    conn.close()

    return render_template('index.html', majors=majors, concentrations=concentrations, all_courses=all_courses)


@app.route('/result', methods=['POST','GET'])
def result():
    # На страницу result мы приходим с POST на index, но также можно GET, если нужно.
    # Переменные можно передавать через session или request.form
    # Для упрощения предположим, что мы пришли POST->redirect GET - в данном примере просто берём request.args ничего
    # Но мы уже возвращаем result.html из index, так что лучше данные извлекать сразу.

    major_id = request.args.get('major_id')
    concentration_id = request.args.get('concentration_id')
    taken_courses = request.args.getlist('taken_courses')

    # Но у нас в коде выше result.html отрисовывается напрямую из POST, значит в result.html мы уже имеем их как локальные переменные
    # Поэтому лучше убрать эту логику из result() и делать всё в index(). Ниже вариант если бы мы переадресовывали.

    return "This route ideally would show results, but we handled in index directly."


@app.route('/calculate_requirements', methods=['POST'])
def calculate_requirements():
    major_id = request.form.get('major_id')
    concentration_id = request.form.get('concentration_id')
    taken_courses = request.form.getlist('taken_courses')

    conn = get_connection()
    cur = conn.cursor()

    # Логика:
    # 1. Выбрать все requirement_group для данного major
    # 2. Если concentration_id есть, выбрать и их requirement_group
    # 3. Выбрать все курсы из requirement_course_link и requirement_notes (но notes просто инфо)
    # 4. Фильтровать те, что студент уже прошел (taken_courses)
    # 5. Результат - список курсов, которые остались

    # Получаем requirement_group мейджора
    cur.execute("""
        SELECT rg.id, rg.name, rg.selection_type, rg.required_credits
        FROM requirement_group rg
        WHERE rg.program_id = %s
        AND rg.id NOT IN (SELECT requirement_group_id FROM concentration_requirement_link)
    """, (major_id,))
    major_groups = cur.fetchall()

    # Если есть концентрация, добавляем её группы
    concentration_groups = []
    if concentration_id and concentration_id.strip() != "":
        cur.execute("""
            SELECT rg.id, rg.name, rg.selection_type, rg.required_credits
            FROM concentration_requirement_link crl
            JOIN requirement_group rg ON rg.id = crl.requirement_group_id
            WHERE crl.concentration_id = %s
        """,(concentration_id,))
        concentration_groups = cur.fetchall()

    # Объединяем списки групп
    all_groups = major_groups + concentration_groups

    # Получаем курсы из групп
    remaining_courses = []
    for g in all_groups:
        g_id, g_name, g_sel, g_credits = g
        cur.execute("""
            SELECT c.code, c.title
            FROM requirement_course_link rcl
            JOIN course c ON c.code = rcl.course_code
            WHERE rcl.requirement_group_id = %s
        """, (g_id,))
        group_courses = cur.fetchall()

        # Фильтруем те, что студент уже прошел
        for gc in group_courses:
            code, title = gc
            if code not in taken_courses:
                remaining_courses.append((g_name, code, title))

        # Аналогично для notes, если нужно

    conn.close()

    # Возвращаем HTML с результатами
    return render_template('result.html', remaining_courses=remaining_courses)

if __name__ == "__main__":
    app.run(debug=True)
