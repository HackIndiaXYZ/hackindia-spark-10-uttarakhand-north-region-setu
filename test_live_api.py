"""
Live verification of all API endpoints and role flows on the main seeded database.
"""
from app import app
import io

client = app.test_client()

print("--- Testing /api/health ---")
r = client.get("/api/health")
print("Health:", r.get_json())
assert r.status_code == 200

print("\n--- Testing Student Login & Dash ---")
r = client.post("/api/auth/login", json={"email": "student@skillbridge.in", "password": "student123"})
assert r.status_code == 200
user_data = r.get_json()
print("Logged in as:", user_data["name"], user_data["role"])

r = client.get("/api/student/dashboard")
assert r.status_code == 200
dash = r.get_json()
print("Dashboard Readiness:", dash["user"]["profile"]["readiness_pct"], "%")
print("Top gap skills:", dash["gaps"]["summary"])
print("Recommended internships count:", len(dash["recommendations"]["internships"]))

print("\n--- Testing Skill Gap Endpoint ---")
r = client.get("/api/student/skill-gaps?career=Data+Analyst")
assert r.status_code == 200
gaps = r.get_json()
print("Gap Engine:", gaps["summary"])
print("Sample row:", gaps["rows"][0])

print("\n--- Testing Resume Upload & Parse ---")
txt_resume = b"""
Priya Sharma
Education: B.Tech in CSE at NIT Jaipur
Skills: Python, SQL, PostgreSQL, Excel, Power BI, Web Development
Projects: Placement Analytics Dashboard in Power BI with SQL queries
"""
r = client.post("/api/student/resume/upload", data={"resume": (io.BytesIO(txt_resume), "priya_resume.txt")}, content_type="multipart/form-data")
assert r.status_code == 200
parse_data = r.get_json()
print("Resume Parse detected count:", parse_data["parsed"]["detected_count"])
print("Detected skills:", list(parse_data["parsed"]["detected_skills"].keys()))

print("\n--- Testing Resume Confirm ---")
r = client.post("/api/student/resume/confirm", json={"skills_to_update": {"SQL": 65, "Excel": 75}})
assert r.status_code == 200
conf_data = r.get_json()
print("Confirm response:", conf_data)

print("\n--- Testing Opportunities & Sorting ---")
r = client.get("/api/opportunities?sort_by=match")
assert r.status_code == 200
opps = r.get_json()["items"]
print("Top matched opp:", opps[0]["title"], "Match:", opps[0]["match"]["score"], "%")
print("Breakdown:", opps[0]["match"]["breakdown"])

print("\n--- Testing Industry Login & Candidates ---")
r = client.post("/api/auth/login", json={"email": "industry@technova.in", "password": "industry123"})
assert r.status_code == 200
r = client.get("/api/industry/dashboard")
opp_id = r.get_json()["opportunities"][0]["id"]
r = client.get(f"/api/industry/opportunities/{opp_id}/candidates")
assert r.status_code == 200
cand_data = r.get_json()
print(f"Candidates for {cand_data['opportunity']['title']}: {len(cand_data['candidates'])} ranked")
top_c = cand_data["candidates"][0]
print("Top candidate:", top_c["name"], "Match:", top_c["match"], "% Matching skills:", top_c["matching_skills"])

print("\n--- Testing Candidate Portfolio Lookup ---")
r = client.get(f"/api/student/portfolio/{top_c['student_id']}")
assert r.status_code == 200
port = r.get_json()
print("Portfolio candidate name:", port["student"]["name"], "Projects:", len(port["projects"]))

print("\n--- Testing Academician Dashboard & Apply ---")
r = client.post("/api/auth/login", json={"email": "faculty@college.edu", "password": "faculty123"})
assert r.status_code == 200
r = client.get("/api/academician/dashboard")
assert r.status_code == 200
fac_dash = r.get_json()
print("Faculty recommendations:", len(fac_dash["recommendations"]))
print("Faculty existing requests:", len(fac_dash["applications"]))

print("\n--- Testing Institution Analytics ---")
r = client.post("/api/auth/login", json={"email": "admin@college.edu", "password": "admin123"})
assert r.status_code == 200
r = client.get("/api/institution/analytics")
assert r.status_code == 200
inst = r.get_json()
print("Institution KPIs:", inst["kpis"])
print("Role-wise readiness:", inst["role_readiness"])
print("Top demanded industry skills:", inst["top_industry_skills"][:3])

print("\n=== ALL ENDPOINTS & ROLES VERIFIED SUCCESSFULLY! ===")
