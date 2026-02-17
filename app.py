from flask import Flask,redirect, url_for,session, flash
from flask import request, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import date, timedelta,datetime
from werkzeug.security import generate_password_hash, check_password_hash





app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///studyplanner.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
app.config['SECRET_KEY'] = 'supersecretkey'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

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
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return render_template("home.html")





@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return render_template("register.html", error="User already exists")

        hashed_password = generate_password_hash(password)

        user = User(
            name=name,
            email=email,
            password=hashed_password
        )

        db.session.add(user)
        db.session.commit()

        session["user_id"] = user.id

        return redirect(url_for("add_study_time"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password, password):
            return "Invalid credentials"

        if not user:
            return "Invalid credentials"

        session["user_id"] = user.id
        return redirect(url_for("dashboard"))

    return '''
        <h2>Login</h2>
        <form method="POST">
            <input name="email" placeholder="Email" required><br><br>
            <input name="password" type="password" placeholder="Password" required><br><br>
            <button type="submit">Login</button>
        </form>
    '''

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("login"))


@app.route("/add-user")
def add_user():
    class User(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(100), nullable=False)
        email = db.Column(db.String(100), unique=True, nullable=False)
        password = db.Column(db.String(200), nullable=False)

        def __repr__(self):
            return f"<User {self.email}>"


@app.route("/users")
def get_users():
    users = User.query.all()
    data = []

    for u in users:
        data.append({
            "id": u.id,
            "name": u.name,
            "email": u.email,
            
        })

    return data

@app.route("/add-subject", methods=["GET", "POST"])
def add_subject():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    user = User.query.get(user_id)

    if request.method == "POST":
        name = request.form["name"]

        subject = Subject(name=name, user_id=user.id)
        db.session.add(subject)
        db.session.commit()

        flash("Subject added successfully!", "success")

    return render_template("add_subject.html")



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
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    subjects = Subject.query.filter_by(user_id=user_id).all()

    if request.method == "POST":
        subject_id = request.form.get("subject_id")
        topics_input = request.form.get("topic_names")

        if not subject_id or not topics_input:
            flash("Please select subject and enter topics.", "danger")
            return redirect(url_for("add_topic"))

        # Split by comma
        topic_list = topics_input.split(",")

        added_count = 0

        for topic_name in topic_list:
            cleaned_name = topic_name.strip()

            if cleaned_name:
                # Avoid duplicates
                existing_topic = Topic.query.filter_by(
                    name=cleaned_name,
                    subject_id=subject_id
                ).first()

                if not existing_topic:
                    new_topic = Topic(
                        name=cleaned_name,
                        subject_id=subject_id
                    )
                    db.session.add(new_topic)
                    added_count += 1

        db.session.commit()

        flash(f"{added_count} topic(s) added successfully!", "success")
        return redirect(url_for("dashboard"))

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
        flash("Date added successfully!", "success")

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
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    user = User.query.get(user_id)

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
        flash("Study-Time added successfully!", "success")

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
        user_id = session.get("user_id")
        if not user_id:
            return redirect(url_for("login"))

        user = User.query.get(user_id)
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
        flash("Plan generated successfully!", "success")

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

@app.route("/tasks/all")
def all_tasks():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    tasks = StudyTask.query.filter_by(user_id=user_id)\
        .order_by(StudyTask.task_date).all()

    return render_template("all_tasks.html", tasks=tasks)


@app.route("/tasks/today")
def today_tasks():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    user = User.query.get(user_id)
    today = date.today()

    tasks = StudyTask.query.filter_by(
        user_id=user.id,
        task_date=today
    ).all()

    return render_template("today_tasks.html", tasks=tasks)

@app.route("/tasks/update", methods=["POST"])
def bulk_complete_tasks():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    selected_tasks = request.form.getlist("completed_tasks")

    # Reset all tasks first
    user_tasks = StudyTask.query.filter_by(user_id=user_id).all()
    for task in user_tasks:
        task.is_completed = False

    # Mark selected ones as completed
    for task_id in selected_tasks:
        task = StudyTask.query.get(int(task_id))
        if task and task.user_id == user_id:
            task.is_completed = True

    db.session.commit()

    return redirect(url_for("all_tasks"))


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
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    user = User.query.get(user_id)
    today = date.today()

    tasks = StudyTask.query.filter_by(user_id=user.id).all()

    total_tasks = len(tasks)
    completed_tasks = 0
    pending_tasks = 0
    missed_tasks = 0
    today_tasks = 0
    upcoming_tasks = 0

    for task in tasks:
        if task.is_completed:
            completed_tasks += 1
        else:
            pending_tasks += 1

            if task.task_date < today:
                missed_tasks += 1
            elif task.task_date == today:
                today_tasks += 1
            else:
                upcoming_tasks += 1

    completion_percentage = (
        (completed_tasks / total_tasks) * 100 if total_tasks else 0
    )

    # Subject Progress
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

    # -------------------------
    # Progress Prediction
    # -------------------------

    prediction_message = None
    predicted_finish = None  # IMPORTANT: define outside

    if completed_tasks > 0:
        first_task = StudyTask.query.filter_by(user_id=user.id)\
            .order_by(StudyTask.task_date).first()

        if first_task:
            days_passed = (today - first_task.task_date).days + 1

            if days_passed > 0:
                avg_tasks_per_day = completed_tasks / days_passed
                remaining_tasks = total_tasks - completed_tasks

                if avg_tasks_per_day > 0 and remaining_tasks > 0:
                    predicted_days = remaining_tasks / avg_tasks_per_day
                    predicted_finish = today + timedelta(days=int(predicted_days))

                    prediction_message = (
                        f"At current pace, you will finish by "
                        f"{predicted_finish.strftime('%Y-%m-%d')}"
                    )

    # -------------------------
    # Exam Check
    # -------------------------

    exam = Exam.query.join(Subject).filter(
        Subject.user_id == user.id
    ).order_by(Exam.exam_date).first()

    status_message = None
    status_type = None

    if predicted_finish and exam:
        if predicted_finish <= exam.exam_date:
            status_message = "You are on track to complete before the exam."
            status_type = "success"
        else:
            status_message = "You may not finish before the exam. Consider increasing study time."
            status_type = "danger"

    return render_template(
        "dashboard.html",
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        missed_tasks=missed_tasks,
        today_tasks=today_tasks,
        upcoming_tasks=upcoming_tasks,
        completion_percentage=round(completion_percentage, 2),
        subject_progress=subject_progress,
        prediction_message=prediction_message,
        status_message=status_message,
        status_type=status_type
    )





if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
