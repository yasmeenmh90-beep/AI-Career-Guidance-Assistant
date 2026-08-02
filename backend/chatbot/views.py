from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login as auth_login
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django_ratelimit.decorators import ratelimit
from asgiref.sync import sync_to_async
from openai import AsyncOpenAI
from pydantic import BaseModel
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
from django.template.loader import render_to_string
from xhtml2pdf import pisa

from .models import ChatQuestion, ResumeReport, SkillGapReport, InterviewReport, CareerPath, RoadmapStep, Course

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

load_dotenv(os.path.join(BASE_DIR, ".env"))

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", "").strip())



INTERVIEW_LENGTH = 5  # number of questions per mock interview


# =========================================================
# Helpers
# =========================================================

async def find_matching_career(question):
    question_lower = question.lower()
    careers = await sync_to_async(lambda: list(CareerPath.objects.values_list('name', flat=True)))()
    for career in careers:
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


async def get_ai_response(system_prompt, user_content, response_format=None):
    """Centralised helper for calling OpenAI so we don't repeat this everywhere.
    Returns None on any failure (rate limit, network error, bad key, etc.) so
    callers can show a friendly message instead of a 500 page."""
    try:
        if response_format:
            response = await client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                response_format=response_format
            )
            return response.choices[0].message.parsed
        else:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ]
            )
            return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI API Error: {e}")
        return None


def to_html(markdown_text):
    """Converts the AI's markdown-formatted reply into clean HTML for display."""
    if not markdown_text:
        return None
    return markdown.markdown(markdown_text, extensions=["extra", "sane_lists"])


def trail_progress_context(session):
    """Shared 'how much of the trail have you explored this visit' data, used
    on every render of the home page. Based on the session-cached results —
    the same ones the page is currently showing — not all-time history, so
    the ring matches what the page actually looks like right now."""
    waypoints_done = sum([
        bool(session.get("last_answer")),
        bool(session.get("last_resume_feedback")),
        bool(session.get("last_skill_gap_feedback")),
        bool(session.get("last_interview_feedback")),
    ])
    radius = 45
    circumference = 2 * math.pi * radius
    dash_offset = circumference * (1 - waypoints_done / 4)

    return {
        "waypoints_done": waypoints_done,
        "trail_progress_percent": int((waypoints_done / 4) * 100),
        "trail_circumference": round(circumference, 2),
        "trail_dash_offset": round(dash_offset, 2),
        "roles": list(CareerPath.objects.values_list('name', flat=True)),
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
            "saved_resume_filename": None,
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
            "saved_resume_filename": session.get("saved_resume_filename"),
        }
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

    # Compute the progress ring after the session's been updated with
    # whatever this request just produced, so a fresh answer counts
    # immediately instead of lagging a request behind.
    context.update(trail_progress_context(session))

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
@ratelimit(key='user_or_ip', rate='10/m', block=False)
async def ask_question(request):
    """POST /ask/ — chatbot question + roadmap + courses."""
    if getattr(request, 'limited', False):
        return await sync_to_async(render_home)(request, answer_error="You're asking questions too quickly. Please wait a moment.", active_waypoint="waypoint-01")
    question = request.POST.get("question", "").strip()

    if not question:
        return await sync_to_async(render_home)(request, answer_error="Type a question before hitting Ask.", active_waypoint="waypoint-01")

    raw_answer = await get_ai_response(
        "You are a helpful career and study guidance assistant for "
        "students. Give clear practical advice, formatted with "
        "markdown headings and bullet points where useful.",
        question
    )

    if raw_answer is None:
        return await sync_to_async(render_home)(request, answer_error="Couldn't reach the AI just now — please try again in a moment.", active_waypoint="waypoint-01")

    answer = to_html(raw_answer)

    roadmap = None
    courses = None
    matched_career = await find_matching_career(question)
    if matched_career:
        roadmap = await sync_to_async(lambda: list(RoadmapStep.objects.filter(career_path__name=matched_career).values_list('step_text', flat=True)))()
        courses = await sync_to_async(lambda: list(Course.objects.filter(career_path__name=matched_career).values('name', 'platform', 'link')))()

    await sync_to_async(ChatQuestion.objects.create)(
        user=request.user,
        question=question,
        answer_html=answer,
        matched_career=matched_career,
    )

    return await sync_to_async(render_home)(request, answer=answer, roadmap=roadmap, courses=courses, asked_question=question, active_waypoint="waypoint-01")


@login_required
@require_POST
@ratelimit(key='user_or_ip', rate='5/m', block=False)
async def analyze_resume(request):
    """POST /resume/ — resume upload + AI feedback."""
    if getattr(request, 'limited', False):
        return await sync_to_async(render_home)(request, resume_error="You're analyzing resumes too quickly. Please wait a moment.", active_waypoint="waypoint-02")
    uploaded_file = request.FILES.get("resume_file")

    if not uploaded_file:
        return await sync_to_async(render_home)(request, resume_error="Choose a PDF or DOCX file before analyzing.", active_waypoint="waypoint-02")

    resume_text = extract_text_from_file(uploaded_file)

    if resume_text is None:
        return await sync_to_async(render_home)(request, resume_error="Couldn't read that file — make sure it's a valid PDF or DOCX.", active_waypoint="waypoint-02")
    if not resume_text.strip():
        return await sync_to_async(render_home)(request, resume_error="That file looks empty — try a different resume.", active_waypoint="waypoint-02")

    request.session["saved_resume_text"] = resume_text
    request.session["saved_resume_filename"] = uploaded_file.name

    raw_feedback = await get_ai_response(
        "You are a professional resume reviewer. Analyze the given resume "
        "text and provide clear, structured feedback using markdown "
        "headings and bullet points: 1) Missing sections (if any), "
        "2) Strengths, 3) Areas to improve, 4) Specific actionable "
        "suggestions. Be concise and practical.",
        resume_text
    )

    if raw_feedback is None:
        return await sync_to_async(render_home)(request, resume_error="Couldn't reach the AI just now — please try again in a moment.", active_waypoint="waypoint-02")

    resume_feedback = to_html(raw_feedback)

    await sync_to_async(ResumeReport.objects.create)(
        user=request.user,
        filename=uploaded_file.name,
        feedback_html=resume_feedback,
    )

    return await sync_to_async(render_home)(request, resume_feedback=resume_feedback, active_waypoint="waypoint-02")


class SkillGapResponse(BaseModel):
    feedback_markdown: str
    missing_skills: list[str]


@login_required
@require_POST
@ratelimit(key='user_or_ip', rate='5/m', block=False)
async def analyze_skill_gap(request):
    """POST /skill-gap/ — resume + target role → gap report."""
    if getattr(request, 'limited', False):
        return await sync_to_async(render_home)(request, skill_gap_error="You're checking skill gaps too quickly. Please wait a moment.", active_waypoint="waypoint-03")
    uploaded_file = request.FILES.get("skill_gap_resume")
    target_role = request.POST.get("skill_gap_role")

    if uploaded_file:
        resume_text = extract_text_from_file(uploaded_file)
        if resume_text is None:
            return await sync_to_async(render_home)(request, skill_gap_error="Couldn't read that file — make sure it's a valid PDF or DOCX.", active_waypoint="waypoint-03")
        if not resume_text.strip():
            return await sync_to_async(render_home)(request, skill_gap_error="That file looks empty — try a different resume.", active_waypoint="waypoint-03")
        
        request.session["saved_resume_text"] = resume_text
        request.session["saved_resume_filename"] = uploaded_file.name
    else:
        resume_text = request.session.get("saved_resume_text")
        if not resume_text:
            return await sync_to_async(render_home)(request, skill_gap_error="Choose a PDF or DOCX file before checking your skill gap.", active_waypoint="waypoint-03")

    valid_roles = await sync_to_async(lambda: list(CareerPath.objects.values_list('name', flat=True)))()
    if not target_role or target_role not in valid_roles:
        return await sync_to_async(render_home)(request, skill_gap_error="Pick a valid target role first.", active_waypoint="waypoint-03")

    steps = await sync_to_async(lambda: list(RoadmapStep.objects.filter(career_path__name=target_role).values_list('step_text', flat=True)))()
    roadmap_steps = "\n".join(f"- {step}" for step in steps)

    system_prompt = (
        f"You are a career skills advisor. Below is the learning roadmap "
        f"for a {target_role} role:\n\n{roadmap_steps}\n\n"
        "Compare the candidate's resume text against this roadmap and "
        "provide structured feedback. For 'feedback_markdown', use markdown "
        "headings and bullet points: 1) Skills the candidate already has "
        "that match this role, 2) Skills/technologies from the roadmap "
        "that are missing from the resume, 3) A prioritised list of 3-5 "
        "skills they should focus on learning next, with a short reason "
        "for each. Be specific and reference the roadmap directly.\n\n"
        "For 'missing_skills', provide a list of 3-6 short skill or "
        "technology names (not sentences) that are missing, matching how "
        "they're named in the roadmap."
    )
    parsed_response = await get_ai_response(system_prompt, resume_text, response_format=SkillGapResponse)

    if parsed_response is None:
        return await sync_to_async(render_home)(request, skill_gap_error="Couldn't reach the AI just now — please try again in a moment.", active_waypoint="waypoint-03")

    missing_skills = ", ".join(parsed_response.missing_skills)
    skill_gap_feedback = to_html(parsed_response.feedback_markdown)

    await sync_to_async(SkillGapReport.objects.create)(
        user=request.user,
        target_role=target_role,
        feedback_html=skill_gap_feedback,
        missing_skills=missing_skills,
    )

    return await sync_to_async(render_home)(request, skill_gap_feedback=skill_gap_feedback, skill_gap_role=target_role, active_waypoint="waypoint-03")


@login_required
@require_POST
@ratelimit(key='user_or_ip', rate='5/m', block=False)
async def start_interview(request):
    """POST /interview/start/ — begins a new mock interview."""
    if getattr(request, 'limited', False):
        return await sync_to_async(render_home)(request, interview_error="You're starting interviews too quickly. Please wait a moment.", active_waypoint="waypoint-04")

    role = request.POST.get("interview_role")

    valid_roles = await sync_to_async(lambda: list(CareerPath.objects.values_list('name', flat=True)))()
    if not role or role not in valid_roles:
        return await sync_to_async(render_home)(request, interview_error="Pick a valid role first.", active_waypoint="waypoint-04")

    system_prompt = (
        f"You are conducting a mock interview for a {role} position. "
        "Ask one relevant, realistic interview question. "
        "Reply with just the question — no extra text, no markdown."
    )
    question = await get_ai_response(system_prompt, "Ask the first interview question.")

    if question is None:
        return await sync_to_async(render_home)(request, interview_error="Couldn't reach the AI just now — please try again in a moment.", active_waypoint="waypoint-04")

    request.session["interview_role"] = role
    request.session["interview_history"] = [
        {"question": question, "answer": None}
    ]

    return await sync_to_async(render_home)(
        request,
        interview_question=question,
        interview_role=role,
        interview_progress=f"Question 1 of {INTERVIEW_LENGTH}",
        active_waypoint="waypoint-04",
    )


@login_required
@require_POST
@ratelimit(key='user_or_ip', rate='10/m', block=False)
async def submit_interview_answer(request):
    """POST /interview/answer/ — records an answer, asks the next question
    or (on the final question) returns the full feedback report."""
    if getattr(request, 'limited', False):
        return await sync_to_async(render_home)(request, interview_error="You're submitting answers too quickly. Please wait a moment.", active_waypoint="waypoint-04")

    user_answer = request.POST.get("interview_answer", "")
    role = request.session.get("interview_role")
    history_data = request.session.get("interview_history", [])

    if not user_answer:
        return await sync_to_async(render_home)(request, interview_error="Type an answer before hitting submit.", active_waypoint="waypoint-04")

    if history_data:
        history_data[-1]["answer"] = user_answer
        request.session["interview_history"] = history_data
    
    is_final = len(history_data) >= INTERVIEW_LENGTH

    if is_final:
        final_prompt = (
            f"Review the candidate's {INTERVIEW_LENGTH} answers for the "
            f"{role} role. Provide a structured feedback report with "
            "markdown headings: 1) Overall impression, 2) Strengths, "
            "3) Areas to improve, 4) One practical tip for their next "
            "real interview."
        )
        history_data.append({"role": "system", "content": final_prompt})
        raw = await get_ai_response("You are an expert interviewer giving final feedback.", repr(history_data))

        if raw is None:
            return await sync_to_async(render_home)(request, interview_error="Couldn't reach the AI just now — please try again in a moment.", active_waypoint="waypoint-04")

        feedback_html = to_html(raw)

        await sync_to_async(InterviewReport.objects.create)(
            user=request.user,
            target_role=role,
            feedback_html=feedback_html,
        )

        request.session.pop("interview_history", None)
        request.session.pop("interview_role", None)

        return await sync_to_async(render_home)(request, interview_feedback=feedback_html, active_waypoint="waypoint-04")
    
    else:
        history_data.append({"role": "system", "content": "Ask the next relevant interview question. Respond with ONLY the question text."})
        raw = await get_ai_response(f"You are an expert interviewer for a {role} position.", repr(history_data))

        if raw is None:
            return await sync_to_async(render_home)(request, interview_error="Couldn't reach the AI just now — please try again in a moment.", active_waypoint="waypoint-04")

        next_question = raw.strip()
        history_data.append({"question": next_question, "answer": None})
        request.session["interview_history"] = history_data

        return await sync_to_async(render_home)(
            request,
            interview_question=next_question,
            interview_role=role,
            interview_progress=f"Question {len(history_data)} of {INTERVIEW_LENGTH}",
            active_waypoint="waypoint-04",
        )


# =========================================================
# PDF export — download resume/interview feedback as PDF
# =========================================================

def _build_pdf_response(filename, title, subtitle, html_body):
    html_string = render_to_string('pdf_template.html', {
        'title': title,
        'subtitle': subtitle,
        'html_body': html_body
    })
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    pisa_status = pisa.CreatePDF(
       html_string, dest=response
    )
    if pisa_status.err:
       return HttpResponse('We had some errors <pre>' + html_string + '</pre>')
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