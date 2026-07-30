# AI Career & Study Guidance Assistant

An AI-powered platform that provides personalised career and study guidance in one place — built for **NextGen Innovation 2026** hackathon under the **AI for Social Impact** theme.

## Problem

Students today are often unsure about which skills to learn, how to prepare for interviews, or how to plan their career path. This information is scattered across many websites, making it overwhelming and time-consuming to piece together.

## Solution

An AI chatbot and guidance dashboard that brings career roadmaps, learning resources, and resume feedback into a single platform.

## Features

- **AI Career Chatbot** — ask any career or study-related question and get a detailed AI-generated answer
- **Career Roadmap Suggestions** — step-by-step roadmaps for roles like AI Engineer, Data Scientist, Web Developer, Cloud Engineer, and Cybersecurity Analyst
- **Resource Recommendations** — curated courses, tutorials, and learning materials linked to each career path
- **Resume Analysis** — upload a resume (PDF or DOCX) and get AI-generated feedback on strengths, missing sections, and specific improvement suggestions

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django |
| AI | OpenAI API |
| Frontend | HTML, CSS, JavaScript |
| Database | SQLite |
| Resume Parsing | PyPDF2 (PDF), python-docx (DOCX) |
| Design System | Trailmark (custom tokens.css, base.css, components.css) |

## Project Structure

```
AI-Career-Guidance-Assistant/
├── backend/
│   ├── config/          # Django project settings, urls.py
│   ├── chatbot/         # Main app — views.py, models.py, roadmaps.json, courses.json
│   ├── static/          # CSS (Trailmark design system) and JS
│   ├── templates/       # home.html and other templates
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

## Adding More Career Paths

To add a new role, add matching entries to `chatbot/roadmaps.json` and `chatbot/courses.json` following the existing format.

## Team

| Name | Role |
|---|---|
| Yasmeen Azmat Ali | AI Chatbot, Django Backend, Career Roadmap Logic, Project Coordination |
| Sai Krishna | Resume Analysis, Deployment, Backend/API Support |
| Mohammed Ayaan | Resource Collection, Testing, Documentation, Content Organisation |
| Gagan | UI/UX Design, Branding, Presentation Deck, Demo Video, Visual Assets |

## Hackathon

Built for **NextGen Innovation 2026** — Innovate • Collaborate • Transform
