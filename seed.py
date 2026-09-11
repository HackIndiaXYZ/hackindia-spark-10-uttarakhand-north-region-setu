"""
Rich realistic demo data for SkillBridge SIH-2026.
"""

from werkzeug.security import generate_password_hash
from models import (
    db, User, Student, Industry, Academician, Institution, Skill, SkillScore,
    Opportunity, Application, Course, Certification, ProjectCatalog,
    StudentProject, StudentCertification, Achievement, FacultyOpportunity,
    FacultyApplication, Notification,
)
from matching import DEMO_SKILL_SCORES, analyze_gaps


SKILL_DEFS = [
    ("Python", "technical"), ("Java", "technical"), ("C/C++", "technical"),
    ("Web Development", "technical"), ("Data Analytics", "technical"),
    ("AI/ML", "technical"), ("SQL", "technical"), ("Cloud", "technical"),
    ("Excel", "technical"), ("Data Visualization", "technical"),
    ("Communication", "soft"), ("Teamwork", "soft"),
    ("Problem Solving", "soft"), ("Leadership", "soft"), ("Time Management", "soft"),
]


def _user(email, password, name, role):
    u = User.query.filter_by(email=email).first()
    if u:
        return u
    u = User(email=email, password_hash=generate_password_hash(password), name=name, role=role)
    db.session.add(u)
    db.session.flush()
    return u


def _set_scores(student, mapping, skills):
    SkillScore.query.filter_by(student_id=student.id).delete()
    for name, score in mapping.items():
        sk = skills.get(name)
        if sk:
            db.session.add(SkillScore(student_id=student.id, skill_id=sk.id, score=float(score)))
    tech = [v for k, v in mapping.items() if k not in ("Communication", "Teamwork", "Problem Solving", "Leadership", "Time Management")]
    student.overall_skill_score = round(sum(tech) / len(tech), 1) if tech else 0
    student.assessment_completed = True
    student.profile_completion = 90
    gaps = analyze_gaps(mapping, student.career_goal or "Data Analyst")
    student.readiness_pct = gaps["readiness"]


def seed():
    # If student exists, we can re-populate or skip
    if User.query.filter_by(email="student@skillbridge.in").first():
        return False

    skills = {}
    for name, cat in SKILL_DEFS:
        s = Skill.query.filter_by(name=name).first()
        if not s:
            s = Skill(name=name, category=cat)
            db.session.add(s)
            db.session.flush()
        skills[name] = s

    # 1. Main Student: Priya Sharma
    su = _user("student@skillbridge.in", "student123", "Priya Sharma", "student")
    priya = Student(
        user_id=su.id,
        college="National Institute of Technology, Jaipur",
        degree="B.Tech",
        branch="Computer Science & Engineering",
        year="3rd Year",
        location="Jaipur",
        career_goal="Data Analyst",
        phone="+91 98765 41021",
        about="Pre-final year CSE student passionate about data analytics, SQL warehousing, and interactive BI dashboards.",
        resume_url="#",
        resume_filename="priya_sharma_resume.pdf",
        profile_completion=75,
    )
    db.session.add(priya)
    db.session.flush()

    _set_scores(priya, DEMO_SKILL_SCORES, skills)

    db.session.add(StudentProject(
        student_id=priya.id, title="Campus Placement Dashboard",
        description="Excel + Python EDA with Power BI visualization on 3 years of engineering campus placement records.",
        skills=["Python", "Excel", "Data Visualization", "SQL"], verified=True,
    ))
    db.session.add(StudentProject(
        student_id=priya.id, title="Hospital Patient Records Query Tool",
        description="Relational database schema with 15 complex SQL queries and Python analytics layer.",
        skills=["SQL", "Python", "Data Analytics"], verified=True,
    ))
    db.session.add(StudentCertification(
        student_id=priya.id, title="Python for Everybody", issuer="Coursera", year="2025", verified=True,
    ))
    db.session.add(StudentCertification(
        student_id=priya.id, title="Google Data Analytics Professional Certificate", issuer="Google", year="2025", verified=True,
    ))
    db.session.add(Achievement(
        student_id=priya.id, title="Smart India Hackathon Internal Finalist",
        detail="Built an academia-industry matching prototype using Flask and PostgreSQL.",
    ))
    db.session.add(Achievement(
        student_id=priya.id, title="Department Dean's Honor List",
        detail="Top 5% academic performance in Computer Science semester V.",
    ))

    # 2. Peer Students
    def add_peer(email, name, college, degree, branch, year, loc, about, scores, goal, projects, certs, placed=False):
        u = _user(email, "peer123", name, "student")
        st = Student(
            user_id=u.id, college=college, degree=degree, branch=branch, year=year,
            location=loc, career_goal=goal, about=about, profile_completion=92, placed=placed,
        )
        db.session.add(st)
        db.session.flush()
        _set_scores(st, scores, skills)
        for p in projects:
            db.session.add(StudentProject(student_id=st.id, **p, verified=True))
        for c in certs:
            db.session.add(StudentCertification(student_id=st.id, **c, verified=True))
        return st

    arjun = add_peer(
        "arjun@skillbridge.in", "Arjun Mehta",
        "NIT Jaipur", "B.Tech", "CSE", "4th Year", "Bengaluru",
        "Strong SQL and visualization; targeting analytics roles with high proficiency in Power BI.",
        {**DEMO_SKILL_SCORES, "Python": 88, "SQL": 86, "Excel": 84, "Data Visualization": 80, "AI/ML": 55, "Communication": 85},
        "Data Analyst",
        [{"title": "Retail Sales BI Dashboard", "description": "Power BI dashboard for retail KPIs.", "skills": ["SQL", "Excel", "Data Visualization"]}],
        [{"title": "Google Data Analytics", "issuer": "Google", "year": "2025"}],
    )

    meera = add_peer(
        "meera@skillbridge.in", "Meera Iyer",
        "NIT Jaipur", "B.Tech", "Information Technology", "3rd Year", "Hyderabad",
        "Machine learning enthusiast working on NLP and tabular feature engineering.",
        {**DEMO_SKILL_SCORES, "Python": 82, "AI/ML": 78, "Data Analytics": 74, "SQL": 65, "Cloud": 55, "Problem Solving": 80},
        "ML Engineer",
        [{"title": "Customer Churn Prediction", "description": "Random Forest and XGBoost model deployed with FastAPI.", "skills": ["Python", "AI/ML", "Data Analytics"]}],
        [{"title": "DeepLearning.AI Specialization", "issuer": "Coursera", "year": "2025"}],
    )

    kabir = add_peer(
        "kabir@skillbridge.in", "Kabir Singh",
        "NIT Jaipur", "B.Tech", "CSE", "2nd Year", "Pune",
        "Focused on algorithms, Java Spring Boot backend services, and clean database schemas.",
        {**DEMO_SKILL_SCORES, "Python": 70, "Java": 82, "C/C++": 75, "SQL": 68, "Web Development": 65, "Problem Solving": 78},
        "Software Engineer",
        [{"title": "Distributed Task Queue", "description": "Java backend with PostgreSQL and Redis.", "skills": ["Java", "SQL"]}],
        [{"title": "Oracle Certified Java Associate", "issuer": "Oracle", "year": "2024"}],
    )

    ananya = add_peer(
        "ananya@skillbridge.in", "Ananya Rao",
        "NIT Jaipur", "B.Tech", "CSE", "4th Year", "Bengaluru",
        "Placed student — Software track at TechNova. Full-stack development expert.",
        {**DEMO_SKILL_SCORES, "Python": 85, "Java": 88, "Web Development": 90, "SQL": 78, "Problem Solving": 85},
        "Software Engineer",
        [{"title": "Campus Lost & Found Platform", "description": "Full-stack web application with React and Node.js.", "skills": ["Web Development", "SQL"]}],
        [{"title": "AWS Certified Cloud Practitioner", "issuer": "AWS", "year": "2025"}],
        placed=True,
    )

    rohan = add_peer(
        "rohan@skillbridge.in", "Rohan Verma",
        "NIT Jaipur", "B.Tech", "Electronics & Communication", "3rd Year", "Gurugram",
        "Passionate about Cloud architecture, DevOps CI/CD, and AWS infrastructure.",
        {**DEMO_SKILL_SCORES, "Cloud": 80, "Python": 72, "SQL": 58, "Web Development": 60, "Problem Solving": 72},
        "Cloud Engineer",
        [{"title": "Serverless Log Aggregator", "description": "AWS Lambda + S3 pipeline for real-time log ingestion.", "skills": ["Cloud", "Python"]}],
        [{"title": "AWS Certified Solutions Architect", "issuer": "AWS", "year": "2025"}],
    )

    pooja = add_peer(
        "pooja@skillbridge.in", "Pooja Patel",
        "NIT Jaipur", "B.Tech", "Information Technology", "4th Year", "Mumbai",
        "Specializing in cybersecurity, network defense, and penetration testing.",
        {**DEMO_SKILL_SCORES, "Cloud": 70, "Python": 74, "SQL": 65, "C/C++": 68, "Problem Solving": 82},
        "Cybersecurity Analyst",
        [{"title": "Vulnerability Scanner Tool", "description": "Automated port and vulnerability scanner built in Python.", "skills": ["Python", "Cloud"]}],
        [{"title": "CompTIA Security+", "issuer": "CompTIA", "year": "2024"}],
    )

    vikram = add_peer(
        "vikram@skillbridge.in", "Vikram Joshi",
        "NIT Jaipur", "B.Tech", "CSE", "3rd Year", "Delhi NCR",
        "Full stack developer building responsive web applications with REST APIs.",
        {**DEMO_SKILL_SCORES, "Web Development": 85, "SQL": 72, "Python": 76, "Cloud": 62, "Teamwork": 80},
        "Full Stack Developer",
        [{"title": "EdTech Collaboration Portal", "description": "Responsive React frontend with Python Flask API.", "skills": ["Web Development", "Python", "SQL"]}],
        [{"title": "Meta Front-End Developer", "issuer": "Coursera", "year": "2025"}],
    )

    # 3. Industry Partners
    tn = _user("industry@technova.in", "industry123", "Neha Kapoor", "industry")
    technova = Industry(
        user_id=tn.id, company_name="TechNova Solutions", sector="IT / Product Analytics",
        location="Bengaluru", website="https://technova.example",
        about="Leading enterprise analytics and AI product studio helping Fortune 500 companies modernize data decisioning.",
    )
    db.session.add(technova)

    iw = _user("industry@insightworks.in", "industry123", "Rahul Desai", "industry")
    insight = Industry(
        user_id=iw.id, company_name="InsightWorks Consulting", sector="Consulting & BFSI",
        location="Hyderabad", website="https://insightworks.example",
        about="Global management and analytics consultancy providing end-to-end data transformation.",
    )
    db.session.add(insight)

    ql = _user("industry@quantlabs.in", "industry123", "Sana Qureshi", "industry")
    quant = Industry(
        user_id=ql.id, company_name="QuantLabs AI", sector="Data Science & ML",
        location="Pune", website="https://quantlabs.example",
        about="Applied machine learning and quantitative research lab focusing on predictive operations.",
    )
    db.session.add(quant)

    cm = _user("industry@cloudmatrix.in", "industry123", "Aditya Sen", "industry")
    cloudmatrix = Industry(
        user_id=cm.id, company_name="CloudMatrix Systems", sector="Cloud Infrastructure & DevOps",
        location="Gurugram", website="https://cloudmatrix.example",
        about="Cloud native migration and infrastructure automation solutions provider.",
    )
    db.session.add(cloudmatrix)

    cs = _user("industry@cybershield.in", "industry123", "Karan Singhania", "industry")
    cybershield = Industry(
        user_id=cs.id, company_name="CyberShield Technologies", sector="Cybersecurity",
        location="Mumbai", website="https://cybershield.example",
        about="Next-generation security operations center and enterprise threat defense firm.",
    )
    db.session.add(cybershield)

    db.session.flush()

    # 4. Opportunities
    def opp(**kwargs):
        o = Opportunity(**kwargs)
        db.session.add(o)
        db.session.flush()
        return o

    da_levels = {"Python": 70, "SQL": 75, "Excel": 70, "Power BI": 65, "Data Visualization": 65, "Communication": 70}
    
    o1 = opp(
        industry_id=technova.id, title="Data Analyst Intern", opp_type="internship",
        required_skills=["Python", "SQL", "Excel", "Data Visualization"], skill_levels=da_levels,
        min_qualification="B.Tech / B.Sc / BCA", experience="Fresher",
        location="Bengaluru", remote=False, duration="6 Months",
        description="Work with our core product analytics team on SQL warehousing, Python exploratory data analysis, and Power BI executive dashboards.",
        eligibility="Pre-final / final year STEM students. Strong SQL and Python foundation required.",
        industry_sector="IT / Product Analytics", deadline="2026-10-31",
    )

    o2 = opp(
        industry_id=insight.id, title="Business Analytics Intern", opp_type="internship",
        required_skills=["Excel", "SQL", "Communication", "Data Visualization"],
        skill_levels={"Excel": 70, "SQL": 65, "Communication": 75, "Data Visualization": 60},
        min_qualification="Any graduate programme (B.Tech, B.Sc, BCA)", experience="Fresher",
        location="Hyderabad", remote=True, duration="3 Months",
        description="Support BFSI clients with metric decks, financial data modeling, Excel dashboards, and stakeholder presentations.",
        eligibility="Strong communication skills. Proficient in Excel and SQL reporting.",
        industry_sector="Consulting & BFSI", deadline="2026-10-15",
    )

    o3 = opp(
        industry_id=quant.id, title="Junior Data Science Intern", opp_type="internship",
        required_skills=["Python", "AI/ML", "SQL", "Data Analytics"],
        skill_levels={"Python": 75, "AI/ML": 65, "SQL": 60, "Data Analytics": 65},
        min_qualification="B.Tech CSE/IT/Math or M.Sc/MCA", experience="Fresher",
        location="Pune", remote=False, duration="6 Months",
        description="Assist research scientists with feature extraction pipelines, baseline model training, and hyperparameter tuning.",
        eligibility="Python projects required. Basic machine learning course completion.",
        industry_sector="Data Science & ML", deadline="2026-11-15",
    )

    o4 = opp(
        industry_id=technova.id, title="Software Engineer Intern", opp_type="internship",
        required_skills=["Java", "Web Development", "SQL", "Problem Solving"],
        skill_levels={"Java": 70, "Web Development": 70, "SQL": 60, "Problem Solving": 70},
        min_qualification="B.Tech CSE / IT / MCA", experience="Fresher",
        location="Bengaluru", remote=False, duration="6 Months",
        description="Build scalable microservices and internal web portals using Java Spring Boot, REST APIs, and relational databases.",
        eligibility="Data structures basics and at least one full-stack web project.",
        industry_sector="IT / Product Analytics", deadline="2026-10-25",
    )

    o5 = opp(
        industry_id=technova.id, title="Associate Data Analyst", opp_type="job",
        required_skills=["Python", "SQL", "Excel", "Data Visualization", "Communication"],
        skill_levels={"Python": 75, "SQL": 80, "Excel": 75, "Data Visualization": 70, "Communication": 75},
        min_qualification="B.Tech / M.Sc / MCA", experience="0-1 years",
        location="Bengaluru", remote=False, duration="Full-time",
        description="Full-time entry-level analyst position working directly on enterprise revenue analytics and business intelligence.",
        eligibility="Graduates or graduating batch. Prior analytics internship experience preferred.",
        industry_sector="IT / Product Analytics", deadline="2026-12-15",
    )

    o6 = opp(
        industry_id=cloudmatrix.id, title="Cloud & DevOps Engineer Intern", opp_type="internship",
        required_skills=["Cloud", "Python", "SQL", "Problem Solving"],
        skill_levels={"Cloud": 70, "Python": 60, "SQL": 55, "Problem Solving": 65},
        min_qualification="B.Tech / MCA", experience="Fresher",
        location="Gurugram", remote=True, duration="6 Months",
        description="Hands-on cloud engineering role focused on AWS architecture, containerization with Docker, and CI/CD pipelines.",
        eligibility="Familiarity with AWS, Linux commands, and scripting.",
        industry_sector="Cloud Infrastructure & DevOps", deadline="2026-11-05",
    )

    o7 = opp(
        industry_id=cybershield.id, title="Security Operations Center (SOC) Intern", opp_type="internship",
        required_skills=["Cloud", "Python", "Problem Solving", "Time Management"],
        skill_levels={"Cloud": 65, "Python": 60, "Problem Solving": 70, "Time Management": 70},
        min_qualification="B.Tech / BCA / MCA", experience="Fresher",
        location="Mumbai", remote=False, duration="4 Months",
        description="Monitor security logs, analyze threat alerts, and assist senior analysts in incident investigation.",
        eligibility="Understanding of networking and basic cybersecurity concepts.",
        industry_sector="Cybersecurity", deadline="2026-10-20",
    )

    o8 = opp(
        industry_id=insight.id, title="Analytics Apprentice", opp_type="apprenticeship",
        required_skills=["Excel", "SQL", "Communication"],
        skill_levels={"Excel": 65, "SQL": 60, "Communication": 70},
        min_qualification="Diploma / B.Sc / BCA / B.Tech", experience="Fresher",
        location="Hyderabad", remote=False, duration="12 Months",
        description="National Apprenticeship Promotion Scheme (NAPS) recognized 1-year corporate analytics apprenticeship.",
        eligibility="Open to fresh graduates seeking guided corporate on-the-job training.",
        industry_sector="Consulting & BFSI", deadline="2026-10-10",
    )

    o9 = opp(
        industry_id=quant.id, title="Predictive Maintenance Live Project", opp_type="live_project",
        required_skills=["Python", "AI/ML", "Data Analytics"],
        skill_levels={"Python": 70, "AI/ML": 60, "Data Analytics": 60},
        min_qualification="Pre-final or final year STEM", experience="Fresher",
        location="Remote", remote=True, duration="8 Weeks",
        description="Industry-mentored live project analyzing sensor telemetry data for industrial anomaly prediction.",
        eligibility="Active GitHub account with at least one Python repository.",
        industry_sector="Data Science & ML", deadline="2026-09-30",
    )

    o10 = opp(
        industry_id=technova.id, title="Full Stack Developer (Graduate)", opp_type="job",
        required_skills=["Web Development", "SQL", "Python", "Problem Solving"],
        skill_levels={"Web Development": 75, "SQL": 65, "Python": 65, "Problem Solving": 70},
        min_qualification="B.Tech / MCA", experience="0-1 years",
        location="Bengaluru", remote=False, duration="Full-time",
        description="Build responsive web applications and backend services for next-generation skilling and collaboration platforms.",
        eligibility="Demonstrated full-stack project portfolio.",
        industry_sector="IT / Product Analytics", deadline="2026-12-30",
    )

    # 5. Student Applications (Rich Pipeline)
    # Priya Sharma applied to Data Analyst Intern
    app1 = Application(
        student_id=priya.id,
        opportunity_id=o1.id,
        status="shortlisted",
        cover_letter="I have built end-to-end placement analytics dashboards using Python and Power BI, and I would love to contribute to TechNova's product analytics team.",
        match_score=88.5,
        match_reasons=[
            "✓ Python requirement satisfied (75% ≥ 70%)",
            "✓ Education eligible: B.Tech in CSE",
            "✓ Career goal aligns with Data Analyst role",
            "⚠ SQL proficiency slightly below requirement (45% < 75%)"
        ],
    )
    db.session.add(app1)

    # Priya applied to Business Analytics Intern
    app2 = Application(
        student_id=priya.id,
        opportunity_id=o2.id,
        status="applied",
        cover_letter="Eager to apply my Excel modeling and communication skills in BFSI consulting at InsightWorks.",
        match_score=82.0,
        match_reasons=[
            "✓ Communication requirement satisfied (80% ≥ 75%)",
            "✓ Education eligible",
            "✓ Excel requirement satisfies baseline",
        ],
    )
    db.session.add(app2)

    # Arjun applied to Data Analyst Intern (Interview)
    app3 = Application(
        student_id=arjun.id,
        opportunity_id=o1.id,
        status="interview",
        cover_letter="Top scores in SQL and Power BI with hands-on enterprise BI projects.",
        match_score=94.0,
        match_reasons=[
            "✓ All technical requirements satisfied with high proficiency",
            "✓ Verified Google Data Analytics certification",
            "✓ Strong career alignment",
        ],
    )
    db.session.add(app3)

    # Arjun applied to Associate Data Analyst (Under Review)
    app4 = Application(
        student_id=arjun.id,
        opportunity_id=o5.id,
        status="under_review",
        cover_letter="Applying for full-time analyst position.",
        match_score=91.5,
        match_reasons=["✓ Complete technical match", "✓ Bachelor degree candidate"],
    )
    db.session.add(app4)

    # Meera applied to Junior Data Science Intern (Selected)
    app5 = Application(
        student_id=meera.id,
        opportunity_id=o3.id,
        status="selected",
        cover_letter="Passionate about machine learning feature pipelines.",
        match_score=92.0,
        match_reasons=["✓ Python & AI/ML requirements strongly met", "✓ Hands-on project portfolio"],
    )
    db.session.add(app5)

    # Kabir applied to Software Engineer Intern (Shortlisted)
    app6 = Application(
        student_id=kabir.id,
        opportunity_id=o4.id,
        status="shortlisted",
        cover_letter="Java Spring Boot developer with strong problem-solving fundamentals.",
        match_score=87.0,
        match_reasons=["✓ Java and OOP concepts validated", "✓ Problem solving rating 78%"],
    )
    db.session.add(app6)

    # Ananya placed at TechNova (Selected)
    app7 = Application(
        student_id=ananya.id,
        opportunity_id=o4.id,
        status="selected",
        cover_letter="Full stack web developer eager to join TechNova.",
        match_score=95.0,
        match_reasons=["✓ Full skill requirements satisfied", "✓ Project verified"],
    )
    db.session.add(app7)

    # 6. Academician & Institution Users
    fu = _user("faculty@college.edu", "faculty123", "Dr. Aditi Menon", "academician")
    academician = Academician(
        user_id=fu.id, designation="Associate Professor", department="Computer Science & Engineering",
        institution_name="National Institute of Technology, Jaipur",
        research_interests="Applied Machine Learning, Educational Data Mining, Curriculum Skilling Models, Industry-Academia Collaboration",
    )
    db.session.add(academician)
    db.session.flush()

    au = _user("admin@college.edu", "admin123", "Prof. R. K. Sharma", "institution")
    inst = Institution(
        user_id=au.id, institution_name="National Institute of Technology, Jaipur",
        inst_type="Institute of National Importance", location="Jaipur, Rajasthan",
    )
    db.session.add(inst)

    # 7. Courses Catalog
    courses = [
        ("Advanced SQL for Data Analysts & Warehousing", "NPTEL", ["SQL", "Data Analytics"], "8 weeks"),
        ("Power BI Desktop: Complete Dashboarding", "Microsoft Learn", ["Data Visualization", "Excel"], "4 weeks"),
        ("Data Visualization & Storytelling with Python", "Coursera", ["Data Visualization", "Python"], "5 weeks"),
        ("Excel for Business Analytics & Modeling", "edX", ["Excel", "Data Analytics"], "3 weeks"),
        ("Python Data Wrangling with Pandas & NumPy", "DataCamp", ["Python", "Data Analytics"], "6 weeks"),
        ("Supervised Machine Learning: Classification & Regression", "Coursera / Stanford Online", ["AI/ML", "Python"], "8 weeks"),
        ("AWS Certified Cloud Practitioner Essentials", "AWS Academy", ["Cloud"], "4 weeks"),
        ("Java Spring Boot Backend Architecture", "Udemy", ["Java", "Web Development", "SQL"], "8 weeks"),
        ("Applied Cybersecurity & Network Security Fundamentals", "SWAYAM", ["Cloud", "C/C++"], "12 weeks"),
        ("Modern Full Stack Web Development with React & Flask", "Coursera", ["Web Development", "Python", "SQL"], "10 weeks"),
    ]
    for t, p, sk, d in courses:
        db.session.add(Course(title=t, provider=p, skills=sk, duration=d))

    # 8. Certifications Catalog
    certs = [
        ("Microsoft Certified: Power BI Data Analyst Associate", "Microsoft", ["Data Visualization", "Excel"]),
        ("Google Data Analytics Professional Certificate", "Google", ["SQL", "Excel", "Data Analytics"]),
        ("HackerRank SQL (Intermediate & Advanced)", "HackerRank", ["SQL"]),
        ("AWS Certified Solutions Architect – Associate", "AWS", ["Cloud"]),
        ("Oracle Certified Professional: Java SE Programmer", "Oracle", ["Java"]),
        ("CompTIA Security+ Certification", "CompTIA", ["Cloud"]),
        ("Meta Professional Front-End Developer Certificate", "Meta", ["Web Development"]),
    ]
    for t, iss, sk in certs:
        db.session.add(Certification(title=t, issuer=iss, skills=sk))

    # 9. Project Catalog
    projects = [
        ("Enterprise Retail KPI & Sales Analytics Dashboard", "Build an automated end-to-end Power BI report connected to a PostgreSQL database with sales, retention, and SKU profitability metrics.", ["Excel", "Data Visualization", "SQL"]),
        ("Star-Schema Data Warehouse & Complex SQL Casebook", "Design a star-schema data mart and implement 20 business analytical queries using CTEs, window functions, and indexing.", ["SQL", "Data Analytics"]),
        ("Engineering Campus Placement Prediction Model", "Train logistic regression and random forest models on 5 years of student academic and skill data to forecast placement probability.", ["Python", "AI/ML", "Data Analytics"]),
        ("Full Stack Microservices Collaboration Portal", "Build a containerized multi-tier web application with role-based access control, REST APIs, and responsive UI.", ["Web Development", "Python", "SQL"]),
        ("Cloud-Native Automated CI/CD Deployment Pipeline", "Deploy a containerized application to AWS ECS with automated GitHub Actions, testing, and monitoring.", ["Cloud", "Python"]),
    ]
    for t, d, sk in projects:
        db.session.add(ProjectCatalog(title=t, description=d, skills=sk))

    # 10. Faculty Opportunities (All 6 SIH Categories)
    fac_opps = [
        ("Faculty Industrial Internship — Analytics & AI COE", "faculty_internship", "TechNova Solutions", "Bengaluru", "6 weeks",
         ["analytics", "sql", "ai"], "Shadow enterprise data engineering teams, work on live telemetry datasets, and co-design a university case study."),
        ("Industrial Training: Cloud Architecture for Educators", "industrial_training", "AWS Academy / CloudMatrix", "Hybrid (Jaipur/Remote)", "2 weeks",
         ["cloud", "devops"], "Hands-on cloud architecture labs, cloud credit grants, and curriculum integration workshops for engineering faculty."),
        ("AICTE ATAL FDP: Generative AI & Deep Learning in Curriculum", "fdp", "AICTE ATAL Academy", "NIT Jaipur", "5 days",
         ["ai", "ml", "python"], "Pedagogical masterclasses on integrating PyTorch and LLMs into undergraduate computer science lab courses."),
        ("State Skill Mission Consultancy: Regional Skill-Gap Dashboard", "consultancy", "State Skill Development Mission", "Jaipur / Remote", "3 months",
         ["analytics", "skilling", "data visualization"], "Paid consultancy project to design an interactive skill deficit dashboard for state technical universities."),
        ("Joint Research Collaboration: Predictive Skilling & Learning Analytics", "research", "InsightWorks Consulting", "Remote", "12 months",
         ["ml", "analytics", "research"], "Collaborative research on predictive models for internship readiness, co-authoring papers for IEEE conferences."),
        ("Industry-Mentored Student Capstone Program", "industry_project", "QuantLabs AI", "Pune / Hybrid", "1 semester",
         ["ml", "projects", "mentoring"], "Supervise student engineering teams working on production anomaly detection problems provided by industry mentors."),
        ("Industry Guest Lecture Series: Real-World Data Engineering", "guest_lecture", "TechNova Solutions", "NIT Jaipur Campus", "4 sessions",
         ["analytics", "sql", "guest lecture"], "Deliver collaborative lecture modules with corporate practitioners on production SQL and big data architectures."),
    ]
    for t, ty, org, loc, dur, tags, desc in fac_opps:
        fo = FacultyOpportunity(title=t, opp_type=ty, org=org, location=loc, duration=dur, tags=tags, description=desc)
        db.session.add(fo)
        db.session.flush()
        if ty == "faculty_internship":
            # Seed a faculty application from Dr. Aditi Menon
            db.session.add(FacultyApplication(
                academician_id=academician.id,
                faculty_opportunity_id=fo.id,
                status="submitted",
                statement_of_purpose="Interested in spending 6 weeks with the Analytics team to co-author campus case studies and incorporate industry datasets into our UG curriculum.",
            ))

    # 11. Notifications
    db.session.add(Notification(
        user_id=su.id, title="Skill Profile Generated",
        body="Your skill assessment has been scored. Review your skill gaps and AI recommendations.",
    ))
    db.session.add(Notification(
        user_id=su.id, title="Application Shortlisted!",
        body="TechNova Solutions has shortlisted your application for Data Analyst Intern.",
    ))
    db.session.add(Notification(
        user_id=tn.id, title="New High-Match Applicant",
        body="Arjun Mehta (94% match) and Priya Sharma (88% match) have applied for Data Analyst Intern.",
    ))
    db.session.add(Notification(
        user_id=fu.id, title="Faculty Internship Application Received",
        body="TechNova Solutions has received your expression of interest for the Faculty Industrial Internship.",
    ))

    db.session.commit()
    return True
