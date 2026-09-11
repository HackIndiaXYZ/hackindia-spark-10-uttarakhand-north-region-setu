import os
import uuid
from datetime import datetime
from functools import wraps

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, session, send_from_directory
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from models import (
    db, User, Student, Industry, Academician, Institution, Skill, SkillScore,
    Assessment, Opportunity, Application, Course, Certification, ProjectCatalog,
    StudentProject, StudentCertification, Achievement, FacultyOpportunity,
    FacultyApplication, Notification,
)
from matching import (
    ASSESSMENT_QUESTIONS, DEMO_SKILL_SCORES, ROLE_REQUIREMENTS, WEIGHTS,
    analyze_gaps, compute_match, recommend, scores_from_answers, student_score_map,
    skill_value, SKILL_ALIASES,
)
from resume_parser import extract_text_from_file, parse_resume_text
from seed import seed

load_dotenv()

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "skillbridge-sih-2026")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Resume uploads directory
UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads", "resumes")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 MB max
ALLOWED_RESUME_EXTENSIONS = {"pdf", "docx", "doc", "txt"}


def resolve_db_uri():
    uri = os.getenv(
        "DATABASE_URL",
        "postgresql://skillbridge:skillbridge@localhost:5432/skillbridge",
    )
    try:
        from sqlalchemy import create_engine, text
        kwargs = {}
        if uri.startswith("postgresql"):
            kwargs["connect_args"] = {"connect_timeout": 3}
        engine = create_engine(uri, **kwargs)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        print("Using database:", uri.split("@")[-1] if "@" in uri else uri)
        return uri
    except Exception as exc:
        print("PostgreSQL not reachable:", exc)
        print("Falling back to sqlite:///skillbridge.db (same models). Start Postgres via docker compose when available.")
        return "sqlite:///skillbridge.db"


app.config["SQLALCHEMY_DATABASE_URI"] = resolve_db_uri()
CORS(app, supports_credentials=True)
db.init_app(app)


def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    return db.session.get(User, uid)


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user:
            return jsonify({"error": "Login required"}), 401
        return fn(user, *args, **kwargs)
    return wrapper


def role_required(*roles):
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = current_user()
            if not user:
                return jsonify({"error": "Login required"}), 401
            if user.role not in roles:
                return jsonify({"error": f"Access restricted to {', '.join(roles)}"}), 403
            return fn(user, *args, **kwargs)
        return wrapper
    return deco


def skill_map_for(student_id):
    rows = SkillScore.query.filter_by(student_id=student_id).all()
    return student_score_map(rows)


def refresh_student_metrics(student):
    smap = skill_map_for(student.id)
    if not smap:
        student.overall_skill_score = 0
        student.readiness_pct = 0
        return
    tech_names = [s.name for s in Skill.query.filter_by(category="technical").all()]
    tech = [smap[n] for n in tech_names if n in smap]
    student.overall_skill_score = round(sum(tech) / len(tech), 1) if tech else 0
    goal = student.career_goal or "Data Analyst"
    gaps = analyze_gaps(smap, goal)
    student.readiness_pct = gaps["readiness"]
    # Profile completion formula based on verifiable steps
    comp = 40
    if student.assessment_completed:
        comp += 25
    if student.career_goal:
        comp += 15
    if student.resume_url and student.resume_url != "#":
        comp += 10
    if StudentProject.query.filter_by(student_id=student.id).count():
        comp += 5
    if StudentCertification.query.filter_by(student_id=student.id).count():
        comp += 5
    student.profile_completion = min(100, comp)


def notify(user_id, title, body):
    db.session.add(Notification(user_id=user_id, title=title, body=body))


def public_user(user):
    payload = {"id": user.id, "email": user.email, "name": user.name, "role": user.role}
    if user.role == "student" and user.student:
        s = user.student
        payload["profile"] = {
            "id": s.id, "college": s.college, "degree": s.degree, "branch": s.branch,
            "year": s.year, "location": s.location, "career_goal": s.career_goal,
            "about": s.about, "phone": s.phone,
            "resume_url": s.resume_url,
            "resume_filename": s.resume_filename,
            "overall_skill_score": s.overall_skill_score, "readiness_pct": s.readiness_pct,
            "profile_completion": s.profile_completion,
            "assessment_completed": s.assessment_completed, "placed": s.placed,
            "parsed_resume_skills": s.parsed_resume_skills or [],
        }
    if user.role == "industry" and user.industry:
        i = user.industry
        payload["profile"] = {
            "id": i.id, "company_name": i.company_name, "sector": i.sector,
            "location": i.location, "website": i.website, "about": i.about,
        }
    if user.role == "academician" and user.academician:
        a = user.academician
        payload["profile"] = {
            "id": a.id, "designation": a.designation, "department": a.department,
            "institution_name": a.institution_name, "research_interests": a.research_interests,
        }
    if user.role == "institution" and user.institution:
        inst = user.institution
        payload["profile"] = {
            "id": inst.id, "institution_name": inst.institution_name,
            "inst_type": inst.inst_type, "location": inst.location,
        }
    return payload


def serialize_opportunity(o, student=None):
    data = {
        "id": o.id,
        "title": o.title,
        "type": o.opp_type,
        "company": o.industry.company_name if o.industry else "Industry Partner",
        "industry_id": o.industry_id,
        "required_skills": o.required_skills or [],
        "skill_levels": o.skill_levels or {},
        "min_qualification": o.min_qualification,
        "experience": o.experience,
        "location": o.location,
        "remote": o.remote,
        "duration": o.duration,
        "description": o.description,
        "eligibility": o.eligibility,
        "industry_sector": o.industry_sector,
        "deadline": o.deadline,
        "created_at": o.created_at.isoformat() if o.created_at else None,
    }
    if student:
        smap = skill_map_for(student.id)
        n_p = StudentProject.query.filter_by(student_id=student.id).count()
        n_c = StudentCertification.query.filter_by(student_id=student.id).count()
        m = compute_match(student, smap, o, n_p, n_c)
        data["match"] = m
        data["match_score"] = m["score"]
        data["matching_skills"] = m["matching_skills"]
        data["missing_skills"] = m["missing_skills"]
        data["skills_to_improve"] = m["skills_to_improve"]
        data["eligibility_info"] = m["eligibility"]
        data["reasons"] = m["reasons"]
        applied = Application.query.filter_by(student_id=student.id, opportunity_id=o.id).first()
        data["applied"] = bool(applied)
        data["application_id"] = applied.id if applied else None
        data["application_status"] = applied.status if applied else None
    return data


def serialize_application(a):
    o = a.opportunity
    steps = ["applied", "under_review", "shortlisted", "interview", "selected"]
    status = a.status
    if status == "rejected":
        current = 4
        terminal = "rejected"
    else:
        current = steps.index(status) if status in steps else 0
        terminal = None
    return {
        "id": a.id,
        "status": a.status,
        "cover_letter": a.cover_letter,
        "match_score": a.match_score,
        "match_reasons": a.match_reasons or [],
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "timeline": steps,
        "current_index": current,
        "terminal": terminal,
        "opportunity": {
            "id": o.id, "title": o.title, "type": o.opp_type,
            "company": o.industry.company_name if o.industry else "Industry Partner",
            "location": o.location,
            "duration": o.duration,
            "required_skills": o.required_skills or [],
        },
    }


# =========================================================================
# ROUTES
# =========================================================================

@app.route("/")
def index():
    return render_template("index.html")


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "engine": "skillbridge-hybrid-v2",
        "features": ["hybrid-recommender", "explainable-skill-gap", "resume-intelligence", "candidate-ranking"],
    }


@app.get("/api/meta")
def meta():
    return {
        "roles": list(ROLE_REQUIREMENTS.keys()),
        "weights": WEIGHTS,
        "questions": ASSESSMENT_QUESTIONS,
        "demo_accounts": [
            {"role": "Student (Priya Sharma)", "email": "student@skillbridge.in", "password": "student123"},
            {"role": "Industry (TechNova)", "email": "industry@technova.in", "password": "industry123"},
            {"role": "Academician (Dr. Aditi)", "email": "faculty@college.edu", "password": "faculty123"},
            {"role": "Institution (NIT Jaipur)", "email": "admin@college.edu", "password": "admin123"},
        ],
    }


# -------------------------------------------------------------------------
# AUTHENTICATION
# -------------------------------------------------------------------------

@app.post("/api/auth/login")
def login():
    body = request.get_json(force=True) or {}
    email = (body.get("email") or "").strip().lower()
    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, body.get("password") or ""):
        return jsonify({"error": "Invalid email or password"}), 401
    session["user_id"] = user.id
    return public_user(user)


@app.post("/api/auth/register")
def register():
    body = request.get_json(force=True) or {}
    email = (body.get("email") or "").strip().lower()
    role = body.get("role") or "student"
    if role not in ("student", "industry", "academician", "institution"):
        return jsonify({"error": "Invalid role"}), 400
    if not email or not body.get("password") or not body.get("name"):
        return jsonify({"error": "Name, email and password are required"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409
        
    user = User(
        email=email,
        password_hash=generate_password_hash(body["password"]),
        name=body["name"],
        role=role,
    )
    db.session.add(user)
    db.session.flush()
    
    if role == "student":
        db.session.add(Student(
            user_id=user.id,
            college=body.get("college") or "NIT Jaipur",
            degree=body.get("degree") or "B.Tech",
            branch=body.get("branch") or "CSE",
            year=body.get("year") or "3rd Year",
            location=body.get("location") or "",
        ))
    elif role == "industry":
        db.session.add(Industry(
            user_id=user.id,
            company_name=body.get("company_name") or body["name"],
            sector=body.get("sector") or "IT / Analytics",
            location=body.get("location") or "",
        ))
    elif role == "academician":
        db.session.add(Academician(
            user_id=user.id,
            designation=body.get("designation") or "Associate Professor",
            department=body.get("department") or "CSE",
            institution_name=body.get("institution_name") or "NIT Jaipur",
            research_interests=body.get("research_interests") or "",
        ))
    else:
        db.session.add(Institution(
            user_id=user.id,
            institution_name=body.get("institution_name") or body["name"],
            location=body.get("location") or "",
        ))
    db.session.commit()
    session["user_id"] = user.id
    return public_user(user), 201


@app.post("/api/auth/logout")
def logout():
    session.clear()
    return {"ok": True}


@app.get("/api/auth/me")
def me():
    user = current_user()
    if not user:
        return jsonify({"user": None})
    return {"user": public_user(user)}


@app.get("/api/notifications")
@login_required
def notifications(user):
    rows = Notification.query.filter_by(user_id=user.id).order_by(Notification.created_at.desc()).limit(15).all()
    return {"items": [{"id": n.id, "title": n.title, "body": n.body, "read": n.read, "created_at": n.created_at.isoformat()} for n in rows]}


# -------------------------------------------------------------------------
# STUDENT DASHBOARD & ASSESSMENT
# -------------------------------------------------------------------------

@app.get("/api/student/dashboard")
@role_required("student")
def student_dashboard(user):
    s = user.student
    refresh_student_metrics(s)
    db.session.commit()
    smap = skill_map_for(s.id)
    rec = None
    if s.assessment_completed:
        rec = recommend(
            smap, s.career_goal or "Data Analyst",
            Course.query.all(), Certification.query.all(), ProjectCatalog.query.all(),
            Opportunity.query.all(), s,
            StudentProject.query.filter_by(student_id=s.id).count(),
            StudentCertification.query.filter_by(student_id=s.id).count(),
        )
    apps = Application.query.filter_by(student_id=s.id).all()
    gaps = analyze_gaps(smap, s.career_goal or "Data Analyst") if s.assessment_completed else None
    
    return {
        "user": public_user(user),
        "skills": smap,
        "gaps": gaps,
        "recommendations": rec,
        "applications_count": len(apps),
        "recent_applications": [serialize_application(a) for a in apps[:3]],
        "projects": [{"id": p.id, "title": p.title, "skills": p.skills, "verified": p.verified} for p in StudentProject.query.filter_by(student_id=s.id)],
        "certifications": [{"id": c.id, "title": c.title, "issuer": c.issuer, "year": c.year} for c in StudentCertification.query.filter_by(student_id=s.id)],
        "career_goals": list(ROLE_REQUIREMENTS.keys()),
    }


@app.post("/api/student/career-goal")
@role_required("student")
def set_goal(user):
    goal = (request.get_json(force=True) or {}).get("career_goal") or "Data Analyst"
    if goal not in ROLE_REQUIREMENTS:
        return jsonify({"error": "Unknown career goal"}), 400
    user.student.career_goal = goal
    refresh_student_metrics(user.student)
    notify(user.id, "Career goal saved", f"Target role set to {goal}. Recommendations and gap analysis updated.")
    db.session.commit()
    return {"ok": True, "career_goal": goal, "readiness_pct": user.student.readiness_pct}


@app.post("/api/student/assessment")
@role_required("student")
def submit_assessment(user):
    body = request.get_json(force=True) or {}
    if body.get("demo"):
        scores = dict(DEMO_SKILL_SCORES)
        answers = {"demo": True}
    else:
        answers = body.get("answers") or {}
        scores = scores_from_answers(answers)
        if len(scores) < 8:
            return jsonify({"error": "Please answer all assessment questions."}), 400
            
    s = user.student
    db.session.add(Assessment(student_id=s.id, answers=answers))
    SkillScore.query.filter_by(student_id=s.id).delete()
    for name, val in scores.items():
        sk = Skill.query.filter_by(name=name).first()
        if not sk:
            cat = "soft" if name in ["Communication", "Teamwork", "Problem Solving", "Leadership", "Time Management"] else "technical"
            sk = Skill(name=name, category=cat)
            db.session.add(sk)
            db.session.flush()
        db.session.add(SkillScore(student_id=s.id, skill_id=sk.id, score=float(val)))
        
    s.assessment_completed = True
    if not s.career_goal:
        s.career_goal = "Data Analyst"
    refresh_student_metrics(s)
    notify(user.id, "Skill profile ready", "Assessment scored. Review your skill gaps and AI recommendations.")
    db.session.commit()
    return {"ok": True, "scores": scores, "overall": s.overall_skill_score, "readiness_pct": s.readiness_pct}


@app.get("/api/student/skill-profile")
@role_required("student")
def skill_profile(user):
    s = user.student
    smap = skill_map_for(s.id)
    tech_names = {x.name for x in Skill.query.filter_by(category="technical")}
    tech = {k: v for k, v in smap.items() if k in tech_names}
    soft = {k: v for k, v in smap.items() if k not in tech_names}
    return {
        "assessment_completed": s.assessment_completed,
        "overall": s.overall_skill_score,
        "readiness_pct": s.readiness_pct,
        "technical": tech,
        "soft": soft,
        "career_goal": s.career_goal,
        "resume_filename": s.resume_filename,
    }


@app.get("/api/student/skill-gaps")
@role_required("student")
def skill_gaps(user):
    goal = request.args.get("career") or user.student.career_goal or "Data Analyst"
    if goal in ROLE_REQUIREMENTS and goal != user.student.career_goal:
        user.student.career_goal = goal
        refresh_student_metrics(user.student)
        db.session.commit()
    smap = skill_map_for(user.student.id)
    gaps = analyze_gaps(smap, goal)
    return gaps


@app.get("/api/student/recommendations")
@role_required("student")
def student_recs(user):
    s = user.student
    if not s.assessment_completed:
        return jsonify({"error": "Complete the skill assessment first."}), 400
    rec = recommend(
        skill_map_for(s.id), s.career_goal or "Data Analyst",
        Course.query.all(), Certification.query.all(), ProjectCatalog.query.all(),
        Opportunity.query.all(), s,
        StudentProject.query.filter_by(student_id=s.id).count(),
        StudentCertification.query.filter_by(student_id=s.id).count(),
    )
    return rec


# -------------------------------------------------------------------------
# PHASE 4: RESUME INTELLIGENCE
# -------------------------------------------------------------------------

@app.post("/api/student/resume/upload")
@role_required("student")
def upload_resume(user):
    if "resume" not in request.files:
        return jsonify({"error": "No resume file provided"}), 400
    file = request.files["resume"]
    if not file or not file.filename:
        return jsonify({"error": "No file selected"}), 400
        
    orig_name = secure_filename(file.filename)
    ext = orig_name.rsplit(".", 1)[-1].lower() if "." in orig_name else ""
    if ext not in ALLOWED_RESUME_EXTENSIONS:
        return jsonify({"error": f"Invalid format .{ext}. Allowed: PDF, DOCX, TXT"}), 400
        
    safe_name = f"{user.id}_{uuid.uuid4().hex[:8]}_{orig_name}"
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], safe_name)
    file.save(save_path)
    
    # Extract text and parse skills
    text = extract_text_from_file(save_path)
    if not text.strip():
        return jsonify({"error": "Could not extract text from document. Ensure file is not password-protected or image-only."}), 400
        
    current_scores = skill_map_for(user.student.id)
    target_role = user.student.career_goal or "Data Analyst"
    role_prof = ROLE_REQUIREMENTS.get(target_role, ROLE_REQUIREMENTS["Data Analyst"])
    target_required = {**role_prof["technical"], **role_prof["soft"]}
    
    parsed = parse_resume_text(text, current_scores, target_required)
    
    # Update student record with resume link (do NOT overwrite scores yet!)
    user.student.resume_filename = orig_name
    user.student.resume_url = f"/static/uploads/resumes/{safe_name}"
    refresh_student_metrics(user.student)
    db.session.commit()
    
    return {
        "ok": True,
        "filename": orig_name,
        "resume_url": user.student.resume_url,
        "parsed": parsed,
    }


@app.post("/api/student/resume/confirm")
@role_required("student")
def confirm_resume_skills(user):
    """Safely merge student-approved resume skills into SkillScore table."""
    body = request.get_json(force=True) or {}
    skills_to_update = body.get("skills_to_update") or {}
    if not skills_to_update:
        return jsonify({"error": "No skills selected for update"}), 400
        
    s = user.student
    updated_names = []
    
    for skill_name, score in skills_to_update.items():
        score_val = max(1.0, min(100.0, float(score)))
        sk = Skill.query.filter_by(name=skill_name).first()
        if not sk:
            cat = "soft" if skill_name in ["Communication", "Teamwork", "Problem Solving", "Leadership", "Time Management"] else "technical"
            sk = Skill(name=skill_name, category=cat)
            db.session.add(sk)
            db.session.flush()
            
        existing = SkillScore.query.filter_by(student_id=s.id, skill_id=sk.id).first()
        if existing:
            existing.score = score_val
        else:
            db.session.add(SkillScore(student_id=s.id, skill_id=sk.id, score=score_val))
        updated_names.append(skill_name)
        
    s.assessment_completed = True
    s.parsed_resume_skills = list(skills_to_update.keys())
    refresh_student_metrics(s)
    notify(user.id, "Resume Skills Confirmed", f"Updated {len(updated_names)} skills from resume: {', '.join(updated_names[:4])}.")
    db.session.commit()
    
    return {
        "ok": True,
        "updated_skills": updated_names,
        "overall_skill_score": s.overall_skill_score,
        "readiness_pct": s.readiness_pct,
    }


# -------------------------------------------------------------------------
# OPPORTUNITIES & APPLICATIONS
# -------------------------------------------------------------------------

@app.get("/api/opportunities")
@login_required
def list_opportunities(user):
    q = Opportunity.query
    typ = request.args.get("type")
    loc = request.args.get("location")
    skill = request.args.get("skill")
    sector = request.args.get("industry")
    duration = request.args.get("duration")
    remote = request.args.get("remote")
    search = request.args.get("q")
    sort_by = request.args.get("sort_by") or "recent"
    
    if typ:
        q = q.filter(Opportunity.opp_type == typ)
    if loc:
        q = q.filter(Opportunity.location.ilike(f"%{loc}%"))
    if sector:
        q = q.filter(Opportunity.industry_sector.ilike(f"%{sector}%"))
    if duration:
        q = q.filter(Opportunity.duration.ilike(f"%{duration}%"))
    if remote == "true":
        q = q.filter(Opportunity.remote.is_(True))
        
    rows = q.order_by(Opportunity.created_at.desc()).all()
    
    if skill:
        rows = [o for o in rows if skill.lower() in [x.lower() for x in (o.required_skills or [])]]
    if search:
        stext = search.lower()
        rows = [
            o for o in rows
            if stext in (o.title + " " + (o.description or "") + " " + (o.industry.company_name if o.industry else "")).lower()
        ]
        
    student = user.student if user.role == "student" else None
    serialized = [serialize_opportunity(o, student) for o in rows]
    
    # Sort options
    if sort_by == "match" and student:
        serialized.sort(key=lambda x: (x.get("match") or {}).get("score", 0), reverse=True)
    elif sort_by == "title":
        serialized.sort(key=lambda x: x["title"].lower())
        
    return {
        "items": serialized,
        "filters": {
            "types": sorted({o.opp_type for o in Opportunity.query.all()}),
            "locations": sorted({o.location for o in Opportunity.query.all() if o.location}),
            "skills": sorted({sk for o in Opportunity.query.all() for sk in (o.required_skills or [])}),
            "industries": sorted({o.industry_sector for o in Opportunity.query.all() if o.industry_sector}),
            "durations": sorted({o.duration for o in Opportunity.query.all() if o.duration}),
        },
    }


@app.get("/api/opportunities/<int:oid>")
@login_required
def get_opportunity(user, oid):
    o = Opportunity.query.get_or_404(oid)
    student = user.student if user.role == "student" else None
    return serialize_opportunity(o, student)


@app.post("/api/opportunities/<int:oid>/apply")
@role_required("student")
def apply(user, oid):
    o = Opportunity.query.get_or_404(oid)
    existing = Application.query.filter_by(student_id=user.student.id, opportunity_id=oid).first()
    if existing:
        return jsonify({"error": "Already applied", "application_id": existing.id}), 409
    if not user.student.assessment_completed:
        return jsonify({"error": "Complete skill assessment before applying."}), 400
        
    body = request.get_json(force=True) or {}
    smap = skill_map_for(user.student.id)
    m = compute_match(
        user.student, smap, o,
        StudentProject.query.filter_by(student_id=user.student.id).count(),
        StudentCertification.query.filter_by(student_id=user.student.id).count(),
    )
    appn = Application(
        student_id=user.student.id,
        opportunity_id=oid,
        status="applied",
        cover_letter=body.get("cover_letter") or "",
        match_score=m["score"],
        match_reasons=m["reasons"],
    )
    db.session.add(appn)
    company = o.industry.company_name if o.industry else "Partner"
    notify(user.id, "Application submitted", f"Applied to {o.title} at {company}.")
    if o.industry and o.industry.user_id:
        notify(o.industry.user_id, "New applicant", f"{user.name} applied for {o.title} ({m['score']}% match).")
    db.session.commit()
    return {"ok": True, "application": serialize_application(appn)}, 201


@app.get("/api/student/applications")
@role_required("student")
def my_applications(user):
    rows = Application.query.filter_by(student_id=user.student.id).order_by(Application.created_at.desc()).all()
    return {"items": [serialize_application(a) for a in rows]}


# -------------------------------------------------------------------------
# DIGITAL PORTFOLIO
# -------------------------------------------------------------------------

@app.get("/api/student/portfolio")
@role_required("student")
def portfolio(user):
    return _build_portfolio(user.student, user)


@app.get("/api/student/portfolio/<int:student_id>")
@login_required
def candidate_portfolio(user, student_id):
    st = Student.query.get_or_404(student_id)
    u = db.session.get(User, st.user_id)
    return _build_portfolio(st, u)


def _build_portfolio(s, u):
    smap = skill_map_for(s.id)
    internships = []
    for a in Application.query.filter_by(student_id=s.id).all():
        internships.append({
            "title": a.opportunity.title,
            "company": a.opportunity.industry.company_name if a.opportunity.industry else "Partner",
            "status": a.status,
            "type": a.opportunity.opp_type,
        })
    return {
        "student": public_user(u),
        "skills": smap,
        "projects": [{"title": p.title, "description": p.description, "skills": p.skills, "verified": p.verified} for p in StudentProject.query.filter_by(student_id=s.id)],
        "certifications": [{"title": c.title, "issuer": c.issuer, "year": c.year, "verified": c.verified} for c in StudentCertification.query.filter_by(student_id=s.id)],
        "achievements": [{"title": a.title, "detail": a.detail} for a in Achievement.query.filter_by(student_id=s.id)],
        "internships": internships,
        "badges": _badges(s, smap),
    }


def _badges(s, smap):
    badges = []
    if s.assessment_completed:
        badges.append({"name": "Skill Assessed", "tone": "teal"})
    if smap.get("Python", 0) >= 70:
        badges.append({"name": "Python Verified", "tone": "navy"})
    if smap.get("SQL", 0) >= 70:
        badges.append({"name": "SQL Verified", "tone": "navy"})
    if s.readiness_pct >= 70:
        badges.append({"name": "Internship Ready", "tone": "gold"})
    if StudentCertification.query.filter_by(student_id=s.id, verified=True).count():
        badges.append({"name": "Certified Learner", "tone": "teal"})
    if s.placed:
        badges.append({"name": "Placed", "tone": "gold"})
    return badges


# -------------------------------------------------------------------------
# INDUSTRY DASHBOARD & CANDIDATE RANKING
# -------------------------------------------------------------------------

@app.get("/api/industry/dashboard")
@role_required("industry")
def industry_dash(user):
    ind = user.industry
    opps = Opportunity.query.filter_by(industry_id=ind.id).order_by(Opportunity.created_at.desc()).all()
    items = []
    for o in opps:
        apps = Application.query.filter_by(opportunity_id=o.id).all()
        items.append({
            **serialize_opportunity(o),
            "applicants": len(apps),
            "shortlisted": sum(1 for a in apps if a.status in ("shortlisted", "interview", "selected")),
        })
    return {"profile": public_user(user)["profile"], "opportunities": items}


@app.post("/api/industry/opportunities")
@role_required("industry")
def post_opportunity(user):
    b = request.get_json(force=True) or {}
    skills = b.get("required_skills") or []
    if isinstance(skills, str):
        skills = [x.strip() for x in skills.split(",") if x.strip()]
    levels = b.get("skill_levels") or {n: 65 for n in skills}
    o = Opportunity(
        industry_id=user.industry.id,
        title=b.get("title") or "Untitled Role",
        opp_type=b.get("opp_type") or "internship",
        required_skills=skills,
        skill_levels=levels,
        min_qualification=b.get("min_qualification") or "B.Tech",
        experience=b.get("experience") or "Fresher",
        location=b.get("location") or "Bengaluru",
        remote=bool(b.get("remote")),
        duration=b.get("duration") or "6 Months",
        description=b.get("description") or "",
        eligibility=b.get("eligibility") or "",
        industry_sector=user.industry.sector or "IT",
        deadline=b.get("deadline") or "",
    )
    db.session.add(o)
    notify(user.id, "Opportunity published", f"{o.title} is now visible on the student portal.")
    db.session.commit()
    return serialize_opportunity(o), 201


@app.get("/api/industry/opportunities/<int:oid>/candidates")
@role_required("industry")
def candidates(user, oid):
    o = Opportunity.query.get_or_404(oid)
    if o.industry_id != user.industry.id:
        return jsonify({"error": "Not authorized for this opportunity"}), 403
        
    view_filter = request.args.get("view") or "all"  # "all" or "applicants"
    students = Student.query.filter_by(assessment_completed=True).all()
    ranked = []
    
    for st in students:
        appn = Application.query.filter_by(student_id=st.id, opportunity_id=o.id).first()
        if view_filter == "applicants" and not appn:
            continue
            
        u = db.session.get(User, st.user_id)
        smap = skill_map_for(st.id)
        n_p = StudentProject.query.filter_by(student_id=st.id).count()
        n_c = StudentCertification.query.filter_by(student_id=st.id).count()
        m = compute_match(st, smap, o, n_p, n_c)
        
        required = o.required_skills or []
        missing = [sk for sk in required if skill_value(smap, sk) < float((o.skill_levels or {}).get(sk, 65))]
        matching = [sk for sk in required if skill_value(smap, sk) >= float((o.skill_levels or {}).get(sk, 65))]
        
        ranked.append({
            "student_id": st.id,
            "user_id": u.id,
            "name": u.name,
            "education": f"{st.degree} {st.branch}, {st.year}",
            "college": st.college,
            "career_goal": st.career_goal,
            "match": m["score"],
            "match_percentage": m["match_percentage"],
            "breakdown": m["breakdown"],
            "reasons": m["reasons"],
            "required_skills": required,
            "matching_skills": matching,
            "missing_skills": missing,
            "skills": smap,
            "projects": [{"title": p.title, "skills": p.skills} for p in StudentProject.query.filter_by(student_id=st.id)],
            "applied": bool(appn),
            "application_id": appn.id if appn else None,
            "status": appn.status if appn else "not_applied",
            "cover_letter": appn.cover_letter if appn else "",
        })
        
    ranked.sort(key=lambda x: x["match"], reverse=True)
    return {
        "opportunity": serialize_opportunity(o),
        "candidates": ranked,
        "total_applicants": sum(1 for c in ranked if c["applied"]),
        "total_candidates": len(ranked),
    }


@app.post("/api/applications/<int:aid>/status")
@role_required("industry")
def set_status(user, aid):
    a = Application.query.get_or_404(aid)
    if a.opportunity.industry_id != user.industry.id:
        return jsonify({"error": "Not authorized for this application"}), 403
        
    status = (request.get_json(force=True) or {}).get("status")
    allowed = {"under_review", "shortlisted", "interview", "selected", "rejected", "applied"}
    if status not in allowed:
        return jsonify({"error": "Invalid status"}), 400
        
    a.status = status
    a.updated_at = datetime.utcnow()
    stu_user = db.session.get(User, a.student.user_id)
    notify(stu_user.id, "Application Update", f"Your application for {a.opportunity.title} is now: {status.replace('_', ' ').title()}.")
    
    if status == "selected":
        a.student.placed = True
        refresh_student_metrics(a.student)
    elif status == "rejected" and a.student.placed:
        # If rejected, ensure placement is calculated accurately
        other_selected = Application.query.filter(Application.student_id == a.student.id, Application.id != a.id, Application.status == "selected").first()
        a.student.placed = bool(other_selected)
        
    db.session.commit()
    return serialize_application(a)


# -------------------------------------------------------------------------
# ACADEMICIAN MODULE (PHASE 9)
# -------------------------------------------------------------------------

@app.get("/api/academician/dashboard")
@role_required("academician")
def academician_dash(user):
    a = user.academician
    interests = [t.strip().lower() for t in (a.research_interests or "").replace(",", " ").split() if t.strip()]
    rows = FacultyOpportunity.query.all()
    scored = []
    
    for r in rows:
        tags = [t.lower() for t in (r.tags or [])]
        blob = f"{r.title} {r.description} {' '.join(tags)}".lower()
        hit = sum(1 for i in interests if i in blob) + sum(2 for t in tags if t in interests)
        scored.append((hit, r))
        
    scored.sort(key=lambda x: x[0], reverse=True)
    
    # Check existing applications
    my_apps = {fa.faculty_opportunity_id: fa.status for fa in FacultyApplication.query.filter_by(academician_id=a.id).all()}
    
    def pack(r, rec=False):
        return {
            "id": r.id, "title": r.title, "type": r.opp_type, "org": r.org,
            "location": r.location, "duration": r.duration, "tags": r.tags,
            "description": r.description, "recommended": rec,
            "applied": r.id in my_apps,
            "application_status": my_apps.get(r.id),
        }
        
    recs = [pack(r, True) for h, r in scored if h > 0][:5]
    grouped = {}
    for r in rows:
        grouped.setdefault(r.opp_type, []).append(pack(r, r.id in {x["id"] for x in recs}))
        
    applications = [
        {
            "id": app.id,
            "opportunity_id": app.faculty_opportunity_id,
            "title": app.opportunity.title,
            "org": app.opportunity.org,
            "type": app.opportunity.opp_type,
            "status": app.status,
            "sop": app.statement_of_purpose,
            "created_at": app.created_at.isoformat() if app.created_at else None,
        }
        for app in FacultyApplication.query.filter_by(academician_id=a.id).order_by(FacultyApplication.created_at.desc()).all()
    ]
    
    return {
        "profile": public_user(user)["profile"],
        "recommendations": recs,
        "grouped": grouped,
        "applications": applications,
    }


@app.post("/api/academician/opportunities/<int:oid>/apply")
@role_required("academician")
def faculty_apply(user, oid):
    fo = FacultyOpportunity.query.get_or_404(oid)
    a = user.academician
    existing = FacultyApplication.query.filter_by(academician_id=a.id, faculty_opportunity_id=oid).first()
    if existing:
        return jsonify({"error": "Expression of interest already submitted", "id": existing.id}), 409
        
    body = request.get_json(force=True) or {}
    sop = body.get("statement_of_purpose") or ""
    
    appn = FacultyApplication(
        academician_id=a.id,
        faculty_opportunity_id=oid,
        status="submitted",
        statement_of_purpose=sop,
    )
    db.session.add(appn)
    notify(user.id, "Expression of Interest Submitted", f"Applied for {fo.title} at {fo.org}.")
    db.session.commit()
    
    return {
        "ok": True,
        "application": {
            "id": appn.id,
            "status": appn.status,
            "title": fo.title,
            "org": fo.org,
        }
    }, 201


@app.get("/api/academician/applications")
@role_required("academician")
def faculty_applications(user):
    a = user.academician
    apps = FacultyApplication.query.filter_by(academician_id=a.id).order_by(FacultyApplication.created_at.desc()).all()
    return {
        "items": [
            {
                "id": x.id,
                "opportunity_id": x.faculty_opportunity_id,
                "title": x.opportunity.title,
                "org": x.opportunity.org,
                "type": x.opportunity.opp_type,
                "status": x.status,
                "sop": x.statement_of_purpose,
                "created_at": x.created_at.isoformat() if x.created_at else None,
            }
            for x in apps
        ]
    }


# -------------------------------------------------------------------------
# INSTITUTION ANALYTICS (PHASE 8)
# -------------------------------------------------------------------------

@app.get("/api/institution/analytics")
@role_required("institution")
def analytics(user):
    students = Student.query.all()
    total = len(students)
    assessed = sum(1 for s in students if s.assessment_completed)
    ready = sum(1 for s in students if s.readiness_pct >= 70)
    placed = sum(1 for s in students if s.placed)
    internships = Opportunity.query.filter_by(opp_type="internship").count()
    partners = Industry.query.count()
    apps = Application.query.all()
    
    # Dynamic skill distribution from SkillScore table
    scores = SkillScore.query.join(Skill).all()
    dist = {}
    for row in scores:
        dist.setdefault(row.skill.name, []).append(row.score)
    avg_dist = {k: round(sum(v) / len(v), 1) for k, v in dist.items()}
    
    # Dynamic demand from active opportunities
    demand = {}
    for o in Opportunity.query.all():
        for sk in o.required_skills or []:
            demand[sk] = demand.get(sk, 0) + 1
    top_demand = sorted(demand.items(), key=lambda x: x[1], reverse=True)[:8]
    mx = max([n for _, n in top_demand], default=1)
    top_industry_skills = [{"skill": k, "pct": round(100 * n / mx, 1), "postings": n} for k, n in top_demand]
    
    # Dynamic Campus Skill Gaps aggregated across all assessed students
    gap_accum = {}
    gap_n = {}
    high_priority_flags = 0
    for s in students:
        if not s.assessment_completed:
            continue
        g = analyze_gaps(skill_map_for(s.id), s.career_goal or "Data Analyst")
        for r in g["rows"]:
            if r["priority"] in ("High", "Medium", "Low"):
                gap_accum[r["skill"]] = gap_accum.get(r["skill"], 0) + r["delta"]
                gap_n[r["skill"]] = gap_n.get(r["skill"], 0) + 1
                if r["priority"] == "High":
                    high_priority_flags += 1
                    
    skill_gaps = sorted(
        [{"skill": k, "students": gap_n[k], "avg_delta": round(gap_accum[k] / gap_n[k], 1)} for k in gap_n],
        key=lambda x: x["students"], reverse=True,
    )
    
    # Role-Wise Readiness breakdown (Phase 8)
    role_readiness = {}
    for role_name in ROLE_REQUIREMENTS:
        role_scores = []
        for s in students:
            if s.assessment_completed:
                g = analyze_gaps(skill_map_for(s.id), role_name)
                role_scores.append(g["readiness"])
        role_readiness[role_name] = round(sum(role_scores) / len(role_scores), 1) if role_scores else 0.0
        
    intern_apps = [a for a in apps if a.opportunity.opp_type == "internship"]
    status_counts = {}
    for a in apps:
        status_counts[a.status] = status_counts.get(a.status, 0) + 1
        
    return {
        "kpis": {
            "total_students": total,
            "assessments_completed": assessed,
            "internship_ready": ready,
            "placed": placed,
            "active_internships": internships,
            "industry_partners": partners,
            "open_skill_gaps": sum(x["students"] for x in skill_gaps),
            "high_priority_gaps": high_priority_flags,
            "avg_readiness": round(sum(s.readiness_pct for s in students if s.assessment_completed) / max(1, assessed), 1),
        },
        "skill_distribution": avg_dist,
        "top_industry_skills": top_industry_skills,
        "skill_gaps": skill_gaps,
        "role_readiness": role_readiness,
        "internship_participation": {
            "applications": len(intern_apps),
            "unique_students": len({a.student_id for a in intern_apps}),
        },
        "placement_readiness": {
            "ready": ready,
            "developing": max(0, assessed - ready),
            "not_assessed": total - assessed,
        },
        "application_pipeline": status_counts,
        "demand_trends": [
            {"month": "Apr", "postings": 4},
            {"month": "May", "postings": 6},
            {"month": "Jun", "postings": 7},
            {"month": "Jul", "postings": 9},
            {"month": "Aug", "postings": 12},
            {"month": "Sep", "postings": Opportunity.query.count()},
        ],
        "institution": public_user(user)["profile"],
    }


# -------------------------------------------------------------------------
# DATABASE INITIALIZATION
# -------------------------------------------------------------------------

def init_db(force_reseed=False):
    with app.app_context():
        db.create_all()
        if force_reseed:
            print("Force reseeding SkillBridge database...")
            # Drop and re-create all tables
            db.drop_all()
            db.create_all()
            seed()
            print("Database reseeded with rich SIH demo dataset.")
        else:
            if seed():
                print("Seeded SkillBridge demo data.")
            else:
                print("Database ready.")


if __name__ == "__main__":
    import sys
    force = "--reseed" in sys.argv
    init_db(force_reseed=force)
    app.run(debug=os.getenv("FLASK_DEBUG", "1") == "1", host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
