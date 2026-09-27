"""
Future Era — Merged FastAPI backend.

Combines:
  - Himanshu's AI career blueprint backend (Gemini + SQLite)
  - Harshit's career data JSON API

Serves the merged frontend as static files from one process on one port.
"""

import os
import hashlib
import json
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response, JSONResponse

from app.config import GEMINI_API_KEY
from app.schemas import (
    AnalyzeRequest,
    CareerBlueprintResponse,
    SuggestProfessionsRequest,
    SuggestProfessionsResponse
)
from app.services.gemini_service import generate_career_blueprint, suggest_eligible_professions
from app.services.validation import validate_career_request, is_gibberish_or_fake
from app.database import (
    init_db,
    save_blueprint_to_db,
    get_blueprint_from_db,
    save_suggestions_to_db,
    get_suggestions_from_db,
    get_database_stats
)

# --- Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
DATA_DIR = os.path.join(BASE_DIR, "data")
DATA_FILE = os.path.join(DATA_DIR, "career_data.json")
PEOPLE_FILE = os.path.join(DATA_DIR, "people.json")

# --- Career data (from Harshit's infoproject) ---
REQUIRED_KEYS = (
    "RESOURCES", "STREAMS", "DURATIONS", "DEGREES", "INTERESTS",
    "HOBBIES", "SKILLS", "ROLES", "PHASES", "GENERIC_ITEM", "GENERIC_PHASES",
)

INTEREST_WEIGHT = 60
SKILL_WEIGHT = 40

@lru_cache(maxsize=1)
def load_career_data() -> dict:
    """Read career_data.json once and keep it in memory."""
    data_path = Path(DATA_FILE)
    if not data_path.exists():
        return {}
    data = json.loads(data_path.read_text(encoding="utf-8"))
    missing = [key for key in REQUIRED_KEYS if key not in data]
    if missing:
        print(f"[career data warning] Missing keys: {', '.join(missing)}")
    return data

@lru_cache(maxsize=1)
def career_payload() -> tuple:
    """The serialised dataset and its ETag."""
    data = load_career_data()
    if not data:
        return "", ""
    body = json.dumps(data, separators=(",", ":"))
    etag = '"' + hashlib.sha256(body.encode("utf-8")).hexdigest()[:32] + '"'
    return body, etag

@lru_cache(maxsize=1)
def load_groups() -> dict:
    """Read groups from people.json."""
    people_path = Path(PEOPLE_FILE)
    if not people_path.exists():
        return {}
    data = json.loads(people_path.read_text(encoding="utf-8"))
    return data.get("GROUPS", {})

@lru_cache(maxsize=1)
def load_people() -> list:
    """Read people list from people.json."""
    people_path = Path(PEOPLE_FILE)
    if not people_path.exists():
        return []
    data = json.loads(people_path.read_text(encoding="utf-8"))
    return data.get("PEOPLE", [])

def score_tags(
    my_interests: set[str],
    my_skills: set[str],
    have_interests: set[str],
    have_skills: set[str],
) -> tuple[int | None, list[str], list[str]]:
    """Score tags between user and member/group."""
    shared_i = sorted(my_interests & have_interests)
    shared_s = sorted(my_skills & have_skills)
    if not my_interests and not my_skills:
        return None, shared_i, shared_s

    parts = 0.0
    score = 0.0
    if my_interests:
        parts += INTEREST_WEIGHT
        score += INTEREST_WEIGHT * (len(shared_i) / len(my_interests))
    if my_skills:
        parts += SKILL_WEIGHT
        score += SKILL_WEIGHT * (len(shared_s) / len(my_skills))

    return round(score * 100 / parts), shared_i, shared_s

def match_people(my_interests: set[str], my_skills: set[str]) -> list[dict]:
    """Score every member against visitor's picks and sort best first."""
    scored: list[dict] = []
    career = load_career_data()
    roles = career.get("ROLES", {})
    for person in load_people():
        score, shared_i, shared_s = score_tags(
            my_interests,
            my_skills,
            set(person.get("interests") or []),
            set(person.get("skills") or []),
        )
        role = person.get("role")
        scored.append({
            "id": person["id"],
            "name": person["name"],
            "handle": person.get("handle", ""),
            "role": role,
            "roleLabel": roles.get(role, {}).get("label", ""),
            "blurb": person.get("blurb", ""),
            "interests": person.get("interests") or [],
            "skills": person.get("skills") or [],
            "groups": person.get("groups") or [],
            "followers": person.get("followers", 0),
            "match": {"score": score, "interests": shared_i, "skills": shared_s},
        })
    scored.sort(key=lambda p: (p["match"]["score"] is None, -(p["match"]["score"] or 0), -p["followers"], p["name"]))
    return scored

def match_groups(my_interests: set[str], my_skills: set[str]) -> list[dict]:
    """Rank groups by member tag match."""
    people = load_people()
    rows: list[dict] = []
    for gid, group in load_groups().items():
        members = [p for p in people if gid in (p.get("groups") or [])]
        group_interests: set[str] = set()
        group_skills: set[str] = set()
        for person in members:
            group_interests |= set(person.get("interests") or [])
            group_skills |= set(person.get("skills") or [])

        score, shared_i, shared_s = score_tags(
            my_interests, my_skills, group_interests, group_skills
        )
        sharing = [
            p for p in members
            if (my_interests & set(p.get("interests") or []))
            or (my_skills & set(p.get("skills") or []))
        ]
        rows.append({
            "id": gid,
            "label": group["label"],
            "blurb": group.get("blurb", ""),
            "members": len(members),
            "matches": len(sharing),
            "names": [p["name"] for p in sharing[:3]],
            "match": {"score": score, "interests": shared_i, "skills": shared_s},
        })
    rows.sort(key=lambda g: (
        g["match"]["score"] is None,
        -(g["match"]["score"] or 0),
        -g["matches"],
        -g["members"],
        g["label"],
    ))
    return rows

def split_tags(raw: str | None) -> set[str]:
    """Read a comma separated tag list."""
    if not raw:
        return set()
    return {t.strip() for t in raw.split(",") if t.strip()}


# --- App ---
app = FastAPI(
    title="Future Era",
    description="The GenX Era — Future-proof career intelligence & market tech engine powered by FastAPI & Gemini",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static folder
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Initialize database
init_db()

# Validate career data at startup
_cd = load_career_data()
if _cd:
    counts = ", ".join(f"{k}={len(v)}" for k, v in _cd.items() if isinstance(v, (list, dict)))
    print(f"[career data ok] {counts}")
else:
    print("[career data] No career_data.json found, /api/career-data will be unavailable")


NO_CACHE_HEADERS = {
    "Cache-Control": "no-cache, no-store, must-revalidate",
    "Pragma": "no-cache",
    "Expires": "0"
}


# ==================== PAGE ROUTES ====================

@app.get("/")
async def serve_index():
    """Serves the Future Era landing page."""
    return FileResponse(os.path.join(STATIC_DIR, "index.html"), headers=NO_CACHE_HEADERS)


@app.get("/creators")
async def serve_creators():
    """Serves the Creators page."""
    return FileResponse(os.path.join(STATIC_DIR, "creators.html"), headers=NO_CACHE_HEADERS)


@app.get("/console")
async def serve_console():
    """Serves the Career Architecture Console page."""
    return FileResponse(os.path.join(STATIC_DIR, "console.html"), headers=NO_CACHE_HEADERS)


@app.get("/stage")
@app.get("/select-stage")
async def serve_stage():
    """Serves the Stage Selection middle page."""
    return FileResponse(os.path.join(STATIC_DIR, "stage.html"), headers=NO_CACHE_HEADERS)


@app.get("/community")
async def serve_community():
    """Serves the Community page."""
    return FileResponse(os.path.join(STATIC_DIR, "community.html"), headers=NO_CACHE_HEADERS)


@app.get("/privacy")
async def serve_privacy():
    """Serves the privacy policy page."""
    return FileResponse(os.path.join(STATIC_DIR, "privacy.html"))


@app.get("/terms")
async def serve_terms():
    """Serves the terms and conditions page."""
    return FileResponse(os.path.join(STATIC_DIR, "terms.html"))


@app.get("/favicon.ico")
async def serve_favicon():
    """Serves the SVG favicon."""
    return FileResponse(os.path.join(STATIC_DIR, "favicon.svg"), media_type="image/svg+xml")


# ==================== API ROUTES ====================

@app.get("/api/health")
def health():
    """Liveness probe."""
    return {"status": "ok"}


@app.get("/api/status")
async def check_status():
    """Checks whether an API key is configured on the server."""
    return {
        "has_server_api_key": bool(GEMINI_API_KEY),
        "status": "ready" if GEMINI_API_KEY else "needs_api_key"
    }


@app.get("/api/career-data")
def career_data(request: Request) -> Response:
    """The full career dataset from Harshit's data file (with ETag caching)."""
    body, etag = career_payload()
    if not body:
        return Response(content='{"error":"career data not loaded"}',
                       media_type="application/json", status_code=500)

    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304, headers={"ETag": etag, "Cache-Control": "public, max-age=300"})

    return Response(
        content=body,
        media_type="application/json",
        headers={"Cache-Control": "public, max-age=300", "ETag": etag},
    )


@app.get("/api/db/stats")
async def db_stats():
    """Returns database telemetry and count of cached blueprints & suggestions."""
    return get_database_stats()


@app.get("/api/people")
def get_people(request: Request) -> JSONResponse:
    """The community member list, ranked against visitor's tags."""
    career = load_career_data()
    valid_interests = {i["id"] for i in career.get("INTERESTS", [])}
    valid_skills = {s["id"] for s in career.get("SKILLS", [])}
    my_interests = split_tags(request.query_params.get("interests")) & valid_interests
    my_skills = split_tags(request.query_params.get("skills")) & valid_skills

    return JSONResponse(
        {
            "interests": [{"id": i["id"], "label": i["label"]} for i in career.get("INTERESTS", [])],
            "skills": [{"id": s["id"], "label": s["label"]} for s in career.get("SKILLS", [])],
            "people": match_people(my_interests, my_skills),
            "groups": match_groups(my_interests, my_skills),
            "mine": {
                "interests": sorted(my_interests),
                "skills": sorted(my_skills),
                "ranked": bool(my_interests or my_skills),
            },
            "weights": {"interest": INTEREST_WEIGHT, "skill": SKILL_WEIGHT},
        },
        headers={"Cache-Control": "no-store"},
    )


@app.get("/api/groups")
def get_groups() -> JSONResponse:
    """The group registry for the profile popup."""
    registry = load_groups()
    people = load_people()
    sizes = {
        gid: sum(1 for p in people if gid in (p.get("groups") or []))
        for gid in registry
    }
    return JSONResponse(
        {
            "groups": [
                {
                    "id": gid,
                    "label": g["label"],
                    "blurb": g.get("blurb", ""),
                    "members": sizes.get(gid, 0),
                }
                for gid, g in registry.items()
            ],
        },
        headers={"Cache-Control": "no-store"},
    )


@app.post("/api/analyze", response_model=CareerBlueprintResponse)
async def analyze_career(request: AnalyzeRequest):
    """
    Main endpoint: Generates future-proof roadmap, AI analysis, 
    and 2026 tech radar for either 12th-pass or final-year students.
    Every generated detail is persisted to the SQLite database.
    If the AI API is offline or unavailable, data is fetched from the database cache.
    """
    data = request.model_dump()

    # 1. Heuristic and sanity check for fake/empty/gibberish details
    is_valid, validation_msg = validate_career_request(data)
    if not is_valid:
        raise HTTPException(status_code=400, detail=validation_msg)

    # 2. Attempt AI Generation
    try:
        result = await generate_career_blueprint(data, client_api_key=request.api_key)

        # Check if AI detected fake or non-existent details
        if not result.get("is_valid", True):
            err_msg = result.get("error_message") or "Blueprint doesn't exist. Please check the entered data and provide legitimate educational degrees, skills, or career roles."
            raise HTTPException(status_code=400, detail=err_msg)

        # Save to database for permanent offline caching
        result["data_source"] = "ai"
        save_blueprint_to_db(data, result)
        return result

    except HTTPException:
        raise
    except Exception as ai_err:
        # 3. If Gemini API is offline/unavailable/failing -> Fetch from Database Vault!
        print(f"[Database Fallback] Gemini API unavailable: {ai_err}. Querying SQLite database...")
        cached_blueprint = get_blueprint_from_db(data)
        if cached_blueprint and cached_blueprint.get("is_valid", True):
            cached_blueprint["data_source"] = "database_cache"
            return cached_blueprint

        raise HTTPException(
            status_code=500,
            detail=f"AI API is currently unavailable and no matching blueprint is cached in the database. Please try again shortly. (Error: {str(ai_err)})"
        )


@app.post("/api/suggest-professions", response_model=SuggestProfessionsResponse)
async def suggest_professions_endpoint(request: SuggestProfessionsRequest):
    """
    Analyzes 12th stream and favorite subjects/interests to provide
    multiple eligible career professions so the student can pick one.
    Every generated response is saved to the SQLite database.
    If the AI API is offline, suggestions are fetched from the database.
    """
    data = request.model_dump()
    interests = (data.get("interests") or "").strip()

    # 1. Validation for fake/gibberish details
    if not interests:
        raise HTTPException(
            status_code=400,
            detail="Please choose an interest from the suggested topics above or describe your favorite subjects."
        )
    if is_gibberish_or_fake(interests):
        raise HTTPException(
            status_code=400,
            detail=f"'{interests}' does not look like valid subjects or interests. Please choose from the suggested topics above or enter your genuine interests."
        )

    # 2. Attempt AI Generation
    try:
        result = await suggest_eligible_professions(data, client_api_key=request.api_key)

        if not result.get("is_valid", True):
            err_msg = result.get("error_message") or "Blueprint doesn't exist for the entered details. Please check the entered data."
            raise HTTPException(status_code=400, detail=err_msg)

        # Save to database for permanent offline caching
        result["data_source"] = "ai"
        save_suggestions_to_db(data, result)
        return result

    except HTTPException:
        raise
    except Exception as ai_err:
        # 3. If Gemini API is offline -> Fetch from Database Vault!
        print(f"[Database Fallback] Gemini API unavailable: {ai_err}. Querying SQLite database for suggestions...")
        cached_suggestions = get_suggestions_from_db(data)
        if cached_suggestions and cached_suggestions.get("is_valid", True):
            cached_suggestions["data_source"] = "database_cache"
            return cached_suggestions

        raise HTTPException(
            status_code=500,
            detail=f"AI API is currently unavailable and no suggestions found in the database. (Error: {str(ai_err)})"
        )
