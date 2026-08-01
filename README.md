
# Trailmark — AI Career & Study Guidance Assistant

An AI-powered platform that provides personalised career and study guidance in one place — built for **NextGen Innovation 2026** hackathon under the **AI for Social Impact** theme.

## Problem

Students today are often unsure about which skills to learn, how to prepare for interviews, or how to plan their career path. This information is scattered across many websites, making it overwhelming and time-consuming to piece together.

## Solution

An AI chatbot and guidance dashboard that brings career roadmaps, learning resources, resume feedback, skill-gap analysis, and mock interview practice into a single platform — styled with **Trailmark**, a trail/journey-themed design system where each feature is a waypoint on the student's career path.

## Features

- **AI Career Chatbot** — ask any career or study-related question and get a detailed, AI-generated answer, rendered as clean formatted text (headings, bold, bullet points)
- **Career Roadmaps** — step-by-step, timeline-style learning paths for 8 roles: AI Engineer, Data Scientist, Web Developer, Cloud Engineer, Cybersecurity Analyst, Data Analyst, UI/UX Designer, and DevOps Engineer
- **Resource Recommendations** — curated, verified courses linked to each career path
- **Resume Analysis** — upload a resume (PDF or DOCX) and get AI-generated feedback on strengths, missing sections, and specific improvement suggestions
- **Skill-Gap Analysis** — upload a resume and pick a target role to see which skills you already have, which are missing, and a prioritised list of what to learn next, with reasons
- **Interview Practice Mode** — pick a role, answer 5 AI-generated mock interview questions one at a time, and receive structured feedback (overall impression, strengths, areas to improve, one practical tip)
- **User Accounts** — sign up, log in, and every result above is saved to your account
- **Trail Progress & Activity Dashboard** — a circular progress ring shows how many of the 4 core features you've explored, and a "My History" page shows a full activity chart plus a log of every question, resume check, skill-gap report, and mock interview you've done
- **Light & Dark Mode** — toggle in the top bar, saved across sessions
- **Route-Draw Animation** — the career roadmap reveals itself step-by-step as you scroll, with an animated connecting line
- **Drag-and-Drop Resume Upload** — resume upload zones support drag-and-drop with a checkmark confirmation

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django |
| AI | OpenAI API (GPT-4o-mini) |
| Auth | Django's built-in authentication (session-based login/signup) |
| Frontend | HTML, CSS, vanilla JS (Trailmark design system, embedded per-template) |
| Database | SQLite |
| Resume Parsing | PyPDF2 (PDF), python-docx (DOCX) |
| Text Formatting | `markdown` (converts AI responses into styled HTML) |
| Fonts | Fraunces (headings), Inter (body), IBM Plex Mono (labels) via Google Fonts |

## Project Structure

```
AI-Career-Guidance-Assistant/
├── backend/
│   ├── config/                     # Django project settings, urls.py
│   ├── chatbot/
│   │   ├── models.py                 # ChatQuestion, ResumeReport, SkillGapReport, InterviewReport
│   │   ├── views.py                  # One view per feature (REST-style endpoints)
│   │   ├── migrations/
│   │   └── templates/chatbot/
│   │       ├── home.html             # Main app — chat, resume, skill gap, interview
│   │       ├── login.html
│   │       ├── signup.html
│   │       └── history.html          # Activity chart + saved history
│   ├── resources/
│   │   ├── roadmaps.json
│   │   └── courses.json
│   ├── requirements.txt
│   └── manage.py
└── README.md
```

## API / URL Structure

Each feature has its own endpoint rather than one large view handling everything:

| URL | Purpose |
|---|---|
| `/` | Home / trail overview |
| `/ask/` | Chatbot question → answer + roadmap + courses |
| `/resume/` | Resume upload → AI feedback |
| `/skill-gap/` | Resume + target role → skill-gap report |
| `/interview/start/` | Begin a mock interview |
| `/interview/answer/` | Submit an answer / get next question or final feedback |
| `/history/` | Activity dashboard |
| `/signup/`, `/login/`, `/logout/` | Auth |

## Setup Instructions

### Prerequisites
- Python 3.10+ (avoid 3.13 if using `pipreqs`, or use the trimmed requirements file)
- pip

### 1. Clone the repository
```bash
git clone https://github.com/yasmeenmh90-beep/AI-Career-Guidance-Assistant.git
cd AI-Career-Guidance-Assistant/backend
```

### 2. Create a virtual environment (recommended)
```bash
python -m venv venv
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
Create a `.env` file in the `backend/` folder:
```
OPENAI_API_KEY=your_openai_api_key_here
```

### 5. Add these lines to `config/settings.py`
```python
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'login'
```

### 6. Run migrations
```bash
python manage.py migrate
```

### 7. Start the development server
```bash
python manage.py runserver
```

The app will be available at `http://127.0.0.1:8000/`. You'll be redirected to the login page — sign up for a new account to get started.

## How Interview Practice Mode Works

1. Select a role from the dropdown and click **Start Mock Interview**
2. The AI asks one question at a time (5 total), tracked via Django sessions
3. After the 5th answer, the AI generates structured feedback covering overall impression, strengths, areas to improve, and one practical tip
4. Click **Try Another Role** to restart with a different career path

## How Skill-Gap Analysis Works

1. Upload a resume and pick a target role
2. The AI compares the resume's content against that role's roadmap
3. It returns: skills already present, skills missing from the roadmap, and a prioritised list of 3–5 skills to learn next, each with a reason

## Adding More Career Paths

To add a new role, add matching entries to `resources/roadmaps.json` and `resources/courses.json` following the existing format — any new role automatically appears in the chatbot, skill-gap dropdown, and interview dropdown.

## Team

| Name | Role |
|---|---|
| Yasmeen Azmat Ali | AI Chatbot, Skill-Gap Analysis, Interview Practice Mode, Django Backend, User Accounts, UI Styling & Animations, Career Roadmap Logic, Project Coordination |
| Sai Krishna | Resume Analysis, Deployment, Backend/API Support |
| Mohammed Ayaan | Resource Collection, Testing, Documentation, Content Organisation |
| Gagan | UI/UX Design, Branding, Presentation Deck, Demo Video, Visual Assets |

## Hackathon

Built for **NextGen Innovation 2026** — Innovate • Collaborate • Transform
