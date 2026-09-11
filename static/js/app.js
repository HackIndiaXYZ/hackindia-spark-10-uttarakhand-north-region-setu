const $ = (sel, el = document) => el.querySelector(sel);
const appEl = $("#app");
const state = {
  user: null,
  notifications: [],
  meta: null,
  _oppFilters: {},
  _candFilter: "all",
  _facultyTab: "browse",
};

let activeCharts = [];
function wipeCharts() {
  activeCharts.forEach(c => { try { c.destroy(); } catch(e) {} });
  activeCharts = [];
}

function toast(msg) {
  const t = $("#toast");
  t.textContent = msg;
  t.classList.remove("hidden");
  setTimeout(() => t.classList.add("hidden"), 3000);
}

function openModal(html) {
  const m = $("#modal");
  m.innerHTML = `<div class="modal-card">${html}</div>`;
  m.classList.remove("hidden");
  m.onclick = (e) => { if (e.target === m) closeModal(); };
}

function closeModal() {
  $("#modal").classList.add("hidden");
  $("#modal").innerHTML = "";
}

async function api(path, opts = {}) {
  const isForm = opts.body instanceof FormData;
  const headers = { ...(opts.headers || {}) };
  if (!isForm && opts.body) {
    headers["Content-Type"] = "application/json";
  }
  const res = await fetch(path, {
    credentials: "include",
    headers,
    ...opts,
    body: isForm ? opts.body : (opts.body ? JSON.stringify(opts.body) : undefined),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || "Request failed");
  return data;
}

function hash() {
  return location.hash.replace(/^#/, "") || "/";
}

function go(path) {
  location.hash = path;
}

const studentNav = [
  ["#/student", "Dashboard"],
  ["#/student/assessment", "Skill Assessment"],
  ["#/student/gaps", "Skill Gap Analysis"],
  ["#/student/recommendations", "AI Recommendations"],
  ["#/student/opportunities", "Internships & Jobs"],
  ["#/student/applications", "My Applications"],
  ["#/student/portfolio", "Digital Portfolio"],
];
const industryNav = [
  ["#/industry", "Dashboard"],
  ["#/industry/post", "Post Opportunity"],
  ["#/industry/candidates", "Candidate Matching"],
];
const facultyNav = [
  ["#/academician", "Faculty Opportunities & Requests"],
];
const instNav = [
  ["#/institution", "Institutional Analytics"],
];

function navFor(role) {
  if (role === "student") return studentNav;
  if (role === "industry") return industryNav;
  if (role === "academician") return facultyNav;
  return instNav;
}

function homeFor(role) {
  return { student: "#/student", industry: "#/industry", academician: "#/academician", institution: "#/institution" }[role] || "#/";
}

function shell(content) {
  const u = state.user;
  const links = navFor(u.role).map(([href, label]) => {
    const active = location.hash === href || (href !== homeFor(u.role) && location.hash.startsWith(href));
    return `<a class="side-link ${active ? "active" : ""}" href="${href}">${label}</a>`;
  }).join("");
  const n = state.notifications.filter((x) => !x.read).length;
  return `
    <div class="shell">
      <aside class="sidebar">
        <a class="brand" href="#/" style="color:#fff;margin-bottom:18px">
          <span class="mark">S</span><span class="brand-word">SkillBridge</span>
        </a>
        <div class="muted" style="padding:0 12px 10px;font-size:12px;color:#9bb;text-transform:capitalize">${u.role} Portal</div>
        ${links}
        <a class="side-link" href="#/" id="logout-link" style="margin-top:auto">Sign out</a>
      </aside>
      <div class="main">
        <div class="topbar">
          <div>
            <div class="kicker">${u.role.toUpperCase()}</div>
            <h2 style="margin:4px 0 0">${u.name}</h2>
          </div>
          <div class="bell">
            <button class="btn btn-ghost btn-sm" id="bell-btn">Notifications</button>
            ${n ? `<span class="badge-n">${n}</span>` : ""}
          </div>
        </div>
        ${content}
      </div>
    </div>`;
}

function landing() {
  return `
    <nav class="nav">
      <a class="brand" href="#/"><span class="mark">S</span><span class="brand-word">SkillBridge</span></a>
      <div class="nav-actions">
        <a class="btn btn-ghost" href="#/login">Login</a>
        <a class="btn btn-primary" href="#/register">Register</a>
      </div>
    </nav>
    <section class="hero">
      <div>
        <div class="kicker">SIH 2026 · Smart Education & Skilling</div>
        <h1>Bridging Academia and Industry</h1>
        <p class="lead">SkillBridge connects students, companies, faculty, and institutions on a single intelligent platform — assess competencies, bridge skill deficits, upload resumes, and match to internships with explainable hybrid intelligence.</p>
        <div style="display:flex;gap:10px;margin-top:18px;flex-wrap:wrap">
          <a class="btn btn-primary" href="#/login">Enter Portal</a>
          <a class="btn btn-ghost" href="#/register">Create Account</a>
        </div>
      </div>
      <div class="hero-panel">
        <div class="kicker" style="color:#8fd4cc">Intelligent Portal Workflow</div>
        <h3 style="margin:8px 0 14px;color:#fff">From Assessment to Industry Placement</h3>
        <div class="flow">
          ${[
            "Skill Assessment & Resume Intelligence",
            "Explainable Skill-Gap Prioritization",
            "Hybrid AI Career & Course Recommendations",
            "Multi-Factor Opportunity Matching",
            "Transparent Candidate Ranking & Shortlisting",
            "Institution Skilling & Placement Analytics"
          ].map((s,i)=>`
            <div class="flow-step"><span class="flow-num">${i+1}</span><span>${s}</span></div>
          `).join("")}
        </div>
      </div>
    </section>
    <section class="roles">
      <h2>Role-Based Collaboration Ecosystem</h2>
      <p class="muted">Four specialized dashboards built over a unified competency taxonomy.</p>
      <div class="grid-4" style="margin-top:18px">
        ${[
          ["Student", "Assess skills, analyze gaps with priority, upload resumes, and apply with real-time match."],
          ["Industry", "Post internships & jobs, define competency levels, rank candidates, and shortlist."],
          ["Academician", "Discover faculty industrial internships, FDPs, research collaborations, and consultancy."],
          ["Institution", "Monitor student readiness, role-wise capability, campus skill gaps, and placements."]
        ].map(([t,d])=>`
          <div class="role-card">
            <div class="role-icon">◆</div>
            <h3>${t}</h3>
            <p class="muted">${d}</p>
            <a class="btn btn-sm btn-primary" href="#/login">Login as ${t}</a>
          </div>`).join("")}
      </div>
    </section>
    <footer class="footer">SkillBridge · Academia–Industry Collaboration Portal · Powered by Hybrid Competency & TF-IDF Cosine Similarity Engine</footer>
  `;
}

function authPage(mode) {
  const isLogin = mode === "login";
  const demos = (state.meta && state.meta.demo_accounts) || [];
  return `
    <div class="auth-wrap">
      <div class="auth-art">
        <a class="brand" href="#/" style="color:#fff"><span class="mark">S</span><span class="brand-word">SkillBridge</span></a>
        <h1 style="color:#fff;margin-top:24px">Bridging Academia and Industry</h1>
        <p>Use the pre-configured SIH demo accounts to explore each stakeholder's perspective: student skill assessment, resume intelligence, industry ranking, and institution analytics.</p>
      </div>
      <form class="auth-form" id="auth-form">
        <h2>${isLogin ? "Sign In" : "Create Account"}</h2>
        ${isLogin ? "" : `
          <label>Full Name</label><input name="name" required placeholder="Dr. / Prof. / Student Name" />
          <label>Role</label>
          <select name="role">
            <option value="student">Student</option>
            <option value="industry">Industry Partner</option>
            <option value="academician">Academician / Faculty</option>
            <option value="institution">Institution Admin</option>
          </select>
          <label>College / Company / Institution</label>
          <input name="org" placeholder="NIT Jaipur / TechNova Solutions" />
        `}
        <label>Email Address</label><input name="email" type="email" required />
        <label>Password</label><input name="password" type="password" required />
        <button class="btn btn-primary" style="margin-top:16px;justify-content:center">${isLogin ? "Sign In" : "Create Account"}</button>
        <p class="muted">${isLogin ? `Need an account? <a href="#/register">Register</a>` : `Already registered? <a href="#/login">Sign in</a>`}</p>
        <div class="demo-box">
          <strong>1-Click SIH Demo Logins</strong>
          ${demos.map(d => `<button type="button" class="btn btn-ghost btn-sm demo-fill" data-email="${d.email}" data-password="${d.password}">${d.role}</button>`).join("")}
        </div>
      </form>
    </div>`;
}

function bars(obj) {
  return Object.entries(obj).map(([k,v]) => {
    const warn = v < 65;
    return `<div>
      <div style="display:flex;justify-content:space-between;font-size:13px">
        <span>${k}</span><strong>${Math.round(v)}%</strong>
      </div>
      <div class="bar ${warn ? "warn" : "ok"}"><span style="width:${Math.min(100, v)}%"></span></div>
    </div>`;
  }).join("");
}

function priorityBadge(p) {
  const pLower = (p || "low").toLowerCase();
  return `<span class="badge-priority priority-${pLower}">${p}</span>`;
}

// -------------------------------------------------------------------------
// STUDENT DASHBOARD (PHASE 7)
// -------------------------------------------------------------------------

async function studentDashboard() {
  const d = await api("/api/student/dashboard");
  const p = d.user.profile;
  const rec = d.recommendations;
  const gaps = d.gaps;

  setTimeout(() => {
    wipeCharts();
    const el = document.getElementById("dash-radar");
    if (el && window.Chart && gaps && gaps.rows) {
      const topRows = gaps.rows.slice(0, 7);
      const chart = new Chart(el, {
        type: "radar",
        data: {
          labels: topRows.map(r => r.skill),
          datasets: [
            {
              label: "Your Skill Score",
              data: topRows.map(r => r.student),
              backgroundColor: "rgba(15, 124, 114, 0.25)",
              borderColor: "#0f7c72",
              pointBackgroundColor: "#0f7c72",
            },
            {
              label: "Target Required",
              data: topRows.map(r => r.required),
              backgroundColor: "rgba(201, 132, 42, 0.15)",
              borderColor: "#c9842a",
              borderDash: [4, 4],
              pointBackgroundColor: "#c9842a",
            }
          ]
        },
        options: {
          scales: { r: { min: 0, max: 100 } },
          plugins: { legend: { position: "bottom" } }
        }
      });
      activeCharts.push(chart);
    }
  }, 60);

  return shell(`
    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px">
      <div>
        <h2 style="margin:0">Student Dashboard</h2>
        <p class="muted">${p.degree} ${p.branch} · ${p.year} · ${p.college}</p>
      </div>
      <div style="display:flex;gap:8px">
        <button class="btn btn-primary btn-sm" id="btn-open-resume">📄 Upload & Analyze Resume</button>
        <a class="btn btn-ghost btn-sm" href="#/student/portfolio">Digital Portfolio</a>
      </div>
    </div>

    <div class="cards" style="margin-top:16px">
      <div class="card">
        <h3>Career Goal</h3>
        <select id="goal-select" style="margin-top:4px;font-weight:600">
          ${(d.career_goals || []).map(g => `<option value="${g}" ${g === p.career_goal ? "selected" : ""}>${g}</option>`).join("")}
        </select>
        <p class="muted" style="margin-top:8px"><small>Target benchmarks update automatically</small></p>
      </div>
      <div class="card">
        <h3>Career Readiness</h3>
        <div class="stat">${p.readiness_pct || 0}%</div>
        <div class="bar"><span style="width:${p.readiness_pct || 0}%"></span></div>
        <p class="muted"><small>${gaps ? gaps.summary : "Complete assessment to measure"}</small></p>
      </div>
      <div class="card">
        <h3>Overall Skill Score</h3>
        <div class="stat">${p.overall_skill_score || "—"}</div>
        <p class="muted"><small>Across core technical competencies</small></p>
      </div>
      <div class="card">
        <h3>Active Applications</h3>
        <div class="stat">${d.applications_count}</div>
        <p class="muted"><small><a href="#/student/applications">View pipeline timeline →</a></small></p>
      </div>
    </div>

    ${!p.assessment_completed ? `
      <div class="notice" style="margin-top:16px">
        <strong>Skill assessment required:</strong> Complete the questionnaire or load sample SIH answers to activate gap analysis and recommendations.
        <a class="btn btn-primary btn-sm" style="margin-left:12px" href="#/student/assessment">Take Assessment</a>
      </div>` : ""}

    <div class="row">
      <div class="card">
        <div style="display:flex;justify-content:space-between;align-items:center">
          <h3 style="margin:0">Competency Comparison Radar</h3>
          <span class="chip">${p.career_goal || "Data Analyst"}</span>
        </div>
        <canvas id="dash-radar" style="max-height:280px;margin-top:12px"></canvas>
      </div>

      <div class="card">
        <h3>Resume Intelligence Status</h3>
        <p><strong>Active Resume:</strong> ${p.resume_filename ? `<span class="chip ok">${p.resume_filename}</span>` : `<span class="chip warn">Not uploaded yet</span>`}</p>
        <p class="muted" style="font-size:13px">Upload your PDF/Word resume to extract verified skills, detect missing competencies for your target career goal, and update your profile with 1-click confirmation.</p>
        <button class="btn btn-primary btn-sm" id="btn-open-resume-2" style="margin-top:8px">Upload Resume</button>
        <hr style="border:0;border-top:1px solid var(--line);margin:14px 0" />
        <h3 style="margin:0 0 8px">Top Identified Strengths</h3>
        ${bars(Object.fromEntries(Object.entries(d.skills).filter(([_,v]) => v >= 65).slice(0, 4)))}
      </div>
    </div>

    <div class="row" style="margin-top:16px">
      <div class="card">
        <div style="display:flex;justify-content:space-between;align-items:center">
          <h3 style="margin:0">AI-Matched Internships</h3>
          <a class="btn btn-ghost btn-sm" href="#/student/opportunities">Browse All</a>
        </div>
        ${rec && rec.internships && rec.internships.length ? rec.internships.slice(0, 3).map(i => `
          <div style="padding:10px 0;border-bottom:1px solid var(--line)">
            <div style="display:flex;justify-content:space-between;align-items:center">
              <div>
                <strong>${i.title}</strong><br>
                <small class="muted">${i.company}</small>
              </div>
              <span class="match-pill">${i.match}% Match</span>
            </div>
            <div class="chips" style="margin-top:6px">
              ${(i.matching_skills || []).slice(0, 3).map(s => `<span class="chip ok">✓ ${s}</span>`).join("")}
              ${(i.missing_skills || []).slice(0, 2).map(s => `<span class="chip warn">⚠ ${s}</span>`).join("")}
            </div>
          </div>`).join("") : `<p class="muted">Complete assessment to view matched internships.</p>`}
      </div>

      <div class="card">
        <div style="display:flex;justify-content:space-between;align-items:center">
          <h3 style="margin:0">Curated Learning Path</h3>
          <a class="btn btn-ghost btn-sm" href="#/student/recommendations">View All</a>
        </div>
        <p style="margin:8px 0 4px"><strong>Recommended Courses</strong></p>
        <ul style="padding-left:18px;margin:0">
          ${(rec && rec.courses || []).slice(0, 3).map(c => `<li style="margin-bottom:6px"><strong>${c.title}</strong> <small class="muted">(${c.provider})</small></li>`).join("") || "<li class='muted'>Assess skills to generate path</li>"}
        </ul>
        <p style="margin:12px 0 4px"><strong>Industry Certifications</strong></p>
        <ul style="padding-left:18px;margin:0">
          ${(rec && rec.certifications || []).slice(0, 2).map(c => `<li style="margin-bottom:6px"><strong>${c.title}</strong> — ${c.issuer}</li>`).join("") || "<li class='muted'>Assess skills to generate path</li>"}
        </ul>
      </div>
    </div>
  `);
}

// -------------------------------------------------------------------------
// SKILL ASSESSMENT (PHASE 1)
// -------------------------------------------------------------------------

async function assessmentPage() {
  const meta = state.meta || await api("/api/meta");
  state.meta = meta;
  const tech = meta.questions.filter(q => q.category === "technical");
  const soft = meta.questions.filter(q => q.category === "soft");
  
  const block = (title, qs) => `
    <h3>${title}</h3>
    ${qs.map(q => `
      <div class="q-card">
        <p style="margin:0 0 10px;font-weight:600">${q.text} <span class="chip" style="font-size:11px">${q.skill}</span></p>
        <div class="scale">
          ${[1,2,3,4,5].map(n => `<label><input type="radio" name="${q.id}" value="${n}" required /> ${n}</label>`).join("")}
        </div>
        <small class="muted">1 = Beginner · 3 = Working Knowledge · 5 = Highly Proficient</small>
      </div>`).join("")}`;

  return shell(`
    <h2>Student Skill Assessment</h2>
    <p class="muted">Evaluate your technical competencies and professional skills to generate your explainable skill graph.</p>
    <div class="notice" style="margin-bottom:16px">
      <strong>SIH Walkthrough Shortcut:</strong> Click the button below to prefill realistic demonstration answers (Python 75%, SQL 45%, AI/ML 35%, Power BI 40%).
      <div style="margin-top:8px">
        <button class="btn btn-gold btn-sm" id="demo-assess">Load SIH Demo Answers & Score</button>
      </div>
    </div>
    <form id="assess-form" style="margin-top:14px">
      ${block("Core Technical Competencies", tech)}
      ${block("Professional & Soft Skills", soft)}
      <button class="btn btn-primary" style="margin-top:14px">Submit & Generate Skill Profile</button>
    </form>
  `);
}

// -------------------------------------------------------------------------
// SKILL GAP ANALYSIS (PHASE 2)
// -------------------------------------------------------------------------

async function gapsPage() {
  const profile = await api("/api/student/skill-profile");
  if (!profile.assessment_completed) {
    return shell(`<div class="notice">Please complete the <a href="#/student/assessment">skill assessment</a> first to generate your skill gap analysis.</div>`);
  }
  const goal = profile.career_goal || "Data Analyst";
  const gaps = await api(`/api/student/skill-gaps?career=${encodeURIComponent(goal)}`);
  const roles = (state.meta && state.meta.roles) || ["Data Analyst", "Software Engineer", "ML Engineer", "Cloud Engineer", "Cybersecurity Analyst", "Full Stack Developer"];

  setTimeout(() => {
    wipeCharts();
    const el = document.getElementById("gaps-bar-chart");
    if (el && window.Chart && gaps.rows) {
      const chart = new Chart(el, {
        type: "bar",
        data: {
          labels: gaps.rows.map(r => r.skill),
          datasets: [
            { label: "Your Score", data: gaps.rows.map(r => r.student), backgroundColor: "#0f7c72" },
            { label: "Required Benchmark", data: gaps.rows.map(r => r.required), backgroundColor: "#c9842a" }
          ]
        },
        options: {
          responsive: true,
          scales: { y: { min: 0, max: 100 } }
        }
      });
      activeCharts.push(chart);
    }
  }, 60);

  return shell(`
    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px">
      <div>
        <h2 style="margin:0">Skill-Gap Analysis Engine</h2>
        <p class="muted">Mathematical competency deficit analysis for targeted skilling</p>
      </div>
      <div>
        <label style="margin:0 0 4px;font-size:12px">Target Role / Career Goal</label>
        <select id="goal-select" style="padding:6px 12px">
          ${roles.map(r => `<option ${r === goal ? "selected" : ""}>${r}</option>`).join("")}
        </select>
      </div>
    </div>

    <div class="cards" style="margin-top:16px">
      <div class="card">
        <h3>Career Readiness Score</h3>
        <div class="stat">${gaps.readiness}%</div>
        <p class="muted"><small>Competency coverage ratio</small></p>
      </div>
      <div class="card">
        <h3>High Priority Gaps</h3>
        <div class="stat" style="color:var(--rose)">${gaps.high_priority_count}</div>
        <p class="muted"><small>Deficit ≥ 25 points</small></p>
      </div>
      <div class="card">
        <h3>Medium Priority Gaps</h3>
        <div class="stat" style="color:var(--warn)">${gaps.medium_priority_count}</div>
        <p class="muted"><small>Deficit 10–24 points</small></p>
      </div>
      <div class="card">
        <h3>Satisfied Requirements</h3>
        <div class="stat" style="color:var(--ok)">${gaps.met_count}</div>
        <p class="muted"><small>Proficiency ≥ Benchmark</small></p>
      </div>
    </div>

    <div class="card" style="margin-top:16px">
      <h3>Visual Competency Benchmark Comparison</h3>
      <canvas id="gaps-bar-chart" style="max-height:280px"></canvas>
    </div>

    <div class="row" style="margin-top:16px">
      <div class="card">
        <h3>Skill-by-Skill Gap Breakdown — ${gaps.career_goal}</h3>
        <table class="table">
          <thead>
            <tr>
              <th>Skill</th>
              <th>Category</th>
              <th>Student</th>
              <th>Required</th>
              <th>Gap (Δ)</th>
              <th>Action Priority</th>
            </tr>
          </thead>
          <tbody>
            ${gaps.rows.map(r => `
              <tr>
                <td><strong>${r.skill}</strong></td>
                <td><span class="chip">${r.category}</span></td>
                <td>${r.student}%</td>
                <td>${r.required}%</td>
                <td><strong>${r.gap ? `${r.gap} pts` : "0"}</strong></td>
                <td>${priorityBadge(r.priority)}</td>
              </tr>`).join("")}
          </tbody>
        </table>
      </div>

      <div class="card">
        <h3>Explainable Readiness Formula</h3>
        <div class="notice">
          <p style="font-weight:700;font-size:14px;margin:0 0 6px">$$\\text{Readiness} = \\frac{\\sum \\min(\\text{Student}_i, \\text{Required}_i)}{\\sum \\text{Required}_i} \\times 100$$</p>
          <p style="margin:4px 0"><strong>Competency Coverage Ratio:</strong> Sum of student scores capped at required benchmark divided by total required benchmark points.</p>
          <ul style="padding-left:16px;margin:8px 0">
            <li><span class="badge-priority priority-high">High</span> : Deficit ≥ 25 points (Immediate focus)</li>
            <li><span class="badge-priority priority-medium">Medium</span> : Deficit 10–24 points (Targeted practice)</li>
            <li><span class="badge-priority priority-low">Low</span> : Deficit 1–9 points (Minor gap)</li>
            <li><span class="badge-priority priority-met">Met</span> : Satisfies or exceeds requirement</li>
          </ul>
        </div>
        <a class="btn btn-primary" href="#/student/recommendations" style="margin-top:16px;width:100%;justify-content:center">View AI Recommendations →</a>
      </div>
    </div>
  `);
}

// -------------------------------------------------------------------------
// AI RECOMMENDATIONS (PHASE 3)
// -------------------------------------------------------------------------

async function recsPage() {
  let rec;
  try { rec = await api("/api/student/recommendations"); }
  catch (e) { return shell(`<div class="notice">${e.message} <a href="#/student/assessment">Assess now</a></div>`); }

  return shell(`
    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px">
      <div>
        <h2 style="margin:0">AI Career & Skilling Recommendations</h2>
        <p class="muted">Hybrid Intelligence: 70% Competency Coverage + 30% TF-IDF Cosine Similarity</p>
      </div>
      <span class="chip ok">${rec.engine_note}</span>
    </div>

    <div class="card" style="margin-top:16px">
      <h3 style="color:var(--navy);font-size:20px">${rec.headline}</h3>
      <p style="margin:4px 0 8px">Target competencies to prioritize:</p>
      <div class="chips">
        ${(rec.target_skills_to_learn || []).map(s => `<span class="chip warn">⚠ Learn ${s}</span>`).join("")}
      </div>
    </div>

    <div class="row" style="margin-top:16px">
      <div class="card">
        <h3>Suitable Career Pathways</h3>
        ${(rec.suitable_roles || []).map(r => `
          <div style="padding:10px 0;border-bottom:1px solid var(--line)">
            <div style="display:flex;justify-content:space-between;align-items:center">
              <strong>${r.title} ${r.is_current_goal ? `<span class="chip ok" style="font-size:11px">Current Goal</span>` : ""}</strong>
              <span class="match-pill">${r.readiness}% Readiness</span>
            </div>
            <small class="muted">${r.why}</small>
          </div>`).join("")}
      </div>

      <div class="card">
        <h3>Recommended Practical Projects</h3>
        ${(rec.projects || []).map(p => `
          <div style="padding:10px 0;border-bottom:1px solid var(--line)">
            <strong>${p.title}</strong>
            <p class="muted" style="margin:4px 0;font-size:13px">${p.description}</p>
            <small style="color:var(--teal)">${p.why}</small>
          </div>`).join("")}
      </div>
    </div>

    <div class="row" style="margin-top:16px">
      <div class="card">
        <h3>Recommended Courses</h3>
        ${(rec.courses || []).map(c => `
          <div style="padding:10px 0;border-bottom:1px solid var(--line)">
            <div style="display:flex;justify-content:space-between">
              <strong>${c.title}</strong>
              <span class="chip">${c.provider}</span>
            </div>
            <small class="muted">Duration: ${c.duration} · ${c.why}</small>
          </div>`).join("")}

        <h3 style="margin-top:18px">Industry Certifications</h3>
        ${(rec.certifications || []).map(c => `
          <div style="padding:8px 0;border-bottom:1px solid var(--line)">
            <strong>${c.title}</strong>
            <small class="muted">(${c.issuer}) · ${c.why}</small>
          </div>`).join("")}
      </div>

      <div class="card">
        <h3>Top Matched Internships & Entry Roles</h3>
        ${(rec.internships || []).map(i => `
          <div style="padding:12px 0;border-bottom:1px solid var(--line)">
            <div style="display:flex;justify-content:space-between;align-items:center">
              <strong>${i.title}</strong>
              <span class="match-pill">${i.match}% Match</span>
            </div>
            <small class="muted">${i.company}</small>
            <div class="chips" style="margin:6px 0">
              ${(i.matching_skills || []).map(s => `<span class="chip ok">✓ ${s}</span>`).join("")}
              ${(i.missing_skills || []).map(s => `<span class="chip warn">⚠ ${s}</span>`).join("")}
            </div>
            <p style="font-size:12px;color:var(--muted);margin:0">${(i.why || []).join(" · ")}</p>
          </div>`).join("")}
        <a class="btn btn-primary btn-sm" href="#/student/opportunities" style="margin-top:12px">Search & Apply to Internships →</a>
      </div>
    </div>
  `);
}

// -------------------------------------------------------------------------
// OPPORTUNITIES PORTAL (PHASE 5)
// -------------------------------------------------------------------------

async function opportunitiesPage() {
  const q = new URLSearchParams();
  const params = state._oppFilters || {};
  Object.entries(params).forEach(([k,v]) => { if (v) q.set(k, v); });
  const data = await api("/api/opportunities" + (q.toString() ? `?${q}` : ""));
  const f = data.filters;

  const sel = (name, arr, extra=[]) => `
    <select data-f="${name}">
      <option value="">Filter by ${name}</option>
      ${[...extra, ...arr].map(x => `<option ${params[name]===x?"selected":""} value="${x}">${x}</option>`).join("")}
    </select>`;

  return shell(`
    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px">
      <div>
        <h2 style="margin:0">Internship & Job Opportunities</h2>
        <p class="muted">Real-time candidate compatibility matching with transparent multi-factor breakdown</p>
      </div>
      <div>
        <select data-f="sort_by" id="opp-sort">
          <option value="match" ${params.sort_by==="match"?"selected":""}>Sort by Match % (Highest)</option>
          <option value="recent" ${params.sort_by==="recent"||!params.sort_by?"selected":""}>Sort by Recently Posted</option>
          <option value="title" ${params.sort_by==="title"?"selected":""}>Sort by Title (A-Z)</option>
        </select>
      </div>
    </div>

    <div class="filters" id="opp-filters" style="margin-top:14px">
      <input data-f="q" placeholder="Search title or company" value="${params.q||""}" style="min-width:200px" />
      ${sel("type", f.types, ["internship", "job", "live_project", "apprenticeship"])}
      ${sel("location", f.locations)}
      ${sel("skill", f.skills)}
      ${sel("industry", f.industries)}
      <select data-f="remote">
        <option value="">Any Location / Remote</option>
        <option value="true" ${params.remote==="true"?"selected":""}>Remote Only</option>
      </select>
      <button class="btn btn-primary btn-sm" id="apply-filters">Apply Filters</button>
      <button class="btn btn-ghost btn-sm" id="reset-filters">Reset</button>
    </div>

    <div class="opp-grid" style="margin-top:14px">
      ${data.items.map(o => {
        const m = o.match;
        const bd = m ? m.breakdown : null;
        return `
          <article class="opp-card">
            <div style="display:flex;justify-content:space-between;align-items:flex-start">
              <span class="chip" style="text-transform:capitalize">${o.type.replace("_"," ")}</span>
              ${m ? `<span class="match-pill">${m.score}% Match</span>` : ""}
            </div>
            <h3 style="margin:2px 0 0;font-size:18px">${o.title}</h3>
            <p class="muted" style="margin:0;font-size:13px">${o.company} · ${o.location}${o.remote?" (Remote)":""} · ${o.duration}</p>
            
            ${bd ? `
              <div class="breakdown-grid">
                <div class="breakdown-item">
                  <span>Skill Compat: <strong>${Math.round(bd.skill_compatibility)}%</strong></span>
                  <div class="mini-bar"><span style="width:${bd.skill_compatibility}%"></span></div>
                </div>
                <div class="breakdown-item">
                  <span>Education: <strong>${Math.round(bd.education)}%</strong></span>
                  <div class="mini-bar"><span style="width:${bd.education}%"></span></div>
                </div>
                <div class="breakdown-item">
                  <span>Career Align: <strong>${Math.round(bd.career_alignment)}%</strong></span>
                  <div class="mini-bar"><span style="width:${bd.career_alignment}%"></span></div>
                </div>
                <div class="breakdown-item">
                  <span>Projects/Certs: <strong>${Math.round((bd.projects + bd.certifications)/2)}%</strong></span>
                  <div class="mini-bar"><span style="width:${(bd.projects + bd.certifications)/2}%"></span></div>
                </div>
              </div>` : ""}

            <div class="chips">
              ${(o.matching_skills || []).map(s => `<span class="chip ok">✓ ${s}</span>`).join("")}
              ${(o.missing_skills || []).map(s => `<span class="chip warn">⚠ ${s}</span>`).join("")}
            </div>

            <p class="muted" style="margin:2px 0;font-size:12px"><strong>Eligibility:</strong> ${o.eligibility || o.min_qualification}</p>

            <button class="btn btn-primary btn-sm apply-btn" data-id="${o.id}" style="margin-top:auto" ${o.applied?"disabled":""}>
              ${o.applied ? `Applied (${(o.application_status || "").replace("_", " ")})` : "Apply with Match Profile"}
            </button>
          </article>`;
      }).join("")}
    </div>
  `);
}

// -------------------------------------------------------------------------
// RESUME INTELLIGENCE MODAL (PHASE 4)
// -------------------------------------------------------------------------

function openResumeModal() {
  openModal(`
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
      <h3 style="margin:0">Resume Intelligence Service</h3>
      <button class="btn btn-ghost btn-sm" id="close-m">✕</button>
    </div>
    <p class="muted" style="font-size:13px">Upload your resume (PDF, Word DOCX, or TXT). We will extract verified technical and soft skills, compare them against your current profile, and let you preview and confirm before updating.</p>
    
    <div class="upload-box" id="drop-area">
      <p style="font-size:28px;margin:0 0 8px">📄</p>
      <p style="margin:0"><strong>Click to select your resume</strong> or drag & drop here</p>
      <p class="muted" style="font-size:12px;margin:4px 0 0">Supported formats: .pdf, .docx, .txt (Max 8MB)</p>
      <input type="file" id="resume-file" accept=".pdf,.docx,.doc,.txt" style="display:none" />
    </div>

    <div id="parse-loading" class="hidden" style="text-align:center;padding:24px">
      <p>Analyzing resume and extracting skills with ontology mapping...</p>
    </div>

    <div id="parse-results" class="hidden" style="margin-top:14px"></div>
  `);

  const drop = $("#drop-area");
  const finput = $("#resume-file");
  $("#close-m").onclick = closeModal;

  drop.onclick = () => finput.click();
  finput.onchange = async () => {
    if (!finput.files || !finput.files[0]) return;
    const file = finput.files[0];
    const fd = new FormData();
    fd.append("resume", file);

    $("#drop-area").classList.add("hidden");
    $("#parse-loading").classList.remove("hidden");

    try {
      const res = await api("/api/student/resume/upload", { method: "POST", body: fd });
      $("#parse-loading").classList.add("hidden");
      renderResumeResults(res);
    } catch (err) {
      $("#parse-loading").classList.add("hidden");
      $("#drop-area").classList.remove("hidden");
      toast("Error: " + err.message);
    }
  };
}

function renderResumeResults(res) {
  const p = res.parsed;
  const target = $("#parse-results");
  target.classList.remove("hidden");

  target.innerHTML = `
    <h4 style="margin:0 0 8px;color:var(--navy)">Extracted Competency Preview — ${res.filename}</h4>
    <p class="muted" style="font-size:13px">Found ${p.detected_count} skills in document. Check the skills you wish to confirm and merge into your verified skill profile.</p>

    <div style="max-height:240px;overflow-y:auto;border:1px solid var(--line);border-radius:8px;padding:8px">
      <table class="table" style="font-size:13px">
        <thead>
          <tr>
            <th>Select</th>
            <th>Skill</th>
            <th>Keywords Detected</th>
            <th>Suggested Score</th>
            <th>Current Profile</th>
          </tr>
        </thead>
        <tbody>
          ${p.comparison.filter(c => c.detected_in_resume).map(c => `
            <tr>
              <td><input type="checkbox" class="resume-skill-check" data-skill="${c.skill}" data-score="${c.suggested_score}" checked /></td>
              <td><strong>${c.skill}</strong></td>
              <td><small class="muted">${(c.keywords || []).slice(0,3).join(", ") || "mention"}</small></td>
              <td><strong>${c.suggested_score}%</strong></td>
              <td>${c.current_score ? `${c.current_score}%` : `<span class="chip ok">New</span>`}</td>
            </tr>`).join("")}
        </tbody>
      </table>
    </div>

    ${p.missing_for_target && p.missing_for_target.length ? `
      <div class="notice" style="margin-top:10px">
        <strong>Missing for Target Career Goal:</strong>
        ${p.missing_for_target.map(m => `${m.skill} (Needed: ${m.required_score}%)`).join(", ")}
      </div>` : ""}

    <div style="display:flex;gap:8px;margin-top:14px">
      <button class="btn btn-primary" id="btn-confirm-resume">Confirm & Update Profile</button>
      <button class="btn btn-ghost" onclick="closeModal()">Cancel</button>
    </div>
  `;

  $("#btn-confirm-resume").onclick = async () => {
    const toUpdate = {};
    document.querySelectorAll(".resume-skill-check:checked").forEach(cb => {
      toUpdate[cb.dataset.skill] = Number(cb.dataset.score);
    });

    if (Object.keys(toUpdate).length === 0) {
      toast("Please select at least one skill to confirm.");
      return;
    }

    try {
      await api("/api/student/resume/confirm", {
        method: "POST",
        body: { skills_to_update: toUpdate }
      });
      closeModal();
      toast("Profile successfully updated from resume!");
      render();
    } catch (e) {
      toast(e.message);
    }
  };
}

// -------------------------------------------------------------------------
// INDUSTRY CANDIDATE RANKING (PHASE 6)
// -------------------------------------------------------------------------

async function candidatesPage() {
  const dash = await api("/api/industry/dashboard");
  const params = new URLSearchParams(location.hash.split("?")[1] || "");
  let oppId = params.get("opp") || (dash.opportunities[0] && dash.opportunities[0].id);
  if (!oppId) return shell(`<div class="notice">Please post an opportunity first to view candidate ranking.</div>`);

  const viewFilter = state._candFilter || "all";
  const data = await api(`/api/industry/opportunities/${oppId}/candidates?view=${viewFilter}`);

  return shell(`
    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px">
      <div>
        <h2 style="margin:0">Intelligent Candidate Ranking</h2>
        <p class="muted">Explainable matching based on competency, qualifications, and project validation</p>
      </div>
      <div style="display:flex;gap:10px;align-items:center">
        <label style="margin:0">Opportunity:</label>
        <select id="cand-opp">
          ${dash.opportunities.map(o => `<option value="${o.id}" ${String(o.id)===String(oppId)?"selected":""}>${o.title} (${o.applicants} applied)</option>`).join("")}
        </select>
      </div>
    </div>

    <div class="card" style="margin-top:16px">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">
        <div>
          <h3 style="margin:0">${data.opportunity.title}</h3>
          <p class="muted" style="margin:2px 0 0;font-size:13px">${data.opportunity.company} · Required: ${(data.opportunity.required_skills || []).join(", ")}</p>
        </div>
        <div class="tab-bar" style="margin-bottom:0;border:0">
          <button class="tab-btn ${viewFilter==='all'?'active':''}" id="filter-cand-all">All Assessed Students (${data.total_candidates})</button>
          <button class="tab-btn ${viewFilter==='applicants'?'active':''}" id="filter-cand-app">Direct Applicants Only (${data.total_applicants})</button>
        </div>
      </div>

      <table class="table" style="margin-top:14px">
        <thead>
          <tr>
            <th>Rank</th>
            <th>Candidate</th>
            <th>Hybrid Match</th>
            <th>Education</th>
            <th>Matching Skills</th>
            <th>Missing Skills</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          ${data.candidates.map((c, idx) => `
            <tr>
              <td><strong>#${idx + 1}</strong></td>
              <td>
                <strong>${c.name}</strong><br>
                <small class="muted">${c.career_goal || "Student"}</small>
              </td>
              <td><span class="match-pill">${c.match}%</span></td>
              <td>
                ${c.education}<br>
                <small class="muted">${c.college}</small>
              </td>
              <td>
                <div class="chips">
                  ${(c.matching_skills || []).slice(0, 3).map(s => `<span class="chip ok">✓ ${s}</span>`).join("") || "—"}
                </div>
              </td>
              <td>
                <div class="chips">
                  ${(c.missing_skills || []).slice(0, 2).map(s => `<span class="chip warn">⚠ ${s}</span>`).join("") || `<span class="chip ok">None</span>`}
                </div>
              </td>
              <td>
                <span class="chip ${c.status === 'selected' ? 'ok' : (c.status === 'rejected' ? 'warn' : '')}">
                  ${c.status.replace("_", " ")}
                </span>
              </td>
              <td>
                <div style="display:flex;gap:6px;flex-wrap:wrap">
                  <button class="btn btn-ghost btn-sm view-portfolio-btn" data-id="${c.student_id}">Portfolio</button>
                  ${c.application_id ? `
                    <button class="btn btn-primary btn-sm shortlist-btn" data-id="${c.application_id}" ${c.status==='shortlisted'||c.status==='selected'?'disabled':''}>Shortlist</button>
                    <button class="btn btn-danger btn-sm reject-btn" data-id="${c.application_id}" ${c.status==='rejected'?'disabled':''}>Reject</button>
                  ` : `<span class="muted" style="font-size:12px;align-self:center">Not applied</span>`}
                </div>
              </td>
            </tr>`).join("")}
        </tbody>
      </table>
    </div>
  `);
}

function openCandidatePortfolioModal(studentId) {
  api(`/api/student/portfolio/${studentId}`).then(p => {
    const s = p.student.profile;
    openModal(`
      <div style="display:flex;justify-content:space-between;align-items:flex-start;border-bottom:2px solid var(--navy);padding-bottom:12px">
        <div>
          <h2 style="margin:0">${p.student.name}</h2>
          <p class="muted" style="margin:4px 0">${s.degree} ${s.branch} · ${s.year} · ${s.college}</p>
          <div class="chips">${p.badges.map(b => `<span class="chip ok">${b.name}</span>`).join(" ")}</div>
        </div>
        <button class="btn btn-ghost btn-sm" onclick="closeModal()">✕</button>
      </div>
      <div style="max-height:400px;overflow-y:auto;margin-top:12px;padding-right:8px">
        <h4 style="margin:8px 0 4px">Verified Skills</h4>
        ${bars(p.skills)}
        <h4 style="margin:14px 0 4px">Student Projects</h4>
        ${p.projects.map(pr => `<p style="margin:4px 0"><strong>${pr.title}</strong> ${pr.verified ? '· Verified ✓' : ''}<br><small class="muted">${pr.description}</small></p>`).join("") || "<p class='muted'>No projects listed</p>"}
        <h4 style="margin:14px 0 4px">Certifications</h4>
        <ul>${p.certifications.map(c => `<li>${c.title} — ${c.issuer} (${c.year})</li>`).join("") || "<li class='muted'>None</li>"}</ul>
      </div>
    `);
  }).catch(e => toast(e.message));
}

// -------------------------------------------------------------------------
// ACADEMICIAN MODULE (PHASE 9)
// -------------------------------------------------------------------------

async function facultyPage() {
  const d = await api("/api/academician/dashboard");
  const tab = state._facultyTab || "browse";
  const labels = {
    faculty_internship: "Faculty Industrial Internships",
    industrial_training: "Industrial Training for Educators",
    fdp: "Faculty Development Programmes (FDPs)",
    workshop: "Industry Workshops",
    consultancy: "Consultancy Opportunities",
    research: "Research Collaborations",
    industry_project: "Industry Capstone Projects",
    guest_lecture: "Guest Lectures",
  };

  return shell(`
    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px">
      <div>
        <h2 style="margin:0">Academician Collaboration Portal</h2>
        <p class="muted">${d.profile.designation}, ${d.profile.department} · ${d.profile.institution_name}</p>
      </div>
      <div class="tab-bar" style="margin-bottom:0;border:0">
        <button class="tab-btn ${tab==='browse'?'active':''}" id="tab-fac-browse">Browse Opportunities</button>
        <button class="tab-btn ${tab==='requests'?'active':''}" id="tab-fac-requests">My Requests (${d.applications.length})</button>
      </div>
    </div>

    ${tab === 'browse' ? `
      <div class="card" style="margin-top:16px">
        <h3>Recommended Opportunities (Based on Research Interests)</h3>
        <p class="muted" style="margin:0 0 10px;font-size:13px">Interests: ${d.profile.research_interests || "Applied ML, curriculum skilling"}</p>
        <div class="opp-grid">
          ${d.recommendations.map(r => `
            <div class="opp-card">
              <span class="match-pill">Recommended</span>
              <h4 style="margin:4px 0 0">${r.title}</h4>
              <p class="muted" style="margin:0;font-size:13px">${r.org} · ${r.location} · ${r.duration}</p>
              <p style="font-size:13px;margin:4px 0">${r.description}</p>
              <button class="btn btn-primary btn-sm faculty-apply-btn" data-id="${r.id}" style="margin-top:auto" ${r.applied?'disabled':''}>
                ${r.applied ? "Request Submitted" : "Express Interest"}
              </button>
            </div>`).join("")}
        </div>
      </div>

      ${Object.entries(d.grouped).map(([k, items]) => `
        <h3 style="margin-top:24px">${labels[k] || k}</h3>
        <div class="opp-grid">
          ${items.map(r => `
            <article class="opp-card">
              <span class="chip">${labels[k] || k}</span>
              <h4 style="margin:4px 0 0">${r.title}</h4>
              <p class="muted" style="margin:0;font-size:13px">${r.org} · ${r.location} · ${r.duration}</p>
              <p style="font-size:13px;margin:4px 0">${r.description}</p>
              <button class="btn btn-primary btn-sm faculty-apply-btn" data-id="${r.id}" style="margin-top:auto" ${r.applied?'disabled':''}>
                ${r.applied ? "Request Submitted" : "Express Interest"}
              </button>
            </article>`).join("")}
        </div>`).join("")}
    ` : `
      <div class="card" style="margin-top:16px">
        <h3>My Submitted Collaboration Requests</h3>
        <table class="table">
          <thead>
            <tr>
              <th>Opportunity</th>
              <th>Organization</th>
              <th>Type</th>
              <th>Status</th>
              <th>Statement / Note</th>
              <th>Submitted Date</th>
            </tr>
          </thead>
          <tbody>
            ${d.applications.map(a => `
              <tr>
                <td><strong>${a.title}</strong></td>
                <td>${a.org}</td>
                <td><span class="chip">${labels[a.type] || a.type}</span></td>
                <td><span class="chip ok">${a.status}</span></td>
                <td><small class="muted">${a.sop || "—"}</small></td>
                <td><small>${a.created_at ? a.created_at.split("T")[0] : "—"}</small></td>
              </tr>`).join("") || `<tr><td colspan="6" class="muted">No collaboration requests submitted yet.</td></tr>`}
          </tbody>
        </table>
      </div>
    `}
  `);
}

function openFacultyApplyModal(oid) {
  openModal(`
    <h3>Express Interest in Faculty Opportunity</h3>
    <p class="muted" style="font-size:13px">Provide a brief statement of purpose or proposed collaboration scope for the host organization.</p>
    <label>Collaboration Proposal / Statement of Purpose</label>
    <textarea id="sop-text" rows="4" placeholder="Briefly describe your department curriculum goals or research expertise..."></textarea>
    <div style="display:flex;gap:8px;margin-top:14px">
      <button class="btn btn-primary" id="confirm-fac-apply">Submit Expression of Interest</button>
      <button class="btn btn-ghost" onclick="closeModal()">Cancel</button>
    </div>
  `);

  $("#confirm-fac-apply").onclick = async () => {
    try {
      await api(`/api/academician/opportunities/${oid}/apply`, {
        method: "POST",
        body: { statement_of_purpose: $("#sop-text").value }
      });
      closeModal();
      toast("Expression of interest submitted successfully!");
      render();
    } catch (e) { toast(e.message); }
  };
}

// -------------------------------------------------------------------------
// INSTITUTION ANALYTICS (PHASE 8)
// -------------------------------------------------------------------------

async function institutionPage() {
  const d = await api("/api/institution/analytics");
  const k = d.kpis;

  setTimeout(() => {
    wipeCharts();
    const mk = (id, cfg) => {
      const el = document.getElementById(id);
      if (!el || !window.Chart) return;
      activeCharts.push(new Chart(el, cfg));
    };

    // Demand bar chart
    mk("chart-demand", {
      type: "bar",
      data: {
        labels: d.top_industry_skills.map(x => x.skill),
        datasets: [{ label: "Demand Index", data: d.top_industry_skills.map(x => x.pct), backgroundColor: "#0f7c72" }]
      },
      options: { plugins: { legend: { display: false } } }
    });

    // Skill distribution radar
    mk("chart-dist", {
      type: "radar",
      data: {
        labels: Object.keys(d.skill_distribution).slice(0, 8),
        datasets: [{ label: "Avg Student Score", data: Object.values(d.skill_distribution).slice(0, 8), backgroundColor: "rgba(15,124,114,.25)", borderColor: "#10233d" }]
      }
    });

    // Placement readiness doughnut
    mk("chart-ready", {
      type: "doughnut",
      data: {
        labels: ["Internship Ready", "Developing", "Not Assessed"],
        datasets: [{ data: [d.placement_readiness.ready, d.placement_readiness.developing, d.placement_readiness.not_assessed], backgroundColor: ["#0f7c72","#c9842a","#d8e0e8"] }]
      }
    });

    // Role-wise readiness bar chart
    mk("chart-roles", {
      type: "bar",
      data: {
        labels: Object.keys(d.role_readiness || {}),
        datasets: [{ label: "Avg Capability %", data: Object.values(d.role_readiness || {}), backgroundColor: "#173252" }]
      },
      options: { scales: { y: { min: 0, max: 100 } } }
    });

    // Trend line
    mk("chart-trend", {
      type: "line",
      data: {
        labels: d.demand_trends.map(x => x.month),
        datasets: [{ label: "Industry Postings", data: d.demand_trends.map(x => x.postings), borderColor: "#10233d", tension: .3 }]
      }
    });
  }, 60);

  return shell(`
    <h2>${d.institution.institution_name} — Skilling & Placement Analytics</h2>
    <div class="cards">
      <div class="card"><h3>Total Students</h3><div class="stat">${k.total_students}</div></div>
      <div class="card"><h3>Assessments Completed</h3><div class="stat">${k.assessments_completed}</div></div>
      <div class="card"><h3>Internship Ready</h3><div class="stat">${k.internship_ready}</div></div>
      <div class="card"><h3>Placed / Selected</h3><div class="stat">${k.placed}</div></div>
      <div class="card"><h3>Active Opportunities</h3><div class="stat">${k.active_internships}</div></div>
      <div class="card"><h3>Industry Partners</h3><div class="stat">${k.industry_partners}</div></div>
      <div class="card"><h3>High Priority Skill Gaps</h3><div class="stat" style="color:var(--rose)">${k.high_priority_gaps}</div></div>
      <div class="card"><h3>Average Readiness</h3><div class="stat">${k.avg_readiness}%</div></div>
    </div>

    <div class="row" style="margin-top:16px">
      <div class="card">
        <h3>Role-Wise Student Capability Readiness</h3>
        <canvas id="chart-roles"></canvas>
      </div>
      <div class="card">
        <h3>Most Demanded Industry Skills</h3>
        <canvas id="chart-demand"></canvas>
      </div>
    </div>

    <div class="row">
      <div class="card">
        <h3>Student Competency Distribution</h3>
        <canvas id="chart-dist"></canvas>
      </div>
      <div class="card">
        <h3>Placement Readiness Pipeline</h3>
        <canvas id="chart-ready"></canvas>
      </div>
    </div>

    <div class="card" style="margin-top:16px">
      <h3>Campus-Wide Skill Gaps Requiring Faculty Intervention</h3>
      <table class="table">
        <thead>
          <tr>
            <th>Skill Deficit</th>
            <th>Students Below Benchmark</th>
            <th>Average Point Gap</th>
            <th>Recommended Action</th>
          </tr>
        </thead>
        <tbody>
          ${d.skill_gaps.map(g => `
            <tr>
              <td><strong>${g.skill}</strong></td>
              <td>${g.students} students</td>
              <td><span class="chip warn">${g.avg_delta} pts</span></td>
              <td>Recommend NPTEL / FDP workshop intervention</td>
            </tr>`).join("")}
        </tbody>
      </table>
    </div>
  `);
}

// -------------------------------------------------------------------------
// APPLICATIONS & PORTFOLIO PAGES
// -------------------------------------------------------------------------

async function applicationsPage() {
  const data = await api("/api/student/applications");
  if (!data.items.length) {
    return shell(`
      <h2>My Applications</h2>
      <div class="notice">No active applications. Browse <a href="#/student/opportunities">Internships & Jobs</a> to apply.</div>
    `);
  }
  return shell(`
    <h2>My Applications Pipeline</h2>
    ${data.items.map(a => `
      <div class="card" style="margin-bottom:14px">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">
          <div>
            <h3 style="font-size:20px;margin:0;color:var(--navy)">${a.opportunity.title}</h3>
            <p class="muted" style="margin:2px 0 0">${a.opportunity.company} · ${a.opportunity.location} · ${a.opportunity.duration}</p>
          </div>
          <span class="match-pill">${a.match_score}% Match</span>
        </div>

        <div class="timeline" style="margin-top:14px">
          ${a.timeline.map((s,i) => {
            let cls = i < a.current_index ? "done" : i === a.current_index ? "current" : "";
            if (a.terminal === "rejected" && i === a.current_index) cls = "fail";
            const label = s.replace("_"," ");
            const show = (a.terminal === "rejected" && i === 4) ? "rejected" : label;
            return `<div class="t-step ${cls}"><div class="dot"></div><small style="text-transform:capitalize">${show}</small></div>`;
          }).join("")}
        </div>

        ${a.cover_letter ? `<p style="font-size:13px;background:#f8fafc;padding:8px 12px;border-radius:8px;margin:8px 0"><strong>Your Note:</strong> ${a.cover_letter}</p>` : ""}
        <p class="muted" style="font-size:12px;margin:0">${(a.match_reasons||[]).slice(0,3).join(" · ")}</p>
      </div>`).join("")}
  `);
}

async function portfolioPage() {
  const p = await api("/api/student/portfolio");
  const s = p.student.profile;
  return shell(`
    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px">
      <h2>Digital Student Portfolio</h2>
      <button class="btn btn-ghost btn-sm" onclick="window.print()">Print / PDF Export</button>
    </div>
    <div class="portfolio" style="margin-top:14px">
      <header>
        <div>
          <div class="kicker">Verified Recruiter Portfolio</div>
          <h1 style="margin:4px 0 0">${p.student.name}</h1>
          <p class="muted">${s.degree} ${s.branch} · ${s.year} · ${s.college}</p>
          <p>${s.about || ""}</p>
        </div>
        <div>
          <div class="chips">${p.badges.map(b => `<span class="chip ok">${b.name}</span>`).join(" ")}</div>
          <p class="muted" style="margin-top:8px">Overall Skill: <strong>${s.overall_skill_score}%</strong> · Career Readiness: <strong>${s.readiness_pct}%</strong></p>
          ${s.resume_url ? `<p><a href="${s.resume_url}" target="_blank">📄 Download Attached Resume</a></p>` : ""}
        </div>
      </header>

      <h3 style="margin-top:20px">Verified Competency Map</h3>
      ${bars(p.skills)}

      <h3 style="margin-top:24px">Academic & Industrial Projects</h3>
      ${p.projects.map(x => `
        <div style="margin-bottom:10px">
          <strong>${x.title}</strong> ${x.verified ? `<span class="chip ok">Verified ✓</span>` : ""}
          <p class="muted" style="margin:2px 0 4px;font-size:13px">${x.description}</p>
          <div class="chips">${(x.skills||[]).map(sk => `<span class="chip">${sk}</span>`).join("")}</div>
        </div>`).join("") || "<p class='muted'>No projects listed</p>"}

      <h3 style="margin-top:24px">Certifications</h3>
      <ul>
        ${p.certifications.map(c => `<li><strong>${c.title}</strong> — ${c.issuer} (${c.year}) ${c.verified ? "✓" : ""}</li>`).join("") || "<li class='muted'>None</li>"}
      </ul>

      <h3 style="margin-top:24px">Internships & Placement History</h3>
      <ul>
        ${p.internships.map(i => `<li><strong>${i.title}</strong> at ${i.company} — <span class="chip">${i.status}</span></li>`).join("") || "<li class='muted'>None yet</li>"}
      </ul>

      <h3 style="margin-top:24px">Honors & Achievements</h3>
      <ul>
        ${p.achievements.map(a => `<li><strong>${a.title}</strong>: ${a.detail}</li>`).join("") || "<li class='muted'>None</li>"}
      </ul>
    </div>
  `);
}

// -------------------------------------------------------------------------
// INDUSTRY DASHBOARD & POSTING
// -------------------------------------------------------------------------

async function industryDash() {
  const d = await api("/api/industry/dashboard");
  return shell(`
    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px">
      <div>
        <h2 style="margin:0">${d.profile.company_name} Dashboard</h2>
        <p class="muted">${d.profile.sector} · ${d.profile.location}</p>
      </div>
      <a class="btn btn-primary btn-sm" href="#/industry/post">Post New Opportunity</a>
    </div>

    <div class="card" style="margin-top:16px">
      <h3>Active Opportunity Postings & Candidate Pipeline</h3>
      <table class="table">
        <thead>
          <tr>
            <th>Role Title</th>
            <th>Type</th>
            <th>Applicants</th>
            <th>Shortlisted</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          ${d.opportunities.map(o => `
            <tr>
              <td><strong>${o.title}</strong></td>
              <td><span class="chip">${o.type}</span></td>
              <td>${o.applicants} candidates</td>
              <td><span class="chip ok">${o.shortlisted} shortlisted</span></td>
              <td>
                <a class="btn btn-primary btn-sm" href="#/industry/candidates?opp=${o.id}">Match & Rank Candidates</a>
              </td>
            </tr>`).join("") || `<tr><td colspan="5" class="muted">No opportunities posted yet.</td></tr>`}
        </tbody>
      </table>
    </div>
  `);
}

async function postOppPage() {
  return shell(`
    <h2>Post Industry Opportunity</h2>
    <form id="post-form" class="card" style="margin-top:14px">
      <label>Opportunity Title</label><input name="title" required placeholder="Data Analyst Intern" />
      <label>Opportunity Type</label>
      <select name="opp_type">
        <option value="internship">Internship</option>
        <option value="job">Entry-Level Job</option>
        <option value="live_project">Industry Live Project</option>
        <option value="apprenticeship">Apprenticeship</option>
        <option value="workshop">Corporate Workshop</option>
        <option value="mentorship">Mentorship Cohort</option>
      </select>
      <label>Required Competencies (comma separated)</label>
      <input name="required_skills" placeholder="Python, SQL, Excel, Data Visualization" required />
      <div class="row" style="margin-top:0">
        <div>
          <label>Minimum Qualification</label>
          <input name="min_qualification" placeholder="B.Tech / B.Sc / BCA" />
        </div>
        <div>
          <label>Experience Required</label>
          <input name="experience" placeholder="Fresher" />
        </div>
      </div>
      <div class="row" style="margin-top:0">
        <div>
          <label>Location</label>
          <input name="location" placeholder="Bengaluru" />
        </div>
        <div>
          <label>Duration</label>
          <input name="duration" placeholder="6 Months" />
        </div>
      </div>
      <label><input type="checkbox" name="remote" style="width:auto" /> Remote Available</label>
      <label>Application Deadline</label><input name="deadline" type="date" />
      <label>Role Description & Responsibilities</label><textarea name="description" rows="4"></textarea>
      <button class="btn btn-primary" style="margin-top:14px">Publish to Student Portal</button>
    </form>
  `);
}

// -------------------------------------------------------------------------
// APPLY MODAL
// -------------------------------------------------------------------------

async function showApply(id) {
  const o = await api(`/api/opportunities/${id}`);
  const m = o.match || {};
  openModal(`
    <h3>Apply: ${o.title}</h3>
    <p class="muted">${o.company} · ${o.location} · ${o.duration}</p>
    <div style="display:flex;gap:8px;align-items:center;margin:8px 0">
      <span class="match-pill">${m.score || "—"}% Hybrid Match</span>
      <span class="chip">${(m.algorithm || "Hybrid Engine")}</span>
    </div>
    <p style="font-size:13px">${m.blurb || ""}</p>
    <ul>${(m.reasons || []).map(r => `<li><small>${r}</small></li>`).join("")}</ul>
    <label>Cover Note for Recruiter</label>
    <textarea id="cover" rows="3" placeholder="Highlight your relevant projects and why you're interested..."></textarea>
    <div style="display:flex;gap:8px;margin-top:14px">
      <button class="btn btn-primary" id="confirm-apply">Submit Application</button>
      <button class="btn btn-ghost" onclick="closeModal()">Cancel</button>
    </div>
  `);

  $("#confirm-apply").onclick = async () => {
    try {
      await api(`/api/opportunities/${id}/apply`, {
        method: "POST",
        body: { cover_letter: $("#cover").value }
      });
      closeModal();
      toast("Application successfully submitted!");
      go("/student/applications");
    } catch (e) { toast(e.message); }
  };
}

// -------------------------------------------------------------------------
// RENDER & ROUTING
// -------------------------------------------------------------------------

async function refreshSession() {
  const me = await api("/api/auth/me");
  state.user = me.user;
  if (state.user) {
    try { state.notifications = (await api("/api/notifications")).items; } catch { state.notifications = []; }
  }
}

function bindCommon() {
  const logout = $("#logout-link");
  if (logout) logout.onclick = async (e) => {
    e.preventDefault();
    await api("/api/auth/logout", { method: "POST", body: {} });
    state.user = null;
    go("/");
  };

  const bell = $("#bell-btn");
  if (bell) bell.onclick = () => {
    const items = state.notifications.map(n => `
      <div style="padding:8px 0;border-bottom:1px solid var(--line)">
        <strong>${n.title}</strong><br>
        <span class="muted" style="font-size:13px">${n.body}</span>
      </div>`).join("") || "<p class='muted'>No unread notifications</p>";
    openModal(`<h3>Notifications</h3>${items}<button class="btn btn-ghost" onclick="closeModal()" style="margin-top:12px">Close</button>`);
  };
}

async function render() {
  try { state.meta = state.meta || await api("/api/meta"); } catch {}
  await refreshSession();
  const path = hash().split("?")[0];
  const needAuth = path.startsWith("/student") || path.startsWith("/industry") || path.startsWith("/academician") || path.startsWith("/institution");
  
  if (needAuth && !state.user) {
    go("/login");
    return;
  }
  if (state.user && (path === "/login" || path === "/register")) {
    go(homeFor(state.user.role).slice(1));
    return;
  }

  let html = "";
  if (path === "/") html = landing();
  else if (path === "/login") html = authPage("login");
  else if (path === "/register") html = authPage("register");
  else if (path === "/student") html = await studentDashboard();
  else if (path === "/student/assessment") html = await assessmentPage();
  else if (path === "/student/gaps") html = await gapsPage();
  else if (path === "/student/recommendations") html = await recsPage();
  else if (path === "/student/opportunities") html = await opportunitiesPage();
  else if (path === "/student/applications") html = await applicationsPage();
  else if (path === "/student/portfolio") html = await portfolioPage();
  else if (path === "/industry") html = await industryDash();
  else if (path === "/industry/post") html = await postOppPage();
  else if (path === "/industry/candidates") html = await candidatesPage();
  else if (path === "/academician") html = await facultyPage();
  else if (path === "/institution") html = await institutionPage();
  else html = landing();

  appEl.innerHTML = html;
  bindCommon();

  // Auth form
  const form = $("#auth-form");
  if (form) {
    form.onsubmit = async (e) => {
      e.preventDefault();
      const fd = new FormData(form);
      try {
        if (path === "/login") {
          const u = await api("/api/auth/login", { method: "POST", body: { email: fd.get("email"), password: fd.get("password") } });
          state.user = u;
          toast("Welcome " + u.name);
          go(homeFor(u.role).slice(1));
        } else {
          const role = fd.get("role");
          const org = fd.get("org");
          const body = { name: fd.get("name"), email: fd.get("email"), password: fd.get("password"), role };
          if (role === "student") body.college = org;
          if (role === "industry") body.company_name = org;
          if (role === "academician") body.institution_name = org;
          if (role === "institution") body.institution_name = org;
          const u = await api("/api/auth/register", { method: "POST", body });
          state.user = u;
          toast("Account registered!");
          go(homeFor(u.role).slice(1));
        }
      } catch (err) { toast(err.message); }
    };
    document.querySelectorAll(".demo-fill").forEach(btn => {
      btn.onclick = () => {
        form.email.value = btn.dataset.email;
        form.password.value = btn.dataset.password;
      };
    });
  }

  // Resume Upload Trigger
  const resumeBtn = $("#btn-open-resume");
  const resumeBtn2 = $("#btn-open-resume-2");
  if (resumeBtn) resumeBtn.onclick = openResumeModal;
  if (resumeBtn2) resumeBtn2.onclick = openResumeModal;

  // Assessment form
  const assess = $("#assess-form");
  if (assess) {
    assess.onsubmit = async (e) => {
      e.preventDefault();
      const answers = {};
      new FormData(assess).forEach((v, k) => answers[k] = Number(v));
      try {
        await api("/api/student/assessment", { method: "POST", body: { answers } });
        toast("Skill profile generated!");
        go("/student/gaps");
      } catch (err) { toast(err.message); }
    };
    $("#demo-assess").onclick = async () => {
      await api("/api/student/assessment", { method: "POST", body: { demo: true } });
      toast("Demo skill profile loaded!");
      go("/student/gaps");
    };
  }

  // Goal Selector
  const goalSel = $("#goal-select");
  if (goalSel) {
    goalSel.onchange = async () => {
      await api("/api/student/career-goal", { method: "POST", body: { career_goal: goalSel.value } });
      toast("Target role set to " + goalSel.value);
      render();
    };
  }

  // Opportunity filters & sort
  const applyFilt = $("#apply-filters");
  if (applyFilt) {
    applyFilt.onclick = () => {
      state._oppFilters = {};
      $("#opp-filters").querySelectorAll("[data-f]").forEach(el => {
        if (el.value) state._oppFilters[el.dataset.f] = el.value;
      });
      const sortEl = $("#opp-sort");
      if (sortEl && sortEl.value) state._oppFilters.sort_by = sortEl.value;
      render();
    };
  }

  const resetFilt = $("#reset-filters");
  if (resetFilt) {
    resetFilt.onclick = () => {
      state._oppFilters = {};
      render();
    };
  }

  const oppSort = $("#opp-sort");
  if (oppSort) {
    oppSort.onchange = () => {
      state._oppFilters.sort_by = oppSort.value;
      render();
    };
  }

  document.querySelectorAll(".apply-btn").forEach(b => {
    b.onclick = () => showApply(b.dataset.id);
  });

  // Post opportunity form
  const post = $("#post-form");
  if (post) {
    post.onsubmit = async (e) => {
      e.preventDefault();
      const fd = new FormData(post);
      try {
        await api("/api/industry/opportunities", { method: "POST", body: {
          title: fd.get("title"), opp_type: fd.get("opp_type"),
          required_skills: fd.get("required_skills"),
          min_qualification: fd.get("min_qualification"),
          experience: fd.get("experience"), location: fd.get("location"),
          remote: post.remote.checked, duration: fd.get("duration"),
          deadline: fd.get("deadline"), description: fd.get("description"),
        }});
        toast("Opportunity published to student portal!");
        go("/industry");
      } catch (err) { toast(err.message); }
    };
  }

  // Candidate matching
  const candOpp = $("#cand-opp");
  if (candOpp) candOpp.onchange = () => { go("/industry/candidates?opp=" + candOpp.value); };

  const candAll = $("#filter-cand-all");
  const candApp = $("#filter-cand-app");
  if (candAll) candAll.onclick = () => { state._candFilter = "all"; render(); };
  if (candApp) candApp.onclick = () => { state._candFilter = "applicants"; render(); };

  document.querySelectorAll(".shortlist-btn").forEach(b => {
    b.onclick = async () => {
      await api(`/api/applications/${b.dataset.id}/status`, { method: "POST", body: { status: "shortlisted" } });
      toast("Candidate shortlisted!");
      render();
    };
  });

  document.querySelectorAll(".reject-btn").forEach(b => {
    b.onclick = async () => {
      await api(`/api/applications/${b.dataset.id}/status`, { method: "POST", body: { status: "rejected" } });
      toast("Application status updated to Rejected");
      render();
    };
  });

  document.querySelectorAll(".view-portfolio-btn").forEach(b => {
    b.onclick = () => openCandidatePortfolioModal(b.dataset.id);
  });

  // Faculty actions
  const facBrowse = $("#tab-fac-browse");
  const facReqs = $("#tab-fac-requests");
  if (facBrowse) facBrowse.onclick = () => { state._facultyTab = "browse"; render(); };
  if (facReqs) facReqs.onclick = () => { state._facultyTab = "requests"; render(); };

  document.querySelectorAll(".faculty-apply-btn").forEach(b => {
    b.onclick = () => openFacultyApplyModal(b.dataset.id);
  });
}

window.addEventListener("hashchange", render);
render();
