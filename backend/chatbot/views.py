from django.shortcuts import render
from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import PyPDF2
from docx import Document

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

load_dotenv(os.path.join(BASE_DIR, ".env"))

api_key = os.getenv("OPENAI_API_KEY", "").strip()

client = OpenAI(api_key=api_key)

# Load roadmap and course data
with open(os.path.join(BASE_DIR, "..", "resources", "roadmaps.json")) as f:
    ROADMAPS = json.load(f)

with open(os.path.join(BASE_DIR, "..", "resources", "courses.json")) as f:
    COURSES = json.load(f)


def find_matching_career(question):
    question_lower = question.lower()
    for career in ROADMAPS.keys():
        if career.lower() in question_lower:
            return career
    return None


def extract_text_from_file(uploaded_file):
    if uploaded_file.name.endswith('.pdf'):
        reader = PyPDF2.PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    elif uploaded_file.name.endswith('.docx'):
        doc = Document(uploaded_file)
        return "\n".join([para.text for para in doc.paragraphs])
    return ""


def home(request):
    answer = None
    roadmap = None
    courses = None
    resume_feedback = None

    if request.method == "POST":
        if "analyze_resume" in request.POST:
            uploaded_file = request.FILES.get("resume_file")
            resume_text = extract_text_from_file(uploaded_file)

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional resume reviewer. Analyze the given resume text and provide clear, structured feedback: 1) Missing sections (if any), 2) Strengths, 3) Areas to improve, 4) Specific actionable suggestions. Be concise and practical."
                    },
                    {
                        "role": "user",
                        "content": resume_text
                    }
                ]
            )
            resume_feedback = response.choices[0].message.content

        else:
            question = request.POST.get("question")

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful career and study guidance assistant for students. Give clear practical advice."
                    },
                    {
                        "role": "user",
                        "content": question
                    }
                ]
            )
            answer = response.choices[0].message.content

            matched_career = find_matching_career(question)
            if matched_career:
                roadmap = ROADMAPS[matched_career]["steps"]
                courses = COURSES[matched_career]

    return render(request, "chatbot/home.html", {
        "answer": answer,
        "roadmap": roadmap,
        "courses": courses,
        "resume_feedback": resume_feedback
    })