from flask import Flask,redirect, url_for
from flask import request, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import date, timedelta,datetime




app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///studyplanner.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)

    def __repr__(self):
        return f"<User {self.email}>"

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    user = db.relationship('User', backref=db.backref('subjects', lazy=True))

    def __repr__(self):
        return f"<Subject {self.name}>"

class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)

    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)

    subject = db.relationship('Subject', backref=db.backref('topics', lazy=True))

    def __repr__(self):
        return f"<Topic {self.name}>"

class Exam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exam_date = db.Column(db.Date, nullable=False)

    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)

    subject = db.relationship('Subject', backref=db.backref('exam', uselist=False))

    def __repr__(self):
        return f"<Exam {self.exam_date}>"

class StudyTime(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hours_per_day = db.Column(db.Float, nullable=False)
    days_per_week = db.Column(db.Integer, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    user = db.relationship('User', backref=db.backref('study_time', uselist=False))

    def __repr__(self):
        return f"<StudyTime {self.hours_per_day}h/day>"


class StudyTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    task_date = db.Column(db.Date, nullable=False)
    is_completed = db.Column(db.Boolean, default=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)

    user = db.relationship('User', backref=db.backref('tasks', lazy=True))
    subject = db.relationship('Subject')
    topic = db.relationship('Topic')

    def __repr__(self):
        return f"<Task {self.task_date} - {self.topic.name}>"




@app.route("/")
def home():
    return "Flask app running with database"

@app.route("/add-user")
def add_user():
    user = User(name="Aditya", email="aditya@gmail.com")
    db.session.add(user)
    db.session.commit()
    return "User added successfully"

@app.route("/users")
def get_users():
    users = User.query.all()
    data = []

    for u in users:
        data.append({
            "id": u.id,
            "name": u.name,
            "email": u.email
        })

    return data

@app.route("/add-subject", methods=["GET", "POST"])
def add_subject():
    user = User.query.first()  # temporary user

    if request.method == "POST":
        name = request.form["name"]

        subject = Subject(name=name, user_id=user.id)
        db.session.add(subject)
        db.session.commit()

        return f"Subject '{name}' added successfully"

    return '''
        <h2>Add Subject</h2>
        <form method="POST">
            <input type="text" name="name" placeholder="Subject name" required>
            <br><br>
            <button type="submit">Add Subject</button>
        </form>
    '''


@app.route("/subjects")
def get_subjects():
    subjects = Subject.query.all()
    data = []

    for s in subjects:
        data.append({
            "id": s.id,
            "name": s.name,
            "user_id": s.user_id
        })

    return data

@app.route("/add-topic", methods=["GET", "POST"])
def add_topic():
    subjects = Subject.query.all()

    if request.method == "POST":
        name = request.form["name"]
        subject_id = request.form["subject_id"]

        topic = Topic(name=name, subject_id=subject_id)
        db.session.add(topic)
        db.session.commit()

        return f"Topic '{name}' added successfully"

    return render_template("add_topic.html", subjects=subjects)



@app.route("/topics")
def get_topics():
    topics = Topic.query.all()
    data = []

    for t in topics:
        data.append({
            "id": t.id,
            "name": t.name,
            "subject_id": t.subject_id
        })

    return data

@app.route("/add-exam", methods=["GET", "POST"])
def add_exam():
    subjects = Subject.query.all()

    if request.method == "POST":
        subject_id = request.form["subject_id"]
        exam_date_str = request.form["exam_date"]
        exam_date = datetime.strptime(exam_date_str, "%Y-%m-%d").date()


        existing_exam = Exam.query.filter_by(subject_id=subject_id).first()

        if existing_exam:
            existing_exam.exam_date = exam_date
        else:
            exam = Exam(subject_id=subject_id, exam_date=exam_date)
            db.session.add(exam)

        db.session.commit()
        return "Exam date saved successfully"

    return render_template("add_exam.html", subjects=subjects)

@app.route("/exams")
def get_exams():
    exams = Exam.query.all()
    data = []

    for e in exams:
        data.append({
            "id": e.id,
            "exam_date": e.exam_date.strftime("%Y-%m-%d"),
            "subject_id": e.subject_id
        })

    return data

@app.route("/add-study-time", methods=["GET", "POST"])
def add_study_time():
    user = User.query.first()  # temporary

    if request.method == "POST":
        hours_per_day = float(request.form["hours_per_day"])
        days_per_week = int(request.form["days_per_week"])

        existing = StudyTime.query.filter_by(user_id=user.id).first()

        if existing:
            existing.hours_per_day = hours_per_day
            existing.days_per_week = days_per_week
        else:
            study_time = StudyTime(
                hours_per_day=hours_per_day,
                days_per_week=days_per_week,
                user_id=user.id
            )
            db.session.add(study_time)

        db.session.commit()
        return "Study time saved successfully"

    return render_template("add_study_time.html")


@app.route("/study-time")
def get_study_time():
    study_times = StudyTime.query.all()
    data = []

    for s in study_times:
        data.append({
            "id": s.id,
            "hours_per_day": s.hours_per_day,
            "days_per_week": s.days_per_week,
            "user_id": s.user_id
        })

    return data

@app.route("/generate-plan", methods=["GET", "POST"])
def generate_plan():
    if request.method == "POST":
        user = User.query.first()
        today = date.today()

        study_time = StudyTime.query.filter_by(user_id=user.id).first()
        if not study_time:
            return "Please set study time first"

        max_tasks_per_day = int(study_time.hours_per_day)
        if max_tasks_per_day == 0:
            return "Study time too low to generate plan"

        subjects = Subject.query.filter_by(user_id=user.id).all()

        for subject in subjects:
            exam = subject.exam
            topics = subject.topics

            if not exam or not topics:
                continue

            current_date = today
            tasks_today = 0

            for topic in topics:
                if current_date >= exam.exam_date:
                    break

                existing = StudyTask.query.filter_by(
                    user_id=user.id,
                    topic_id=topic.id
                ).first()

                if existing:
                    continue

                if tasks_today >= max_tasks_per_day:
                    current_date += timedelta(days=1)
                    tasks_today = 0

                task = StudyTask(
                    task_date=current_date,
                    user_id=user.id,
                    subject_id=subject.id,
                    topic_id=topic.id
                )

                db.session.add(task)
                tasks_today += 1

        db.session.commit()
        return "Smart study plan generated successfully"

    return render_template("generate_plan.html")


@app.route("/tasks")
def view_tasks():
    tasks = StudyTask.query.all()
    data = []

    for t in tasks:
        data.append({
            "date": t.task_date.strftime("%Y-%m-%d"),
            "subject": t.subject.name,
            "topic": t.topic.name,
            "completed": t.is_completed
        })

    return data

@app.route("/tasks/today")
def today_tasks():
    user = User.query.first()
    today = date.today()

    tasks = StudyTask.query.filter_by(
        user_id=user.id,
        task_date=today
    ).all()

    return render_template("today_tasks.html", tasks=tasks)


@app.route("/complete-task/<int:task_id>")
def complete_task(task_id):
    task = StudyTask.query.get(task_id)

    if not task:
        return "Task not found"

    task.is_completed = True
    db.session.commit()

    return f"Task {task_id} marked as completed"

@app.route("/auto-reschedule")
def auto_reschedule():
    today = date.today()

    missed_tasks = StudyTask.query.filter(
        StudyTask.task_date < today,
        StudyTask.is_completed == False
    ).all()

    if not missed_tasks:
        return "No missed tasks 🎉"

    new_date = today + timedelta(days=1)

    for task in missed_tasks:
        # Find next free date
        while StudyTask.query.filter_by(
            user_id=task.user_id,
            task_date=new_date
        ).first():
            new_date += timedelta(days=1)

        task.task_date = new_date
        new_date += timedelta(days=1)

    db.session.commit()
    return f"{len(missed_tasks)} task(s) rescheduled successfully"



@app.route("/dashboard")
def dashboard():
    user = User.query.first()
    today = date.today()

    tasks = StudyTask.query.filter_by(user_id=user.id).all()

    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if t.is_completed)
    pending_tasks = total_tasks - completed_tasks
    missed_tasks = sum(1 for t in tasks if t.task_date < today and not t.is_completed)

    completion_percentage = (
        (completed_tasks / total_tasks) * 100 if total_tasks else 0
    )

    subject_progress = {}

    for task in tasks:
        subject = task.subject.name
        if subject not in subject_progress:
            subject_progress[subject] = {"total": 0, "completed": 0}

        subject_progress[subject]["total"] += 1
        if task.is_completed:
            subject_progress[subject]["completed"] += 1

    for subject in subject_progress:
        total = subject_progress[subject]["total"]
        completed = subject_progress[subject]["completed"]
        subject_progress[subject]["percentage"] = round(
            (completed / total) * 100 if total else 0, 2
        )

    return render_template(
        "dashboard.html",
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        missed_tasks=missed_tasks,
        completion_percentage=round(completion_percentage, 2),
        subject_progress=subject_progress
    )




if __name__ == "__main__":
    app.run(debug=True)

with app.app_context():
    db.create_all()

