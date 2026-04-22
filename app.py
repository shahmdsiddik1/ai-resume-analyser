import os
import re
from flask import Flask, render_template, request
import pdfplumber
import pytesseract
from PIL import Image

# ✅ Tesseract path (Windows)
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

        if s in ["DOCKER", "KUBERNETES", "GIT"]:
            roles["DevOps Engineer"] += 1

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

    if "GIT" not in skills:
        suggestions.append("Add Git & GitHub experience")

    if not suggestions:
        suggestions.append("Great resume! Add real-world projects.")

    return suggestions


# ================= PORTFOLIO GENERATOR =================
def generate_portfolio(skills):
    summary = ""
    projects = []

    if "PYTHON" in skills:
        summary = "Aspiring Software Engineer with strong Python skills and problem-solving ability."
        projects.append("AI Resume Analyzer (Flask + NLP)")
        projects.append("Automation Scripts using Python")

    if "AWS" in skills or "DOCKER" in skills:
        summary += " Experienced in Cloud and DevOps tools."
        projects.append("Cloud Deployment Project (AWS EC2 + Docker)")
        projects.append("CI/CD Pipeline using GitHub Actions")

    if "MACHINE LEARNING" in skills:
        summary += " Passionate about Machine Learning and Data Science."
        projects.append("ML Model for Prediction")
        projects.append("Data Analysis using Pandas & NumPy")

    if summary == "":
        summary = "Entry-level developer building strong foundations in programming."

    return summary, projects


# ================= ROUTES =================
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("resume")

    if not file or file.filename == "":
        return "❌ No file selected"

    path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(path)

    text = extract_text(path)

    print("\n========== EXTRACTED TEXT ==========\n")
    print(text[:500])
    print("\nTEXT LENGTH:", len(text))

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
def portfolio():
    name = request.args.get("name", "Your Name")
    email = request.args.get("email", "your@email.com")
    skills = request.args.get("skills", "")

    skills = skills.split(",") if skills else []

    summary, projects = generate_portfolio(skills)

    return render_template(
        "portfolio.html",
        name=name,
        email=email,
        skills=skills,
        summary=summary,
        projects=projects
    )
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


def create_pdf(name, email, skills, summary, projects):
    file_path = "portfolio.pdf"

    doc = SimpleDocTemplate(file_path)
    styles = getSampleStyleSheet()

    content = []

    content.append(Paragraph(f"<b>Name:</b> {name}", styles["Normal"]))
    content.append(Paragraph(f"<b>Email:</b> {email}", styles["Normal"]))
    content.append(Spacer(1, 10))

    content.append(Paragraph("<b>Skills:</b>", styles["Heading2"]))
    for s in skills:
        content.append(Paragraph(s, styles["Normal"]))

    content.append(Spacer(1, 10))

    content.append(Paragraph("<b>Summary:</b>", styles["Heading2"]))
    content.append(Paragraph(summary, styles["Normal"]))

    content.append(Spacer(1, 10))

    content.append(Paragraph("<b>Projects:</b>", styles["Heading2"]))
    for p in projects:
        content.append(Paragraph(p, styles["Normal"]))

    doc.build(content)

    return file_path


# ================= RUN =================
if __name__ == "__main__":
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    app.run(debug=True)
