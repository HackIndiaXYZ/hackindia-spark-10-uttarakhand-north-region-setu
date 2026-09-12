# 🚀 SkillBridge

SkillBridge is a smart student–industry skill matching platform developed as part of **Smart India Hackathon 2026**.

The platform aims to bridge the gap between student skills and industry requirements by analysing student profiles, identifying skill gaps, calculating career readiness, and recommending relevant opportunities.

## 🎯 Problem

Students often struggle to understand:

- Which skills are required for their desired career?
- How ready are they for a particular role?
- What skills are they missing?
- Which internships or job opportunities are relevant to their profile?

SkillBridge provides these insights through a single platform.

## ✨ Features

### 👨‍🎓 Student

- Student registration and login
- Profile management
- Skill Gap Analysis
- Career Readiness Score
- Role-based skill matching
- AI-based recommendations
- Internship & Job opportunities
- Application tracking
- Digital Portfolio

### 🏢 Industry

- Industry login
- Create job/internship opportunities
- Define required skills
- View suitable candidates
- Manage posted opportunities

### 🏫 Institution

- Manage student information
- Monitor student career readiness
- View platform-level insights

## 🧠 Skill Matching

SkillBridge uses a transparent hybrid matching approach.

| Factor | Weight |
|---|---:|
| Skills | 40% |
| Education / Eligibility | 20% |
| Career Interest | 15% |
| Projects | 10% |
| Certifications | 10% |
| Soft Skills | 5% |

The final matching score combines a weighted requirement-based score with text similarity using **TF-IDF and Cosine Similarity**.

```text
Final Match Score
        ↓
70% Weighted Matching
        +
30% Cosine Similarity
