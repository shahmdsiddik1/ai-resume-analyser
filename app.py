import os
import re
from flask import Flask, render_template, request
import pdfplumber
import pytesseract
from PIL import Image

# Tesseract path (Windows)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


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


# ================= BASIC INFO =================
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


# ================= SKILLS =================
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


# ================= SCORE =================
def calculate_score(skills):
    if "No skills detected" in skills:
        return 5.0
    return round((len(skills) / 15) * 100, 2)


# ================= MISSING =================
def missing_skills(found):
    important = ["PYTHON", "AWS", "DOCKER", "KUBERNETES", "GIT"]
    return [s for s in important if s not in found]


# ================= ROLES =================
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

    return roles


# ================= COLOR =================
def get_color(score):
    if score > 70:
        return "green-bar"
    elif score > 40:
        return "orange-bar"
    return "red-bar"


# ================= SUGGESTIONS =================
def generate_suggestions(skills):
    suggestions = []

    if "PYTHON" not in skills:
        suggestions.append("Add Python projects")
    if "AWS" not in skills:
        suggestions.append("Learn AWS (important for Cloud)")
    if "DOCKER" not in skills:
        suggestions.append("Learn Docker")
    if "KUBERNETES" not in skills:
        suggestions.append("Learn Kubernetes")

    if not suggestions:
        suggestions.append("Great resume!")

    return suggestions


# ================= ROUTES =================
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
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

    return render_template(
        "result.html",
        name=name,
        email=email,
        skills=skills,
        score=score,
        missing=missing,
        roles=roles,
        color=color,
        suggestions=suggestions
    )


@app.route("/portfolio")
def portfolio():
    name = request.args.get("name")
    email = request.args.get("email")
    skills = request.args.get("skills")

    skills = skills.split(",") if skills else []

    return render_template(
        "portfolio.html",
        name=name,
        email=email,
        skills=skills
    )


# ================= RUN =================
if __name__ == "__main__":
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    app.run(debug=True)