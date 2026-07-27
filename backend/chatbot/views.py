from django.shortcuts import render
from openai import OpenAI
from dotenv import load_dotenv
import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

load_dotenv(os.path.join(BASE_DIR, ".env"))

api_key = os.getenv("OPENAI_API_KEY", "").strip()

client = OpenAI(api_key=api_key)

# Load roadmap and course data
with open(os.path.join(BASE_DIR, "..", "resources", "roadmaps.json")) as f:
    ROADMAPS = json.load(f)

with open(os.path.join(BASE_DIR, "..", "resources", "courses.json")) as f:
    COURSES = json.load(f)


def find_matching_career(question):
    question_lower = question.lower()
    for career in ROADMAPS.keys():
        if career.lower() in question_lower:
            return career
    return None


def home(request):
    answer = None
    roadmap = None
    courses = None

    if request.method == "POST":
        question = request.POST.get("question")

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful career and study guidance assistant for students. Give clear practical advice."
                },
                {
                    "role": "user",
                    "content": question
                }
            ]
        )

        answer = response.choices[0].message.content

        matched_career = find_matching_career(question)
        if matched_career:
            roadmap = ROADMAPS[matched_career]["steps"]
            courses = COURSES[matched_career]

    return render(request, "chatbot/home.html", {
        "answer": answer,
        "roadmap": roadmap,
        "courses": courses
    })