import json
import psycopg2
import os

def check_course_exists(conn, code):
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM course WHERE code = %s", (code,))
        return cur.fetchone() is not None

def insert_program(conn, name):
    print(f"Inserting program: {name}")
    with conn.cursor() as cur:
        try:
            cur.execute("INSERT INTO program (name) VALUES (%s) RETURNING id", (name,))
            program_id = cur.fetchone()[0]
            print(f"Program inserted with ID: {program_id}")
            return program_id
        except Exception as e:
            print(f"Error inserting program '{name}': {e}")
            return None

def insert_requirement_group(conn, program_id, parent_id, name, selection_type, required_credits):
    print(f"Inserting requirement group: {name} under program ID: {program_id}")
    with conn.cursor() as cur:
        try:
            cur.execute("""
                INSERT INTO requirement_group (program_id, parent_id, name, selection_type, required_credits)
                VALUES (%s, %s, %s, %s, %s) RETURNING id
            """, (program_id, parent_id, name, selection_type, required_credits))
            group_id = cur.fetchone()[0]
            print(f"Requirement group inserted with ID: {group_id}")
            return group_id
        except Exception as e:
            print(f"Error inserting requirement group '{name}': {e}")
            return None

def insert_requirement_course_link(conn, requirement_group_id, course_code, excluded=False):
    print(f"Inserting course link: {course_code} for group ID: {requirement_group_id}")
    with conn.cursor() as cur:
        try:
            cur.execute("""
                INSERT INTO requirement_course_link (requirement_group_id, course_code, excluded)
                VALUES (%s, %s, %s)
            """, (requirement_group_id, course_code, excluded))
            print(f"Course link inserted for course: {course_code}")
        except Exception as e:
            print(f"Error inserting course link '{course_code}': {e}")

def insert_requirement_note(conn, requirement_group_id, note):
    print(f"Inserting requirement note for group ID: {requirement_group_id}")
    with conn.cursor() as cur:
        try:
            cur.execute("""
                INSERT INTO requirement_notes (requirement_group_id, note)
                VALUES (%s, %s)
            """, (requirement_group_id, note))
            print(f"Requirement note inserted: {note}")
        except Exception as e:
            print(f"Error inserting requirement note '{note}': {e}")

def insert_concentration(conn, program_id, name, selection_type, required_credits):
    print(f"Inserting concentration: {name} under program ID: {program_id}")
    with conn.cursor() as cur:
        try:
            cur.execute("""
                INSERT INTO concentration (program_id, name, selection_type, required_credits)
                VALUES (%s, %s, %s, %s) RETURNING id
            """, (program_id, name, selection_type, required_credits))
            concentration_id = cur.fetchone()[0]
            print(f"Concentration inserted with ID: {concentration_id}")
            return concentration_id
        except Exception as e:
            print(f"Error inserting concentration '{name}': {e}")
            return None

def insert_concentration_requirement_link(conn, concentration_id, requirement_group_id):
    print(f"Linking concentration ID {concentration_id} to requirement group ID {requirement_group_id}")
    with conn.cursor() as cur:
        try:
            cur.execute("""
                INSERT INTO concentration_requirement_link (concentration_id, requirement_group_id)
                VALUES (%s, %s)
            """, (concentration_id, requirement_group_id))
            print(f"Link inserted between concentration and requirement group")
        except Exception as e:
            print(f"Error linking concentration and requirement group: {e}")

def handle_course_or_note(conn, requirement_group_id, course_code):
    # Проверяем, является ли запись реальным кодом курса
    if check_course_exists(conn, course_code):
        insert_requirement_course_link(conn, requirement_group_id, course_code)
    else:
        # Если курс не существует – записываем как note
        insert_requirement_note(conn, requirement_group_id, course_code)

def process_requirement_groups(conn, program_id, groups, parent_id=None):
    for g in groups:
        g_id = insert_requirement_group(
            conn,
            program_id,
            parent_id,
            g["name"],
            g.get("selection_type"),
            g.get("required_credits")
        )

        # Если по какой-то причине группа не вставилась, пропускаем
        if g_id is None:
            continue

        courses = g.get("courses", [])
        for c in courses:
            # Если это специальные обозначения core или math уровней
            if c.startswith("Core:") or "MATH" in c or "**" in c:
                # Сразу записываем в notes
                insert_requirement_note(conn, g_id, c)
            else:
                # Проверяем есть ли такой курс
                handle_course_or_note(conn, g_id, c)

        subgroups = g.get("subgroups", [])
        if subgroups:
            process_requirement_groups(conn, program_id, subgroups, g_id)

def process_concentrations(conn, program_id, concentrations):
    for c in concentrations:
        c_id = insert_concentration(
            conn,
            program_id,
            c["name"],
            c.get("selection_type"),
            c.get("required_credits")
        )

        # Если концентрация не вставилась, пропускаем
        if c_id is None:
            continue

        subgroups = c.get("subgroups", [])
        if subgroups:
            for sg in subgroups:
                rg_id = insert_requirement_group(
                    conn,
                    program_id,
                    None,
                    sg["name"],
                    sg.get("selection_type"),
                    sg.get("required_credits")
                )
                # Если подгруппа не вставилась
                if rg_id is None:
                    continue

                for c_sg in sg.get("courses", []):
                    if c_sg.startswith("Core:") or "**" in c_sg:
                        insert_requirement_note(conn, rg_id, c_sg)
                    else:
                        handle_course_or_note(conn, rg_id, c_sg)

                insert_concentration_requirement_link(conn, c_id, rg_id)

def main():
    try:
        conn = psycopg2.connect(
            dbname="gu_scheduler",
            user="postgres",
            password="1103",
            host="localhost",
            port="5432"
        )
        print("Connected to the database successfully.")
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        exit(1)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    prereq_data_dir = os.path.join(script_dir, "..", "degree_req")

    for filename in os.listdir(prereq_data_dir):
        if filename.endswith(".json"):
            file_path = os.path.join(prereq_data_dir, filename)
            print(f"Processing file: {file_path}")
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Итерируемся по списку программ
                    for p in data.get("programs", []):
                        program_id = insert_program(conn, p["name"])
                        if program_id is None:
                            continue
                        # Обрабатываем requirement_groups для данной программы
                        process_requirement_groups(conn, program_id, p.get("requirement_groups", []))
                        # Обрабатываем concentrations для данной программы
                        process_concentrations(conn, program_id, p.get("concentrations", []))

                # После успешной обработки файла фиксируем изменения
                conn.commit()
                print(f"Changes committed to the database after processing {filename}.")
            except Exception as e:
                print(f"Error processing file '{filename}': {e}")
                # Если ошибка, мы можем решить откатить изменения данного файла:
                conn.rollback()

    conn.close()
    print("All done.")

if __name__ == "__main__":
    main()
