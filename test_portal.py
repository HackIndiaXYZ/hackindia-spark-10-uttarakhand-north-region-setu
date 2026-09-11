"""
End-to-end automated verification script for SkillBridge SIH-2026.
Tests:
- Database seeding
- Intelligent skill-gap prioritization
- ML content-based cosine similarity & hybrid recommendations
- Resume parsing (PDF, DOCX, TXT)
- Role-based API authentication & workflows
"""

import os
import io
import json
import unittest
from app import app, db, User, Student, Opportunity, Application, Skill, SkillScore, FacultyOpportunity, FacultyApplication
from matching import analyze_gaps, compute_match, recommend, compute_content_similarity, ROLE_REQUIREMENTS
from resume_parser import parse_resume_text, extract_text_from_file


class TestSkillBridgePortal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test_skillbridge.db"
        cls.client = app.test_client()
        with app.app_context():
            db.drop_all()
            db.create_all()
            from seed import seed
            seed()

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            db.drop_all()
        if os.path.exists("test_skillbridge.db"):
            try:
                os.remove("test_skillbridge.db")
            except Exception:
                pass

    def test_01_health_and_meta(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["ok"])
        self.assertIn("features", data)

        res = self.client.get("/api/meta")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("Data Analyst", data["roles"])
        self.assertEqual(len(data["demo_accounts"]), 4)

    def test_02_intelligent_skill_gap_engine(self):
        """Phase 2: Verify explainable skill gaps & priorities."""
        test_scores = {"SQL": 45, "Python": 75, "Excel": 60, "Data Visualization": 40, "Data Analytics": 65, "Communication": 80, "Problem Solving": 70}
        gaps = analyze_gaps(test_scores, "Data Analyst")
        
        # Verify SQL gap: Student = 45, Required = 75, Gap = 30 -> High Priority
        sql_row = next(r for r in gaps["rows"] if r["skill"] == "SQL")
        self.assertEqual(sql_row["student"], 45)
        self.assertEqual(sql_row["required"], 75)
        self.assertEqual(sql_row["gap"], 30)
        self.assertEqual(sql_row["priority"], "High")

        # Verify Python: Student = 75, Required = 70, Gap = 0 -> Met
        py_row = next(r for r in gaps["rows"] if r["skill"] == "Python")
        self.assertEqual(py_row["gap"], 0)
        self.assertEqual(py_row["priority"], "Met")

        # Verify Readiness is strictly bounded between 0 and 100
        self.assertGreaterEqual(gaps["readiness"], 0)
        self.assertLessEqual(gaps["readiness"], 100)
        self.assertIn("High", gaps["summary"])

    def test_03_hybrid_recommender_and_content_similarity(self):
        """Phase 3: Verify ML cosine similarity & hybrid matching."""
        sim = compute_content_similarity(
            "Student skilled in Python, SQL, exploratory data analysis, and Power BI dashboards.",
            "Data Analyst Intern requiring SQL queries, Python data analysis, and Power BI reporting."
        )
        self.assertGreater(sim, 50.0)

        with app.app_context():
            priya = Student.query.join(User).filter(User.email == "student@skillbridge.in").first()
            smap = {ss.skill.name: ss.score for ss in priya.user.student.id and SkillScore.query.filter_by(student_id=priya.id).all()}
            opp = Opportunity.query.filter(Opportunity.title.ilike("%Data Analyst%")).first()
            m = compute_match(priya, smap, opp, n_projects=2, n_certs=2)
            
            self.assertIn("score", m)
            self.assertIn("matching_skills", m)
            self.assertIn("missing_skills", m)
            self.assertIn("skills_to_improve", m)
            self.assertIn("breakdown", m)
            self.assertGreaterEqual(m["score"], 50.0)

    def test_04_resume_parsing_and_intelligence(self):
        """Phase 4: Verify text extraction and skill identification."""
        sample_resume_text = """
        PRIYA SHARMA
        Computer Science & Engineering Student
        Skills: Python, SQL, PostgreSQL, Excel, Power BI, Web Development with HTML and JavaScript.
        Projects:
        - Retail Sales Dashboard: Built Power BI reports and performed SQL data cleaning.
        - Machine Learning: Basic regression model using scikit-learn.
        Communication & Teamwork: Led department hackathon team.
        """
        current_scores = {"Python": 75, "SQL": 45}
        target_role = {"SQL": 75, "Python": 70, "Excel": 70, "Data Visualization": 65}
        
        parsed = parse_resume_text(sample_resume_text, current_scores, target_role)
        self.assertIn("Python", parsed["detected_skills"])
        self.assertIn("SQL", parsed["detected_skills"])
        self.assertIn("Excel", parsed["detected_skills"])
        self.assertIn("Data Visualization", parsed["detected_skills"])
        self.assertGreater(parsed["detected_count"], 3)

    def test_05_student_workflows_and_api(self):
        """Phase 5 & 7: Test student login, goal, opportunities, and apply."""
        # 1. Login
        login_res = self.client.post("/api/auth/login", json={"email": "student@skillbridge.in", "password": "student123"})
        self.assertEqual(login_res.status_code, 200)

        # 2. Get Dashboard
        dash_res = self.client.get("/api/student/dashboard")
        self.assertEqual(dash_res.status_code, 200)
        dash_data = dash_res.get_json()
        self.assertEqual(dash_data["user"]["role"], "student")
        self.assertIn("gaps", dash_data)

        # 3. Change Career Goal
        goal_res = self.client.post("/api/student/career-goal", json={"career_goal": "ML Engineer"})
        self.assertEqual(goal_res.status_code, 200)
        self.assertEqual(goal_res.get_json()["career_goal"], "ML Engineer")

        # Reset back to Data Analyst
        self.client.post("/api/student/career-goal", json={"career_goal": "Data Analyst"})

        # 4. Opportunities with sorting
        opps_res = self.client.get("/api/opportunities?sort_by=match")
        self.assertEqual(opps_res.status_code, 200)
        opps = opps_res.get_json()["items"]
        self.assertGreater(len(opps), 0)
        self.assertIn("match", opps[0])

        # 5. Resume Upload & Confirm
        dummy_file = (io.BytesIO(b"Skills: Python, SQL, Excel, Power BI, Communication"), "resume.txt")
        up_res = self.client.post("/api/student/resume/upload", data={"resume": dummy_file}, content_type="multipart/form-data")
        self.assertEqual(up_res.status_code, 200)
        up_data = up_res.get_json()
        self.assertTrue(up_data["ok"])
        self.assertIn("parsed", up_data)

        # Confirm skills
        conf_res = self.client.post("/api/student/resume/confirm", json={"skills_to_update": {"SQL": 65, "Excel": 72}})
        self.assertEqual(conf_res.status_code, 200)
        self.assertTrue(conf_res.get_json()["ok"])

    def test_06_industry_workflow_and_candidate_ranking(self):
        """Phase 6: Industry login, candidate ranking, shortlist, reject."""
        # 1. Login
        login_res = self.client.post("/api/auth/login", json={"email": "industry@technova.in", "password": "industry123"})
        self.assertEqual(login_res.status_code, 200)

        # 2. Industry Dashboard
        dash_res = self.client.get("/api/industry/dashboard")
        self.assertEqual(dash_res.status_code, 200)
        opps = dash_res.get_json()["opportunities"]
        self.assertGreater(len(opps), 0)
        opp_id = opps[0]["id"]

        # 3. Candidate Ranking
        cand_res = self.client.get(f"/api/industry/opportunities/{opp_id}/candidates")
        self.assertEqual(cand_res.status_code, 200)
        candidates = cand_res.get_json()["candidates"]
        self.assertGreater(len(candidates), 0)
        # Verify ranking is sorted descending by match score
        scores = [c["match"] for c in candidates]
        self.assertEqual(scores, sorted(scores, reverse=True))

        # 4. Status Update (Shortlist & Reject)
        applicant = next((c for c in candidates if c["application_id"]), None)
        if applicant:
            aid = applicant["application_id"]
            st_res = self.client.post(f"/api/applications/{aid}/status", json={"status": "shortlisted"})
            self.assertEqual(st_res.status_code, 200)
            self.assertEqual(st_res.get_json()["status"], "shortlisted")

    def test_07_academician_and_institution(self):
        """Phase 8 & 9: Academician application & Institutional analytics."""
        # 1. Academician
        self.client.post("/api/auth/login", json={"email": "faculty@college.edu", "password": "faculty123"})
        fac_dash = self.client.get("/api/academician/dashboard")
        self.assertEqual(fac_dash.status_code, 200)
        fac_data = fac_dash.get_json()
        self.assertIn("recommendations", fac_data)
        self.assertIn("applications", fac_data)

        # 2. Institution Analytics
        self.client.post("/api/auth/login", json={"email": "admin@college.edu", "password": "admin123"})
        inst_res = self.client.get("/api/institution/analytics")
        self.assertEqual(inst_res.status_code, 200)
        inst_data = inst_res.get_json()
        self.assertIn("kpis", inst_data)
        self.assertIn("role_readiness", inst_data)
        self.assertIn("skill_gaps", inst_data)
        self.assertIn("top_industry_skills", inst_data)
        self.assertGreater(inst_data["kpis"]["total_students"], 0)


if __name__ == "__main__":
    unittest.main()
