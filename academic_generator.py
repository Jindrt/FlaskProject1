import random
from datetime import datetime, timedelta
from faker import Faker

fake = Faker('zh_CN')

# 常量定义
JOURNALS = ["科学通报", "清华大学学报", "中国科学", "Nature", "Science"]
DEPARTMENTS = ["计算机系", "电子系", "自动化系", "微电子所", "交叉信息院"]

def generate_academic_title(author_type):
    """生成学术论文标题"""
    disciplines = {
        "工科": ["基于", "面向", "多模态", "智能", "协同"],
        "理科": ["量子", "拓扑", "非线性", "熵", "对称性"],
        "文科": ["后现代", "文化认同", "全球化", "话语体系"]
    }

    methods = {
        "工科": ["优化算法", "深度学习", "仿真", "系统设计"],
        "理科": ["理论推导", "数值模拟", "实验验证"],
        "文科": ["话语分析", "田野调查", "比较研究"]
    }

    subjects = {
        "工科": ["无人机集群", "区块链", "5G网络"],
        "理科": ["黑洞", "超导体", "量子纠缠"],
        "文科": ["乡村振兴", "一带一路", "文化记忆"]
    }

    field = random.choice(["工科", "理科", "文科"]) if author_type == "教师" else random.choice(["工科", "理科"])

    template = random.choice([
        f"{{discipline}}{{subject}}的{{method}}研究",
        f"{{method}}在{{discipline}}{{subject}}中的应用"
    ])

    title = template.format(
        discipline=random.choice(disciplines[field]),
        method=random.choice(methods[field]),
        subject=random.choice(subjects[field])
    )

    if random.random() < 0.3:
        title += f": 以{random.choice(['清华大学', '北京市'])}为例"

    return title


def generate_data():
    """生成随机学术数据"""
    departments = ["计算机系", "电子系", "自动化系", "微电子所", "交叉信息院"]

    # 生成教职工
    faculty = []
    for _ in range(random.randint(15, 25)):
        faculty_id = f"TH{random.randint(2000, 2023)}{random.randint(1000, 9999):04d}"
        faculty.append({
            'id': faculty_id,
            'name': fake.name(),
            'gender': random.choice(["男", "女"]),
            'birth_date': (datetime.now() - timedelta(days=random.randint(365 * 25, 365 * 65))).strftime("%Y-%m-%d"),
            'title': random.choice(["讲师", "副教授", "教授"]),
            'department': random.choice(departments),
            'major': random.choice(["人工智能", "量子计算", "新能源"]),
            'hire_year': random.randint(1990, 2023),
            'email': f"{fake.name()}@tsinghua.edu.cn"
        })

    # 生成学生
    students = []
    faculty_ids = [f['id'] for f in faculty]
    for _ in range(random.randint(40, 60)):
        students.append({
            'id': f"{random.randint(2018, 2023)}{random.randint(1000, 9999):04d}",
            'name': fake.name(),
            'gender': random.choice(["男", "女"]),
            'department': random.choice(departments),
            'major': random.choice(["计算机科学", "电子工程", "物理学"]),
            'grade': f"{random.randint(2018, 2023)}级",
            'advisor_id': random.choice(faculty_ids),
            'email': f"{fake.name()}@mails.tsinghua.edu.cn"
        })

    # 生成论文 # 生成论文时区分教师/学生作者
    papers = []
    all_authors = []
    # 创建教师作者列表
    teacher_authors = [{'id': f['id'], 'type': '教师'} for f in faculty]
    # 创建学生作者列表（仅博士生可发表论文）
    student_authors = [{'id': s['id'], 'type': '学生'}
                       for s in students if int(s['grade'][:4]) <= 2020]  # 假设2020级及以前是博士生

    all_authors = teacher_authors + student_authors
    for _ in range(random.randint(80, 120)):
        author = random.choice(all_authors)
        papers.append({
            'id': f"P{random.randint(2010, 2023)}{random.randint(10000, 99999)}",
            'title': generate_academic_title(author['type']),
            'author_id': author['id'],
            'author_type': author['type'],
            'journal': random.choice(JOURNALS),  # 使用常量
            'year': random.randint(2015, 2023),
            'impact_factor': round(random.uniform(1.0, 20.0), 2),
            'keywords': "; ".join(random.sample(["AI", "机器学习", "大数据", "量子"], random.randint(2, 3)))
        })

    return {
        'faculty': faculty,
        'students': students,
        'papers': papers
    }