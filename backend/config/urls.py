from django.contrib import admin
from django.urls import path
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

    # Feature endpoints — one per action
    path('ask/', views.ask_question, name='ask_question'),
    path('resume/', views.analyze_resume, name='analyze_resume'),
    path('skill-gap/', views.analyze_skill_gap, name='analyze_skill_gap'),
    path('interview/start/', views.start_interview, name='start_interview'),
    path('interview/answer/', views.submit_interview_answer, name='submit_interview_answer'),

    path('', views.home, name='home'),
]