# SkillBridge — Academia–Industry Collaboration Portal

SIH 2026 Problem Statement **26044**. MVP stack: **HTML, CSS, JavaScript, Flask, PostgreSQL**.

Matching is a **transparent weighted scorer** (not a production ML model):

| Signal | Weight |
| --- | --- |
| Skill compatibility | 40% |
| Education / eligibility | 20% |
| Career interest | 15% |
| Projects | 10% |
| Certifications | 10% |
| Soft skills | 5% |

Replace `matching.compute_match` later with a trained recommender; API shapes stay the same.

## Run locally

1. Start PostgreSQL (Docker):

```bash
docker compose up -d
```

Or create a database `skillbridge` with user/password `skillbridge` / `skillbridge`.

2. Python env:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python app.py
```

3. Open [http://127.0.0.1:5000](http://127.0.0.1:5000)

## Demo accounts

| Role | Email | Password |
| --- | --- | --- |
| Student (Priya Sharma) | student@skillbridge.in | student123 |
| Industry (TechNova) | industry@technova.in | industry123 |
| Academician | faculty@college.edu | faculty123 |
| Institution (NIT Jaipur) | admin@college.edu | admin123 |

## SIH walkthrough

1. Login as **Student**.
2. Skill Assessment → **Load SIH demo answers & submit**.
3. Skill profile + **Skill Gap Analysis**; set career goal **Data Analyst**.
4. Open **AI Recommendations** (courses, certs, projects, internships).
5. Search **Internships & Jobs**, open **Data Analyst Intern** (TechNova), Apply.
6. Confirm it appears in **My Applications**.
7. Login as **Industry** → Candidate matching → **Shortlist** Priya.
8. Login as **Institution** — KPIs and charts update (assessments, applications, gaps).
