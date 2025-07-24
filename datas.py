from main import db, Student, Course, Grade, app
import random

credit_all = [1, 1.5, 2, 2.5, 3]
teacher_all = ['张伟', '王强', '李明', '孙明德', '覃燕', '陈胜强', '吴丹', '谭国强']
major_all = ['数据科学与大数据技术', '机器人工程', '人工智能']
course_all = ['数据库原理', '计算机网络组成', '数据结构与算法', '数值计算', '人工智能导论', '人工智能数学基础', '高等数学', '线性代数']
address_all = ['广西', '广东', '北京', '黑龙江', '辽宁', '吉林', '河北', '山西', '陕西', '甘肃', '青海', '山东', '安徽', '浙江',
               '河南', '河北', '湖北', '湖南', '江西', '福建', '云南', '海南', '四川', '贵州', '内蒙古', '新疆', '西藏', '宁夏',
               '上海', '天津', '重庆']

with app.app_context():
    db.drop_all()
    db.create_all()

    for i in range(101):
        s = Student(
            id=str(230160000 + i + 1),
            name=f'学生{i+1}',
            age=random.randint(18,23),
            sex=random.choice(['男', '女']),
            major=random.choice(major_all),
            address=random.choice(address_all)
        )
        db.session.add(s)
    db.session.commit()

    for name in course_all:
        c = Course(
            name=name,
            credit=random.choice(credit_all),
            teacher=random.choice(teacher_all)
        )
        db.session.add(c)
    db.session.commit()

    students = Student.query.all()
    courses = Course.query.all()
    for s in students:
        selected_courses = random.sample(courses, k=random.randint(4, 6))
        for c in selected_courses:
            g = Grade(
                student_id=str(s.id),
                course_id=c.id,
                score=random.uniform(40, 100)
            )
            db.session.add(g)

    db.session.commit()
