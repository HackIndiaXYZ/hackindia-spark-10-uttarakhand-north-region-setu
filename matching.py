"""
Intelligent Recommendation & Skill-Gap Engine for SkillBridge SIH-2026.

Combines:
1. Multi-factor explainable weighted matching (Transparent Baseline)
2. Content-based TF-IDF vectorization & Cosine Similarity (Scikit-Learn ML with pure-python fallback)
3. Hybrid ensemble scoring:
   Match = 0.70 * WeightedScore + 0.30 * CosineSimilarity
4. Mathematically explainable Skill Gap Priority (High / Medium / Low / Met)
   and Competency Coverage Career Readiness.
"""

import math
import re
from typing import Dict, List, Tuple, Any, Optional

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


ROLE_REQUIREMENTS = {
    "Data Analyst": {
        "technical": {
            "Python": 70,
            "SQL": 75,
            "Excel": 70,
            "Data Visualization": 65,
            "Data Analytics": 65,
        },
        "soft": {"Communication": 70, "Problem Solving": 65},
        "education": ["B.Tech", "B.E.", "B.Sc", "BCA", "M.Sc", "MCA", "M.Tech"],
        "keywords": ["data", "analyst", "analytics", "business intelligence", "bi", "sql", "excel", "power bi", "tableau"],
        "learn": ["Advanced SQL & Window Functions", "Power BI / Tableau Dashboards", "Exploratory Data Analysis with Pandas"],
        "intern_titles": [
            "Data Analyst Intern",
            "Business Analytics Intern",
            "Junior Data Science Intern",
            "Analytics Apprentice",
        ],
    },
    "Software Engineer": {
        "technical": {
            "Python": 65,
            "Java": 70,
            "Web Development": 75,
            "SQL": 60,
            "C/C++": 55,
        },
        "soft": {"Problem Solving": 70, "Teamwork": 65, "Time Management": 65},
        "education": ["B.Tech", "B.E.", "MCA", "M.Tech", "BCA"],
        "keywords": ["software", "developer", "engineer", "web", "backend", "full stack", "frontend", "api", "java", "python"],
        "learn": ["Data Structures & Algorithms", "RESTful API Architecture", "Database Design & Optimization"],
        "intern_titles": ["Software Engineer Intern", "Web Developer Intern", "Backend Developer Intern"],
    },
    "ML Engineer": {
        "technical": {
            "Python": 75,
            "AI/ML": 75,
            "Data Analytics": 70,
            "SQL": 60,
            "Cloud": 55,
        },
        "soft": {"Problem Solving": 75, "Communication": 65},
        "education": ["B.Tech", "B.E.", "M.Tech", "M.Sc", "MCA"],
        "keywords": ["ml", "machine learning", "ai", "data science", "deep learning", "neural networks", "nlp", "predictive"],
        "learn": ["Feature Pipeline Engineering", "Supervised & Unsupervised Learning", "Model Evaluation & Deployment"],
        "intern_titles": ["Junior Data Science Intern", "ML Intern", "AI Research Intern"],
    },
    "Cloud Engineer": {
        "technical": {
            "Cloud": 75,
            "Python": 60,
            "SQL": 55,
            "Web Development": 55,
        },
        "soft": {"Problem Solving": 70, "Teamwork": 65},
        "education": ["B.Tech", "B.E.", "MCA", "BCA"],
        "keywords": ["cloud", "aws", "azure", "devops", "docker", "infrastructure", "kubernetes", "linux"],
        "learn": ["AWS Cloud Practitioner & Architecture", "Linux Shell Scripting & Networking", "Docker Containerization"],
        "intern_titles": ["Cloud Intern", "DevOps Intern", "Cloud Infrastructure Intern"],
    },
    "Cybersecurity Analyst": {
        "technical": {
            "Cloud": 65,
            "Python": 60,
            "SQL": 55,
            "C/C++": 50,
        },
        "soft": {"Problem Solving": 75, "Time Management": 70},
        "education": ["B.Tech", "B.E.", "BCA", "MCA"],
        "keywords": ["security", "cyber", "network security", "vulnerability", "infosec", "penetration testing"],
        "learn": ["Network Protocols & Security", "Threat Modeling & Vulnerability Assessment", "Security Auditing Basics"],
        "intern_titles": ["Cybersecurity Intern", "SOC Analyst Intern", "Security Intern"],
    },
    "Full Stack Developer": {
        "technical": {
            "Web Development": 80,
            "SQL": 70,
            "Python": 65,
            "Cloud": 55,
        },
        "soft": {"Problem Solving": 70, "Teamwork": 70, "Time Management": 65},
        "education": ["B.Tech", "B.E.", "BCA", "MCA"],
        "keywords": ["full stack", "frontend", "backend", "web", "react", "node", "javascript", "api", "database"],
        "learn": ["Modern JavaScript / React Frameworks", "API Development & Authentication", "Database Indexing & Caching"],
        "intern_titles": ["Full Stack Developer Intern", "Web Application Intern"],
    },
}

WEIGHTS = {
    "skills": 0.40,
    "education": 0.20,
    "career": 0.15,
    "projects": 0.10,
    "certs": 0.10,
    "soft": 0.05,
}

ASSESSMENT_QUESTIONS = [
    {"id": "py1", "skill": "Python", "category": "technical", "text": "How confidently can you write Python programs for data processing (lists, pandas, files)?"},
    {"id": "py2", "skill": "Python", "category": "technical", "text": "Can you debug Python code and use libraries (NumPy/pandas) without much help?"},
    {"id": "jv1", "skill": "Java", "category": "technical", "text": "Rate your Java OOP skills (classes, inheritance, collections)."},
    {"id": "cpp1", "skill": "C/C++", "category": "technical", "text": "Rate your C/C++ programming for algorithms and memory basics."},
    {"id": "web1", "skill": "Web Development", "category": "technical", "text": "Can you build a responsive webpage with HTML, CSS, and JavaScript?"},
    {"id": "da1", "skill": "Data Analytics", "category": "technical", "text": "How well can you clean datasets and compute descriptive statistics?"},
    {"id": "ml1", "skill": "AI/ML", "category": "technical", "text": "Have you trained a basic ML model (regression/classification) end-to-end?"},
    {"id": "sql1", "skill": "SQL", "category": "technical", "text": "Can you write SQL joins, GROUP BY, and window-style aggregations?"},
    {"id": "sql2", "skill": "SQL", "category": "technical", "text": "How comfortably can you design tables and query a relational database?"},
    {"id": "cld1", "skill": "Cloud", "category": "technical", "text": "Rate your experience with AWS/Azure/GCP (deploy, storage, compute)."},
    {"id": "ex1", "skill": "Excel", "category": "technical", "text": "Can you use Excel pivot tables, VLOOKUP/XLOOKUP, and charts?"},
    {"id": "dv1", "skill": "Data Visualization", "category": "technical", "text": "Can you build dashboards (Power BI / Tableau / matplotlib) that tell a story?"},
    {"id": "cm1", "skill": "Communication", "category": "soft", "text": "How clearly can you present technical work to non-technical listeners?"},
    {"id": "tm1", "skill": "Teamwork", "category": "soft", "text": "How well do you collaborate in group projects and take feedback?"},
    {"id": "ps1", "skill": "Problem Solving", "category": "soft", "text": "When a requirement is unclear, how well do you break it into solvable steps?"},
    {"id": "ld1", "skill": "Leadership", "category": "soft", "text": "Have you led a team, club, or project and owned delivery?"},
    {"id": "ti1", "skill": "Time Management", "category": "soft", "text": "How consistently do you meet academic and project deadlines?"},
]

DEMO_SKILL_SCORES = {
    "Python": 75,
    "Java": 60,
    "C/C++": 50,
    "Web Development": 55,
    "Data Analytics": 65,
    "AI/ML": 35,
    "SQL": 45,
    "Cloud": 40,
    "Excel": 60,
    "Data Visualization": 40,
    "Communication": 80,
    "Teamwork": 75,
    "Problem Solving": 70,
    "Leadership": 60,
    "Time Management": 72,
}

SKILL_ALIASES = {
    "Power BI": "Data Visualization",
    "PowerBI": "Data Visualization",
    "Tableau": "Data Visualization",
    "Database/SQL": "SQL",
    "PostgreSQL": "SQL",
    "MySQL": "SQL",
    "Database": "SQL",
    "React": "Web Development",
    "HTML/CSS": "Web Development",
    "JavaScript": "Web Development",
    "Machine Learning": "AI/ML",
    "Deep Learning": "AI/ML",
    "AWS": "Cloud",
    "Azure": "Cloud",
    "GCP": "Cloud",
    "DevOps": "Cloud",
    "MS Excel": "Excel",
}


def skill_value(score_map: Dict[str, float], name: str) -> float:
    """Retrieve skill score directly or via known ontology aliases."""
    if name in score_map:
        return float(score_map[name])
    alt = SKILL_ALIASES.get(name)
    if alt and alt in score_map:
        return float(score_map[alt])
    # Case-insensitive search
    lower_map = {k.lower(): v for k, v in score_map.items()}
    if name.lower() in lower_map:
        return float(lower_map[name.lower()])
    if alt and alt.lower() in lower_map:
        return float(lower_map[alt.lower()])
    return 0.0


def scores_from_answers(answers: Dict[str, Any]) -> Dict[str, int]:
    """Compute 0-100 skill scores from 1-5 questionnaire answers."""
    buckets = {}
    for q in ASSESSMENT_QUESTIONS:
        raw = answers.get(q["id"])
        if raw is None:
            continue
        val = max(1, min(5, float(raw)))
        buckets.setdefault(q["skill"], []).append(val)
    out = {}
    for skill, vals in buckets.items():
        out[skill] = round((sum(vals) / len(vals) / 5.0) * 100)
    return out


def student_score_map(skill_rows) -> Dict[str, float]:
    """Map DB SkillScore records to dictionary {skill_name: score}."""
    return {row.skill.name: float(row.score) for row in skill_rows if row.skill}


def analyze_gaps(score_map: Dict[str, float], career_goal: str = "Data Analyst") -> Dict[str, Any]:
    """
    Phase 2 — Intelligent Explainable Skill Gap Engine.
    
    Formula:
    - delta = max(0, required - student)
    - priority:
        * Met: delta == 0
        * High: delta >= 25 (critical skill shortfall)
        * Medium: 10 <= delta < 25 (moderate gap)
        * Low: 0 < delta < 10 (minor gap)
    - overall career readiness = (sum(min(have_i, need_i)) / sum(need_i)) * 100
      (Coverage ratio of competency requirements, explainable & bounded 0-100%)
    """
    profile = ROLE_REQUIREMENTS.get(career_goal, ROLE_REQUIREMENTS["Data Analyst"])
    required = {**profile["technical"], **profile["soft"]}
    
    rows = []
    total_needed = 0.0
    total_satisfied = 0.0
    high_count = 0
    medium_count = 0
    low_count = 0
    met_count = 0

    for skill, need in required.items():
        have = skill_value(score_map, skill)
        gap = round(max(0.0, float(need) - float(have)), 1)
        
        if gap == 0:
            priority = "Met"
            status = "strong"
            met_count += 1
        elif gap >= 25:
            priority = "High"
            status = "gap"
            high_count += 1
        elif gap >= 10:
            priority = "Medium"
            status = "gap"
            medium_count += 1
        else:
            priority = "Low"
            status = "gap"
            low_count += 1

        total_needed += float(need)
        total_satisfied += min(float(have), float(need))

        rows.append({
            "skill": skill,
            "required": need,
            "student": have,
            "delta": gap,
            "gap": gap,
            "status": status,
            "priority": priority,
            "category": "technical" if skill in profile["technical"] else "soft",
        })

    # Sort gaps: High priority first, then Medium, then Low, then Met
    p_order = {"High": 0, "Medium": 1, "Low": 2, "Met": 3}
    rows.sort(key=lambda x: (p_order[x["priority"]], -x["gap"]))

    readiness = round((total_satisfied / total_needed * 100) if total_needed > 0 else 0, 1)
    readiness = min(100.0, max(0.0, readiness))
    
    gap_skills_count = high_count + medium_count + low_count
    summary = f"{gap_skills_count} skill gaps ({high_count} High, {medium_count} Medium, {low_count} Low priority) vs {career_goal} requirements."

    return {
        "career_goal": career_goal,
        "required": required,
        "rows": rows,
        "readiness": readiness,
        "overall_readiness_score": readiness,
        "high_priority_count": high_count,
        "medium_priority_count": medium_count,
        "low_priority_count": low_count,
        "met_count": met_count,
        "gap_score": round(max(0.0, 100.0 - readiness), 1),
        "summary": summary,
    }


# =========================================================================
# ML / CONTENT-BASED SIMILARITY MODULE
# =========================================================================

def _pure_python_cosine_sim(text1: str, text2: str) -> float:
    """Pure-python fallback TF-IDF cosine similarity."""
    def tokenize(txt):
        return re.findall(r"\b[a-z0-9+#.-]{2,}\b", txt.lower())
    words1 = tokenize(text1)
    words2 = tokenize(text2)
    if not words1 or not words2:
        return 0.50
    vocab = list(set(words1 + words2))
    v1 = [words1.count(w) for w in vocab]
    v2 = [words2.count(w) for w in vocab]
    dot = sum(a * b for a, b in zip(v1, v2))
    mag1 = math.sqrt(sum(a * a for a in v1))
    mag2 = math.sqrt(sum(b * b for b in v2))
    if mag1 == 0 or mag2 == 0:
        return 0.50
    return dot / (mag1 * mag2)


def compute_content_similarity(student_profile_text: str, item_text: str) -> float:
    """
    Computes text similarity (0-100) between student profile representation
    and opportunity/course/project text using Scikit-Learn TF-IDF or pure-python fallback.
    """
    if not student_profile_text.strip() or not item_text.strip():
        return 60.0
    if SKLEARN_AVAILABLE:
        try:
            vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=500)
            tfidf_matrix = vec.fit_transform([student_profile_text, item_text])
            sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            # Rescale square-root of cosine similarity to 0-100 scale
            pct = round(min(98.0, max(15.0, (float(sim) ** 0.5) * 100)), 1)
            return pct
        except Exception:
            pass
    raw = _pure_python_cosine_sim(student_profile_text, item_text)
    return round(min(98.0, max(15.0, (float(raw) ** 0.5) * 100)), 1)


# =========================================================================
# MATCHING ENGINE (PHASE 3 & PHASE 5)
# =========================================================================

def _skill_compat(score_map: Dict[str, float], required_skills: List[str], skill_levels: Dict[str, float]):
    if not required_skills:
        return 75.0, [], [], []
    checks = []
    satisfied = []
    missing = []
    parts = []
    
    for name in required_skills:
        need = float(skill_levels.get(name, 65))
        have = skill_value(score_map, name)
        ratio = min(1.0, have / need) if need > 0 else 1.0
        parts.append(ratio * 100)
        ok = have >= need
        gap = max(0, round(need - have, 1))
        
        chk = {
            "skill": name,
            "have": round(have),
            "need": round(need),
            "gap": gap,
            "ok": ok,
        }
        checks.append(chk)
        if ok:
            satisfied.append(chk)
        else:
            missing.append(chk)

    # Sort missing by highest gap
    missing.sort(key=lambda x: x["gap"], reverse=True)
    compat_score = round(sum(parts) / len(parts), 1) if parts else 70.0
    return compat_score, checks, satisfied, missing


def _education_score(degree: str, min_qualification: str) -> Tuple[float, bool, str]:
    d = (degree or "").lower()
    q = (min_qualification or "").lower()
    if not q or "any" in q:
        return 90.0, True, "Open to all degrees"
    if "b.tech" in d or "b.e" in d:
        if "b." in q or "graduate" in q or "b.tech" in q or "stem" in q:
            return 95.0, True, f"Eligible: {degree} satisfies {min_qualification}"
        return 80.0, True, f"Degree {degree} matches requirement {min_qualification}"
    if any(deg in d for deg in ["bca", "mca", "b.sc", "m.sc", "m.tech"]):
        if any(deg in q for deg in ["bca", "mca", "b.sc", "m.sc", "graduate"]):
            return 90.0, True, f"Eligible: {degree} satisfies {min_qualification}"
        return 75.0, True, f"Degree {degree} accepted"
    return 60.0, False, f"Qualification {min_qualification} may require additional equivalence for {degree or 'None'}"


def _career_score(career_goal: str, title: str, description: str, keywords: List[str]) -> float:
    blob = f"{title} {description}".lower()
    goal = (career_goal or "").lower()
    if goal and any(k in blob for k in goal.split()):
        return 95.0
    if any(k in blob for k in keywords):
        return 88.0
    if career_goal:
        return 50.0
    return 60.0


def compute_match(student, score_map: Dict[str, float], opportunity, n_projects: int = 0, n_certs: int = 0, career_keywords: List[str] = None) -> Dict[str, Any]:
    """
    Intelligent Hybrid Matching Engine (Phase 3 & Phase 5).
    Combines transparent multi-factor weighted scoring + TF-IDF cosine similarity.
    """
    career_keywords = career_keywords or []
    skill_levels = opportunity.skill_levels or {}
    required = opportunity.required_skills or []
    
    # 1. Skill compatibility (40%)
    skill_s, checks, satisfied, missing = _skill_compat(score_map, required, skill_levels)

    # 2. Education match (20%)
    edu_s, is_eligible, edu_msg = _education_score(student.degree if student else "", opportunity.min_qualification)

    # 3. Career alignment (15%)
    profile = ROLE_REQUIREMENTS.get((student.career_goal if student else "") or "Data Analyst", ROLE_REQUIREMENTS["Data Analyst"])
    kws = list(career_keywords) + profile.get("keywords", [])
    car_s = _career_score(student.career_goal if student else "", opportunity.title, opportunity.description or "", kws)

    # 4. Projects (10%) & Certifications (10%)
    proj_s = min(100.0, 45 + n_projects * 18)
    cert_s = min(100.0, 45 + n_certs * 18)

    # 5. Soft skills (5%)
    soft_names = ["Communication", "Teamwork", "Problem Solving", "Leadership", "Time Management"]
    soft_vals = [skill_value(score_map, n) for n in soft_names]
    soft_s = round(sum(soft_vals) / len(soft_vals), 1) if soft_vals else 65.0

    # Multi-factor weighted baseline score
    weighted_total = (
        WEIGHTS["skills"] * skill_s
        + WEIGHTS["education"] * edu_s
        + WEIGHTS["career"] * car_s
        + WEIGHTS["projects"] * proj_s
        + WEIGHTS["certs"] * cert_s
        + WEIGHTS["soft"] * soft_s
    )

    # 6. ML / Content-Based Vector Similarity
    student_profile_text = f"Student career goal {student.career_goal if student else ''}. Degree: {student.degree if student else ''} {student.branch if student else ''}. Skills: {' '.join([f'{k} '*int(v/20) for k, v in score_map.items() if v >= 40])}. About: {student.about if student else ''}"
    opp_text = f"{opportunity.title} {opportunity.opp_type} {opportunity.industry_sector} {opportunity.description} Requirements: {' '.join(required)} {opportunity.min_qualification}"
    cosine_sim = compute_content_similarity(student_profile_text, opp_text)

    # Hybrid Score (70% multi-factor weighted + 30% ML content-based cosine similarity)
    hybrid_score = round(0.70 * weighted_total + 0.30 * cosine_sim, 1)
    final_score = round(min(98.0, max(15.0, hybrid_score)), 1)

    # Generate explainable reasons & checklists
    reasons = []
    for c in checks:
        if c["ok"]:
            reasons.append(f"✓ {c['skill']} requirement satisfied ({c['have']}% ≥ {c['need']}%)")
        else:
            reasons.append(f"⚠ {c['skill']} proficiency below required level ({c['have']}% < {c['need']}%)")
            
    if is_eligible:
        reasons.append(f"✓ Eligibility: {edu_msg}")
    else:
        reasons.append(f"⚠ Eligibility: {edu_msg}")
        
    if car_s >= 85:
        reasons.append("✓ Career alignment: Matches your career aspiration")
    elif student and student.career_goal:
        reasons.append("⚠ Career alignment: Partially aligned with your stated goal")

    skills_to_improve = [
        {"skill": m["skill"], "current": m["have"], "required": m["need"], "gap": m["gap"], "priority": "High" if m["gap"] >= 25 else "Medium"}
        for m in missing
    ]

    return {
        "score": final_score,
        "match_percentage": int(round(final_score)),
        "weighted_score": round(weighted_total, 1),
        "content_similarity": cosine_sim,
        "algorithm": "Hybrid (70% Multi-Factor Competency + 30% TF-IDF Cosine Similarity)",
        "breakdown": {
            "skill_compatibility": skill_s,
            "education": edu_s,
            "career_alignment": car_s,
            "career_interest": car_s,
            "projects": proj_s,
            "certifications": cert_s,
            "soft_skills": soft_s,
        },
        "matching_skills": [c["skill"] for c in satisfied],
        "missing_skills": [c["skill"] for c in missing],
        "skills_to_improve": skills_to_improve,
        "eligibility": {
            "eligible": is_eligible,
            "details": edu_msg,
        },
        "checks": checks,
        "reasons": reasons,
        "blurb": f"{int(round(final_score))}% Match (Skills {int(round(skill_s))}%, Edu {int(round(edu_s))}%, Career {int(round(car_s))}%): " + "; ".join(reasons[:3]),
    }


def recommend(score_map: Dict[str, float], career_goal: str, courses, certifications, projects, opportunities, student, n_projects: int, n_certs: int) -> Dict[str, Any]:
    """
    Phase 3 — Intelligent Career Recommendation Service.
    Recommends career roles, skills to learn, courses, certifications, projects, internships, jobs.
    Uses hybrid scoring and content vectorization.
    """
    goal = career_goal or "Data Analyst"
    profile = ROLE_REQUIREMENTS.get(goal, ROLE_REQUIREMENTS["Data Analyst"])
    gaps = analyze_gaps(score_map, goal)
    
    # Priority skills needing immediate improvement
    gap_skills = [r["skill"] for r in gaps["rows"] if r["priority"] in ("High", "Medium", "Low")]
    high_priority_gaps = [r["skill"] for r in gaps["rows"] if r["priority"] == "High"]
    target_skills_to_learn = high_priority_gaps if high_priority_gaps else gap_skills

    # Rank suitable career roles across all known roles
    role_recommendations = []
    for r_name, r_prof in ROLE_REQUIREMENTS.items():
        r_gaps = analyze_gaps(score_map, r_name)
        role_recommendations.append({
            "title": r_name,
            "readiness": r_gaps["readiness"],
            "match": r_gaps["readiness"],
            "high_gaps": r_gaps["high_priority_count"],
            "is_current_goal": r_name == goal,
            "why": f"{r_gaps['readiness']}% readiness score with {r_gaps['met_count']} satisfied requirements."
        })
    role_recommendations.sort(key=lambda x: x["readiness"], reverse=True)

    # Helper for catalog relevance
    def item_relevance(item_skills, item_text=""):
        # Overlap with current high gaps gets 3x, any gap gets 2x, role skill gets 1x
        item_skills_set = set(item_skills or [])
        score = 0
        for s in item_skills_set:
            if s in high_priority_gaps:
                score += 30
            elif s in gap_skills:
                score += 20
            elif s in profile["technical"]:
                score += 10
        # Cosine text similarity if text is provided
        if item_text and SKLEARN_AVAILABLE:
            txt_sim = compute_content_similarity(" ".join(gap_skills + [goal]), item_text)
            score += txt_sim * 0.2
        return score

    # Courses
    rec_courses = sorted(courses, key=lambda c: item_relevance(c.skills, c.title), reverse=True)[:5]
    # Certifications
    rec_certs = sorted(certifications, key=lambda c: item_relevance(c.skills, c.title), reverse=True)[:4]
    # Projects
    rec_projects = sorted(projects, key=lambda p: item_relevance(p.skills, p.title + " " + (p.description or "")), reverse=True)[:4]

    # Rank opportunities
    ranked_opps = []
    for opp in opportunities:
        m = compute_match(student, score_map, opp, n_projects, n_certs)
        boost = 6 if any(t in (opp.title or "").lower() for t in [x.lower() for x in profile.get("intern_titles", [])]) else 0
        ranked_opps.append((m["score"] + boost, opp, m))
        
    ranked_opps.sort(key=lambda x: x[0], reverse=True)

    internships = [x for x in ranked_opps if x[1].opp_type == "internship"][:5]
    jobs = [x for x in ranked_opps if x[1].opp_type in ("job", "apprenticeship")][:4]

    headline = f"Based on your profile, you are {gaps['readiness']}% ready for {goal} roles."
    
    return {
        "headline": headline,
        "career_goal": goal,
        "readiness_pct": gaps["readiness"],
        "gap_skills": gap_skills,
        "learn": profile.get("learn", []),
        "target_skills_to_learn": target_skills_to_learn,
        "suitable_roles": role_recommendations[:4],
        "roles": role_recommendations[:4],
        "courses": [
            {
                "id": c.id,
                "title": c.title,
                "provider": c.provider,
                "duration": c.duration,
                "skills": c.skills,
                "why": f"Addresses gap in {', '.join(set(c.skills or []) & set(gap_skills)) if set(c.skills or []) & set(gap_skills) else 'core competencies'}"
            }
            for c in rec_courses
        ],
        "certifications": [
            {
                "id": c.id,
                "title": c.title,
                "issuer": c.issuer,
                "skills": c.skills,
                "why": f"Industry validation for {', '.join(c.skills or [])}"
            }
            for c in rec_certs
        ],
        "projects": [
            {
                "id": p.id,
                "title": p.title,
                "description": p.description,
                "skills": p.skills,
                "why": f"Hands-on project targeting {', '.join(p.skills or [])}"
            }
            for p in rec_projects
        ],
        "internships": [
            {
                "id": o.id,
                "title": o.title,
                "company": o.industry.company_name if o.industry else "Industry Partner",
                "match": m["score"],
                "match_percentage": m["match_percentage"],
                "breakdown": m["breakdown"],
                "matching_skills": m["matching_skills"],
                "missing_skills": m["missing_skills"],
                "checks": m["checks"],
                "blurb": m["blurb"],
                "why": m["reasons"][:3]
            }
            for _, o, m in internships
        ],
        "jobs": [
            {
                "id": o.id,
                "title": o.title,
                "company": o.industry.company_name if o.industry else "Industry Partner",
                "match": m["score"],
                "match_percentage": m["match_percentage"],
                "breakdown": m["breakdown"],
                "checks": m["checks"],
                "blurb": m["blurb"]
            }
            for _, o, m in jobs
        ],
        "engine_note": "Hybrid recommendation layer active (70% Multi-Factor Competency + 30% TF-IDF Cosine Similarity) with rule-based explainability.",
    }
