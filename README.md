# FutureEra — Chart Your Career in the Age of AI

FutureEra is an AI-powered architectural career intelligence platform engineered for the generation navigating the AI revolution. It bridges the gap between decade-old college syllabuses and 2026 production hiring standards.

---

## 🚀 Key Features

- **Multi-Eligible Career Suggestion Engine**: Analyzes your 12th stream or degree background to recommend 5 high-yield 2026 careers tailored to your exact analytical strengths with live match scores.
- **AI Shield & Automation Resistance Audit**: Comprehensive automation risk audits pinpointing deep human edges AI cannot replace.
- **Multi-Year Roadmap & Production Capstones**: Year-by-year engineering milestones with production capstone systems, documentation links, and placement action items.
- **2026 Market Tech Radar**: Tracks modern technologies to adopt vs obsolete syllabus tech to avoid.
- **Offline SQLite Vault**: Every generated blueprint and suggestion is cached locally with WAL mode for zero-latency offline fallback.
- **Searchable Degree & Profession Combobox**: Interactive comboboxes with keyboard navigation and instant autocomplete.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.10+, FastAPI, Uvicorn, Pydantic v2
- **AI Engine**: Google Gemini API (`gemini-2.5-flash`)
- **Database**: SQLite with WAL mode & zero-latency fallback caching
- **Frontend**: HTML5, Vanilla CSS3 (Architectural Design System), JavaScript ES6+
- **Animations**: GSAP 3 & ScrollTrigger

---

## 📦 Project Structure

```
final_project/
├── app/
│   ├── config.py              # Environment configuration & port settings
│   ├── database.py            # SQLite database schema, WAL mode, cache & stats
│   ├── main.py                # FastAPI routes, endpoints & static mount
│   ├── schemas.py             # Pydantic models for request/response validation
│   ├── data/
│   │   └── career_data.json   # Comprehensive career knowledge graph
│   ├── services/
│   │   ├── gemini_service.py  # Gemini API integration & blueprint generation
│   │   ├── prompts.py         # 2026 architectural prompts
│   │   └── validation.py      # Input validation & anti-gibberish heuristics
│   └── static/
│       ├── index.html         # Landing page with GSAP animations
│       ├── stage.html         # 12th vs Final-Year path selector
│       ├── console.html       # AI Blueprint generation console
│       ├── creators.html      # Creative & engineering team showcase
│       ├── privacy.html       # Privacy policy
│       ├── terms.html         # Terms of service
│       ├── css/style.css      # Design system & responsive styles
│       ├── js/script.js       # Landing page animations
│       └── js/console.js      # Interactive console controller & offline cache
├── run.py                     # Application entry point
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variables template
└── .gitignore                 # Git ignore rules
```

---

## ⚡ Quick Start

### 1. Clone repository & Navigate
```bash
git clone <repository-url>
cd final_project
```

### 2. Setup Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Environment Variables
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 4. Run Development Server
```bash
python3 run.py
```
Open [http://127.0.0.1:8002/](http://127.0.0.1:8002/) in your browser.

---

## 👥 Creators

- **Dev Sharma** — Backend Architecture & API Pipeline
- **Harshit Chaurasiya** — Backend Services, Data Stacks & Caching
- **Himanshu Bisht** — Frontend Architectural UI & Micro-interactions
- **Aman Chauhan** — SQLite Database Vault & Telemetry

---

## 📄 License

MIT License &copy; 2026 FutureEra. All rights reserved.
