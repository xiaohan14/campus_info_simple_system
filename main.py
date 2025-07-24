from flask import Flask, redirect, request, jsonify, url_for, render_template, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from sklearn.cluster import KMeans
import pandas as pd
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:050114@localhost:3306/score_list?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
SECRET_KEY = 'your_secret_key'

db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    def __repr__(self):
        return f'<User {self.username}>'

class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    sex = db.Column(db.String(4), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    major = db.Column(db.String(50), nullable=False)
    address = db.Column(db.String(50), nullable=False)


class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    credit = db.Column(db.Float)
    teacher = db.Column(db.String(50))



class Grade(db.Model):
    __tablename__ = 'grades'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), db.ForeignKey('students.id', ondelete='CASCADE'))
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id', ondelete='CASCADE'))
    score = db.Column(db.Float)

    student = db.relationship('Student', backref='grades')
    course = db.relationship('Course', backref='grades')

@app.route('/log_in', methods=['GET'])
def log_in():
    return render_template('log_in.html')

@app.route("/api/log_in", methods=['POST'])
def api_log_in():
    data = request.json
    if not data:
        return jsonify({"message": "No data provided"}), 400
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username, password=password).first()
    if user:
        session['user_id'] = user.id
        session['username'] = user.username
        return jsonify({"message": "登录成功"}), 200
    else:
        return jsonify({"message": "用户名或密码错误"}), 401

@app.route("/api/sign_up", methods=['POST'])
def api_sign_up():
    data = request.json
    if not data:
        return jsonify({"message": "No data provided"}), 400
    username = data.get('username')
    password = data.get('password')  
    if not username or not password:
        return jsonify({"message": "用户名和密码不能为空"}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"message": "用户名已存在"}), 400
    new_user = User(username=username, password=password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "注册成功"}), 201

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('log_in'))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
@login_required
def index():
    return render_template('index.html')

@app.route("/student")
@login_required
def student():
    return render_template('student.html')

@app.route("/course")
@login_required
def course_grade():
    return render_template('course.html')

@app.route("/grade")
@login_required
def grade():
    return render_template('grade.html')

@app.route("/api/overview")
def api_overview():
    student_total = db.session.query(Student).count()
    major_total = db.session.query(Student.major).distinct().count()
    course_total = db.session.query(Course).count()
    teacher_total = db.session.query(Course.teacher).distinct().count()
    return jsonify({
        "student_total": student_total,
        "major_total": major_total,
        "course_total": course_total,
        "teacher_total": teacher_total
    })

@app.route("/api/student_count")
def api_student_count():
    student_count = db.session.query(Student).count()
    return jsonify({"student_count": student_count})

@app.route("/api/major_chart")
def api_major_chart():
    data = db.session.query(Student.major, db.func.count(Student.id)).group_by(Student.major).all()
    majors = [item[0] for item in data]
    counts = [item[1] for item in data]
    return jsonify({"names": majors, "counts": counts})

@app.route("/api/age_chart")
def api_age_chart():
    data = db.session.query(Student.age, db.func.count(Student.id)).group_by(Student.age).all()
    ages = [item[0] for item in data]
    counts = [item[1] for item in data]
    return jsonify({"names": ages, "counts": counts})

@app.route("/api/student_map")
def student_map():
    data = db.session.query(
        Student.address, 
        func.count(Student.id).label('count')
    ).group_by(Student.address).all()
        
        # 将地址映射为标准省份名
    province_mapping = {
        '北京': '北京市', '天津': '天津市', '上海': '上海市', '重庆': '重庆市', '河北': '河北省',
        '山西': '山西省', '辽宁': '辽宁省', '吉林': '吉林省', '黑龙江': '黑龙江省', '江苏': '江苏省',
        '浙江': '浙江省', '安徽': '安徽省', '福建': '福建省', '江西': '江西省', '山东': '山东省', 
        '河南': '河南省', '湖北': '湖北省', '湖南': '湖南省', '广东': '广东省', '海南': '海南省', 
        '四川': '四川省', '贵州': '贵州省', '云南': '云南省', '陕西': '陕西省', '甘肃': '甘肃省', 
        '青海': '青海省', '台湾': '台湾省', '广西': '广西壮族自治区', '内蒙古': '内蒙古自治区', 
        '西藏': '西藏自治区', '宁夏': '宁夏回族自治区', '新疆': '新疆维吾尔自治区', '香港': '香港特别行政区', 
        '澳门': '澳门特别行政区'
    }
        
    province_data = {}
    for addr, count in data:
        if addr:
            # 获取（GeoJSON全称）
            province = province_mapping.get(addr, addr)
            if province in province_data:
                province_data[province] += count
            else:
                province_data[province] = count
    result = [{"name": province, "value": count} for province, count in province_data.items()]
    return jsonify(result)

@app.route("/api/student_search", methods=['POST'])
def api_student_search():
    data = request.json
    if not data:
        return jsonify([])
    query = data.get("query", "")
    results = db.session.query(Student).filter(Student.name.contains(query)).all()
    return jsonify([{"id": student.id, "name": student.name} for student in results])

@app.route("/api/student_list")
def api_student_list():
    query = request.args.get('query', '').strip()
    major = request.args.get('major', '').strip()
    region = request.args.get('region', '').strip()
    q = db.session.query(Student)
    if query:
        q = q.filter(Student.name.contains(query))
    if major:
        q = q.filter(Student.major == major)
    if region:
        q = q.filter(Student.address == region)
    students = q.all()
    columns = ["学号", "姓名", "性别", "年龄", "专业", "生源地"]
    rows=[{
        "学号": student.id,
        "姓名": student.name,
        "性别": student.sex,
        "年龄": student.age,
        "专业": student.major,
        "生源地": student.address
    } for student in students]
    return jsonify({"columns": columns, "rows": rows})


@app.route("/api/delete_student", methods=['POST'])
def api_student_delete():
    data = request.json
    if not data:
        return jsonify({"message": "No data provided"}), 400
    student_id = data.get('id')
    student = db.session.get(Student, student_id)
    if student:
        # 先删除该学生的所有成绩记录
        db.session.query(Grade).filter(Grade.student_id == student_id).delete()
        # 再删除学生
        db.session.delete(student)
        db.session.commit()
        return jsonify({"message": "Student deleted successfully"}), 200
    else:
        return jsonify({"message": "Student not found"}), 404

@app.route("/api/add_student", methods=['POST'])
def api_add_student():
    data = request.json
    if not data:
        return jsonify({"message": "No data provided"}), 400
    # 新增：支持自定义id（学号）
    student_id = data.get('id', '')
    if not student_id:
        return jsonify({"message": "学号不能为空"}), 400
    # 检查学号是否已存在
    if Student.query.filter_by(id=student_id).first():
        return jsonify({"message": "学号已存在"}), 400
    # 检查所有字段
    name = data.get('name', '').strip()
    sex = data.get('sex', '').strip()
    age = data.get('age', '')
    major = data.get('major', '').strip()
    address = data.get('address', '').strip()
    if not all([name, sex, age, major, address]):
        return jsonify({"message": "所有字段均不能为空"}), 400
    new_student = Student(
        id=student_id,
        name=name,
        sex=sex,
        age=age,
        major=major,
        address=address
    )
    db.session.add(new_student)
    db.session.commit()
    return jsonify({"id": new_student.id}), 201

@app.route("/api/major_select")
def api_major_select():
    majors = db.session.query(Student.major).distinct().all()
    major_list = [major[0] for major in majors if major[0]]
    return jsonify(major_list)

@app.route("/api/region_select")
def api_region_select():
    regions = db.session.query(Student.address).distinct().all()
    region_list = [region[0] for region in regions if region[0]]
    return jsonify(region_list)

@app.route("/api/course_select")
def api_course_select():
    course = db.session.query(Course.name).distinct().all()
    course_list = [course[0] for course in course if course[0]]
    return jsonify(course_list)

# 获取课程详细信息
@app.route("/api/course_info")
def api_course_info():
    course_name = request.args.get('course', '').strip()
    if not course_name:
        return jsonify({
            "name": "",
            "credit": "",
            "teacher": "",
            "student_count": 0
        })
    
    course = db.session.query(Course).filter(Course.name == course_name).first()
    if not course:
        return jsonify({
            "name": "",
            "credit": "",
            "teacher": "",
            "student_count": 0
        })
    
    # 统计选课学生数量
    student_count = db.session.query(Grade).filter(Grade.course_id == course.id).count()
    
    return jsonify({
        "name": course.name,
        "credit": course.credit,
        "teacher": course.teacher,
        "student_count": student_count
    })

# 获取课程学生列表
@app.route("/api/course_student_list")
def api_course_student_list():
    course_name = request.args.get('course', '').strip()
    if not course_name:
        return jsonify({"columns": [], "rows": []})
    
    course = db.session.query(Course).filter(Course.name == course_name).first()
    if not course:
        return jsonify({"columns": [], "rows": []})
    
    # 查询选课学生信息
    students = db.session.query(
        Student.id,
        Student.name,
        Student.sex,
        Student.major,
    ).join(Grade, Student.id == Grade.student_id)\
     .filter(Grade.course_id == course.id).all()
    
    columns = ["学号", "姓名", "性别", "专业"]
    rows = [{
        "学号": student.id,
        "姓名": student.name,
        "性别": student.sex,
        "专业": student.major,
    } for student in students]
    
    return jsonify({"columns": columns, "rows": rows})

# 搜索教师课程
@app.route("/api/course_search")
def api_course_search():
    teacher = request.args.get('teacher', '').strip()
    if not teacher:
        return jsonify([])
    
    courses = db.session.query(Course).filter(Course.teacher.contains(teacher)).all()
    return jsonify([course.name for course in courses])

# 添加课程
@app.route("/api/add_course", methods=['POST'])
def api_add_course():
    data = request.json
    if not data:
        return jsonify({"message": "No data provided"}), 400
    
    name = data.get('name', '').strip()
    credit = data.get('credit', 0)
    teacher = data.get('teacher', '').strip()
    
    if not name or not teacher:
        return jsonify({"message": "课程名称和教师不能为空"}), 400
    
    # 检查课程是否已存在
    existing_course = db.session.query(Course).filter(Course.name == name).first()
    if existing_course:
        return jsonify({"message": "课程已存在"}), 400
    
    new_course = Course(name=name, credit=credit, teacher=teacher)
    db.session.add(new_course)
    db.session.commit()
    
    return jsonify({"message": "课程添加成功", "id": new_course.id}), 201

# 修改课程信息
@app.route("/api/update_course", methods=['POST'])
def api_update_course():
    data = request.json
    if not data:
        return jsonify({"message": "No data provided"}), 400
    
    course_name = data.get('name', '').strip()
    credit = data.get('credit', 0)
    teacher = data.get('teacher', '').strip()
    
    if not course_name or not teacher:
        return jsonify({"message": "课程名称和教师不能为空"}), 400
    
    course = db.session.query(Course).filter(Course.name == course_name).first()
    if not course:
        return jsonify({"message": "课程不存在"}), 404
    
    course.credit = credit
    course.teacher = teacher
    db.session.commit()
    
    return jsonify({"message": "课程信息更新成功"}), 200

# 添加学生到课程
@app.route("/api/add_student_to_course", methods=['POST'])
def api_add_student_to_course():
    data = request.json
    if not data:
        return jsonify({"message": "No data provided"}), 400
    
    course_name = data.get('course', '').strip()
    student_id = data.get('student_id', 0)
    
    if not course_name or not student_id:
        return jsonify({"message": "课程名称和学生ID不能为空"}), 400
    
    course = db.session.query(Course).filter(Course.name == course_name).first()
    student = db.session.query(Student).filter(Student.id == student_id).first()
    
    if not course:
        return jsonify({"message": "课程不存在"}), 404
    if not student:
        return jsonify({"message": "学生不存在"}), 404
    
    # 检查是否已经选课
    existing_grade = db.session.query(Grade).filter(
        Grade.course_id == course.id,
        Grade.student_id == student_id
    ).first()
    
    if existing_grade:
        return jsonify({"message": "学生已选此课程"}), 400
    
    new_grade = Grade(course_id=course.id, student_id=student_id)
    db.session.add(new_grade)
    db.session.commit()
    
    return jsonify({"message": "学生添加成功"}), 201

# 获取所有学生列表（用于添加学生到课程）
@app.route("/api/all_students")
def api_all_students():
    students = db.session.query(Student).all()
    return jsonify([{
        "id": student.id,
        "name": student.name,
        "major": student.major,
        "sex": student.sex,
        "age": student.age,
        "address": student.address
    } for student in students])

@app.route("/api/course_table")
def api_course_table():
    query = request.args.get('query', '').strip()
    major = request.args.get('major', '').strip()
    q = db.session.query(Student)
    if query:
        q = q.filter(Student.name.contains(query))
    if major:
        q = q.filter(Student.major == major)
    students = q.all()
    columns = ["学号", "姓名", "性别", "专业"]
    rows = [{
        "学号": student.id,
        "姓名": student.name,
        "性别": student.sex,
        "专业": student.major
    }for student in students]
    return jsonify({"columns": columns, "rows": rows})


# 箱线图
@app.route("/api/grade_boxplot")
def api_grade_boxplot():
    major = request.args.get('major', '').strip()
    course = request.args.get('course', '').strip()
    
    # 构建查询
    query = db.session.query(
        Student.name.label('student_name'),
        Student.major.label('major'),
        Course.name.label('course_name'),
        Grade.score.label('score')
    ).join(Grade, Student.id == Grade.student_id)\
     .join(Course, Course.id == Grade.course_id)
    
    # 筛选
    if major:
        query = query.filter(Student.major == major)
    if course:
        query = query.filter(Course.name == course)
    
    results = query.all()
    
    if major and course:
        # 专业+课程
        scores = [r.score for r in results if r.score is not None]
        raw_data = [scores] if scores else []
        categories = [f"{major}-{course}"] if scores else []
    elif major and not course:
        # 专业+全部课程
        course_scores = {}
        for r in results:
            if r.score is not None:
                course_scores.setdefault(r.course_name, []).append(r.score)
        categories = list(course_scores.keys())
        raw_data = list(course_scores.values())
    elif course and not major:
        # 课程+全部专业
        major_scores = {}
        for r in results:
            if r.score is not None:
                major_scores.setdefault(r.major, []).append(r.score)
        categories = list(major_scores.keys())
        raw_data = list(major_scores.values())
    else:
        # 全部+全部：显示专业
        major_scores = {}
        for r in results:
            if r.score is not None:
                major_scores.setdefault(r.major, []).append(r.score)
        categories = list(major_scores.keys())
        raw_data = list(major_scores.values())

    # 保证类别和raw_data一一对应且都不为空
    filtered = [(cat, arr) for cat, arr in zip(categories, raw_data) if arr]
    categories = [cat for cat, arr in filtered]
    raw_data = [arr for cat, arr in filtered]
    return jsonify({
        "categories": categories,
        "rawData": raw_data
    })

# 平均成绩
@app.route("/api/grade_avg")
def api_grade_avg():
    major = request.args.get('major', '').strip()
    course = request.args.get('course', '').strip()
    
    if major and course:
        # 专业+课程：显示单个平均分
        query = db.session.query(
            func.avg(Grade.score).label('avg_score')
        ).join(Student, Student.id == Grade.student_id)\
         .join(Course, Course.id == Grade.course_id)\
         .filter(Student.major == major, Course.name == course)
        
        result = query.first()
        if result and result.avg_score:
            names = [f"{major}-{course}"]
            counts = [round(float(result.avg_score), 2)]
        else:
            names = []
            counts = []
    elif major and not course:
        # 专业+全部课程：按课程分组
        query = db.session.query(
            Course.name.label('course_name'),
            func.avg(Grade.score).label('avg_score')
        ).join(Student, Student.id == Grade.student_id)\
         .join(Course, Course.id == Grade.course_id)\
         .filter(Student.major == major)\
         .group_by(Course.name)
        
        results = query.all()
        names = [r.course_name for r in results]
        counts = [round(float(r.avg_score), 2) for r in results]
    elif course and not major:
        # 课程+全部专业：按专业分组
        query = db.session.query(
            Student.major.label('major'),
            func.avg(Grade.score).label('avg_score')
        ).join(Student, Student.id == Grade.student_id)\
         .join(Course, Course.id == Grade.course_id)\
         .filter(Course.name == course)\
         .group_by(Student.major)
        
        results = query.all()
        names = [r.major for r in results]
        counts = [round(float(r.avg_score), 2) for r in results]
    else:
        # 全部+全部：按专业分组
        query = db.session.query(
            Student.major.label('major'),
            func.avg(Grade.score).label('avg_score')
        ).join(Student, Student.id == Grade.student_id)\
         .join(Course, Course.id == Grade.course_id)\
         .group_by(Student.major)
        
        results = query.all()
        names = [r.major for r in results]
        counts = [round(float(r.avg_score), 2) for r in results]
    
    return jsonify({
        "names": names,
        "counts": counts
    })

# 成绩表
@app.route("/api/grade_info")
def api_grade_info():
    major = request.args.get('major', '').strip()
    course = request.args.get('course', '').strip()

    query = db.session.query(Grade.score, Student.id).join(Student, Student.id == Grade.student_id).join(Course, Course.id == Grade.course_id)
    if major:
        query = query.filter(Student.major == major)
    if course:
        query = query.filter(Course.name == course)
    results = query.all()

    from collections import defaultdict
    student_scores = defaultdict(list)
    for score, student_id in results:
        if score is not None:
            student_scores[student_id].append(score)

    if not student_scores:
        return jsonify({
            "total_students": 0,
            "avg_score": 0,
            "pass_rate": 0,
            "excellent_rate": 0,
            "level_count": {"优秀": 0, "良好": 0, "及格": 0, "挂科": 0}
        })

    total_students = len(student_scores)
    avg_scores = [sum(scores)/len(scores) for scores in student_scores.values()]
    avg_score = sum(avg_scores) / total_students
    pass_count = sum(1 for s in avg_scores if s >= 60)
    excellent_count = sum(1 for s in avg_scores if s >= 85)
    pass_rate = (pass_count / total_students) * 100
    excellent_rate = (excellent_count / total_students) * 100

        # 统计等级分布
    level_count = {"优秀": 0, "良好": 0, "及格": 0, "挂科": 0}
    for s in avg_scores:
        if s >= 85:
            level_count["优秀"] += 1
        elif s >= 70:
            level_count["良好"] += 1
        elif s >= 60:
            level_count["及格"] += 1
        else:
            level_count["挂科"] += 1

    names = list(level_count.keys())
    counts = list(level_count.values())

    return jsonify({
        "total_students": total_students,
        "avg_score": avg_score,
        "pass_rate": pass_rate,
        "excellent_rate": excellent_rate,
        "level_count": level_count,
        "names": names,
        "counts": counts
    })

# 成绩表格
@app.route("/api/grade_table")
def api_grade_table():
    major = request.args.get('major', '').strip()
    course = request.args.get('course', '').strip()
    
    # 查询
    query = db.session.query(
        Student.id.label('student_id'),
        Student.name.label('student_name'),
        Student.sex.label('sex'),
        Student.major.label('major'),
        Course.name.label('course_name'),
        Grade.score.label('score')
    ).join(Grade, Student.id == Grade.student_id)\
     .join(Course, Course.id == Grade.course_id)
    
    # 应用筛选条件
    if major:
        query = query.filter(Student.major == major)
    if course:
        query = query.filter(Course.name == course)

    student_id = request.args.get('student_id', '').strip()
    student_name = request.args.get('student_name', '').strip()
    if student_id:
       query = query.filter(Student.id == student_id)
    if student_name:
        query = query.filter(Student.name.contains(student_name))
    
    results = query.all()
    
    columns = ["学号", "姓名", "性别", "专业", "课程", "成绩", "是否及格"]
    rows = []
    
    for r in results:
        is_pass = "是" if r.score and r.score >= 60 else "否"
        rows.append({
            "学号": r.student_id,
            "姓名": r.student_name,
            "性别": r.sex,
            "专业": r.major,
            "课程": r.course_name,
            "成绩": r.score if r.score else "无",
            "是否及格": is_pass
        })
    
    return jsonify({"columns": columns, "rows": rows})

@app.route("/api/add_grade", methods=['POST'])
def api_add_grade():
    data = request.json
    if not data:
        return jsonify({"message": "No data provided"}), 400
    
    student_id = data.get('student_id', 0)
    student_name = data.get('student_name', '')
    major = data.get('major', '')
    course = data.get('course', '')
    score = data.get('score', 0)

    if not student_id or not student_name or not major or not course or not score:
        return jsonify({"message": "Missing required fields"}), 400
    
    student = Student.query.filter_by(id=student_id, name=student_name, major=major).first()
    if not student:
        return jsonify({"message": "Student not found"}), 404
    
    course_obj = Course.query.filter_by(name=course).first()
    if not course_obj:
        return jsonify({"message": "Course not found"}), 404

    # 检查是否已有成绩
    existing_grade = Grade.query.filter_by(student_id=student_id, course_id=course_obj.id).first()
    if existing_grade:
        # 覆盖成绩
        existing_grade.score = score
        db.session.commit()
        return jsonify({"message": "Grade updated successfully"}), 200

    # 没有则新增
    new_grade = Grade(student_id=student_id, course_id=course_obj.id, score=score)
    db.session.add(new_grade)
    db.session.commit()

    return jsonify({"message": "Grade added successfully"}), 201

@app.route("/api/get_student_by_id")
def get_student_by_id():
    student_id = request.args.get('student_id', '').strip()
    if not student_id:
        return jsonify({"message": "No student_id provided"}), 400
    # student_id 现在是字符串类型，不需要转换
    student = Student.query.filter_by(id=student_id).first()
    if not student:
        return jsonify({"message": "Student not found"}), 404
    return jsonify({
        "id": student.id,
        "name": student.name,
        "major": student.major
    })

# 课程热度
@app.route("/api/course_heat")
def api_course_heat():
    engine = db.engine

    results = db.session.query(
        Course.id,
        Course.name,
        Course.credit,
        func.count(Grade.id).label('student_count'),
        func.avg(Grade.score).label('avg_score'),
        func.stddev(Grade.score).label('score_std')
    ).outerjoin(Grade, Course.id == Grade.course_id).group_by(Course.id).all()

    import pandas as pd
    df = pd.DataFrame(results, columns=['id', 'name', 'credit', 'student_count', 'avg_score', 'score_std'])
    df = df.fillna(0)

    # 聚类要>=3个样本
    if len(df) < 3:
        return jsonify([])

    features = df[['credit', 'student_count', 'avg_score', 'score_std']]
    kmeans = KMeans(n_clusters=3, random_state=42)
    df['cluster'] = kmeans.fit_predict(features)

    cluster_order = df.groupby('cluster')['student_count'].mean().sort_values().index.tolist()
    # 从少到多对应冷到热
    label_map = {cluster_order[0]: '冷门', cluster_order[1]: '中热', cluster_order[2]: '热门'}
    df['heat_level'] = df['cluster'].replace(label_map)

    result = df[['name', 'heat_level']].to_dict(orient='records')
    return jsonify(result)


# 删除课程
@app.route("/api/delete_course", methods=['POST'])
def api_delete_course():
    data = request.json
    if not data or not data.get('name'):
        return jsonify({"message": "No course name provided"}), 400
    course = db.session.query(Course).filter(Course.name == data['name']).first()
    if not course:
        return jsonify({"message": "课程不存在"}), 404
    # 删除该课程的所有成绩记录
    db.session.query(Grade).filter(Grade.course_id == course.id).delete()
    db.session.delete(course)
    db.session.commit()
    return jsonify({"message": "课程删除成功"}), 200

# 课程移除学生
@app.route("/api/delete_student_from_course", methods=['POST'])
def api_delete_student_from_course():
    data = request.json
    if not data:
        return jsonify({"message": "No data provided"}), 400
    course_name = data.get('course', '').strip()
    student_id = data.get('student_id', 0)
    if not course_name or not student_id:
        return jsonify({"message": "课程名称和学生ID不能为空"}), 400
    course = db.session.query(Course).filter(Course.name == course_name).first()
    if not course:
        return jsonify({"message": "课程不存在"}), 404
    grade = db.session.query(Grade).filter(Grade.course_id == course.id, Grade.student_id == student_id).first()
    if not grade:
        return jsonify({"message": "该学生未选此课程"}), 404
    db.session.delete(grade)
    db.session.commit()
    return jsonify({"message": "学生已从课程移除"}), 200

@app.route("/api/delete_grade", methods=['POST'])
def api_delete_grade():
    data = request.json
    if not data:
        return jsonify({"message": "No data provided"}), 400
    student_id = data.get('student_id')
    course_name = data.get('course_name')
    if not student_id or not course_name:
        return jsonify({"message": "参数不完整"}), 400
    course = Course.query.filter_by(name=course_name).first()
    if not course:
        return jsonify({"message": "课程不存在"}), 404
    grade = Grade.query.filter_by(student_id=student_id, course_id=course.id).first()
    if not grade:
        return jsonify({"message": "成绩记录不存在"}), 404
    db.session.delete(grade)
    db.session.commit()
    return jsonify({"message": "删除成功"}), 200

if __name__ == "__main__":
    app.run(debug=True)
