from django.shortcuts import render
from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import PyPDF2
import markdown
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

INTERVIEW_LENGTH = 5  # number of questions per mock interview


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


def get_ai_response(system_prompt, user_content):
    """Centralised helper for calling OpenAI so we don't repeat this everywhere."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
    )
    return response.choices[0].message.content


def to_html(markdown_text):
    """Converts the AI's markdown-formatted reply into clean HTML for display."""
    if not markdown_text:
        return None
    return markdown.markdown(markdown_text, extensions=["extra", "sane_lists"])


def home(request):
    answer = None
    roadmap = None
    courses = None
    resume_feedback = None

    interview_question = None
    interview_feedback = None
    interview_role = None
    interview_progress = None

    if request.method == "POST":

        # ---------- Resume Analysis ----------
        if "analyze_resume" in request.POST:
            uploaded_file = request.FILES.get("resume_file")
            resume_text = extract_text_from_file(uploaded_file)

            raw_feedback = get_ai_response(
                "You are a professional resume reviewer. Analyze the given resume "
                "text and provide clear, structured feedback using markdown "
                "headings and bullet points: 1) Missing sections (if any), "
                "2) Strengths, 3) Areas to improve, 4) Specific actionable "
                "suggestions. Be concise and practical.",
                resume_text
            )
            resume_feedback = to_html(raw_feedback)

        # ---------- Start Interview ----------
        elif "start_interview" in request.POST:
            role = request.POST.get("interview_role")

            system_prompt = (
                f"You are conducting a mock interview for a {role} position. "
                "Ask one relevant, realistic interview question. "
                "Reply with just the question — no extra text, no markdown."
            )
            question = get_ai_response(system_prompt, "Ask the first interview question.")

            request.session["interview_role"] = role
            request.session["interview_history"] = [
                {"question": question, "answer": None}
            ]

            interview_question = question
            interview_role = role
            interview_progress = f"Question 1 of {INTERVIEW_LENGTH}"

        # ---------- Submit Answer / Continue Interview ----------
        elif "interview_answer" in request.POST:
            user_answer = request.POST.get("interview_answer", "")
            role = request.session.get("interview_role")
            history = request.session.get("interview_history", [])

            if history:
                history[-1]["answer"] = user_answer

            if role and len(history) < INTERVIEW_LENGTH:
                qa_summary = "\n".join(
                    f"Q: {h['question']}\nA: {h['answer']}" for h in history
                )
                system_prompt = (
                    f"You are conducting a mock interview for a {role} position. "
                    "Based on the conversation so far, ask the next relevant "
                    "interview question. Reply with just the question — no "
                    "extra text, no markdown."
                )
                next_question = get_ai_response(system_prompt, qa_summary)

                history.append({"question": next_question, "answer": None})
                request.session["interview_history"] = history

                interview_question = next_question
                interview_role = role
                interview_progress = f"Question {len(history)} of {INTERVIEW_LENGTH}"

            elif role:
                qa_summary = "\n".join(
                    f"Q: {h['question']}\nA: {h['answer']}" for h in history
                )
                system_prompt = (
                    f"You just conducted a mock interview for a {role} position. "
                    "Review the candidate's answers below and give constructive "
                    "feedback using markdown headings and bullet points: "
                    "1) Overall impression, 2) Strengths, 3) Areas to improve, "
                    "4) One practical tip for their next real interview. "
                    "Be encouraging but honest."
                )
                raw_feedback = get_ai_response(system_prompt, qa_summary)
                interview_feedback = to_html(raw_feedback)

                # reset interview state
                request.session["interview_role"] = None
                request.session["interview_history"] = []

        # ---------- Regular Chatbot Question ----------
        else:
            question = request.POST.get("question")

            raw_answer = get_ai_response(
                "You are a helpful career and study guidance assistant for "
                "students. Give clear practical advice, formatted with "
                "markdown headings and bullet points where useful.",
                question
            )
            answer = to_html(raw_answer)

            matched_career = find_matching_career(question)
            if matched_career:
                roadmap = ROADMAPS[matched_career]["steps"]
                courses = COURSES[matched_career]

    return render(request, "chatbot/home.html", {
        "answer": answer,
        "roadmap": roadmap,
        "courses": courses,
        "resume_feedback": resume_feedback,
        "interview_question": interview_question,
        "interview_feedback": interview_feedback,
        "interview_role": interview_role,
        "interview_progress": interview_progress,
        "roles": list(ROADMAPS.keys()),
    })