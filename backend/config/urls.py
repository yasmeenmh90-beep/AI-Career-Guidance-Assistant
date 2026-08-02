from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from chatbot import views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='chatbot/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # Dashboard
    path('history/', views.history, name='history'),

    # PDF exports
    path('history/resume/<int:report_id>/pdf/', views.download_resume_pdf, name='download_resume_pdf'),
    path('history/interview/<int:report_id>/pdf/', views.download_interview_pdf, name='download_interview_pdf'),
    path('history/skill-gap/<int:report_id>/pdf/', views.download_skill_gap_pdf, name='download_skill_gap_pdf'),

    # Feature endpoints — one per action
    path('ask/', views.ask_question, name='ask_question'),
    path('resume/', views.analyze_resume, name='analyze_resume'),
    path('skill-gap/', views.analyze_skill_gap, name='analyze_skill_gap'),
    path('interview/start/', views.start_interview, name='start_interview'),
    path('interview/answer/', views.submit_interview_answer, name='submit_interview_answer'),

    # REST API
    path('api/', include('chatbot.urls')),

    path('', views.home, name='home'),
]