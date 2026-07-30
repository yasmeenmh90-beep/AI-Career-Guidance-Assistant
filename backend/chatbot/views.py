from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login as auth_login
from django.views.decorators.http import require_POST
from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import math
import PyPDF2
import markdown
from docx import Document

from .models import ChatQuestion, ResumeReport, SkillGapReport, InterviewReport

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


# =========================================================
# Helpers
# =========================================================

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


def trail_progress_context(user):
    """Shared 'how much of the app has this user explored' data, used on every
    render of the home page regardless of which endpoint produced the result."""
    waypoints_done = sum([
        ChatQuestion.objects.filter(user=user).exists(),
        ResumeReport.objects.filter(user=user).exists(),
        SkillGapReport.objects.filter(user=user).exists(),
        InterviewReport.objects.filter(user=user).exists(),
    ])
    radius = 45
    circumference = 2 * math.pi * radius
    dash_offset = circumference * (1 - waypoints_done / 4)

    return {
        "waypoints_done": waypoints_done,
        "trail_progress_percent": int((waypoints_done / 4) * 100),
        "trail_circumference": round(circumference, 2),
        "trail_dash_offset": round(dash_offset, 2),
        "roles": list(ROADMAPS.keys()),
    }


def render_home(request, **extra_context):
    """Every endpoint below ends by calling this — it renders the same
    home.html template with whatever result that endpoint produced, plus
    the shared trail-progress context."""
    context = {
        "answer": None,
        "roadmap": None,
        "courses": None,
        "resume_feedback": None,
        "interview_question": None,
        "interview_feedback": None,
        "interview_role": None,
        "interview_progress": None,
        "skill_gap_feedback": None,
        "skill_gap_role": None,
    }
    context.update(trail_progress_context(request.user))
    context.update(extra_context)
    return render(request, "chatbot/home.html", context)


# =========================================================
# Auth
# =========================================================

def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect("home")
    else:
        form = UserCreationForm()
    return render(request, "chatbot/signup.html", {"form": form})


# =========================================================
# History / dashboard
# =========================================================

@login_required
def history(request):
    chat_count = ChatQuestion.objects.filter(user=request.user).count()
    resume_count = ResumeReport.objects.filter(user=request.user).count()
    skill_gap_count = SkillGapReport.objects.filter(user=request.user).count()
    interview_count = InterviewReport.objects.filter(user=request.user).count()

    max_count = max(chat_count, resume_count, skill_gap_count, interview_count, 1)

    chart_bars = [
        {"label": "Questions", "count": chat_count, "percent": int(chat_count / max_count * 100)},
        {"label": "Resumes", "count": resume_count, "percent": int(resume_count / max_count * 100)},
        {"label": "Skill Gaps", "count": skill_gap_count, "percent": int(skill_gap_count / max_count * 100)},
        {"label": "Interviews", "count": interview_count, "percent": int(interview_count / max_count * 100)},
    ]

    return render(request, "chatbot/history.html", {
        "chat_questions": request.user.chat_questions.all()[:20],
        "resume_reports": request.user.resume_reports.all()[:20],
        "skill_gap_reports": request.user.skill_gap_reports.all()[:20],
        "interview_reports": request.user.interview_reports.all()[:20],
        "chart_bars": chart_bars,
    })


# =========================================================
# Feature endpoints — one per action, REST-style
# =========================================================

@login_required
def home(request):
    """GET / — just shows the empty trail."""
    return render_home(request)


@login_required
@require_POST
def ask_question(request):
    """POST /ask/ — chatbot question + roadmap + courses."""
    question = request.POST.get("question")

    raw_answer = get_ai_response(
        "You are a helpful career and study guidance assistant for "
        "students. Give clear practical advice, formatted with "
        "markdown headings and bullet points where useful.",
        question
    )
    answer = to_html(raw_answer)

    roadmap = None
    courses = None
    matched_career = find_matching_career(question)
    if matched_career:
        roadmap = ROADMAPS[matched_career]["steps"]
        courses = COURSES[matched_career]

    ChatQuestion.objects.create(
        user=request.user,
        question=question,
        answer_html=answer,
        matched_career=matched_career,
    )

    return render_home(request, answer=answer, roadmap=roadmap, courses=courses)


@login_required
@require_POST
def analyze_resume(request):
    """POST /resume/ — resume upload + AI feedback."""
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

    ResumeReport.objects.create(
        user=request.user,
        filename=uploaded_file.name,
        feedback_html=resume_feedback,
    )

    return render_home(request, resume_feedback=resume_feedback)


@login_required
@require_POST
def analyze_skill_gap(request):
    """POST /skill-gap/ — resume + target role → gap report."""
    uploaded_file = request.FILES.get("skill_gap_resume")
    target_role = request.POST.get("skill_gap_role")
    resume_text = extract_text_from_file(uploaded_file)

    roadmap_steps = "\n".join(f"- {step}" for step in ROADMAPS[target_role]["steps"])

    system_prompt = (
        f"You are a career skills advisor. Below is the learning roadmap "
        f"for a {target_role} role:\n\n{roadmap_steps}\n\n"
        "Compare the candidate's resume text against this roadmap and "
        "provide structured feedback using markdown headings and bullet "
        "points: 1) Skills the candidate already has that match this "
        "role, 2) Skills/technologies from the roadmap that are missing "
        "from the resume, 3) A prioritised list of 3-5 skills they "
        "should focus on learning next, with a short reason for each. "
        "Be specific and reference the roadmap directly."
    )
    raw_feedback = get_ai_response(system_prompt, resume_text)
    skill_gap_feedback = to_html(raw_feedback)

    SkillGapReport.objects.create(
        user=request.user,
        target_role=target_role,
        feedback_html=skill_gap_feedback,
    )

    return render_home(request, skill_gap_feedback=skill_gap_feedback, skill_gap_role=target_role)


@login_required
@require_POST
def start_interview(request):
    """POST /interview/start/ — begins a new mock interview."""
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

    return render_home(
        request,
        interview_question=question,
        interview_role=role,
        interview_progress=f"Question 1 of {INTERVIEW_LENGTH}",
    )


@login_required
@require_POST
def submit_interview_answer(request):
    """POST /interview/answer/ — records an answer, asks the next question
    or (on the final question) returns the full feedback report."""
    user_answer = request.POST.get("interview_answer", "")
    role = request.session.get("interview_role")
    history_data = request.session.get("interview_history", [])

    if history_data:
        history_data[-1]["answer"] = user_answer

    if role and len(history_data) < INTERVIEW_LENGTH:
        qa_summary = "\n".join(
            f"Q: {h['question']}\nA: {h['answer']}" for h in history_data
        )
        system_prompt = (
            f"You are conducting a mock interview for a {role} position. "
            "Based on the conversation so far, ask the next relevant "
            "interview question. Reply with just the question — no "
            "extra text, no markdown."
        )
        next_question = get_ai_response(system_prompt, qa_summary)

        history_data.append({"question": next_question, "answer": None})
        request.session["interview_history"] = history_data

        return render_home(
            request,
            interview_question=next_question,
            interview_role=role,
            interview_progress=f"Question {len(history_data)} of {INTERVIEW_LENGTH}",
        )

    elif role:
        qa_summary = "\n".join(
            f"Q: {h['question']}\nA: {h['answer']}" for h in history_data
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

        InterviewReport.objects.create(
            user=request.user,
            role=role,
            feedback_html=interview_feedback,
        )

        request.session["interview_role"] = None
        request.session["interview_history"] = []

        return render_home(request, interview_feedback=interview_feedback)

    return render_home(request)