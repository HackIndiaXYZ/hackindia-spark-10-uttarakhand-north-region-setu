from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(180), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(160), nullable=False)
    role = db.Column(db.String(32), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship("Student", backref="user", uselist=False)
    industry = db.relationship("Industry", backref="user", uselist=False)
    academician = db.relationship("Academician", backref="user", uselist=False)
    institution = db.relationship("Institution", backref="user", uselist=False)


class Student(db.Model):
    __tablename__ = "students"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    college = db.Column(db.String(200), default="")
    degree = db.Column(db.String(80), default="")
    branch = db.Column(db.String(120), default="")
    year = db.Column(db.String(20), default="")
    location = db.Column(db.String(120), default="")
    career_goal = db.Column(db.String(120), default="")
    phone = db.Column(db.String(40), default="")
    about = db.Column(db.Text, default="")
    resume_url = db.Column(db.String(300), default="")
    resume_filename = db.Column(db.String(200), default="")
    parsed_resume_skills = db.Column(db.JSON, default=list)
    overall_skill_score = db.Column(db.Float, default=0)
    readiness_pct = db.Column(db.Float, default=0)
    profile_completion = db.Column(db.Integer, default=40)
    assessment_completed = db.Column(db.Boolean, default=False)
    placed = db.Column(db.Boolean, default=False)


class Industry(db.Model):
    __tablename__ = "industries"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    company_name = db.Column(db.String(200), nullable=False)
    sector = db.Column(db.String(120), default="")
    location = db.Column(db.String(120), default="")
    website = db.Column(db.String(200), default="")
    about = db.Column(db.Text, default="")


class Academician(db.Model):
    __tablename__ = "academicians"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    designation = db.Column(db.String(120), default="")
    department = db.Column(db.String(120), default="")
    institution_name = db.Column(db.String(200), default="")
    research_interests = db.Column(db.Text, default="")


class Institution(db.Model):
    __tablename__ = "institutions"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    institution_name = db.Column(db.String(200), nullable=False)
    inst_type = db.Column(db.String(80), default="Engineering College")
    location = db.Column(db.String(120), default="")


class Skill(db.Model):
    __tablename__ = "skills"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    category = db.Column(db.String(20), nullable=False)


class Assessment(db.Model):
    __tablename__ = "assessments"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    answers = db.Column(db.JSON, default=dict)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)


class SkillScore(db.Model):
    __tablename__ = "skill_scores"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id"), nullable=False)
    score = db.Column(db.Float, nullable=False)
    skill = db.relationship("Skill")


class Opportunity(db.Model):
    __tablename__ = "opportunities"
    id = db.Column(db.Integer, primary_key=True)
    industry_id = db.Column(db.Integer, db.ForeignKey("industries.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    opp_type = db.Column(db.String(40), nullable=False)
    required_skills = db.Column(db.JSON, default=list)
    skill_levels = db.Column(db.JSON, default=dict)
    min_qualification = db.Column(db.String(120), default="")
    experience = db.Column(db.String(80), default="Fresher")
    location = db.Column(db.String(120), default="")
    remote = db.Column(db.Boolean, default=False)
    duration = db.Column(db.String(80), default="")
    description = db.Column(db.Text, default="")
    eligibility = db.Column(db.String(300), default="")
    industry_sector = db.Column(db.String(120), default="")
    deadline = db.Column(db.String(40), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    industry = db.relationship("Industry")


class Application(db.Model):
    __tablename__ = "applications"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    opportunity_id = db.Column(db.Integer, db.ForeignKey("opportunities.id"), nullable=False)
    status = db.Column(db.String(40), default="applied")
    cover_letter = db.Column(db.Text, default="")
    match_score = db.Column(db.Float, default=0)
    match_reasons = db.Column(db.JSON, default=list)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    student = db.relationship("Student")
    opportunity = db.relationship("Opportunity")


class Course(db.Model):
    __tablename__ = "courses"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    provider = db.Column(db.String(120), default="")
    skills = db.Column(db.JSON, default=list)
    duration = db.Column(db.String(40), default="")
    level = db.Column(db.String(40), default="Intermediate")
    url = db.Column(db.String(300), default="#")


class Certification(db.Model):
    __tablename__ = "certifications"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    issuer = db.Column(db.String(120), default="")
    skills = db.Column(db.JSON, default=list)


class ProjectCatalog(db.Model):
    __tablename__ = "project_catalog"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    skills = db.Column(db.JSON, default=list)


class StudentProject(db.Model):
    __tablename__ = "student_projects"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    skills = db.Column(db.JSON, default=list)
    verified = db.Column(db.Boolean, default=False)


class StudentCertification(db.Model):
    __tablename__ = "student_certifications"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    issuer = db.Column(db.String(120), default="")
    year = db.Column(db.String(10), default="")
    verified = db.Column(db.Boolean, default=True)


class Achievement(db.Model):
    __tablename__ = "achievements"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    detail = db.Column(db.String(300), default="")


class FacultyOpportunity(db.Model):
    __tablename__ = "faculty_opportunities"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    opp_type = db.Column(db.String(60), nullable=False)
    org = db.Column(db.String(160), default="")
    location = db.Column(db.String(120), default="")
    duration = db.Column(db.String(80), default="")
    tags = db.Column(db.JSON, default=list)
    description = db.Column(db.Text, default="")


class FacultyApplication(db.Model):
    __tablename__ = "faculty_applications"
    id = db.Column(db.Integer, primary_key=True)
    academician_id = db.Column(db.Integer, db.ForeignKey("academicians.id"), nullable=False)
    faculty_opportunity_id = db.Column(db.Integer, db.ForeignKey("faculty_opportunities.id"), nullable=False)
    status = db.Column(db.String(40), default="submitted")
    statement_of_purpose = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    academician = db.relationship("Academician")
    opportunity = db.relationship("FacultyOpportunity")


class Notification(db.Model):
    __tablename__ = "notifications"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.String(400), default="")
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
