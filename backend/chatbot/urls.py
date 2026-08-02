from django.urls import path
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, JSONParser
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit

from asgiref.sync import sync_to_async
from .views import (
    find_matching_career,
    extract_text_from_file,
    get_ai_response,
    to_html,
    SkillGapResponse,
)
from .models import ChatQuestion, ResumeReport, CareerPath, RoadmapStep, Course, InterviewReport, SkillGapReport
from django.conf import settings
from .auth_api import auth_status, api_login, api_logout, api_signup
INTERVIEW_LENGTH = 5


class CareerListView(APIView):
    def get(self, request):
        careers = list(CareerPath.objects.values_list('name', flat=True))
        return Response({"careers": careers})


class ChatAPIView(APIView):
    parser_classes = [JSONParser]

    @method_decorator(ratelimit(key='user_or_ip', rate='10/m', block=False))
    async def post(self, request):
        if getattr(request, 'limited', False):
            return Response(
                {"error": "Too many requests. Please slow down."},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        question = (request.data.get("question") or "").strip()
        if not question:
            return Response(
                {"error": "Question is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        raw = await get_ai_response(
            "You are a helpful career and study guidance assistant for students. "
            "Give clear practical advice.",
            question,
        )
        if raw is None:
            return Response(
                {"error": "Could not reach the AI service. Please try again."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        answer_html = to_html(raw)
        matched_career = await find_matching_career(question)

        if request.user.is_authenticated:
            await sync_to_async(ChatQuestion.objects.create)(
                user=request.user,
                question=question,
                answer_html=answer_html or "",
                matched_career=matched_career or "",
            )

        roadmap = await sync_to_async(lambda: list(RoadmapStep.objects.filter(career_path__name=matched_career).values_list('step_text', flat=True)))() if matched_career else []
        courses = await sync_to_async(lambda: list(Course.objects.filter(career_path__name=matched_career).values('name', 'platform', 'link')))() if matched_career else []

        return Response({
            "answer_html": answer_html,
            "matched_career": matched_career,
            "roadmap": roadmap,
            "courses": courses,
        })


class ResumeAPIView(APIView):
    parser_classes = [MultiPartParser]

    @method_decorator(ratelimit(key='user_or_ip', rate='5/m', block=False))
    async def post(self, request):
        if getattr(request, 'limited', False):
            return Response(
                {"error": "Too many requests. Please slow down."},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        uploaded_file = request.FILES.get("resume_file")
        if not uploaded_file:
            return Response(
                {"error": "No file uploaded. Please provide a PDF or DOCX file."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ext = uploaded_file.name.rsplit(".", 1)[-1].lower()
        if ext not in ("pdf", "docx"):
            return Response(
                {"error": f"Unsupported file type '.{ext}'. Please upload a PDF or DOCX."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        resume_text = extract_text_from_file(uploaded_file)
        if resume_text is None:
            return Response(
                {"error": "Could not read the file. It may be corrupted or image-based."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        raw = await get_ai_response(
            "You are a professional resume reviewer. Analyze the given resume and provide "
            "clear structured feedback: 1) Missing sections, 2) Strengths, "
            "3) Areas to improve, 4) Specific actionable suggestions. "
            "Be concise and practical. Use markdown.",
            resume_text,
        )
        if raw is None:
            return Response(
                {"error": "Could not reach the AI service. Please try again."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        feedback_html = to_html(raw)

        if request.user.is_authenticated:
            await sync_to_async(ResumeReport.objects.create)(
                user=request.user,
                filename=uploaded_file.name,
                feedback_html=feedback_html or "",
            )

        return Response({
            "feedback_html": feedback_html,
            "filename": uploaded_file.name,
        })


class SkillGapAPIView(APIView):
    parser_classes = [MultiPartParser]

    @method_decorator(ratelimit(key='user_or_ip', rate='5/m', block=False))
    async def post(self, request):
        if getattr(request, 'limited', False):
            return Response(
                {"error": "Too many requests. Please slow down."},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        uploaded_file = request.FILES.get("resume_file")
        target_role = request.POST.get("target_role", "").strip()

        if not uploaded_file or not target_role:
            return Response(
                {"error": "Both 'resume_file' and 'target_role' are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        valid_roles = await sync_to_async(lambda: list(CareerPath.objects.values_list('name', flat=True)))()
        if target_role not in valid_roles:
            return Response(
                {"error": "Pick a valid target role first."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        resume_text = extract_text_from_file(uploaded_file)
        if not resume_text:
            return Response(
                {"error": "Could not read the file. It may be corrupted or image-based."},
                status=status.HTTP_400_BAD_REQUEST,
            )

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
        parsed_response = await get_ai_response(
            system_prompt,
            resume_text,
            response_format=SkillGapResponse
        )
        if parsed_response is None:
            return Response(
                {"error": "Could not reach the AI service. Please try again."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response({
            "feedback_html": to_html(parsed_response.feedback_markdown),
            "missing_skills": parsed_response.missing_skills,
            "target_role": target_role,
        })


class InterviewStartAPIView(APIView):
    parser_classes = [JSONParser]

    @method_decorator(ratelimit(key='user_or_ip', rate='5/m', block=False))
    async def post(self, request):
        if getattr(request, 'limited', False):
            return Response({"error": "Too many requests. Please slow down."}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        role = request.data.get("interview_role", "").strip()
        
        valid_roles = await sync_to_async(lambda: list(CareerPath.objects.values_list('name', flat=True)))()
        if not role or role not in valid_roles:
            return Response({"error": "Pick a valid role first."}, status=status.HTTP_400_BAD_REQUEST)

        system_prompt = (
            f"You are conducting a mock interview for a {role} position. "
            "Ask one relevant, realistic interview question. "
            "Reply with just the question — no extra text, no markdown."
        )
        question = await get_ai_response(system_prompt, "Ask the first interview question.")

        if question is None:
            return Response({"error": "Could not reach the AI service."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        request.session["interview_role"] = role
        request.session["interview_history"] = [{"question": question, "answer": None}]

        return Response({
            "question": question,
            "progress": f"Question 1 of {INTERVIEW_LENGTH}"
        })


class InterviewAnswerAPIView(APIView):
    parser_classes = [JSONParser]

    @method_decorator(ratelimit(key='user_or_ip', rate='10/m', block=False))
    async def post(self, request):
        if getattr(request, 'limited', False):
            return Response({"error": "Too many requests. Please slow down."}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        user_answer = request.data.get("answer", "").strip()
        role = request.session.get("interview_role")
        history_data = request.session.get("interview_history", [])

        if not user_answer:
            return Response({"error": "Answer is required."}, status=status.HTTP_400_BAD_REQUEST)

        if not role or not history_data:
            return Response({"error": "No active interview found. Please start a new one."}, status=status.HTTP_400_BAD_REQUEST)

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
                return Response({"error": "Could not reach the AI service."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

            feedback_html = to_html(raw)
            if request.user.is_authenticated:
                await sync_to_async(InterviewReport.objects.create)(
                    user=request.user,
                    role=role,
                    feedback_html=feedback_html,
                )

            request.session.pop("interview_history", None)
            request.session.pop("interview_role", None)

            return Response({
                "feedback_html": feedback_html,
                "is_final": True
            })
        else:
            history_data.append({"role": "system", "content": "Ask the next relevant interview question. Respond with ONLY the question text."})
            raw = await get_ai_response(f"You are an expert interviewer for a {role} position.", repr(history_data))

            if raw is None:
                return Response({"error": "Could not reach the AI service."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

            next_question = raw.strip()
            history_data.append({"question": next_question, "answer": None})
            request.session["interview_history"] = history_data

            return Response({
                "question": next_question,
                "progress": f"Question {len(history_data)} of {INTERVIEW_LENGTH}",
                "is_final": False
            })


from django.http import JsonResponse

async def api_history(request):
    user = await request.auser()
    is_auth = await sync_to_async(lambda: user.is_authenticated)()
    if not is_auth:
        return JsonResponse({"error": "Not authenticated"}, status=401)
        
    chat_count = await sync_to_async(ChatQuestion.objects.filter(user=user).count)()
    resume_count = await sync_to_async(ResumeReport.objects.filter(user=user).count)()
    skill_gap_count = await sync_to_async(SkillGapReport.objects.filter(user=user).count)()
    interview_count = await sync_to_async(InterviewReport.objects.filter(user=user).count)()
    
    total_activity = chat_count + resume_count + skill_gap_count + interview_count
    
    import math
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
        
    # Skill-gap trends
    skill_counts = {}
    skill_gaps = await sync_to_async(list)(SkillGapReport.objects.filter(user=user))
    for report in skill_gaps:
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
    
    chat_qs = await sync_to_async(list)(ChatQuestion.objects.filter(user=user).order_by('-created_at'))
    chat_questions = [{"question": q.question, "matched_career": q.matched_career, "created_at": q.created_at.strftime("%d %b %Y, %H:%M")} for q in chat_qs]
    
    resume_qs = await sync_to_async(list)(ResumeReport.objects.filter(user=user).order_by('-created_at'))
    resume_reports = [{"id": r.id, "filename": r.filename, "created_at": r.created_at.strftime("%d %b %Y, %H:%M")} for r in resume_qs]
    
    skill_gap_reports = [{"id": s.id, "target_role": s.target_role, "created_at": s.created_at.strftime("%d %b %Y, %H:%M")} for s in skill_gaps]
    
    interview_qs = await sync_to_async(list)(InterviewReport.objects.filter(user=user).order_by('-created_at'))
    interview_reports = [{"id": i.id, "role": i.role, "created_at": i.created_at.strftime("%d %b %Y, %H:%M")} for i in interview_qs]
    
    return JsonResponse({
        "total_activity": total_activity,
        "donut_segments": donut_segments,
        "skill_trend_rows": skill_trend_rows,
        "chat_questions": chat_questions,
        "resume_reports": resume_reports,
        "skill_gap_reports": skill_gap_reports,
        "interview_reports": interview_reports
    })

urlpatterns = [
    path("auth/status/", auth_status, name="api-auth-status"),
    path("auth/login/", api_login, name="api-auth-login"),
    path("auth/logout/", api_logout, name="api-auth-logout"),
    path("auth/signup/", api_signup, name="api-auth-signup"),

    path("careers/", CareerListView.as_view(), name="api-career-list"),
    path("chat/", ChatAPIView.as_view(), name="api-chat"),
    path("resume/", ResumeAPIView.as_view(), name="api-resume"),
    path("skill-gap/", SkillGapAPIView.as_view(), name="api-skill-gap"),
    path("interview/start/", InterviewStartAPIView.as_view(), name="api-interview-start"),
    path("interview/answer/", InterviewAnswerAPIView.as_view(), name="api-interview-answer"),
    path("history/", api_history, name="api-history"),
]
