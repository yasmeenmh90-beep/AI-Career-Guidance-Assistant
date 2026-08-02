from django.contrib import admin
from .models import (
    ChatQuestion,
    ResumeReport,
    SkillGapReport,
    InterviewReport,
    CareerPath,
    RoadmapStep,
    Course,
)

admin.site.register(ChatQuestion)
admin.site.register(ResumeReport)
admin.site.register(SkillGapReport)
admin.site.register(InterviewReport)

class RoadmapStepInline(admin.TabularInline):
    model = RoadmapStep
    extra = 1

class CourseInline(admin.TabularInline):
    model = Course
    extra = 1

@admin.register(CareerPath)
class CareerPathAdmin(admin.ModelAdmin):
    inlines = [RoadmapStepInline, CourseInline]
    list_display = ("name", "created_at")

admin.site.register(RoadmapStep)
admin.site.register(Course)
