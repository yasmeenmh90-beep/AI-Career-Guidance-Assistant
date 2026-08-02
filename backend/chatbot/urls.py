from django.urls import path
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, JSONParser

from .views import (
    find_matching_career,
    extract_text_from_file,
    get_ai_response,
    to_html,
    ROADMAPS,
    COURSES,
)
from .models import ChatQuestion, ResumeReport


class CareerListView(APIView):
    def get(self, request):
        return Response({"careers": list(ROADMAPS.keys())})


class ChatAPIView(APIView):
    parser_classes = [JSONParser]

    def post(self, request):
        question = (request.data.get("question") or "").strip()
        if not question:
            return Response(
                {"error": "Question is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        raw = get_ai_response(
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
        matched_career = find_matching_career(question)

        if request.user.is_authenticated:
            ChatQuestion.objects.create(
                user=request.user,
                question=question,
                answer_html=answer_html or "",
                matched_career=matched_career or "",
            )

        return Response({
            "answer_html": answer_html,
            "matched_career": matched_career,
            "roadmap": ROADMAPS[matched_career]["steps"] if matched_career else [],
            "courses": COURSES.get(matched_career, []) if matched_career else [],
        })


class ResumeAPIView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
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

        raw = get_ai_response(
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
            ResumeReport.objects.create(
                user=request.user,
                filename=uploaded_file.name,
                feedback_html=feedback_html or "",
            )

        return Response({
            "feedback_html": feedback_html,
            "filename": uploaded_file.name,
        })


class SkillGapAPIView(APIView):
    parser_classes = [JSONParser]

    def post(self, request):
        current_skills = (request.data.get("current_skills") or "").strip()
        target_role = (request.data.get("target_role") or "").strip()

        if not current_skills or not target_role:
            return Response(
                {"error": "Both 'current_skills' and 'target_role' are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        prompt = (
            f"The user wants to become a {target_role}. "
            f"Their current skills are: {current_skills}. "
            "Identify the skill gaps, explain why each matters, and give a prioritised "
            "learning plan. Use markdown headings and bullet points."
        )
        raw = get_ai_response(
            "You are an expert career coach specialising in tech skill development.",
            prompt,
        )
        if raw is None:
            return Response(
                {"error": "Could not reach the AI service. Please try again."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response({
            "feedback_html": to_html(raw),
            "target_role": target_role,
        })


urlpatterns = [
    path("careers/", CareerListView.as_view(), name="api-career-list"),
    path("chat/", ChatAPIView.as_view(), name="api-chat"),
    path("resume/", ResumeAPIView.as_view(), name="api-resume"),
    path("skill-gap/", SkillGapAPIView.as_view(), name="api-skill-gap"),
]
