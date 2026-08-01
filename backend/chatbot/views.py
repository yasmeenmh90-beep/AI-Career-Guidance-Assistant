from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login as auth_login
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from openai import OpenAI
from dotenv import load_dotenv
import os
import io
import json
import math
import PyPDF2
import markdown
from bs4 import BeautifulSoup
from docx import Document
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem

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
    """Returns extracted text, or None if the file couldn't be read at all."""
    try:
        if uploaded_file.name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(uploaded_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text
        elif uploaded_file.name.endswith('.docx'):
            doc = Document(uploaded_file)
            return "\n".join([para.text for para in doc.paragraphs])
        return ""
    except Exception:
        return None


def get_ai_response(system_prompt, user_content):
    """Centralised helper for calling OpenAI so we don't repeat this everywhere.
    Returns None on any failure (rate limit, network error, bad key, etc.) so
    callers can show a friendly message instead of a 500 page."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]
        )
        return response.choices[0].message.content
    except Exception:
        return None


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


def render_home(request, fresh_load=False, **extra_context):
    """Every endpoint below ends by calling this — it renders the same
    home.html template with whatever result that endpoint produced, plus
    the shared trail-progress context.

    Each waypoint's last result is cached in the session, so asking a
    question and then analyzing a resume doesn't wipe the chat answer off
    the page — every section keeps showing its own most recent result,
    for the rest of that back-and-forth.

    fresh_load=True is for a plain page visit (GET /) — it deliberately
    ignores the session cache so a page you just opened starts empty,
    instead of showing whatever you last asked in an earlier visit."""
    session = request.session

    if fresh_load:
        # Wipe the cached results themselves, not just what's shown — otherwise
        # the next POST (e.g. asking a fresh question) would pull in stale
        # results from a waypoint nobody touched this visit.
        for key in (
            "last_answer", "last_asked_question", "last_roadmap", "last_courses",
            "last_resume_feedback", "last_skill_gap_feedback", "last_skill_gap_role",
            "last_interview_feedback",
        ):
            session.pop(key, None)

        context = {
            "answer": None,
            "asked_question": None,
            "roadmap": None,
            "courses": None,
            "resume_feedback": None,
            "interview_question": None,
            "interview_feedback": None,
            "interview_role": None,
            "interview_progress": None,
            "skill_gap_feedback": None,
            "skill_gap_role": None,
            "answer_error": None,
            "resume_error": None,
            "skill_gap_error": None,
            "interview_error": None,
            "active_waypoint": None,
        }
    else:
        context = {
            "answer": session.get("last_answer"),
            "asked_question": session.get("last_asked_question"),
            "roadmap": session.get("last_roadmap"),
            "courses": session.get("last_courses"),
            "resume_feedback": session.get("last_resume_feedback"),
            "interview_question": None,
            "interview_feedback": session.get("last_interview_feedback"),
            "interview_role": None,
            "interview_progress": None,
            "skill_gap_feedback": session.get("last_skill_gap_feedback"),
            "skill_gap_role": session.get("last_skill_gap_role"),
            "answer_error": None,
            "resume_error": None,
            "skill_gap_error": None,
            "interview_error": None,
            "active_waypoint": None,
        }
    context.update(trail_progress_context(request.user))
    context.update(extra_context)

    if "answer" in extra_context:
        session["last_answer"] = extra_context.get("answer")
        session["last_asked_question"] = extra_context.get("asked_question")
        session["last_roadmap"] = extra_context.get("roadmap")
        session["last_courses"] = extra_context.get("courses")
    if "resume_feedback" in extra_context:
        session["last_resume_feedback"] = extra_context.get("resume_feedback")
    if "skill_gap_feedback" in extra_context:
        session["last_skill_gap_feedback"] = extra_context.get("skill_gap_feedback")
        session["last_skill_gap_role"] = extra_context.get("skill_gap_role")
    if "interview_feedback" in extra_context:
        session["last_interview_feedback"] = extra_context.get("interview_feedback")

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
    skill_gap_reports_qs = SkillGapReport.objects.filter(user=request.user)
    skill_gap_count = skill_gap_reports_qs.count()
    interview_count = InterviewReport.objects.filter(user=request.user).count()

    total_activity = chat_count + resume_count + skill_gap_count + interview_count

    # ---------- Activity Breakdown as a donut chart ----------
    # Same "stacked circle" trick as the trail-progress ring on the home page,
    # just with 4 segments instead of 1 — keeps the visual language consistent.
    donut_radius = 46
    donut_circumference = round(2 * math.pi * donut_radius, 2)

    raw_bars = [
        {"label": "Questions", "count": chat_count, "color": "var(--blaze)"},
        {"label": "Resumes", "count": resume_count, "color": "var(--focus)"},
        {"label": "Skill Gaps", "count": skill_gap_count, "color": "var(--pine)"},
        {"label": "Interviews", "count": interview_count, "color": "var(--moss)"},
    ]

    donut_segments = []
    cumulative_length = 0.0
    for bar in raw_bars:
        fraction = (bar["count"] / total_activity) if total_activity else 0
        length = round(fraction * donut_circumference, 2)
        donut_segments.append({
            "label": bar["label"],
            "count": bar["count"],
            "color": bar["color"],
            "percent": round(fraction * 100),
            "dasharray": f"{length} {round(donut_circumference - length, 2)}",
            "dashoffset": round(-cumulative_length, 2),
        })
        cumulative_length += length

    # ---------- Skill-gap trends: which skills keep coming up as missing ----------
    skill_counts = {}
    for report in skill_gap_reports_qs:
        for skill in report.missing_skills.split(","):
            skill = skill.strip()
            if not skill:
                continue
            skill_counts[skill] = skill_counts.get(skill, 0) + 1

    top_skills = sorted(skill_counts.items(), key=lambda pair: pair[1], reverse=True)[:6]
    max_skill_count = max([count for _, count in top_skills], default=1)
    skill_trend_rows = [
        {
            "rank": i + 1,
            "label": skill,
            "count": count,
            "dots": list(range(min(count, 5))),
            "empty_dots": list(range(max(0, 5 - count))) if count < 5 else [],
            "percent": int(count / max_skill_count * 100),
        }
        for i, (skill, count) in enumerate(top_skills)
    ]

    return render(request, "chatbot/history.html", {
        "chat_questions": request.user.chat_questions.all()[:20],
        "resume_reports": request.user.resume_reports.all()[:20],
        "skill_gap_reports": skill_gap_reports_qs[:20],
        "interview_reports": request.user.interview_reports.all()[:20],
        "total_activity": total_activity,
        "donut_segments": donut_segments,
        "donut_radius": donut_radius,
        "donut_circumference": donut_circumference,
        "skill_trend_rows": skill_trend_rows,
    })


# =========================================================
# Feature endpoints — one per action, REST-style
# =========================================================

@login_required
def home(request):
    """GET / — just shows the empty trail."""
    return render_home(request, fresh_load=True)


@login_required
@require_POST
def ask_question(request):
    """POST /ask/ — chatbot question + roadmap + courses."""
    question = request.POST.get("question", "").strip()

    if not question:
        return render_home(request, answer_error="Type a question before hitting Ask.", active_waypoint="waypoint-01")

    raw_answer = get_ai_response(
        "You are a helpful career and study guidance assistant for "
        "students. Give clear practical advice, formatted with "
        "markdown headings and bullet points where useful.",
        question
    )

    if raw_answer is None:
        return render_home(request, answer_error="Couldn't reach the AI just now — please try again in a moment.", active_waypoint="waypoint-01")

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

    return render_home(request, answer=answer, roadmap=roadmap, courses=courses, asked_question=question, active_waypoint="waypoint-01")


@login_required
@require_POST
def analyze_resume(request):
    """POST /resume/ — resume upload + AI feedback."""
    uploaded_file = request.FILES.get("resume_file")

    if not uploaded_file:
        return render_home(request, resume_error="Choose a PDF or DOCX file before analyzing.", active_waypoint="waypoint-02")

    resume_text = extract_text_from_file(uploaded_file)

    if resume_text is None:
        return render_home(request, resume_error="Couldn't read that file — make sure it's a valid PDF or DOCX.", active_waypoint="waypoint-02")
    if not resume_text.strip():
        return render_home(request, resume_error="That file looks empty — try a different resume.", active_waypoint="waypoint-02")

    raw_feedback = get_ai_response(
        "You are a professional resume reviewer. Analyze the given resume "
        "text and provide clear, structured feedback using markdown "
        "headings and bullet points: 1) Missing sections (if any), "
        "2) Strengths, 3) Areas to improve, 4) Specific actionable "
        "suggestions. Be concise and practical.",
        resume_text
    )

    if raw_feedback is None:
        return render_home(request, resume_error="Couldn't reach the AI just now — please try again in a moment.", active_waypoint="waypoint-02")

    resume_feedback = to_html(raw_feedback)

    ResumeReport.objects.create(
        user=request.user,
        filename=uploaded_file.name,
        feedback_html=resume_feedback,
    )

    return render_home(request, resume_feedback=resume_feedback, active_waypoint="waypoint-02")


@login_required
@require_POST
def analyze_skill_gap(request):
    """POST /skill-gap/ — resume + target role → gap report."""
    uploaded_file = request.FILES.get("skill_gap_resume")
    target_role = request.POST.get("skill_gap_role")

    if not uploaded_file:
        return render_home(request, skill_gap_error="Choose a PDF or DOCX file before checking your skill gap.", active_waypoint="waypoint-03")
    if not target_role or target_role not in ROADMAPS:
        return render_home(request, skill_gap_error="Pick a valid target role first.", active_waypoint="waypoint-03")

    resume_text = extract_text_from_file(uploaded_file)

    if resume_text is None:
        return render_home(request, skill_gap_error="Couldn't read that file — make sure it's a valid PDF or DOCX.", active_waypoint="waypoint-03")
    if not resume_text.strip():
        return render_home(request, skill_gap_error="That file looks empty — try a different resume.", active_waypoint="waypoint-03")

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
        "Be specific and reference the roadmap directly.\n\n"
        "After the full report, add exactly one final line with no "
        "markdown, no bullets, in this exact format:\n"
        "MISSING_SKILLS: skill one, skill two, skill three\n"
        "List 3-6 short skill or technology names (not sentences) that "
        "are missing, matching how they're named in the roadmap. This "
        "must be the very last line of your response."
    )
    raw_feedback = get_ai_response(system_prompt, resume_text)

    if raw_feedback is None:
        return render_home(request, skill_gap_error="Couldn't reach the AI just now — please try again in a moment.", active_waypoint="waypoint-03")

    # Pull the machine-readable MISSING_SKILLS line out before rendering —
    # it's for the trend chart, not something the user needs to see.
    missing_skills = ""
    lines = raw_feedback.strip().split("\n")
    if lines and lines[-1].strip().upper().startswith("MISSING_SKILLS:"):
        missing_skills = lines[-1].split(":", 1)[1].strip()
        raw_feedback = "\n".join(lines[:-1]).strip()

    skill_gap_feedback = to_html(raw_feedback)

    SkillGapReport.objects.create(
        user=request.user,
        target_role=target_role,
        feedback_html=skill_gap_feedback,
        missing_skills=missing_skills,
    )

    return render_home(request, skill_gap_feedback=skill_gap_feedback, skill_gap_role=target_role, active_waypoint="waypoint-03")


@login_required
@require_POST
def start_interview(request):
    """POST /interview/start/ — begins a new mock interview."""
    role = request.POST.get("interview_role")

    if not role or role not in ROADMAPS:
        return render_home(request, interview_error="Pick a valid role first.", active_waypoint="waypoint-04")

    system_prompt = (
        f"You are conducting a mock interview for a {role} position. "
        "Ask one relevant, realistic interview question. "
        "Reply with just the question — no extra text, no markdown."
    )
    question = get_ai_response(system_prompt, "Ask the first interview question.")

    if question is None:
        return render_home(request, interview_error="Couldn't reach the AI just now — please try again in a moment.", active_waypoint="waypoint-04")

    request.session["interview_role"] = role
    request.session["interview_history"] = [
        {"question": question, "answer": None}
    ]

    return render_home(
        request,
        interview_question=question,
        interview_role=role,
        interview_progress=f"Question 1 of {INTERVIEW_LENGTH}",
        active_waypoint="waypoint-04",
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

        if next_question is None:
            return render_home(request, interview_error="Couldn't reach the AI just now — please try again in a moment.", active_waypoint="waypoint-04")

        history_data.append({"question": next_question, "answer": None})
        request.session["interview_history"] = history_data

        return render_home(
            request,
            interview_question=next_question,
            interview_role=role,
            interview_progress=f"Question {len(history_data)} of {INTERVIEW_LENGTH}",
            active_waypoint="waypoint-04",
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

        if raw_feedback is None:
            return render_home(request, interview_error="Couldn't reach the AI just now — please try again in a moment.", active_waypoint="waypoint-04")

        interview_feedback = to_html(raw_feedback)

        InterviewReport.objects.create(
            user=request.user,
            role=role,
            feedback_html=interview_feedback,
        )

        request.session["interview_role"] = None
        request.session["interview_history"] = []

        return render_home(request, interview_feedback=interview_feedback, active_waypoint="waypoint-04")

    return render_home(request)


# =========================================================
# PDF export — download resume/interview feedback as PDF
# =========================================================

PINE = colors.HexColor("#2F4B3C")
BLAZE = colors.HexColor("#E2632A")
MOSS = colors.HexColor("#7C9083")
INK = colors.HexColor("#1E2B22")


def _pdf_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="TMEyebrow", fontSize=9, leading=11, textColor=BLAZE,
        fontName="Helvetica-Bold", spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="TMTitle", fontSize=20, leading=24, textColor=PINE,
        fontName="Helvetica-Bold", spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="TMSub", fontSize=10, leading=14, textColor=MOSS,
        fontName="Helvetica", spaceAfter=20,
    ))
    styles.add(ParagraphStyle(
        name="TMHeading", fontSize=13, leading=17, textColor=PINE,
        fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="TMBody", fontSize=10.5, leading=15, textColor=INK,
        fontName="Helvetica", spaceAfter=6,
    ))
    return styles


def _clean_inline(html_fragment):
    """reportlab's Paragraph only understands a handful of tags — swap the
    ones markdown.markdown() produces for reportlab-friendly equivalents."""
    return (
        (html_fragment or "")
        .replace("<strong>", "<b>").replace("</strong>", "</b>")
        .replace("<em>", "<i>").replace("</em>", "</i>")
        .replace("<code>", "<font face='Courier'>").replace("</code>", "</font>")
    )


def _html_to_flowables(html, styles):
    """Walks the stored feedback HTML and turns it into reportlab flowables,
    so the PDF keeps the same headings/bold/bullets the web page shows."""
    soup = BeautifulSoup(html or "", "html.parser")
    flowables = []

    for el in soup.find_all(["h1", "h2", "h3", "h4", "p", "ul", "ol", "hr"], recursive=False):
        if el.name in ("h1", "h2", "h3", "h4"):
            flowables.append(Paragraph(el.get_text(), styles["TMHeading"]))
        elif el.name == "p":
            flowables.append(Paragraph(_clean_inline(el.decode_contents()), styles["TMBody"]))
        elif el.name in ("ul", "ol"):
            items = []
            for li in el.find_all("li", recursive=False):
                items.append(ListItem(
                    Paragraph(_clean_inline(li.decode_contents()), styles["TMBody"]),
                    bulletColor=BLAZE,
                ))
            flowables.append(ListFlowable(
                items,
                bulletType="bullet" if el.name == "ul" else "1",
                leftIndent=16,
            ))
        elif el.name == "hr":
            flowables.append(Spacer(1, 10))

    return flowables


def _build_pdf_response(filename, title, subtitle, html_body):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=LETTER,
        topMargin=0.85 * inch, bottomMargin=0.85 * inch,
        leftMargin=0.9 * inch, rightMargin=0.9 * inch,
    )
    styles = _pdf_styles()

    story = [
        Paragraph("TRAILMARK", styles["TMEyebrow"]),
        Paragraph(title, styles["TMTitle"]),
        Paragraph(subtitle, styles["TMSub"]),
    ]
    story.extend(_html_to_flowables(html_body, styles))

    doc.build(story)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@login_required
def download_resume_pdf(request, report_id):
    report = get_object_or_404(ResumeReport, id=report_id, user=request.user)
    subtitle = f"{report.filename} &nbsp;&mdash;&nbsp; {report.created_at.strftime('%d %b %Y, %H:%M')}"
    return _build_pdf_response(
        f"resume-feedback-{report.id}.pdf",
        "Resume Feedback Report",
        subtitle,
        report.feedback_html,
    )


@login_required
def download_interview_pdf(request, report_id):
    report = get_object_or_404(InterviewReport, id=report_id, user=request.user)
    subtitle = f"{report.role} &nbsp;&mdash;&nbsp; {report.created_at.strftime('%d %b %Y, %H:%M')}"
    return _build_pdf_response(
        f"interview-feedback-{report.id}.pdf",
        "Interview Feedback Report",
        subtitle,
        report.feedback_html,
    )


@login_required
def download_skill_gap_pdf(request, report_id):
    report = get_object_or_404(SkillGapReport, id=report_id, user=request.user)
    subtitle = f"{report.target_role} &nbsp;&mdash;&nbsp; {report.created_at.strftime('%d %b %Y, %H:%M')}"
    return _build_pdf_response(
        f"skill-gap-{report.id}.pdf",
        "Skill Gap Report",
        subtitle,
        report.feedback_html,
    )