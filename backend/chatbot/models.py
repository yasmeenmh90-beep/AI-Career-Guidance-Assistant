from django.db import models
from django.contrib.auth.models import User


class ChatQuestion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_questions")
    question = models.TextField()
    answer_html = models.TextField()
    matched_career = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class ResumeReport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="resume_reports")
    filename = models.CharField(max_length=255)
    feedback_html = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class SkillGapReport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="skill_gap_reports")
    target_role = models.CharField(max_length=100)
    feedback_html = models.TextField()
    missing_skills = models.TextField(blank=True, default="")  # comma-separated, used for trend chart
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class InterviewReport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="interview_reports")
    role = models.CharField(max_length=100)
    feedback_html = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class CareerPath(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class RoadmapStep(models.Model):
    career_path = models.ForeignKey(CareerPath, on_delete=models.CASCADE, related_name="steps")
    step_text = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.career_path.name} - Step {self.order}"


class Course(models.Model):
    career_path = models.ForeignKey(CareerPath, on_delete=models.CASCADE, related_name="courses")
    name = models.CharField(max_length=255)
    platform = models.CharField(max_length=100)
    link = models.URLField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name