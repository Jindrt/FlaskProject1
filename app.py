from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
from mysql.connector import Error
from academic_generator import generate_data
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# 数据库配置
db_config = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
    'charset': 'utf8mb4'
}


def get_db_connection():
    """获取数据库连接"""
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except Error as e:
        print(f"数据库连接失败: {e}")
        return None


def check_tables_exist(conn):
    cursor = conn.cursor()
    try:
        # 先删除可能存在的旧表（仅开发环境使用）
        cursor.execute("DROP TABLE IF EXISTS papers, students, faculty")

        # 重新创建表（使用新结构）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS faculty(
                faculty_id VARCHAR  (20) PRIMARY KEY,
                name VARCHAR(50) NOT NULL,
                gender ENUM
                       (
                           '男',
                           '女'
                       ) NOT NULL,
                           birth_date DATE,
                           title VARCHAR
                       (
                           20
                       ),
                           department VARCHAR
                       (
                           50
                       ),
                           major VARCHAR
                       (
                           50
                       ),
                           hire_year INT,
                           email VARCHAR
                       (
                           100
                       )
                           )
                       """)

        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS students
                       (
                           student_id
                           VARCHAR
                       (
                           20
                       ) PRIMARY KEY,
                           name VARCHAR
                       (
                           50
                       ) NOT NULL,
                           gender ENUM
                       (
                           '男',
                           '女'
                       ) NOT NULL,
                           department VARCHAR
                       (
                           50
                       ),
                           major VARCHAR
                       (
                           50
                       ),
                           grade VARCHAR
                       (
                           20
                       ),
                           advisor_id VARCHAR
                       (
                           20
                       ),
                           email VARCHAR
                       (
                           100
                       ),
                           FOREIGN KEY
                       (
                           advisor_id
                       ) REFERENCES faculty
                       (
                           faculty_id
                       )
                           )
                       """)

        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS papers
                       (
                           paper_id
                           VARCHAR
                       (
                           20
                       ) PRIMARY KEY,
                           title VARCHAR
                       (
                           200
                       ) NOT NULL,
                           author_id VARCHAR
                       (
                           20
                       ) NOT NULL,
                           author_type ENUM
                       (
                           '教师',
                           '学生'
                       ) NOT NULL,
                           journal VARCHAR
                       (
                           100
                       ),
                           publish_year INT,
                           impact_factor FLOAT,
                           keywords TEXT,
                           INDEX
                       (
                           author_id,
                           author_type
                       )
                           )
                       """)
        conn.commit()
    except Error as e:
        print(f"创建表时出错: {e}")
        conn.rollback()
    finally:
        cursor.close()


def validate_data(data):
    """增强版数据验证"""
    faculty_ids = {f['id'] for f in data['faculty']}
    student_ids = {s['id'] for s in data['students']}

    valid_papers = []
    invalid_papers = []

    for paper in data['papers']:
        if paper['author_type'] == '教师' and paper['author_id'] in faculty_ids:
            valid_papers.append(paper)
        elif paper['author_type'] == '学生' and paper['author_id'] in student_ids:
            valid_papers.append(paper)
        else:
            invalid_papers.append(paper)

    if invalid_papers:
        print(f"过滤掉 {len(invalid_papers)} 篇无效论文，示例如下：")
        for p in invalid_papers[:3]:
            print(f"论文ID: {p['id']}, 作者ID: {p['author_id']}, 类型: {p['author_type']}")

    data['papers'] = valid_papers
    return data

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/generate', methods=['POST'])
def generate_and_save():
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return "数据库连接失败", 500

        conn.start_transaction()
        cursor = conn.cursor()

        # 强制重建表结构
        check_tables_exist(conn)

        # 生成并验证数据
        data = validate_data(generate_data())

        # 按正确顺序插入
        # 1. 插入教师
        faculty_values = [(f['id'], f['name'], f['gender'], f['birth_date'],
                           f['title'], f['department'], f['major'],
                           f['hire_year'], f['email']) for f in data['faculty']]
        cursor.executemany(
            "INSERT INTO faculty VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            faculty_values
        )

        # 2. 插入学生
        student_values = [(s['id'], s['name'], s['gender'], s['department'],
                           s['major'], s['grade'], s['advisor_id'],
                           s['email']) for s in data['students']]
        cursor.executemany(
            "INSERT INTO students VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            student_values
        )

        # 3. 插入论文
        paper_values = [(p['id'], p['title'], p['author_id'], p['author_type'],
                         p['journal'], p['year'], p['impact_factor'],
                         p['keywords']) for p in data['papers']]
        cursor.executemany(
            "INSERT INTO papers VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            paper_values
        )

        conn.commit()
        return redirect(url_for('view_data'))

    except Exception as e:
        if conn: conn.rollback()
        return f"操作失败: {str(e)}", 500
    finally:
        if conn and conn.is_connected():
            if 'cursor' in locals(): cursor.close()
            conn.close()

@app.route('/view')
def view_data():
    """查看数据库中的数据"""
    conn = get_db_connection()
    if not conn:
        return "数据库连接失败", 500

    try:
        cursor = conn.cursor(dictionary=True)

        # 获取教职工数据
        cursor.execute("SELECT * FROM faculty ORDER BY hire_year DESC LIMIT 20")
        faculty = cursor.fetchall()

        # 获取学生数据
        cursor.execute("""
                       SELECT s.*, f.name as advisor_name
                       FROM students s
                                JOIN faculty f ON s.advisor_id = f.faculty_id
                       ORDER BY s.grade DESC LIMIT 20
                       """)
        students = cursor.fetchall()

        # 获取论文数据
        # --- 插入点：替换原有的论文查询 ---
        cursor.execute("""
            SELECT p.*,
                   CASE
                       WHEN p.author_type = '教师' THEN f.name
                       WHEN p.author_type = '学生' THEN s.name
                   END as author_name,
                   CASE
                       WHEN p.author_type = '教师' THEN f.department
                       WHEN p.author_type = '学生' THEN s.department
                   END as author_dept
            FROM papers p
            LEFT JOIN faculty f ON p.author_id = f.faculty_id AND p.author_type = '教师'
            LEFT JOIN students s ON p.author_id = s.student_id AND p.author_type = '学生'
            ORDER BY p.impact_factor DESC LIMIT 20
        """)
        papers = cursor.fetchall()
        # --- 插入结束 ---

        return render_template('view.html',
                               faculty=faculty,
                               students=students,
                               papers=papers)

    except Error as e:
        return f"数据库查询失败: {e}", 500
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)