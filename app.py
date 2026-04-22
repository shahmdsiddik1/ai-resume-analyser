import os
import re
from flask import Flask, render_template, request, redirect, url_for, flash
import pdfplumber
import pytesseract
from PIL import Image
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# ================= TESSERACT =================
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ================= APP =================
app = Flask(__name__)

app.config["UPLOAD_FOLDER"] = "uploads"
app.config["SECRET_KEY"] = "secret123"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# ================= USER MODEL =================
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ================= AUTH =================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if User.query.filter_by(username=username).first():
            flash("⚠️ User already exists", "error")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)  # ✅ auto login
        flash("✅ Registered successfully!", "success")

        return redirect(url_for("index"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("✅ Login successful!", "success")
            return redirect(url_for("index"))

        flash("❌ Invalid username or password", "error")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# ================= TEXT EXTRACTION =================
def extract_text(filepath):
    text = ""

    try:
        if filepath.lower().endswith(".pdf"):
            with pdfplumber.open(filepath) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""

        elif filepath.lower().endswith((".jpg", ".jpeg", ".png")):
            image = Image.open(filepath)
            text = pytesseract.image_to_string(image)

    except Exception as e:
        print("ERROR:", e)

    return text


# ================= YOUR ORIGINAL LOGIC =================
def extract_basic_info(text):
    name = "Not Found"
    email = "Not Found"

    email_match = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}", text)
    if email_match:
        email = email_match[0]

    lines = text.strip().split("\n")
    for line in lines:
        line = line.strip()
        if len(line) > 2 and len(line.split()) <= 4:
            if "resume" not in line.lower():
                name = line
                break

    return name, email


def analyze_skills(text):
    skills_list = [
        "python", "java", "c++", "sql", "html", "css",
        "javascript", "machine learning", "aws", "docker",
        "kubernetes", "linux", "react", "node",
        "git", "github"
    ]

    found = []
    text = text.lower()

    for skill in skills_list:
        if skill in text:
            found.append(skill.upper())

    return list(set(found)) if found else ["No skills detected"]


def calculate_score(skills):
    if "No skills detected" in skills:
        return 5.0
    return round((len(skills) / 15) * 100, 2)


def missing_skills(found):
    important = ["PYTHON", "AWS", "DOCKER", "KUBERNETES", "GIT"]
    return [s for s in important if s not in found]


def analyze_roles(skills):
    roles = {
        "Cloud Engineer": 0,
        "DevOps Engineer": 0,
        "Data Scientist": 0
    }

    for s in skills:
        if s in ["AWS", "DOCKER", "KUBERNETES"]:
            roles["Cloud Engineer"] += 1
            roles["DevOps Engineer"] += 1

        if s in ["PYTHON", "MACHINE LEARNING"]:
            roles["Data Scientist"] += 1

        if s in ["DOCKER", "KUBERNETES", "GIT"]:
            roles["DevOps Engineer"] += 1

    return roles


def get_color(score):
    if score > 70:
        return "green-bar"
    elif score > 40:
        return "orange-bar"
    return "red-bar"


def generate_suggestions(skills):
    suggestions = []

    if "PYTHON" not in skills:
        suggestions.append("Add Python projects")
    if "AWS" not in skills:
        suggestions.append("Learn AWS")
    if "DOCKER" not in skills:
        suggestions.append("Learn Docker")
    if "KUBERNETES" not in skills:
        suggestions.append("Learn Kubernetes")

    if not suggestions:
        suggestions.append("Great resume!")

    return suggestions


def generate_portfolio(skills):
    summary = ""
    projects = []

    if "PYTHON" in skills:
        summary = "Aspiring Software Engineer with strong Python skills."
        projects.append("AI Resume Analyzer")
        projects.append("Automation Scripts")

    if "AWS" in skills:
        summary += " Cloud knowledge."
        projects.append("AWS Deployment")

    if summary == "":
        summary = "Beginner developer."

    return summary, projects


# ================= ROUTES =================
@app.route("/")
@login_required
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
@login_required
def upload():
    file = request.files.get("resume")

    if not file or file.filename == "":
        return "No file selected"

    path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(path)

    text = extract_text(path)

    name, email = extract_basic_info(text)
    skills = analyze_skills(text)
    score = calculate_score(skills)
    missing = missing_skills(skills)
    roles = analyze_roles(skills)
    color = get_color(score)
    suggestions = generate_suggestions(skills)
    summary, projects = generate_portfolio(skills)

    return render_template(
        "result.html",
        name=name,
        email=email,
        skills=skills,
        score=score,
        missing=missing,
        roles=roles,
        color=color,
        suggestions=suggestions,
        summary=summary,
        projects=projects
    )


@app.route("/portfolio")
@login_required
def portfolio():
    skills = request.args.get("skills", "").split(",")
    summary, projects = generate_portfolio(skills)

    return render_template(
        "portfolio.html",
        skills=skills,
        summary=summary,
        projects=projects
    )


# ================= RUN =================
if __name__ == "__main__":
    if not os.path.exists("uploads"):
        os.makedirs("uploads")

    with app.app_context():
        db.create_all()

    app.run(debug=True)
