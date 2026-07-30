# AI Career & Study Guidance Assistant

An AI-powered platform that provides personalised career and study guidance in one place — built for **NextGen Innovation 2026** hackathon under the **AI for Social Impact** theme.

## Problem

Students today are often unsure about which skills to learn, how to prepare for interviews, or how to plan their career path. This information is scattered across many websites, making it overwhelming and time-consuming to piece together.

## Solution

An AI chatbot and guidance dashboard that brings career roadmaps, learning resources, resume feedback, and mock interview practice into a single platform — styled with **Trailmark**, a trail/journey-themed design system where each feature is a waypoint on the student's career path.

## Features

- **AI Career Chatbot** — ask any career or study-related question and get a detailed, AI-generated answer, rendered as clean formatted text (headings, bold, bullet points)
- **Career Roadmap Suggestions** — step-by-step roadmaps for roles like AI Engineer, Data Scientist, Web Developer, Cloud Engineer, and Cybersecurity Analyst
- **Resource Recommendations** — curated courses, tutorials, and learning materials linked to each career path
- **Resume Analysis** — upload a resume (PDF or DOCX) and get AI-generated feedback on strengths, missing sections, and specific improvement suggestions
- **Interview Practice Mode** — pick a role, answer 5 AI-generated mock interview questions one at a time, and receive structured feedback (overall impression, strengths, areas to improve, one practical tip) at the end

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django |
| AI | OpenAI API |
| Frontend | HTML, CSS (Trailmark design system, embedded in `home.html`) |
| Database | SQLite |
| Resume Parsing | PyPDF2 (PDF), python-docx (DOCX) |
| Text Formatting | `markdown` (converts AI responses into styled HTML) |
| Session State | Django sessions (used for tracking mock interview progress) |
| Fonts | Fraunces (headings), Inter (body), IBM Plex Mono (labels) via Google Fonts |

## Project Structure

```
AI-Career-Guidance-Assistant/
├── backend/
│   ├── config/          # Django project settings, urls.py
│   ├── chatbot/         # Main app — views.py, models.py
│   │   └── templates/chatbot/home.html   # Trailmark UI (chat, resume, interview)
│   ├── resources/       # roadmaps.json, courses.json
│   ├── requirements.txt
│   └── manage.py
└── README.md
```

## Setup Instructions

### Prerequisites
- Python 3.10+ (avoid 3.13 if using `pipreqs`, or use the trimmed requirements file)
- pip

### 1. Clone the repository
```bash
git clone <repo-url>
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

### 5. Run migrations
```bash
python manage.py migrate
```

### 6. Start the development server
```bash
python manage.py runserver
```

The app will be available at `http://127.0.0.1:8000/`

## How Interview Practice Mode Works

1. Select a role from the dropdown and click **Start Mock Interview**
2. The AI asks one question at a time (5 total), tracked via Django sessions
3. After the 5th answer, the AI generates structured feedback covering overall impression, strengths, areas to improve, and one practical tip
4. Click **Try Another Role** to restart with a different career path

## Adding More Career Paths

To add a new role, add matching entries to `resources/roadmaps.json` and `resources/courses.json` following the existing format.

## Team

| Name | Role |
|---|---|
| Yasmeen Azmat Ali | 
| Sai Krishna | |
| Mohammed Ayaan | 
| Gagan | 

## Hackathon

Built for **NextGen Innovation 2026** — Innovate • Collaborate • Transform
